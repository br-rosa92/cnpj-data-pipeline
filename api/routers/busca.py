"""Router for filtered searches over the CNPJ database."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.config import api_config
from api.dependencies import expect_api_key, rate_limiter
from api.queries import buscar
from api.schemas import BuscaResultadoOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buscar", tags=["busca"])


class BuscaParams(BaseModel):
    uf: str | None = None
    cnae: str | None = None
    porte: str | None = None
    situacao: str | None = None
    capital_min: float | None = None
    capital_max: float | None = None
    razao: str | None = None


@router.get("/", response_model=BuscaResultadoOut, dependencies=[Depends(expect_api_key)])
def get_busca(
    uf: str | None = Query(default=None, max_length=2),
    cnae: str | None = Query(default=None, max_length=7),
    porte: str | None = Query(default=None, max_length=2),
    situacao: str | None = Query(default=None, max_length=2),
    capital_min: float | None = Query(default=None),
    capital_max: float | None = Query(default=None),
    razao: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=api_config.page_size_max),
):
    if not rate_limiter.allows("busca", "busca"):
        raise HTTPException(status_code=429, detail="Rate limit excedido", headers={"Retry-After": "60"})
    offset_max = api_config.offset_max
    if (page - 1) * page_size >= offset_max:
        raise HTTPException(status_code=422, detail=f"Offset maximo excedido (max {offset_max})")
    try:
        total, items = buscar(
            {
                "uf": uf,
                "cnae": cnae,
                "porte": porte,
                "situacao": situacao,
                "capital_min": capital_min,
                "capital_max": capital_max,
                "razao": razao,
                "page": page,
                "page_size": page_size,
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"total": total, "page": page, "page_size": page_size, "items": items}
