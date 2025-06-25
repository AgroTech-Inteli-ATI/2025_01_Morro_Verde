---
sidebar_position: 1
slug: /sistema/funcionalidades
description: "Principais funcionalidades do Dashboard Morro Verde"
---

# Principais Funcionalidades

## Dashboard de Preços

- Visualiza preços de fertilizantes (Ureia, MAP, DAP, SSP, TSP, MOP, NPK)
- Compara preços entre regiões e produtos
- Mostra histórico de variações
- Converte automaticamente USD/BRL

## Processamento de PDFs

- Extrai dados de relatórios automaticamente usando Google Gemini
- Identifica preços, produtos, localizações e fretes
- Processa documentos dividindo em partes menores
- Valida e limpa dados automaticamente

## Sistema de Previsões

- Acesse através do botão **"📊 Previsões"** na sidebar
- Selecione produto, origem e destino
- Escolha período (1-12 meses)
- Gera cenários: neutro, otimista e pessimista
- Usa algoritmos XGBoost e Random Forest
- Calcula intervalos de confiança

## Alertas Automáticos

- Detecta variações de preço > 10%
- Mostra alertas visuais na tela principal
- Identifica produtos e regiões com mudanças significativas

## Análise de Fretes

- Monitora custos rodoviários e marítimos
- Calcula valor entregue (preço + frete)
- Analisa rotas origem-destino

## Filtros e Visualizações

- Filtra por produto, localização, moeda e período
- Gráficos interativos com zoom e detalhes
- Boxplots para identificar outliers
- Mapas de calor para comparação visual
- Análise de correlação entre produtos

## Backup e Restauração

- Backup automático antes de cada importação
- Mantém últimos 5 backups em CSV
- Restauração com um clique
- Log de todas as ações realizadas

## Entrada Manual de Dados

- Formulário para dados pontuais
- Campos para preços e fretes
- Validação automática de entrada