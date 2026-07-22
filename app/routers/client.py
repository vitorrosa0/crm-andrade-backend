import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.cliente import Cliente
from app.repositories.client_repository import ClientRepository
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse

router = APIRouter(prefix="/clients", tags=["clients"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ClienteResponse, status_code=201)
def create_client(payload: ClienteCreate, db: Session = Depends(get_db)):
    repository = ClientRepository(db)
    client = Cliente(**payload.model_dump())
    return repository.create(client)


@router.get("/", response_model=list[ClienteResponse])
def list_clients(db: Session = Depends(get_db)):
    repository = ClientRepository(db)
    return repository.list_all()


@router.get("/{client_id}", response_model=ClienteResponse)
def get_client(client_id: uuid.UUID, db: Session = Depends(get_db)):
    repository = ClientRepository(db)
    client = repository.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClienteResponse)
def update_client(client_id: uuid.UUID, payload: ClienteUpdate, db: Session = Depends(get_db)):
    repository = ClientRepository(db)
    client = repository.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(client, field, value)

    return repository.update(client)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: uuid.UUID, db: Session = Depends(get_db)):
    repository = ClientRepository(db)
    client = repository.get_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    repository.delete(client)