"""renomear entidade cliente para ingles

Renomeia a tabela `clientes` e suas colunas para inglês, alinhando o schema
à convenção de nomenclatura do projeto. Usa ALTER ... RENAME (e não
drop/create) para preservar os dados já existentes.

Aproveita para quitar o débito técnico do `criado_em`: a coluna passa a ter
`server_default = now()` e `NOT NULL`, de modo que o valor seja garantido
pelo próprio Postgres — e não apenas pelo SQLAlchemy.

Revision ID: b7c1d4e28f30
Revises: ec6f5bd69c7c
Create Date: 2026-09-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c1d4e28f30'
down_revision: Union[str, Sequence[str], None] = 'ec6f5bd69c7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. As check constraints referenciam as colunas antigas e os valores
    #    'FISICA'/'JURIDICA'. Removemos antes de mexer no resto.
    op.drop_constraint('check_tipo_pessoa_valido', 'clientes', type_='check')
    op.drop_constraint('check_documento_por_tipo_pessoa', 'clientes', type_='check')

    # 2. Tabela e colunas
    op.rename_table('clientes', 'clients')
    op.alter_column('clients', 'nome', new_column_name='name')
    op.alter_column('clients', 'tipo_pessoa', new_column_name='person_type')
    op.alter_column('clients', 'telefone', new_column_name='phone')
    op.alter_column('clients', 'criado_em', new_column_name='created_at')

    # 3. Dados existentes: os valores do domínio também passam para inglês
    op.execute("UPDATE clients SET person_type = 'INDIVIDUAL' WHERE person_type = 'FISICA'")
    op.execute("UPDATE clients SET person_type = 'COMPANY' WHERE person_type = 'JURIDICA'")

    # 4. created_at: preenche as linhas antigas antes de exigir NOT NULL
    op.execute("UPDATE clients SET created_at = now() WHERE created_at IS NULL")
    op.alter_column(
        'clients',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('now()'),
    )

    # 5. Constraints recriadas com os nomes e valores novos
    op.create_check_constraint(
        'check_person_type_valid',
        'clients',
        "person_type IN ('INDIVIDUAL', 'COMPANY')",
    )
    op.create_check_constraint(
        'check_document_by_person_type',
        'clients',
        "(person_type = 'INDIVIDUAL' AND cpf IS NOT NULL AND cnpj IS NULL) OR "
        "(person_type = 'COMPANY' AND cnpj IS NOT NULL AND cpf IS NULL)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('check_person_type_valid', 'clients', type_='check')
    op.drop_constraint('check_document_by_person_type', 'clients', type_='check')

    op.alter_column(
        'clients',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
    )

    op.execute("UPDATE clients SET person_type = 'FISICA' WHERE person_type = 'INDIVIDUAL'")
    op.execute("UPDATE clients SET person_type = 'JURIDICA' WHERE person_type = 'COMPANY'")

    op.alter_column('clients', 'created_at', new_column_name='criado_em')
    op.alter_column('clients', 'phone', new_column_name='telefone')
    op.alter_column('clients', 'person_type', new_column_name='tipo_pessoa')
    op.alter_column('clients', 'name', new_column_name='nome')
    op.rename_table('clients', 'clientes')

    op.create_check_constraint(
        'check_tipo_pessoa_valido',
        'clientes',
        "tipo_pessoa IN ('FISICA', 'JURIDICA')",
    )
    op.create_check_constraint(
        'check_documento_por_tipo_pessoa',
        'clientes',
        "(tipo_pessoa = 'FISICA' AND cpf IS NOT NULL AND cnpj IS NULL) OR "
        "(tipo_pessoa = 'JURIDICA' AND cnpj IS NOT NULL AND cpf IS NULL)",
    )
