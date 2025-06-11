import streamlit as st
import os
import pandas as pd
import plotly.express as px
import sqlite3
from prophet import Prophet

# Deve ser o primeiro comando Streamlit
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

# Esconde o seletor de páginas padrão do Streamlit
hide_pages = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)

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

# CONTEÚDO DA PÁGINA
st.title("📈 Página de Previsões")
st.markdown("Esta seção está reservada para visualizações e modelos preditivos futuros.")

@st.cache_data
def carregar_dados():
    conn = sqlite3.connect("../morro_verde.db")
    df = pd.read_sql_query('''
        SELECT p.nome_produto AS produto, l.nome AS local, pr.data, pr.preco_min AS preco
        FROM precos pr
        JOIN produtos p ON pr.produto_id = p.id
        JOIN locais l ON pr.local_id = l.id
    ''', conn)
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

# Carregar dados
with st.spinner("Carregando dados..."):
    df = carregar_dados()

# Filtros
produto = st.selectbox("Selecione o Produto:", sorted(df['produto'].unique()))
local = st.selectbox("Selecione o Local:", sorted(df['local'].unique()))

# Filtrar dados
df_filt = df[(df['produto'] == produto) & (df['local'] == local)].sort_values('data')

if df_filt.shape[0] < 12:
    st.warning("⚠️ É necessário pelo menos 12 registros mensais para gerar uma previsão confiável.")
    st.dataframe(df_filt)
    st.stop()

# Preparar dados para o Prophet
df_prophet = df_filt[['data', 'preco']].copy()
df_prophet = df_prophet.rename(columns={'data': 'ds', 'preco': 'y'})
df_prophet = df_prophet.resample('MS', on='ds').mean(numeric_only=True).dropna().reset_index()

# Modelo Prophet
model = Prophet()
model.fit(df_prophet)

# Criar dataframe futuro para 6 meses
future = model.make_future_dataframe(periods=6, freq='MS')
forecast = model.predict(future)

# Dados de previsão para exibição
forecast_df = forecast[['ds', 'yhat']].tail(6)
forecast_df = forecast_df.rename(columns={'ds': 'data', 'yhat': 'previsao'})

# Gráfico
st.subheader(f"📊 Histórico + Previsão para {produto} em {local}")
fig = px.line(df_filt, x='data', y='preco', title="Histórico e Previsão de Preço")
fig.add_scatter(x=forecast_df['data'], y=forecast_df['previsao'], mode='lines+markers', name='Previsão')
fig.update_layout(margin=dict(t=50, b=20))
st.plotly_chart(fig, use_container_width=True)

# Mostrar dados
with st.expander("🔍 Visualizar dados utilizados"):
    st.dataframe(df_filt, use_container_width=True)

with st.expander("🔮 Ver previsão futura"):
    st.dataframe(forecast_df, use_container_width=True)
