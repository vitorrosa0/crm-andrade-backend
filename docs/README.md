# Documentação — CRM Andrade (backend)

Documentação técnica do backend do CRM Andrade. O objetivo é que qualquer
pessoa (inclusive o Vitor daqui a seis meses) consiga entender **o que o
sistema faz, como está construído e — principalmente — por que foi
construído assim**.

## Como navegar

| Documento | Para quê |
|---|---|
| [01 — Visão geral](01-visao-geral.md) | O problema, o escopo, quem usa |
| [02 — Arquitetura](02-arquitetura.md) | Camadas, fluxo de uma requisição, patterns |
| [03 — Modelo de dados](03-modelo-de-dados.md) | Tabelas, colunas, constraints |
| [04 — API](04-api.md) | Referência dos endpoints |
| [05 — Ambiente de desenvolvimento](05-ambiente-de-desenvolvimento.md) | Como rodar o projeto do zero |
| [06 — Migrations](06-migrations.md) | Como trabalhar com Alembic sem quebrar nada |
| [07 — Convenções](07-convencoes.md) | Nomenclatura, Git, estilo de código |
| [08 — Integrações externas](08-integracoes.md) | Banco Inter e WhatsApp |
| [Decisões (ADRs)](decisoes/) | **Toda decisão técnica e o porquê dela** |

## Onde fica cada coisa

- **`docs/`** (esta pasta) — documentação viva. Descreve o sistema **como ele
  é hoje**. Quando o código muda, isto muda junto, no mesmo commit.
- **`docs/decisoes/`** — os ADRs. Registram **por que** cada escolha foi
  feita, no momento em que foi feita. Ao contrário do resto, um ADR
  **não é reescrito**: se a decisão mudar, escreve-se um novo ADR que
  substitui o anterior, e o antigo é marcado como `Substituído`. O
  histórico do raciocínio é tão valioso quanto a conclusão.
- **`CRMAndrade.md`** (raiz) — narrativa histórica do projeto: o que
  aconteceu, em ordem cronológica, incluindo troubleshooting e caminhos
  que não deram certo. É um diário, não uma referência.

## Estado atual

Implementado e funcionando:

- CRUD completo de clientes (`/clients`)
- Persistência em PostgreSQL com migrations versionadas via Alembic
- Validação em duas camadas (Pydantic + constraints no banco)
- Tradução de erros de integridade do banco para respostas HTTP corretas

Ainda não implementado: módulo de cobrança (Banco Inter), envio via
WhatsApp, módulo de leads/CRM, autenticação, e o front-end (que hoje é
apenas o template inicial do Next.js).
