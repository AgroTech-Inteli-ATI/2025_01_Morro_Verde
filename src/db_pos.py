import sqlite3

def limpar_bd(db_path="morro_verde.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Apagar registros órfãos (precos e fretes com referências inválidas)
    cursor.execute("""
        DELETE FROM precos
        WHERE produto_id NOT IN (SELECT id FROM produtos)
           OR local_id NOT IN (SELECT id FROM locais)
    """)
    print(f"Preços órfãos removidos: {cursor.rowcount}")

    cursor.execute("""
        DELETE FROM fretes
        WHERE origem_id NOT IN (SELECT id FROM locais)
           OR destino_id NOT IN (SELECT id FROM locais)
    """)
    print(f"Fretes órfãos removidos: {cursor.rowcount}")

    cursor.execute("""
        DELETE FROM barter_ratios
        WHERE produto_id NOT IN (SELECT id FROM produtos)
    """)
    print(f"Barter órfãos removidos: {cursor.rowcount}")

    cursor.execute("""
        DELETE FROM custos_portos
        WHERE porto_id NOT IN (SELECT id FROM locais)
    """)
    print(f"Custos portuários órfãos removidos: {cursor.rowcount}")

    # 2. Remover duplicados nas tabelas com coluna id
    tabelas_duplicados = {
        'produtos': ['nome_produto', 'formulacao', 'origem'],
        'locais': ['nome', 'estado', 'pais', 'tipo'],
        'precos': ['produto_id', 'local_id', 'data', 'tipo_preco', 'modalidade', 'fonte', 'moeda', 'preco_min', 'preco_max', 'variacao', 'simbolo_var'],
        'fretes': ['tipo', 'origem_id', 'destino_id', 'data', 'custo_usd', 'custo_brl'],
        'barter_ratios': ['cultura', 'produto_id', 'estado', 'data', 'preco_cultura', 'barter_ratio', 'barter_index'],
        'custos_portos': ['porto_id', 'data', 'armazenagem', 'demurrage', 'custo_total'],
    }

    for tabela, colunas in tabelas_duplicados.items():
        cols_group = ", ".join(colunas)
        sql = f"""
        DELETE FROM {tabela}
        WHERE id NOT IN (
            SELECT MIN(id) FROM {tabela}
            GROUP BY {cols_group}
        )
        """
        cursor.execute(sql)
        print(f"Duplicados removidos na tabela {tabela}: {cursor.rowcount}")

    # 3. Remover duplicados da tabela cambio (sem coluna id)
    cursor.execute("""
        DELETE FROM cambio
        WHERE data NOT IN (
            SELECT MIN(data) FROM cambio GROUP BY data
        )
    """)
    print(f"Duplicados removidos na tabela cambio: {cursor.rowcount}")

    # 4. Apagar linhas onde **todos os campos relevantes** são NULL (para evitar registros vazios)
    tabelas_nulls = {
        'produtos': ['nome_produto', 'formulacao', 'origem', 'tipo', 'unidade'],
        'locais': ['nome', 'estado', 'pais', 'tipo'],
        'precos': ['produto_id', 'local_id', 'data', 'tipo_preco', 'modalidade', 'fonte', 'moeda', 'preco_min', 'preco_max', 'variacao', 'simbolo_var'],
        'fretes': ['tipo', 'origem_id', 'destino_id', 'data', 'custo_usd', 'custo_brl'],
        'barter_ratios': ['cultura', 'produto_id', 'estado', 'data', 'preco_cultura', 'barter_ratio', 'barter_index'],
        'cambio': ['usd_brl'],  # 'data' é PK e não pode ser null
        'custos_portos': ['porto_id', 'data', 'armazenagem', 'demurrage', 'custo_total'],
    }

    for tabela, colunas in tabelas_nulls.items():
        condicoes_null = " AND ".join([f"{col} IS NULL" for col in colunas])
        sql = f"DELETE FROM {tabela} WHERE {condicoes_null}"
        cursor.execute(sql)
        print(f"Registros vazios removidos na tabela {tabela}: {cursor.rowcount}")

    conn.commit()
    conn.close()
    print("✅ Banco limpo e duplicados removidos com sucesso!")

if __name__ == "__main__":
    limpar_bd()
