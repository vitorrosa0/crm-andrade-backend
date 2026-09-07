# Decisões de Arquitetura (ADRs)

## O que é um ADR

Um **Architecture Decision Record** é um documento curto que registra uma
decisão técnica **no momento em que ela é tomada**, junto com o contexto que
a motivou e as alternativas que foram descartadas.

O problema que ele resolve: seis meses depois, o código mostra *o que* foi
feito, mas não *por quê*. Sem o registro, ou se repete a análise do zero, ou
— pior — se desfaz uma decisão correta sem perceber qual problema ela
resolvia.

## Regras

1. **Um ADR por decisão.** Curto e focado.
2. **ADR aceito não se edita.** Se a decisão mudar, escreve-se um novo ADR
   que substitui o anterior, e o antigo é marcado como `Substituído`. O
   histórico do raciocínio é parte do valor.
3. **Registre as alternativas.** "Por que não a outra opção" costuma ser
   mais útil do que a escolha em si.
4. **Registre as consequências negativas.** Toda decisão tem custo. Um ADR
   que só lista vantagens não foi honesto — foi propaganda.

## Status possíveis

| Status | Significado |
|---|---|
| `Aceito` | Em vigor |
| `Substituído por ADR XXXX` | Não vale mais; ver o substituto |
| `Proposto` | Em discussão |
| `Descartado` | Considerado e rejeitado |

## Índice

### Stack e infraestrutura
| # | Decisão | Status |
|---|---|---|
| [0001](0001-backend-em-python-fastapi.md) | Backend em Python com FastAPI | Aceito |
| [0002](0002-postgresql-como-banco.md) | PostgreSQL como banco de dados | Aceito |
| [0003](0003-alembic-para-migrations.md) | Alembic para versionar o schema | Aceito |

### Arquitetura e código
| # | Decisão | Status |
|---|---|---|
| [0004](0004-repository-pattern.md) | Repository Pattern com sessão injetada | Aceito |
| [0008](0008-validacao-em-duas-camadas.md) | Validar em duas camadas (Pydantic + banco) | Aceito |
| [0009](0009-integridade-garantida-pelo-banco.md) | Integridade garantida pelo banco, traduzida para HTTP | Aceito |
| [0012](0012-gateway-de-cobranca-abstrato.md) | Gateway de cobrança abstrato | Proposto |

### Modelagem de dados
| # | Decisão | Status |
|---|---|---|
| [0005](0005-uuid-como-chave-primaria.md) | UUID como chave primária | Aceito |
| [0006](0006-sem-enum-para-person-type.md) | String + CHECK em vez de ENUM | Aceito |
| [0013](0013-migrations-de-rename-a-mao.md) | Migrations de renomeação escritas à mão | Aceito |
| [0014](0014-normalizacao-de-documentos.md) | Normalizar CPF e CNPJ na entrada | Aceito |

### Convenções
| # | Decisão | Status |
|---|---|---|
| [0007](0007-nomenclatura-em-ingles.md) | Nomenclatura de código em inglês | Aceito |

### Produto e integrações
| # | Decisão | Status |
|---|---|---|
| [0010](0010-sem-ia-generativa-livre.md) | Sem IA generativa livre no atendimento | Aceito |
| [0011](0011-whatsapp-api-oficial.md) | Apenas a API oficial do WhatsApp | Aceito |
