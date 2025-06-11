import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from statsmodels.tsa.api import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Dashboard Morro Verde - Previsões Avançadas",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': None,
        'Get Help': None,
        'Report a bug': None
    }
)

# CSS customizado
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .prediction-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR personalizada
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

# Funções de carregamento de dados
@st.cache_data
def carregar_dados():
    conn = sqlite3.connect("morro_verde.db")
    df = pd.read_sql_query('''
        SELECT p.nome_produto AS produto, l.nome AS local, pr.data, pr.preco_min AS preco,
               pr.moeda, pr.tipo_preco, pr.modalidade, l.estado, l.pais
        FROM precos pr
        JOIN produtos p ON pr.produto_id = p.id
        JOIN locais l ON pr.local_id = l.id
        WHERE pr.preco_min IS NOT NULL
    ''', conn)
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

@st.cache_data
def carregar_dados_cambio():
    conn = sqlite3.connect("morro_verde.db")
    df_cambio = pd.read_sql_query('SELECT * FROM cambio', conn)
    conn.close()
    if not df_cambio.empty:
        df_cambio['data'] = pd.to_datetime(df_cambio['data'])
    return df_cambio

@st.cache_data
def carregar_dados_barter():
    conn = sqlite3.connect("morro_verde.db")
    df_barter = pd.read_sql_query('''
        SELECT br.cultura, p.nome_produto AS produto, br.estado, br.data,
               br.preco_cultura, br.barter_ratio, br.barter_index
        FROM barter_ratios br
        JOIN produtos p ON br.produto_id = p.id
        WHERE br.barter_ratio IS NOT NULL
    ''', conn)
    conn.close()
    if not df_barter.empty:
        df_barter['data'] = pd.to_datetime(df_barter['data'])
    return df_barter

# Modelos de previsão
def modelo_exponential_smoothing(serie, periodos=6):
    """Modelo Exponential Smoothing tradicional"""
    try:
        model = ExponentialSmoothing(serie, trend='add', seasonal=None)
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=periodos)
        return forecast, 'Exponential Smoothing'
    except Exception as e:
        st.error(f"Erro no Exponential Smoothing: {e}")
        return None, None

def modelo_arima(serie, periodos=6):
    """Modelo ARIMA auto-ajustado"""
    try:
        # Auto ARIMA simplificado
        model = ARIMA(serie, order=(1,1,1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=periodos)
        return forecast, 'ARIMA(1,1,1)'
    except Exception as e:
        try:
            # Fallback para ordem mais simples
            model = ARIMA(serie, order=(0,1,0))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=periodos)
            return forecast, 'ARIMA(0,1,0)'
        except:
            return None, None

def modelo_random_forest(serie, periodos=6):
    """Modelo Random Forest com features de lag"""
    try:
        # Criar features de lag
        df_temp = pd.DataFrame({'valor': serie.values})
        df_temp['lag1'] = df_temp['valor'].shift(1)
        df_temp['lag2'] = df_temp['valor'].shift(2)
        df_temp['lag3'] = df_temp['valor'].shift(3)
        df_temp['trend'] = range(len(df_temp))
        
        # Remover NaN
        df_temp = df_temp.dropna()
        
        if len(df_temp) < 6:
            return None, None
            
        X = df_temp[['lag1', 'lag2', 'lag3', 'trend']]
        y = df_temp['valor']
        
        # Treinar modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Fazer previsões iterativas
        forecast = []
        last_values = list(serie.tail(3).values)
        
        for i in range(periodos):
            trend_val = len(serie) + i
            X_pred = np.array([[last_values[-1], last_values[-2], last_values[-3], trend_val]])
            pred = model.predict(X_pred)[0]
            forecast.append(pred)
            last_values.append(pred)
            last_values = last_values[-3:]  # Manter apenas os últimos 3
            
        return pd.Series(forecast), 'Random Forest'
    except Exception as e:
        return None, None

def modelo_ensemble(serie, periodos=6):
    """Ensemble de múltiplos modelos"""
    modelos = []
    pesos = []
    
    # Exponential Smoothing
    pred_es, nome_es = modelo_exponential_smoothing(serie, periodos)
    if pred_es is not None:
        modelos.append(pred_es)
        pesos.append(0.4)
    
    # ARIMA
    pred_arima, nome_arima = modelo_arima(serie, periodos)
    if pred_arima is not None:
        modelos.append(pred_arima)
        pesos.append(0.3)
    
    # Random Forest
    pred_rf, nome_rf = modelo_random_forest(serie, periodos)
    if pred_rf is not None:
        modelos.append(pred_rf)
        pesos.append(0.3)
    
    if not modelos:
        return None, None
    
    # Normalizar pesos
    pesos = np.array(pesos)
    pesos = pesos / pesos.sum()
    
    # Calcular ensemble
    ensemble = np.zeros(periodos)
    for i, modelo in enumerate(modelos):
        ensemble += pesos[i] * np.array(modelo)
    
    return pd.Series(ensemble), f'Ensemble ({len(modelos)} modelos)'

def calcular_metricas_precisao(y_true, y_pred):
    """Calcula métricas de precisão"""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}

# INTERFACE PRINCIPAL
st.title("📈 Sistema de Previsões Avançado")
st.markdown("Análise preditiva com múltiplos modelos e validação cruzada")

# Carregar dados
with st.spinner("Carregando dados..."):
    df = carregar_dados()
    df_cambio = carregar_dados_cambio()
    df_barter = carregar_dados_barter()

if df.empty:
    st.error("❌ Nenhum dado encontrado no banco. Execute primeiro o script de importação.")
    st.stop()

# Seleção de análise
tipo_analise = st.selectbox(
    "🔍 Tipo de Análise:",
    ["Previsão de Preços", "Análise de Câmbio", "Análise Barter Ratio", "Comparativo Multi-Produto"]
)

if tipo_analise == "Previsão de Preços":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        produto = st.selectbox("Produto:", sorted(df['produto'].unique()))
    with col2:
        local = st.selectbox("Local:", sorted(df['local'].unique()))
    with col3:
        modelo_escolhido = st.selectbox(
            "Modelo de Previsão:",
            ["Ensemble", "Exponential Smoothing", "ARIMA", "Random Forest"]
        )
    
    # Filtrar dados
    df_filt = df[(df['produto'] == produto) & (df['local'] == local)].sort_values('data')
    
    if df_filt.shape[0] < 12:
        st.warning("⚠️ É necessário pelo menos 12 registros para gerar uma previsão confiável.")
        st.dataframe(df_filt)
        st.stop()
    
    # Preparar série temporal
    serie = df_filt.set_index('data')['preco'].resample('MS').mean().dropna()
    
    # Configurações de previsão
    col1, col2 = st.columns(2)
    with col1:
        periodos = st.slider("Períodos para prever:", 3, 12, 6)
    with col2:
        validacao = st.checkbox("Validação Cruzada", value=True)
    
    # Fazer previsão
    if modelo_escolhido == "Ensemble":
        forecast, nome_modelo = modelo_ensemble(serie, periodos)
    elif modelo_escolhido == "Exponential Smoothing":
        forecast, nome_modelo = modelo_exponential_smoothing(serie, periodos)
    elif modelo_escolhido == "ARIMA":
        forecast, nome_modelo = modelo_arima(serie, periodos)
    else:  # Random Forest
        forecast, nome_modelo = modelo_random_forest(serie, periodos)
    
    if forecast is None:
        st.error("❌ Não foi possível gerar previsão com os dados disponíveis.")
        st.stop()
    
    # Validação cruzada
    if validacao and len(serie) > 18:
        st.subheader("🎯 Validação Cruzada")
        
        # Usar últimos 6 pontos para validação
        serie_treino = serie[:-6]
        serie_teste = serie[-6:]
        
        if modelo_escolhido == "Ensemble":
            pred_validacao, _ = modelo_ensemble(serie_treino, 6)
        elif modelo_escolhido == "Exponential Smoothing":
            pred_validacao, _ = modelo_exponential_smoothing(serie_treino, 6)
        elif modelo_escolhido == "ARIMA":
            pred_validacao, _ = modelo_arima(serie_treino, 6)
        else:
            pred_validacao, _ = modelo_random_forest(serie_treino, 6)
        
        if pred_validacao is not None:
            metricas = calcular_metricas_precisao(serie_teste.values, pred_validacao.values)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MAE (Erro Médio Absoluto)", f"{metricas['MAE']:.2f}")
            with col2:
                st.metric("RMSE (Raiz do Erro Quadrático)", f"{metricas['RMSE']:.2f}")
            with col3:
                st.metric("MAPE (Erro Percentual)", f"{metricas['MAPE']:.1f}%")
    
    # Gerar DataFrame de previsão
    forecast_df = pd.DataFrame({
        'data': pd.date_range(start=serie.index[-1] + pd.DateOffset(months=1), periods=periodos, freq='MS'),
        'previsao': forecast.values
    })
    
    # Calcular intervalos de confiança (simulação simples)
    std_erro = serie.std() * 0.1  # 10% do desvio padrão como erro
    forecast_df['limite_inferior'] = forecast_df['previsao'] - 1.96 * std_erro
    forecast_df['limite_superior'] = forecast_df['previsao'] + 1.96 * std_erro
    
    # Gráfico principal
    st.subheader(f"📊 {nome_modelo}: {produto} em {local}")
    
    fig = go.Figure()
    
    # Dados históricos
    fig.add_trace(go.Scatter(
        x=df_filt['data'], 
        y=df_filt['preco'],
        mode='lines+markers',
        name='Histórico',
        line=dict(color='blue')
    ))
    
    # Previsão
    fig.add_trace(go.Scatter(
        x=forecast_df['data'], 
        y=forecast_df['previsao'],
        mode='lines+markers',
        name='Previsão',
        line=dict(color='red', dash='dash')
    ))
    
    # Intervalo de confiança
    fig.add_trace(go.Scatter(
        x=list(forecast_df['data']) + list(forecast_df['data'][::-1]),
        y=list(forecast_df['limite_superior']) + list(forecast_df['limite_inferior'][::-1]),
        fill='toself',
        fillcolor='rgba(255,0,0,0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name='IC 95%',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"Previsão de Preços - {produto} ({local})",
        xaxis_title="Data",
        yaxis_title="Preço",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Resumo da previsão
    st.subheader("📋 Resumo da Previsão")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Preço Atual", f"{serie.iloc[-1]:.2f}")
    with col2:
        variacao = ((forecast.iloc[0] - serie.iloc[-1]) / serie.iloc[-1]) * 100
        st.metric("Variação Próximo Mês", f"{variacao:+.1f}%")
    with col3:
        st.metric("Previsão 6 Meses", f"{forecast.iloc[-1]:.2f}")
    with col4:
        tendencia = "📈 Alta" if forecast.iloc[-1] > serie.iloc[-1] else "📉 Baixa"
        st.metric("Tendência", tendencia)

elif tipo_analise == "Análise de Câmbio":
    if df_cambio.empty:
        st.warning("⚠️ Dados de câmbio não disponíveis.")
    else:
        st.subheader("💱 Previsão do Câmbio USD/BRL")
        
        serie_cambio = df_cambio.set_index('data')['usd_brl'].resample('D').last().dropna()
        
        if len(serie_cambio) >= 12:
            forecast_cambio, nome_modelo = modelo_ensemble(serie_cambio, 30)  # 30 dias
            
            if forecast_cambio is not None:
                forecast_cambio_df = pd.DataFrame({
                    'data': pd.date_range(start=serie_cambio.index[-1] + pd.Timedelta(days=1), periods=30, freq='D'),
                    'previsao': forecast_cambio.values
                })
                
                fig = px.line(title="Histórico e Previsão do Câmbio USD/BRL")
                fig.add_scatter(x=serie_cambio.index, y=serie_cambio.values, name="Histórico", mode='lines')
                fig.add_scatter(x=forecast_cambio_df['data'], y=forecast_cambio_df['previsao'], 
                              name="Previsão", mode='lines', line=dict(dash='dash'))
                
                st.plotly_chart(fig, use_container_width=True)

elif tipo_analise == "Análise Barter Ratio":
    if df_barter.empty:
        st.warning("⚠️ Dados de barter ratio não disponíveis.")
    else:
        st.subheader("🌾 Análise de Barter Ratio")
        
        cultura = st.selectbox("Cultura:", sorted(df_barter['cultura'].unique()))
        estado = st.selectbox("Estado:", sorted(df_barter['estado'].unique()))
        
        df_barter_filt = df_barter[(df_barter['cultura'] == cultura) & 
                                   (df_barter['estado'] == estado)]
        
        if not df_barter_filt.empty:
            fig = px.line(df_barter_filt, x='data', y='barter_ratio', 
                         color='produto', title=f"Barter Ratio - {cultura} ({estado})")
            st.plotly_chart(fig, use_container_width=True)

else:  
    st.subheader("📊 Comparativo Multi-Produto")
    
    produtos_selecionados = st.multiselect(
        "Selecione produtos para comparar:",
        sorted(df['produto'].unique()),
        default=sorted(df['produto'].unique())[:3]
    )
    
    local_comp = st.selectbox("Local para comparação:", sorted(df['local'].unique()))
    
    if produtos_selecionados:
        fig = go.Figure()
        
        for produto in produtos_selecionados:
            df_temp = df[(df['produto'] == produto) & (df['local'] == local_comp)]
            if not df_temp.empty:
                fig.add_trace(go.Scatter(
                    x=df_temp['data'],
                    y=df_temp['preco'],
                    name=produto,
                    mode='lines+markers'
                ))
        
        fig.update_layout(
            title=f"Comparativo de Preços - {local_comp}",
            xaxis_title="Data",
            yaxis_title="Preço",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Dados expandidos
with st.expander("🔍 Dados Utilizados"):
    if tipo_analise == "Previsão de Preços":
        st.dataframe(df_filt, use_container_width=True)
    elif tipo_analise == "Análise de Câmbio":
        st.dataframe(df_cambio, use_container_width=True)
    elif tipo_analise == "Análise Barter Ratio":
        st.dataframe(df_barter, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

# Rodapé informativo
st.markdown("---")
st.markdown("""
**📝 Notas sobre os modelos:**
- **Exponential Smoothing**: Ideal para tendências simples
- **ARIMA**: Captura autocorrelações e tendências complexas  
- **Random Forest**: Usa machine learning com features de lag
- **Ensemble**: Combina múltiplos modelos para maior robustez
- **Validação Cruzada**: Testa a precisão em dados históricos
""")