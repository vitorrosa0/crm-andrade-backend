# ADR 0015 — Status de cobrança separado dos fatos de emissão e envio

**Status:** Aceito
**Data:** 2026-09-05

## Contexto

Uma cobrança passa por vários acontecimentos ao longo da vida:

1. É criada no sistema
2. O boleto é emitido no banco
3. O boleto é enviado ao cliente pelo WhatsApp
4. O cliente paga — ou não, e a cobrança vence

O esboço inicial ([03 — Modelo de dados](../03-modelo-de-dados.md)) previa
uma coluna `status` com todos esses estados juntos:

```
PENDING / SENT / PAID / OVERDUE / CANCELLED
```

## O problema

**Esses fatos não são mutuamente exclusivos.** Uma cobrança emitida,
enviada e paga é o caso **normal** — não uma exceção. Com uma coluna só,
os três não cabem: gravar `PAID` apaga a informação de que foi enviada.

As perguntas que o sistema precisa responder deixam isso evidente:

- "Quais cobranças pagas ainda não tinham sido enviadas?" — impossível
- "Este boleto já foi emitido no banco?" — perdido assim que vira `PAID`
- "Reenviar as que foram enviadas há mais de 3 dias e continuam pendentes"
  — precisa de "foi enviada" **e** "não foi paga" ao mesmo tempo

Modelar assim é confundir uma **máquina de estados** (o pagamento, que de
fato é sequencial e exclusivo) com um **registro de fatos** (emissão,
notificação — coisas que aconteceram, e continuam tendo acontecido).

## Decisão

`status` guarda **apenas o ciclo de vida do pagamento**:

```
PENDING → PAID
        → OVERDUE
        → CANCELLED
```

Os demais acontecimentos viram colunas próprias, cada um com o momento em
que ocorreu:

| Coluna | O fato que registra |
|---|---|
| `external_id` + `issued_at` | O boleto existe no banco |
| `notified_at` | O boleto foi enviado ao cliente |
| `paid_at` | O pagamento foi confirmado |

**Timestamp em vez de booleano**, deliberadamente: `notified_at` responde
"foi enviada?" (é nulo ou não) **e** "quando?" — enquanto um
`is_notified = true` responderia só a primeira, e a segunda pergunta
apareceria uma semana depois.

### Constraints que amarram a coerência

O banco não deixa os dois lados divergirem:

```sql
-- Paga precisa dizer quando; nenhuma outra pode ter data de pagamento
CHECK ((status = 'PAID' AND paid_at IS NOT NULL) OR
       (status <> 'PAID' AND paid_at IS NULL))

-- Identificador do banco e data de emissão existem juntos, ou nenhum dos dois
CHECK ((external_id IS NULL AND issued_at IS NULL) OR
       (external_id IS NOT NULL AND issued_at IS NOT NULL))
```

Sem elas, colunas separadas seriam um convite à inconsistência — uma
cobrança `PAID` sem `paid_at`, ou com `external_id` de um boleto que nunca
foi emitido. É o mesmo princípio de
[ADR 0009](0009-integridade-garantida-pelo-banco.md): o banco garante o que
a aplicação apenas promete.

## Justificativa

**Cada coluna responde a uma pergunta, e só uma.** "Foi paga?" é `status`.
"Foi emitida?" é `external_id IS NOT NULL`. "Foi avisado?" é `notified_at`.
Nenhuma sobrescreve a resposta da outra.

**O histórico não se perde.** Uma cobrança paga continua sabendo quando foi
emitida e quando foi avisada. Isso importa para o painel do escritório, e
mais ainda para uma eventual disputa ("vocês nunca me mandaram o boleto").

**As consultas da rotina diária ficam diretas.** "Vence em 5 dias, ainda
pendente, e ainda não foi avisado" é um `WHERE` de três condições sobre
três colunas — não uma decodificação de estados combinados.

**A máquina de estados fica pequena e revisável.** Quatro estados de
pagamento, com transições óbvias. Misturar emissão e envio produziria uma
explosão combinatória de estados que ninguém consegue validar.

## Consequências

**Positivas**

- Nenhuma informação é sobrescrita por outra
- Consultas do agendador e do painel são diretas
- Auditoria completa: dá para reconstruir a linha do tempo de cada cobrança
- A máquina de estados de pagamento fica trivial de validar

**Negativas**

- **Mais colunas.** Seis, onde uma poderia (mal) servir
- **Mais constraints para manter.** As duas CHECK precisam acompanhar
  qualquer mudança no ciclo de vida — se um estado novo entrar, elas
  precisam ser revistas
- **Nada impede uma ordem absurda por si só.** O banco aceita `notified_at`
  anterior a `issued_at`. Amarrar isso exigiria mais constraints; ficou de
  fora por ora, já que a aplicação é quem escreve esses campos
- **Não guarda múltiplas tentativas.** `notified_at` registra um envio, não
  três. Se for preciso saber cada tentativa, isso vira uma tabela própria —
  ver abaixo

## O que ficou de fora

**Tabela de tentativas de envio.** Se o escritório precisar reenviar
boletos e auditar cada tentativa (com erro, status de entrega do WhatsApp,
data), `notified_at` não basta — seria uma tabela `charge_notifications`
com uma linha por tentativa.

Não foi feito porque ainda não há requisito para isso, e a coluna resolve o
caso conhecido ("já avisei este cliente?"). O gatilho para mudar é: **a
primeira vez que alguém perguntar "quantas vezes tentamos avisar?"**.

## Alternativas consideradas

**Status único com todos os estados** — Mais simples de ler à primeira
vista. Descartado: perde informação, como demonstrado acima.

**Tabela de eventos** (`charge_events`, uma linha por acontecimento) —
Auditoria perfeita, event sourcing leve. Descartado por ora: toda consulta
de "estado atual" viraria uma agregação, e o painel do escritório pergunta
justamente isso o tempo todo. Complexidade não justificada nesta escala.

**Booleanos em vez de timestamps** (`is_notified`, `is_issued`) —
Descartado: responde metade da pergunta e a data acaba sendo pedida depois,
custando uma migration a mais.
