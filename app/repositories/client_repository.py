import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.cliente import Cliente


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, client: Cliente) -> Cliente:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get_by_id(self, client_id: uuid.UUID) -> Optional[Cliente]:
        return self.db.query(Cliente).filter(Cliente.id == client_id).first()

    def list_all(self) -> list[Cliente]:
        return self.db.query(Cliente).all()

    def update(self, client: Cliente) -> Cliente:
        self.db.commit()
        self.db.refresh(client)
        return client

    def delete(self, client: Cliente) -> None:
        self.db.delete(client)
        self.db.commit()