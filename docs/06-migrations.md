# 06 — Migrations (Alembic)

## O que é e por que existe

Uma migration é um arquivo Python versionado que descreve **uma mudança no
schema do banco**. Cada uma sabe se aplicar (`upgrade`) e se desfazer
(`downgrade`), e aponta para a anterior — formando uma corrente.

Sem isso, o schema do banco viveria só na cabeça de quem o criou. Com isso,
o banco é reconstituível a partir do repositório, e a evolução do schema
entra no code review junto com o código que depende dela.

## Histórico

| Revisão | Descrição |
|---|---|
| `ec6f5bd69c7c` | Cria a tabela `clientes` |
| `b7c1d4e28f30` | Renomeia tudo para inglês; `created_at` ganha `NOT NULL` + `server_default` |
| `c93a5f17b204` | Unicidade de CPF e CNPJ |
| `d24e8b91fa07` | Normaliza CPF e CNPJ para apenas dígitos |

```
ec6f5bd69c7c  →  b7c1d4e28f30  →  c93a5f17b204  →  d24e8b91fa07  (head)
```

## Fluxo normal

```bash
# 1. Altere o model em app/models/
# 2. Gere a migration
alembic revision --autogenerate -m "descricao curta"

# 3. ABRA O ARQUIVO GERADO E LEIA. Sempre.
# 4. Aplique
alembic upgrade head

# 5. Confirme que não sobrou diferença
alembic check
```

O passo 3 não é opcional. O `--autogenerate` é um **assistente**, não uma
autoridade: ele compara os models com o banco e chuta o que fazer. Às vezes
chuta errado — e o modo mais caro de errar é o descrito a seguir.

## ⚠️ A armadilha: renomeações

**O Alembic não detecta renomeação.** Ele compara listas de nomes. Se você
renomear a coluna `nome` para `name`, ele vê "sumiu uma coluna `nome`" e
"apareceu uma coluna `name`", e gera:

```python
op.drop_column('clients', 'nome')       # ← APAGA todos os dados da coluna
op.add_column('clients', sa.Column('name', ...))
```

Isso passa nos testes com o banco vazio e **destrói dados em produção**.

O correto é escrever à mão:

```python
op.alter_column('clients', 'nome', new_column_name='name')
```

`ALTER TABLE ... RENAME` preserva o conteúdo. O mesmo vale para renomear
tabelas (`op.rename_table`).

A migration `b7c1d4e28f30` é o exemplo real no projeto — foi escrita
inteiramente à mão por esse motivo. Ver
[ADR 0013](decisoes/0013-migrations-de-rename-a-mao.md).

## Regras adotadas no projeto

### 1. Sempre implementar o `downgrade`

O Alembic gera `pass` ou levanta `NotImplementedError` quando não sabe o
que fazer. Deixar assim significa que a migration é irreversível — e
descobrir isso durante um rollback de produção às 23h é péssimo.

Ambas as migrations escritas à mão neste projeto têm `downgrade` completo
e **testado** (`alembic downgrade -1 && alembic upgrade head`).

### 2. Ordem importa quando há constraints

Constraints referenciam colunas e valores. Se você renomear uma coluna que
uma CHECK constraint usa, ou mudar os valores que ela valida, a constraint
precisa **cair antes e ser recriada depois**:

```python
def upgrade():
    op.drop_constraint('check_tipo_pessoa_valido', 'clientes', type_='check')
    # ... renomeia coluna, migra os dados ...
    op.create_check_constraint('check_person_type_valid', 'clients', "...")
```

No `downgrade`, a ordem se inverte.

### 3. Migrar dados, não só schema

Uma migration pode conter `UPDATE`. Quando `person_type` mudou de
`'FISICA'` para `'INDIVIDUAL'`, as linhas existentes precisaram ser
convertidas:

```python
op.execute("UPDATE clients SET person_type = 'INDIVIDUAL' WHERE person_type = 'FISICA'")
```

Sem isso, a nova CHECK constraint rejeitaria as linhas antigas e a
migration falharia no meio.

### 4. Preencher antes de exigir NOT NULL

`ALTER COLUMN ... SET NOT NULL` falha se qualquer linha tiver nulo. Sempre
preencha primeiro:

```python
op.execute("UPDATE clients SET created_at = now() WHERE created_at IS NULL")
op.alter_column('clients', 'created_at', nullable=False, server_default=sa.text('now()'))
```

### 5. Avisar sobre pré-condições no docstring

A migration `c93a5f17b204` (unicidade) falha se já houver documentos
duplicados no banco. O docstring dela traz a query para conferir antes de
aplicar. Quem for aplicar em produção precisa saber disso **antes** de
rodar, não depois de falhar.

### 6. Verificar o resultado, não confiar

Roteiro completo usado após cada migration deste projeto:

```bash
alembic upgrade head        # aplica
alembic check               # confirma que model e banco batem
alembic downgrade -1        # testa a volta
alembic upgrade head        # e a ida de novo
```

Se `alembic check` acusar diferença logo após aplicar a migration, o model
e a migration divergiram — quase sempre porque a migration foi editada à
mão e o model não acompanhou (ou vice-versa).

## `alembic check` e por que ele é útil

Compara os models com o banco atual e falha se houver diferença. Serve para
pegar o caso clássico: alguém altera um model e esquece de gerar a
migration. O código funciona na máquina dele (onde o banco foi alterado à
mão) e quebra em todas as outras.

É um bom candidato a rodar em CI, quando houver CI.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `Target database is not up to date` | Faltou `alembic upgrade head` |
| `Can't locate revision identified by '...'` | A tabela `alembic_version` aponta para uma revisão que não existe mais no repositório (arquivo deletado ou branch trocada) |
| `--autogenerate` gera migration vazia | O model novo não foi importado em `alembic/env.py` |
| `--autogenerate` quer dropar tabelas que você não conhece | O `target_metadata` não enxerga todos os models |
| Migration falha no meio | O Postgres tem DDL transacional: nada foi aplicado. Corrija e rode de novo |

Sobre o penúltimo caso: todo model novo precisa ser importado em
`alembic/env.py`, senão o Alembic não sabe que ele existe:

```python
from app.models.client import Client  # noqa: F401
```
