import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.domain import CHARGE_STATUSES

# O Inter não emite cobrança abaixo deste valor. É regra da instituição,
# não do domínio — por isso vive aqui, na borda, e não como CHECK no banco
# (que só garante amount > 0). Trocar de banco muda este número; não deve
# exigir migration.
MINIMUM_AMOUNT = Decimal("2.50")


class ChargeCreate(BaseModel):
    client_id: uuid.UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    due_date: date
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_minimum_amount(cls, value: Decimal) -> Decimal:
        if value < MINIMUM_AMOUNT:
            raise ValueError(
                f"Valor mínimo para emissão de cobrança é R$ {MINIMUM_AMOUNT}"
            )
        return value

    @field_validator("due_date")
    @classmethod
    def validate_due_date_not_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("A data de vencimento não pode estar no passado")
        return value


class ChargeResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    amount: Decimal
    due_date: date
    description: Optional[str]
    status: str

    external_id: Optional[str]
    payment_url: Optional[str]
    digitable_line: Optional[str]
    pix_copy_paste: Optional[str]

    issued_at: Optional[datetime]
    notified_at: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


__all__ = ["ChargeCreate", "ChargeResponse", "MINIMUM_AMOUNT", "CHARGE_STATUSES"]
