# ADR 0008 — Validar em duas camadas (Pydantic + banco)

**Status:** Aceito
**Data:** 2026-07

## Contexto

A regra "pessoa física tem CPF e não tem CNPJ; jurídica, o inverso" está
escrita **duas vezes**.

No schema Pydantic:

```python
@model_validator(mode="after")
def validate_document_by_person_type(self):
    if self.person_type == "INDIVIDUAL":
        if not self.cpf:
            raise ValueError("CPF é obrigatório para pessoa física")
    ...
```

E no banco:

```python
CheckConstraint(
    "(person_type = 'INDIVIDUAL' AND cpf IS NOT NULL AND cnpj IS NULL) OR "
    "(person_type = 'COMPANY' AND cnpj IS NOT NULL AND cpf IS NULL)",
    name="check_document_by_person_type"
)
```

Isso é duplicação, e duplicação normalmente é defeito: duas cópias podem
divergir.

## Decisão

**Manter as duas**, deliberadamente, com papéis distintos.

- **Pydantic** — experiência de quem usa a API. Rejeita cedo, com mensagem
  clara, em português, apontando o campo errado.
- **Banco** — garantia real. Vale para qualquer escrita, venha de onde vier.

## Justificativa

**Elas protegem contra coisas diferentes.**

O Pydantic só vê o que passa pela API. Não protege contra:

- Um script de importação usando o model direto
- Uma correção manual via DBeaver ou psql
- Um bug num endpoint futuro que monte o objeto de outro jeito
- A rotina agendada de cobrança, que não passa por HTTP

A constraint do banco protege contra tudo isso, porque está na camada mais
profunda: **não existe caminho para o dado que não passe por ela.**

**Só a constraint seria ruim de usar.** Sem o Pydantic, uma pessoa física
sem CPF só falharia no INSERT, retornando um erro genérico de constraint em
vez de "o campo cpf é obrigatório". Erro tardio e mensagem pobre.

**Só o Pydantic seria inseguro.** Validação em aplicação é uma **política**;
constraint em banco é uma **garantia**. Para dado financeiro e pessoal, a
diferença importa.

Isto é *defense in depth*: camadas independentes, cada uma suficiente
sozinha, nenhuma confiando na outra.

## Consequências

**Positivas**

- Erro rápido e legível pela API
- Integridade garantida por qualquer caminho de escrita
- Nenhum dado inválido consegue entrar no banco

**Negativas**

- **Duplicação real.** Se a regra mudar, precisa mudar em dois lugares. Um
  esquecimento cria divergência silenciosa
- Mais código para a mesma regra
- **A constraint do banco raramente dispara em produção**, porque o Pydantic
  barra antes. Isso significa que esse caminho fica pouco exercitado — foi
  preciso um teste que fala direto com o model, sem passar pela API, para
  verificar que funciona

**Sobre o último ponto:** a divergência entre as duas camadas é justamente o
cenário em que a constraint salva. Ela ser "código morto" no dia a dia é o
comportamento esperado — como um extintor.

## Mitigação da duplicação

Se a regra ficar complexa, extrair para uma função única que gere tanto a
validação Python quanto a expressão SQL. Não foi feito: com uma regra, a
abstração custaria mais do que a duplicação.

## Alternativas consideradas

**Só Pydantic** — Menos código, sem duplicação. Descartado: qualquer escrita
fora da API contorna a regra.

**Só constraint no banco** — Fonte única de verdade. Descartado pela péssima
experiência de erro e pela validação tardia.

**Regra em uma camada de serviço** — Centralizaria em um lugar do código.
Descartado por ainda ser aplicação: continua sem proteger contra escrita
direta no banco. E hoje não há camada de serviço.
