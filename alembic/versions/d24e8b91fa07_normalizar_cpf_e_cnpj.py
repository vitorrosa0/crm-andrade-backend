"""normalizar cpf e cnpj para apenas digitos

A normalização passou a ser feita na camada de schema (Pydantic), mas isso
só vale para dados que entram a partir de agora. Esta migration alinha as
linhas que já existem.

Por que importa: "111.222.333-44" e "11122233344" são strings diferentes
para a constraint UNIQUE. Sem normalizar, a unicidade de CPF/CNPJ é
burlável apenas mudando a pontuação.

ATENÇÃO: se a normalização revelar documentos duplicados que antes
passavam por terem pontuação diferente, esta migration falha na constraint
UNIQUE — o que é o comportamento correto: são de fato duplicatas. Para
identificá-las antes de aplicar:

    SELECT regexp_replace(cpf, '\D', '', 'g') AS doc, count(*)
    FROM clients WHERE cpf IS NOT NULL
    GROUP BY doc HAVING count(*) > 1;

Revision ID: d24e8b91fa07
Revises: c93a5f17b204
Create Date: 2026-09-05

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd24e8b91fa07'
down_revision: Union[str, Sequence[str], None] = 'c93a5f17b204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # '\D' = qualquer caractere que não seja dígito; 'g' = todas as ocorrências
    op.execute(r"UPDATE clients SET cpf = regexp_replace(cpf, '\D', '', 'g') WHERE cpf IS NOT NULL")
    op.execute(r"UPDATE clients SET cnpj = regexp_replace(cnpj, '\D', '', 'g') WHERE cnpj IS NOT NULL")

    # Se a pontuação era o único conteúdo, o resultado é '' — que violaria a
    # CHECK constraint (que exige IS NULL, não string vazia).
    op.execute("UPDATE clients SET cpf = NULL WHERE cpf = ''")
    op.execute("UPDATE clients SET cnpj = NULL WHERE cnpj = ''")


def downgrade() -> None:
    """Downgrade schema.

    Irreversível por natureza: a pontuação original foi descartada e não há
    como saber qual formato cada linha usava. Não é uma falha — é o efeito
    esperado de uma normalização. O `pass` é deliberado, para que o
    downgrade das migrations seguintes não fique bloqueado.
    """
    pass
