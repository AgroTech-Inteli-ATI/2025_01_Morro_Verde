import sqlite3

DB_PATH = "morro_verde_test.db"  # Ajuste aqui para seu arquivo de banco

def diagnostico_bd(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Quantidade total de registros
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM locais")
    locais_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM precos")
    precos_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM fretes")
    fretes_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM barter_ratios")
    barter_count = cursor.fetchone()[0]

    print(f"Produtos: {produtos_count}")
    print(f"Locais: {locais_count}")
    print(f"Preços: {precos_count}")
    print(f"Fretes: {fretes_count}")
    print(f"Barter Ratios: {barter_count}")

    # Verificar precos com produto_id inválido (sem correspondência na tabela produtos)
    cursor.execute("""
        SELECT COUNT(*) FROM precos pr
        LEFT JOIN produtos p ON pr.produto_id = p.id
        WHERE p.id IS NULL
    """)
    precos_sem_produto = cursor.fetchone()[0]

    # Verificar precos com local_id inválido
    cursor.execute("""
        SELECT COUNT(*) FROM precos pr
        LEFT JOIN locais l ON pr.local_id = l.id
        WHERE l.id IS NULL
    """)
    precos_sem_local = cursor.fetchone()[0]

    # Verificar fretes com origem_id inválido
    cursor.execute("""
        SELECT COUNT(*) FROM fretes f
        LEFT JOIN locais l ON f.origem_id = l.id
        WHERE l.id IS NULL
    """)
    fretes_sem_origem = cursor.fetchone()[0]

    # Verificar fretes com destino_id inválido
    cursor.execute("""
        SELECT COUNT(*) FROM fretes f
        LEFT JOIN locais l ON f.destino_id = l.id
        WHERE l.id IS NULL
    """)
    fretes_sem_destino = cursor.fetchone()[0]

    print(f"Preços com produto_id inválido: {precos_sem_produto}")
    print(f"Preços com local_id inválido: {precos_sem_local}")
    print(f"Fretes com origem_id inválido: {fretes_sem_origem}")
    print(f"Fretes com destino_id inválido: {fretes_sem_destino}")

    conn.close()

if __name__ == "__main__":
    diagnostico_bd(DB_PATH)
