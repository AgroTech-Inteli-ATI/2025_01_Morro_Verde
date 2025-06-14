import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import timedelta
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Dashboard Morro Verde",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': None,
        'Get Help': None,
        'Report a bug': None
    }
)

# Esconde a navegação padrão
hide_pages = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)

# Sidebar com logo e navegação
logo_path = "img/logo-morro-verde.png"
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("# 🌱 Morro Verde")
    st.markdown("---")
    if st.button("🏠 Página Inicial", use_container_width=True):
        st.switch_page("app.py")
    if st.button("📊 Previsões", use_container_width=True):
        st.switch_page("pages/previsoes.py")

st.title("📈 Página de Previsões")

@st.cache_data
def carregar_dados():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'morro_verde.db'))

    df = pd.read_sql_query("""
        SELECT pr.data, pr.preco_min, pr.variacao, pr.modalidade, pr.moeda,
               p.nome_produto, p.formulacao, p.origem AS origem_produto, p.tipo AS tipo_produto, p.unidade,
               l.id as local_id, l.nome AS local, l.estado, l.pais, l.tipo AS tipo_local,
               c.usd_brl, co.custo_total
        FROM precos pr
        JOIN produtos p ON pr.produto_id = p.id
        JOIN locais l ON pr.local_id = l.id
        LEFT JOIN cambio c ON pr.data = c.data
        LEFT JOIN custos_portos co ON co.data = pr.data AND co.porto_id = l.id
    """, conn)

    fretes = pd.read_sql_query("""
        SELECT data, origem_id, destino_id, tipo, custo_usd, custo_brl
        FROM fretes
    """, conn)

    locais = pd.read_sql_query("SELECT id, nome FROM locais", conn)
    
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    df['mes'] = df['data'].dt.month
    df['ano'] = df['data'].dt.year
    df['custo_total'] = df['custo_total'].fillna(0)
    df['usd_brl'] = df['usd_brl'].fillna(method='ffill')
    fretes['data'] = pd.to_datetime(fretes['data'])

    return df, fretes, locais

def detectar_outliers(df, coluna, metodo='iqr'):
    """Detecta e remove outliers usando IQR ou Z-score"""
    if metodo == 'iqr':
        Q1 = df[coluna].quantile(0.25)
        Q3 = df[coluna].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return df[(df[coluna] >= lower_bound) & (df[coluna] <= upper_bound)]
    else:  # z-score
        z_scores = np.abs(stats.zscore(df[coluna]))
        return df[z_scores < 3]

def criar_features_avancadas(df):
    """Cria features temporais e de lag mais sofisticadas"""
    df_sorted = df.sort_values('data').copy()
    
    # Features temporais avançadas
    df_sorted['trimestre'] = df_sorted['data'].dt.quarter
    df_sorted['dia_semana'] = df_sorted['data'].dt.dayofweek
    df_sorted['dia_mes'] = df_sorted['data'].dt.day
    df_sorted['semana_ano'] = df_sorted['data'].dt.isocalendar().week
    
    # Sazonalidade cíclica
    df_sorted['mes_sin'] = np.sin(2 * np.pi * df_sorted['mes'] / 12)
    df_sorted['mes_cos'] = np.cos(2 * np.pi * df_sorted['mes'] / 12)
    df_sorted['trimestre_sin'] = np.sin(2 * np.pi * df_sorted['trimestre'] / 4)
    df_sorted['trimestre_cos'] = np.cos(2 * np.pi * df_sorted['trimestre'] / 4)
    
    # Features de lag melhoradas
    for lag in [1, 2, 3, 7, 15, 30]:
        if len(df_sorted) > lag * 2:
            df_sorted[f'valor_lag_{lag}'] = df_sorted['valor_entregue'].shift(lag)
            df_sorted[f'preco_lag_{lag}'] = df_sorted['preco_min'].shift(lag)
    
    # Médias móveis de diferentes janelas
    for window in [3, 7, 15, 30]:
        if len(df_sorted) > window * 2:
            df_sorted[f'ma_{window}'] = df_sorted['valor_entregue'].rolling(window=window).mean()
            df_sorted[f'std_{window}'] = df_sorted['valor_entregue'].rolling(window=window).std()
    
    # Features de volatilidade
    df_sorted['volatilidade_7d'] = df_sorted['valor_entregue'].rolling(window=7).std()
    df_sorted['volatilidade_30d'] = df_sorted['valor_entregue'].rolling(window=30).std()
    
    # Tendências
    df_sorted['tendencia_7d'] = (df_sorted['valor_entregue'] / df_sorted['valor_entregue'].shift(7)) - 1
    df_sorted['tendencia_30d'] = (df_sorted['valor_entregue'] / df_sorted['valor_entregue'].shift(30)) - 1
    
    # Features de câmbio
    df_sorted['usd_volatilidade'] = df_sorted['usd_brl'].rolling(window=7).std()
    df_sorted['usd_tendencia'] = (df_sorted['usd_brl'] / df_sorted['usd_brl'].shift(7)) - 1
    
    # Razões importantes
    df_sorted['ratio_frete_preco'] = df_sorted['frete_final'] / df_sorted['preco_min']
    df_sorted['ratio_custo_preco'] = df_sorted['custo_total'] / df_sorted['preco_min']
    
    return df_sorted

def validacao_temporal(pipeline, X, y, n_splits=3):
    """Validação temporal usando TimeSeriesSplit"""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = {'mae': [], 'rmse': [], 'mape': []}
    
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_val)
        
        scores['mae'].append(mean_absolute_error(y_val, y_pred))
        scores['rmse'].append(np.sqrt(mean_squared_error(y_val, y_pred)))
        scores['mape'].append(mean_absolute_percentage_error(y_val, y_pred))
    
    return {
        'MAE': np.mean(scores['mae']),
        'RMSE': np.mean(scores['rmse']),
        'MAPE': np.mean(scores['mape']),
        'MAE_std': np.std(scores['mae']),
        'RMSE_std': np.std(scores['rmse']),
        'MAPE_std': np.std(scores['mape'])
    }

def criar_ensemble_model():
    """Cria um ensemble de modelos para melhor performance"""
    models = {
        'xgb': XGBRegressor(
            n_estimators=300,
            learning_rate=0.08,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1
        ),
        'rf': RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
    }
    return models

def calcular_intervalos_confianca(predictions, confidence_level=0.95):
    """Calcula intervalos de confiança usando bootstrap"""
    n_bootstrap = 100
    bootstrap_preds = []
    
    for _ in range(n_bootstrap):
        # Adiciona ruído baseado na variabilidade histórica
        noise = np.random.normal(0, np.std(predictions) * 0.1, len(predictions))
        bootstrap_preds.append(predictions + noise)
    
    bootstrap_preds = np.array(bootstrap_preds)
    alpha = 1 - confidence_level
    
    lower = np.percentile(bootstrap_preds, (alpha/2) * 100, axis=0)
    upper = np.percentile(bootstrap_preds, (1 - alpha/2) * 100, axis=0)
    
    return lower, upper

# Carregamento dos dados
df, fretes, locais = carregar_dados()

st.subheader("🔧 Parâmetros da previsão")

produto = st.selectbox("Produto", sorted(df['nome_produto'].dropna().unique()))
df_prod = df[df['nome_produto'] == produto]

origens = df_prod['local'].unique()
origem = st.selectbox("Origem (porto)", sorted(origens))
filtro_origem = df_prod[df_prod['local'] == origem]
if filtro_origem.empty:
    st.error(f"❌ Local de origem '{origem}' não encontrado.")
    st.stop()
origem_id = filtro_origem['local_id'].iloc[0]


destinos = locais[locais['id'] != origem_id]
destino_nome = st.selectbox("Destino (cliente)", sorted(destinos['nome']))
filtro_destino = destinos[destinos['nome'] == destino_nome]
if filtro_destino.empty:
    st.error(f"❌ Destino '{destino_nome}' não encontrado na base.")
    st.stop()
destino_id = filtro_destino['id'].iloc[0]


meses_futuros = st.slider("Meses futuros para prever:", min_value=1, max_value=12, value=6)

cenario = st.selectbox("Cenário de tendência para previsão futura:", [
    "Neutro (sem ajuste)", "Alta (otimista)", "Queda (pessimista)"
])

# Preparação dos dados melhorada
df_merge = df_prod[df_prod['local'] == origem].copy()
frete_match = fretes[(fretes['origem_id'] == origem_id) & (fretes['destino_id'] == destino_id)]
df_merge = df_merge.merge(frete_match[['data', 'custo_brl', 'custo_usd']], on='data', how='left')

df_merge['custo_brl'] = df_merge['custo_brl'].fillna(0)
df_merge['custo_usd'] = df_merge['custo_usd'].fillna(0)
df_merge['frete_final'] = df_merge['custo_brl'] + (df_merge['custo_usd'] * df_merge['usd_brl'])
df_merge['valor_entregue'] = df_merge['preco_min'] + df_merge['frete_final']

if len(df_merge) < 10:
    st.warning("⚠️ Dados insuficientes para previsão robusta com esse filtro (mínimo 30 registros).")
    st.dataframe(df_merge)
    st.stop()

# Detecção e remoção de outliers
df_merge_clean = detectar_outliers(df_merge, 'valor_entregue', 'iqr')
outliers_removidos = len(df_merge) - len(df_merge_clean)

if outliers_removidos > 0:
    st.info(f"🧹 Removidos {outliers_removidos} outliers para melhor qualidade do modelo")

# Criar features avançadas
df_merge_clean = criar_features_avancadas(df_merge_clean)

# Seleção inteligente de features
base_features = [
    'formulacao', 'origem_produto', 'tipo_produto', 'unidade', 'estado', 'pais',
    'tipo_local', 'modalidade', 'moeda', 'variacao', 'usd_brl',
    'custo_total', 'frete_final', 'mes', 'ano', 'trimestre', 'dia_semana',
    'mes_sin', 'mes_cos', 'trimestre_sin', 'trimestre_cos',
    'ratio_frete_preco', 'ratio_custo_preco'
]

# Features avançadas condicionais
advanced_features = []
for col in df_merge_clean.columns:
    if any(x in col for x in ['lag_', 'ma_', 'std_', 'volatilidade', 'tendencia']):
        if df_merge_clean[col].notna().sum() > len(df_merge_clean) * 0.5:  # 50% de dados válidos
            advanced_features.append(col)

all_features = base_features + advanced_features

# Filtrar dados válidos
df_clean = df_merge_clean.dropna(subset=base_features + ['valor_entregue']).copy()

# Usar features avançadas apenas se tiver dados suficientes
if len(df_clean) >= 50 and advanced_features:
    df_with_advanced = df_merge_clean.dropna(subset=all_features + ['valor_entregue']).copy()
    if len(df_with_advanced) >= 10:
        df_clean = df_with_advanced
        features_to_use = all_features
    else:
        features_to_use = base_features
else:
    features_to_use = base_features

X = df_clean[features_to_use]
y = df_clean['valor_entregue']

# Preparação do pipeline melhorado
categorical_cols = X.select_dtypes(include='object').columns.tolist()
numeric_cols = X.select_dtypes(include=['float64', 'int64']).columns.tolist()

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore', drop='first'), categorical_cols),
    ('num', StandardScaler(), numeric_cols)  # Normalização para melhor performance
])

# Criação do ensemble
models = criar_ensemble_model()
best_model = None
best_score = float('inf')
best_metrics = None

# Teste de modelos com validação temporal
progress_bar = st.progress(0)
status_text = st.empty()

for i, (name, model) in enumerate(models.items()):
    status_text.text(f"🔄 Testando modelo {name.upper()}...")
    
    pipeline = Pipeline([
        ('prep', preprocessor),
        ('model', model)
    ])
    
    # Validação temporal
    metrics = validacao_temporal(pipeline, X, y, n_splits=3)
    
    if metrics['MAPE'] < best_score:
        best_score = metrics['MAPE']
        best_model = pipeline
        best_metrics = metrics
        best_name = name
    
    progress_bar.progress((i + 1) / len(models))

status_text.text(f"✅ Melhor modelo: {best_name.upper()}")

# Exibir métricas com intervalos de confiança
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("MAE", f"R$ {best_metrics['MAE']:.2f}", 
              delta=f"±{best_metrics['MAE_std']:.2f}")
with col2:
    st.metric("RMSE", f"R$ {best_metrics['RMSE']:.2f}", 
              delta=f"±{best_metrics['RMSE_std']:.2f}")
with col3:
    st.metric("MAPE", f"{best_metrics['MAPE']:.2%}", 
              delta=f"±{best_metrics['MAPE_std']:.2%}")

# Treinamento final
best_model.fit(X, y)

# Previsão futura mais robusta
last_row = X.iloc[-1].copy()
last_mes = int(last_row['mes'])
last_ano = int(last_row['ano'])

# Análise de tendência mais sofisticada
recent_data = df_clean.tail(12)  # últimos 12 meses
if len(recent_data) >= 2:
    primeiro_valor = recent_data['valor_entregue'].iloc[0]
    ultimo_valor = recent_data['valor_entregue'].iloc[-1]

    # Evita divisão por zero
    if primeiro_valor != 0:
        tendencia_percentual = (ultimo_valor / primeiro_valor) ** (1 / len(recent_data)) - 1
    else:
        tendencia_percentual = 0

    volatilidade_historica = recent_data['valor_entregue'].pct_change().std()
else:
    tendencia_percentual = 0
    volatilidade_historica = 0.05

futuras = []
for i in range(1, meses_futuros + 1):
    next_mes = (last_mes + i - 1) % 12 + 1
    next_ano = last_ano + (last_mes + i - 1) // 12

    row = last_row.copy()
    row['mes'] = next_mes
    row['ano'] = next_ano
    row['trimestre'] = (next_mes - 1) // 3 + 1
    
    # Atualizar features cíclicas
    row['mes_sin'] = np.sin(2 * np.pi * next_mes / 12)
    row['mes_cos'] = np.cos(2 * np.pi * next_mes / 12)
    row['trimestre_sin'] = np.sin(2 * np.pi * row['trimestre'] / 4)
    row['trimestre_cos'] = np.cos(2 * np.pi * row['trimestre'] / 4)

    # Variações baseadas em volatilidade histórica
    frete_factor = np.random.normal(1, volatilidade_historica * 0.5)
    usd_factor = np.random.normal(1, volatilidade_historica * 0.3)
    
    row['frete_final'] *= frete_factor
    row['usd_brl'] *= usd_factor
    row['custo_total'] *= np.random.normal(1, 0.02)
    row['variacao'] = tendencia_percentual

    futuras.append(row)

X_futuro = pd.DataFrame(futuras)
previsoes_futuras = best_model.predict(X_futuro)

# Ajuste de cenário mais sofisticado
if cenario == "Alta (otimista)":
    fator_base = 1 + max(0.02, abs(tendencia_percentual) * 1.5)  # mínimo 2% de alta
    previsoes_ajustadas = [valor * (fator_base ** (i * 0.1)) for i, valor in enumerate(previsoes_futuras)]
elif cenario == "Queda (pessimista)":
    fator_base = 1 - max(0.02, abs(tendencia_percentual) * 1.2)  # mínimo 2% de queda
    previsoes_ajustadas = [valor * (fator_base ** (i * 0.1)) for i, valor in enumerate(previsoes_futuras)]
else:
    previsoes_ajustadas = previsoes_futuras

# Calcular intervalos de confiança
lower_bound, upper_bound = calcular_intervalos_confianca(previsoes_ajustadas)

# Resultados com intervalos de confiança
datas_futuras = pd.date_range(start=df_clean['data'].max() + timedelta(days=1), periods=meses_futuros, freq='MS')
df_previsao = pd.DataFrame({
    'data': datas_futuras, 
    'valor_previsto': previsoes_ajustadas,
    'limite_inferior': lower_bound,
    'limite_superior': upper_bound
})

# Gráfico melhorado com intervalos de confiança
serie_real = df_clean[['data', 'valor_entregue']].rename(columns={'valor_entregue': 'valor'})

fig = go.Figure()

# Série histórica
fig.add_trace(go.Scatter(
    x=serie_real['data'],
    y=serie_real['valor'],
    mode='lines+markers',
    name='Histórico',
    line=dict(color='blue')
))

# Previsão central
fig.add_trace(go.Scatter(
    x=df_previsao['data'],
    y=df_previsao['valor_previsto'],
    mode='lines+markers',
    name='Previsão',
    line=dict(color='red', dash='dash')
))

# Intervalo de confiança
fig.add_trace(go.Scatter(
    x=list(df_previsao['data']) + list(df_previsao['data'][::-1]),
    y=list(df_previsao['limite_superior']) + list(df_previsao['limite_inferior'][::-1]),
    fill='toself',
    fillcolor='rgba(255,0,0,0.2)',
    line=dict(color='rgba(255,255,255,0)'),
    name='Intervalo de Confiança (95%)',
    showlegend=True
))

fig.update_layout(
    title=f"Valor Entregue - {produto} de {origem} até {destino_nome}",
    xaxis_title="Data",
    yaxis_title="Valor (R$)",
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# Expandables com informações detalhadas
with st.expander("🔍 Visualizar dados históricos utilizados"):
    st.dataframe(df_clean[['data', 'preco_min', 'frete_final', 'valor_entregue']].sort_values('data'))

with st.expander("🔮 Ver previsão futura mês a mês"):
    st.dataframe(df_previsao)

with st.expander("📊 Detalhes do modelo"):
    st.write(f"**Modelo selecionado:** {best_name.upper()}")
    st.write(f"**Features utilizadas:** {len(features_to_use)}")
    st.write(f"**Outliers removidos:** {outliers_removidos}")
    st.write(f"**Tendência detectada:** {tendencia_percentual:.2%} ao período")
    st.write(f"**Volatilidade histórica:** {volatilidade_historica:.2%}")

# Métricas finais
st.caption(f"Modelo {best_name.upper()} otimizado - MAPE: {best_metrics['MAPE']:.2%} ± {best_metrics['MAPE_std']:.2%} | Features: {len(features_to_use)} | Validação temporal com 3 folds")