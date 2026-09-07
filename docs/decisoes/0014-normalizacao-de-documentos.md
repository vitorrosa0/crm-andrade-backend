# ADR 0014 — Normalizar CPF e CNPJ na entrada

**Status:** Aceito
**Data:** 2026-09-05

## Contexto

O [ADR 0009](0009-integridade-garantida-pelo-banco.md) adicionou constraints
UNIQUE em `cpf` e `cnpj` para impedir cadastro duplicado.

A garantia era mais fraca do que parecia. Para o banco, `"111.222.333-44"` e
`"11122233344"` são strings diferentes — logo, valores diferentes para a
constraint UNIQUE. **Bastava mudar a pontuação para cadastrar o mesmo CPF
duas vezes**, o que anulava na prática a proteção recém-criada.

O problema não é hipotético: quem digita um CPF num formulário formata de
um jeito, e uma importação de planilha traz de outro.

## Decisão

Documentos são **normalizados na entrada da API**, no schema Pydantic:
tudo que não é dígito é removido antes de qualquer outra validação.

```python
@field_validator("cpf", "cnpj", mode="after")
@classmethod
def strip_document_punctuation(cls, value):
    return normalize_document(value)
```

O banco passa a guardar **uma única forma canônica**: apenas dígitos.

Duas regras acompanham a decisão:

**1. Tamanho é validado após a normalização.** CPF precisa resultar em 11
dígitos, CNPJ em 14. Antes de normalizar, contar caracteres não significava
nada — `"111.222.333-44"` tem 14.

**2. Resultado vazio vira `None`, não string vazia.** Se a entrada só tinha
pontuação (ou era `""`), o resultado é `None`. Isso é essencial: `""` seria
gravado como string vazia e violaria a CHECK constraint do banco, que exige
`cpf IS NULL` para pessoa jurídica.

A migration `d24e8b91fa07` normalizou as linhas já existentes.

## Justificativa

**Sem isto, a constraint UNIQUE é decorativa.** Esta é a razão principal —
a decisão do ADR 0009 dependia desta para funcionar de verdade.

**Normalizar na borda, não no uso.** O documento é convertido uma vez, ao
entrar, e todo o resto do sistema trabalha com a forma canônica. A
alternativa — normalizar em cada comparação — significaria lembrar de fazer
isso em toda query, toda regra e toda integração futura. Um esquecimento
reintroduz o bug.

**Apenas dígitos é a forma certa para armazenar.** É o formato que a API do
Banco Inter espera, o que ocupa menos espaço e o único que não tem variantes
("`.`" vs "`/`" vs espaço). Formatação é assunto de **apresentação** — o
front-end formata na exibição, o banco guarda o dado.

**Aceitar pontuação continua sendo bom para quem usa.** A normalização é
permissiva na entrada e estrita no armazenamento. Quem consome a API pode
mandar o CPF como quiser; o sistema resolve.

## Consequências

**Positivas**

- A constraint UNIQUE passa a valer de fato
- Uma forma canônica só no banco — comparações e buscas são confiáveis
- Formato já pronto para a integração com o Inter
- Entrada tolerante: a API aceita qualquer formatação usual

**Negativas**

- **A formatação original é descartada.** Se alguém quisesse saber como o
  documento foi digitado, não dá mais. Irrelevante aqui, mas é uma perda de
  informação real — e por isso o `downgrade` da migration é `pass`: não há
  como reverter
- **O front-end precisa formatar na exibição.** A API devolve
  `"11122233344"`, e mostrar isso cru para um usuário é ruim
- **Validação de tamanho não é validação de documento.** `"11111111111"`
  tem 11 dígitos e passa, embora seja um CPF matematicamente inválido. Ver
  abaixo

## O que ficou de fora: dígito verificador

CPF e CNPJ têm dígitos verificadores calculáveis. Validá-los rejeitaria
sequências como `"11111111111"` ou documentos digitados errado.

**Não foi implementado**, deliberadamente, para manter a mudança focada. É
o próximo passo natural, e o débito está registrado em
[03 — Modelo de dados](../03-modelo-de-dados.md).

Vale registrar o argumento contrário, porque existe: alguns sistemas evitam
validar DV para não travar cadastro em casos de borda (documentos
estrangeiros, registros antigos, CNPJ alfanumérico — formato que passou a
ser emitido a partir de 2026). Se isso se mostrar um problema real para o
escritório, a validação de DV pode ser um aviso em vez de um bloqueio.

## Alternativas consideradas

**Normalizar só na comparação** — Guardar como veio e comparar sem
pontuação, via índice funcional
(`CREATE UNIQUE INDEX ON clients (regexp_replace(cpf, '\D', '', 'g'))`).
Funcionaria e preservaria o formato original. Descartado por deixar o dado
inconsistente no banco e exigir que toda query futura lembre de normalizar.

**Normalizar no model SQLAlchemy** (via listener de evento) — Cobriria
também escrita que não passa pela API. Descartado por ora: esconde a
transformação num lugar pouco óbvio, e a validação de formato já vive no
schema, junto com as demais regras de entrada. Vale reconsiderar quando
houver importação em massa.

**Guardar formatado** — Descartado: cria variantes do mesmo dado, é o
formato errado para a integração com o Inter, e mistura apresentação com
armazenamento.
