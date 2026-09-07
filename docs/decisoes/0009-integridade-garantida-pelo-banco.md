# ADR 0009 — Integridade garantida pelo banco, traduzida para HTTP

**Status:** Aceito
**Data:** 2026-09-05

## Contexto

Era possível cadastrar o mesmo cliente duas vezes — nada impedia dois
registros com o mesmo CPF.

Ao adicionar a constraint UNIQUE, apareceu um segundo problema: a violação
subia como `sqlalchemy.exc.IntegrityError` até o topo e o FastAPI respondia
**500 Internal Server Error**.

Isso é uma mentira para quem consome a API. `5xx` significa "o servidor
falhou"; aqui o servidor funcionou perfeitamente e **recusou um pedido
inválido** — o que é `4xx`. A diferença é prática: um cliente HTTP bem
escrito tenta de novo em caso de `5xx`, e reenviar um cadastro duplicado
infinitas vezes não ajuda ninguém. Além disso, `5xx` polui monitoramento
com alarmes falsos.

## Decisão

Duas partes:

**1. O banco é a fonte de verdade sobre integridade.** Constraints UNIQUE em
`cpf` e `cnpj` (migration `c93a5f17b204`).

**2. Um handler central traduz violações para HTTP.** Registrado uma vez em
`app/main.py`, cobre toda a aplicação:

```python
app.add_exception_handler(IntegrityError, integrity_error_handler)
```

O handler lê o **SQLSTATE** e o **nome da constraint** do erro do driver, e
mapeia para status e mensagem:

| SQLSTATE | Significado | HTTP |
|---|---|---|
| `23505` | UNIQUE | `409 Conflict` |
| `23514` | CHECK | `422 Unprocessable Entity` |
| `23502` | NOT NULL | `422` |
| `23503` | FOREIGN KEY | `409` |

## Justificativa

### Por que a constraint, e não uma checagem antes do INSERT

A alternativa seria consultar antes ("existe alguém com este CPF?") e
recusar sem tentar gravar. Foi descartada por duas razões:

**1. Race condition (TOCTOU).** Entre a consulta e o INSERT, outra
requisição pode inserir o mesmo CPF. As duas passam na verificação, as duas
gravam. A checagem prévia dá **ilusão** de segurança — só a constraint
realmente garante, porque o banco a avalia no momento da escrita, sob
bloqueio.

**2. Duplicação de regra.** A regra passaria a viver na aplicação e no
banco, livres para divergir.

Conclusão: **tenta gravar e deixa o banco recusar.** É a única forma correta
sob concorrência — aqui não é questão de estilo, é de correção.

### Por que mapear pelo nome da constraint

O handler indexa mensagens por **nome de constraint**, não pelo texto do
erro do Postgres:

```python
CONSTRAINT_MESSAGES = {
    "uq_clients_cpf": "Já existe um cliente cadastrado com este CPF.",
    ...
}
```

O texto do erro do Postgres muda conforme o idioma configurado no servidor —
e este projeto já foi mordido exatamente por isso (o `UnicodeDecodeError` do
psycopg2 documentado em [05 — Ambiente](../05-ambiente-de-desenvolvimento.md)
era uma mensagem de erro em português). **O nome da constraint não muda.**

### Por que centralizado

Um handler no topo, e não `try/except` em cada rota:

- Nenhuma rota precisa saber que erros de banco existem
- Uma tabela nova nasce coberta automaticamente
- Cobrir uma constraint nova é acrescentar uma linha no dicionário —
  **nenhuma rota muda**. É o Open-Closed Principle aplicado a erros

## Consequências

**Positivas**

- Impossível duplicar cliente, mesmo sob requisições concorrentes
- Status HTTP semanticamente corretos
- Mensagens em português, úteis para o front-end
- O campo `constraint` na resposta dá ao front um identificador **estável**
  para destacar o campo certo no formulário, sem comparar strings de mensagem
- Comportamento uniforme em toda a API

**Negativas**

- **Depende de detalhes do driver.** `error.orig.pgcode` e
  `error.orig.diag.constraint_name` são específicos do psycopg2. Trocar de
  driver quebra o handler — por isso o acesso é defensivo (`getattr` com
  fallback): falhar ao *tratar* um erro seria pior que o erro original
- **Depende de nomes de constraint explícitos.** Se alguém criar uma
  constraint sem nomear, o Postgres inventa um nome e ela cai na mensagem
  genérica. Daí a convenção obrigatória de nomes em
  [07 — Convenções](../07-convencoes.md)
- O dicionário de mensagens precisa ser mantido junto com as migrations

## Complemento obrigatório

A constraint UNIQUE sozinha era mais fraca do que parecia: `"111.222.333-44"`
e `"11122233344"` são strings distintas para o banco, então bastava mudar a
pontuação para burlá-la. A normalização de documentos na entrada
([ADR 0014](0014-normalizacao-de-documentos.md)) é o que torna esta decisão
efetiva de verdade.

## Verificação

Testado ponta a ponta:

| Cenário | Resultado |
|---|---|
| Criar cliente PF | `201` |
| Criar outro com o mesmo CPF | `409` + mensagem sobre CPF |
| Criar cliente PJ | `201` |
| Criar outro com o mesmo CNPJ | `409` + mensagem sobre CNPJ |
| Criar duas PJ diferentes (ambas com `cpf = NULL`) | `201` nas duas |
| Violar CHECK direto no model | SQLSTATE `23514` + nome correto extraído |

O quinto caso confirma o ponto sutil: **UNIQUE permite múltiplos NULL** no
Postgres, então uma constraint só resolve tanto "não duplicar CPF" quanto
"pessoas jurídicas não colidem entre si por não terem CPF".
