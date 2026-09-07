# ADR 0003 — Alembic para versionar o schema

**Status:** Aceito
**Data:** 2026-07

## Contexto

O SQLAlchemy oferece `Base.metadata.create_all()`, que cria todas as
tabelas a partir dos models. É uma linha e funciona.

O problema aparece na **segunda** vez. `create_all()` cria o que não
existe, mas **não altera o que já existe**. Adicione uma coluna ao model e
ela simplesmente não aparece no banco — sem erro, sem aviso. O código passa
a esperar uma coluna que não está lá.

A alternativa manual seria alterar o banco por SQL direto. Aí o schema
passa a existir apenas na memória de quem o alterou: não está no
repositório, não passa por code review, e não há como reconstituir o banco
do zero.

## Decisão

**Alembic** para versionar todas as mudanças de schema. Nenhuma alteração
de estrutura é feita por SQL direto.

## Justificativa

**O schema vira código versionado.** Cada mudança é um arquivo no
repositório, com autor, data e mensagem. Aparece no diff, entra no code
review junto com o código que depende dela.

**O banco é reconstituível.** `alembic upgrade head` em um banco vazio
produz exatamente o schema esperado. Isso vale para uma máquina nova, para
o ambiente de homologação e para produção.

**Rollback existe.** Cada migration tem `downgrade`. Uma alteração ruim
pode ser desfeita de forma determinística, em vez de reparada na mão sob
pressão.

**É o par natural do SQLAlchemy.** Mesmo autor, integração direta com o
metadata dos models, e `--autogenerate` que compara model e banco.

**`alembic check`.** Detecta model alterado sem migration correspondente —
o erro mais comum e mais silencioso desse fluxo.

## Consequências

**Positivas**
- Histórico de schema auditável
- Ambientes reproduzíveis
- Rollback possível
- Migração de dados no mesmo lugar que a de schema (`op.execute`)

**Negativas**
- Um passo a mais em toda alteração de model
- **`--autogenerate` não é confiável sozinho.** Ele não detecta
  renomeações e gera `drop` + `create`, que apaga dados. Isso motivou o
  [ADR 0013](0013-migrations-de-rename-a-mao.md)
- Todo model novo precisa ser importado em `alembic/env.py`, ou é ignorado
  silenciosamente
- Conflito de migrations entre branches (múltiplos `head`) é chato de
  resolver — irrelevante hoje, com um desenvolvedor só

## Alternativas consideradas

**`create_all()`** — Descartado: não lida com evolução de schema, que é
justamente o problema.

**SQL manual versionado** (arquivos `.sql` numerados) — Funciona e é
transparente. Descartado por não ter rollback automático, não integrar com
os models e exigir controle manual do que já foi aplicado.

**Ferramenta agnóstica (Flyway, Liquibase)** — Maduras, mas pensadas para o
ecossistema Java. Descartado por adicionar uma dependência externa sem
ganho sobre o Alembic neste contexto.

## Notas de uso

O fluxo completo, as armadilhas e as regras adotadas estão em
[06 — Migrations](../06-migrations.md).
