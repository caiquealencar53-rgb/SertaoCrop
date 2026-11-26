# -*- coding: utf-8 -*-
"""Importação, validação e preparação de dados climáticos."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd

from database import repositories as repo
from services.validation import validar_planilha_clima

# Ordem das colunas exigida pelo AquaCrop 3.1.0: ele lê as colunas por posição.
COLUNAS_AQUACROP = ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]


def ler_csv(caminho, sep=None) -> pd.DataFrame:
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo climático não encontrado: {caminho}")
    if sep is None:
        try:
            return pd.read_csv(caminho, sep=None, engine="python")
        except Exception:
            return pd.read_csv(caminho)
    return pd.read_csv(caminho, sep=sep)


def importar_csv(conn, caminho, nome_estacao, codigo, sep=None, **campos_estacao):
    """Lê, valida e persiste uma série climática, criando a estação."""
    bruto = ler_csv(caminho, sep=sep)
    dados = validar_planilha_clima(bruto)
    estacao_id = repo.add_estacao(conn, nome_estacao, codigo, **campos_estacao)
    registros = []
    for _, linha in dados.iterrows():
        registro = {
            "data": linha["data"],
            "temperatura_min": float(linha["temperatura_min"]),
            "temperatura_max": float(linha["temperatura_max"]),
            "precipitacao": float(linha["precipitacao"]),
            "eto": float(linha["eto"]),
        }
        for origem, destino in (
            ("umidade_relativa", "umidade_relativa"),
            ("velocidade_vento", "velocidade_vento"),
            ("radiacao_solar", "radiacao_solar"),
        ):
            if origem in dados.columns and pd.notna(linha[origem]):
                registro[destino] = float(linha[origem])
        registros.append(registro)
    origem = "DEMONSTRACAO" if campos_estacao.get("eh_demonstracao") else "OBSERVADO"
    repo.upsert_clima(conn, estacao_id, registros, origem=origem,
                      validado=int(bool(campos_estacao.get("validado", 0))))
    return estacao_id, len(registros)


def importar_registros_manuais(conn, registros, nome_estacao, codigo, **campos_estacao):
    """Persiste uma lista de dicts já no formato do repositório."""
    dados = validar_planilha_clima(pd.DataFrame(registros))
    estacao_id = repo.add_estacao(conn, nome_estacao, codigo, **campos_estacao)
    registros_validos = dados.to_dict("records")
    origem = "DEMONSTRACAO" if campos_estacao.get("eh_demonstracao") else "MANUAL"
    repo.upsert_clima(conn, estacao_id, registros_validos, origem=origem,
                      validado=int(bool(campos_estacao.get("validado", 0))))
    return estacao_id, len(registros_validos)


def weather_from_rows(linhas) -> pd.DataFrame:
    """Converte linhas do banco no DataFrame exigido pelo AquaCrop."""
    if not linhas:
        raise ValueError("Nenhum dado climático cadastrado para a estação selecionada.")
    df = pd.DataFrame(linhas)
    df["data"] = pd.to_datetime(df["data"])
    df["eto"] = pd.to_numeric(df["eto"], errors="coerce").clip(lower=0.1)
    weather = pd.DataFrame(
        {
            "MinTemp": pd.to_numeric(df["temperatura_min"], errors="coerce"),
            "MaxTemp": pd.to_numeric(df["temperatura_max"], errors="coerce"),
            "Precipitation": pd.to_numeric(df["precipitacao"], errors="coerce"),
            "ReferenceET": df["eto"],
            "Date": df["data"],
        }
    )
    return weather[COLUNAS_AQUACROP].reset_index(drop=True)


def weather_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Converte uma planilha validada no formato do AquaCrop."""
    dados = validar_planilha_clima(df)
    weather = pd.DataFrame(
        {
            "MinTemp": dados["temperatura_min"],
            "MaxTemp": dados["temperatura_max"],
            "Precipitation": dados["precipitacao"],
            "ReferenceET": dados["eto"].clip(lower=0.1),
            "Date": pd.to_datetime(dados["data"]),
        }
    )
    return weather[COLUNAS_AQUACROP]


def resumo(linhas) -> dict:
    """Estatísticas descritivas dos dados persistidos (sem inventar valores)."""
    if not linhas:
        return {"dias": 0}
    df = pd.DataFrame(linhas)
    return {
        "dias": len(df),
        "inicio": str(df["data"].min()),
        "fim": str(df["data"].max()),
        "precipitacao_total_mm": float(pd.to_numeric(df["precipitacao"]).sum()),
        "eto_medio_mm": float(pd.to_numeric(df["eto"]).mean()),
        "tmin_medio_c": float(pd.to_numeric(df["temperatura_min"]).mean()),
        "tmax_medio_c": float(pd.to_numeric(df["temperatura_max"]).mean()),
        "origem": ", ".join(sorted(set(str(o) for o in df.get("origem", [])))) or "—",
    }


def periodos_do_clima(linhas, dias=30):
    """Úteis para pré-visualização: agrupa a série em blocos de ``dias``."""
    if not linhas:
        return []
    df = pd.DataFrame(linhas).sort_values("data")
    inicio = pd.to_datetime(df["data"].iloc[0])
    blocos = []
    for i in range(0, len(df), dias):
        bloco = df.iloc[i:i + dias]
        blocos.append(
            {
                "inicio": str(bloco["data"].iloc[0]),
                "fim": str(bloco["data"].iloc[-1]),
                "precipitacao_mm": float(pd.to_numeric(bloco["precipitacao"]).sum()),
                "eto_mm": float(pd.to_numeric(bloco["eto"]).sum()),
            }
        )
    return blocos
