"""unicidade de cpf e cnpj

Impede que o mesmo cliente seja cadastrado duas vezes.

No Postgres, uma constraint UNIQUE permite múltiplos NULL (dois NULL não
são considerados iguais). Isso é justamente o que queremos: toda pessoa
jurídica tem `cpf IS NULL` e nenhuma delas colide com as outras.

ATENÇÃO ao aplicar em um banco que já tem dados: se existirem CPFs ou
CNPJs repetidos, esta migration falha. Para conferir antes:

    SELECT cpf, count(*) FROM clients
    WHERE cpf IS NOT NULL GROUP BY cpf HAVING count(*) > 1;

Revision ID: c93a5f17b204
Revises: b7c1d4e28f30
Create Date: 2026-09-05

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c93a5f17b204'
down_revision: Union[str, Sequence[str], None] = 'b7c1d4e28f30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_clients_cpf', 'clients', ['cpf'])
    op.create_unique_constraint('uq_clients_cnpj', 'clients', ['cnpj'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_clients_cnpj', 'clients', type_='unique')
    op.drop_constraint('uq_clients_cpf', 'clients', type_='unique')
