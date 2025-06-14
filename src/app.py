import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from processar_relatorio import processar_relatorio
import threading  
import time        
from streamlit_autorefresh import st_autorefresh
from database_utils import salvar_preco_manual, salvar_frete_manual
import os
from uuid import uuid4  # coloque no início do arquivo, se ainda não estiver
import threading
import json
import shutil
import statsmodels.api as sm
import glob

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

def ler_progresso_do_arquivo():
    try:
        with open("progresso.json", "r") as f:
            data = json.load(f)
            return data.get("progresso", 0), data.get("mensagem", "")
    except:
        return 0, ""

# Variável global segura para progresso
progresso_compartilhado = {"valor": 0}
progresso_lock = threading.Lock()

def atualizar_progresso_seguro(p):
    with progresso_lock:
        progresso_compartilhado["valor"] = p



# Esconde o seletor de páginas padrão
hide_pages = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_pages, unsafe_allow_html=True)


DB_PATH = os.path.join(os.path.dirname(__file__), 'morro_verde.db')
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

def criar_backup(max_backups=5):
    os.makedirs("backups", exist_ok=True)

    # 1. Descobre o próximo número
    i = 1
    while os.path.exists(f"backups/backup_rollback_{i}.db"):
        i += 1

    # 2. Cria novo backup
    shutil.copy(DB_PATH, f"backups/backup_rollback_{i}.db")

    # 3. Limpa backups antigos, mantém os `max_backups` mais recentes
    backups = sorted(
        glob.glob("backups/backup_rollback_*.db"),
        key=lambda x: int(x.split("_")[-1].split(".")[0])
    )

    while len(backups) > max_backups:
        os.remove(backups[0])
        backups.pop(0)


def restaurar_backup_mais_recente():
    backups = sorted(
        glob.glob("backups/backup_rollback_*.db"),
        key=lambda x: int(x.split("_")[-1].split(".")[0])
    )

    if not backups:
        return False

    # Restaura o mais recente
    mais_recente = backups[-1]
    shutil.copy(mais_recente, DB_PATH)
    os.remove(mais_recente)
    return True


def registrar_acao(descricao):
    log = []
    if os.path.exists("acoes_realizadas.json"):
        with open("acoes_realizadas.json", "r") as f:
            log = json.load(f)
    log.append(descricao)
    with open("acoes_realizadas.json", "w") as f:
        json.dump(log, f)


# Inicializar session state
if 'filtros_aplicados' not in st.session_state:
    st.session_state.filtros_aplicados = False
if 'mostrar_filtros' not in st.session_state:
    st.session_state.mostrar_filtros = False
if 'dados_inseridos' not in st.session_state:
    st.session_state.dados_inseridos = False
if 'relatorio_em_processamento' not in st.session_state:
    st.session_state.relatorio_em_processamento = False
if 'progresso_relatorio' not in st.session_state:
    st.session_state.progresso_relatorio = 0
if 'processamento_concluido' not in st.session_state:
    st.session_state.processamento_concluido = False
if 'erro_processamento' not in st.session_state:
    st.session_state.erro_processamento = None

def threaded_processar_relatorio(caminho_pdf, num_partes):
    # Marca que o processamento começou
    st.session_state.relatorio_em_processamento = True
    st.session_state.processamento_concluido = False
    st.session_state.erro_processamento = None
    st.session_state.progresso_relatorio = 0

    def executar_processamento():
        try:
            # Função principal de processamento, com callback para progresso
            def progresso_callback(p):
                st.session_state.progresso_relatorio = p

            processar_relatorio(
                caminho_pdf,
                callback_progresso=progresso_callback,
                num_partes=num_partes
            )

            st.session_state.processamento_concluido = True
        except Exception as e:
            st.session_state.erro_processamento = str(e)
        finally:
            st.session_state.relatorio_em_processamento = False
            st.session_state.progresso_relatorio = 100  # Garante que a barra encha visualmente

    # Executa o processamento em thread
    thread = threading.Thread(target=executar_processamento)
    thread.start()


# Função para input manual de dados
def mostrar_formulario_input():
    st.subheader("📝 Inserir Dados Manualmente")
    
    with st.form("input_dados"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💰 Dados de Preços**")
            produto = st.text_input("Nome do Produto *", placeholder="Ex: Soja, Milho, Trigo")
            localizacao = st.text_input("Localização *", placeholder="Ex: Porto de Santos, Chicago")
            preco = st.number_input("Preço *", min_value=0.0, step=0.01, format="%.2f")
            moeda = st.selectbox("Moeda *", ["USD", "BRL", "EUR"])
            data_preco = st.date_input("Data do Preço", value=datetime.today())
        
        with col2:
            st.markdown("**🚛 Dados de Frete**")
            origem = st.text_input("Origem", placeholder="Ex: São Paulo")
            destino = st.text_input("Destino", placeholder="Ex: Porto de Santos")
            tipo_transporte = st.selectbox("Tipo de Transporte", ["Rodoviário", "Ferroviário", "Marítimo"])
            custo_frete = st.number_input("Custo do Frete (USD)", min_value=0.0, step=0.01, format="%.2f")
            data_frete = st.date_input("Data do Frete", value=datetime.today())
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted_preco = st.form_submit_button("💾 Salvar Apenas Preço", use_container_width=True)
        with col_btn2:
            submitted_completo = st.form_submit_button("💾 Salvar Preço + Frete", use_container_width=True)
        
        # Processamento dos dados
        if submitted_preco or submitted_completo:
            # Validação dos campos obrigatórios para preço
            if not produto or not localizacao or preco <= 0:
                st.error("❌ Preencha todos os campos obrigatórios de preço: Produto, Localização e Preço > 0")
                return
            
            criar_backup()

            # Salvar preço
            sucesso_preco, msg_preco = salvar_preco_manual(produto, localizacao, preco, moeda, data_preco)

            if submitted_completo:
                # Validação para frete também
                if not origem or not destino or custo_frete <= 0:
                    st.error("❌ Para salvar frete também, preencha: Origem, Destino e Custo > 0")
                    return

                sucesso_frete, msg_frete = salvar_frete_manual(origem, destino, custo_frete, "USD", data_frete)

                if sucesso_preco and sucesso_frete:
                    st.success("✅ Preço e Frete salvos com sucesso!")
                    registrar_acao("✍️ Novo dado inputado manualmente: preço e frete.")
                else:
                    if not sucesso_preco:
                        st.error(f"❌ Erro ao salvar preço: {msg_preco}")
                    if not sucesso_frete:
                        st.error(f"❌ Erro ao salvar frete: {msg_frete}")
            else:
                if sucesso_preco:
                    st.success("✅ Preço salvo com sucesso!")
                    registrar_acao("✍️ Novo dado inputado manualmente: apenas preço.")
                else:
                    st.error(f"❌ Erro ao salvar preço: {msg_preco}")


            time.sleep(2)
            st.rerun()

# Sidebar
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
    
    # Indicador de status
    st.markdown("---")
    st.markdown("**📊 Status do Sistema**")
    
    try:
        df_precos, df_fretes, df_barter = carregar_dados()
        st.metric("Registros de Preços", len(df_precos))
        st.metric("Registros de Fretes", len(df_fretes))
        st.metric("Registros de Barter", len(df_barter))
    except:
        st.error("❌ Erro ao conectar com banco")

st.title("📊 DASHBOARD - Análise de Concorrência")
st.markdown("**Sistema de monitoramento de preços e logística agrícola**")

# Botões principais
col1, col2, col3 = st.columns([1,1,1])

with col1:
    if st.button("🔍 FILTRAR DADOS", use_container_width=True):
        st.session_state.mostrar_filtros = not st.session_state.mostrar_filtros
        st.rerun()

with col2:
    st.markdown("**📥 Importar Relatório PDF**")
    
    col2a, col2b = st.columns([3, 1])
    with col2a:
        uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"], key="upload")
    with col2b:
        num_partes = st.slider("Partes", 1, 15, 10, help="Dividir relatório em quantas partes?")

    if st.button("📥 IMPORTAR RELATÓRIO", use_container_width=True) and uploaded_file is not None:
        os.makedirs("relatorios", exist_ok=True)
        caminho_pdf = "relatorios/relatorio_temp.pdf"
        
        with open(caminho_pdf, "wb") as f:
            f.write(uploaded_file.getbuffer())

        criar_backup()  # Cria backup antes de processar
        registrar_acao(f"📄 {uploaded_file.name} importado!")

        # 🔄 Limpa o progresso anterior (caso exista)
        if os.path.exists("progresso.json"):
            os.remove("progresso.json")

        # Sempre crie nova thread ao importar, mesmo que seja o mesmo arquivo
        nova_thread = threading.Thread(target=threaded_processar_relatorio, args=(caminho_pdf, num_partes))
        nova_thread.start()

        # ⚠️ Atualize o session_state corretamente
        st.session_state.relatorio_em_processamento = True
        st.session_state.processamento_concluido = False
        st.session_state.erro_processamento = None
        st.session_state.progresso_relatorio = 0
        st.session_state.thread = nova_thread


with col3:
    if st.button("📝 INPUTAR DADOS", use_container_width=True):
        st.session_state.dados_inseridos = not st.session_state.dados_inseridos
        st.rerun()

# ============ STATUS DO PROCESSAMENTO ============

if st.session_state.get("relatorio_em_processamento", False):
    st_autorefresh(interval=2000, limit=100, key="refresh_durante_processamento")

    progresso, mensagem = ler_progresso_do_arquivo()
    st.progress(progresso / 100)
    st.write(f"**Progresso: {progresso}%**")
    if mensagem:
        st.info(mensagem)

    if progresso == 100 and not st.session_state.thread.is_alive():
        st.session_state.relatorio_em_processamento = False
        st.session_state.processamento_concluido = True
        st.rerun()

elif st.session_state.get("processamento_concluido", False):
    st.success("✅ Relatório processado com sucesso!")
    st.info("🔄 Atualize a página para ver as mudanças nos gráficos e dados.")

elif st.session_state.get("erro_processamento"):
    st.error(f"❌ Erro no processamento: {st.session_state.erro_processamento}")

# Mostrar formulário de input se solicitado
if st.session_state.dados_inseridos:
    mostrar_formulario_input()
    st.markdown("---")

# Carregar dados do banco
try:
    df_precos, df_fretes, df_barter = carregar_dados()
except Exception as e:
    st.error(f"❌ Erro ao carregar dados do banco: {e}")
    st.stop()

if df_precos.empty and df_fretes.empty:
    st.warning("⚠️ **Nenhum dado encontrado no banco.** Importe um relatório ou insira dados manualmente.")
    st.info("💡 **Dicas:**")
    st.markdown("""
    - Use o botão **📝 INPUTAR DADOS** para adicionar dados manualmente
    - Use o botão **📥 IMPORTAR RELATÓRIO** para processar um PDF
    - Verifique se o banco de dados foi criado corretamente
    """)
    st.stop()

# Converter tipos de dados
if not df_precos.empty:
    df_precos['data_preco'] = pd.to_datetime(df_precos['data_preco'])
    df_precos['preco'] = pd.to_numeric(df_precos['preco'], errors='coerce')

if not df_barter.empty:
    df_barter['data'] = pd.to_datetime(df_barter['data'], errors='coerce')
    df_barter['preco_cultura'] = pd.to_numeric(df_barter['preco_cultura'], errors='coerce')
    df_barter['razao_barter'] = pd.to_numeric(df_barter['razao_barter'], errors='coerce')

# SISTEMA DE FILTROS FUNCIONAL
if not df_precos.empty:
    filtro_produto = df_precos['produto'].unique()
    filtro_local = df_precos['localizacao'].unique()
    filtro_moeda = df_precos['moeda'].unique()
    data_min = df_precos['data_preco'].min().date() if not pd.isna(df_precos['data_preco'].min()) else datetime.today().date()
    data_max = df_precos['data_preco'].max().date() if not pd.isna(df_precos['data_preco'].max()) else datetime.today().date()

    # Mostrar filtros se solicitado
    if st.session_state.mostrar_filtros:
        with st.expander("🔍 Filtros Avançados", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                filtro_produto = st.multiselect(
                    "Produtos:", 
                    options=df_precos['produto'].unique(), 
                    default=list(df_precos['produto'].unique())
                )
                
            with col_f2:
                filtro_local = st.multiselect(
                    "Localizações:", 
                    options=df_precos['localizacao'].unique(), 
                    default=list(df_precos['localizacao'].unique())
                )
                
            with col_f3:
                filtro_moeda = st.multiselect(
                    "Moedas:", 
                    options=df_precos['moeda'].unique(), 
                    default=list(df_precos['moeda'].unique())
                )
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                data_inicio = st.date_input("Data Início:", value=data_min, min_value=data_min, max_value=data_max)
            with col_d2:
                data_fim = st.date_input("Data Fim:", value=data_max, min_value=data_min, max_value=data_max)
            
            if st.button("✅ Aplicar Filtros", use_container_width=True):
                st.session_state.filtros_aplicados = True
                st.success("Filtros aplicados!")
                time.sleep(1)
                st.rerun()
            
            filtro_data = [data_inicio, data_fim]
    else:
        filtro_data = [data_min, data_max]

    # Aplicar filtros nos dados
    df_precos_filt = df_precos[
        (df_precos['produto'].isin(filtro_produto)) &
        (df_precos['localizacao'].isin(filtro_local)) &
        (df_precos['moeda'].isin(filtro_moeda)) &
        (df_precos['data_preco'] >= pd.to_datetime(filtro_data[0])) &
        (df_precos['data_preco'] <= pd.to_datetime(filtro_data[1]))
    ]
else:
    df_precos_filt = df_precos

# KPIs MELHORADOS
st.subheader("📊 Indicadores Principais")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric("Produtos únicos", df_precos_filt['produto'].nunique() if not df_precos_filt.empty else 0)

with kpi2:
    st.metric("Locais únicos", df_precos_filt['localizacao'].nunique() if not df_precos_filt.empty else 0)

with kpi3:
    st.metric("Registros de preço", len(df_precos_filt))

with kpi4:
    if not df_precos_filt.empty and df_precos_filt['preco'].notna().any():
        preco_medio = df_precos_filt['preco'].mean()
        st.metric("Preço médio", f"${preco_medio:.2f}")
    else:
        st.metric("Preço médio", "N/A")

with kpi5:
    st.metric("Registros de permuta", len(df_barter))

# GRÁFICOS EXISTENTES + NOVOS + MELHORADOS

# 1. Gráfico histórico de preços
st.subheader("📈 Histórico de Preços")
if not df_precos_filt.empty:
    fig_preco = px.line(
        df_precos_filt.sort_values('data_preco'),
        x='data_preco',
        y='preco',
        color='produto',
        line_dash='localizacao',
        markers=True,
        title="Evolução dos preços por produto e localização"
    )
    fig_preco.update_layout(
        margin=dict(t=50, b=20),
        hovermode='x unified'
    )
    st.plotly_chart(fig_preco, use_container_width=True)
else:
    st.info("Nenhum dado de preços disponível para o gráfico de histórico.")

# 2. Comparação de preços por produto (Boxplot)
if not df_precos_filt.empty and df_precos_filt['preco'].notna().any():
    st.subheader("📊 Distribuição de Preços por Produto")
    fig_box = px.box(
        df_precos_filt,
        x='produto',
        y='preco',
        color='produto',
        title="Distribuição e outliers de preços por produto"
    )
    fig_box.update_layout(margin=dict(t=50, b=20))
    st.plotly_chart(fig_box, use_container_width=True)

# 3. Variação percentual mensal
if not df_precos_filt.empty and len(df_precos_filt) > 1:
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
        title="Variação percentual média mensal por produto",
        markers=True
    )
    fig_pct.update_layout(margin=dict(t=50, b=20))
    st.plotly_chart(fig_pct, use_container_width=True)

# 4. Heatmap de preços por localização e produto
if not df_precos_filt.empty and len(df_precos_filt) > 3:
    st.subheader("🔥 Mapa de Calor - Preços por Localização")
    heatmap_data = df_precos_filt.groupby(['produto', 'localizacao'])['preco'].mean().reset_index()
    
    if len(heatmap_data) > 1:
        heatmap_pivot = heatmap_data.pivot(index='produto', columns='localizacao', values='preco')
        
        fig_heatmap = px.imshow(
            heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            aspect="auto",
            title="Preços médios por produto e localização",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

# 5. Dispersão preço x data
if not df_precos_filt.empty:
    st.subheader("🔍 Dispersão Preço x Data")
    fig_disp = px.scatter(
        df_precos_filt,
        x='data_preco',
        y='preco',
        color='produto',
        size='preco',
        hover_data=['localizacao', 'moeda'],
        title="Dispersão dos preços ao longo do tempo"
    )
    fig_disp.update_layout(margin=dict(t=50, b=20))
    st.plotly_chart(fig_disp, use_container_width=True)

# 6. Ranking de produtos por preço médio
if not df_precos_filt.empty:
    st.subheader("🏆 Ranking de Produtos por Preço Médio")
    ranking_produtos = df_precos_filt.groupby('produto')['preco'].agg(['mean', 'count']).reset_index()
    ranking_produtos.columns = ['Produto', 'Preço Médio', 'Qtd Registros']
    ranking_produtos = ranking_produtos.sort_values('Preço Médio', ascending=False)
    
    fig_ranking = px.bar(
        ranking_produtos.head(10),
        x='Produto',
        y='Preço Médio',
        title="Top 10 Produtos por Preço Médio",
        text='Preço Médio',
        color='Preço Médio',
        color_continuous_scale="Viridis"
    )
    fig_ranking.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
    st.plotly_chart(fig_ranking, use_container_width=True)

# 7. NOVO: Análise de correlação entre produtos
if not df_precos_filt.empty and len(df_precos_filt['produto'].unique()) > 1:
    st.subheader("🔗 Correlação de Preços Entre Produtos")
    
    # Preparar dados para correlação
    df_corr = df_precos_filt.pivot_table(
        index='data_preco', 
        columns='produto', 
        values='preco', 
        aggfunc='mean'
    )
    
    if df_corr.shape[1] > 1:
        corr_matrix = df_corr.corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            aspect="auto",
            title="Matriz de Correlação de Preços Entre Produtos",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1
        )
        st.plotly_chart(fig_corr, use_container_width=True)

# Dashboard Fretes (melhorado)
st.subheader("🚛 Análise Detalhada de Custos Logísticos (Fretes)")
if not df_fretes.empty:
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # Gráfico de fretes por tipo de transporte
        frete_por_tipo = df_fretes.groupby('tipo_transporte')['preco'].mean().reset_index()
        fig_frete_tipo = px.pie(
            frete_por_tipo,
            names='tipo_transporte',
            values='preco',
            title="Distribuição de Custos por Tipo de Transporte"
        )
        st.plotly_chart(fig_frete_tipo, use_container_width=True)
    
    with col_f2:
        # Scatter plot origem-destino
        df_fretes_agrup = df_fretes.groupby(['origem', 'destino', 'tipo_transporte']).agg({
            'preco':'mean', 
            'data':'count'
        }).reset_index()
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

# Análise Sazonal (melhorada)
st.subheader("📅 Análise Sazonal dos Preços")
try:
    
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
            name='Componente Sazonal',
            line=dict(color='blue')
        ))
        fig_seasonal.update_layout(
            title='Componente Sazonal dos Preços Médios',
            margin=dict(t=50, b=20),
            xaxis_title="Data",
            yaxis_title="Variação Sazonal"
        )
        st.plotly_chart(fig_seasonal, use_container_width=True)
    else:
        st.info(f"A série temporal precisa de pelo menos 24 meses para análise sazonal. Atualmente possui {len(ts_data)} meses.")
        
        # Mostrar análise mensal alternativa
        if len(ts_data) >= 6:
            fig_mensal = px.line(
                x=ts_data.index,
                y=ts_data.values,
                title="Evolução dos Preços Médios Mensais",
                labels={'x': 'Data', 'y': 'Preço Médio'}
            )
            st.plotly_chart(fig_mensal, use_container_width=True)

except Exception as e:
    st.warning(f"Análise sazonal não disponível: {e}")

# Alertas automáticos (melhorados)
st.subheader("⚠️ Alertas Automáticos")
try:
    if not df_precos_filt.empty and len(df_precos_filt) > 1:
        df_precos_filt_sorted = df_precos_filt.sort_values(['produto', 'localizacao', 'data_preco'])
        df_precos_filt_sorted['pct_change'] = df_precos_filt_sorted.groupby(['produto', 'localizacao'])['preco'].pct_change(fill_method=None) * 100
        
        alertas = df_precos_filt_sorted[
            (df_precos_filt_sorted['pct_change'].abs() > 10) & 
            (df_precos_filt_sorted['pct_change'].notna())
        ]
        
        if not alertas.empty:
            st.markdown("**🚨 Variações Significativas Detectadas:**")
            for _, row in alertas.head(5).iterrows():
                if row['pct_change'] > 0:
                    st.success(f"📈 {row['produto']} em {row['localizacao']}: +{row['pct_change']:.1f}% em {row['data_preco'].date()}")
                else:
                    st.error(f"📉 {row['produto']} em {row['localizacao']}: {row['pct_change']:.1f}% em {row['data_preco'].date()}")
        else:
            st.info("✅ Nenhuma variação significativa detectada (>10%).")
    else:
        st.info("Dados insuficientes para análise de variação.")
        
except Exception as e:
    st.warning(f"Erro ao gerar alertas: {e}")

# Distribuição preço médio por produto (melhorado)
st.subheader("📊 Distribuição do Preço Médio por Produto")
if not df_precos_filt.empty:
    preco_medio_produto = df_precos_filt.groupby('produto')['preco'].mean().reset_index()
    fig_pie = px.pie(
        preco_medio_produto, 
        names='produto', 
        values='preco', 
        title='Distribuição de Preço Médio por Produto'
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# Tabelas de dados (melhoradas)
col_tab1, col_tab2 = st.columns(2)

with col_tab1:
    st.subheader("💰 Últimos Preços Registrados")
    if not df_precos_filt.empty:
        tabela_precos = df_precos_filt.sort_values("data_preco", ascending=False).head(10)
        tabela_precos['data_preco'] = tabela_precos['data_preco'].dt.strftime('%d/%m/%Y')
        st.dataframe(tabela_precos[['produto', 'localizacao', 'preco', 'moeda', 'data_preco']], use_container_width=True)
    else:
        st.info("Nenhum dado de preços disponível.")

with col_tab2:
    st.subheader("🚚 Últimos Fretes Registrados")
    if not df_fretes.empty:
        tabela_fretes = df_fretes.sort_values("data", ascending=False).head(10)
        st.dataframe(tabela_fretes, use_container_width=True)
    else:
        st.info("Nenhum dado de fretes disponível.")

# Rodapé visual
st.markdown("---")
st.markdown("**Dashboard Morro Verde** - Análise de Concorrência | Dados atualizados em tempo real")

# Seção de Desfazer e Histórico de Ações
st.markdown("---")
st.markdown("### ⏪ Deseja desfazer a última atualização?")

if os.path.exists("backups"):
    if st.button("Desfazer Última Atualização", use_container_width=True):
        if restaurar_backup_mais_recente():
            if os.path.exists("acoes_realizadas.json"):
                with open("acoes_realizadas.json", "r") as f:
                    log = json.load(f)
                if log:
                    log.pop()  # Remove a última ação do histórico
                    with open("acoes_realizadas.json", "w") as f:
                        json.dump(log, f)
            st.success("✅ Banco de dados restaurado com sucesso!")
            st.rerun()

if os.path.exists("acoes_realizadas.json"):
    with open("acoes_realizadas.json", "r") as f:
        acoes = json.load(f)
    if acoes:
        st.markdown("#### 📚 Histórico de alterações no banco:")
        for acao in reversed(acoes[-5:]):
            st.markdown(f"- {acao}")


