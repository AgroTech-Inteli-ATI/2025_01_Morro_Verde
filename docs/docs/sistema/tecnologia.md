---
sidebar_position: 3
slug: /sistema/tecnologia
description: "Visão técnica do Dashboard Morro Verde"
---

# Visão Técnica do Sistema

## Arquitetura

### Tecnologias Utilizadas
- **Frontend**: Streamlit (interface web)
- **Backend**: Python com SQLAlchemy
- **Banco de Dados**: PostgreSQL no Supabase
- **IA**: Google Gemini 1.5 Flash
- **Machine Learning**: Scikit-learn, XGBoost
- **Gráficos**: Plotly

### Fluxo de Dados
1. PDF → Google Gemini (extração)
2. Dados → Validação e limpeza
3. PostgreSQL → Armazenamento
4. Análises → Visualizações
5. Machine Learning → Previsões

## Processamento de PDFs

### Como Funciona
- **Divisão**: PDF dividido em partes menores (evita limitações de tamanho)
- **Extração**: Google Gemini identifica preços, produtos e localizações
- **Validação**: Sistema verifica consistência dos dados
- **Combinação**: Partes são reunidas em dataset único

### Dados Extraídos Automaticamente
- Preços FOB/CIF/EXW com faixas min/max
- Produtos fertilizantes e formulações
- Localizações (portos, estados, países)
- Fretes rodoviários e marítimos
- Câmbio USD/BRL
- Barter ratios por cultura

## Modelos de Previsão

### Algoritmos
- **XGBoost**: Gradient boosting otimizado
- **Random Forest**: Ensemble de árvores de decisão
- **Seleção automática**: Sistema escolhe melhor modelo baseado na precisão

### Features Utilizadas
- **Temporais**: Mês, trimestre, sazonalidade
- **Históricas**: Preços passados (lags)
- **Econômicas**: Câmbio, custos portuários
- **Geográficas**: Origem, destino, tipo de local

### Validação
- **TimeSeriesSplit**: Respeita ordem cronológica
- **Métricas**: MAE, RMSE, MAPE
- **Intervalos de confiança**: 95% usando bootstrap

## Banco de Dados

### Migração SQLite → PostgreSQL
- **Antes**: SQLite local
- **Agora**: PostgreSQL no Supabase
- **Vantagens**: Maior performance, múltiplos usuários, backup automático

### Estrutura Principal
```sql
produtos (id, nome_produto, formulacao, origem)
locais (id, nome, estado, pais, tipo)
precos (produto_id, local_id, data, preco_min, preco_max)
fretes (origem_id, destino_id, custo_usd, custo_brl)
cambio (data, usd_brl)
```

## Performance

### Otimizações
- **Threading**: Processamento paralelo de PDFs
- **Cache**: Dados frequentes mantidos em memória
- **Batch processing**: Inserções em lote
- **Indexação**: Queries otimizadas no PostgreSQL

### Backup e Segurança
- **Backup automático**: Antes de cada importação
- **Retenção**: 5 backups mais recentes
- **Restauração**: Um clique para desfazer
- **Logs**: Histórico completo de ações

## Interface

### Streamlit
- **Responsivo**: Funciona em desktop e mobile
- **Interativo**: Gráficos com zoom e filtros
- **Real-time**: Atualizações automáticas
- **Simples**: Deploy com um comando

### Visualizações
- **Plotly**: Gráficos interativos
- **Filtros dinâmicos**: Atualizações em tempo real
- **Export**: PNG, PDF, CSV
- **Hover**: Detalhes ao passar mouse

## Escalabilidade

### Atual
- Suporta múltiplos usuários simultâneos
- Processamento de PDFs até 50+ páginas
- Milhares de registros de preços
- Análises em tempo real

### Futuro
- APIs REST para integração
- Processamento assíncrono
- Cache distribuído
- Deploy em containers