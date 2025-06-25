import sqlite3

# Conecta ou cria o banco morro_verde.db
conn = sqlite3.connect("morro_verde.db")
cursor = conn.cursor()

# Tabela de produtos
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_produto TEXT,
    formulacao TEXT,
    origem TEXT,
    tipo TEXT,
    unidade TEXT,
    UNIQUE(nome_produto, formulacao, origem)
)
""")

# Tabela de locais (portos, estados, países)
cursor.execute("""
CREATE TABLE IF NOT EXISTS locais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    estado TEXT,
    pais TEXT,
    tipo TEXT
)
""")

# Tabela de preços
cursor.execute("""
CREATE TABLE IF NOT EXISTS precos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    local_id INTEGER,
    data TEXT,
    tipo_preco TEXT,
    modalidade TEXT,
    fonte TEXT,
    moeda TEXT,
    preco_min REAL,
    preco_max REAL,
    variacao REAL,
    simbolo_var TEXT,
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (local_id) REFERENCES locais(id)
)
""")

# Tabela de fretes
cursor.execute("""
CREATE TABLE IF NOT EXISTS fretes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    origem_id INTEGER,
    destino_id INTEGER,
    data TEXT,
    custo_usd REAL,
    custo_brl REAL,
    FOREIGN KEY (origem_id) REFERENCES locais(id),
    FOREIGN KEY (destino_id) REFERENCES locais(id)
)
""")

# Tabela de razões de troca (barter)
cursor.execute("""
CREATE TABLE IF NOT EXISTS barter_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cultura TEXT,
    produto_id INTEGER,
    estado TEXT,
    data TEXT,
    preco_cultura REAL,
    barter_ratio REAL,
    barter_index REAL,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
)
""")

# Tabela de câmbio
cursor.execute("""
CREATE TABLE IF NOT EXISTS cambio (
    data TEXT PRIMARY KEY,
    usd_brl REAL
)
""")

# Tabela de custos portuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS custos_portos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    porto_id INTEGER,
    data TEXT,
    armazenagem REAL,
    demurrage REAL,
    custo_total REAL,
    FOREIGN KEY (porto_id) REFERENCES locais(id)
)
""")

conn.commit()
conn.close()

print("✅ Banco de dados 'morro_verde.db' criado com sucesso!")
