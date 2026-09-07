# ADR 0006 — String + CHECK em vez de ENUM

**Status:** Aceito
**Data:** 2026-07

## Contexto

`person_type` aceita exatamente dois valores: `INDIVIDUAL` e `COMPANY`.
Existem três formas de garantir isso no Postgres:

1. Tipo `ENUM` nativo
2. `String` + `CHECK constraint`
3. Tabela de referência + `FOREIGN KEY`

## Decisão

**`String` com `CHECK constraint`.**

```python
person_type = Column(String, nullable=False)

CheckConstraint(
    "person_type IN ('INDIVIDUAL', 'COMPANY')",
    name="check_person_type_valid"
)
```

## Justificativa

**Alterar um ENUM no Postgres é desconfortável.** `ALTER TYPE ... ADD VALUE`
tem restrições reais — historicamente não podia rodar dentro de um bloco
de transação, o que atrita com o modo como o Alembic aplica migrations. E
**remover** ou **renomear** um valor de ENUM exige recriar o tipo inteiro e
atualizar todas as colunas que o usam.

Uma CHECK constraint se altera com `DROP CONSTRAINT` + `CREATE CONSTRAINT`.
Duas linhas, dentro da transação, sem cerimônia.

Isso deixou de ser hipotético: a migration `b7c1d4e28f30` precisou trocar
os valores de `'FISICA'`/`'JURIDICA'` para `'INDIVIDUAL'`/`'COMPANY'`. Com
CHECK, foi derrubar a constraint, rodar um `UPDATE` e recriar. Com ENUM
teria sido consideravelmente mais trabalhoso.

**A validação já existe na aplicação.** O `Literal["INDIVIDUAL", "COMPANY"]`
do Pydantic barra o valor inválido antes de chegar ao banco. A constraint é
a segunda linha de defesa, não a única — ver
[ADR 0008](0008-validacao-em-duas-camadas.md).

**Simplicidade de leitura.** Um `varchar` com CHECK é compreensível para
qualquer pessoa que abra o banco. Um tipo customizado exige consultar o
catálogo para descobrir quais valores existem.

## Consequências

**Positivas**
- Adicionar, remover ou renomear valores é barato
- Sem tipo customizado no banco para manter
- Migrations mais simples

**Negativas**
- **Ocupa mais espaço** que um ENUM (que é armazenado como inteiro
  internamente). Irrelevante nesta escala
- **A lista de valores válidos está em três lugares**: no `Literal` do
  Pydantic, na CHECK constraint e no comentário do model. Podem divergir.
  Mitigação: se crescer, extrair para uma constante única
- Nenhuma garantia de tipo em Python — `person_type` é `str`, e um typo só
  aparece em runtime

## Alternativas consideradas

**`ENUM` nativo do Postgres** — Mais eficiente e auto-documentado no banco.
Descartado pela dificuldade de evolução, que se materializou logo na
segunda migration.

**`Enum` do Python + `sa.Enum`** — Daria segurança de tipo em Python. Mas o
SQLAlchemy traduz isso para um ENUM nativo no Postgres, herdando o mesmo
problema. Usar `sa.Enum(native_enum=False)` produziria varchar + check —
essencialmente a decisão adotada, com uma camada a mais de abstração. Foi
preferido o explícito.

**Tabela de referência (`person_types`) + FK** — Permitiria adicionar
valores sem migration e guardar metadados (rótulo para exibição). Descartado
por *over-engineering*: são dois valores que não vão mudar. Um JOIN a mais
em toda consulta para uma lista fixa e binária não se paga.

## Nota

Se o conjunto de valores crescer e passar a ter atributos próprios (rótulo,
ordem, ativo/inativo), a tabela de referência volta à mesa. O gatilho é
"o valor precisa carregar informação além de si mesmo".
