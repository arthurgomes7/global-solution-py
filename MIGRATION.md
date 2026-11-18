# MIGRATION — Criação das tabelas no PostgreSQL

Este documento descreve como o banco de dados do **Agendador de Queima Prescrita** é criado e versionado.

## 1. Pré-requisitos

- PostgreSQL 14 ou superior rodando (local ou remoto)
- Um usuário com permissão de criar tabelas (ex.: `postgres`)
- Dependências do projeto instaladas: `py -m pip install -r requirements.txt`

## 2. Criar o banco

Uma única vez, crie o banco `queimas`:

```bash
psql -U postgres -c "CREATE DATABASE queimas;"
```

(ou pelo pgAdmin: *Databases → Create → Database…* com o nome `queimas`)

## 3. Configurar a conexão

Copie `.env.example` para `.env` e ajuste usuário e senha:

```
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=queimas
DB_USER=postgres
DB_PASSWORD=sua_senha
```

A API lê esse arquivo ao iniciar. O `.env` está no `.gitignore` para a senha não ir junto com o código.

## 4. Aplicar as migrations

Os scripts ficam em [`migrations/`](migrations/) e são aplicados **em ordem alfabética** (por isso o prefixo numérico).

**Opção A — automática:** ao subir a API (`py app.py`), a função `criar_tabela()` em `database.py` executa todos os scripts `.sql` da pasta.

**Opção B — manual, via psql:**

```bash
psql -U postgres -d queimas -f migrations/001_create_agendamentos.sql
psql -U postgres -d queimas -f migrations/002_create_brigadistas.sql
psql -U postgres -d queimas -f migrations/003_add_brigadista_em_agendamentos.sql
```

Os scripts usam `IF NOT EXISTS` (`CREATE TABLE`, `ADD COLUMN`, `CREATE INDEX`), então podem ser executados mais de uma vez sem erro nem perda de dados.

## 5. Migrations existentes

### `001_create_agendamentos.sql`

Cria a tabela `agendamentos`:

| Coluna | Tipo | Regras |
|---|---|---|
| `id` | `SERIAL` | Chave primária, gerada automaticamente |
| `solicitante` | `VARCHAR(150)` | Obrigatório |
| `endereco` | `VARCHAR(255)` | Obrigatório |
| `area_hectares` | `DOUBLE PRECISION` | Obrigatório, maior que zero |
| `data_prevista` | `DATE` | Obrigatório |
| `descricao` | `TEXT` | Opcional |
| `analise_brigadista` | `VARCHAR(20)` | Padrão `em_analise`; só aceita `em_analise`, `aceita`, `recusada` |
| `criado_em` | `TIMESTAMP` | Preenchido automaticamente com a data/hora da inserção |

As regras `CHECK` garantem a integridade dos dados direto no banco, mesmo que alguém insira registros fora da API.

**Exclusão lógica:** nenhum registro é apagado. O `DELETE` da API marca `analise_brigadista = 'recusada'`, e os registros nesse status ficam fora das consultas `GET`.

### `002_create_brigadistas.sql`

Cria a tabela `brigadistas`, com os responsáveis por analisar as solicitações:

| Coluna | Tipo | Regras |
|---|---|---|
| `id` | `SERIAL` | Chave primária, gerada automaticamente |
| `nome` | `VARCHAR(150)` | Obrigatório |
| `brigada` | `VARCHAR(150)` | Obrigatório |
| `regiao` | `VARCHAR(150)` | Obrigatório |
| `criado_em` | `TIMESTAMP` | Preenchido automaticamente com a data/hora da inserção |

### `003_add_brigadista_em_agendamentos.sql`

Cria o relacionamento entre as duas tabelas (um brigadista analisa vários agendamentos):

- Adiciona a coluna `brigadista_id INTEGER` em `agendamentos`, com chave estrangeira para `brigadistas(id)`. O banco recusa qualquer `brigadista_id` que não exista.
- A coluna fica nula enquanto a solicitação está `em_analise` e é preenchida quando um brigadista aceita ou recusa.
- Cria o índice `idx_agendamentos_brigadista`, usado na consulta `GET /brigadistas/{id}/agendamentos`.

Essa mudança foi feita numa migration nova, sem alterar a `001`, que já tinha sido aplicada. Os registros que já existiam continuam válidos, com `brigadista_id` nulo.

## 6. Conferir se deu certo

```bash
psql -U postgres -d queimas -c "\d agendamentos"
psql -U postgres -d queimas -c "\d brigadistas"
```

Em `\d agendamentos` deve aparecer a coluna `brigadista_id` e a restrição `agendamentos_brigadista_id_fkey`.

## 7. Criando uma nova migration

1. Crie um arquivo com o próximo número: `migrations/004_descricao_curta.sql`
2. Escreva SQL idempotente (`IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`…)
3. Nunca altere uma migration que já foi aplicada; crie uma nova

Exemplo:

```sql
-- 004: adiciona telefone do solicitante
ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);
```

## 8. Desfazer (rollback)

Para recriar o banco do zero (**apaga todos os dados**):

```sql
DROP TABLE IF EXISTS agendamentos;
DROP TABLE IF EXISTS brigadistas;
```

A ordem importa: `agendamentos` sai primeiro porque depende de `brigadistas` pela chave estrangeira.

Depois, aplique as migrations novamente (passo 4).
