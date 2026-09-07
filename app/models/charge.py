import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain import CHARGE_STATUS_PENDING, CHARGE_STATUSES

_STATUS_LIST = ", ".join(f"'{s}'" for s in CHARGE_STATUSES)


class Charge(Base):
    __tablename__ = "charges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # RESTRICT: o banco recusa apagar um cliente que tenha cobranças.
    # Histórico financeiro não pode sumir junto com o cadastro — e o
    # handler de erros já traduz essa recusa em 409, em vez de 500.
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT", name="fk_charges_client_id"),
        nullable=False,
    )

    # Numeric, nunca Float. Float é binário e não representa exatamente
    # valores decimais — 0.1 + 0.2 != 0.3. Em dinheiro, esse erro acumula
    # e vira divergência de centavos no fechamento.
    amount = Column(Numeric(10, 2), nullable=False)

    due_date = Column(Date, nullable=False)
    description = Column(String, nullable=True)

    # Ciclo de vida do PAGAMENTO apenas. Emissão e notificação são fatos
    # independentes, registrados nas colunas de timestamp abaixo.
    status = Column(String, nullable=False, default=CHARGE_STATUS_PENDING)

    # Identificador da cobrança na instituição financeira. NULL enquanto o
    # boleto ainda não foi emitido — é o que distingue "cobrança criada no
    # sistema" de "boleto existente no banco".
    external_id = Column(String, nullable=True)

    payment_url = Column(String, nullable=True)
    digitable_line = Column(String, nullable=True)
    pix_copy_paste = Column(String, nullable=True)

    # Três fatos ortogonais, cada um com seu próprio momento:
    issued_at = Column(DateTime(timezone=True), nullable=True)    # emitida no banco
    notified_at = Column(DateTime(timezone=True), nullable=True)  # enviada no WhatsApp
    paid_at = Column(DateTime(timezone=True), nullable=True)      # pagamento confirmado

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    client = relationship("Client", back_populates="charges")

    __table_args__ = (
        # O Postgres NÃO cria índice automaticamente para chave estrangeira.
        # Sem este, listar as cobranças de um cliente vira varredura da tabela.
        Index("ix_charges_client_id", "client_id"),
        # A rotina diária pergunta "o que vence daqui a 5 dias e ainda não
        # foi pago?". O índice composto atende exatamente essa consulta.
        Index("ix_charges_status_due_date", "status", "due_date"),
        UniqueConstraint("external_id", name="uq_charges_external_id"),
        CheckConstraint(
            f"status IN ({_STATUS_LIST})",
            name="check_charge_status_valid",
        ),
        CheckConstraint(
            "amount > 0",
            name="check_charge_amount_positive",
        ),
        # Coerência entre o status e o fato que ele afirma: uma cobrança
        # marcada como paga precisa dizer quando foi paga, e nenhuma outra
        # pode ter data de pagamento.
        CheckConstraint(
            "(status = 'PAID' AND paid_at IS NOT NULL) OR "
            "(status <> 'PAID' AND paid_at IS NULL)",
            name="check_charge_paid_at_matches_status",
        ),
        # Se tem identificador no banco, foi emitida — e vice-versa.
        CheckConstraint(
            "(external_id IS NULL AND issued_at IS NULL) OR "
            "(external_id IS NOT NULL AND issued_at IS NOT NULL)",
            name="check_charge_issued_consistency",
        ),
    )
