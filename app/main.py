from fastapi import FastAPI

app = FastAPI(title="CRM Andrade")

@app.get("/")
def read_root():
    return {"status": "ok", "projeto": "CRM Andrade"}