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

## Tabela `charges`

Definida em [`app/models/charge.py`](../app/models/charge.py). Criada pela
migration `33f1693378a4`.

| Coluna | Tipo | Nulo? | Descrição |
|---|---|---|---|
| `id` | `UUID` | não | Chave primária |
| `client_id` | `UUID` | não | FK para `clients`, com `ON DELETE RESTRICT` |
| `amount` | `Numeric(10,2)` | não | Valor. **Nunca `Float`** |
| `due_date` | `Date` | não | Vencimento |
| `description` | `String` | sim | Ex: "Honorários — setembro" |
| `status` | `String` | não | Ciclo de vida do **pagamento**, só isso |
| `external_id` | `String` | sim | Id do boleto no banco. Único. NULL = ainda não emitido |
| `payment_url` | `String` | sim | Link do boleto |
| `digitable_line` | `String` | sim | Linha digitável |
| `pix_copy_paste` | `String` | sim | Pix copia-e-cola |
| `issued_at` | `timestamptz` | sim | Quando o boleto foi emitido no banco |
| `notified_at` | `timestamptz` | sim | Quando foi enviado ao cliente |
| `paid_at` | `timestamptz` | sim | Quando o pagamento foi confirmado |
| `created_at` / `updated_at` | `timestamptz` | não | `server_default = now()` |

### Estados de `status`

```
PENDING ──→ PAID
        ──→ OVERDUE
        ──→ CANCELLED
```

`status` cobre **apenas o pagamento**. Emissão e notificação são fatos
independentes, registrados em `issued_at` e `notified_at` — porque uma
cobrança emitida, enviada **e** paga é o caso normal, e uma coluna só não
comportaria os três. Ver [ADR 0015](decisoes/0015-status-de-cobranca-separado-de-fatos.md).

### Constraints e índices

| Nome | Tipo | Regra |
|---|---|---|
| `fk_charges_client_id` | FK | `ON DELETE RESTRICT` — impede apagar cliente com cobranças |
| `uq_charges_external_id` | UNIQUE | Um boleto do banco não se repete |
| `check_charge_status_valid` | CHECK | `status` entre os valores conhecidos |
| `check_charge_amount_positive` | CHECK | `amount > 0` |
| `check_charge_paid_at_matches_status` | CHECK | `PAID` ⟺ tem `paid_at` |
| `check_charge_issued_consistency` | CHECK | `external_id` ⟺ `issued_at` |
| `ix_charges_client_id` | Índice | O Postgres **não** indexa FK automaticamente |
| `ix_charges_status_due_date` | Índice | Atende a consulta da rotina diária |

### Decisões de modelagem

**`Numeric(10,2)`, nunca `Float`.** `Float` é binário e não representa
decimais exatamente — `0.1 + 0.2 != 0.3`. Em dinheiro esse erro acumula e
vira divergência de centavos no fechamento do mês.

**`ON DELETE RESTRICT` na FK.** Apagar um cliente com histórico financeiro
seria perda de dado contábil. O banco recusa, e o handler de erros traduz
a recusa em `409` com mensagem útil. Isso transformou o débito do "DELETE
físico" em um erro seguro, sem precisar de soft delete ainda.

> ⚠️ Isso exigiu `passive_deletes="all"` no relationship do lado do
> `Client`. Sem isso, o SQLAlchemy tenta "ajudar" emitindo
> `UPDATE charges SET client_id = NULL` antes do DELETE, e o erro que sobe
> é um `NotNullViolation` confuso em vez da recusa correta da FK.

**Valor mínimo mora no schema, não no banco.** A CHECK garante só
`amount > 0`. O mínimo de R$ 2,50 é regra da **instituição financeira**, não
do domínio — vive em `app/schemas/charge.py`. Trocar de banco muda esse
número e não deve exigir migration.

## Modelagem ainda em aberto: recorrência

O escritório cobra **mensalmente**. Como representar isso ainda não foi
decidido. As opções na mesa:

- Uma tabela `subscriptions` (o contrato) que gera `charges` (as faturas)
  mensalmente. Separa bem "o acordo" de "a cobrança do mês"
- Cobranças que se auto-replicam ao serem pagas

A primeira parece mais correta — permite mudar o valor do contrato sem
reescrever o histórico, e responde "quanto este cliente paga por mês?" sem
inferir das faturas. Mas não foi decidido.
