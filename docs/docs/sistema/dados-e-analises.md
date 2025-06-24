---
sidebar_position: 2
slug: /sistema/dados-e-analises
description: "Tipos de dados processados e análises disponíveis"
---

# Dados e Análises

## Dados Processados

### Preços de Fertilizantes
- **Produtos**: Ureia, MAP, DAP, SSP, TSP, MOP, NPK, Amsul, AN
- **Origens**: Brasil, China, EUA, Marrocos, Rússia, Egito
- **Tipos**: FOB, CIF, EXW
- **Modalidades**: Spot, Contrato, Indicativo
- **Moedas**: USD, BRL, EUR

### Dados Logísticos
- **Fretes rodoviários**: Entre cidades brasileiras
- **Fretes marítimos**: Rotas internacionais
- **Portos**: Santos, Paranaguá, Rio Grande, Vitória
- **Custos**: Armazenagem e demurrage

### Informações Econômicas
- **Câmbio**: USD/BRL para conversões
- **Barter ratios**: Soja, Milho, Algodão, Café, Arroz, Cana
- **Regiões**: Todos estados brasileiros

## Análises Disponíveis

### Histórico de Preços
- Evolução temporal por produto
- Comparação entre regiões
- Identificação de tendências

### Distribuição de Preços
- Boxplots com quartis e outliers
- Estatísticas: média, mediana, desvio padrão
- Detecção automática de valores atípicos

### Correlação Entre Produtos
- Matriz visual de correlações
- Identifica produtos que se movem juntos
- Heatmap com escala de cores

### Análise Sazonal
Quando há dados suficientes (24+ meses):
- Decomposição em tendência e sazonalidade
- Padrões anuais de comportamento
- Identificação de períodos sazonais

### Alertas de Variação
- Variações > 10% destacadas automaticamente
- Comparação mensal e semanal
- Alertas visuais por produto/região

## KPIs Principais

- **Produtos únicos** monitorados
- **Localizações** cobertas
- **Registros** de preços e fretes
- **Preço médio** por produto
- **Cobertura temporal** dos dados

## Controle de Qualidade

### Detecção de Outliers
- **Método IQR**: Remove valores fora de 1,5x o intervalo interquartil
- **Validação contextual**: Considera características do produto
- **Preserva eventos reais**: Não remove variações legítimas de mercado

### Tratamento de Dados
- Preenche campos vazios automaticamente
- Consolida produtos e locais similares
- Remove duplicatas
- Valida datas e moedas

### Limpeza Automática
- Padroniza nomes de produtos e locais
- Converte formatos de data
- Normaliza unidades de medida
- Estima variações baseado em símbolos (▲▼=)