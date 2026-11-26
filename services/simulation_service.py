# -*- coding: utf-8 -*-
"""Orquestração: interface -> serviços -> AquaCrop -> Pandas -> SQLite.

Esta é a única porta de entrada para executar simulações. Nenhuma tela chama
o AquaCrop diretamente e nenhum resultado é inventado quando a execução falha.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from config.settings import AQUACROP_VERSION
from database import connect
from database import repositories as repo
from integracao_aquacrop import adapter, crop_parameters
from services import climate_service, validation


class FalhaSimulacao(RuntimeError):
    """Erro de execução já registrado no banco com status ERRO."""


def validar_configuracao(conn, config: dict) -> dict:
    """Valida todos os dados cadastrados antes de tocar no AquaCrop."""
    inicio, plantio, fim = validation.validar_datas(
        config["data_inicio"], config["data_plantio"], config["data_fim"]
    )

    verificacao = crop_parameters.verificar_cultura(conn, int(config["cultura_id"]))

    solo = repo.get_solo(conn, int(config["solo_id"]))
    if not solo:
        raise ValueError("Perfil de solo não encontrado.")

    estacao = repo.get_estacao(conn, int(config["estacao_id"]))
    if not estacao:
        raise ValueError("Estação meteorológica não encontrada.")

    linhas = repo.get_clima(
        conn, int(config["estacao_id"]),
        inicio.isoformat(), fim.isoformat(),
    )
    if not linhas:
        raise ValueError(
            "Não há dados climáticos cadastrados para o período selecionado."
        )
    weather = climate_service.weather_from_rows(linhas)
    validation.validar_cobertura_clima(weather, inicio.isoformat(), fim.isoformat())

    manejo = repo.get_manejo(conn, int(config["manejo_id"]))
    if not manejo:
        raise ValueError("Manejo de irrigação não encontrado.")
    validation.validar_irrigacao(manejo, manejo["agenda"], inicio.isoformat(), fim.isoformat())

    tipo = str(config.get("umidade_inicial_tipo", "FC")).upper()
    if tipo not in ("FC", "WP", "SAT", "PCT"):
        raise ValueError("Condição inicial de umidade inválida.")
    valor = config.get("umidade_inicial_valor")
    if tipo == "PCT" and valor is None:
        raise ValueError("Informe a porcentagem de água disponível no solo.")

    return {
        "inicio": inicio,
        "plantio": plantio,
        "fim": fim,
        "verificacao": verificacao,
        "solo": solo,
        "estacao": estacao,
        "weather": weather,
        "manejo": manejo,
        "tipo_umidade": tipo,
        "valor_umidade": valor,
        "precipitacao_total": float(weather["Precipitation"].clip(lower=0).sum()),
    }


def _processar_resultados(resultado: dict, inicio, precipitacao_total: float):
    """Converte saídas reais do AquaCrop em métricas e série diária com Pandas."""
    safra = resultado["safra"]
    if safra.empty:
        raise ValueError("O AquaCrop não retornou resultados de safra.")
    ultima = safra.iloc[-1]

    cresc = resultado["crescimento"]
    cresc = cresc[cresc["dap"] > 0].copy()
    if cresc.empty:
        raise ValueError("O AquaCrop não retornou crescimento durante a safra.")

    fluxo = resultado["fluxo"]
    colunas_fluxo = [c for c in ["time_step_counter", "Wr", "Es", "Tr", "TrPot"]
                     if c in fluxo.columns]
    diario = cresc.merge(fluxo[colunas_fluxo], on="time_step_counter", how="left")

    diario["data"] = diario["time_step_counter"].map(
        lambda c: (inicio + timedelta(days=int(c))).isoformat()
    )
    tr_pot = pd.to_numeric(diario.get("TrPot"), errors="coerce")
    tr = pd.to_numeric(diario.get("Tr"), errors="coerce")
    diario["transpiracao_relativa"] = (tr / tr_pot.where(tr_pot > 0)).round(4)
    diario["biomassa_t_ha"] = (pd.to_numeric(diario["biomass"]) / 100).round(4)
    diario["cobertura_dossel"] = pd.to_numeric(diario["canopy_cover"]).round(4)
    diario["indice_colheita"] = pd.to_numeric(diario["harvest_index_adj"]).round(4)
    diario["profundidade_raiz"] = pd.to_numeric(diario["z_root"]).round(3)
    diario["umidade_solo"] = pd.to_numeric(diario["Wr"]).round(2)

    et_mm = float((tr.fillna(0) + pd.to_numeric(diario["Es"], errors="coerce").fillna(0)).sum())
    biomassa_final_g_m2 = float(pd.to_numeric(diario["biomass"]).iloc[-1])
    biomassa_final_t_ha = biomassa_final_g_m2 / 100
    ef = pd.to_numeric(diario["transpiracao_relativa"]).replace([float("inf")], pd.NA)
    stress_relativo = float(ef.mean()) if ef.notna().any() else None

    metricas = {
        "produtividade": float(ultima["Dry yield (tonne/ha)"]),
        "produtividade_potencial": float(ultima["Yield potential (tonne/ha)"]),
        "biomassa_final": round(biomassa_final_t_ha, 4),
        "indice_colheita": float(diario["indice_colheita"].iloc[-1]),
        "irrigacao_sazonal": float(ultima["Seasonal irrigation (mm)"]),
        "precipitacao_total": round(precipitacao_total, 2),
        "evapotranspiracao": round(et_mm, 2),
        # WP da biomassa: (g/m2) / (mm) = kg/m3. Derivado de Es+Tr reais.
        "produtividade_agua": round(biomassa_final_g_m2 / et_mm, 4) if et_mm > 0 else None,
        "transpiracao_relativa_media": round(stress_relativo, 4) if stress_relativo else None,
        "observacoes": (
            "ET, WP e transpiração relativa são derivados das saídas diárias "
            "Es/Tr/TrPot do AquaCrop; não são parâmetros calibrados localmente."
        ),
    }

    registros = [
        {
            "data": r["data"],
            "dap": int(r["dap"]),
            "cobertura_dossel": float(r["cobertura_dossel"]),
            "biomassa": float(r["biomassa_t_ha"]),
            "indice_colheita": float(r["indice_colheita"]),
            "profundidade_raiz": float(r["profundidade_raiz"]),
            "umidade_solo": float(r["umidade_solo"]) if pd.notna(r["umidade_solo"]) else None,
            "transpiracao_relativa": (
                float(r["transpiracao_relativa"])
                if pd.notna(r["transpiracao_relativa"]) else None
            ),
        }
        for _, r in diario.iterrows()
    ]
    return metricas, registros, diario


def executar(config: dict, db_path=None) -> dict:
    """Executa, persiste e devolve os resultados de uma simulação.

    Cada fase usa sua própria conexão: assim o status ERRO sobrevive mesmo
    quando o AquaCrop levanta exceção.
    """
    with connect(db_path) as conn:
        preparado = validar_configuracao(conn, config)
        simulacao_id = repo.create_simulacao(
            conn,
            {
                "nome": config.get("nome"),
                "area_id": config.get("area_id"),
                "cultura_id": int(config["cultura_id"]),
                "solo_id": int(config["solo_id"]),
                "estacao_id": int(config["estacao_id"]),
                "manejo_id": int(config["manejo_id"]),
                "data_plantio": preparado["plantio"].isoformat(),
                "data_inicio": preparado["inicio"].isoformat(),
                "data_fim": preparado["fim"].isoformat(),
                "umidade_inicial_tipo": preparado["tipo_umidade"],
                "umidade_inicial_valor": preparado["valor_umidade"],
                "aquacrop_version": AQUACROP_VERSION,
            },
        )
        repo.set_status(conn, simulacao_id, "EXECUTANDO")

    try:
        resultado = adapter.executar(
            weather_df=preparado["weather"],
            solo=preparado["solo"],
            verificacao_cultura=preparado["verificacao"],
            manejo=preparado["manejo"],
            data_plantio=preparado["plantio"].isoformat(),
            data_inicio=preparado["inicio"].isoformat(),
            data_fim=preparado["fim"].isoformat(),
            umidade_inicial_tipo=preparado["tipo_umidade"],
            umidade_inicial_valor=preparado["valor_umidade"],
            data_colheita=config.get("data_colheita"),
            overrides_cultura=config.get("overrides_cultura"),
        )
        if not resultado["metadados"]["concluido"]:
            raise RuntimeError("O modelo não concluiu a simulação até a maturidade.")

        metricas, registros, diario = _processar_resultados(
            resultado, preparado["inicio"], preparado["precipitacao_total"]
        )
        with connect(db_path) as conn:
            repo.save_resultado(conn, simulacao_id, metricas)
            repo.save_crescimento_diario(conn, simulacao_id, registros)
            repo.set_status(conn, simulacao_id, "CONCLUIDA")
    except Exception as exc:
        with connect(db_path) as conn:
            repo.set_status(conn, simulacao_id, "ERRO", erro=str(exc))
        raise FalhaSimulacao(
            f"Simulação {simulacao_id} falhou: {exc}"
        ) from exc

    return {
        "sucesso": True,
        "simulacao_id": simulacao_id,
        "metricas": metricas,
        "diario": diario,
        "metadados": resultado["metadados"],
    }


def consultar_resultado(conn, simulacao_id: int) -> dict:
    """Recupera simulação + métricas + série diária do banco."""
    simulacao = repo.get_simulacao(conn, simulacao_id)
    if not simulacao:
        raise ValueError(f"Simulação {simulacao_id} não encontrada.")
    return {
        "simulacao": simulacao,
        "resultado": repo.get_resultado(conn, simulacao_id),
        "diario": repo.get_crescimento_diario(conn, simulacao_id),
    }
