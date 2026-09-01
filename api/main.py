"""CNPJ API FastAPI application."""

import logging

from fastapi import FastAPI

from api.database import db
from api.routers import busca, cnpj, referencias

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CNPJ API",
    description="Consulta a base CNPJ da Receita Federal (banco do cnpj-data-pipeline).",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(cnpj.router)
app.include_router(busca.router)
app.include_router(referencias.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "database": "up"}


@app.on_event("shutdown")
def shutdown():
    db.close()
