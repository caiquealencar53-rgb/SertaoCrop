# -*- coding: utf-8 -*-
"""Roteiro de estudo da API do AquaCrop-OSPy (pacote `aquacrop` 3.x). Roda offline.

Como usar: leia de cima para baixo; cada seção imprime o que está explicando.
    pip install aquacrop pandas
    python estudo_api_aquacrop.py

Mapa mental da API (são só 5 peças + o modelo):
    clima  (DataFrame)          -> prepare_weather(arquivo)
    Soil(...)                   -> solo e suas camadas
    Crop(...)                   -> cultura, data de plantio e parâmetros
    InitialWaterContent(...)    -> água no solo no primeiro dia
    IrrigationManagement(...)   -> como irrigar (ou não)
    AquaCropModel(...)          -> junta tudo; .run_model(); .get_*() devolve os resultados
"""
import warnings

import pandas as pd
from aquacrop import AquaCropModel, Crop, InitialWaterContent, IrrigationManagement, Soil
from aquacrop.utils import get_filepath, prepare_weather

warnings.filterwarnings("ignore")
pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 12)


def secao(titulo: str) -> None:
    print("\n" + "=" * 78 + f"\n{titulo}\n" + "=" * 78)


# ---------------------------------------------------------------------------------------------
secao("1) CLIMA – um DataFrame com colunas em ORDEM FIXA (o AquaCrop lê por posição!)")
clima = prepare_weather(get_filepath("tunis_climate.txt"))
print(clima.head(3))
print("colunas, nesta ordem:", list(clima.columns))
print(f"período: {clima['Date'].min():%d/%m/%Y} a {clima['Date'].max():%d/%m/%Y}  ({len(clima)} dias)")
print("Para usar o SEU clima: monte um DataFrame com estas mesmas colunas (Date por último).")

# ---------------------------------------------------------------------------------------------
secao("2) SOLO – nome pronto OU camadas suas (é o que o banco do SertãoCrop vai alimentar)")
solo = Soil("SandyLoam")
print(solo.profile[["dz", "th_wp", "th_fc", "th_s", "Ksat"]].head(3))
print("th_wp = ponto de murcha | th_fc = capacidade de campo | th_s = saturação (sempre wp < fc < s)")

solo_proprio = Soil("custom")
for _ in range(4):  # 4 camadas de 0,2 m: espessura, th_wp, th_fc, th_s, Ksat, penetrabilidade
    solo_proprio.add_layer(0.2, 0.11, 0.24, 0.42, 900, 100)
p = solo_proprio.profile
print(f"solo próprio: {len(p)} compartimentos de {p.dz.iloc[0]} m, th_wp={p.th_wp.iloc[0]}, th_fc={p.th_fc.iloc[0]}, th_s={p.th_s.iloc[0]}")
print("(o AquaCrop divide as suas camadas em compartimentos; é normal haver mais compartimentos que camadas)")

# ---------------------------------------------------------------------------------------------
secao("3) CULTURA – o nome escolhe um conjunto de parâmetros; você pode sobrescrever qualquer um")
sorgo = Crop("Sorghum", planting_date="03/01")          # data no formato MM/DD
print("Obs.: CGC e CDC aparecem como -9,0 aqui. É um marcador de 'calcular depois':")
print("      o AquaCrop os calcula a partir dos graus-dia quando o modelo inicializa.")
for par in ("CCx", "CGC", "CDC", "WP", "HI0", "Zmax"):
    if hasattr(sorgo, par):
        print(f"  {par:5s} = {getattr(sorgo, par)}")
print("Milheto NÃO vem pronto. Teste:")
for nome in ("Millet", "PearlMillet"):
    try:
        Crop(nome, planting_date="03/01")
        print(f"  {nome}: existe")
    except Exception as e:
        print(f"  {nome}: não existe ({type(e).__name__}) -> precisa de parâmetros próprios")
sorgo_ajustado = Crop("Sorghum", planting_date="03/01", CCx=0.70)   # sobrescrevendo um parâmetro
print("CCx original:", sorgo.CCx, "| ajustado:", sorgo_ajustado.CCx)

# ---------------------------------------------------------------------------------------------
secao("4) RODAR – uma função que monta e executa, para comparar cenários de irrigação")


def rodar(irrigacao: IrrigationManagement, cultura: Crop = None, solo_usado: Soil = None) -> AquaCropModel:
    m = AquaCropModel(
        sim_start_time="1990/03/01", sim_end_time="1990/09/30",   # o clima precisa cobrir este período
        weather_df=clima,
        soil=solo_usado or Soil("SandyLoam"),
        crop=cultura or Crop("Sorghum", planting_date="03/01"),
        initial_water_content=InitialWaterContent(value=["FC"]),  # FC = começa na capacidade de campo
        irrigation_management=irrigacao,
    )
    m.run_model(till_termination=True)   # roda até a colheita/maturidade
    return m


agenda = pd.DataFrame({"Date": pd.to_datetime(["1990-03-25", "1990-04-15", "1990-05-06"]), "Depth": [30, 30, 30]})
cenarios = {
    "sequeiro (método 0)": IrrigationManagement(irrigation_method=0),
    "por umidade 70% (método 1)": IrrigationManagement(irrigation_method=1, SMT=[70] * 4),
    "calendário 3x30 mm (método 3)": IrrigationManagement(irrigation_method=3, Schedule=agenda),
}
modelos, linhas = {}, []
for nome, irr in cenarios.items():
    modelos[nome] = rodar(irr)
    r = modelos[nome].get_simulation_results().iloc[-1]
    linhas.append({"cenário": nome, "produtividade (t/ha)": round(r["Dry yield (tonne/ha)"], 2),
                   "potencial (t/ha)": round(r["Yield potential (tonne/ha)"], 2),
                   "irrigação (mm)": round(r["Seasonal irrigation (mm)"], 0)})
print(pd.DataFrame(linhas).to_string(index=False))

# ---------------------------------------------------------------------------------------------
secao("5) RESULTADOS – quatro tabelas, cada uma responde uma pergunta")
m = modelos["calendário 3x30 mm (método 3)"]
safra = m.get_simulation_results()
print("a) get_simulation_results(): UMA linha por safra ->", list(safra.columns))
cresc = m.get_crop_growth()
print("\nb) get_crop_growth(): diário ->", list(cresc.columns))
print("   (dap = dias após plantio; dap = 0 são dias FORA da safra, filtre com dap >= 1)")
print("   canopy_cover vem em fração 0–1; biomass em g/m² (÷100 = t/ha)")
armaz = m.get_water_storage()
print("\nc) get_water_storage(): umidade por camada ->", list(armaz.columns)[:6], "...")
fluxo = m.get_water_flux()
print("\nd) get_water_flux(): evaporação, transpiração, escoamento... ->", list(fluxo.columns)[:10], "...")

# ---------------------------------------------------------------------------------------------
secao("6) CONFERINDO UMA REGRA – biomassa final x índice de colheita = produtividade")
c = cresc[cresc.dap >= 1].iloc[-1]
print(f"biomassa/100 x HI = {c.biomass / 100 * c.harvest_index_adj:.3f} t/ha | "
      f"produtividade informada = {safra.iloc[-1]['Dry yield (tonne/ha)']:.3f} t/ha")

print("\nPróximo passo: ligar isso ao banco (solo = tabelas perfil_solo/camada_solo; clima = dado_climatico;"
      "\nirrigação = plano_irrigacao/evento_irrigacao) dentro de backend/engine/, SEM Qt.")