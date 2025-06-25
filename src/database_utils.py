from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Setup Engine
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def salvar_preco_manual(produto, localizacao, preco, moeda, data_preco):
    try:
        with engine.begin() as connection:

            # Verificar/inserir produto
            connection.execute(text('''
                INSERT INTO produtos (nome_produto, formulacao, origem, tipo, unidade)
                VALUES (:produto, '', '', 'Manual', 'USD')
                ON CONFLICT (nome_produto, formulacao, origem) DO NOTHING
            '''), {"produto": produto})

            result = connection.execute(text('SELECT id FROM produtos WHERE nome_produto = :produto'),
                                        {"produto": produto})
            produto_id = result.fetchone()[0]

            # Verificar/inserir local
            connection.execute(text('''
                INSERT INTO locais (nome, estado, pais, tipo)
                VALUES (:localizacao, '', '', 'Manual')
                ON CONFLICT (nome, estado, pais, tipo) DO NOTHING
            '''), {"localizacao": localizacao})

            result = connection.execute(text('SELECT id FROM locais WHERE nome = :localizacao'),
                                        {"localizacao": localizacao})
            local_id = result.fetchone()[0]

            # Inserir preço
            data_formatada = data_preco.strftime('%Y-%m-%d') if data_preco else datetime.today().strftime('%Y-%m-%d')

            connection.execute(text('''
                INSERT INTO precos (produto_id, local_id, data, tipo_preco, modalidade, fonte, moeda, preco_min, preco_max, variacao, simbolo_var)
                VALUES (:produto_id, :local_id, :data, 'Manual', 'Spot', 'Input Manual', :moeda, :preco_min, :preco_max, 0, '')
            '''), {
                "produto_id": produto_id,
                "local_id": local_id,
                "data": data_formatada,
                "moeda": moeda,
                "preco_min": preco,
                "preco_max": preco
            })

            return True, "Preço inserido com sucesso!"

    except Exception as e:
        return False, f"Erro ao inserir preço: {e}"


def salvar_frete_manual(origem, destino, valor, moeda, data_frete):
    try:
        with engine.begin() as connection:

            # Verificar/inserir origem
            connection.execute(text('''
                INSERT INTO locais (nome, estado, pais, tipo)
                VALUES (:origem, '', '', 'Manual')
                ON CONFLICT (nome, estado, pais, tipo) DO NOTHING
            '''), {"origem": origem})

            origem_result = connection.execute(text('SELECT id FROM locais WHERE nome = :origem'),
                                               {"origem": origem}).fetchone()
            if not origem_result:
                return False, f"Erro: origem '{origem}' não encontrada"
            origem_id = origem_result[0]

            # Verificar/inserir destino
            connection.execute(text('''
                INSERT INTO locais (nome, estado, pais, tipo)
                VALUES (:destino, '', '', 'Manual')
                ON CONFLICT (nome, estado, pais, tipo) DO NOTHING
            '''), {"destino": destino})

            destino_result = connection.execute(text('SELECT id FROM locais WHERE nome = :destino'),
                                                {"destino": destino}).fetchone()
            if not destino_result:
                return False, f"Erro: destino '{destino}' não encontrada"
            destino_id = destino_result[0]

            # Inserir frete
            data_formatada = data_frete.strftime('%Y-%m-%d') if data_frete else datetime.today().strftime('%Y-%m-%d')

            connection.execute(text('''
                INSERT INTO fretes (tipo, origem_id, destino_id, data, custo_usd, custo_brl)
                VALUES (:tipo, :origem_id, :destino_id, :data, :custo_usd, :custo_brl)
            '''), {
                "tipo": 'Manual',
                "origem_id": origem_id,
                "destino_id": destino_id,
                "data": data_formatada,
                "custo_usd": valor,
                "custo_brl": valor * 5.5  # Você pode refinar essa conversão depois
            })

            return True, "Frete inserido com sucesso!"

    except Exception as e:
        return False, f"Erro ao inserir frete: {e}"
