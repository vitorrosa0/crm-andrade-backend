from fastapi import FastAPI
from app.routers import client

app = FastAPI(title="CRM Andrade")

app.include_router(client.router)

@app.get("/")
def read_root():
    return {"status": "ok", "projeto": "CRM Andrade"}