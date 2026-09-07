# ADR 0010 — Sem IA generativa livre no atendimento

**Status:** Aceito
**Data:** 2026-07

## Contexto

Esta decisão não é teórica — ela nasce de um fracasso concreto.

**A tentativa anterior de desenvolvimento do sistema falhou exatamente
aqui.** O desenvolvedor responsável integrou uma IA generativa livre para
responder automaticamente os leads vindos de anúncios. O resultado foi
imprevisível o suficiente para que ele próprio não se sentisse seguro em
liberar o sistema para uso. O escritório continuou pagando hospedagem por
um produto que nunca entrou em operação.

O risco de fundo: um modelo de linguagem gerando texto livre em nome de um
**escritório de advocacia**, falando com potenciais clientes sobre
**questões jurídicas**. Uma resposta inventada pode:

- Dar orientação jurídica errada, que a pessoa siga
- Prometer prazo, valor ou resultado que o escritório não pode cumprir
- Afirmar algo que caracterize relação advogado-cliente indevidamente
- Expor o escritório perante a OAB e perante a lei

O escritório é um escritório de advocacia. Exposição jurídica é
exatamente o tipo de risco que ele menos pode assumir.

## Decisão

**Nenhum LLM gera texto livre que seja enviado a um cliente ou lead.**

O atendimento inicial é feito por um **fluxo estruturado**: árvore de
decisão com perguntas fixas, definidas por área jurídica, todas escritas e
aprovadas por um humano.

### Uso aceitável de IA

Se houver IA no fluxo, restrita à **classificação**: dado o texto do lead,
identificar a área jurídica provável para rotear a conversa.

A distinção é a natureza da saída:

| | Saída | Se errar |
|---|---|---|
| **Classificação** (aceito) | Um rótulo de um conjunto fechado (`TRABALHISTA`, `FAMILIA`, …) | Pergunta fora de contexto. Recuperável, constrangimento pequeno |
| **Geração** (proibido) | Texto livre enviado ao lead | Orientação jurídica errada em nome do escritório. Não recuperável |

Mesmo na classificação, o texto apresentado ao lead continua sendo fixo e
escrito por humano — a IA só escolhe **qual** texto, nunca **o** texto.

## Justificativa

**Determinismo.** Um fluxo estruturado faz a mesma coisa sempre. Pode ser
testado, revisado e aprovado antes de entrar no ar. Um LLM pode responder
diferente para a mesma pergunta.

**Auditabilidade.** Se um lead reclamar do que foi dito, é possível apontar
exatamente qual nó da árvore produziu qual texto. Com geração livre, a
resposta é irreprodutível.

**Aprovação prévia.** Todo texto que sai do sistema pode passar pelo crivo
do escritório antes de ser usado. Isso é impossível com geração em tempo
real.

**Custo zero.** Sem chamadas a API de modelo, sem custo por token, sem
dependência de disponibilidade de terceiro.

**O escopo real é modesto.** O objetivo do primeiro atendimento é
**qualificar**: descobrir a área de interesse e coletar contato, para
passar a um advogado. Isso é um formulário conversacional. Não precisa de
inteligência — precisa de confiabilidade.

**O precedente.** A tentativa anterior já provou empiricamente que essa
abordagem não funcionava para este cliente. Repeti-la seria ignorar a
evidência disponível.

## Consequências

**Positivas**

- Comportamento previsível e testável
- Nenhum risco de o sistema dizer algo juridicamente comprometedor
- Custo zero e sem dependência externa
- O escritório aprova exatamente o que será dito
- Rastreabilidade completa das conversas

**Negativas**

- **Conversa mais engessada.** O lead percebe que fala com um sistema. Uma
  IA soaria mais natural
- **Não lida com o inesperado.** Uma pergunta fora da árvore não tem
  resposta boa. Mitigação: sempre oferecer a saída "falar com um atendente"
- **Manutenção manual.** Cada área jurídica nova exige desenhar o fluxo à
  mão
- **Menos impressionante.** "Fluxo estruturado" vende menos que "IA". Mas
  o objetivo é funcionar, não impressionar

## Alternativas consideradas

**LLM com prompt restritivo** — Instruir o modelo a só falar de certos
assuntos. Descartado: prompt não é garantia. É uma sugestão forte, e
existem formas conhecidas de contorná-la. Para um domínio com risco
jurídico, "quase sempre obedece" não é suficiente.

**LLM com respostas pré-aprovadas** (o modelo escolhe entre textos
prontos) — Essencialmente a classificação já aceita acima, com o modelo no
papel de roteador. É a evolução natural, se o fluxo fixo se mostrar
insuficiente.

**LLM com revisão humana antes do envio** — Elimina o risco, mas também
elimina a automação: alguém precisaria aprovar cada mensagem, que é
exatamente o trabalho manual que o sistema deveria remover.

## Revisão

Esta decisão pode ser revista se — e somente se — houver evidência de que o
fluxo estruturado está perdendo leads por rigidez. Mesmo então, o caminho
seria a classificação, não a geração livre.
