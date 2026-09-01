"""Tests for the CNPJ API."""

import pytest
from fastapi.testclient import TestClient

from api.config import api_config
from api.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api_config, "api_keys", ["test-key"])
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    from api.dependencies import rate_limiter

    rate_limiter._mem = rate_limiter._mem.__class__(rate_limiter._mem.limit)
    rate_limiter._mem_per_key = {}
    yield


def test_health_without_key(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_requires_api_key(client):
    resp = client.get("/cnpj/00000000000000/resumo")
    assert resp.status_code == 401


def test_invalid_api_key(client):
    resp = client.get("/cnpj/00000000000000/resumo", headers={"X-Api-Key": "wrong"})
    assert resp.status_code == 401


def test_cnpj_404(client, monkeypatch):
    from api.routers import cnpj as cnpj_router

    monkeypatch.setattr(cnpj_router, "consultar_resumo", lambda cnpj: None)
    resp = client.get("/cnpj/00000000000000/resumo", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 404


def test_cnpj_resumo_ok(client, monkeypatch):
    from api.routers import cnpj as cnpj_router

    monkeypatch.setattr(
        cnpj_router,
        "consultar_resumo",
        lambda cnpj: {
            "cnpj": cnpj,
            "razao_social": "EMPRESA TESTE LTDA",
            "nome_fantasia": "Teste",
            "situacao_cadastral": "02",
            "data_inicio_atividade": None,
            "cnae_principal": "6202300",
            "cnae_principal_descricao": "Desenvolvimento de programas",
            "cnaes_secundarias": [],
            "porte": "01",
            "capital_social": 100000.0,
            "natureza_juridica": "2062",
            "natureza_juridica_descricao": "Sociedade Empresaria Limitada",
            "uf": "SP",
            "municipio_nome": "SAO PAULO",
            "opcao_simples": "S",
            "opcao_mei": "N",
            "telefone": "(11) 9999-9999",
            "email": "contato@teste.com.br",
            "idade_anos": 5,
        },
    )
    resp = client.get("/cnpj/00000000000000/resumo", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["razao_social"] == "EMPRESA TESTE LTDA"
    assert body["cnae_principal"] == "6202300"


def test_cnpj_invalido(client):
    resp = client.get("/cnpj/123/resumo", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 422


def test_rate_limit_429(client, monkeypatch):
    from api.routers import cnpj as cnpj_router

    monkeypatch.setattr(cnpj_router, "consultar_resumo", lambda cnpj: None)

    from api.config import api_config
    from api.dependencies import SlidingWindowLimiter, rate_limiter

    api_config.rate_limit_per_key = 3
    rate_limiter._redis = None
    rate_limiter._mem_per_key["00000000000000"] = SlidingWindowLimiter(3)
    rate_limiter._mem = SlidingWindowLimiter(api_config.rate_limit_global)

    for _ in range(3):
        resp = client.get("/cnpj/00000000000000/resumo", headers={"X-Api-Key": "test-key"})
        assert resp.status_code == 404
    resp = client.get("/cnpj/00000000000000/resumo", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") == "60"


def test_busca_filtros(client, monkeypatch):
    from api.routers import busca as busca_router

    monkeypatch.setattr(
        busca_router,
        "buscar",
        lambda f: (
            1,
            [
                {
                    "cnpj": "00000000000000",
                    "razao_social": "EMPRESA TESTE",
                    "nome_fantasia": None,
                    "situacao_cadastral": "02",
                    "data_inicio_atividade": None,
                    "cnae_principal": "62",
                    "cnae_principal_descricao": None,
                    "cnaes_secundarias": [],
                    "porte": "03",
                    "capital_social": 500000.0,
                    "natureza_juridica": None,
                    "natureza_juridica_descricao": None,
                    "uf": "SP",
                    "municipio_nome": None,
                    "opcao_simples": None,
                    "opcao_mei": None,
                    "telefone": None,
                    "email": None,
                    "idade_anos": None,
                }
            ],
        ),
    )
    resp = client.get(
        "/buscar/?uf=SP&cnae=62&porte=03&page=1&page_size=50",
        headers={"X-Api-Key": "test-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["uf"] == "SP"


def test_busca_page_size_max(client):
    resp = client.get("/buscar/?page_size=51", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 422


def test_busca_offset_max(client):
    resp = client.get("/buscar/?page=200&page_size=50", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 422


def test_busca_uf_invalida(client, monkeypatch):
    from api.routers import busca as busca_router

    monkeypatch.setattr(busca_router, "buscar", lambda f: (0, []))

    from api.dependencies import validate_uf

    with pytest.raises(ValueError):
        validate_uf("XYZ")

    resp = client.get("/buscar/?uf=XYZ", headers={"X-Api-Key": "test-key"})
    assert resp.status_code in (200, 422)


def test_referencias(client, monkeypatch):
    from api.routers import referencias as ref_router

    monkeypatch.setattr(
        ref_router,
        "obter_referencia",
        lambda tabela, codigo: {"codigo": codigo, "descricao": "Desenvolvimento de programas"},
    )
    resp = client.get("/cnaes/6202300", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["descricao"] == "Desenvolvimento de programas"

    monkeypatch.setattr(ref_router, "obter_referencia", lambda tabela, codigo: None)
    resp = client.get("/municipios/1234567", headers={"X-Api-Key": "test-key"})
    assert resp.status_code == 404
