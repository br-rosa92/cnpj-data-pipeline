"""Lead scoring engine v1 (6 dimensoes) - port de apps.leads.services.LeadScoringEngine."""

from datetime import date

ICP_CNAE_MAP = {
    "FinTech / Payments": ["62023", "63119", "74907", "66118", "66126"],
    "Food Service": ["56112", "56121", "56201"],
    "Retail": ["47113", "47121", "47512", "47717"],
    "GovTech": ["62015", "62040", "63119", "84116"],
    "Servicos Empresariais": ["70204", "74100", "82113", "82997", "73114"],
}


def get_vertical(cnae: str | None) -> str | None:
    if not cnae:
        return None
    for vertical, prefixes in ICP_CNAE_MAP.items():
        for prefix in prefixes:
            if cnae.startswith(prefix):
                return vertical
    return None


def _score_capital(capital):
    if capital is None:
        return {"score": 0, "capital": None, "faixa": "sem dado"}
    capital = float(capital)
    if capital > 1_000_000:
        return {"score": 10, "capital": capital, "faixa": ">1M"}
    if capital >= 500_000:
        return {"score": 8, "capital": capital, "faixa": "500k-1M"}
    if capital >= 100_000:
        return {"score": 6, "capital": capital, "faixa": "100k-500k"}
    if capital >= 50_000:
        return {"score": 4, "capital": capital, "faixa": "50k-100k"}
    return {"score": 2, "capital": capital, "faixa": "<50k"}


def _score_porte(porte):
    if not porte:
        return {"score": 0, "porte_code": None, "porte_desc": "sem dado"}
    mapping = {
        "05": (10, "Demais"),
        "03": (7, "PE"),
        "01": (4, "ME"),
        "00": (2, "N/I"),
    }
    score, desc = mapping.get(porte, (0, "desconhecido"))
    return {"score": score, "porte_code": porte, "porte_desc": desc}


def _score_idade(data_inicio):
    if data_inicio is None:
        return {"score": 0, "idade_anos": None, "faixa": "sem dado"}
    if isinstance(data_inicio, str):
        return {"score": 0, "idade_anos": None, "faixa": "sem dado"}
    idade = (date.today() - data_inicio).days // 365
    if idade > 10:
        return {"score": 10, "idade_anos": idade, "faixa": ">10a"}
    if idade >= 5:
        return {"score": 8, "idade_anos": idade, "faixa": "5-10a"}
    if idade >= 2:
        return {"score": 6, "idade_anos": idade, "faixa": "2-5a"}
    if idade >= 1:
        return {"score": 4, "idade_anos": idade, "faixa": "1-2a"}
    return {"score": 2, "idade_anos": idade, "faixa": "<1a"}


def _score_cnae(cnae):
    if not cnae:
        return {"score": 1, "cnae": None, "vertical": None}
    vertical = get_vertical(cnae)
    if vertical is None:
        return {"score": 3, "cnae": cnae, "vertical": None}
    vertical_scores = {
        "FinTech / Payments": 10,
        "Food Service": 9,
        "Retail": 8,
        "GovTech": 7,
        "Servicos Empresariais": 6,
    }
    return {"score": vertical_scores.get(vertical, 3), "cnae": cnae, "vertical": vertical}


def _score_uf(uf):
    if not uf:
        return {"score": 1, "uf": None}
    prioritarias = {"SP": 10, "PR": 10, "SC": 10}
    secundarias = {"RJ": 7, "MG": 7, "RS": 7}
    if uf in prioritarias:
        return {"score": 10, "uf": uf}
    if uf in secundarias:
        return {"score": 7, "uf": uf}
    return {"score": 4, "uf": uf}


def _score_simples(opcao_simples, opcao_mei):
    if opcao_mei:
        val = str(opcao_mei).strip()
        if val in ("1", "S", "s", "Sim", "SIM"):
            return {"score": 3, "simples": opcao_simples, "mei": True}
    if opcao_simples is True or str(opcao_simples).strip() in ("1", "S", "Sim", "SIM"):
        return {"score": 8, "simples": True, "mei": False}
    if opcao_simples is False or str(opcao_simples).strip() in ("0", "N", "Nao"):
        return {"score": 5, "simples": False, "mei": False}
    if opcao_simples:
        s = str(opcao_simples).strip().lower()
        if s in ("1", "s", "sim"):
            return {"score": 8, "simples": True, "mei": False}
        if s in ("0", "n", "nao", "não"):
            return {"score": 5, "simples": False, "mei": False}
    return {"score": 0, "simples": None, "mei": None}


def calculate_score(resumo: dict) -> dict:
    scores = {
        "f_capital": _score_capital(resumo.get("capital_social")),
        "f_porte": _score_porte(resumo.get("porte")),
        "f_idade": _score_idade(resumo.get("data_inicio_atividade")),
        "f_cnae": _score_cnae(resumo.get("cnae_principal")),
        "f_uf": _score_uf(resumo.get("uf")),
        "f_simples": _score_simples(resumo.get("opcao_simples"), resumo.get("opcao_mei")),
    }
    weights = {
        "f_capital": 0.20,
        "f_porte": 0.20,
        "f_idade": 0.15,
        "f_cnae": 0.25,
        "f_uf": 0.10,
        "f_simples": 0.10,
    }
    score = round(sum(scores[k]["score"] * weights[k] for k in scores) * 10)
    for k in scores:
        scores[k]["weighted"] = round(scores[k]["score"] * weights[k], 3)
    return {"score": score, "breakdown": scores, "formula": "v1", "vertical": scores["f_cnae"].get("vertical")}
