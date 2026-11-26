# -*- coding: utf-8 -*-
"""Adaptador da API real do AquaCrop 3.1.0.

Aqui não há valores simulados nem cálculos "bonitos": tudo o que é devolvido
vem de ``AquaCropModel.get_*()`` ou é derivado dessas saídas.
"""

from __future__ import annotations

import pandas as pd
from aquacrop import AquaCropModel, InitialWaterContent, IrrigationManagement

from config.settings import AQUACROP_VERSION
from integracao_aquacrop.crop_parameters import criar_crop
from services import climate_service, soil_service, validation


def preparar_agua_inicial(tipo: str, valor: float | None, n_camadas: int):
    """InitialWaterContent para todas as camadas do perfil."""
    tipo = str(tipo).upper()
    n = max(1, int(n_camadas))
    if tipo in ("FC", "WP", "SAT"):
        return InitialWaterContent(
            wc_type="Prop", method="Layer",
            depth_layer=list(range(1, n + 1)), value=[tipo] * n,
        )
    if tipo in ("PCT", "Pct", "PERCENTUAL"):
        if valor is None:
            raise ValueError("Informe a porcentagem da água disponível no solo.")
        return InitialWaterContent(
            wc_type="Pct", method="Layer",
            depth_layer=list(range(1, n + 1)), value=[float(valor)] * n,
        )
    raise ValueError("Condição inicial inválida. Use FC, WP, SAT ou percentual.")


def preparar_irrigacao(manejo: dict) -> IrrigationManagement:
    metodo = validation.validar_irrigacao(
        manejo,
        manejo.get("agenda", []),
        manejo["_inicio"],
        manejo["_fim"],
    )
    if metodo == 0:
        return IrrigationManagement(irrigation_method=0)
    if metodo == 1:
        limite = float(manejo["limite_umidade"])
        return IrrigationManagement(irrigation_method=1, SMT=[limite] * 4)
    if metodo == 2:
        return IrrigationManagement(
            irrigation_method=2, IrrInterval=int(manejo.get("intervalo") or 3)
        )
    agenda = pd.DataFrame(
        {
            "Date": pd.to_datetime([e["data"] for e in manejo["agenda"]]),
            "Depth": [float(e["lamina"]) for e in manejo["agenda"]],
        }
    )
    return IrrigationManagement(irrigation_method=3, Schedule=agenda)


def executar(weather_df: pd.DataFrame, solo: dict, verificacao_cultura: dict,
             manejo: dict, data_plantio: str, data_inicio: str, data_fim: str,
             umidade_inicial_tipo="FC", umidade_inicial_valor=None,
             data_colheita=None, overrides_cultura=None) -> dict:
    """Executa o modelo e devolve saídas brutas + metadados da execução."""
    validation.validar_datas(data_inicio, data_plantio, data_fim)
    validation.validar_cobertura_clima(weather_df, data_inicio, data_fim)

    solo_obj = soil_service.criar_solo(solo)
    n_camadas = int(solo_obj.profile["Layer"].nunique())
    # O AquaCrop espera planting_date/harvest_date no formato MM/DD.
    plantio_mmdd = pd.to_datetime(data_plantio).strftime("%m/%d")
    colheita_mmdd = (
        pd.to_datetime(data_colheita).strftime("%m/%d") if data_colheita else None
    )
    crop = criar_crop(
        verificacao_cultura, plantio_mmdd, colheita_mmdd, overrides_cultura
    )
    irrigacao = preparar_irrigacao(
        {**manejo, "_inicio": data_inicio, "_fim": data_fim}
    )
    agua_inicial = preparar_agua_inicial(
        umidade_inicial_tipo, umidade_inicial_valor, n_camadas
    )

    modelo = AquaCropModel(
        sim_start_time=pd.to_datetime(data_inicio).strftime("%Y/%m/%d"),
        sim_end_time=pd.to_datetime(data_fim).strftime("%Y/%m/%d"),
        weather_df=weather_df.copy(),
        soil=solo_obj,
        crop=crop,
        initial_water_content=agua_inicial,
        irrigation_management=irrigacao,
    )
    modelo.run_model(till_termination=True)

    return {
        "sucesso": True,
        "safra": modelo.get_simulation_results().copy(),
        "crescimento": modelo.get_crop_growth().copy(),
        "fluxo": modelo.get_water_flux().copy(),
        "armazenamento": modelo.get_water_storage().copy(),
        "informacoes": modelo.get_additional_information().copy(),
        "metadados": {
            "aquacrop_version": AQUACROP_VERSION,
            "cultura": verificacao_cultura["codigo_aquacrop"],
            "origem_parametros": verificacao_cultura["origem"],
            "calibrada_localmente": verificacao_cultura["calibrada_localmente"],
            "numero_camadas": n_camadas,
            "metodo_irrigacao": int(manejo["metodo_aquacrop"]),
            "concluido": bool(modelo.get_additional_information().get("has_model_finished")),
            "tempo_execucao_s": float(
                modelo.get_additional_information().get("execution_time") or 0
            ),
        },
    }
