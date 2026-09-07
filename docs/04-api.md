# 04 — Referência da API

Base URL em desenvolvimento: `http://127.0.0.1:8000`

Documentação interativa gerada automaticamente pelo FastAPI:

- **Swagger UI** — <http://127.0.0.1:8000/docs>
- **ReDoc** — <http://127.0.0.1:8000/redoc>
- **OpenAPI JSON** — <http://127.0.0.1:8000/openapi.json>

> ⚠️ **Não há autenticação ainda.** Todos os endpoints são públicos. Isso é
> aceitável enquanto o sistema roda apenas em `localhost`, e é
> **bloqueante para qualquer deploy**. Ver [Pendências](#pendências).

---

## `GET /`

Health check. Útil para o serviço de hospedagem saber se a aplicação subiu.

```json
{ "status": "ok", "projeto": "CRM Andrade" }
```

---

## Clientes

### `POST /clients/` — cria um cliente

**Corpo:**

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `name` | string | sim | |
| `person_type` | `"INDIVIDUAL"` \| `"COMPANY"` | sim | |
| `cpf` | string | condicional | Obrigatório se `INDIVIDUAL`; proibido se `COMPANY`. Pontuação é aceita e removida; deve resultar em 11 dígitos |
| `cnpj` | string | condicional | Obrigatório se `COMPANY`; proibido se `INDIVIDUAL`. Pontuação é aceita e removida; deve resultar em 14 dígitos |
| `phone` | string | sim | |
| `email` | string | não | |

**Exemplo:**

```bash
curl -X POST http://127.0.0.1:8000/clients/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Maria Silva",
    "person_type": "INDIVIDUAL",
    "cpf": "11122233344",
    "phone": "5511999999999",
    "email": "maria@exemplo.com"
  }'
```

**`201 Created`:**

```json
{
  "name": "Maria Silva",
  "person_type": "INDIVIDUAL",
  "cpf": "11122233344",
  "cnpj": null,
  "phone": "5511999999999",
  "email": "maria@exemplo.com",
  "id": "0fffef6a-5636-483d-851e-bcfc0c760add",
  "created_at": "2026-09-05T15:38:21.510335-03:00"
}
```

**Erros:**

| Status | Quando |
|---|---|
| `422` | Campo faltando, tipo errado, regra CPF/CNPJ violada, ou documento com quantidade errada de dígitos |
| `409` | CPF ou CNPJ já cadastrado |

> **Documentos são normalizados na entrada.** `"111.222.333-44"` e
> `"11122233344"` são o mesmo valor: a pontuação é removida antes de gravar,
> e a resposta sempre traz apenas dígitos. Isso é o que torna a constraint
> UNIQUE efetiva — sem normalizar, bastaria mudar a pontuação para cadastrar
> o mesmo CPF duas vezes. Ver [ADR 0014](decisoes/0014-normalizacao-de-documentos.md).

### `GET /clients/` — lista todos

Retorna um array de clientes.

> **Sem paginação.** Retorna a tabela inteira. Aceitável para a escala do
> escritório (dezenas de clientes), mas é dívida técnica assumida.

### `GET /clients/{client_id}` — busca por id

`404` se não existir. `422` se o id não for um UUID válido.

### `PATCH /clients/{client_id}` — atualiza

Aceita **apenas** `name`, `phone` e `email`. Todos opcionais; só os campos
enviados são alterados (`exclude_unset=True`).

`person_type`, `cpf` e `cnpj` **não são aceitos aqui, de propósito**.
Trocar o documento de um cliente não é "editar um campo" — é dizer que o
cadastro é de outra pessoa. Isso merece uma rota própria, com regra e
registro próprios, quando houver necessidade real. Ver
[02 — Arquitetura](02-arquitetura.md#por-que-models-e-schemas-são-separados).

```bash
curl -X PATCH http://127.0.0.1:8000/clients/{id} \
  -H "Content-Type: application/json" \
  -d '{"phone": "5511977777777"}'
```

### `DELETE /clients/{client_id}` — remove

`204 No Content` em caso de sucesso, `404` se não existir.

> **É um delete físico.** A linha some do banco. Quando existirem cobranças
> vinculadas, isso vira problema: apagar um cliente com histórico
> financeiro é perda de dado contábil. A solução provável é *soft delete*
> (coluna `deleted_at`), a ser decidida junto com o módulo de cobrança.

---

## Formato dos erros

### Erros de validação (Pydantic) — `422`

Formato padrão do FastAPI, com o caminho exato do campo problemático:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, CPF é obrigatório para pessoa física"
    }
  ]
}
```

### Erros de integridade (banco) — `409` / `422`

Formato próprio, definido em [`app/errors.py`](../app/errors.py):

```json
{
  "detail": "Já existe um cliente cadastrado com este CPF.",
  "constraint": "uq_clients_cpf"
}
```

O campo `constraint` é intencional: dá ao front-end um identificador
**estável** para tratar o erro programaticamente (destacar o campo certo
no formulário, por exemplo), sem depender de comparar strings de mensagem
— que podem ser reescritas a qualquer momento.

### Mapeamento de códigos

| SQLSTATE | Significado | HTTP |
|---|---|---|
| `23505` | Violação de UNIQUE | `409 Conflict` |
| `23514` | Violação de CHECK | `422 Unprocessable Entity` |
| `23502` | Violação de NOT NULL | `422 Unprocessable Entity` |
| `23503` | Violação de FOREIGN KEY | `409 Conflict` |

A escolha entre 409 e 422 segue a semântica: **409** quando o pedido é
válido mas conflita com o estado atual do sistema (o CPF é legítimo, só já
está em uso); **422** quando o pedido em si viola uma regra.

---

## Pendências

Antes de qualquer deploy público:

1. **Autenticação e autorização.** Hoje qualquer um lista todos os clientes
   do escritório, com CPF e telefone. Inaceitável fora de `localhost`.
2. **CORS.** Ainda não configurado — o front-end em outro domínio será
   bloqueado pelo navegador.
3. **Rate limiting.**
4. **Paginação** em `GET /clients/`.
5. **Validação de dígito verificador** de CPF/CNPJ — hoje o tamanho é
   conferido, mas não o cálculo.
