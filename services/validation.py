# -*- coding: utf-8 -*-
"""Validações compartilhadas por serviços e interface.

Nenhuma função desta pasta depende de Qt.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

COLUNAS_CLIMA = {
    "data": "Date",
    "temperatura_min": "MinTemp",
    "temperatura_max": "MaxTemp",
    "precipitacao": "Precipitation",
    "eto": "ReferenceET",
}
ALIASES_CSV = {
    "date": "data",
    "data": "data",
    "tmin": "temperatura_min",
    "temperatura_min": "temperatura_min",
    "mintemp": "temperatura_min",
    "tmax": "temperatura_max",
    "temperatura_max": "temperatura_max",
    "maxtemp": "temperatura_max",
    "rain": "precipitacao",
    "precip": "precipitacao",
    "precipitacao": "precipitacao",
    "precipitation": "precipitacao",
    "eto": "eto",
    "referenceet": "eto",
    "et0": "eto",
    "rh": "umidade_relativa",
    "umidade_relativa": "umidade_relativa",
    "humidity": "umidade_relativa",
    "wind": "velocidade_vento",
    "velocidade_vento": "velocidade_vento",
    "windspeed": "velocidade_vento",
    "rs": "radiacao_solar",
    "radiacao_solar": "radiacao_solar",
}


def parse_date(valor) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip().replace("/", "-")
    for formato in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {valor!r}. Use AAAA-MM-DD.")


def validar_datas(inicio, plantio, fim):
    ini, plant, fim_dt = parse_date(inicio), parse_date(plantio), parse_date(fim)
    if not (ini <= plant <= fim_dt):
        raise ValueError("A data de plantio deve estar entre o início e o fim da simulação.")
    if (fim_dt - ini).days > 3650:
        raise ValueError("O período simulado não pode ultrapassar 10 anos.")
    return ini, plant, fim_dt


def validar_planilha_clima(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza colunas, converte tipos e valida uma série diária.

    Retorna DataFrame com colunas: data, temperatura_min, temperatura_max,
    precipitacao, eto e opcionais de umidade/vento/radiação.
    """
    if df is None or df.empty:
        raise ValueError("A planilha climática está vazia.")

    normalizado = df.copy()
    normalizado.columns = [str(c).strip().lower() for c in normalizado.columns]
    renomear = {c: ALIASES_CSV[c] for c in normalizado.columns if c in ALIASES_CSV}
    normalizado = normalizado.rename(columns=renomear)

    obrigatorias = ["data", "temperatura_min", "temperatura_max", "precipitacao", "eto"]
    faltando = [c for c in obrigatorias if c not in normalizado.columns]
    if faltando:
        rotulos = {
            "data": "data (Date)",
            "temperatura_min": "temperatura_min (Tmin)",
            "temperatura_max": "temperatura_max (Tmax)",
            "precipitacao": "precipitacao (Rain)",
            "eto": "eto (ETo)",
        }
        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(rotulos.get(c, c) for c in faltando)
            + ". Esperado: data, temperatura_min, temperatura_max, precipitacao, eto."
        )

    normalizado["data"] = normalizado["data"].map(parse_date)
    for coluna in obrigatorias[1:]:
        normalizado[coluna] = pd.to_numeric(normalizado[coluna], errors="coerce")

    if normalizado[obrigatorias].isna().any().any():
        linhas = normalizado[normalizado[obrigatorias].isna().any(axis=1)]
        raise ValueError(
            f"Valores ausentes ou não numéricos em {len(linhas)} linha(s), "
            f"primeira delas: {linhas.iloc[0]['data']}."
        )
    if normalizado["data"].duplicated().any():
        duplicadas = normalizado.loc[normalizado["data"].duplicated(), "data"].unique()
        raise ValueError(f"Datas duplicadas: {', '.join(map(str, duplicadas[:5]))}.")

    normalizado = normalizado.sort_values("data").reset_index(drop=True)
    tmin = normalizado["temperatura_min"]
    tmax = normalizado["temperatura_max"]
    if (tmin > tmax).any():
        raise ValueError("Temperatura mínima maior que máxima em alguma data.")
    if (normalizado["precipitacao"] < 0).any():
        raise ValueError("Precipitação não pode ser negativa.")
    if (normalizado["eto"] <= 0).any():
        raise ValueError("ETo deve ser positivo (o AquaCrop limita ETo a no mínimo 0,1 mm).")

    datas = normalizado["data"].tolist()
    for anterior, atual in zip(datas, datas[1:]):
        if (atual - anterior).days != 1:
            raise ValueError(
                f"Série climática com lacuna: {anterior} -> {atual}. "
                "O AquaCrop exige dados diários contínuos."
            )
    return normalizado


def validar_cobertura_clima(df: pd.DataFrame, inicio, fim):
    """Garante que o clima cubra todo o período simulado."""
    ini, _plant, fim_dt = validar_datas(inicio, inicio, fim)
    coluna_data = "Date" if "Date" in df.columns else "data"
    primeira = parse_date(df[coluna_data].iloc[0])
    ultima = parse_date(df[coluna_data].iloc[-1])
    if primeira > ini:
        raise ValueError(
            f"O clima começa em {primeira}, mas a simulação começa em {ini}."
        )
    if ultima < fim_dt:
        raise ValueError(
            f"O clima termina em {ultima}, mas a simulação termina em {fim_dt}."
        )


def validar_camadas(camadas: list[dict]) -> list[dict]:
    if not camadas:
        raise ValueError("O perfil de solo precisa de ao menos uma camada.")
    validadas = []
    for indice, camada in enumerate(camadas, start=1):
        vals = {
            "espessura": float(camada["espessura"]),
            "th_wp": float(camada["th_wp"]),
            "th_fc": float(camada["th_fc"]),
            "th_s": float(camada["th_s"]),
            "ksat": float(camada["ksat"]),
            "penetrabilidade": float(camada.get("penetrabilidade") or 100),
        }
        if vals["espessura"] <= 0 or vals["espessura"] > 10:
            raise ValueError(f"Camada {indice}: espessura deve estar entre 0 e 10 m.")
        if not (0 < vals["th_wp"] < vals["th_fc"] < vals["th_s"] < 1):
            raise ValueError(
                f"Camada {indice}: é necessário 0 < th_wp < th_fc < th_s < 1."
            )
        if vals["ksat"] <= 0:
            raise ValueError(f"Camada {indice}: Ksat deve ser positivo.")
        validadas.append(vals)
    return validadas


def validar_irrigacao(manejo: dict, agenda: list[dict], inicio, fim):
    metodo = int(manejo["metodo_aquacrop"])
    if metodo not in (0, 1, 2, 3):
        raise ValueError("Método de irrigação não suportado pelo adaptador.")
    if metodo == 1:
        limite = manejo.get("limite_umidade")
        if limite is None or not (0 < float(limite) <= 100):
            raise ValueError("Informe o limite de umidade (0 < valor <= 100).")
    if metodo == 2:
        intervalo = manejo.get("intervalo")
        intervalo = 3 if intervalo is None else intervalo
        if int(intervalo) <= 0:
            raise ValueError("O intervalo de irrigação deve ser positivo.")
    if metodo == 3:
        if not agenda:
            raise ValueError("Informe ao menos uma data/lâmina no calendário de irrigação.")
        ini, _plant, fim_dt = validar_datas(inicio, inicio, fim)
        for evento in agenda:
            data_ev = parse_date(evento["data"])
            if not (ini <= data_ev <= fim_dt):
                raise ValueError(f"Data de irrigação fora do período: {data_ev}.")
            if float(evento["lamina"]) < 0:
                raise ValueError("Lâmina de irrigação não pode ser negativa.")
    return metodo
