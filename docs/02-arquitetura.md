# 02 — Arquitetura

## Visão em camadas

O backend é uma aplicação FastAPI organizada em camadas, cada uma com uma
responsabilidade única e uma direção de dependência bem definida.

```
        HTTP (cliente: Next.js, Swagger, curl…)
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Routers            app/routers/             │
│  Traduz HTTP <-> domínio. Não sabe SQL.      │
└──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Schemas            app/schemas/             │
│  Contrato da API. Valida entrada e formata   │
│  saída. Pydantic.                            │
└──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Repositories       app/repositories/        │
│  Único lugar que sabe consultar/gravar.      │
└──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Models             app/models/              │
│  Mapeamento objeto-relacional. SQLAlchemy.   │
└──────────────────────────────────────────────┘
                       │
                       ▼
                  PostgreSQL
```

Transversal a tudo: **`app/errors.py`**, que traduz erros do banco para
respostas HTTP, e **`app/database.py`**, que constrói a conexão.

### Regra de dependência

**As dependências apontam para dentro.** Um router conhece o repositório;
o repositório não conhece o router. O model não sabe que existe HTTP.

Isso importa porque significa que a lógica de negócio pode ser testada,
reutilizada por um script de agendamento (o envio de boletos vai precisar
disso) ou exposta por outro protocolo, sem arrastar o FastAPI junto.

## O que ainda não existe: a camada de serviço

Hoje o router fala direto com o repositório, porque o CRUD de clientes
**não tem regra de negócio** — criar um cliente é literalmente inserir uma
linha. Adicionar uma camada de serviço que só repassa chamadas seria
cerimônia vazia.

Isso **vai mudar** no módulo de cobrança. "Emitir um boleto" envolve
buscar o cliente, chamar a API do Inter, persistir o resultado e agendar o
envio — orquestração real, com mais de um passo e mais de uma dependência.
Aí nasce `app/services/`, e o router volta a ser o que deve ser: uma
casca fina.

**Princípio adotado:** introduzir a camada quando ela ganhar o seu
sustento, não antes.

## Fluxo de uma requisição

Exemplo real: `POST /clients` com um CPF que já existe no banco.

```
1. FastAPI recebe o JSON
        │
2. Pydantic valida contra ClientCreate
        │  ├─ JSON malformado ou campo faltando  → 422 (automático)
        │  └─ Pessoa física sem CPF              → 422 (model_validator)
        ▼
3. Router monta o objeto Client e chama ClientRepository.create()
        │  A sessão de banco veio via Depends(get_db)
        ▼
4. Repository faz add + commit
        ▼
5. Postgres rejeita: uq_clients_cpf violada
        │  psycopg2 levanta erro → SQLAlchemy encapsula em IntegrityError
        ▼
6. integrity_error_handler intercepta
        │  Lê o SQLSTATE (23505) e o nome da constraint
        ▼
7. Resposta: 409 Conflict
   { "detail": "Já existe um cliente cadastrado com este CPF.",
     "constraint": "uq_clients_cpf" }
```

Repare que **nenhuma camada precisou saber sobre as outras** para isso
funcionar. O router não tem `try/except`; o repositório não conhece
códigos HTTP. Ver [ADR 0009](decisoes/0009-integridade-garantida-pelo-banco.md).

## Patterns aplicados

### Repository Pattern

`ClientRepository` concentra todo o acesso a dados de cliente. Nenhuma
outra parte do sistema escreve query.

O repositório **recebe** a sessão pelo construtor, não a cria:

```python
class ClientRepository:
    def __init__(self, db: Session):
        self.db = db
```

Isso é deliberado. Quem controla o ciclo de vida da conexão é quem controla
a requisição — o FastAPI, via `Depends(get_db)`. Se o repositório abrisse a
própria conexão, cada operação viveria numa transação separada e seria
impossível fazer duas escritas atomicamente. Detalhes em
[ADR 0004](decisoes/0004-repository-pattern.md).

### Dependency Injection

`get_db()` é um *generator dependency*: o FastAPI executa até o `yield`,
entrega a sessão para a rota e, quando a resposta termina — **mesmo se a
rota levantar exceção** — roda o `finally` e fecha a conexão.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Sem isso, uma exceção no meio de uma rota vazaria a conexão. Depois de
algumas centenas de erros, o pool esgota e a aplicação para de responder —
um bug que só aparece em produção, sob carga.

### Dependency Inversion (planejado)

O módulo de cobrança vai definir uma interface abstrata `BillingGateway`,
com duas implementações: uma real (Banco Inter) e um *fake* em memória para
desenvolvimento. A regra de negócio vai depender da interface, nunca do
Inter. Ver [ADR 0012](decisoes/0012-gateway-de-cobranca-abstrato.md).

## Estrutura de pastas

```
crm-andrade-backend/
├── alembic/                    Migrations versionadas
│   ├── versions/               Uma migration por arquivo, encadeadas
│   └── env.py                  Configuração (lê DATABASE_URL do .env)
├── app/
│   ├── main.py                 Cria o app, registra routers e handlers
│   ├── database.py             Engine, SessionLocal, Base
│   ├── errors.py               Traduz erros do banco para HTTP
│   ├── models/                 SQLAlchemy — o que existe no banco
│   ├── schemas/                Pydantic — o contrato da API
│   ├── repositories/           Acesso a dados
│   └── routers/                Endpoints HTTP
├── docs/                       Esta documentação
├── requirements.txt            Dependências de produção
├── requirements-dev.txt        + dependências de teste
└── .env                        Segredos — NÃO versionado
```

### Por que `models/` e `schemas/` são separados

São coisas diferentes, e confundi-las é um erro comum:

- **Model** (`Client`) = a **tabela**. Tem `id`, `created_at`, e um dia terá
  colunas internas que ninguém de fora deveria ver.
- **Schema** (`ClientCreate`, `ClientResponse`) = o **contrato público**.
  Define o que se pode enviar e o que se recebe de volta.

Se fossem a mesma classe, qualquer coluna nova no banco vazaria
automaticamente na API. `ClientUpdate` é a prova de que a separação vale:
ele **omite de propósito** `person_type`, `cpf` e `cnpj`, tornando
impossível trocar o documento de um cliente por um PATCH distraído — mesmo
que as colunas existam e sejam editáveis no banco.

## Decisões que moldaram esta arquitetura

- [ADR 0001 — Backend em Python/FastAPI](decisoes/0001-backend-em-python-fastapi.md)
- [ADR 0004 — Repository Pattern](decisoes/0004-repository-pattern.md)
- [ADR 0008 — Validação em duas camadas](decisoes/0008-validacao-em-duas-camadas.md)
- [ADR 0009 — Integridade garantida pelo banco](decisoes/0009-integridade-garantida-pelo-banco.md)
