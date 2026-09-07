from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError

from app.errors import integrity_error_handler
from app.routers import client

app = FastAPI(title="CRM Andrade")

# Registrado uma única vez, no topo: qualquer rota — atual ou futura — que
# provoque uma violação de integridade no banco passa a responder um 4xx
# com mensagem útil, em vez de 500.
app.add_exception_handler(IntegrityError, integrity_error_handler)

app.include_router(client.router)


@app.get("/")
def read_root():
    return {"status": "ok", "projeto": "CRM Andrade"}
