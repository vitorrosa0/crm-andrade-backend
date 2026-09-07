# 01 — Visão geral

## O problema

Um escritório de advocacia cobra seus clientes de forma **recorrente**
(honorários mensais). Hoje esse processo é inteiramente manual:

1. Alguém do escritório abre o aplicativo do Banco Inter
2. Gera o boleto de cada cliente, um por um
3. Envia o boleto pelo WhatsApp, manualmente
4. Acompanha os pagamentos conferindo o extrato

Isso se repete todo mês, para todos os clientes. É trabalho repetitivo,
sujeito a esquecimento (boleto não enviado = pagamento atrasado) e não
gera nenhum registro consultável do que foi cobrado e do que foi pago.

Em paralelo, o escritório recebe **leads de anúncios** e o primeiro
atendimento também é manual — alguém precisa responder, perguntar a área
de interesse e qualificar o contato antes de passar para um advogado.

## A solução

Um sistema que automatiza os dois fluxos:

**Cobrança.** Cadastro de clientes e de cobranças recorrentes. O sistema
gera o boleto via API do Banco Inter, envia ao cliente pelo WhatsApp
**5 dias antes do vencimento**, e acompanha o status de pagamento em um
painel.

**CRM de leads.** Recebe leads via webhook, conduz um **fluxo estruturado**
de qualificação (perguntas fixas por área jurídica) e entrega o contato já
triado para a equipe.

## Escopo

### Dentro do escopo

- Cadastro de clientes (pessoa física e jurídica)
- Cobrança recorrente integrada ao Banco Inter
- Envio automático do boleto via WhatsApp, 5 dias antes do vencimento
- Painel de acompanhamento de status de pagamento
- Recepção e qualificação estruturada de leads
- Painel de CRM para a equipe
- Hospedagem gratuita (eliminando o custo atual de servidor)

### Fora do escopo

- **Atendimento jurídico automatizado por IA.** Decisão consciente — ver
  [ADR 0010](decisoes/0010-sem-ia-generativa-livre.md).
- **Negociação de dívidas automatizada.** Envolve decisão de negócio que
  o sistema não tem competência para tomar.
- **ERP completo** (folha, contabilidade, gestão de processos jurídicos).
  Existe software especializado para isso; competir seria desperdício.

## Contexto e histórico

A demanda chegou através de um primo do desenvolvedor. Começou apenas como
"automatizar as cobranças" e cresceu para incluir o CRM de leads.

**Houve uma tentativa anterior que falhou.** O desenvolvedor responsável
tentou plugar uma IA generativa livre para responder os leads
automaticamente. O resultado foi imprevisível o bastante para que ele
próprio não se sentisse seguro em liberar para uso. O escritório ficou
pagando hospedagem (Hostinger) por um produto que nunca entrou em operação.

Esse fracasso é o motivo direto de duas decisões deste projeto: **não usar
IA generativa livre** para falar com clientes ([ADR 0010](decisoes/0010-sem-ia-generativa-livre.md))
e **migrar para hospedagem gratuita**, para que o escritório não pague
enquanto não houver valor entregue.

## Quem está envolvido

- **Escritório de advocacia** — cliente final. Quem usa o painel e sofre
  com o processo manual hoje.
- **Clientes do escritório** — recebem os boletos pelo WhatsApp. Não usam
  o sistema diretamente, mas são quem mais interage com a saída dele.
- **Leads** — pessoas que responderam anúncios e entram pelo fluxo de
  qualificação.
- **Vitor** — desenvolvedor único. Em formação em Engenharia de Software,
  toca o projeto como *side project*, com poucas horas por semana.

## Restrições que moldam o projeto

Estas não são detalhes — elas explicam boa parte das decisões técnicas:

| Restrição | Consequência |
|---|---|
| **Desenvolvedor único, poucas horas/semana** | Prioriza-se stack conhecida e simplicidade sobre sofisticação. Nada de microsserviços, filas ou infra complexa. |
| **Custo precisa ser ~zero** | Free tier em tudo (Supabase, Railway/Render). Os 100 boletos/mês gratuitos do Inter provavelmente cobrem o escritório inteiro. |
| **O projeto também é aprendizado** | Justifica escolher Python/FastAPI (que o Vitor não dominava) e aplicar patterns explicitamente, mesmo quando uma solução mais direta funcionaria. |
| **Já houve um fracasso antes** | Confiabilidade e previsibilidade valem mais que features impressionantes. O sistema precisa fazer pouco, mas fazer certo. |
| **Lida com dados pessoais (LGPD)** | CPF, CNPJ, telefone e e-mail são dados pessoais. Influencia decisões de ID ([ADR 0005](decisoes/0005-uuid-como-chave-primaria.md)) e a rejeição de bibliotecas não-oficiais de WhatsApp. |
