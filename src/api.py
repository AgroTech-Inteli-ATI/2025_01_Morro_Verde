import fitz
import sqlite3
import google.generativeai as genai
import json
import os
from datetime import datetime
#from db_pos import limpar_bd

# ======================= CONFIGURAÇÃO =======================
GEMINI_API_KEY = "AIzaSyDgvxDR1UI1BgwaTsBbK2lJPJnDGWLce-M"
CAMINHO_PDF = "relatorio.pdf"
NOME_ARQUIVO = os.path.basename(CAMINHO_PDF)

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ======================= ETAPA 1: LER PDF =======================
def ler_pdf(caminho_pdf):
    texto = ""
    with fitz.open(caminho_pdf) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

# Função para dividir texto em n partes
def dividir_texto(texto, n_partes):
    tamanho = len(texto)
    parte_tamanho = tamanho // n_partes
    partes = [texto[i * parte_tamanho : (i + 1) * parte_tamanho] for i in range(n_partes - 1)]
    partes.append(texto[(n_partes - 1) * parte_tamanho :])
    return partes

# ======================= ETAPA 2.1: EXTRAIR DADOS COM IA =======================
def gerar_json_estruturado(texto):
    prompt = f"""
Você é um extrator de dados que transforma um relatório semanal de fertilizantes no Brasil em um JSON compatível com um banco relacional. Extraia **todas** as informações quantitativas possíveis.

--- 

O JSON deve conter as seguintes seções (listas de objetos), com os tipos exatos:

1. **produtos**:
  - nome_produto: string (ex: "Granular Urea", "MAP", "SSP", "DAP", "MOP", "TSP", "Amsul", "AN")
  - formulacao: string ou null (ex: "11-52", "00-18-18")
  - origem: string (ex: "Brasil", "China", "US", "Marrocos", etc.)
  - tipo: string (ex: "Ureia", "MAP", "NPK", "DAP", "SSP", "TSP", "Amsul", "AN")
  - unidade: string ("USD/t" ou "BRL/t")

2. **locais**:
  - nome: string
  - estado: string ou null (ex: "SP", "MT", "GO")
  - pais: string
  - tipo: string ("porto", "cidade", "estado", "pais")

3. **precos**:
  - produto: objeto (igual ao tipo produtos)
  - local: objeto (igual ao tipo locais)
  - data: string (ex: "2024-01-11")
  - tipo_preco: string (ex: "FOB", "CIF", "EXW")
  - modalidade: string ("Spot", "Contrato", "Indicativo")
  - fonte: string ("relatorio")
  - moeda: string ("USD" ou "BRL")
  - preco_min: float
  - preco_max: float
  - variacao: float ou null (estimado se possível)
  - simbolo_var: string ("▲", "▼", "=")

4. **fretes**:
  - tipo: string ("rodoviário" ou "marítimo"). Inclua fretes marítimos spot internacionais (ex: China, Egito, Marrocos → Brasil)
  - origem: objeto (tipo locais)
  - destino: objeto (tipo locais)
  - data: string ("YYYY-MM-DD")
  - custo_usd: float ou null
  - custo_brl: float ou null

5. **barter_ratios**:
  - cultura: string. Inclua **todas** as culturas presentes no relatório: Soja, Milho, Algodão, Arroz, Café, Cana-de-açúcar
  - produto: objeto (tipo produtos)
  - estado: string
  - data: string
  - preco_cultura: float
  - barter_ratio: float
  - barter_index: float ou null

6. **cambio**:
  - data: string (ex: "2024-01-11")
  - usd_brl: float

7. **custos_portos**:
  - porto: string (ex: "Santos", "Paranagua", etc.)
  - data: string
  - armazenagem: float
  - demurrage: float
  - custo_total: float

---

🧠 Instruções:

- Extraia **todos os produtos fertilizantes** mencionados no relatório, mesmo que apenas uma vez. Isso inclui: Ureia, MAP, NPK, DAP, MOP, SSP, TSP, AN, Amsul. NÃO omita fertilizantes menos citados — mesmo se os dados forem parciais, inclua-os.

- Inclua **todas as culturas agrícolas** listadas nas seções de barter: Soja, Milho, Algodão, Café, Arroz, Cana-de-açúcar. Mesmo que estejam incompletas, não omita nenhuma cultura presente nas tabelas.

- Extraia tanto **fretes rodoviários quanto fretes marítimos spot**. Nos fretes marítimos, inclua rotas como: China → Brasil, Marrocos → Brasil, Egito → Brasil, EUA → Brasil. Inclua **pelo menos um frete marítimo**, mesmo que estimado.

- Inclua **todos os estados brasileiros** mencionados no relatório, especialmente nos pontos de distribuição e barter.

- Sempre que símbolos de variação (`▲`, `▼`, `=`) aparecerem, preencha o campo `variacao` com valores aproximados: `+5.0` para `▲`, `-5.0` para `▼` e `0.0` para `=`.

- Use `"2024-01-11"` como data padrão caso a data não esteja explicitamente informada.

---

Agora leia o relatório abaixo e retorne **apenas o JSON bruto** com essa estrutura:


\"\"\" 
{texto[:35000]} 
\"\"\" 
"""
    resposta = model.generate_content(prompt)
    conteudo = resposta.text.strip()

    # Remover blocos de código markdown se existirem
    if conteudo.startswith("```"):
        conteudo = "\n".join(l for l in conteudo.splitlines() if not l.strip().startswith("```"))

    # Tentar carregar JSON, e se der erro, tentar cortar e fechar JSON para evitar erro
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as e:
        print("❌ Erro ao interpretar o JSON, tentando recuperação parcial...")
        # Tentar cortar no último } válido para tentar evitar erro de JSON incompleto
        ultimo_fecha = conteudo.rfind("}")
        if ultimo_fecha != -1:
            conteudo_corrigido = conteudo[:ultimo_fecha + 1]
            try:
                dados = json.loads(conteudo_corrigido)
                print("✅ Recuperação parcial bem-sucedida!")
                return dados
            except Exception:
                raise e
        else:
            raise e

    # ========== MELHORIAS AUTOMÁTICAS ==========
    # 1. Preencher origens nulas com "Brasil"
    for p in dados["produtos"]:
        if p.get("origem") is None:
            p["origem"] = "Brasil"

    # 2. Consolidar produtos únicos
    produtos_unicos = {}
    for p in dados["produtos"]:
        chave = (p["nome_produto"], p["formulacao"], p["origem"], p["tipo"], p["unidade"])
        produtos_unicos[chave] = p
    dados["produtos"] = list(produtos_unicos.values())

    # 3. Consolidar locais únicos
    locais_unicos = {}
    for l in dados["locais"]:
        chave = (l["nome"], l["estado"])
        locais_unicos[chave] = l
    dados["locais"] = list(locais_unicos.values())

    # 4. Inferir tipo_preco com base no tipo de local
    inferir_tipo_preco = {
        "porto": "FOB",
        "estado": "CIF",
        "cidade": "CIF",
        "pais": "FOB"
    }
    for p in dados["precos"]:
        if p.get("tipo_preco") is None:
            local = p.get("local")
            if isinstance(local, dict):
                tipo_local = local.get("tipo")
            else:
                tipo_local = None
            p["tipo_preco"] = inferir_tipo_preco.get(tipo_local, "CIF")

    # 5. Estimar variação com base no símbolo_var
    simbolo_para_variacao = {
        "▲": +5.0,
        "▼": -5.0,
        "=": 0.0
    }
    for p in dados["precos"]:
        if p.get("variacao") is None and p.get("simbolo_var") in simbolo_para_variacao:
            p["variacao"] = simbolo_para_variacao[p["simbolo_var"]]

    # ========== FIM DAS MELHORIAS ==========

    return dados

# ======================= ETAPA 2.2: COMBINAR JSONS =======================
def combinar_listas(lista1, lista2, chave=None):
    if chave:
        visto = {tuple(item.get(k) for k in chave) for item in lista1}
        novos = [item for item in lista2 if tuple(item.get(k) for k in chave) not in visto]
        return lista1 + novos
    else:
        return lista1 + [item for item in lista2 if item not in lista1]

def combinar_json(*partes):
    resultado = {
        "produtos": [],
        "locais": [],
        "precos": [],
        "fretes": [],
        "barter_ratios": [],
        "cambio": [],
        "custos_portos": [],
    }

    for parte in partes:
        resultado["produtos"] = combinar_listas(resultado["produtos"], parte.get("produtos", []), chave=["nome_produto", "formulacao", "origem", "tipo", "unidade"])
        resultado["locais"] = combinar_listas(resultado["locais"], parte.get("locais", []), chave=["nome", "estado"])
        resultado["precos"] = combinar_listas(resultado["precos"], parte.get("precos", []))
        resultado["fretes"] = combinar_listas(resultado["fretes"], parte.get("fretes", []))
        resultado["barter_ratios"] = combinar_listas(resultado["barter_ratios"], parte.get("barter_ratios", []))
        resultado["cambio"] = combinar_listas(resultado["cambio"], parte.get("cambio", []))
        resultado["custos_portos"] = combinar_listas(resultado["custos_portos"], parte.get("custos_portos", []))

    return resultado

# ======================= ETAPA 3: INSERIR NO BANCO =======================
def inserir_dados_no_banco(dados):
    conn = sqlite3.connect("morro_verde.db")
    cursor = conn.cursor()

    def get_or_create_local(nome, estado, pais, tipo):
        cursor.execute("SELECT id FROM locais WHERE nome = ?", (nome,))
        res = cursor.fetchone()
        if res: return res[0]
        cursor.execute("INSERT INTO locais (nome, estado, pais, tipo) VALUES (?, ?, ?, ?)", (nome, estado, pais, tipo))
        return cursor.lastrowid

    def get_or_create_produto(p):
        if not isinstance(p, dict):
            print("⚠️ Erro: produto inválido ->", p)
            return None  # evita o erro e segue em frente

        # O restante da função continua igual
        cursor.execute("SELECT id FROM produtos WHERE nome_produto = ? AND formulacao = ? AND origem = ?", (
            p.get("nome_produto"),
            p.get("formulacao"),
            p.get("origem")
        ))
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute("INSERT INTO produtos (nome_produto, formulacao, origem) VALUES (?, ?, ?)", (
            p.get("nome_produto"),
            p.get("formulacao"),
            p.get("origem")
        ))
        return cursor.lastrowid


    for p in dados["produtos"]:
        get_or_create_produto(p)

    for l in dados["locais"]:
        get_or_create_local(l.get("nome"), l.get("estado"), l.get("pais"), l.get("tipo"))

   # Inserção de preços
    for preco in dados.get("precos", []):
        produto_id = get_or_create_produto(preco["produto"])
        local_info = preco.get("local") or {}
        local_id = get_or_create_local(local_info.get("nome"), local_info.get("estado"), local_info.get("pais"), local_info.get("tipo"))
        cursor.execute("""
            INSERT INTO precos (produto_id, local_id, data, tipo_preco, modalidade, fonte, moeda, preco_min, preco_max, variacao, simbolo_var)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            produto_id,
            local_id,
            preco.get("data"),
            preco.get("tipo_preco"),
            preco.get("modalidade"),
            preco.get("fonte"),
            preco.get("moeda"),
            preco.get("preco_min"),
            preco.get("preco_max"),
            preco.get("variacao"),
            preco.get("simbolo_var")
        ))

    # Inserção de fretes
    for f in dados.get("fretes", []):
        origem = f.get("origem") or {}
        destino = f.get("destino") or {}
        origem_id = get_or_create_local(origem.get("nome"), origem.get("estado"), origem.get("pais"), origem.get("tipo"))
        destino_id = get_or_create_local(destino.get("nome"), destino.get("estado"), destino.get("pais"), destino.get("tipo"))
        cursor.execute("""
            INSERT INTO fretes (tipo, origem_id, destino_id, data, custo_usd, custo_brl)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f.get("tipo"), origem_id, destino_id, f.get("data"), f.get("custo_usd"), f.get("custo_brl")))

    # Inserção de barter_ratios
    for b in dados.get("barter_ratios", []):
        produto_id = get_or_create_produto(b["produto"])
        cursor.execute("""
            INSERT INTO barter_ratios (cultura, produto_id, estado, data, preco_cultura, barter_ratio, barter_index)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (b.get("cultura"), produto_id, b.get("estado"), b.get("data"), b.get("preco_cultura"), b.get("barter_ratio"), b.get("barter_index")))

    # Inserção de cambio
    for c in dados.get("cambio", []):
        cursor.execute("INSERT OR IGNORE INTO cambio (data, usd_brl) VALUES (?, ?)", (c.get("data"), c.get("usd_brl")))

    # Inserção de custos_portos
    for custo in dados.get("custos_portos", []):
        porto_id = get_or_create_local(custo.get("porto"), "", "Brasil", "porto")
        cursor.execute("""
            INSERT INTO custos_portos (porto_id, data, armazenagem, demurrage, custo_total)
            VALUES (?, ?, ?, ?, ?)
        """, (porto_id, custo.get("data"), custo.get("armazenagem"), custo.get("demurrage"), custo.get("custo_total")))
    conn.commit()
    conn.close()
    print("✅ Dados inseridos com sucesso no banco morro_verde.db!")
    
    # Chama limpeza pós inserção
    #limpar_bd()
    #print("✅ Pós-processamento: dados duplicados e vazios removidos.")

# ======================= EXECUÇÃO =======================
if __name__ == "__main__":
    print("📄 Lendo o relatório PDF...")
    texto = ler_pdf(CAMINHO_PDF)

    # Dividir em 15 partes para reduzir chance de truncamento
    partes = dividir_texto(texto, 15)

    dados_partes = []
    for i, parte in enumerate(partes, 1):
        print(f"🤖 Processando a Parte {i} com Gemini...")
        try:
            dados = gerar_json_estruturado(parte)
            dados_partes.append(dados)
        except Exception as e:
            print(f"⚠️ Erro ao processar a Parte {i}: {e}")
            continue

    print("🔀 Combinando os resultados...")
    dados_json = combinar_json(*dados_partes)

    # Salvar JSON em arquivo para comparação
    json_path = "saida_gemini3.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2)
    print(f"📁 JSON salvo como '{json_path}'")

    print("🗄️ Inserindo no banco...")
    inserir_dados_no_banco(dados_json)
