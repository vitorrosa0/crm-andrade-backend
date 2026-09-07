# 08 — Integrações externas

Nenhuma destas está implementada. Este documento registra a análise de
viabilidade feita antes de começar, para que as decisões não precisem ser
redescobertas.

---

## Banco Inter — API de Cobrança

### O que resolve

Emissão programática de boletos (com Pix embutido), consulta de status de
pagamento e webhook de baixa automática. É o núcleo do sistema.

### Credenciais

**São gratuitas.** Não se paga pela API — paga-se por boleto emitido acima
da franquia.

**Exigem conta PJ.** O Inter não libera API para conta pessoa física. Esta
é a barreira real do projeto, não o custo.

Como obter, no Internet Banking:

```
Conta Digital → Aplicações → Nova aplicação
```

Sai dali:

| Item | Para quê |
|---|---|
| `client_id` | Identifica a aplicação no OAuth |
| `client_secret` | Autentica a aplicação no OAuth |
| Certificado (`.crt`) | Autenticação mTLS |
| Chave privada (`.key`) | Par do certificado |
| Número da conta corrente | Header `x-conta-corrente`, obrigatório quando a aplicação tem acesso a mais de uma conta |

Na criação da aplicação escolhem-se também **quais contas** e **quais
escopos** ela pode operar. Princípio a seguir: conceder só o escopo de
cobrança, nada além.

### Autenticação: duas camadas

Isto costuma confundir, então vale explicitar — são mecanismos
independentes e **ambos** obrigatórios:

1. **mTLS** (*mutual TLS*). No TLS comum, só o servidor prova quem é. No
   mTLS, o cliente também apresenta certificado. O par `.crt`/`.key` prova,
   no nível da conexão, que quem está chamando é a sua aplicação.
2. **OAuth2 client credentials.** Sobre a conexão já autenticada, troca-se
   `client_id` + `client_secret` por um *access token* de curta duração,
   usado no header `Authorization` das chamadas seguintes.

O token deve ficar **apenas em memória**, com renovação automática ao
expirar. Nunca persistido em banco ou arquivo.

### Custos

| Item | Valor |
|---|---|
| Boletos gratuitos | **100/mês** |
| Excedente (Pix) | ~R$ 0,99 |
| Excedente (linha digitável) | ~R$ 2,49 |
| Cobrança mínima | R$ 2,50 |

> ⚠️ Números levantados na análise inicial e **não reconfirmados**.
> Confirmar com o gerente antes de prometer custo ao escritório. Para a
> escala do escritório, a franquia de 100/mês provavelmente cobre tudo —
> o que significa **custo zero de cobrança**.

### Como será implementado

Atrás de uma interface abstrata `BillingGateway`, com uma implementação
falsa para desenvolvimento. Isso permite construir e testar o módulo
inteiro **antes** de a conta PJ existir. Ver
[ADR 0012](decisoes/0012-gateway-de-cobranca-abstrato.md).

---

## WhatsApp — envio do boleto

### A distinção que determina o custo

A Meta cobra por **conversa**, e o preço depende de quem iniciou:

| Tipo | Quem inicia | Custo |
|---|---|---|
| Atendimento | O cliente | **Gratuito e ilimitado** (janela de 24h para responder) |
| Utilidade | A empresa | ~R$ 0,035/mensagem, exige template aprovado |

O envio do boleto 5 dias antes do vencimento é **iniciado pela empresa**.
Portanto: categoria Utilidade, template aprovado pela Meta, e **não é
gratuito**.

> ⚠️ **Alinhar essa expectativa com o escritório.** O projeto foi
> apresentado com a premissa de custo zero. Um escritório com 50 clientes
> gastaria cerca de R$ 1,75/mês — trivial, mas precisa ser dito antes, não
> na primeira fatura.

### Template

Mensagens iniciadas pela empresa exigem template previamente aprovado —
texto fixo com variáveis. Algo como:

```
Olá, {{1}}. Seu boleto de {{2}} vence em {{3}}.
Segue o documento para pagamento.
```

Aprovação leva de horas a dias, e o template **não pode ser alterado** sem
nova aprovação. Convém desenhá-lo com cuidado antes de submeter.

### Pré-requisitos

- Conta comercial verificada no Meta Business
- **Número dedicado**, separado do WhatsApp que o escritório já usa. Um
  número migrado para a API deixa de funcionar no aplicativo comum — se
  usarem o número do escritório, perdem o WhatsApp do dia a dia.

### Bibliotecas não-oficiais: rejeitadas

Existem bibliotecas (Baileys, whatsapp-web.js) que automatizam o WhatsApp
sem passar pela API oficial, sem custo por mensagem. **Foram descartadas.**
Ver [ADR 0011](decisoes/0011-whatsapp-api-oficial.md). Em resumo: violam os
termos de uso, o número pode ser banido a qualquer momento sem aviso, e
tratar dados pessoais por canal não-oficial é problema de LGPD — o
escritório é um escritório de advocacia, exposição jurídica é o custo que
menos pode assumir.

---

## Módulo de leads / IA

### Sem IA generativa livre

Decisão central do projeto, herdada diretamente do fracasso anterior.
Nenhum LLM gera texto livre enviado a um cliente ou lead. Ver
[ADR 0010](decisoes/0010-sem-ia-generativa-livre.md).

### O que substitui

Um **fluxo estruturado**: árvore de decisão com perguntas fixas por área
jurídica. Determinístico, auditável, testável, e — decisivo — todo texto
que sai foi escrito e aprovado por um humano.

### Uso aceitável de IA

Se algum dia houver IA no fluxo, restrita a **classificação**: dado o texto
do lead, identificar a área jurídica provável para rotear a conversa. A
saída é um rótulo de um conjunto fechado, nunca texto para o cliente. Se
classificar errado, o pior caso é uma pergunta fora de contexto — não uma
promessa jurídica indevida.

---

## Hospedagem

| Camada | Candidato | Situação |
|---|---|---|
| Banco | Supabase | Free tier; resolveria também autenticação |
| Backend | Railway ou Render | Free tier; precisa rodar scheduler |
| Frontend | Vercel | Natural para Next.js |

Requisito que elimina opções: o envio de boletos exige uma **rotina diária**
que varre vencimentos. Hospedagem puramente serverless, que dorme sem
tráfego, não serve sem um gatilho externo (cron job).

Nada decidido ainda.
