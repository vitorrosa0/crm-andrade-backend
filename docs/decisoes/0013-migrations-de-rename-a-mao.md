# ADR 0013 — Migrations de renomeação escritas à mão

**Status:** Aceito
**Data:** 2026-09-05

## Contexto

O fluxo normal do Alembic é gerar a migration automaticamente:

```bash
alembic revision --autogenerate -m "descricao"
```

O `--autogenerate` compara os models com o banco e escreve as operações
necessárias. Funciona bem para adicionar colunas, criar tabelas e mudar
tipos.

Ao quitar a dívida de nomenclatura ([ADR 0007](0007-nomenclatura-em-ingles.md)),
foi preciso renomear a tabela `clientes` para `clients` e quatro colunas.

**O Alembic não detecta renomeação.** Ele compara **listas de nomes**. Ao
ver que `nome` sumiu e `name` apareceu, conclui que uma coluna foi removida
e outra criada:

```python
op.drop_column('clients', 'nome')                    # ← apaga os dados
op.add_column('clients', sa.Column('name', ...))     # ← cria coluna vazia
```

Isso é sintaticamente válido, roda sem erro, e **destrói todos os dados
daquela coluna**. Pior: em desenvolvimento, com o banco vazio ou com dados
descartáveis, passa despercebido. O estrago só aparece em produção.

## Decisão

**Migrations que envolvem renomeação são escritas à mão**, usando
`ALTER ... RENAME`, e nunca aceitas do `--autogenerate` sem revisão.

```python
op.rename_table('clientes', 'clients')
op.alter_column('clients', 'nome', new_column_name='name')
```

Por extensão: **toda migration gerada automaticamente é lida antes de ser
aplicada.** O `--autogenerate` é um assistente, não uma autoridade.

## Justificativa

**`ALTER ... RENAME` preserva os dados.** É a operação que expressa a
intenção real: a coluna é a mesma, só o nome mudou.

**O risco é assimétrico.** Ler uma migration de 30 linhas custa dois
minutos. Não ler pode custar a base de dados de um escritório de advocacia.

**Existe uma classe inteira de casos assim.** Renomeação é o exemplo mais
perigoso, mas o `--autogenerate` também não lida bem com: mudanças de tipo
que precisam de conversão explícita (`USING`), migração de dados junto com o
schema, e constraints com dependências de ordem.

## O que a migration precisou fazer além do rename

A `b7c1d4e28f30` mostra por que o resultado automático não serviria de
qualquer forma. Além dos renames, ela precisou:

**1. Derrubar constraints antes, recriar depois.** As CHECK constraints
antigas referenciavam as colunas e os valores antigos. Sem removê-las
primeiro, o rename falharia ou deixaria uma constraint inválida.

**2. Migrar os dados, não só o schema.** Os valores mudaram de
`'FISICA'`/`'JURIDICA'` para `'INDIVIDUAL'`/`'COMPANY'`:

```python
op.execute("UPDATE clients SET person_type = 'INDIVIDUAL' WHERE person_type = 'FISICA'")
```

Sem isso, a nova CHECK constraint rejeitaria as linhas existentes e a
migration abortaria no meio.

**3. Preencher antes de exigir NOT NULL.** `created_at` passou a ser
obrigatório. Linhas antigas podiam ter nulo:

```python
op.execute("UPDATE clients SET created_at = now() WHERE created_at IS NULL")
op.alter_column('clients', 'created_at', nullable=False, server_default=sa.text('now()'))
```

Nada disso o `--autogenerate` teria produzido — ele não sabe nada sobre os
**dados**, só sobre a **estrutura**.

## Regra adicional: `downgrade` de verdade

O Alembic gera `pass` quando não sabe reverter. Deixar assim torna a
migration irreversível — e descobrir isso durante um rollback de produção é
o pior momento possível.

Ambas as migrations escritas à mão têm `downgrade` completo, que desfaz
schema **e** dados, na ordem inversa.

## Verificação obrigatória

Roteiro aplicado após cada migration escrita à mão:

```bash
alembic upgrade head     # aplica
alembic check            # model e banco estão sincronizados?
alembic downgrade -1     # a volta funciona?
alembic upgrade head     # e a ida de novo?
```

O `alembic check` é o passo que mais pega erro: se acusar diferença logo
após aplicar, a migration e o model divergiram — quase sempre porque a
migration foi editada à mão e o model não acompanhou.

Ambas as migrations do projeto passaram nesse roteiro.

## Consequências

**Positivas**

- Nenhum dado perdido em renomeação
- Migrations expressam a intenção real da mudança
- `downgrade` confiável e testado
- Migração de dados e de schema no mesmo lugar, aplicadas atomicamente
  (o Postgres tem DDL transacional)

**Negativas**

- **Mais trabalho manual**, e exige conhecer as operações do Alembic
- **Exige saber que o problema existe.** Alguém que não conheça essa
  armadilha vai aceitar o resultado do `--autogenerate` — daí este ADR e o
  aviso destacado em [06 — Migrations](../06-migrations.md)
- Migration escrita à mão pode divergir do model. Mitigado pelo
  `alembic check`

## Alternativas consideradas

**Aceitar `drop` + `create` em ambiente de desenvolvimento** — Funcionaria
hoje, com o banco praticamente vazio. Descartado por criar o hábito errado:
a mesma migration seria aplicada em produção um dia.

**Não renomear** — Evitaria o problema por completo. Descartado: o custo de
manter nomenclatura mista cresce com o tempo, e o momento mais barato para
renomear era antes do módulo de cobrança. Ver
[ADR 0007](0007-nomenclatura-em-ingles.md).

**Dump, transformar, restore** — Exportar, renomear no SQL, reimportar.
Descartado por ser manual, irreprodutível e não versionado — exatamente o
que o Alembic existe para evitar.
