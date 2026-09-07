# ADR 0002 — PostgreSQL como banco de dados

**Status:** Aceito
**Data:** 2026-07

## Contexto

O domínio do sistema é fortemente relacional:

```
cliente ──< cobranças ──< tentativas de envio
   └──< leads
```

Um cliente tem várias cobranças; cada cobrança tem histórico de envio e de
status. As consultas do painel são naturalmente relacionais: "cobranças
vencidas do cliente X", "quanto foi recebido neste mês", "leads sem
resposta há mais de 3 dias".

Além disso, trata-se de **dado financeiro**. Um boleto emitido duas vezes,
ou um pagamento registrado errado, é um problema com o cliente do
escritório — não um bug qualquer.

## Decisão

**PostgreSQL**, tanto em desenvolvimento (local) quanto em produção
(Supabase).

## Justificativa

**O dado é relacional de verdade.** Não é um caso onde se force um modelo
relacional sobre dados que não pedem — as entidades têm relações reais e as
consultas as atravessam.

**Garantias de integridade no próprio banco.** CHECK constraints, UNIQUE,
FOREIGN KEY e transações ACID. Para dado financeiro, ter o banco recusando
estado inválido — independentemente de qual código tentou gravar — é a
diferença entre "provavelmente correto" e "garantidamente correto". Esse
princípio virou explícito no [ADR 0009](0009-integridade-garantida-pelo-banco.md).

**Tipos adequados.** `NUMERIC` para dinheiro (sem erro de arredondamento
binário, ao contrário de `FLOAT`), `TIMESTAMPTZ` para vencimento com fuso,
`UUID` nativo, e `JSONB` para guardar respostas cruas de API quando for
útil auditar.

**Free tier no Supabase.** Atende a restrição de custo zero e ainda oferece
autenticação e storage prontos, caso venham a ser necessários.

**Mesmo banco em dev e produção.** Elimina toda uma classe de bugs do tipo
"funciona na minha máquina": diferenças de tipo, de comportamento com NULL,
de sintaxe.

## Consequências

**Positivas**
- Integridade garantida na camada mais profunda
- Migrations expressivas (Alembic com dialeto Postgres)
- Paridade dev/produção
- Espaço de sobra para crescer (índices, views, full-text search)

**Negativas**
- Exige um Postgres rodando localmente — setup mais pesado que SQLite, e
  de fato custou troubleshooting (ver [05 — Ambiente](../05-ambiente-de-desenvolvimento.md))
- Free tier do Supabase tem limites (pausa por inatividade, cota de
  armazenamento) que precisarão ser observados
- Um serviço a mais para operar e monitorar

## Alternativas consideradas

**SQLite** — Zero configuração, arquivo único, ótimo para desenvolvimento.
Descartado por não servir em produção com múltiplas conexões, ter tipagem
fraca e não suportar bem escrita concorrente. Usá-lo só em dev criaria
divergência com produção, exatamente o que se queria evitar.

**MySQL/MariaDB** — Perfeitamente capaz. Descartado por preferência:
Postgres tem tipos mais ricos, CHECK constraints com suporte mais sólido
historicamente, e melhor free tier disponível (Supabase).

**MongoDB** — Descartado sem hesitação. Dado financeiro relacional em banco
de documentos significa reimplementar na aplicação as garantias que um
banco relacional dá de graça.
