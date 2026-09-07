"""Tests for scoring (PRD24 S2)."""

from api.scoring import calculate_score


def test_calculate_score_basico():
    resumo = {
        "capital_social": 600000,
        "porte": "05",
        "data_inicio_atividade": __import__("datetime").date(2010, 1, 1),
        "cnae_principal": "62023",
        "uf": "SP",
        "opcao_simples": True,
        "opcao_mei": False,
    }
    result = calculate_score(resumo)
    assert result["score"] == 94
    assert result["vertical"] == "FinTech / Payments"
    assert result["formula"] == "v1"
