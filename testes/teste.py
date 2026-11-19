"""
Módulo de calibração do SertãoCrop
Calibra parâmetros do AquaCrop-OSPy (v3.1.0) usando SpotPy (SCE-UA)
para a cultura de milheto no Semiárido.
"""

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import numpy as np
import pandas as pd
import spotpy
from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent, IrrigationManagement
from aquacrop.utils import prepare_weather

# ============================================================
# 1. DADOS DE ENTRADA (FIXOS)
# ============================================================

# Cronograma de irrigação (Data, Profundidade em mm)
IRRIGATION_LIST = [
    ('2019-02-27', 2.1), ('2019-02-28', 0.0), ('2019-03-01', 3.0), ('2019-03-02', 0.0),
    ('2019-03-03', 0.0), ('2019-03-04', 4.4), ('2019-03-05', 0.0), ('2019-03-06', 1.3),
    ('2019-03-07', 0.0), ('2019-03-08', 3.5), ('2019-03-09', 0.0), ('2019-03-10', 0.0),
    ('2019-03-11', 6.6), ('2019-03-12', 0.0), ('2019-03-13', 2.5), ('2019-03-14', 0.0),
    ('2019-03-15', 0.0), ('2019-03-16', 0.0), ('2019-03-17', 0.0), ('2019-03-18', 6.2),
    ('2019-03-19', 0.0), ('2019-03-20', 2.6), ('2019-03-21', 0.0), ('2019-03-22', 4.1),
    ('2019-03-23', 0.0), ('2019-03-24', 0.0), ('2019-03-25', 0.6), ('2019-03-26', 0.0),
    ('2019-03-27', 1.9), ('2019-03-28', 0.0), ('2019-03-29', 1.8), ('2019-03-30', 0.0),
    ('2019-03-31', 0.0), ('2019-04-01', 2.1), ('2019-04-02', 0.0), ('2019-04-03', 3.1),
    ('2019-04-04', 0.0), ('2019-04-05', 0.0), ('2019-04-06', 0.0), ('2019-04-07', 0.0),
    ('2019-04-08', 1.5), ('2019-04-09', 0.0), ('2019-04-10', 1.4), ('2019-04-11', 0.0),
    ('2019-04-12', 1.7), ('2019-04-13', 0.0), ('2019-04-14', 0.0), ('2019-04-15', 5.2),
    ('2019-04-16', 0.0), ('2019-04-17', 1.6), ('2019-04-18', 0.0), ('2019-04-19', 3.7),
    ('2019-04-20', 0.0), ('2019-04-21', 0.0), ('2019-04-22', 1.8), ('2019-04-23', 0.0),
    ('2019-04-24', 1.9), ('2019-04-25', 0.0), ('2019-04-26', 3.0), ('2019-04-27', 0.0),
    ('2019-04-28', 0.0), ('2019-04-29', 4.9), ('2019-04-30', 0.0), ('2019-05-01', 0.9),
    ('2019-05-02', 0.0), ('2019-05-03', 2.5), ('2019-05-04', 0.0), ('2019-05-05', 0.0),
    ('2019-05-06', 5.5), ('2019-05-07', 0.0), ('2019-05-08', 3.6), ('2019-05-09', 0.0),
    ('2019-05-10', 0.0), ('2019-05-11', 0.0), ('2019-05-12', 4.3), ('2019-05-13', 0.0),
    ('2019-05-14', 2.8), ('2019-05-15', 0.0), ('2019-05-16', 1.3), ('2019-05-17', 0.0),
    ('2019-05-18', 0.0), ('2019-05-19', 3.0), ('2019-05-20', 0.0), ('2019-05-21', 2.3),
    ('2019-05-22', 0.0), ('2019-05-23', 2.5), ('2019-05-24', 0.0), ('2019-05-25', 0.0),
    ('2019-05-26', 3.7), ('2019-05-27', 0.0), ('2019-05-28', 0.0), ('2019-05-29', 0.0),
    ('2019-05-30', 0.0), ('2019-05-31', 0.0), ('2019-06-01', 0.0), ('2019-06-02', 0.0),
    ('2019-06-03', 0.0), ('2019-06-04', 0.0), ('2019-06-05', 0.0), ('2019-06-06', 0.0),
    ('2019-06-07', 0.0), ('2019-06-08', 0.0), ('2019-06-09', 0.0), ('2019-06-10', 0.0),
    ('2019-06-11', 0.0), ('2019-06-12', 0.0), ('2019-06-13', 0.0), ('2019-06-14', 0.0),
    ('2019-06-15', 0.0), ('2019-06-16', 0.0), ('2019-06-17', 0.0), ('2019-06-18', 0.0),
    ('2019-06-19', 0.0), ('2019-06-20', 0.0), ('2019-06-21', 0.0), ('2019-06-22', 0.0),
    ('2019-06-23', 0.0), ('2019-06-24', 0.0), ('2019-06-25', 0.0), ('2019-06-26', 0.0),
    ('2019-06-27', 0.0), ('2019-06-28', 0.0), ('2019-06-29', 0.0), ('2019-06-30', 0.0),
]

IRRIGATION_DF = pd.DataFrame(IRRIGATION_LIST, columns=['Date', 'Depth'])
IRRIGATION_DF['Date'] = pd.to_datetime(IRRIGATION_DF['Date'])

# Caminho do arquivo climático (ajuste se necessário)
WEATHER_FILE = "Clima_Serra.txt"

# Período de simulação
SIM_START = "2019/02/27"
SIM_END   = "2019/06/30"

# Cultura
CROP_NAME     = "Millet"
PLANTING_DATE = "02/27"
HARVEST_DATE  = "05/28"

# Valor observado (rendimento final em t/ha)
# ⚠️ SUBSTITUA pelo valor real do experimento GAS/UFRPE
OBSERVED_YIELD = 3.0


# ============================================================
# 2. CLASSE DE CALIBRAÇÃO
# ============================================================

class AquaCropSpotpy:
    """
    Wrapper do AquaCrop-OSPy para calibração com SpotPy.
    Cada chamada de simulation() cria objetos novos para evitar
    corrupção de estado interno da biblioteca.
    """

    def __init__(self, observed_yield: float):
        self.observed_yield = observed_yield

        # Dados climáticos (carregados uma vez)
        self.weather_data = prepare_weather(WEATHER_FILE)

        # Parâmetros a calibrar (com limites fisicamente realistas)
        self.params = [
            spotpy.parameter.Uniform('WP',  low=18.0, high=40.0),
            spotpy.parameter.Uniform('CGC', low=0.03, high=0.09),
            spotpy.parameter.Uniform('CDC', low=0.02, high=0.09),
            spotpy.parameter.Uniform('HI0', low=0.20, high=0.50),
        ]

    def parameters(self):
        return spotpy.parameter.generate(self.params)

    def _build_soil(self):
        """Cria um novo objeto Soil a cada simulação."""
        soil = Soil('custom')
        soil.add_layer(thickness=0.2, thWP=0.067, thFC=0.151, thS=0.31, Ksat=53.4,  penetrability=100)
        soil.add_layer(thickness=0.2, thWP=0.072, thFC=0.162, thS=0.31, Ksat=98.1,  penetrability=100)
        soil.add_layer(thickness=0.2, thWP=0.083, thFC=0.169, thS=0.35, Ksat=121.1, penetrability=100)
        soil.add_layer(thickness=0.2, thWP=0.087, thFC=0.181, thS=0.36, Ksat=151.7, penetrability=100)
        return soil

    def _build_irrigation(self):
        """Cria um novo objeto IrrigationManagement a cada simulação."""
        return IrrigationManagement(
            irrigation_method=3,
            Schedule=IRRIGATION_DF.copy()
        )

    def simulation(self, vector):
        """Executa o modelo e retorna o rendimento final simulado."""
        wp, cgc, cdc, hi0 = vector

        crop = Crop(
            c_name=CROP_NAME,
            planting_date=PLANTING_DATE,
            harvest_date=HARVEST_DATE,
            WP=wp,
            CGC=cgc,
            CDC=cdc,
            HI0=hi0,
        )

        try:
            model = AquaCropModel(
                sim_start_time=SIM_START,
                sim_end_time=SIM_END,
                weather_df=self.weather_data,
                soil=self._build_soil(),
                crop=crop,
                initial_water_content=InitialWaterContent(value=['FC']),
                irrigation_management=self._build_irrigation(),
            )
            model.run_model(till_termination=True)
            results = model.get_simulation_results()

            yield_col = 'Yield (tonne/ha)'
            if yield_col not in results.columns:
                return np.array([np.nan])

            return np.array([results[yield_col].values[-1]])

        except Exception:
            return np.array([np.nan])

    def evaluation(self):
        return np.array([self.observed_yield])

    def objectivefunction(self, simulation, evaluation):
        if np.isnan(simulation[0]):
            return 1e6
        return spotpy.objectivefunctions.rmse(evaluation, simulation)


# ============================================================
# 3. EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    setup = AquaCropSpotpy(OBSERVED_YIELD)

    sampler = spotpy.algorithms.sceua(
        setup,
        dbname='SCEUA_AquaCrop',
        dbformat='ram',   # mais rápido que CSV
        save_sim=False,
    )

    print("Iniciando calibração SCE-UA...")
    sampler.sample(
        repetitions=200,  # aumente para 500-1000 na versão final
        ngs=7,
        kstop=5,
        peps=0.1,
        pcento=0.1,
    )

    results = sampler.getdata()
    best = spotpy.analyser.get_best_parameterset(results, maximize=False)

    # Extração robusta dos valores
    if isinstance(best, np.ndarray) and best.dtype == object:
        best_values = best[0]
    elif isinstance(best, np.ndarray) and best.ndim == 2:
        best_values = best[0]
    else:
        best_values = best

    param_names = [p.name for p in setup.params]

    print("\n===== RESULTADO FINAL =====")
    output_lines = [
        f"Cultura: {CROP_NAME}",
        f"Data de plantio: 2019-{PLANTING_DATE.replace('/', '-')}",
        f"Rendimento observado: {OBSERVED_YIELD:.3f} t/ha",
        "Parâmetros calibrados:",
    ]
    for name, value in zip(param_names, best_values):
        output_lines.append(f"  {name}: {float(value):.6f}")

    text = "\n".join(output_lines)
    print(text)

    with open('calibracao_resultados.txt', 'w', encoding='utf-8') as f:
        f.write(text)

    # Salva também em CSV estruturado
    pd.DataFrame([best_values], columns=param_names).to_csv(
        'calibracao_resultados.csv', index=False
    )

    print("\nArquivos salvos: calibracao_resultados.txt / .csv")