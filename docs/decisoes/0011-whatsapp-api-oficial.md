# ADR 0011 — Apenas a API oficial do WhatsApp

**Status:** Aceito
**Data:** 2026-07

## Contexto

O sistema precisa enviar o boleto ao cliente pelo WhatsApp, 5 dias antes do
vencimento. Há dois caminhos técnicos:

**1. WhatsApp Business Platform (API oficial da Meta).** Requer conta
comercial verificada, número dedicado, e template aprovado para mensagens
iniciadas pela empresa. Tem custo por mensagem.

**2. Bibliotecas não-oficiais** (Baileys, whatsapp-web.js). Simulam um
cliente WhatsApp comum — conectam via QR code, como o WhatsApp Web. Sem
verificação, sem template, sem custo por mensagem.

A segunda opção é tentadora: gratuita, sem burocracia, funciona com o número
que o escritório já usa, e implementa-se em uma tarde.

## Decisão

**Apenas a API oficial.** Bibliotecas não-oficiais estão descartadas.

## Justificativa

**Violam os termos de uso.** Automatizar o WhatsApp por cliente não-oficial
é proibido pela Meta. Não é uma zona cinzenta — está escrito.

**O número pode ser banido, sem aviso e sem recurso.** Este é o argumento
decisivo. O número usado seria o do **escritório de advocacia** — o mesmo
por onde clientes reais falam sobre processos reais. Perdê-lo significa:

- Perder o canal de contato com toda a carteira de clientes
- Perder o histórico de conversas
- Ter que avisar cada cliente do número novo
- Um dano operacional muito maior do que o sistema jamais valeria

O risco não é proporcional ao ganho. Economizar ~R$ 2/mês não justifica
apostar o canal de comunicação do escritório.

**LGPD.** Tratar dados pessoais de clientes (nome, valor devido, boleto)
por canal não-oficial, sem garantia contratual do provedor, é exposição
regulatória. Para um escritório de advocacia, ser flagrado descumprindo a
LGPD é um problema de reputação profissional, não só uma multa.

**Fragilidade técnica.** Essas bibliotecas dependem de engenharia reversa do
protocolo. A Meta muda algo, a biblioteca quebra, e o sistema para de enviar
boletos — silenciosamente, provavelmente descoberto quando os clientes não
pagarem.

**Este projeto já herdou um fracasso.** A tentativa anterior morreu por
escolher uma solução que "funcionava" mas não era confiável o bastante para
ser liberada. Repetir o padrão com outro componente seria não ter aprendido
nada — ver [ADR 0010](0010-sem-ia-generativa-livre.md).

## Consequências

**Positivas**

- Sem risco de banimento do número do escritório
- Conformidade com termos de uso e com a LGPD
- Estabilidade contratual: a Meta versiona e anuncia mudanças
- Recursos oficiais: status de entrega, leitura, mensagens interativas

**Negativas**

- **Não é gratuito.** Mensagem de Utilidade custa ~R$ 0,035. Um escritório
  com 50 clientes gastaria ~R$ 1,75/mês — trivial, mas **contraria a
  premissa de custo zero com que o projeto foi apresentado.** Precisa ser
  alinhado com o escritório **antes**, não na primeira fatura
- **Burocracia.** Conta comercial verificada no Meta Business, com envio de
  documentos e prazo de aprovação
- **Número dedicado obrigatório.** Um número migrado para a API deixa de
  funcionar no aplicativo comum. O escritório precisa de uma linha nova —
  não pode usar a que já usa
- **Template engessado.** Mensagens iniciadas pela empresa exigem template
  pré-aprovado, com texto fixo e variáveis. Alterar exige nova aprovação
  (horas a dias). O template precisa ser bem desenhado de primeira

## Nota sobre custo

Vale registrar a distinção que determina o preço, porque ela não é óbvia:

| Tipo de conversa | Quem inicia | Custo |
|---|---|---|
| Atendimento | O cliente | **Gratuito e ilimitado** (janela de 24h para responder) |
| Utilidade | A empresa | ~R$ 0,035/mensagem, exige template |

O envio proativo do boleto é **iniciado pela empresa** — portanto, pago.

Já o módulo de **leads** tende a ser gratuito: o lead inicia a conversa
(respondeu um anúncio), e o sistema responde dentro da janela de 24h.

## Alternativas consideradas

**Baileys / whatsapp-web.js** — Gratuito e sem burocracia. Descartado pelo
risco de banimento e pela exposição de LGPD.

**Provedor intermediário** (Twilio, Zenvia, 360dialog) — Camada sobre a API
oficial que simplifica a burocracia. Descartado **por ora** por adicionar
margem sobre o custo por mensagem e mais um fornecedor. Vale reconsiderar se
a verificação direta na Meta se mostrar penosa demais.

**E-mail em vez de WhatsApp** — Gratuito e sem burocracia. Descartado porque
o escritório já usa WhatsApp com os clientes, e a taxa de leitura de e-mail
é muito menor. O objetivo é o boleto ser visto e pago.

**SMS** — Descartado: mais caro que WhatsApp, não suporta anexo, e tem baixa
confiança do destinatário.
