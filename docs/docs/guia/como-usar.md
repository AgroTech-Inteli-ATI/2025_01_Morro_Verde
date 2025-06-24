---
sidebar_position: 1
slug: /guia/como-usar
description: "Guia prático para utilizar o Dashboard Morro Verde"
---

# Como Usar o Dashboard

## Acessando o Sistema

Execute na pasta `src/`:
```bash
streamlit run app.py
```

O sistema abre em `http://localhost:8501`

## Importando Relatórios PDF

1. Clique em **"📥 IMPORTAR RELATÓRIO"**
2. Selecione o arquivo PDF
3. Ajuste as "Partes" (10-15 para relatórios grandes)
4. Clique em **"IMPORTAR RELATÓRIO"**

O sistema extrai automaticamente preços, produtos e localizações usando IA.

## Inserindo Dados Manualmente

1. Clique em **"📝 INPUTAR DADOS"**
2. Preencha:
   - Nome do produto (ex: Ureia, MAP)
   - Localização (ex: Santos, Paranaguá)
   - Preço e moeda
   - Data
3. Opcionalmente adicione dados de frete
4. Salve apenas preço ou preço + frete

## Usando os Filtros

1. Clique em **"🔍 FILTRAR DADOS"**
2. Selecione produtos, localizações e período
3. Clique em **"✅ Aplicar Filtros"**

Os gráficos se atualizam automaticamente.

## Interpretando os Gráficos

### Histórico de Preços
- Linhas coloridas = produtos diferentes
- Pontos = registros individuais de preço
- Passe o mouse para ver detalhes

### Alertas de Variação
- **Verde**: Aumento > 10%
- **Vermelho**: Queda > 10%
- Mostra produto, local e percentual

### Mapa de Calor
- Cores quentes = preços altos
- Cores frias = preços baixos

## Restaurando Dados

Se algo der errado:
1. Role até o final da página
2. Clique em **"Desfazer Última Atualização"**

O sistema mantém backups automáticos antes de cada importação.