# ADR 0004 — Repository Pattern com sessão injetada

**Status:** Aceito
**Data:** 2026-07

## Contexto

O caminho mais curto seria a rota consultar o banco diretamente:

```python
@router.get("/clients/{client_id}")
def get_client(client_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Cliente).filter(Cliente.id == client_id).first()
```

Funciona. Mas espalha `db.query(...)` por todos os endpoints, e conforme o
sistema cresce a mesma consulta aparece em três lugares ligeiramente
diferentes. Trocar qualquer coisa na camada de dados vira uma caçada.

## Decisão

Todo acesso a dados passa por uma classe **Repository**, uma por entidade.
O repositório **recebe** a sessão pelo construtor — não a cria.

```python
class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()
```

## Justificativa

### Por que um repositório

**Um lugar só para o acesso a dados.** Mudar de ORM, adicionar cache,
introduzir *soft delete* — tudo acontece dentro do repositório. As rotas
não percebem.

**Open-Closed Principle.** É o exemplo concreto do princípio no projeto:
para mudar *como* os dados são buscados, não se toca em quem os consome.

**Testabilidade.** Um repositório é substituível por um duplo em memória,
permitindo testar regra de negócio sem banco.

**Vocabulário do domínio.** `repository.get_by_id(x)` diz o que se quer;
`db.query(Client).filter(...).first()` diz como se obtém. A primeira forma
sobrevive a mudanças de implementação.

### Por que a sessão é injetada, e não criada

Este é o ponto que mais importa, e o mais fácil de errar.

Se o repositório criasse a própria sessão:

```python
class ClientRepository:
    def __init__(self):
        self.db = SessionLocal()   # ← ERRADO
```

...cada repositório viveria em uma transação separada. Consequências:

1. **Atomicidade impossível.** No módulo de cobrança será necessário criar
   uma cobrança e atualizar o cliente na **mesma** transação. Com sessões
   separadas, uma pode ser confirmada e a outra falhar, deixando o banco
   inconsistente.
2. **Vazamento de conexões.** Ninguém teria a responsabilidade clara de
   fechar. Sob carga, o pool esgota e a aplicação trava.
3. **Objetos de sessões diferentes não se relacionam.** O SQLAlchemy
   recusa associar entidades carregadas em sessões distintas.

Com a sessão injetada, quem controla a requisição controla a transação — e
quem controla a requisição é o FastAPI, via `Depends(get_db)`:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()      # roda sempre, inclusive se a rota levantar exceção
```

Isso é **Dependency Injection** e **Inversão de Controle** aplicados de
forma concreta: a dependência é entregue de fora, e o ciclo de vida
pertence a quem tem a informação para gerenciá-lo.

## Consequências

**Positivas**
- Um ponto único de mudança para acesso a dados
- Transações compostas se tornam possíveis
- Conexões nunca vazam
- Regra de negócio testável sem banco

**Negativas**
- **Mais código para o caso trivial.** No CRUD atual, o repositório é quase
  um repasse. O ganho só aparece quando as consultas ficam complexas —
  é um investimento antecipado, conscientemente
- Risco de o repositório virar depósito de métodos específicos demais
  (`get_by_name_and_phone_ordered_by_date`), sinal de que falta uma camada
  de serviço
- Uma indireção a mais para quem lê o código pela primeira vez

## Alternativas consideradas

**Query direto na rota** — Mais simples no começo. Descartado por espalhar
acesso a dados e travar qualquer evolução futura.

**Active Record** (métodos no próprio model, `Client.find_by_id()`) —
Comum em Django e Rails. Descartado por acoplar a entidade à persistência,
o que dificulta testar o domínio isoladamente.

**Unit of Work** — Padrão mais completo, que coordena vários repositórios
sob uma transação. Descartado **por ora**: com uma entidade só, seria
cerimônia vazia. Vale reconsiderar quando cobranças e clientes precisarem
ser gravados atomicamente.
