import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.domain import CHARGE_STATUS_PENDING
from app.models.charge import Charge


class ChargeRepository:
    """Acesso a dados de cobrança.

    Como o ClientRepository, recebe a sessão pelo construtor — quem controla
    a requisição controla a transação. Isso é o que vai permitir, no módulo
    de emissão, gravar a cobrança e atualizar o cliente atomicamente.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, charge: Charge) -> Charge:
        self.db.add(charge)
        self.db.commit()
        self.db.refresh(charge)
        return charge

    def get_by_id(self, charge_id: uuid.UUID) -> Optional[Charge]:
        return self.db.query(Charge).filter(Charge.id == charge_id).first()

    def get_by_external_id(self, external_id: str) -> Optional[Charge]:
        """Busca pelo identificador da instituição financeira.

        É por aqui que um webhook de pagamento encontra a cobrança local:
        o banco só conhece o id dele.
        """
        return (
            self.db.query(Charge)
            .filter(Charge.external_id == external_id)
            .first()
        )

    def list_by_client(self, client_id: uuid.UUID) -> list[Charge]:
        return (
            self.db.query(Charge)
            .filter(Charge.client_id == client_id)
            .order_by(Charge.due_date.desc())
            .all()
        )

    def list_due_on(self, due_date: date, status: str = CHARGE_STATUS_PENDING) -> list[Charge]:
        """Cobranças que vencem em uma data, ainda no status informado.

        É a consulta da rotina diária de envio: "o que vence daqui a 5 dias
        e continua pendente?". O índice ix_charges_status_due_date existe
        exatamente para ela.
        """
        return (
            self.db.query(Charge)
            .filter(Charge.status == status, Charge.due_date == due_date)
            .all()
        )

    def list_pending_before(self, reference: date) -> list[Charge]:
        """Cobranças pendentes já vencidas — candidatas a virar OVERDUE."""
        return (
            self.db.query(Charge)
            .filter(
                Charge.status == CHARGE_STATUS_PENDING,
                Charge.due_date < reference,
            )
            .all()
        )

    def save(self, charge: Charge) -> Charge:
        self.db.commit()
        self.db.refresh(charge)
        return charge
