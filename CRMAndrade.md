# CRM Andrade — Histórico do Projeto

> 📚 **A documentação técnica do projeto vive em [`docs/`](docs/).**
> Este arquivo é o **diário** — narra o que aconteceu, em ordem cronológica,
> incluindo troubleshooting e caminhos que não deram certo.
> A `docs/` descreve o sistema **como ele é hoje**, e o registro de decisões
> (com justificativa e alternativas descartadas) está em
> [`docs/decisoes/`](docs/decisoes/).

## 1. Contexto e Origem

O CRM Andrade nasceu de uma demanda de um escritório de advocacia, repassada por um primo do desenvolvedor. Inicialmente, a necessidade era apenas automatizar cobranças (que hoje são feitas manualmente pelo app do Banco Inter) e evoluiu para incluir um CRM de atendimento inicial de leads vindos de anúncios.

Uma tentativa anterior de desenvolvimento havia falhado — o desenvolvedor responsável tentou integrar uma IA generativa livre para responder os leads automaticamente, mas o resultado não funcionou bem, ficou inseguro de disponibilizar, e o escritório continuou pagando por hospedagem (Hostinger) sem uso efetivo do produto.

Vitor, o desenvolvedor atual, está em formação em **Engenharia de Software** e assumiu o projeto como *side project*, dedicando poucas horas por semana, com a ideia de eventualmente substituir o desenvolvedor anterior caso ele desista.

---

## 2. Escopo do Projeto

- Sistema próprio de cobrança recorrente integrado ao Banco Inter
- Envio automático do boleto ao cliente via WhatsApp, 5 dias antes do vencimento
- CRM simples para primeiro atendimento de leads vindos de anúncios
- Substituição da IA generativa livre por um **fluxo estruturado** (sem os riscos do modelo anterior)
- Migração para hospedagem gratuita, eliminando o custo atual do servidor

**Fora do escopo (por ora):** atendimento jurídico automatizado por IA, negociação de dívidas automatizada, funcionalidades de ERP completo.

---

## 3. Decisões Técnicas

### 3.1 Stack escolhida
| Camada | Tecnologia | Motivo |
|---|---|---|
| Front-end | Next.js + TypeScript | Vitor já domina, produtividade alta |
| Back-end | Python + FastAPI | Desafio saudável, ótimo para integrações externas (Inter, WhatsApp), tipagem forte com Pydantic |
| Banco de dados | PostgreSQL | Dado é fortemente relacional (cliente → cobranças → leads) |
| Hospedagem do banco | Supabase (produção) / Postgres local (desenvolvimento) | Free tier, já resolve autenticação/storage se necessário |
| Hospedagem do back-end | Railway / Render (a definir) | Free tier, roda Python com scheduler |
| Versionamento | GitHub | Gratuito, já é o que Vitor usa |
| Migrations | Alembic | Versiona mudanças de schema junto com o código |

### 3.2 Fluxo de trabalho Git
Estrutura de branches: **develop / homolog / main**

### 3.3 Convenção de nomenclatura
**Todo nome de código (arquivos, classes, funções, variáveis, tabelas, colunas) é em inglês.** A dívida inicial em português (`Cliente`, `clientes`, `ClienteCreate`, etc.) foi quitada na migration `b7c1d4e28f30` — ver seção 7.7. Mensagens voltadas ao usuário final (erros de validação, textos de UI) seguem em português.

### 3.4 Boas práticas acordadas
- Aplicação de princípios **SOLID**, com destaque para o **Open-Closed Principle**
- Uso consciente de **Design Patterns**, sempre explicados no momento em que são aplicados (ex: Repository Pattern)
- Separação clara de camadas: rotas (API) → regras de negócio → integrações externas → persistência

---

## 4. Descrição Oficial do Projeto

> O CRM Andrade é um sistema desenvolvido para automatizar a gestão de cobranças e o atendimento inicial de leads de um escritório de advocacia. O projeto nasceu da necessidade de eliminar processos manuais recorrentes — como a geração de boletos diretamente pelo aplicativo do banco — substituindo-os por um fluxo integrado que conecta a API do Banco Inter, o WhatsApp Business e um painel de acompanhamento centralizado.
>
> Além da automação de cobranças recorrentes, o sistema conta com um módulo de CRM responsável por realizar o primeiro atendimento de leads oriundos de anúncios, qualificando o contato através de um fluxo estruturado antes do encaminhamento para a equipe do escritório.
>
> O projeto é desenvolvido por Vitor, atualmente em formação em Engenharia de Software, como forma de aplicar na prática conceitos técnicos aprendidos ao longo da graduação. A arquitetura e a implementação seguem boas práticas de desenvolvimento de software, com foco na aplicação de princípios SOLID (especialmente Open-Closed), Design Patterns reconhecidos pela comunidade, e separação clara de responsabilidades entre camadas.

---

## 5. Análise de Viabilidade (Integrações Externas)

### 5.1 API Banco Inter (Cobrança)
- Requer conta PJ ativa + geração de credenciais (Client ID/Secret) e certificado (KEY/CRT) via Internet Banking
- Permite cobrança simples, parcelada ou recorrente, com juros/multa/desconto
- Valor mínimo de cobrança: R$ 2,50
- **100 boletos gratuitos por mês**; excedentes custam R$ 0,99 (Pix) ou R$ 2,49 (linha digitável)

### 5.2 WhatsApp (envio de boleto)
- Conversas de atendimento (iniciadas pelo cliente, respondidas em até 24h) são **gratuitas e ilimitadas**
- Envio proativo do boleto (iniciado pela empresa) exige **template aprovado pela Meta**, categoria "Utilidade" — custo baixo (~R$ 0,035/mensagem), mas não é gratuito
- Requer conta comercial verificada na Meta e número dedicado (separado do WhatsApp já usado no escritório)
- **Não recomendado**: bibliotecas não-oficiais (Baileys, whatsapp-web.js) — risco de banimento do número e problemas de conformidade com LGPD

### 5.3 Módulo de IA / CRM
- Decisão consciente de **não usar LLM generativa livre** para responder leads (fonte do fracasso do projeto anterior)
- Substituído por **fluxo estruturado** (árvore de decisão / perguntas fixas por área de interesse)
- Uso de IA, se houver, restrito à **classificação de intenção** (ex: identificar área jurídica), nunca geração de texto livre para o cliente

---

## 6. Plano de Implementação (Visão Geral)

1. Módulo de cobrança (Inter) — cadastro de cliente + emissão de boleto
2. Agendamento e envio automático via WhatsApp
3. Painel de acompanhamento de status de pagamento
4. Recepção de leads (webhook) + fluxo estruturado de qualificação
5. Painel de CRM para a equipe
6. Ajustes finos de segurança, logs e monitoramento

---

## 7. Execução — O Que Já Foi Feito

### 7.1 Setup do ambiente
- Instalado Python **3.14** (após troubleshooting: Python 3.9 causava erro de build do `greenlet` por falta do Visual C++ Build Tools)
- Criado ambiente virtual (`venv`) e instaladas dependências: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg2-binary`, `python-dotenv`, `alembic`
- Repositório criado no GitHub: **CRM-andrade**, pasta do backend: `crm-andrade-backend`
- Branch de trabalho: `develop`

### 7.2 Banco de dados
- Postgres local configurado (usado via DBeaver)
- Resolvido erro de `UnicodeDecodeError` no psycopg2 (causa raiz: banco `crm_andrade` não existia — os erros de decodificação eram só sintoma de mensagens de erro do Postgres em português)
- Banco `crm_andrade` criado
- Configurado `app/database.py` (engine, SessionLocal, Base) lendo `DATABASE_URL` do `.env`

### 7.3 Alembic
- Inicializado (`alembic init alembic`)
- `env.py` ajustado para importar `Base` e os models, e para puxar a `DATABASE_URL` do `.env`
- Primeira migration gerada e aplicada: criação da tabela `clientes`

### 7.4 Modelo de dados — Client
Tabela `clients`:

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | UUID | Chave primária, gerada via `uuid.uuid4()` (evita IDs sequenciais adivinháveis) |
| `name` | String | Obrigatório |
| `person_type` | String | `"INDIVIDUAL"` ou `"COMPANY"` (sem uso de Enum, por decisão do Vitor) |
| `cpf` | String | Opcional, obrigatório se `person_type = INDIVIDUAL`. Mantido em português por ser nome próprio do domínio brasileiro |
| `cnpj` | String | Opcional, obrigatório se `person_type = COMPANY`. Idem `cpf` |
| `phone` | String | Obrigatório (uso futuro: integração WhatsApp) |
| `email` | String | Opcional |
| `created_at` | DateTime (timezone-aware) | `NOT NULL` com `server_default = now()` — garantido pelo Postgres, não só pelo SQLAlchemy |

Duas `CheckConstraint` no banco:
- `check_person_type_valid`: `person_type IN ('INDIVIDUAL', 'COMPANY')`
- `check_document_by_person_type`: regra cruzada de CPF/CNPJ conforme `person_type`

### 7.5 Camada de API — Módulo de Cliente
- **Schemas Pydantic** (`app/schemas/client.py`): `ClientCreate`, `ClientUpdate` (sem `person_type`/`cpf`/`cnpj` de propósito — mudança de documento merece rota própria futuramente), `ClientResponse`. Validação de CPF/CNPJ replicada na camada de API via `model_validator`.
- **Repository Pattern** (`app/repositories/client_repository.py`): classe `ClientRepository`, recebe uma `Session` via `__init__` (não cria conexão própria — isso é responsabilidade da camada de rota). Métodos: `create`, `get_by_id`, `list_all`, `update`, `delete`.
- **Router** (`app/routers/client.py`): rotas REST completas em `/clients` (POST, GET lista, GET por id, PATCH, DELETE). Usa **Dependency Injection** do FastAPI (`Depends(get_db)`) para fornecer a sessão de banco de forma segura (fecha a conexão sempre, via `try/finally`).
- Router registrado em `app/main.py`.

### 7.6 Conceitos explicados até aqui
- **Repository Pattern**: isola acesso a dados do resto da aplicação; conecta com Open-Closed Principle (trocar ORM/banco sem afetar rotas).
- **Dependency Injection (`Depends`)**: FastAPI gerencia criação/fechamento de recursos (sessão de banco) de forma automática e seguindocorretamente o ciclo de vida da requisição.

### 7.7 Renomeação para inglês (migration `b7c1d4e28f30`)
Dívida técnica de nomenclatura quitada antes de o projeto crescer — quanto mais código em português fosse escrito, mais caro seria o rename depois.

**Código:** `app/models/cliente.py` → `app/models/client.py` (`Cliente` → `Client`); `app/schemas/cliente.py` → `app/schemas/client.py` (`ClienteCreate`/`ClienteUpdate`/`ClienteResponse` → `ClientCreate`/`ClientUpdate`/`ClientResponse`). Imports atualizados no repository, no router e no `alembic/env.py`. Adicionado `app/schemas/__init__.py`, que faltava.

**Banco:** tabela `clientes` → `clients`; colunas `nome`→`name`, `tipo_pessoa`→`person_type`, `telefone`→`phone`, `criado_em`→`created_at`. Valores do domínio `'FISICA'`/`'JURIDICA'` → `'INDIVIDUAL'`/`'COMPANY'` (via `UPDATE`, preservando as linhas existentes). Constraints recriadas como `check_person_type_valid` e `check_document_by_person_type`.

**Decisões da migration:**
- Escrita **à mão**, não via `--autogenerate`: o Alembic não reconhece renomeação — ele geraria um `drop_table` + `create_table`, o que apagaria os dados. `ALTER TABLE ... RENAME` preserva tudo.
- **Ordem importa:** as check constraints antigas referenciam as colunas e os valores antigos, então são derrubadas primeiro e recriadas no fim.
- `downgrade()` implementado de verdade (e testado), revertendo schema e dados.
- `cpf` e `cnpj` **não** foram traduzidos: são nomes próprios do domínio brasileiro, sem equivalente em inglês que não perdesse significado.

**Débito quitado junto:** `created_at` agora é `NOT NULL` com `server_default = now()` — o valor passa a ser garantido pelo Postgres, e não apenas pelo default em Python do SQLAlchemy.

**Validação executada:** `alembic upgrade head` → `alembic check` (sem drift entre model e banco) → round-trip `downgrade -1` + `upgrade head` → smoke test do CRUD completo via `TestClient` (POST 201, GET lista, GET por id, PATCH, DELETE 204, GET 404, validação de pessoa física sem CPF retornando 422).

**Também corrigido:** `alembic` estava faltando no `requirements.txt` (junto com suas dependências `Mako` e `MarkupSafe`). Criado `requirements-dev.txt` para dependências só de teste (`httpx2`, exigido pelo `TestClient`).

### 7.8 Integridade de dados e tratamento de erro (2026-09-05)
Dois débitos fechados antes de seguir para o módulo de cobrança.

**Unicidade de CPF/CNPJ** (migration `c93a5f17b204`). Nada impedia cadastrar
o mesmo cliente duas vezes. Adicionadas as constraints `uq_clients_cpf` e
`uq_clients_cnpj`. Detalhe importante: no Postgres, UNIQUE permite múltiplos
NULL — então uma única constraint por coluna resolve tanto "não duplicar CPF"
quanto "pessoas jurídicas (que têm `cpf = NULL`) não colidem entre si".

**Violação de constraint deixou de virar 500.** Antes, um CPF duplicado
subia como `IntegrityError` até o topo e o FastAPI respondia
`500 Internal Server Error` — mentindo, porque o servidor não falhou: o
*pedido* é que era inválido. Criado `app/errors.py`, com um handler
registrado uma única vez em `app/main.py`, que lê o **SQLSTATE** e o **nome
da constraint** do erro do psycopg2 e traduz para o status certo (`409` para
UNIQUE, `422` para CHECK/NOT NULL).

Decisões por trás disso, documentadas em [ADR 0009](docs/decisoes/0009-integridade-garantida-pelo-banco.md):
- **A constraint no banco, e não uma checagem antes do INSERT.** Consultar
  "já existe esse CPF?" antes de gravar tem race condition (TOCTOU): entre a
  consulta e o insert, outra requisição pode inserir o mesmo valor. Só a
  constraint garante de verdade.
- **Mapeamento pelo nome da constraint, não pelo texto do erro.** O texto do
  Postgres muda conforme o idioma do servidor — este projeto já foi mordido
  por isso (o `UnicodeDecodeError` da seção 7.2). O nome da constraint não muda.
- **Handler centralizado, não `try/except` por rota.** Tabela nova nasce
  coberta; cobrir uma constraint nova é uma linha num dicionário, sem tocar
  em rota nenhuma. Open-Closed aplicado a erros.

**Validado:** CPF duplicado → 409 com mensagem sobre CPF; CNPJ duplicado →
409 com mensagem sobre CNPJ; duas PJ diferentes (ambas com `cpf = NULL`) →
201 nas duas; violação de CHECK direto no model → SQLSTATE `23514` e nome da
constraint extraídos corretamente. Round-trip `downgrade`/`upgrade` OK.

### 7.9 Normalização de CPF/CNPJ (migration `d24e8b91fa07`)
A unicidade da seção 7.8 era mais fraca do que parecia: `"111.222.333-44"` e
`"11122233344"` são strings diferentes para o banco, então bastava mudar a
pontuação para cadastrar o mesmo CPF duas vezes.

Documentos passam a ser normalizados no schema Pydantic — toda pontuação é
removida na entrada, e o banco guarda uma forma canônica só (apenas dígitos).
O tamanho é validado depois disso (11 dígitos para CPF, 14 para CNPJ);
antes de normalizar, contar caracteres não significava nada, já que
`"111.222.333-44"` tem 14.

Detalhe que evitou um bug: resultado vazio vira `None`, não `""`. Uma string
vazia seria gravada como `''` e violaria a CHECK constraint do banco, que
exige `cpf IS NULL` para pessoa jurídica. Testado: uma PJ enviada com
`cpf: ""` é aceita e grava NULL.

A migration normaliza também as linhas já existentes. O `downgrade` é `pass`
de propósito — a pontuação original foi descartada e não há como saber qual
formato cada linha usava. Isso é o efeito esperado de uma normalização, não
uma falha.

**Fora do escopo, de propósito:** validação de dígito verificador.
`"11111111111"` tem 11 dígitos e passa, embora seja um CPF matematicamente
inválido. Débito registrado. Ver [ADR 0014](docs/decisoes/0014-normalizacao-de-documentos.md).

### 7.10 Documentação do projeto (2026-09-05)
Criada a pasta [`docs/`](docs/) com a documentação técnica completa: visão
geral, arquitetura, modelo de dados, referência da API, setup de ambiente
(com as pegadinhas de Windows), guia de migrations e convenções.

O registro de decisões ficou em [`docs/decisoes/`](docs/decisoes/), no
formato **ADR** (Architecture Decision Record): um arquivo por decisão, com
contexto, justificativa, **consequências negativas** e alternativas
descartadas. Regra adotada: ADR aceito não se edita — se a decisão mudar,
escreve-se um novo e o antigo vira `Substituído`. O histórico do raciocínio
vale tanto quanto a conclusão.

São 13 ADRs cobrindo tudo que foi decidido até aqui, das escolhas de stack
até a rejeição da IA generativa livre e das bibliotecas não-oficiais de
WhatsApp.

### 7.11 Módulo de cobrança — entidade e gateway (2026-09-05)
Primeira parte do módulo de cobrança: a entidade `Charge` e o contrato do
gateway. A integração real com o Inter fica pendente das credenciais, mas
nada mais depende delas.

**`app/gateways/billing.py`** — a *porta*. Interface abstrata `BillingGateway`
com `issue`, `get_status` e `cancel`, mais os dataclasses `ChargeRequest`,
`Payer` e `IssuedCharge`, e as exceções `BillingGatewayError` /
`ChargeNotFoundError`.

Decisão importante: **o gateway fala em dataclasses, não no model do ORM**.
Se `issue()` recebesse a entidade `Charge` do SQLAlchemy, o adaptador do
Inter ficaria acoplado à nossa persistência. A porta precisa ser
independente das duas pontas que separa.

**`app/gateways/fake_billing.py`** — o adaptador falso, em memória. Reproduz
de propósito recusas do mundo real (cobrança paga não pode ser cancelada,
id inexistente levanta erro) e expõe `fail_next_calls` para exercitar o
caminho de falha sem depender de a rede cair.

**`app/models/charge.py` + migration `33f1693378a4`** — tabela `charges`.
O ponto de modelagem que mais rendeu: **`status` guarda só o ciclo de vida
do pagamento** (`PENDING`/`PAID`/`OVERDUE`/`CANCELLED`). Emissão e
notificação viraram colunas próprias (`issued_at`, `notified_at`), porque
uma cobrança emitida, enviada **e** paga é o caso normal — com uma coluna
só, gravar `PAID` apagaria a informação de que foi enviada. Ver
[ADR 0015](docs/decisoes/0015-status-de-cobranca-separado-de-fatos.md).

**`app/domain.py`** — constantes do domínio em um lugar só, para que a lista
de valores válidos não viva duplicada entre model, schema e comparações.

**Dois problemas reais encontrados pelos testes:**

1. **O SQLAlchemy sabotava o `ON DELETE RESTRICT`.** Ao apagar um cliente com
   cobranças, o ORM "ajudava" emitindo `UPDATE charges SET client_id = NULL`
   antes do DELETE — que batia no NOT NULL e produzia um `NotNullViolation`
   confuso, em vez da recusa correta da FK. Resolvido com
   `passive_deletes="all"` no relationship.
2. **O handler de erros não mapeava RESTRICT.** O Postgres usa SQLSTATE
   `23001` para violação de `ON DELETE RESTRICT`, distinto do `23503` de FK
   comum. Adicionado ao mapa em `app/errors.py`.

Com isso, apagar um cliente que tem cobranças devolve `409` com mensagem
útil — o débito do "DELETE físico" virou um erro seguro, sem precisar de
soft delete ainda.

**Validado:** gateway (emissão, consulta, recusa de cancelar cobrança paga,
id inexistente, falha simulada); schema (valor abaixo do mínimo de R$ 2,50,
valor zero, vencimento no passado); repositório (busca por `external_id`
para o webhook, consulta de vencimentos, listagem por cliente); e as cinco
constraints do banco, cada uma bloqueando o que deveria.

---

## 8. Próximos Passos

1. ~~Testar as rotas de cliente~~ — feito via `TestClient` (ver 7.7)
2. ~~Commit do módulo de cliente~~ — feito (`5f233fa`)
3. ~~Renomear entidades para inglês~~ — feito (`b7c1d4e28f30`, ver 7.7)
4. ~~Tratamento de erro de constraint~~ — feito (`app/errors.py`, ver 7.8)
5. ~~Unicidade de CPF/CNPJ~~ — feito (`c93a5f17b204`, ver 7.8)
6. ~~Documentação do projeto~~ — feito (`docs/`, ver 7.10)
7. **Testes automatizados** (`pytest` + `TestClient` + banco de teste isolado) — hoje a verificação é script solto; virar suíte de verdade antes de o módulo de cobrança crescer
8. ~~Normalizar CPF/CNPJ~~ — feito (`d24e8b91fa07`, ver 7.9)
9. **Validação de dígito verificador** de CPF/CNPJ — o tamanho é conferido, o cálculo não
10. Módulo de **cobrança (Inter)**:
   - ~~Modelagem da entidade de cobrança, vinculada ao cliente~~ — feito (ver 7.11)
   - ~~Interface abstrata `BillingGateway` + implementação fake~~ — feito (ver 7.11)
   - **Camada de serviço de emissão** — orquestrar "buscar cliente → chamar gateway → persistir" numa transação, e criar `app/services/`
   - **Rotas REST de cobrança** (`/charges`)
   - **Decidir a modelagem de recorrência** (tabela `subscriptions` vs. cobranças auto-replicantes)
   - **Integração real com o Inter** (mTLS + OAuth2), quando houver credenciais
10. Módulo de **agendamento/envio via WhatsApp**:
   - Configuração da conta oficial (Meta Business)
   - Aprovação de template de mensagem
   - Rotina de verificação diária de vencimentos (scheduler)
11. Módulo de **CRM/leads**:
   - Webhook de recepção de mensagens
   - Fluxo estruturado de qualificação (sem IA generativa livre)
   - Painel de acompanhamento de leads
12. Definir e configurar hospedagem definitiva (Railway/Render + Supabase)
13. Front-end: sair do template do Next e construir a primeira tela real consumindo `/clients`

---

## 9. Pontos de Atenção / Débitos Técnicos

- ~~**`criado_em` sem `NOT NULL` no banco**~~ — quitado na migration `b7c1d4e28f30` (ver 7.7).
- ~~**Nomenclatura mista (PT/EN)**~~ — quitado na migration `b7c1d4e28f30` (ver 7.7).
- ~~**Violação de constraint retorna 500**~~ — quitado (ver 7.8).
- ~~**Sem unicidade em CPF e CNPJ**~~ — quitado (ver 7.8).
- ~~**`DELETE` de cliente é físico e perigoso**~~ — mitigado (ver 7.11): a FK com `ON DELETE RESTRICT` impede apagar cliente com cobranças, devolvendo 409.
- **Sem testes automatizados**: a validação do CRUD hoje é script avulso. Próximo passo natural: `pytest` + `TestClient` com banco de teste isolado.
- ~~**CPF/CNPJ sem normalização**~~ — quitado (ver 7.9).
- **Sem validação de dígito verificador** de CPF/CNPJ: o tamanho é conferido, mas não o cálculo do DV. `"11111111111"` é aceito.
- **Sem autenticação**: todos os endpoints são públicos. Bloqueante para deploy — hoje qualquer um listaria todos os clientes do escritório, com CPF e telefone.
- **Sem paginação** em `GET /clients/`: retorna a tabela inteira.
- **Sem linter/formatador** (`ruff`, `black`): o estilo depende de disciplina.
- **`Charge` ainda não tem rotas nem camada de serviço**: a entidade e o gateway existem, mas nada os orquestra ainda.
- **Recorrência não modelada**: o escritório cobra mensalmente e ainda não foi decidido como representar o contrato recorrente.
- **`notified_at` registra um envio, não várias tentativas**: se for preciso auditar cada tentativa de envio, vira tabela própria.
- **`venv` com pacotes alheios ao projeto** (`graphifyy`, `numpy`): não entraram no `requirements.txt`, mas vale limpar o ambiente em algum momento.
- **WhatsApp**: envio proativo de boleto não é 100% gratuito (custo pequeno por mensagem de template) — importante alinhar essa expectativa com o escritório.
- **Ambiente Windows**: diversos pontos de atenção específicos da máquina de desenvolvimento (Git Bash vs PowerShell, `psql` fora do PATH, necessidade de aspas em caminhos com espaço) — não afetam o código, mas vale documentar para onboarding de outro desenvolvedor no futuro.

---

## 10. Mensagem de Commit Sugerida (Módulo de Cliente)

```
feat: implementa CRUD de clientes com Alembic e Repository Pattern

- Configura SQLAlchemy e conexão com Postgres via .env
- Adiciona Alembic para versionamento de migrations
- Cria model Cliente com validação de tipo de pessoa (CPF/CNPJ)
- Cria schemas Pydantic (ClienteCreate, ClienteUpdate, ClienteResponse)
- Implementa ClientRepository para isolar acesso a dados
- Cria rotas CRUD de clientes (create, list, get, update, delete)
- Registra router de clientes na aplicação principal
```

---

## 11. Estrutura Atual de Pastas (Backend)

```
crm-andrade-backend/
├── venv/                          (não versionado)
├── alembic/
│   ├── versions/
│   │   ├── ec6f5bd69c7c_criar_tabela_clientes.py
│   │   └── b7c1d4e28f30_renomear_clientes_para_ingles.py
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── client_repository.py
│   └── routers/
│       ├── __init__.py
│       └── client.py
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── .env                            (não versionado)
```