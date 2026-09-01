"""Business queries against the CNPJ database."""

import logging
from datetime import date

from api.database import db
from api.dependencies import normalize_cnpj, split_cnpj, validate_uf

logger = logging.getLogger(__name__)

_CONSULTA_BASE = """
SELECT e.cnpj_basico, e.cnpj_ordem, e.cnpj_dv,
       e.nome_fantasia, e.situacao_cadastral, e.data_situacao_cadastral,
       e.data_inicio_atividade, e.cnae_fiscal_principal, e.cnae_fiscal_secundaria,
       e.motivo_situacao_cadastral, e.tipo_logradouro, e.logradouro, e.numero,
       e.complemento, e.bairro, e.cep, e.uf, e.municipio, e.pais,
       e.ddd_1, e.telefone_1, e.ddd_2, e.telefone_2, e.correio_eletronico,
       e.identificador_matriz_filial, e.situacao_especial,
       emp.razao_social, emp.natureza_juridica, emp.capital_social,
       emp.porte, emp.ente_federativo_responsavel,
       ds.opcao_pelo_simples, ds.opcao_pelo_mei,
       c.descricao AS cnae_descricao,
       m.descricao AS municipio_descricao,
       nj.descricao AS natureza_juridica_descricao
FROM estabelecimentos e
JOIN empresas emp ON emp.cnpj_basico = e.cnpj_basico
LEFT JOIN dados_simples ds ON ds.cnpj_basico = e.cnpj_basico
LEFT JOIN cnaes c ON c.codigo = e.cnae_fiscal_principal
LEFT JOIN municipios m ON m.codigo = e.municipio
LEFT JOIN naturezas_juridicas nj ON nj.codigo = emp.natureza_juridica
"""


def _telefone_completo(e: dict) -> str | None:
    ddd = e.get("ddd_1") or ""
    fone = e.get("telefone_1") or ""
    if ddd and fone:
        return f"({ddd}) {fone}"
    return fone or None


def _resumo_from_row(row: dict) -> dict:
    cnpj = f"{row['cnpj_basico']}{row['cnpj_ordem']}{row['cnpj_dv']}"
    cnaes_sec = [c for c in (row.get("cnae_fiscal_secundaria") or "").split(",") if c]
    idade = None
    if row.get("data_inicio_atividade"):
        idade = (date.today() - row["data_inicio_atividade"]).days // 365
    return {
        "cnpj": cnpj,
        "razao_social": row.get("razao_social"),
        "nome_fantasia": row.get("nome_fantasia"),
        "situacao_cadastral": row.get("situacao_cadastral"),
        "data_inicio_atividade": row.get("data_inicio_atividade"),
        "cnae_principal": row.get("cnae_fiscal_principal"),
        "cnae_principal_descricao": row.get("cnae_descricao"),
        "cnaes_secundarias": cnaes_sec,
        "porte": row.get("porte"),
        "capital_social": float(row["capital_social"]) if row.get("capital_social") is not None else None,
        "natureza_juridica": row.get("natureza_juridica"),
        "natureza_juridica_descricao": row.get("natureza_juridica_descricao"),
        "uf": row.get("uf"),
        "municipio_nome": row.get("municipio_descricao"),
        "opcao_simples": row.get("opcao_pelo_simples"),
        "opcao_mei": row.get("opcao_pelo_mei"),
        "telefone": _telefone_completo(row),
        "email": row.get("correio_eletronico"),
        "idade_anos": idade,
    }


def consultar_resumo(cnpj_raw: str) -> dict | None:
    cnpj = normalize_cnpj(cnpj_raw)
    basico, ordem, dv = split_cnpj(cnpj)
    sql = _CONSULTA_BASE + "\nWHERE e.cnpj_basico = %s AND e.cnpj_ordem = %s AND e.cnpj_dv = %s"
    row = db.fetch_one(sql, (basico, ordem, dv))
    if not row:
        return None
    data = _resumo_from_row(row)
    data["cnpj"] = cnpj
    return data


def consultar_detalhe(cnpj_raw: str) -> dict | None:
    cnpj = normalize_cnpj(cnpj_raw)
    basico, ordem, dv = split_cnpj(cnpj)
    sql = _CONSULTA_BASE + "\nWHERE e.cnpj_basico = %s AND e.cnpj_ordem = %s AND e.cnpj_dv = %s"
    row = db.fetch_one(sql, (basico, ordem, dv))
    if not row:
        return None
    data = _resumo_from_row(row)
    data["cnpj"] = cnpj
    data["cnpj_ordem"] = row.get("cnpj_ordem")
    data["cnpj_dv"] = row.get("cnpj_dv")
    data["identificador_matriz_filial"] = row.get("identificador_matriz_filial")
    data["data_situacao_cadastral"] = row.get("data_situacao_cadastral")
    data["motivo_situacao_cadastral"] = row.get("motivo_situacao_cadastral")
    data["logradouro"] = row.get("logradouro")
    data["numero"] = row.get("numero")
    data["complemento"] = row.get("complemento")
    data["bairro"] = row.get("bairro")
    data["cep"] = row.get("cep")
    data["municipio_codigo"] = row.get("municipio")

    socios = db.fetch_all(
        "SELECT * FROM socios WHERE cnpj_basico = %s ORDER BY identificador_de_socio, nome_socio",
        (basico,),
    )
    simples = db.fetch_one("SELECT * FROM dados_simples WHERE cnpj_basico = %s", (basico,))
    data["socios"] = [dict(s) for s in socios]
    data["dados_simples"] = dict(simples) if simples else None
    return data


def buscar(filtros: dict) -> tuple[int, list[dict]]:
    """Busca com filtros e paginação. Retorna (total, rows)."""
    where = []
    params: list = []

    uf = validate_uf(filtros.get("uf"))
    if uf:
        where.append("e.uf = %s")
        params.append(uf)
    cnae = (filtros.get("cnae") or "").strip()
    if cnae:
        where.append("e.cnae_fiscal_principal LIKE %s")
        params.append(f"{cnae}%")
    porte = (filtros.get("porte") or "").strip()
    if porte:
        where.append("emp.porte = %s")
        params.append(porte)
    situacao = (filtros.get("situacao") or "").strip()
    if situacao:
        where.append("e.situacao_cadastral = %s")
        params.append(situacao)
    if filtros.get("capital_min") is not None:
        where.append("emp.capital_social >= %s")
        params.append(filtros["capital_min"])
    if filtros.get("capital_max") is not None:
        where.append("emp.capital_social <= %s")
        params.append(filtros["capital_max"])
    if filtros.get("razao"):
        where.append("emp.razao_social ILIKE %s")
        params.append(f"%{filtros['razao']}%")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    offset = (filtros.get("page", 1) - 1) * filtros.get("page_size", 20)
    sql_total = (
        "SELECT count(*) AS total FROM estabelecimentos e "
        "JOIN empresas emp ON emp.cnpj_basico = e.cnpj_basico "
        f"{where_sql}"
    )
    total_row = db.fetch_one(sql_total, tuple(params))
    total = int(total_row["total"]) if total_row else 0

    sql = _CONSULTA_BASE + f"\n{where_sql}" + "\nORDER BY emp.razao_social LIMIT %s OFFSET %s"
    rows = db.fetch_all(sql, tuple(params) + (filtros.get("page_size", 20), offset))
    return total, [_resumo_from_row(r) for r in rows]


def obter_referencia(tabela: str, codigo: str) -> dict | None:
    tabelas = {"cnaes": "cnaes", "municipios": "municipios"}
    real = tabelas.get(tabela)
    if not real:
        raise ValueError("Tabela de referencia invalida")
    return db.fetch_one(f"SELECT codigo, descricao FROM {real} WHERE codigo = %s", (codigo,))
