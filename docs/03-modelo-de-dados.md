# 03 — Modelo de dados

## Estado atual

Uma única tabela: `clients`. As entidades de cobrança e de lead ainda não
foram modeladas.

```
┌─────────────────────────┐
│        clients          │
├─────────────────────────┤
│ id           UUID   PK  │
│ name         text   NN  │
│ person_type  text   NN  │
│ cpf          text   UQ  │
│ cnpj         text   UQ  │
│ phone        text   NN  │
│ email        text       │
│ created_at   timestamptz NN │
└─────────────────────────┘
          │
          │  (planejado)
          ▼
┌─────────────────────────┐
│       charges           │   Cobranças — módulo Banco Inter
└─────────────────────────┘
```

## Tabela `clients`

Definida em [`app/models/client.py`](../app/models/client.py).

| Coluna | Tipo | Nulo? | Descrição |
|---|---|---|---|
| `id` | `UUID` | não | Chave primária, gerada na aplicação via `uuid4()` |
| `name` | `String` | não | Nome da pessoa ou razão social |
| `person_type` | `String` | não | `'INDIVIDUAL'` ou `'COMPANY'` |
| `cpf` | `String` | sim | Obrigatório se `INDIVIDUAL`, proibido se `COMPANY`. Único. Armazenado sem pontuação (11 dígitos) |
| `cnpj` | `String` | sim | Obrigatório se `COMPANY`, proibido se `INDIVIDUAL`. Único. Armazenado sem pontuação (14 dígitos) |
| `phone` | `String` | não | Destino do boleto no WhatsApp |
| `email` | `String` | sim | Contato secundário |
| `created_at` | `DateTime(timezone=True)` | não | `server_default = now()` |

### Constraints

| Nome | Tipo | Regra |
|---|---|---|
| `uq_clients_cpf` | UNIQUE | Não permite dois clientes com o mesmo CPF |
| `uq_clients_cnpj` | UNIQUE | Não permite dois clientes com o mesmo CNPJ |
| `check_person_type_valid` | CHECK | `person_type IN ('INDIVIDUAL', 'COMPANY')` |
| `check_document_by_person_type` | CHECK | Pessoa física tem CPF e não tem CNPJ; jurídica, o inverso |

## Decisões de modelagem

### `id` é UUID, não inteiro sequencial

Um `id` sequencial exposto na URL entrega duas informações de graça:
quantos clientes existem, e a possibilidade de enumerar todos trocando o
número (`/clients/1`, `/clients/2`, …). Com dados pessoais e LGPD no meio,
isso é risco desnecessário. Detalhes em [ADR 0005](decisoes/0005-uuid-como-chave-primaria.md).

O UUID é gerado **na aplicação** (`default=uuid.uuid4`), não no banco.
Vantagem prática: o objeto já tem `id` antes do `INSERT`, o que simplifica
montar relacionamentos em memória.

### `person_type` é string com CHECK, não ENUM

Postgres tem tipo `ENUM` nativo, e o SQLAlchemy suporta. Não foi usado:
alterar um `ENUM` no Postgres exige `ALTER TYPE`, que tem restrições
chatas em transação; uma CHECK constraint se altera com um simples
`DROP` + `CREATE`. Ver [ADR 0006](decisoes/0006-sem-enum-para-person-type.md).

### `cpf` e `cnpj` são colunas separadas

A alternativa seria uma coluna única `document` + `document_type`. Duas
colunas foram preferidas porque:

- CPF e CNPJ têm formatos, tamanhos e algoritmos de validação diferentes
- A CHECK constraint cruzada fica legível e o banco consegue garantir a regra
- As queries futuras ("busque pelo CNPJ") ficam diretas

O custo é uma coluna sempre nula em cada linha — irrelevante nesta escala.

### UNIQUE com NULL: por que funciona

No SQL padrão (e no Postgres), `NULL` nunca é igual a `NULL`. Uma constraint
UNIQUE por isso **permite quantos NULL quiser**.

Isso é exatamente o comportamento desejado aqui: toda pessoa jurídica tem
`cpf IS NULL`, e nenhuma delas colide com as outras — mas duas pessoas
físicas com o mesmo CPF são rejeitadas. Uma única constraint resolve os
dois casos, sem precisar de índice parcial.

> Verificado em teste: dois clientes `COMPANY` (ambos com `cpf = NULL`)
> são aceitos; dois com o mesmo CNPJ, não.

### `created_at` tem `server_default`

Originalmente o default era só em Python (`default=lambda: datetime.now(...)`).
O problema: quem inserisse uma linha por SQL direto — um script de carga,
uma correção manual no DBeaver — criaria uma linha com `created_at` nulo.

Com `server_default=func.now()` e `NOT NULL`, o **Postgres** garante o
valor. A regra passa a valer para todo mundo, não só para quem entra pela
aplicação. É o mesmo princípio de [ADR 0009](decisoes/0009-integridade-garantida-pelo-banco.md).

O tipo é `timestamptz` (timezone-aware) e não `timestamp`. Cobrança tem
vencimento, e vencimento sem fuso horário é uma bomba-relógio — ainda mais
quando o servidor de produção quase certamente roda em UTC enquanto o
escritório opera em horário de Brasília.

## Débitos conhecidos

- **Não há validação de dígito verificador de CPF/CNPJ.** O tamanho é
  conferido, mas não o cálculo do DV — `"11111111111"` tem 11 dígitos e é
  aceito, embora seja um CPF matematicamente inválido.
- ~~**Não há normalização de formato.**~~ Resolvido: `cpf` e `cnpj` são
  reduzidos a apenas dígitos no schema Pydantic, e o tamanho é validado
  (11 e 14 dígitos). A migration `d24e8b91fa07` normalizou as linhas
  existentes. Ver [ADR 0014](decisoes/0014-normalizacao-de-documentos.md).
- **`phone` sem formato definido.** A integração com WhatsApp vai exigir o
  formato E.164 (`5511999999999`). Ainda não é imposto.
- **Sem `updated_at`.** Não há como saber quando um cliente foi alterado.

## Modelagem planejada: `charges`

Esboço, ainda não implementado:

| Coluna | Observação |
|---|---|
| `id` | UUID |
| `client_id` | FK para `clients` |
| `amount` | `Numeric(10,2)` — **nunca `Float`**, dinheiro não admite erro de arredondamento binário |
| `due_date` | Data de vencimento |
| `status` | `PENDING` / `SENT` / `PAID` / `OVERDUE` / `CANCELLED` |
| `external_id` | Identificador do boleto no Banco Inter |
| `created_at` / `updated_at` | |

A questão em aberto é como representar **recorrência**: uma tabela
`subscriptions` que gera `charges` mensalmente, ou cobranças que se
auto-replicam. A primeira opção separa melhor "o contrato" de "a fatura",
mas ainda não foi decidida.
