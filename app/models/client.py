import uuid

from sqlalchemy import Column, String, DateTime, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    person_type = Column(String, nullable=False)  # "INDIVIDUAL" ou "COMPANY"
    cpf = Column(String, nullable=True)
    cnpj = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # No Postgres, UNIQUE permite múltiplos NULL. Isso é exatamente o
        # comportamento desejado: toda pessoa jurídica tem cpf = NULL, e
        # nenhuma delas colide com as outras.
        UniqueConstraint("cpf", name="uq_clients_cpf"),
        UniqueConstraint("cnpj", name="uq_clients_cnpj"),
        CheckConstraint(
            "person_type IN ('INDIVIDUAL', 'COMPANY')",
            name="check_person_type_valid"
        ),
        CheckConstraint(
            "(person_type = 'INDIVIDUAL' AND cpf IS NOT NULL AND cnpj IS NULL) OR "
            "(person_type = 'COMPANY' AND cnpj IS NOT NULL AND cpf IS NULL)",
            name="check_document_by_person_type"
        ),
    )
