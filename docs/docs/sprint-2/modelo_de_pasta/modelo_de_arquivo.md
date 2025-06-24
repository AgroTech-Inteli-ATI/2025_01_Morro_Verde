# Módulo de Banco de Dados - db.py

## Introdução

O módulo `db.py` é um componente fundamental do sistema Morro Verde, responsável por gerenciar todas as operações de banco de dados relacionadas ao armazenamento e recuperação de informações sobre fertilizantes. Este módulo implementa uma camada de abstração para interações com o banco de dados SQLite, fornecendo uma interface simples e eficiente para operações CRUD (Create, Read, Update, Delete).

O sistema utiliza SQLite como banco de dados local, proporcionando uma solução leve e confiável para o armazenamento de dados sem a necessidade de configurações complexas de servidor. Esta documentação foi criada para a plataforma Docusaurus, garantindo uma apresentação clara e navegável da funcionalidade do módulo.

## Visão Geral da Arquitetura

O módulo segue um padrão de design simples e direto, com funções específicas para cada operação de banco de dados:

- **Conexão**: Gerenciamento de conexões com o banco SQLite
- **Criação**: Inicialização da estrutura de tabelas
- **Inserção**: Adição de novos registros de fertilizantes
- **Consulta**: Recuperação de dados armazenados

## Estrutura do Banco de Dados

### Tabela: fertilizantes

A tabela principal do sistema armazena informações sobre fertilizantes com a seguinte estrutura:

| Campo | Tipo | Descrição | Restrições |
|-------|------|-----------|------------|
| `id` | INTEGER | Identificador único do fertilizante | PRIMARY KEY, AUTOINCREMENT |
| `nome` | TEXT | Nome do fertilizante | NOT NULL |
| `preco` | REAL | Preço do fertilizante | NOT NULL |
| `fornecedor` | TEXT | Nome do fornecedor | NOT NULL |
| `data_atualizacao` | TEXT | Data da última atualização | NOT NULL |

## Funções Disponíveis

### `criar_conexao()`

**Descrição**: Estabelece uma conexão com o banco de dados SQLite.

**Parâmetros**: Nenhum

**Retorno**: Objeto de conexão SQLite3

**Exemplo de uso**:
```python
conn = criar_conexao()
```

**Detalhes técnicos**:
- Conecta ao arquivo de banco `morro_verde.db`
- Cria o arquivo automaticamente se não existir
- Retorna um objeto de conexão para operações subsequentes

---

### `criar_tabela()`

**Descrição**: Cria a tabela `fertilizantes` no banco de dados caso ela não exista.

**Parâmetros**: Nenhum

**Retorno**: Nenhum

**Exemplo de uso**:
```python
criar_tabela()
```

**Detalhes técnicos**:
- Utiliza `CREATE TABLE IF NOT EXISTS` para evitar erros
- Define a estrutura completa da tabela com tipos e restrições
- Executa commit automático e fecha a conexão
- Operação idempotente (pode ser executada múltiplas vezes sem efeitos colaterais)

---

### `inserir_fertilizante(nome, preco, fornecedor, data_atualizacao)`

**Descrição**: Insere um novo registro de fertilizante no banco de dados.

**Parâmetros**:
- `nome` (str): Nome do fertilizante
- `preco` (float): Preço do fertilizante
- `fornecedor` (str): Nome do fornecedor
- `data_atualizacao` (str): Data da atualização no formato string

**Retorno**: Nenhum

**Exemplo de uso**:
```python
inserir_fertilizante("NPK 10-10-10", 45.50, "AgroTech Ltda", "2024-01-15")
```

**Detalhes técnicos**:
- Utiliza prepared statements (?) para prevenir SQL injection
- Executa commit automático após a inserção
- Fecha a conexão automaticamente
- O ID é gerado automaticamente pelo AUTOINCREMENT

---

### `consultar_fertilizantes()`

**Descrição**: Recupera todos os registros de fertilizantes do banco de dados.

**Parâmetros**: Nenhum

**Retorno**: Lista de tuplas contendo todos os registros da tabela

**Exemplo de uso**:
```python
fertilizantes = consultar_fertilizantes()
for fertilizante in fertilizantes:
    print(f"ID: {fertilizante[0]}, Nome: {fertilizante[1]}, Preço: {fertilizante[2]}")
```

**Detalhes técnicos**:
- Executa SELECT * para recuperar todos os campos
- Utiliza `fetchall()` para obter todos os registros
- Retorna uma lista vazia se não houver registros
- Fecha a conexão automaticamente após a consulta

## Exemplo de Uso Completo

```python
import db

# Inicializar o banco de dados
db.criar_tabela()

# Inserir alguns fertilizantes
db.inserir_fertilizante("NPK 20-05-20", 52.00, "FertilMax", "2024-01-20")
db.inserir_fertilizante("Ureia", 38.75, "AgroSupply", "2024-01-18")
db.inserir_fertilizante("Superfosfato Simples", 28.90, "NutriPlant", "2024-01-22")

# Consultar todos os fertilizantes
fertilizantes = db.consultar_fertilizantes()

print("Fertilizantes cadastrados:")
for fert in fertilizantes:
    print(f"ID: {fert[0]} | Nome: {fert[1]} | Preço: R$ {fert[2]:.2f} | Fornecedor: {fert[3]} | Atualizado em: {fert[4]}")
```

## Considerações de Segurança

- **SQL Injection**: O módulo utiliza prepared statements com placeholders (?) para prevenir ataques de SQL injection
- **Gerenciamento de Conexões**: Todas as funções fecham as conexões automaticamente para evitar vazamentos de recursos
- **Transações**: Cada operação de escrita inclui commit automático para garantir persistência dos dados

## Limitações Conhecidas

1. **Concorrência**: SQLite tem limitações para acesso concorrente de escrita
2. **Validação**: Não há validação de tipos ou formatos de dados na camada de banco
3. **Tratamento de Erros**: Ausência de tratamento específico para exceções de banco de dados
4. **Operações CRUD**: Faltam funções para atualização e exclusão de registros

## Conclusão

O módulo `db.py` fornece uma base sólida e funcional para o gerenciamento de dados de fertilizantes no sistema Morro Verde. Sua implementação simples e direta facilita a manutenção e compreensão do código, enquanto o uso de SQLite garante confiabilidade e portabilidade.

A arquitetura atual atende adequadamente aos requisitos básicos de armazenamento e recuperação de dados, proporcionando uma fundação estável para futuras expansões do sistema. Para ambientes de produção ou sistemas com maior complexidade, recomenda-se considerar a implementação de funcionalidades adicionais como tratamento de erros, validação de dados e operações CRUD completas.

Esta documentação, criada especificamente para a plataforma Docusaurus, serve como referência técnica para desenvolvedores que trabalham com o sistema Morro Verde, facilitando a compreensão e manutenção do código relacionado ao gerenciamento de banco de dados.
