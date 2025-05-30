import sqlite3
from datetime import datetime

def salvar_preco_manual(produto, localizacao, preco, moeda, data_preco):
    try:
        conn = sqlite3.connect("morro_verde.db")
        cursor = conn.cursor()
        
        # Primeiro, verificar/inserir produto
        cursor.execute('''
            INSERT OR IGNORE INTO produtos (nome_produto, formulacao, origem, tipo, unidade)
            VALUES (?, '', '', 'Manual', 'USD')
        ''', (produto,))
        
        cursor.execute('SELECT id FROM produtos WHERE nome_produto = ?', (produto,))
        produto_id = cursor.fetchone()[0]
        
        # Segundo, verificar/inserir local
        cursor.execute('''
            INSERT OR IGNORE INTO locais (nome, estado, pais, tipo)
            VALUES (?, '', '', 'Manual')
        ''', (localizacao,))
        
        cursor.execute('SELECT id FROM locais WHERE nome = ?', (localizacao,))
        local_id = cursor.fetchone()[0]
        
        # Terceiro, inserir preço na tabela correta
        data_formatada = data_preco.strftime('%Y-%m-%d') if data_preco else datetime.today().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO precos (produto_id, local_id, data, tipo_preco, modalidade, fonte, moeda, preco_min, preco_max, variacao, simbolo_var)
            VALUES (?, ?, ?, 'Manual', 'Spot', 'Input Manual', ?, ?, ?, 0, '')
        ''', (produto_id, local_id, data_formatada, moeda, preco, preco))
        
        conn.commit()
        conn.close()
        return True, "Preço inserido com sucesso!"
    
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Erro ao inserir preço: {e}"

        
def salvar_frete_manual(origem, destino, valor, moeda, data_frete):
    try:
        conn = sqlite3.connect("morro_verde.db")
        cursor = conn.cursor()
        
        # Verificar/inserir origem
        cursor.execute('''
            INSERT OR IGNORE INTO locais (nome, estado, pais, tipo)
            VALUES (?, '', '', 'Manual')
        ''', (origem,))
        
        cursor.execute('SELECT id FROM locais WHERE nome = ?', (origem,))
        origem_result = cursor.fetchone()
        if not origem_result:
            conn.close()
            return False, f"Erro: origem '{origem}' não encontrada"
        origem_id = origem_result[0]
        
        # Verificar/inserir destino
        cursor.execute('''
            INSERT OR IGNORE INTO locais (nome, estado, pais, tipo)
            VALUES (?, '', '', 'Manual')
        ''', (destino,))
        
        cursor.execute('SELECT id FROM locais WHERE nome = ?', (destino,))
        destino_result = cursor.fetchone()
        if not destino_result:
            conn.close()
            return False, f"Erro: destino '{destino}' não encontrado"
        destino_id = destino_result[0]
        
        # Inserir frete
        data_formatada = data_frete.strftime('%Y-%m-%d') if data_frete else datetime.today().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO fretes (tipo, origem_id, destino_id, data, custo_usd, custo_brl)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Manual', origem_id, destino_id, data_formatada, valor, valor * 5.5))  # Assumindo conversão aproximada
        
        conn.commit()
        conn.close()
        return True, "Frete inserido com sucesso!"
    
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Erro ao inserir frete: {e}"