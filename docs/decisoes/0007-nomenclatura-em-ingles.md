# ADR 0007 — Nomenclatura de código em inglês

**Status:** Aceito
**Data:** 2026-07 (convenção) / 2026-09-05 (dívida quitada)

## Contexto

O projeto começou com nomes em português: model `Cliente`, tabela
`clientes`, colunas `nome`, `tipo_pessoa`, `telefone`, `criado_em`, schemas
`ClienteCreate`/`ClienteUpdate`/`ClienteResponse`.

Isso gerou um híbrido desconfortável de imediato:

```python
class ClientRepository:          # inglês
    def get_by_id(self, ...):    # inglês
        return self.db.query(Cliente)  # português
```

O router já estava em `/clients`, retornando objetos `Cliente`.

## Decisão

**Todo nome de código é em inglês** — arquivos, classes, funções, variáveis,
tabelas, colunas, constraints.

**Todo texto voltado ao usuário final é em português** — mensagens de
validação, mensagens de erro de constraint, textos de interface.

Comentários e documentação em português, por serem dirigidos a quem mantém.

### Exceção deliberada: `cpf` e `cnpj`

Permanecem como estão. São **nomes próprios do domínio brasileiro**, não
palavras a traduzir. `tax_id` para ambos perderia exatamente a distinção
que as constraints precisam garantir, e nenhum outro par de termos em
inglês representa esses dois documentos.

## Justificativa

**Consistência interna.** A alternativa real não era "tudo em português" —
era o híbrido, que já existia e já confundia. Metade das bibliotecas
(`query`, `filter`, `Column`, `String`) impõe inglês de qualquer forma.

**Convenção do ecossistema.** SQLAlchemy, FastAPI, Pydantic e o próprio SQL
são em inglês. Nomes de domínio em inglês fluem no meio disso sem costura
visível.

**Portabilidade.** Se outro desenvolvedor entrar — e a intenção declarada é
eventualmente substituir o desenvolvedor anterior — código em inglês é
universalmente legível. Código em português exclui quem não fala português.

**Acentuação e SQL.** `criado_em` não tem acento, mas `endereço` ou
`observação` teriam. Acento em identificador SQL exige aspas duplas em toda
referência, ou se aceita perder o acento e escrever errado de propósito.
Inglês evita a escolha.

## Consequências

**Positivas**
- Um idioma só no código
- Alinhado às bibliotecas e ao SQL
- Sem problema de acentuação em identificadores
- Legível por qualquer desenvolvedor

**Negativas**
- **Custou uma migration de renomeação** (`b7c1d4e28f30`), com risco real
  de perda de dados se feita de forma descuidada — ver
  [ADR 0013](0013-migrations-de-rename-a-mao.md)
- Tradução de termos jurídicos brasileiros nem sempre é óbvia. Já apareceu
  com `cpf`/`cnpj`, e vai voltar em conceitos como "honorários",
  "parcelamento", "inadimplência"
- Distância entre a linguagem do código e a linguagem do cliente, que fala
  em português. Um custo de tradução mental permanente

## Quando a dívida foi quitada

Em **2026-09-05**, na migration `b7c1d4e28f30`, antes de qualquer código
novo ser escrito. O raciocínio: o custo de renomear cresce com a quantidade
de código, e o módulo de cobrança estava prestes a dobrar o tamanho do
projeto. Renomear uma entidade é barato; renomear cinco não é.

Renomeações realizadas:

| Antes | Depois |
|---|---|
| `Cliente` | `Client` |
| `clientes` (tabela) | `clients` |
| `nome` | `name` |
| `tipo_pessoa` | `person_type` |
| `telefone` | `phone` |
| `criado_em` | `created_at` |
| `'FISICA'` / `'JURIDICA'` | `'INDIVIDUAL'` / `'COMPANY'` |
| `ClienteCreate` etc. | `ClientCreate` etc. |

Os **valores** também foram traduzidos, e não só os nomes de coluna. Isso
muda o contrato da API, mas o custo era zero: o front-end ainda não
consumia o endpoint. Adiar teria tornado a mudança cara.
