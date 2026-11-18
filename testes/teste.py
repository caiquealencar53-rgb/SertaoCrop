# -*- coding: utf-8 -*-
"""Calibração demonstrativa AquaCrop + SPOTPY (adaptada do notebook)."""

import numpy as np
import pandas as pd
import spotpy
from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent, IrrigationManagement
from aquacrop.utils import prepare_weather, get_filepath
import warnings
from pathlib import Path

# Edite este caminho se o arquivo climático estiver em outro local.
WEATHER_FILE = Path(__file__).resolve().parent / "Clima_Serra.txt"

# Ignorar avisos de FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)
# Lista de irrigação: [(data, profundidade), (data, profundidade), ...]
irrigation_list = [
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
    ('2019-06-27', 0.0), ('2019-06-28', 0.0), ('2019-06-29', 0.0), ('2019-06-30', 0.0)
]
# Converter a lista em um DataFrame do Pandas
irrigation_schedule = pd.DataFrame(irrigation_list, columns=['Date', 'Depth'])
irrigation_schedule['Date'] = pd.to_datetime(irrigation_schedule['Date'])

print(type(irrigation_schedule))
print(irrigation_schedule.head())
class AquaCropSpotpy:
    def __init__(self, observed_values):
        self.observed_values = observed_values
        
        # Definição dos parâmetros para calibração
        self.params = [
            spotpy.parameter.Uniform('WP', low=15.0, high=45.0),
            spotpy.parameter.Uniform('CGC', low=0.01, high=0.1),
            spotpy.parameter.Uniform('CDC', low=0.01, high=0.1),
            spotpy.parameter.Uniform('HI0', low=0.1, high=1.0)
        ]
        
        # Configuração do solo
        self.soil = Soil('custom')
        self.soil.add_layer(thickness=0.2, thWP=0.067, thFC=0.151, thS=0.31, Ksat=53.4, penetrability=100)
        self.soil.add_layer(thickness=0.2, thWP=0.072, thFC=0.162, thS=0.31, Ksat=98.1, penetrability=100)
        self.soil.add_layer(thickness=0.2, thWP=0.083, thFC=0.169, thS=0.35, Ksat=121.1, penetrability=100)
        self.soil.add_layer(thickness=0.2, thWP=0.087, thFC=0.181, thS=0.36, Ksat=151.7, penetrability=100)
        
        # O arquivo Clima_Serra.txt deve ficar na mesma pasta deste script.
        self.weather_file_path = WEATHER_FILE
        if not self.weather_file_path.is_file():
            raise FileNotFoundError(
                f"Arquivo climático não encontrado: {self.weather_file_path}\n"
                "Coloque Clima_Serra.txt na mesma pasta do script ou altere WEATHER_FILE."
            )
        self.weather_data = prepare_weather(str(self.weather_file_path))

        # Guardamos uma cópia original da agenda. Cada simulação recebe
        # uma cópia nova para evitar que o AquaCrop/SPOTPY altere a agenda compartilhada.
        self.irrigation_schedule = irrigation_schedule.copy(deep=True)

    def parameters(self):
        return spotpy.parameter.generate(self.params)
        0

    def simulation(self, vector):

        # Criar dicionário com parâmetros da cultura
        crop_kwargs = {
            'c_name': 'Millet',
            'planting_date': '02/27',
            'harvest_date': '05/28',
            'WP': vector[0],
            'CGC': vector[1],
            'CDC': vector[2],
            'HI0': vector[3],
        }

        # Configurar e executar modelo
        initial_water_content = InitialWaterContent(value=['FC'])
        
        try:
            # Definir o modelo AquaCrop
            model = AquaCropModel(
                sim_start_time="2019/02/27",
                sim_end_time="2019/06/30",
                weather_df=self.weather_data,
                soil=self.soil,
                crop=Crop(**crop_kwargs),
                initial_water_content=initial_water_content,
                irrigation_management=IrrigationManagement(
                    irrigation_method=3,
                    Schedule=self.irrigation_schedule.copy(deep=True)
                )
            )

            # Executar o modelo
            model.run_model(till_termination=True)
            
            # Obter resultados
            results = model.get_simulation_results()
            
            # Verificar se a coluna existente
            if 'Yield (tonne/ha)' in results.columns:
                yield_column = 'Yield (tonne/ha)'
            elif 'Yield potential (tonne/ha)' in results.columns:
                yield_column = 'Yield potential (tonne/ha)'
            else:
                print("Colunas disponíveis: ", results.columns)
                return np.array([0.0])  # Retornar um valor padrão se não encontrar a coluna

            # Obter os valores de rendimento
            simulated_values = results[yield_column].values
            
            if len(simulated_values) > 0:
                # Usar o último valor para comparação
                final_yield = simulated_values[-1]
                print(f"Valor simulado final: {final_yield}")
                return np.array([final_yield])
            else:
                print("Nenhum valor de rendimento encontrado")
                return np.array([0.0])
                
        except Exception as e:
            print(f"Erro na simulação: {e}")
            import traceback
            traceback.print_exc()
            return np.array([10000.0])  # Valor alto para ser rejeitado pela função objetivo

    def evaluation(self):
        return self.observed_values

    def objectivefunction(self, simulation, evaluation):
        if simulation[0] == 10000.0:
            return 1000000.0  # Retornar um valor alto para rejeitar esta simulação
        return spotpy.objectivefunctions.rmse(evaluation, simulation)
if __name__ == "__main__":
    # ATENÇÃO: valor demonstrativo do notebook, não é observação real.
    observed_values = np.array([3.0], dtype=float)

    spot_setup = AquaCropSpotpy(observed_values)

    sampler = spotpy.algorithms.sceua(
        spot_setup,
        dbname="SCEUA_AquaCrop",
        dbformat="csv"
    )

    print("Iniciando calibração de teste...")
    # Dez avaliações servem apenas para verificar se o fluxo executa.
    # Para pesquisa, será necessário definir observações, limites e orçamento
    # de avaliações adequados ao experimento.
    sampler.sample(repetitions=10, ngs=7, kstop=3, peps=0.1, pcento=0.1)

    results = sampler.getdata()
    best_params = spotpy.analyser.get_best_parameterset(results, maximize=False)
    param_names = [param.name for param in spot_setup.params]

    if len(best_params) == 0:
        raise RuntimeError("O SPOTPY não retornou parâmetros calibrados.")

    best_row = best_params[0]

    # SPOTPY pode devolver um registro estruturado (campos parWP, parCGC...)
    # ou uma tupla/array, dependendo da versão.
    if getattr(getattr(best_row, "dtype", None), "names", None):
        values = []
        for name in param_names:
            field = "par" + name
            if field in best_row.dtype.names:
                values.append(float(best_row[field]))
            elif name in best_row.dtype.names:
                values.append(float(best_row[name]))
            else:
                raise KeyError(f"Não encontrei o parâmetro {name} no resultado do SPOTPY.")
    else:
        values = np.asarray(best_row, dtype=float).reshape(-1).tolist()
        # Algumas versões retornam uma tupla aninhada dentro do primeiro item.
        if len(values) == 1 and isinstance(best_row[0], (tuple, list, np.ndarray)):
            values = np.asarray(best_row[0], dtype=float).reshape(-1).tolist()

    if len(values) < len(param_names):
        raise RuntimeError(
            f"Quantidade de parâmetros inesperada: {len(values)}. Esperado: {len(param_names)}. "
            f"Resultado recebido: {best_params}"
        )

    print("\nMelhores parâmetros encontrados (resultado de teste):")
    for name, value in zip(param_names, values):
        print(f"{name}: {value:.6f}")

    linhas = [
        "ATENÇÃO: resultado demonstrativo do notebook, não validado cientificamente.",
        "Cultura: Millet",
        "Data de plantio: 2019-02-27",
        "Métrica: RMSE contra um único valor demonstrativo (3.0 t/ha)",
        "Parâmetros encontrados:"
    ]
    linhas.extend(f"{name}: {value:.6f}" for name, value in zip(param_names, values))

    output_file = Path(__file__).resolve().parent / "calibracao_resultados.txt"
    output_file.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nResultado salvo em: {output_file}")
