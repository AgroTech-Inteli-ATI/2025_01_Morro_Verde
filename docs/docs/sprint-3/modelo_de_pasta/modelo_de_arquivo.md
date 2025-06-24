---
sidebar_position: 2
custom_edit_url: null
---

# API com IA (GEMINI)

# API de Processamento de Relatórios

## Introdução

A API de processamento de relatórios do Sistema Morro Verde é responsável por extrair, processar e armazenar dados de fertilizantes a partir de relatórios PDF. O sistema utiliza inteligência artificial (Google Gemini) para extrair informações estruturadas de documentos não estruturados, convertendo-os em dados relacionais organizados.

### Principais Funcionalidades

- **Extração automática de dados**: Converte PDFs em dados estruturados JSON
- **Processamento inteligente**: Utiliza IA para identificar preços, produtos, locais e métricas
- **Armazenamento relacional**: Organiza dados em tabelas relacionais otimizadas
- **Validação e correção**: Aplica regras de negócio para garantir consistência dos dados

## Arquitetura do Sistema

### Dependências

```python
import fitz              # PyMuPDF para leitura de PDFs
import google.generativeai as genai  # Google Gemini AI
import json              # Manipulação de dados JSON
import os                # Operações do sistema
from dotenv import load_dotenv       # Variáveis de ambiente
from sqlalchemy import create_engine, text  # ORM e SQL
```

### Configuração

```python
# Carregamento de variáveis de ambiente
load_dotenv()
api_key = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuração do banco de dados
engine = create_engine(DATABASE_URL)

# Configuração do modelo AI
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash-latest")
```

## Funções Principais

### 1. Leitura de PDF

#### `ler_pdf(caminho_pdf)`

Extrai todo o texto de um arquivo PDF.

**Parâmetros:**

- `caminho_pdf` (string): Caminho para o arquivo PDF

**Retorna:**

- `string`: Texto completo extraído do PDF

**Exemplo:**

```python
texto = ler_pdf("relatorio.pdf")
print(f"Texto extraído: {len(texto)} caracteres")
```

#### `dividir_texto(texto, n_partes)`

Divide o texto em partes menores para processamento otimizado.

**Parâmetros:**

- `texto` (string): Texto a ser dividido
- `n_partes` (int): Número de partes desejadas

**Retorna:**

- `list`: Lista com as partes do texto

**Exemplo:**

```python
partes = dividir_texto(texto, 10)
print(f"Texto dividido em {len(partes)} partes")
```

### 2. Extração de Dados com IA

#### `gerar_json_estruturado(texto)`

Utiliza IA para extrair dados estruturados do texto do relatório.

**Parâmetros:**

- `texto` (string): Texto do relatório para processamento

**Retorna:**

- `dict`: Dados estruturados no formato JSON

**Estrutura de Retorno:**

```json
{
  "produtos": [
    {
      "nome_produto": "string",
      "formulacao": "string|null",
      "origem": "string",
      "tipo": "string",
      "unidade": "string"
    }
  ],
  "locais": [
    {
      "nome": "string",
      "estado": "string|null",
      "pais": "string",
      "tipo": "string"
    }
  ],
  "precos": [
    {
      "produto": "object",
      "local": "object",
      "data": "string",
      "tipo_preco": "string",
      "modalidade": "string",
      "fonte": "string",
      "moeda": "string",
      "preco_min": "float",
      "preco_max": "float",
      "variacao": "float|null",
      "simbolo_var": "string"
    }
  ],
  "fretes": [
    {
      "tipo": "string",
      "origem": "object",
      "destino": "object",
      "data": "string",
      "custo_usd": "float|null",
      "custo_brl": "float|null"
    }
  ],
  "barter_ratios": [
    {
      "cultura": "string",
      "produto": "object",
      "estado": "string",
      "data": "string",
      "preco_cultura": "float",
      "barter_ratio": "float",
      "barter_index": "float|null"
    }
  ],
  "cambio": [
    {
      "data": "string",
      "usd_brl": "float"
    }
  ],
  "custos_portos": [
    {
      "porto": "string",
      "data": "string",
      "armazenagem": "float",
      "demurrage": "float",
      "custo_total": "float"
    }
  ]
}
```

**Melhorias Automáticas:**

A função aplica automaticamente as seguintes correções:

1. **Preenchimento de origens nulas**: Define "Brasil" como origem padrão
2. **Consolidação de entidades únicas**: Remove duplicatas de produtos e locais
3. **Inferência de tipo de preço**: Define tipo baseado no local (porto=FOB, cidade=CIF)
4. **Estimativa de variação**: Converte símbolos (▲, ▼, =) em valores numéricos
5. **Validação de dados**: Garante consistência dos tipos de dados

### 3. Combinação de Dados

#### `combinar_listas(lista1, lista2, chave=None)`

Combina duas listas removendo duplicatas baseadas em chaves específicas.

**Parâmetros:**

- `lista1` (list): Primeira lista
- `lista2` (list): Segunda lista
- `chave` (list, opcional): Campos para identificar duplicatas

**Retorna:**

- `list`: Lista combinada sem duplicatas

#### `combinar_json(*partes)`

Combina múltiplos objetos JSON em um único resultado consolidado.

**Parâmetros:**

- `*partes`: Múltiplos dicionários JSON para combinar

**Retorna:**

- `dict`: JSON consolidado com todas as informações

**Exemplo:**

```python
parte1 = gerar_json_estruturado(texto_parte1)
parte2 = gerar_json_estruturado(texto_parte2)
resultado = combinar_json(parte1, parte2)
```

### 4. Persistência no Banco de Dados

#### `inserir_dados_no_banco(dados)`

Insere os dados processados no banco de dados relacional.

**Parâmetros:**

- `dados` (dict): Dados estruturados para inserção

**Funcionalidades:**

##### `get_or_create_local(nome, estado, pais, tipo)`

- Busca ou cria um registro de local
- **Retorna:** ID do local

##### `get_or_create_produto(produto_dict)`

- Busca ou cria um registro de produto
- **Retorna:** ID do produto

**Tabelas Afetadas:**

- `produtos`: Informações de fertilizantes
- `locais`: Cidades, portos, estados e países
- `precos`: Cotações e preços de mercado
- `fretes`: Custos de transporte
- `barter_ratios`: Razões de troca agrícola
- `cambio`: Taxas de câmbio
- `custos_portos`: Custos portuários

## Fluxo de Execução Principal

### Script Principal

```python
if __name__ == "__main__":
    # 1. Leitura do PDF
    print("📄 Lendo o relatório PDF...")
    texto = ler_pdf(CAMINHO_PDF)

    # 2. Divisão do texto
    partes = dividir_texto(texto, 15)

    # 3. Processamento com IA
    dados_partes = []
    for i, parte in enumerate(partes, 1):
        print(f"🤖 Processando a Parte {i} com Gemini...")
        try:
            dados = gerar_json_estruturado(parte)
            dados_partes.append(dados)
        except Exception as e:
            print(f"⚠️ Erro ao processar a Parte {i}: {e}")
            continue

    # 4. Combinação dos resultados
    print("🔀 Combinando os resultados...")
    dados_json = combinar_json(*dados_partes)

    # 5. Salvamento em arquivo
    json_path = "saida_gemini3.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2)

    # 6. Inserção no banco
    print("🗄️ Inserindo no banco...")
    inserir_dados_no_banco(dados_json)
```

## Tratamento de Erros

### Recuperação de JSON

O sistema implementa um mecanismo robusto de recuperação para casos onde a IA gera JSON incompleto:

```python
try:
    dados = json.loads(conteudo)
except json.JSONDecodeError as e:
    print("❌ Erro ao interpretar o JSON, tentando recuperação parcial...")
    ultimo_fecha = conteudo.rfind("}")
    if ultimo_fecha != -1:
        conteudo_corrigido = conteudo[:ultimo_fecha + 1]
        try:
            dados = json.loads(conteudo_corrigido)
            print("✅ Recuperação parcial bem-sucedida!")
            return dados
        except Exception:
            raise e
```

### Transações de Banco

Todas as operações de banco são realizadas em transações seguras:

```python
with engine.begin() as connection:
    # Operações de inserção
    # Commit automático ou rollback em caso de erro
```

## Configuração de Ambiente

### Variáveis Necessárias (.env)

```env
API_KEY=sua_api_key_do_google_gemini
DATABASE_URL=postgresql://usuario:senha@host:porta/database
```

### Dependências (requirements.txt)

```txt
PyMuPDF==1.23.0
google-generativeai==0.3.0
python-dotenv==1.0.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.0
```

## Prompt de IA Otimizado

A API utiliza um prompt específico para o Google Gemini que:

1. **Define estrutura clara**: Especifica exatamente o formato JSON esperado
2. **Instrui sobre completude**: Garante extração de todos os produtos e culturas
3. **Estabelece regras de negócio**: Define como tratar dados faltantes
4. **Padroniza saídas**: Normaliza formatos de data e moeda

### Categorias de Dados Extraídas

- **Fertilizantes**: Ureia, MAP, NPK, DAP, MOP, SSP, TSP, AN, Amsul
- **Culturas**: Soja, Milho, Algodão, Arroz, Café, Cana-de-açúcar
- **Modalidades de Frete**: Rodoviário, Marítimo, Ferroviário
- **Tipos de Preço**: FOB, CIF, EXW
- **Moedas**: USD, BRL, EUR

## Métricas de Performance

### Processamento por Partes

- **Texto pequeno (< 10k chars)**: 1-3 partes
- **Texto médio (10k-50k chars)**: 5-10 partes
- **Texto grande (> 50k chars)**: 10-15 partes

### Tempo de Processamento Estimado

- **Por parte**: 3-8 segundos (dependendo da API)
- **Relatório completo**: 1-5 minutos
- **Inserção no banco**: 5-15 segundos

## Monitoramento e Logs

### Logs de Execução

```python
print("📄 Lendo o relatório PDF...")
print(f"🤖 Processando a Parte {i} com Gemini...")
print("🔀 Combinando os resultados...")
print("🗄️ Inserindo no banco...")
print("✅ Dados inseridos com sucesso no banco Supabase!")
```

### Tratamento de Exceções

```python
try:
    dados = gerar_json_estruturado(parte)
    dados_partes.append(dados)
except Exception as e:
    print(f"⚠️ Erro ao processar a Parte {i}: {e}")
    continue  # Continua processamento com outras partes
```

## Integração com Dashboard

A API se integra perfeitamente com o sistema de dashboard através de:

### Interface Streamlit

```python
from processar_relatorio import processar_relatorio

# Processamento em thread separada
def threaded_processar_relatorio(caminho_pdf, num_partes):
    def executar_processamento():
        processar_relatorio(
            caminho_pdf,
            callback_progresso=progresso_callback,
            num_partes=num_partes
        )
```

### Monitoramento em Tempo Real

- **Barra de progresso**: Atualização visual do processamento
- **Callback de status**: Feedback em tempo real
- **Tratamento de erros**: Exibição de mensagens para o usuário

## Conclusão

A API de processamento de relatórios do Sistema Morro Verde representa uma solução robusta e escalável para automatização da extração de dados de fertilizantes. Através da combinação de tecnologias modernas como IA generativa, processamento de PDFs e banco de dados relacionais, o sistema oferece:

### Principais Vantagens

1. **Automação Completa**: Elimina a necessidade de entrada manual de dados
2. **Precisão**: Utiliza IA avançada para interpretação contextual
3. **Escalabilidade**: Processa relatórios de qualquer tamanho
4. **Robustez**: Implementa recuperação de erros e validação de dados
5. **Integração**: Conecta-se perfeitamente com o sistema de dashboard

### Impacto no Negócio

- **Redução de tempo**: De horas para minutos no processamento de relatórios
- **Diminuição de erros**: Eliminação de erros de digitação manual
- **Consistência**: Padronização na estrutura e formato dos dados
- **Análise avançada**: Dados estruturados permitem análises sofisticadas
- **Tomada de decisão**: Informações atualizadas em tempo real
