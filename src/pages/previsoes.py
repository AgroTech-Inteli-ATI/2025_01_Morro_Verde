import streamlit as st
import os

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
st.info("🚧 Em construção. Em breve você verá aqui gráficos e análises de previsão.")
