import streamlit as st
import os
import pandas as pd
import plotly.express as px
import sqlite3
from sklearn.metrics import mean_absolute_percentage_error
from prophet import Prophet

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

hide_pages = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)

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
st.markdown("Escolha abaixo a categoria para gerar previsões com base nos dados do sistema.")

aba = st.radio("Escolha o que deseja prever:", ["Preço", "Frete", "Barter Ratio"])

@st.cache_data
def carregar_dados_preco():
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'morro_verde.db')
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT p.nome_produto AS produto, l.nome AS local, pr.data, pr.preco_min AS preco
        FROM precos pr
        JOIN produtos p ON pr.produto_id = p.id
        JOIN locais l ON pr.local_id = l.id
    """, conn)
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

@st.cache_data
def carregar_dados_frete():
    conn = sqlite3.connect("morro_verde.db")
    df = pd.read_sql_query("""
        SELECT l1.nome AS origem, l2.nome AS destino, f.tipo, f.data, f.custo_usd AS preco
        FROM fretes f
        JOIN locais l1 ON f.origem_id = l1.id
        JOIN locais l2 ON f.destino_id = l2.id
    """, conn)
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

@st.cache_data
def carregar_dados_barter():
    conn = sqlite3.connect("morro_verde.db")
    df = pd.read_sql_query("""
        SELECT b.cultura, p.nome_produto AS produto, b.estado, b.data, b.barter_ratio AS preco
        FROM barter_ratios b
        JOIN produtos p ON b.produto_id = p.id
    """, conn)
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

if aba == "Preço":
    df = carregar_dados_preco()
    produto = st.selectbox("Produto:", sorted(df['produto'].unique()))
    local = st.selectbox("Local:", sorted(df['local'].unique()))
    df_filt = df[(df['produto'] == produto) & (df['local'] == local)].sort_values('data')

elif aba == "Frete":
    df = carregar_dados_frete()
    origem = st.selectbox("Origem:", sorted(df['origem'].unique()))
    destino = st.selectbox("Destino:", sorted(df['destino'].unique()))
    tipo = st.selectbox("Tipo de Transporte:", sorted(df['tipo'].unique()))
    df_filt = df[(df['origem'] == origem) & (df['destino'] == destino) & (df['tipo'] == tipo)].sort_values('data')

elif aba == "Barter Ratio":
    df = carregar_dados_barter()
    cultura = st.selectbox("Cultura:", sorted(df['cultura'].unique()))
    estado = st.selectbox("Estado:", sorted(df['estado'].unique()))
    produto = st.selectbox("Produto:", sorted(df['produto'].unique()))
    df_filt = df[(df['cultura'] == cultura) & (df['estado'] == estado) & (df['produto'] == produto)].sort_values('data')

if df_filt.shape[0] < 12:
    st.warning("⚠️ É necessário pelo menos 12 registros mensais para gerar uma previsão confiável.")
    st.dataframe(df_filt)
    st.stop()

serie = df_filt.set_index('data')[['preco']].resample('MS').mean().dropna()
serie = serie.reset_index().rename(columns={"data": "ds", "preco": "y"})

# Escolha do número de meses futuros
num_meses = st.slider("Quantos meses futuros deseja prever?", min_value=3, max_value=12, value=6)

# Separar para avaliar acurácia
train = serie[:-6]
test = serie[-6:]

modelo = Prophet()
modelo.fit(train)
future_test = modelo.make_future_dataframe(periods=6, freq='MS')
forecast_test = modelo.predict(future_test)
forecast_test = forecast_test[['ds', 'yhat']].set_index('ds')

mape = mean_absolute_percentage_error(test.set_index('ds')['y'], forecast_test[-6:]['yhat'])
print(f"[DEBUG] MAPE (erro percentual médio): {mape:.2%}")

# Previsão final com todos os dados
modelo_final = Prophet()
modelo_final.fit(serie)
future_final = modelo_final.make_future_dataframe(periods=num_meses, freq='MS')
forecast_final = modelo_final.predict(future_final)
forecast_df = forecast_final[['ds', 'yhat']].tail(num_meses).rename(columns={'ds': 'data', 'yhat': 'previsao'})

titulo = (
    f"{produto} em {local}" if aba == "Preço" else
    f"{origem} → {destino} ({tipo})" if aba == "Frete" else
    f"{cultura} - {produto} ({estado})"
)

st.subheader("📊 Histórico + Previsão")
fig = px.line(serie, x='ds', y='y', title=titulo)
fig.add_scatter(x=forecast_df['data'], y=forecast_df['previsao'], mode='lines+markers', name='Previsão')
fig.update_layout(margin=dict(t=50, b=20))
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Visualizar dados utilizados"):
    st.dataframe(serie.rename(columns={'ds': 'data', 'y': 'preco'}))

with st.expander("🔮 Ver previsão futura"):
    st.dataframe(forecast_df)
