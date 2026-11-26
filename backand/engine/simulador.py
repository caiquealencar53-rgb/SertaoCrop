# backend/engine_aquacrop.py
# -*- coding: utf-8 -*-
"""Engine de simulação do SertãoCrop.
Encapsula o AquaCrop-OSPy.
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from aquacrop import (
    AquaCropModel, Crop, InitialWaterContent,
    IrrigationManagement, Soil
)
from aquacrop.utils import prepare_weather


def montar_solo(dados_solo: dict) -> Soil:
    """Recebe o dicionário do banco (ou da interface) e devolve um Soil."""
    solo = Soil("custom")
    for camada in dados_solo["camadas"]:
        solo.add_layer(
            thickness=camada["espessura"],
            thWP=camada["th_wp"],
            thFC=camada["th_fc"],
            thS=camada["th_s"],
            Ksat=camada["ksat"],
            penetrability=camada.get("penetrabilidade", 100),
        )
    return solo


def montar_clima(caminho_arquivo: str) -> pd.DataFrame:
    """Lê o arquivo climático no formato esperado pelo AquaCrop."""
    return prepare_weather(caminho_arquivo)


def montar_cultura(dados_cultura: dict) -> Crop:
    """Recebe o dicionário da cultura e devolve um Crop."""
    return Crop(
        c_name=dados_cultura["nome"],
        planting_date=dados_cultura["data_plantio"],  # formato "MM/DD"
        harvest_date=dados_cultura.get("data_colheita"),
        CCx=dados_cultura.get("ccx"),
        CGC=dados_cultura.get("cgc"),
        CDC=dados_cultura.get("cdc"),
        WP=dados_cultura.get("wp"),
        HI0=dados_cultura.get("hi0"),
    )


def montar_irrigacao(dados_irrigacao: dict) -> IrrigationManagement:
    """Recebe o dicionário do plano de irrigação e devolve IrrigationManagement."""
    metodo = dados_irrigacao.get("metodo", 0)
    if metodo == 3:  # calendário
        agenda = pd.DataFrame({
            "Date": pd.to_datetime(dados_irrigacao["datas"]),
            "Depth": dados_irrigacao["profundidades"],
        })
        return IrrigationManagement(irrigation_method=3, Schedule=agenda)
    if metodo == 1:  # por umidade
        return IrrigationManagement(irrigation_method=1, SMT=dados_irrigacao["smt"])
    return IrrigationManagement(irrigation_method=0)  # sequeiro


def executar_simulacao(
    dados_solo: dict,
    dados_cultura: dict,
    caminho_clima: str,
    dados_irrigacao: dict,
    sim_start: str,
    sim_end: str,
    agua_inicial: str = "FC",
) -> dict:
    """
    Executa a simulação e devolve um dicionário simples e serializável.
    Este é o contrato entre a interface e o AquaCrop.
    """
    try:
        modelo = AquaCropModel(
            sim_start_time=sim_start,
            sim_end_time=sim_end,
            weather_df=montar_clima(caminho_clima),
            soil=montar_solo(dados_solo),
            crop=montar_cultura(dados_cultura),
            initial_water_content=InitialWaterContent(value=[agua_inicial]),
            irrigation_management=montar_irrigacao(dados_irrigacao),
        )
        modelo.run_model(till_termination=True)

        safra = modelo.get_simulation_results().iloc[-1]
        crescimento = modelo.get_crop_growth()

        return {
            "sucesso": True,
            "produtividade": float(safra["Dry yield (tonne/ha)"]),
            "produtividade_potencial": float(safra["Yield potential (tonne/ha)"]),
            "irrigacao_sazonal": float(safra["Seasonal irrigation (mm)"]),
            "evapotranspiracao": float(safra["Seasonal ET (mm)"]),
            "crescimento": crescimento,  # DataFrame bruto (a interface pode plotar)
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def executar_calibracao(
    dados_solo: dict,
    caminho_clima: str,
    dados_irrigacao: dict,
    sim_start: str,
    sim_end: str,
    produtividade_observada: float,
    repeticoes: int = 200,
) -> dict:
    """
    Calibração via SpotPy/SCE-UA.
    Devolve os parâmetros ótimos e o RMSE final.
    """
    try:
        import spotpy

        class _Calibrador:
            def __init__(self):
                self.obs = produtividade_observada
                self.params = [
                    spotpy.parameter.Uniform("WP", 18.0, 40.0),
                    spotpy.parameter.Uniform("CGC", 0.03, 0.09),
                    spotpy.parameter.Uniform("CDC", 0.02, 0.09),
                    spotpy.parameter.Uniform("HI0", 0.20, 0.50),
                ]
                self.clima = montar_clima(caminho_clima)
                self.solo = montar_solo(dados_solo)
                self.irrigacao = montar_irrigacao(dados_irrigacao)

            def parameters(self):
                return spotpy.parameter.generate(self.params)

            def simulation(self, vector):
                wp, cgc, cdc, hi0 = vector
                try:
                    crop = Crop(
                        c_name="Millet", planting_date="02/27",
                        WP=wp, CGC=cgc, CDC=cdc, HI0=hi0,
                    )
                    m = AquaCropModel(
                        sim_start_time=sim_start, sim_end_time=sim_end,
                        weather_df=self.clima, soil=self.solo, crop=crop,
                        initial_water_content=InitialWaterContent(value=["FC"]),
                        irrigation_management=self.irrigacao,
                    )
                    m.run_model(till_termination=True)
                    r = m.get_simulation_results().iloc[-1]
                    return [float(r["Dry yield (tonne/ha)"])]
                except Exception:
                    return [float("nan")]

            def evaluation(self):
                return [self.obs]

            def objectivefunction(self, simulation, evaluation):
                import numpy as np
                if np.isnan(simulation[0]):
                    return 1e6
                return spotpy.objectivefunctions.rmse(evaluation, simulation)

        setup = _Calibrador()
        sampler = spotpy.algorithms.sceua(setup, dbname="calib", dbformat="ram", save_sim=False)
        sampler.sample(repetitions=repeticoes, ngs=7, kstop=5, peps=0.1, pcento=0.1)
        dados = sampler.getdata()
        melhor = spotpy.analyser.get_best_parameterset(dados, maximize=False)
        valores = melhor[0] if isinstance(melhor, list) else melhor
        return {
            "sucesso": True,
            "WP": float(valores[0]),
            "CGC": float(valores[1]),
            "CDC": float(valores[2]),
            "HI0": float(valores[3]),
            "rmse": float(spotpy.analyser.get_best_parameterset(dados, maximize=False)[-1])
                   if hasattr(melhor, "__len__") else 0.0,
        }
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}