"""Router for reference tables (CNAE, municipios, etc.)."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import expect_api_key
from api.queries import obter_referencia
from api.schemas import ReferenciaOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["referencias"])


@router.get("/cnaes/{codigo}", response_model=ReferenciaOut, dependencies=[Depends(expect_api_key)])
def get_cnae(codigo: str):
    ref = obter_referencia("cnaes", codigo)
    if ref is None:
        raise HTTPException(status_code=404, detail="CNAE nao encontrado")
    return ref


@router.get("/municipios/{codigo}", response_model=ReferenciaOut, dependencies=[Depends(expect_api_key)])
def get_municipio(codigo: str):
    ref = obter_referencia("municipios", codigo)
    if ref is None:
        raise HTTPException(status_code=404, detail="Municipio nao encontrado")
    return ref
