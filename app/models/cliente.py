import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False)
    tipo_pessoa = Column(String, nullable=False)  # "FISICA" ou "JURIDICA"
    cpf = Column(String, nullable=True)
    cnpj = Column(String, nullable=True)
    telefone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint(
            "tipo_pessoa IN ('FISICA', 'JURIDICA')",
            name="check_tipo_pessoa_valido"
        ),
        CheckConstraint(
            "(tipo_pessoa = 'FISICA' AND cpf IS NOT NULL AND cnpj IS NULL) OR "
            "(tipo_pessoa = 'JURIDICA' AND cnpj IS NOT NULL AND cpf IS NULL)",
            name="check_documento_por_tipo_pessoa"
        ),
    )