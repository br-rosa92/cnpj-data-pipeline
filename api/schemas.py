"""Pydantic schemas for API responses."""

import datetime

from pydantic import BaseModel, ConfigDict


class ReferenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    descricao: str | None = None


class SocioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cnpj_basico: str
    identificador_de_socio: str
    nome_socio: str | None = None
    cnpj_cpf_do_socio: str | None = None
    qualificacao_do_socio: str | None = None
    data_entrada_sociedade: datetime.date | None = None
    pais: str | None = None
    representante_legal: str | None = None
    nome_do_representante: str | None = None
    faixa_etaria: str | None = None


class SimplesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cnpj_basico: str
    opcao_pelo_simples: str | None = None
    data_opcao_pelo_simples: datetime.date | None = None
    data_exclusao_do_simples: datetime.date | None = None
    opcao_pelo_mei: str | None = None
    data_opcao_pelo_mei: datetime.date | None = None
    data_exclusao_do_mei: datetime.date | None = None


class CNPJResumoOut(BaseModel):
    cnpj: str
    razao_social: str | None = None
    nome_fantasia: str | None = None
    situacao_cadastral: str | None = None
    data_inicio_atividade: datetime.date | None = None
    cnae_principal: str | None = None
    cnae_principal_descricao: str | None = None
    cnaes_secundarias: list[str] = []
    porte: str | None = None
    capital_social: float | None = None
    natureza_juridica: str | None = None
    natureza_juridica_descricao: str | None = None
    uf: str | None = None
    municipio_nome: str | None = None
    opcao_simples: str | None = None
    opcao_mei: str | None = None
    telefone: str | None = None
    email: str | None = None
    idade_anos: int | None = None


class CNPJDetailOut(CNPJResumoOut):
    cnpj_ordem: str | None = None
    cnpj_dv: str | None = None
    identificador_matriz_filial: int | None = None
    data_situacao_cadastral: datetime.date | None = None
    motivo_situacao_cadastral: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cep: str | None = None
    municipio_codigo: str | None = None
    socios: list[SocioOut] = []
    dados_simples: SimplesOut | None = None


class BuscaItemOut(CNPJResumoOut):
    cnpj_formatado: str = ""


class BuscaResultadoOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BuscaItemOut]
