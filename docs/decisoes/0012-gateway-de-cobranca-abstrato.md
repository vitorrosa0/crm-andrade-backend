# ADR 0012 — Gateway de cobrança abstrato

**Status:** Aceito
**Data:** 2026-09-05

## Contexto

O módulo de cobrança é o núcleo do sistema, e depende da API do Banco Inter.
Mas as credenciais do Inter **exigem conta PJ ativa**, que ainda não existe
(ver [08 — Integrações](../08-integracoes.md)).

Três problemas decorrem disso:

1. **Não dá para desenvolver esperando a conta.** O módulo é grande demais
   para ficar parado até a burocracia bancária resolver.
2. **Não dá para testar contra o banco real.** Testes automatizados que
   emitem boletos de verdade são inviáveis — lentos, dependentes de rede, e
   com efeito colateral financeiro.
3. **O banco pode mudar.** O escritório pode trocar de instituição, ou
   passar a aceitar outro meio de pagamento.

## Decisão

A regra de negócio depende de uma **interface abstrata**, nunca do Inter
diretamente.

```python
class BillingGateway(ABC):
    @abstractmethod
    def issue(self, request: ChargeRequest) -> IssuedCharge: ...

    @abstractmethod
    def get_status(self, external_id: str) -> str: ...

    @abstractmethod
    def cancel(self, external_id: str) -> None: ...
```

**O gateway fala em dataclasses, não no model do ORM.** `issue()` recebe um
`ChargeRequest` (com `amount`, `due_date` e um `Payer`), e não a entidade
`Charge` do SQLAlchemy. Se recebesse o model, o adaptador do Inter ficaria
acoplado à nossa persistência — passaria a depender de *como guardamos* os
dados, o que não é da conta dele. A porta precisa ser independente das duas
pontas que ela separa.

Duas implementações:

- **`InterBillingGateway`** — a real. mTLS + OAuth2 contra a API do Inter.
- **`FakeBillingGateway`** — em memória. Gera identificadores e PDFs falsos,
  permite forçar cenários (pago, vencido, recusado) para teste.

Qual delas o sistema usa é decidido por configuração (`.env`), e injetado
via `Depends` do FastAPI. Nenhuma regra de negócio sabe qual está ativa.

## Justificativa

### Não é Strategy — é Dependency Inversion

A confusão é comum e a distinção importa:

**Strategy** é quando existem **várias formas igualmente válidas de fazer a
mesma coisa**, e se escolhe entre elas por regra de negócio, em runtime. Ex:
cálculo de juros simples vs. composto — ambos são "de verdade" e coexistem
em produção.

Aqui não é isso. Existe **uma** intenção — "emitir um boleto" — e as
implementações diferem só em **com quem falam**. O fake não é uma
alternativa de negócio; é um dublê. As duas nunca coexistem em produção.

O nome correto é **Dependency Inversion Principle** (o "D" do SOLID), e no
vocabulário de arquitetura hexagonal: `BillingGateway` é uma **porta**, e as
implementações são **adaptadores**.

O ganho não é flexibilidade de negócio — é **inverter a direção da
dependência**. Sem a interface, a regra de negócio depende do Inter. Com
ela, o Inter depende de um contrato que **nós** definimos. Quem manda no
formato é o domínio, não o fornecedor.

### Benefícios concretos

**Desenvolver antes das credenciais.** O módulo inteiro — modelo, regra,
rotas, agendamento — pode ser construído e testado com o fake. A integração
real vira o último passo, sem reescrever nada.

**Testes rápidos e determinísticos.** O fake permite simular boleto vencido,
pagamento recebido e falha de comunicação sem tocar a rede.

**Trocar de banco não toca a regra.** Um `BradescoBillingGateway` novo, e o
resto do sistema não percebe. Open-Closed na prática: aberto para extensão
(nova implementação), fechado para modificação (a regra não muda).

**A interface documenta o que o sistema precisa.** Ao escrevê-la antes de
ler a documentação do Inter, define-se o que o *domínio* precisa — e não se
deixa o formato da API do banco vazar para dentro do sistema.

## Consequências

**Positivas**

- Desenvolvimento desbloqueado, sem depender da conta PJ
- Testes sem rede e sem efeito colateral financeiro
- Troca de provedor localizada em uma classe
- Regra de negócio testável isoladamente

**Negativas**

- **Uma camada de indireção.** Para quem lê o código, há um salto a mais
  entre "emitir cobrança" e a chamada HTTP real
- **O fake pode mentir.** É o risco principal: um fake que não reproduz o
  comportamento real do Inter gera falsa confiança. Erros, timeouts e
  formatos precisam ser modelados com honestidade — e nada substitui um
  teste de integração real antes de ir a produção
- **Risco de abstração errada.** Definir a interface sem conhecer a API do
  Inter pode produzir um contrato que não encaixa. Mitigação: ler a
  documentação do Inter antes de fechar a interface, mesmo sem credencial
- Mais arquivos e mais código do que chamar a API direto

## Alternativas consideradas

**Chamar a API do Inter direto na regra de negócio** — Menos código,
caminho mais curto. Descartado: trava o desenvolvimento até a conta existir,
impossibilita teste automatizado e acopla o domínio ao fornecedor.

**Usar uma biblioteca pronta** (ex: `bancointer-python`) — Pouparia
implementar mTLS e OAuth2. Não descartado — pode muito bem ser usada
**dentro** do `InterBillingGateway`. A decisão aqui é sobre a fronteira,
não sobre como o adaptador se implementa por dentro.

**Mockar nos testes, sem interface** (`unittest.mock.patch`) — Resolveria o
teste, mas não o desenvolvimento sem credencial, e deixaria o acoplamento de
pé. Mock resolve sintoma; a interface resolve a causa.

## Próximos passos

1. Ler a documentação da API de Cobrança do Inter, mesmo sem credencial
2. Modelar a entidade `Charge` ([03 — Modelo de dados](../03-modelo-de-dados.md))
3. Definir a interface `BillingGateway` a partir do que o domínio precisa
4. Implementar `FakeBillingGateway` e construir o módulo inteiro contra ele
5. Implementar `InterBillingGateway` quando houver conta PJ

**Implementado em 2026-09-05:** `app/gateways/billing.py` (a porta) e
`app/gateways/fake_billing.py` (o adaptador falso). O `InterBillingGateway`
segue pendente das credenciais.

O fake reproduz de propósito recusas do mundo real — cobrança paga não pode
ser cancelada, id inexistente levanta `ChargeNotFoundError` — e expõe
`fail_next_calls` para exercitar o caminho de erro sem depender de a rede
cair. Ainda assim vale a ressalva registrada acima: **um fake que mente é
pior que nenhum fake**, e nada substitui um teste de integração real antes
de produção.
