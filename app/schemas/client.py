import re
import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, field_validator, model_validator

CPF_LENGTH = 11
CNPJ_LENGTH = 14

_NON_DIGITS = re.compile(r"\D")


def normalize_document(value: Optional[str]) -> Optional[str]:
    """Reduz um documento à sua forma canônica: apenas dígitos.

    Sem isto, "111.222.333-44" e "11122233344" são strings diferentes — e
    portanto valores diferentes para a constraint UNIQUE do banco. Ou seja:
    seria possível cadastrar o mesmo CPF duas vezes só mudando a pontuação,
    o que anula a garantia de unicidade.

    Retorna None para entrada vazia (ou que só continha pontuação). Isso
    importa: uma string vazia seria gravada como '' e violaria a CHECK
    constraint do banco, que exige `cpf IS NULL` para pessoa jurídica.
    """
    if value is None:
        return None

    digits = _NON_DIGITS.sub("", value)
    return digits or None


class ClientBase(BaseModel):
    name: str
    person_type: Literal["INDIVIDUAL", "COMPANY"]
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    phone: str
    email: Optional[str] = None

    @field_validator("cpf", "cnpj", mode="after")
    @classmethod
    def strip_document_punctuation(cls, value: Optional[str]) -> Optional[str]:
        return normalize_document(value)

    @model_validator(mode="after")
    def validate_document_by_person_type(self) -> "ClientBase":
        # Roda depois do field_validator acima, então cpf/cnpj já chegam
        # aqui normalizados — a checagem de tamanho é sobre dígitos puros.
        if self.person_type == "INDIVIDUAL":
            if not self.cpf:
                raise ValueError("CPF é obrigatório para pessoa física")
            if self.cnpj:
                raise ValueError("CNPJ não deve ser informado para pessoa física")
            if len(self.cpf) != CPF_LENGTH:
                raise ValueError(f"CPF deve ter {CPF_LENGTH} dígitos")
        elif self.person_type == "COMPANY":
            if not self.cnpj:
                raise ValueError("CNPJ é obrigatório para pessoa jurídica")
            if self.cpf:
                raise ValueError("CPF não deve ser informado para pessoa jurídica")
            if len(self.cnpj) != CNPJ_LENGTH:
                raise ValueError(f"CNPJ deve ter {CNPJ_LENGTH} dígitos")
        return self


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    # person_type, cpf e cnpj não entram aqui de propósito:
    # trocar o documento de um cliente é uma operação de negócio distinta,
    # que merece rota e regra próprias no futuro.


class ClientResponse(ClientBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
