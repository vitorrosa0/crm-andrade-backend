import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.client import Client


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, client: Client) -> Client:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()

    def list_all(self) -> list[Client]:
        return self.db.query(Client).all()

    def update(self, client: Client) -> Client:
        self.db.commit()
        self.db.refresh(client)
        return client

    def delete(self, client: Client) -> None:
        self.db.delete(client)
        self.db.commit()
