# 07 — Convenções

## Nomenclatura

**Todo nome de código é em inglês** — arquivos, classes, funções,
variáveis, tabelas, colunas, constraints. Ver
[ADR 0007](decisoes/0007-nomenclatura-em-ingles.md).

**Texto para o usuário final é em português** — mensagens de erro de
validação, mensagens de constraint, textos de interface. Quem lê é o
escritório, não o desenvolvedor.

```python
class ClientCreate(BaseModel):      # ← código em inglês
    person_type: Literal["INDIVIDUAL", "COMPANY"]

    @model_validator(mode="after")
    def validate_document_by_person_type(self):
        if not self.cpf:
            raise ValueError("CPF é obrigatório para pessoa física")
            #                 ↑ mensagem ao usuário, em português
```

**Exceção deliberada: `cpf` e `cnpj`.** São nomes próprios do domínio
brasileiro. Traduzir para `tax_id` perderia a distinção entre os dois, que
é justamente o que as constraints precisam enforçar.

Comentários e docstrings ficam em português — é a língua de quem mantém o
código.

### Padrões de nome

| Elemento | Padrão | Exemplo |
|---|---|---|
| Classe | `PascalCase` | `ClientRepository` |
| Função, variável, coluna | `snake_case` | `get_by_id`, `person_type` |
| Constante | `UPPER_SNAKE` | `UNIQUE_VIOLATION` |
| Arquivo/módulo | `snake_case` | `client_repository.py` |
| Tabela | plural, `snake_case` | `clients` |
| Model | singular | `Client` |

### Nomes de constraints

Nomear constraints explicitamente é obrigatório. Se você não nomear, o
Postgres inventa algo como `clients_cpf_key` — e aí as migrations ficam
dependentes de um nome gerado, e o handler de erro não consegue mapear a
constraint para uma mensagem útil.

| Prefixo | Tipo | Exemplo |
|---|---|---|
| `uq_` | UNIQUE | `uq_clients_cpf` |
| `check_` | CHECK | `check_person_type_valid` |
| `fk_` | FOREIGN KEY | `fk_charges_client_id` |
| `ix_` | Índice | `ix_charges_due_date` |

## Git

### Branches

```
main      produção
homolog   homologação
develop   desenvolvimento  ← trabalho do dia a dia
```

O fluxo é `develop → homolog → main`. Enquanto o projeto não está em
produção, o trabalho acontece direto na `develop`.

### Mensagens de commit

[Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>: <resumo no imperativo, minúsculo, sem ponto final>

- detalhe
- detalhe
```

| Tipo | Uso |
|---|---|
| `feat` | Funcionalidade nova |
| `fix` | Correção de bug |
| `refactor` | Mudança que não altera comportamento |
| `docs` | Só documentação |
| `chore` | Dependências, configuração, tarefas de manutenção |
| `test` | Testes |

Exemplo real do projeto:

```
feat: implementa CRUD de clientes com Alembic e Repository Pattern

- Configura SQLAlchemy e conexão com Postgres via .env
- Adiciona Alembic para versionamento de migrations
- Cria model Cliente com validação de tipo de pessoa (CPF/CNPJ)
```

### O que nunca é versionado

Está no `.gitignore`:

- `.env` — credenciais de banco, e futuramente do Inter e da Meta
- `venv/` — ambiente virtual, reconstituível pelo `requirements.txt`
- `__pycache__/`
- Certificados do Banco Inter (`.crt`, `.key`) quando existirem

**Um certificado ou senha commitado é comprometido para sempre**, mesmo que
o commit seguinte o remova — ele continua no histórico. Se acontecer, a
credencial precisa ser revogada e regerada, não apenas apagada.

## Código

### Camadas e responsabilidades

Cada camada tem uma responsabilidade e não invade a vizinha:

| Camada | Faz | Não faz |
|---|---|---|
| Router | Traduz HTTP, injeta dependências | Query SQL, regra de negócio complexa |
| Schema | Valida entrada, formata saída | Acessar banco |
| Repository | Consulta e grava | Conhecer HTTP ou status code |
| Model | Mapear tabela | Regra de negócio |

### Repositórios recebem a sessão, não a criam

```python
class ClientRepository:
    def __init__(self, db: Session):   # ← recebe
        self.db = db
```

Quem controla a requisição controla a transação. Ver
[ADR 0004](decisoes/0004-repository-pattern.md).

### Erros do banco não são tratados nas rotas

Nenhum `try/except IntegrityError` dentro de um endpoint. O handler
centralizado em `app/errors.py` cuida disso para o sistema inteiro. Para
cobrir uma tabela nova, acrescenta-se uma entrada no dicionário
`CONSTRAINT_MESSAGES` — nenhuma rota muda.

### Comentários explicam *por quê*, não *o quê*

O código já diz o que faz. O comentário serve para o que não é óbvio:

```python
# No Postgres, UNIQUE permite múltiplos NULL. Isso é exatamente o
# comportamento desejado: toda pessoa jurídica tem cpf = NULL, e
# nenhuma delas colide com as outras.
UniqueConstraint("cpf", name="uq_clients_cpf"),
```

### Estilo

- 4 espaços de indentação (PEP 8)
- Linhas até ~100 caracteres
- Type hints em assinaturas públicas
- Imports em três blocos: stdlib, terceiros, aplicação

Ainda **não** há formatador ou linter configurado (`black`, `ruff`). É um
débito — sem eles, o estilo depende de disciplina.

## Documentação

- Mudou o comportamento? Atualize `docs/` **no mesmo commit**. Documentação
  atualizada depois é documentação que não é atualizada.
- Tomou uma decisão técnica com alternativa plausível? Escreva um ADR.
- ADRs **não são editados** depois de aceitos. Mudou de ideia? Novo ADR,
  e o antigo passa a `Substituído por ADR XXXX`.
