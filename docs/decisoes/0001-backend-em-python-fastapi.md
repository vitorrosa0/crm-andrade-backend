# ADR 0001 — Backend em Python com FastAPI

**Status:** Aceito
**Data:** 2026-07

## Contexto

O front-end seria Next.js + TypeScript, tecnologia que o Vitor já domina. A
escolha óbvia para o back-end seria Node.js — mesma linguagem, um contexto
mental só, entrega mais rápida.

Mas o projeto tem dois objetivos simultâneos: **entregar um sistema
funcionando** e **servir de aprendizado prático** para a graduação em
Engenharia de Software. Uma stack inteiramente conhecida atenderia o
primeiro e desperdiçaria o segundo.

Além disso, o sistema é essencialmente uma **camada de integração**: fala
com a API do Banco Inter (OAuth2 + mTLS + certificados), com a API do
WhatsApp, e roda uma rotina agendada de verificação de vencimentos.

## Decisão

Back-end em **Python com FastAPI**.

## Justificativa

**Desafio calibrado.** Python é uma linguagem que o Vitor conhece o
suficiente para não travar, mas não domina o bastante para o projeto ser
mecânico. É a zona onde se aprende de verdade.

**Ecossistema de integração.** Certificados, mTLS, OAuth2, agendamento —
Python tem bibliotecas maduras e muito exemplo pronto para exatamente esse
tipo de trabalho. A integração com o Inter, em particular, tem
implementações de referência públicas em Python.

**Pydantic.** A validação declarativa e tipada do FastAPI é a peça que mais
pesou. O contrato da API vira código executável, e a documentação
interativa (Swagger) sai de graça a partir dele.

**Documentação automática.** Sem escrever uma linha extra, existe um
`/docs` navegável. Para um desenvolvedor solo, isso substitui uma
ferramenta inteira.

## Consequências

**Positivas**
- Duas linguagens praticadas em vez de uma
- Ferramental adequado às integrações que são o núcleo do projeto
- Swagger sem custo
- Tipagem forte nas duas pontas (Pydantic e TypeScript)

**Negativas**
- **Troca de contexto** entre TS e Python a cada sessão de trabalho
- **Nada é compartilhado** entre front e back. Os tipos do cliente estão
  escritos duas vezes, e podem divergir silenciosamente. Mitigação
  possível: gerar tipos TS a partir do `openapi.json`
- Mais lento no começo — cada tarefa trivial custa uma consulta a mais
- Dois `package manager`, dois toolings, dois pipelines de deploy

**Risco assumido:** para um desenvolvedor solo com poucas horas por semana,
qualquer atrito extra é significativo. A aposta é que o aprendizado
compensa — e que a facilidade do FastAPI nas integrações devolve o tempo
perdido no começo.

## Alternativas consideradas

**Node.js + Express/NestJS** — Uma linguagem só, tipos compartilháveis
entre front e back, entrega mais rápida. Descartado por não agregar
aprendizado e por ecossistema menos confortável para certificados/mTLS.

**Java + Spring Boot** — Excelente para sistemas financeiros e comum no
mercado. Descartado por verbosidade e cerimônia altas demais para um
projeto solo de poucas horas semanais.

**Go** — Ótimo desempenho e binário único (deploy simples). Descartado:
desempenho não é gargalo aqui, e a curva seria mais íngreme sem benefício
proporcional.
