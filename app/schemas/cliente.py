import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, field_validator, model_validator


class ClienteBase(BaseModel):
    nome: str
    tipo_pessoa: Literal["FISICA", "JURIDICA"]
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: str
    email: Optional[str] = None

    @model_validator(mode="after")
    def validar_documento_por_tipo(self) -> "ClienteBase":
        if self.tipo_pessoa == "FISICA":
            if not self.cpf:
                raise ValueError("CPF é obrigatório para pessoa física")
            if self.cnpj:
                raise ValueError("CNPJ não deve ser informado para pessoa física")
        elif self.tipo_pessoa == "JURIDICA":
            if not self.cnpj:
                raise ValueError("CNPJ é obrigatório para pessoa jurídica")
            if self.cpf:
                raise ValueError("CPF não deve ser informado para pessoa jurídica")
        return self


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    # tipo_pessoa, cpf e cnpj não entram aqui de propósito — ver explicação abaixo


class ClienteResponse(ClienteBase):
    id: uuid.UUID
    criado_em: datetime

    model_config = {"from_attributes": True}