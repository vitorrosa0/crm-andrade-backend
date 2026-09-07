# ADR 0005 — UUID como chave primária

**Status:** Aceito
**Data:** 2026-07

## Contexto

O padrão mais comum seria um inteiro auto-incremental (`SERIAL`/`BIGSERIAL`).
É compacto, rápido de indexar e simples.

Mas esse id vai aparecer nas URLs da API: `/clients/1`, `/clients/2`.
E os dados por trás são **dados pessoais** — nome, CPF, telefone, e-mail —
de clientes de um escritório de advocacia.

## Decisão

Chave primária **UUID v4**, gerada na aplicação:

```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

## Justificativa

**Não é enumerável.** Com id sequencial, quem obtiver acesso a um endpoint
consegue percorrer a base inteira incrementando o número. Com UUID v4, o
espaço é grande demais para adivinhação.

> Isto **não substitui autenticação** — que ainda não existe e é o
> bloqueador real para deploy. É uma camada a mais, não a única.

**Não vaza volume de negócio.** Um id sequencial conta quantos clientes o
escritório tem, e quantos entraram entre duas datas. Para um escritório de
advocacia, isso é informação comercial que não precisa estar em uma URL.

**Id disponível antes do INSERT.** Gerado em Python, o objeto já tem `id`
antes de tocar o banco. Isso simplifica montar relacionamentos em memória —
criar uma cobrança já apontando para o cliente, e gravar tudo de uma vez.

**Sem colisão entre ambientes.** Dados de desenvolvimento, homologação e
produção podem coexistir sem conflito de chave. Útil para importar um caso
real e investigar um bug.

**LGPD.** Reduzir a exposição de dados pessoais é princípio da lei. Um
identificador não-enumerável é minimização de risco na prática.

## Consequências

**Positivas**
- Enumeração inviável
- Volume de negócio não exposto
- Id conhecido antes da persistência
- Ambientes com dados intercambiáveis

**Negativas**
- **16 bytes contra 4 ou 8.** Índices maiores e ligeiramente mais lentos.
  Irrelevante na escala de um escritório (dezenas a centenas de clientes)
- **UUID v4 é aleatório**, o que fragmenta o índice B-tree na inserção
  (ao contrário de um sequencial, que sempre insere no fim). Só importaria
  com volume alto de escrita
- **Ilegível para humanos.** Comparar dois UUIDs no DBeaver é desagradável.
  Suportar um id curto para uso interno é possível, mas não foi feito
- URLs longas

**Sobre o desempenho:** existe UUID v7, que é ordenável por tempo e resolve
a fragmentação. Não foi adotado por não haver problema real a resolver — e
adicionar dependência para otimizar o que não dói é otimização prematura.

## Alternativas consideradas

**Inteiro sequencial** — Menor e mais rápido. Descartado pela enumerabilidade
e pelo vazamento de volume.

**Sequencial + slug público** (id interno numérico, identificador aleatório
exposto) — Junta os dois benefícios. Descartado por exigir duas colunas,
dois índices e disciplina permanente para nunca vazar o interno. Complexidade
não justificada nesta escala.

**UUID v7** — Ordenável por tempo, melhor para índices. Descartado por
exigir dependência extra em Python 3.14 e resolver um problema que o
projeto não tem.
