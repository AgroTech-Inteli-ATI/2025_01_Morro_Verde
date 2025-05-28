import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from processar_relatorio import processar_relatorio
import threading  
import time        
from streamlit_autorefresh import st_autorefresh


DB_PATH = 'morro_verde.db'
logo_path = "img/logo-morro-verde.png"

def criar_conexao():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def carregar_dados():
    conn = criar_conexao()
    df_precos = pd.read_sql_query('''
        SELECT p.nome_produto AS produto, l.nome AS localizacao, pr.data AS data_preco, pr.preco_min AS preco, pr.moeda
        FROM precos pr
        JOIN produtos p ON p.id = pr.produto_id
        JOIN locais l ON l.id = pr.local_id
    ''', conn)

    df_fretes = pd.read_sql_query('''
        SELECT l1.nome AS origem, l2.nome AS destino, f.tipo AS tipo_transporte, f.custo_usd AS preco, "USD" AS moeda, f.data
        FROM fretes f
        JOIN locais l1 ON f.origem_id = l1.id
        JOIN locais l2 ON f.destino_id = l2.id
    ''', conn)

    df_barter = pd.read_sql_query('''
        SELECT cultura, produto_id, estado, data, preco_cultura, barter_ratio AS razao_barter
        FROM barter_ratios
    ''', conn)

    conn.close()
    return df_precos, df_fretes, df_barter

# Configuração da página
st.set_page_config(page_title="Dashboard Morro Verde", layout="wide")


# Função para processar relatório em uma thread separada
def threaded_processar_relatorio(caminho_pdf, num_partes):
    st.session_state.relatorio_em_processamento = True
    st.session_state.progresso_relatorio = 0

    def atualizar_progresso(p):
        st.session_state.progresso_relatorio = p

    try:
        processar_relatorio(
            caminho_pdf,
            callback_progresso=atualizar_progresso,
            num_partes=num_partes  # <- passe aqui
        )
    finally:
        st.session_state.relatorio_em_processamento = False
        st.session_state.progresso_relatorio = 100


# Sidebar
with st.sidebar:
    st.image(logo_path, use_container_width=True)
    st.markdown("---")
    st.button("Página Inicial")
    st.button("Previsões")

st.title("DASHBOARD - Análise de Concorrência")

# Botões principais
col1, col2, col3 = st.columns([1,1,1])

with col1:
    filtrar_click = st.button("🔍 FILTRAR DADOS")

with col2:
    num_partes = st.slider("Dividir relatório em quantas partes?", 1, 15, 10)

    uploaded_file = st.file_uploader("Selecione o arquivo PDF do relatório", type=["pdf"], key="upload")
    if st.button("📥 IMPORTAR RELATÓRIO") and uploaded_file is not None:
        caminho_pdf = "relatorios/relatorio_temp.pdf"
        with open(caminho_pdf, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Inicia o processamento com número de partes ajustável
        thread = threading.Thread(target=threaded_processar_relatorio, args=(caminho_pdf, num_partes))
        thread.start()

with col3:
    st.button("📝 INPUTAR DADOS")

# Atualiza a cada 1 segundo enquanto estiver processando
if st.session_state.get("relatorio_em_processamento", False):
    st_autorefresh(interval=1000, key="auto_refresh")

# STATUS DO PROCESSAMENTO
with st.container():
    progresso = st.session_state.get("progresso_relatorio", 0)

    if st.session_state.get("relatorio_em_processamento", False):
        st.info("⏳ Relatório está sendo processado... aguarde.")
        st.progress(progresso)

    elif progresso == 100:
        st.success("✅ Relatório processado com sucesso! Os dados já estão no banco.")
        if st.button("🔄 Atualizar dados do dashboard"):
            st.rerun()

    else:
        st.success("✅ Nenhum relatório em processamento no momento.")


# Carregar dados do banco
df_precos, df_fretes, df_barter = carregar_dados()
df_precos['data_preco'] = pd.to_datetime(df_precos['data_preco'])
df_precos['preco'] = pd.to_numeric(df_precos['preco'], errors='coerce')
df_barter['data'] = pd.to_datetime(df_barter['data'])
df_barter['preco_cultura'] = pd.to_numeric(df_barter['preco_cultura'], errors='coerce')
df_barter['razao_barter'] = pd.to_numeric(df_barter['razao_barter'], errors='coerce')

# Filtros padrão para aplicar quando botão não clicado
filtro_produto = df_precos['produto'].unique()
filtro_local = df_precos['localizacao'].unique()
filtro_moeda = df_precos['moeda'].unique()
data_min = df_precos['data_preco'].min().date() if not pd.isna(df_precos['data_preco'].min()) else datetime.today().date()
data_max = df_precos['data_preco'].max().date() if not pd.isna(df_precos['data_preco'].max()) else datetime.today().date()
filtro_data = [data_min, data_max]

# Mostrar filtros avançados dentro do botão "FILTRAR DADOS"
if filtrar_click:
    with st.expander("Filtros avançados", expanded=True):
        filtro_produto = st.multiselect("Filtrar por Produto(s):", options=df_precos['produto'].unique(), default=filtro_produto)
        filtro_local = st.multiselect("Filtrar por Localização(s):", options=df_precos['localizacao'].unique(), default=filtro_local)
        filtro_moeda = st.multiselect("Filtrar por Moeda(s):", options=df_precos['moeda'].unique(), default=filtro_moeda)
        filtro_data = st.date_input(
            "Selecionar intervalo de datas:",
            [data_min, data_max],
            min_value=data_min,
            max_value=data_max
        )

# Aplicar filtros nos dados
df_precos_filt = df_precos[
    (df_precos['produto'].isin(filtro_produto)) &
    (df_precos['localizacao'].isin(filtro_local)) &
    (df_precos['moeda'].isin(filtro_moeda)) &
    (df_precos['data_preco'] >= pd.to_datetime(filtro_data[0])) &
    (df_precos['data_preco'] <= pd.to_datetime(filtro_data[1]))
]

# KPIs
st.subheader("📊 Indicadores Principais")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Produtos únicos", df_precos_filt['produto'].nunique())
kpi2.metric("Locais únicos", df_precos_filt['localizacao'].nunique())
kpi3.metric("Registros de preço", len(df_precos_filt))
kpi4.metric("Registros de permuta", len(df_barter))

# Gráfico histórico de preços
st.subheader("📈 Histórico de Preços")
fig_preco = px.line(
    df_precos_filt.sort_values('data_preco'),
    x='data_preco',
    y='preco',
    color='produto',
    line_dash='localizacao',
    markers=True,
    title="Evolução dos preços por produto e localização"
)
fig_preco.update_layout(margin=dict(t=50, b=20))
st.plotly_chart(fig_preco, use_container_width=True)

# Variação percentual mensal
st.subheader("📊 Variação Percentual Mensal dos Preços")
df_precos_filt['ano_mes'] = df_precos_filt['data_preco'].dt.to_period('M')
df_pct = df_precos_filt.groupby(['produto', 'ano_mes']).preco.mean().reset_index()
df_pct['ano_mes'] = df_pct['ano_mes'].dt.to_timestamp()
df_pct['pct_var'] = df_pct.groupby('produto')['preco'].pct_change() * 100

fig_pct = px.line(
    df_pct,
    x='ano_mes',
    y='pct_var',
    color='produto',
    title="Variação percentual média mensal por produto"
)
fig_pct.update_layout(margin=dict(t=50, b=20))
st.plotly_chart(fig_pct, use_container_width=True)

# Dispersão preço x data (outliers)
st.subheader("🔍 Dispersão Preço x Data")
fig_disp = px.scatter(
    df_precos_filt,
    x='data_preco',
    y='preco',
    color='produto',
    hover_data=['localizacao', 'moeda'],
    title="Dispersão dos preços ao longo do tempo"
)
fig_disp.update_layout(margin=dict(t=50, b=20))
st.plotly_chart(fig_disp, use_container_width=True)

# Variação de Preço ao Longo do Tempo por Local
st.subheader("📈 Variação de Preço ao Longo do Tempo por Localização")

# Agrupar por data e local, calculando a média de preço
preco_por_local_data = df_precos_filt.groupby(['data_preco', 'localizacao'])['preco'].mean().reset_index()

# Criar o gráfico de linha
fig_linha_local = px.line(
    preco_por_local_data,
    x='data_preco',
    y='preco',
    color='localizacao',
    markers=True,
    title='Evolução do Preço por Localização ao Longo do Tempo'
)

fig_linha_local.update_layout(margin=dict(t=50, b=20))
st.plotly_chart(fig_linha_local, use_container_width=True)

# Distribuição preço médio por produto
st.subheader("📊 Distribuição do Preço Médio por Produto")
preco_medio_produto = df_precos_filt.groupby('produto')['preco'].mean().reset_index()
fig_pie = px.pie(preco_medio_produto, names='produto', values='preco', title='Distribuição de Preço Médio por Produto')
st.plotly_chart(fig_pie, use_container_width=True)

# Dashboard Fretes
st.subheader("🚛 Análise Detalhada de Custos Logísticos (Fretes)")
if not df_fretes.empty:
    df_fretes_agrup = df_fretes.groupby(['origem', 'destino', 'tipo_transporte']).agg({'preco':'mean', 'data':'count'}).reset_index()
    df_fretes_agrup.rename(columns={'data':'volume'}, inplace=True)
    fig_fretes = px.scatter(
        df_fretes_agrup,
        x='origem',
        y='destino',
        size='volume',
        color='tipo_transporte',
        hover_name='tipo_transporte',
        title="Volume e Preço Médio dos Fretes por Rota"
    )
    st.plotly_chart(fig_fretes, use_container_width=True)
else:
    st.info("Nenhum dado de fretes disponível para exibir.")

# Análise Sazonal (com checagem de tamanho da série)
st.subheader("📅 Análise Sazonal dos Preços")

try:
    import statsmodels.api as sm

    ts_data = df_precos_filt.copy()
    ts_data['ano_mes'] = ts_data['data_preco'].dt.to_period('M')
    ts_data = ts_data.groupby('ano_mes')['preco'].mean()
    ts_data = ts_data.dropna()
    ts_data.index = ts_data.index.to_timestamp()

    if len(ts_data) >= 24:
        decomposition = sm.tsa.seasonal_decompose(ts_data, model='additive', period=12)
        fig_seasonal = go.Figure()
        fig_seasonal.add_trace(go.Scatter(
            x=decomposition.seasonal.index,
            y=decomposition.seasonal.values,
            mode='lines',
            name='Sazonal'
        ))
        fig_seasonal.update_layout(title='Componente Sazonal dos Preços Médios', margin=dict(t=50, b=20))
        st.plotly_chart(fig_seasonal, use_container_width=True)
    else:
        st.info(f"A série temporal precisa de pelo menos 24 meses para análise sazonal. Atualmente possui {len(ts_data)}.")

except Exception as e:
    st.warning(f"Erro na análise sazonal: {e}")



# Alertas automáticos
st.subheader("⚠️ Alertas Automáticos")

try:
    df_precos_filt['pct_change'] = df_precos_filt.groupby(['produto', 'localizacao'])['preco'].pct_change(fill_method=None) * 100
    alertas = df_precos_filt[(df_precos_filt['pct_change'].abs() > 10)]

    if not alertas.empty:
        for _, row in alertas.iterrows():
            st.warning(f"Alerta: {row['produto']} em {row['localizacao']} teve variação de {row['pct_change']:.2f}% em {row['data_preco'].date()}")
    else:
        st.info("Nenhum alerta de variação significativa detectado.")
except Exception as e:
    st.warning(f"Erro ao gerar alertas: {e}")

# Tabela de fretes
st.subheader("🚚 Tabela de Fretes Atuais")
st.dataframe(df_fretes.sort_values("data", ascending=False).head(10))