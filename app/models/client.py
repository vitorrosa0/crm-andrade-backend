import uuid

from sqlalchemy import Column, String, DateTime, CheckConstraint, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain import PERSON_TYPES

_PERSON_TYPE_LIST = ", ".join(f"'{p}'" for p in PERSON_TYPES)


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

    # passive_deletes="all" impede o SQLAlchemy de tentar anular o client_id
    # das cobranças ao apagar um cliente. Sem isto, o ORM "ajuda" emitindo
    # UPDATE charges SET client_id = NULL, que esbarra no NOT NULL e produz
    # um erro confuso — em vez de deixar o RESTRICT da FK fazer seu trabalho
    # e devolver a recusa correta (409, via app/errors.py).
    charges = relationship("Charge", back_populates="client", passive_deletes="all")

    __table_args__ = (
        # No Postgres, UNIQUE permite múltiplos NULL. Isso é exatamente o
        # comportamento desejado: toda pessoa jurídica tem cpf = NULL, e
        # nenhuma delas colide com as outras.
        UniqueConstraint("cpf", name="uq_clients_cpf"),
        UniqueConstraint("cnpj", name="uq_clients_cnpj"),
        CheckConstraint(
            f"person_type IN ({_PERSON_TYPE_LIST})",
            name="check_person_type_valid"
        ),
        CheckConstraint(
            "(person_type = 'INDIVIDUAL' AND cpf IS NOT NULL AND cnpj IS NULL) OR "
            "(person_type = 'COMPANY' AND cnpj IS NOT NULL AND cpf IS NULL)",
            name="check_document_by_person_type"
        ),
    )
