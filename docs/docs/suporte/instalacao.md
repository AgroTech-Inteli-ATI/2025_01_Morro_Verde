---
sidebar_position: 1
slug: /suporte/instalacao
description: "Guia de instalação e execução do Dashboard Morro Verde"
---

# Instalação e Execução

## Executando o Sistema

### Dashboard Principal
```bash
cd src/
streamlit run app.py
```
Acesse: `http://localhost:8501`

### Documentação
```bash
cd docs/
npm run start
```
Acesse: `http://localhost:3000`

## Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Memória RAM**: 4GB mínimo, 8GB recomendado
- **Espaço em disco**: 2GB livres
- **Conexão**: Internet estável
- **Navegador**: Chrome, Firefox, Safari ou Edge (versões recentes)

## Configuração Inicial

### Variáveis de Ambiente
Certifique-se de que o arquivo `.env` contém:
```bash
API_KEY=sua_chave_google_gemini
DATABASE_URL=sua_url_supabase_postgresql
```

### Primeira Execução
1. O banco será criado automaticamente
2. Importe um relatório PDF para popular com dados iniciais
3. Teste funcionalidades básicas de filtro e visualização
4. Verifique a pasta `backups_csv/` para confirmar sistema de backup

## Problemas Comuns na Instalação

### Erro: Módulos não encontrados
```bash
pip install -r requirements.txt
```

### Erro: Porta ocupada
- Mude a porta: `streamlit run app.py --server.port 8502`
- Ou finalize processos que usam a porta 8501

### Erro: Permissões
- Linux/Mac: Use `sudo` se necessário
- Windows: Execute como administrador

### Erro: Python não encontrado
- Verifique se Python está no PATH
- Use `python3` ao invés de `python` em sistemas Unix

## Problemas Operacionais

### PDF não processa
**Soluções:**
- **Arquivo grande**: Aumente "Partes" para 12-15
- **PDF com imagens**: Certifique-se que contém texto selecionável
- **Conexão instável**: Verifique internet
- **Limite de API**: Aguarde alguns minutos

### Dashboard lento
**Otimizações:**
- Use filtros para reduzir volume de dados
- Feche outras aplicações pesadas
- Reinicie: `Ctrl+C` e execute novamente
- Aplique filtros de período

### Erro de conexão com banco
**Verificações:**
- Arquivo `.env` configurado corretamente
- URL do Supabase válida
- Conexão com internet ativa
- Firewall liberando conexões HTTPS

### Dados inconsistentes após importação
**Soluções:**
- Use "Desfazer Última Atualização" no final da página
- Verifique se PDF é de relatório de fertilizantes
- Tente com número diferente de "Partes"
- Confirme que PDF tem dados de preços

## Sistema de Previsões

### Erro: "Dados insuficientes para previsão"
**Requisitos mínimos:**
- 10+ registros históricos para o produto
- Campo origem deve estar preenchido
- Pelo menos um registro dos últimos 6 meses

### Previsões imprecisas
**Verificações:**
- Sistema remove outliers automaticamente
- Considera padrões sazonais históricos
- Verifique qualidade dos dados de entrada
- Experimente diferentes cenários (neutro/otimista/pessimista)

## Verificações de Funcionamento

### Checklist Diário
- [ ] Dashboard carrega em menos de 30 segundos
- [ ] Dados mostram registros recentes
- [ ] Gráficos respondem a filtros
- [ ] Alertas detectam variações > 10%

### Checklist Semanal
- [ ] Backups estão sendo criados (pasta `backups_csv/`)
- [ ] Import de PDFs funciona
- [ ] Previsões geram resultados
- [ ] Performance estável

## Manutenção Preventiva

### Backups
- **Frequência**: Automático antes de cada importação
- **Localização**: Pasta `backups_csv/`
- **Retenção**: Últimos 5 backups mantidos
- **Restauração**: Botão "Desfazer Última Atualização"

### Limpeza
- Arquivos temporários em `relatorios/` podem ser removidos
- Logs antigos podem ser arquivados
- Backups > 30 dias podem ser removidos manualmente

### Monitoramento
- Verifique logs no terminal para erros
- Monitore uso de memória do sistema
- Acompanhe tempo de resposta das queries