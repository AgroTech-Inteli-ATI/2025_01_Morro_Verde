# mock_data_rich.py

import sqlite3
from datetime import date, timedelta
import random

# Conecta no banco local
conn = sqlite3.connect("morro_verde.db")
cursor = conn.cursor()

# Produtos
produtos = [
    ('Fertilizante X', 'NPK 20-20-20'),
    ('Fertilizante Y', 'NPK 10-30-10'),
    ('Fertilizante Z', 'Ureia 46%')
]

for nome, formulacao in produtos:
    cursor.execute("""
    INSERT OR IGNORE INTO produtos (nome_produto, formulacao, origem, tipo, unidade)
    VALUES (?, ?, 'Brasil', 'Fertilizante', 'Tonelada')
    """, (nome, formulacao))

# Pega IDs dos produtos
cursor.execute("SELECT id, nome_produto FROM produtos")
produtos_ids = cursor.fetchall()

# Locais
locais = [
    ('Porto de Santos', 'SP', 'porto'),
    ('Paranaguá', 'PR', 'porto'),
    ('Porto de Itaqui', 'MA', 'porto'),
    ('Mato Grosso', 'MT', 'estado'),
    ('Goiás', 'GO', 'estado'),
    ('Bahia', 'BA', 'estado')
]

for nome, estado, tipo in locais:
    cursor.execute("""
    INSERT OR IGNORE INTO locais (nome, estado, pais, tipo)
    VALUES (?, ?, 'Brasil', ?)
    """, (nome, estado, tipo))

# Pega IDs dos locais
cursor.execute("SELECT id, nome FROM locais")
locais_ids = cursor.fetchall()

# Mock por 45 dias
hoje = date.today()

for i in range(45):
    data_dia = hoje - timedelta(days=i)
    data_str = str(data_dia)

    # Mock de preços
    for produto_id, nome_produto in produtos_ids:
        for local_id, local_nome in locais_ids:
            if 'porto' in local_nome.lower():  # só insere preço em portos
                preco_min = random.uniform(350, 450)
                preco_max = preco_min + random.uniform(10, 30)
                variacao = random.uniform(-3, 5)
                simbolo_var = '+' if variacao >= 0 else '-'

                cursor.execute("""
                INSERT INTO precos (produto_id, local_id, data, tipo_preco, modalidade, fonte, moeda, preco_min, preco_max, variacao, simbolo_var)
                VALUES (?, ?, ?, 'Spot', 'FOB', 'Mock', 'USD', ?, ?, ?, ?)
                """, (produto_id, local_id, data_str, preco_min, preco_max, abs(variacao), simbolo_var))

    # Mock de fretes
    for origem_id, origem_nome in locais_ids:
        for destino_id, destino_nome in locais_ids:
            if 'porto' in origem_nome.lower() and 'estado' not in destino_nome.lower() and origem_id != destino_id:
                custo_usd = random.uniform(50, 120)
                custo_brl = custo_usd * random.uniform(5.0, 5.3)

                cursor.execute("""
                INSERT INTO fretes (tipo, origem_id, destino_id, data, custo_usd, custo_brl)
                VALUES ('Rodoviário', ?, ?, ?, ?, ?)
                """, (origem_id, destino_id, data_str, custo_usd, custo_brl))

    # Mock de barter
    for produto_id, _ in produtos_ids:
        barter_ratio = random.uniform(2.5, 4.5)
        preco_cultura = random.uniform(140, 180)
        barter_index = barter_ratio * preco_cultura

        cursor.execute("""
        INSERT INTO barter_ratios (cultura, produto_id, estado, data, preco_cultura, barter_ratio, barter_index)
        VALUES ('Soja', ?, 'MT', ?, ?, ?, ?)
        """, (produto_id, data_str, preco_cultura, barter_ratio, barter_index))

    # Mock câmbio
    usd_brl = random.uniform(4.9, 5.4)
    cursor.execute("""
    INSERT OR REPLACE INTO cambio (data, usd_brl)
    VALUES (?, ?)
    """, (data_str, usd_brl))

    # Mock custos portuários
    for porto_id, porto_nome in locais_ids:
        if 'porto' in porto_nome.lower():
            armazenagem = random.uniform(20, 40)
            demurrage = random.uniform(15, 35)
            custo_total = armazenagem + demurrage

            cursor.execute("""
            INSERT INTO custos_portos (porto_id, data, armazenagem, demurrage, custo_total)
            VALUES (?, ?, ?, ?, ?)
            """, (porto_id, data_str, armazenagem, demurrage, custo_total))

conn.commit()
conn.close()

print("✅ Mock RICH de dados inserido com sucesso no banco!")
