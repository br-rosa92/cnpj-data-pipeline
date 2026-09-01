"""Router for CNPJ consultation endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import expect_api_key, rate_limiter
from api.queries import consultar_detalhe, consultar_resumo
from api.schemas import CNPJDetailOut, CNPJResumoOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cnpj", tags=["cnpj"])


@router.get("/{cnpj}/resumo", response_model=CNPJResumoOut, dependencies=[Depends(expect_api_key)])
def get_resumo(cnpj: str):
    if not rate_limiter.allows(cnpj, "cnpj"):
        raise HTTPException(status_code=429, detail="Rate limit excedido", headers={"Retry-After": "60"})
    try:
        data = consultar_resumo(cnpj)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if data is None:
        raise HTTPException(status_code=404, detail="CNPJ nao encontrado")
    return data


@router.get("/{cnpj}", response_model=CNPJDetailOut, dependencies=[Depends(expect_api_key)])
def get_detalhe(cnpj: str):
    if not rate_limiter.allows(cnpj, "cnpj"):
        raise HTTPException(status_code=429, detail="Rate limit excedido", headers={"Retry-After": "60"})
    try:
        data = consultar_detalhe(cnpj)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if data is None:
        raise HTTPException(status_code=404, detail="CNPJ nao encontrado")
    return data
