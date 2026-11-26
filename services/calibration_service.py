# -*- coding: utf-8 -*-
"""Calibração opcional com SpotPy/SCE-UA (funcionalidade preservada).

Os parâmetros retornados são experimentais: não viram "validados" apenas
porque o algoritmo convergiu. A tela exibe esse alerta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import AQUACROP_VERSION
from integracao_aquacrop import adapter, crop_parameters
from services import climate_service, validation


class CalibracaoIndisponivel(RuntimeError):
    pass


def calibrar(config: dict, db_path=None) -> dict:
    from database import connect
    from database import repositories as repo

    with connect(db_path) as conn:
        cultura = crop_parameters.verificar_cultura(conn, int(config["cultura_id"]))
        if cultura["codigo_aquacrop"] not in ("Sorghum", "SorghumGDD"):
            raise CalibracaoIndisponivel(
                "A calibração automatizada só está implementada para Sorghum "
                "(parâmetros CGC_CD/CDC_CD em dias calendário)."
            )
        inicio, plantio, fim = validation.validar_datas(
            config["data_inicio"], config["data_plantio"], config["data_fim"]
        )
        solo = repo.get_solo(conn, int(config["solo_id"]))
        linhas = repo.get_clima(conn, int(config["estacao_id"]),
                                inicio.isoformat(), fim.isoformat())
        weather = climate_service.weather_from_rows(linhas)
        validation.validar_cobertura_clima(weather, inicio.isoformat(), fim.isoformat())
        manejo = repo.get_manejo(conn, int(config["manejo_id"]))
        observado = float(config["produtividade_observada"])
        if observado <= 0:
            raise ValueError("Informe a produtividade observada em campo (maior que zero).")
        experimento_id = int(config["experimento_id"])

    try:
        import spotpy
    except ImportError as exc:
        raise CalibracaoIndisponivel(
            "SpotPy não está instalado. Instale com: pip install spotpy"
        ) from exc

    class _Setup:
        def __init__(self):
            self.params = [
                spotpy.parameter.Uniform("WP", 18.0, 40.0),
                spotpy.parameter.Uniform("CGC_CD", 0.05, 0.30),
                spotpy.parameter.Uniform("CDC_CD", 0.03, 0.30),
                spotpy.parameter.Uniform("HI0", 0.20, 0.55),
            ]

        def parameters(self):
            return spotpy.parameter.generate(self.params)

        def simulation(self, vetor):
            wp, cgc_cd, cdc_cd, hi0 = vetor
            try:
                resultado = adapter.executar(
                    weather_df=weather,
                    solo=solo,
                    verificacao_cultura=cultura,
                    manejo=manejo,
                    data_plantio=plantio.isoformat(),
                    data_inicio=inicio.isoformat(),
                    data_fim=fim.isoformat(),
                    overrides_cultura={
                        "WP": float(wp), "CGC_CD": float(cgc_cd),
                        "CDC_CD": float(cdc_cd), "HI0": float(hi0),
                    },
                )
                return np.array([float(resultado["safra"].iloc[-1]["Dry yield (tonne/ha)"])])
            except Exception:
                return np.array([np.nan])

        def evaluation(self):
            return np.array([observado])

        def objectivefunction(self, simulation, evaluation):
            if np.isnan(simulation[0]):
                return 1e6
            return spotpy.objectivefunctions.rmse(evaluation, simulation)

    repeticoes = max(5, int(config.get("repeticoes", 30)))
    sampler = spotpy.algorithms.sceua(
        _Setup(), dbname="calibracao_sertaocrop", dbformat="ram", save_sim=False
    )
    sampler.sample(repeticoes=repeticoes, ngs=7, kstop=5, peps=0.1, pcento=0.1)
    dados = sampler.getdata()
    melhor = spotpy.analyser.get_best_parameterset(dados, maximize=False)
    valores = np.asarray(melhor[0] if isinstance(melhor, (list, tuple)) else melhor).ravel()
    nomes = ["WP", "CGC_CD", "CDC_CD", "HI0"]
    parametros = {nome: float(valores[i]) for i, nome in enumerate(nomes)}

    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO calibracoes
               (experimento_id, cultura_id, versao_aquacrop, metodo_otimizacao,
                rmse, status)
               VALUES (?, ?, ?, 'SCE-UA', ?, 'EXPERIMENTAL')""",
            (experimento_id, int(config["cultura_id"]), AQUACROP_VERSION, None),
        )
        calibracao_id = cur.lastrowid
        for nome, valor in parametros.items():
            conn.execute(
                """INSERT INTO parametros_calibrados (calibracao_id, nome_parametro, valor_calibrado)
                   VALUES (?, ?, ?)""",
                (calibracao_id, nome, valor),
            )
    return {
        "sucesso": True,
        "calibracao_id": calibracao_id,
        "parametros": parametros,
        "status": "EXPERIMENTAL",
        "observacoes": "Parâmetros ajustados por otimização; não validados cientificamente.",
    }
