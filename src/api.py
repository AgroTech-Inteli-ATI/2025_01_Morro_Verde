import fitz  # PyMuPDF
import sqlite3
import google.generativeai as genai
import json
import os
from datetime import datetime

# ======================= CONFIGURAÇÃO =======================
GEMINI_API_KEY = "AIzaSyBu-dCd8gDai2c39Lslg9JYQaS-rzqhxq8"
CAMINHO_PDF = "relatorios/relatorio.pdf"
NOME_ARQUIVO = os.path.basename(CAMINHO_PDF)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ======================= ETAPA 1: LER PDF =======================
def ler_pdf(caminho_pdf):
    texto = ""
    with fitz.open(caminho_pdf) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

# ======================= ETAPA 2: EXTRAIR DADOS COM IA =======================
def gerar_json_estruturado(texto):
    prompt = f"""
Extraia as informações do relatório abaixo no seguinte formato JSON:

[
  {{
    "nome_produto": "...",
    "origem": "...",
    "tipo": "...",
    "estado": "...",
    "data_referencia": "YYYY-MM-DD",
    "preco": ...,
    "preco_anterior": ...,
    "variacao": "▲" ou "▼" ou "="
  }},
  ...
]

Use apenas os dados disponíveis. Se algum campo não estiver no texto, preencha com `null`.

Texto do relatório:
\"\"\"{texto}\"\"\"
"""
    resposta = model.generate_content(prompt)
    conteudo = resposta.text.strip()

    if conteudo.startswith("```"):
        conteudo = "\n".join(l for l in conteudo.splitlines() if not l.strip().startswith("```"))

    try:
        if not conteudo.startswith("["):
            conteudo = "[" + conteudo
        if not conteudo.endswith("]"):
            conteudo = conteudo[:conteudo.rfind("}") + 1] + "]"

        return json.loads(conteudo)
    except json.JSONDecodeError as e:
        print("❌ JSON inválido gerado pela IA:")
        print(conteudo[:1000])
        raise e

# ======================= ETAPA 3: INSERIR NO BANCO =======================
def inserir_dados_no_banco(dados):
    conn = sqlite3.connect("morro_verde.db")
    cursor = conn.cursor()

    for entrada in dados:
        # Produto
        cursor.execute("""
            SELECT id FROM produtos WHERE nome = ? AND origem = ? AND tipo = ?
        """, (entrada["nome"], entrada["origem"], entrada["tipo"]))
        produto = cursor.fetchone()
        if produto:
            produto_id = produto[0]
        else:
            cursor.execute("""
                INSERT INTO produtos (nome, origem, tipo) VALUES (?, ?, ?)
            """, (entrada["nome"], entrada["origem"], entrada["tipo"]))
            produto_id = cursor.lastrowid

        # Mercado
        cursor.execute("SELECT id FROM mercados WHERE estado = ?", (entrada["estado"],))
        mercado = cursor.fetchone()
        if mercado:
            mercado_id = mercado[0]
        else:
            cursor.execute("INSERT INTO mercados (estado) VALUES (?)", (entrada["estado"],))
            mercado_id = cursor.lastrowid

        # Relatório
        cursor.execute("""
            SELECT id FROM relatorios WHERE data_referencia = ? AND nome_arquivo = ?
        """, (entrada["data_referencia"], NOME_ARQUIVO))
        relatorio = cursor.fetchone()
        if relatorio:
            relatorio_id = relatorio[0]
        else:
            cursor.execute("""
                INSERT INTO relatorios (data_referencia, nome_arquivo) VALUES (?, ?)
            """, (entrada["data_referencia"], NOME_ARQUIVO))
            relatorio_id = cursor.lastrowid

        # Preço
        cursor.execute("""
            INSERT INTO precos (
                produto_id, mercado_id, relatorio_id, preco, comparado_a, variacao
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            produto_id,
            mercado_id,
            relatorio_id,
            entrada["preco"],
            entrada["preco_anterior"],
            entrada["variacao"]
        ))

    conn.commit()
    conn.close()
    print("✅ Dados inseridos no banco com sucesso!")

# ======================= EXECUÇÃO =======================
if __name__ == "__main__":
    print("📄 Lendo o relatório PDF...")
    texto = ler_pdf(CAMINHO_PDF)

    print("🤖 Processando com Gemini...")
    dados_json = gerar_json_estruturado(texto)

    print("🗄️ Inserindo no banco...")
    inserir_dados_no_banco(dados_json)
