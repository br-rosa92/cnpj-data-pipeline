"""Router for lead scoring (PRD24 S2)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import expect_api_key, rate_limiter
from api.queries import buscar, consultar_resumo
from api.schemas import ScoreOut, ScoreRequest, ScoreTopOut
from api.scoring import calculate_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/score", tags=["score"])


@router.post("/", response_model=list[ScoreOut], dependencies=[Depends(expect_api_key)])
def post_score(payload: ScoreRequest):
    if not rate_limiter.allows("score", "score"):
        raise HTTPException(status_code=429, detail="Rate limit excedido", headers={"Retry-After": "60"})
    if not payload.cnpjs:
        raise HTTPException(status_code=422, detail="Lista de CNPJs vazia")
    if len(payload.cnpjs) > 100:
        raise HTTPException(status_code=422, detail="Maximo 100 CNPJs por request")
    results = []
    for cnpj in payload.cnpjs:
        try:
            resumo = consultar_resumo(cnpj)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if resumo is None:
            continue
        scored = calculate_score(resumo)
        results.append({"cnpj": resumo["cnpj"], **scored})
    return results


@router.get("/top", response_model=ScoreTopOut, dependencies=[Depends(expect_api_key)])
def get_top(
    uf: str | None = Query(default=None, max_length=2),
    cnae: str | None = Query(default=None, max_length=7),
    limit: int = Query(default=20, ge=1, le=100),
):
    if not rate_limiter.allows("top", "score"):
        raise HTTPException(status_code=429, detail="Rate limit excedido", headers={"Retry-After": "60"})
    total, items = buscar({"uf": uf, "cnae": cnae, "page": 1, "page_size": limit * 2})
    scored = []
    for item in items:
        s = calculate_score(item)
        scored.append({"cnpj": item["cnpj"], **s})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"total": total, "items": scored[:limit]}
