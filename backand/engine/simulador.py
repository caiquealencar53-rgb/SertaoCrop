
import sqlite3
import pandas as pd
from datetime import datetime

from aquacrop import (
    AquaCropModel,
    Soil,
    Crop,
    InitialWaterContent,
    IrrigationManagement
)


BANCO = "sertaocrop.db"


# =====================================================
# 1. CONEXÃO E CONSULTAS
# =====================================================

def conectar():
    con = sqlite3.connect(BANCO)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def buscar_simulacao(simulacao_id):

    con = conectar()

    sql = """
    SELECT
        s.*,
        c.nome AS cultura,
        so.nome AS solo,
        so.codigo_aquacrop,
        m.nome AS manejo,
        m.metodo,
        m.limite_umidade,
        m.lamina_irrigacao
    FROM simulacoes s
    JOIN culturas c ON c.id = s.cultura_id
    JOIN solos so ON so.id = s.solo_id
    JOIN manejo_irrigacao m ON m.id = s.manejo_id
    WHERE s.id = ?
    """

    df = pd.read_sql_query(sql, con, params=(simulacao_id,))
    con.close()

    if df.empty:
        raise ValueError("Simulação não encontrada.")

    return df.iloc[0]


# =====================================================
# 2. BUSCAR PARÂMETROS DA CULTURA
# =====================================================

def buscar_parametros_cultura(cultura_id):

    con = conectar()

    sql = """
    SELECT *
    FROM parametros_cultura
    WHERE cultura_id = ?
    """

    df = pd.read_sql_query(sql, con, params=(cultura_id,))
    con.close()

    if df.empty:
        raise ValueError(
            "A cultura ainda não possui parâmetros cadastrados."
        )

    parametros = df.iloc[0].to_dict()

    parametros.pop("id", None)
    parametros.pop("cultura_id", None)

    obrigatorios = [
        "CCx", "CGC", "CDC", "WP", "HI0",
        "Kcb", "Zmin", "Zmax", "PlantPop",
        "EmergenceCD", "MaxRootingCD",
        "SenescenceCD", "MaturityCD",
        "HIstartCD", "YldFormCD"
    ]

    for nome in obrigatorios:
        valor = parametros.get(nome)

        if valor is None or pd.isna(valor):
            raise ValueError(
                f"Parâmetro {nome} não cadastrado para a cultura."
            )

    return parametros


# =====================================================
# 3. BUSCAR DADOS CLIMÁTICOS
# =====================================================

def buscar_clima(estacao_id, inicio, fim):

    con = conectar()

    sql = """
    SELECT
        data AS Date,
        temperatura_min AS MinTemp,
        temperatura_max AS MaxTemp,
        precipitacao AS Precipitation,
        eto AS ReferenceET
    FROM dados_climaticos
    WHERE estacao_id = ?
      AND data BETWEEN ? AND ?
    ORDER BY data
    """

    clima = pd.read_sql_query(
        sql,
        con,
        params=(estacao_id, inicio, fim)
    )

    con.close()

    if clima.empty:
        raise ValueError("Não existem dados climáticos para o período.")

    clima["Date"] = pd.to_datetime(clima["Date"])

    if clima.isnull().any().any():
        raise ValueError("Existem dados climáticos incompletos.")

    clima = clima.sort_values("Date").reset_index(drop=True)

    # O modelo precisa de dados diários.
    dias = pd.date_range(
        start=inicio,
        end=fim,
        freq="D"
    )

    if not clima["Date"].equals(pd.Series(dias, name="Date")):
        raise ValueError(
            "A série climática possui dias ausentes ou duplicados."
        )

    return clima


# =====================================================
# 4. CONSTRUIR PERFIL DO SOLO
# =====================================================

def construir_solo(solo_id):

    con = conectar()

    sql = """
    SELECT *
    FROM dado_solos
    WHERE solo_id = ?
    ORDER BY numero_camada
    """

    camadas = pd.read_sql_query(
        sql,
        con,
        params=(solo_id,)
    )

    con.close()

    if camadas.empty:
        raise ValueError("O solo não possui camadas cadastradas.")

    solo = Soil(soil_type="custom")

    profundidade_acumulada = 0

    for _, camada in camadas.iterrows():

        valores = [
            camada["espessura"],
            camada["th_wp"],
            camada["th_fc"],
            camada["th_s"],
            camada["ksat"],
            camada["penetrabilidade"]
        ]

        if any(pd.isna(v) for v in valores):
            raise ValueError("Existem propriedades de solo incompletas.")

        profundidade_acumulada += camada["espessura"]

        solo.add_layer(
            thickness=profundidade_acumulada,
            thWP=camada["th_wp"],
            thFC=camada["th_fc"],
            thS=camada["th_s"],
            Ksat=camada["ksat"],
            penetrability=camada["penetrabilidade"]
        )

    return solo


# =====================================================
# 5. CONSTRUIR MANEJO DE IRRIGAÇÃO
# =====================================================

def construir_irrigacao(simulacao):

    metodo = int(simulacao["metodo"])

    if metodo == 0:

        return IrrigationManagement(
            irrigation_method=0
        )

    elif metodo == 1:

        limite = simulacao["limite_umidade"]

        if pd.isna(limite):
            raise ValueError("Limite de umidade não cadastrado.")

        return IrrigationManagement(
            irrigation_method=1,
            SMT=[float(limite)] * 4
        )

    elif metodo == 3:

        con = conectar()

        sql = """
        SELECT data AS Date, lamina AS Depth
        FROM agenda_irrigacao
        WHERE manejo_id = ?
        ORDER BY data
        """

        agenda = pd.read_sql_query(
            sql,
            con,
            params=(simulacao["manejo_id"],)
        )

        con.close()

        if agenda.empty:
            raise ValueError("Agenda de irrigação vazia.")

        agenda["Date"] = pd.to_datetime(agenda["Date"])

        return IrrigationManagement(
            irrigation_method=3,
            Schedule=agenda
        )

    else:
        raise ValueError("Método de irrigação não implementado.")


# =====================================================
# 6. ATUALIZAR STATUS
# =====================================================

def atualizar_status(simulacao_id, status):

    con = conectar()

    con.execute(
        """
        UPDATE simulacoes
        SET status = ?
        WHERE id = ?
        """,
        (status, simulacao_id)
    )

    con.commit()
    con.close()


# =====================================================
# 7. SALVAR RESULTADOS
# =====================================================

def salvar_resultados(simulacao_id, resultados, crescimento):

    con = conectar()

    # Impede duplicação caso a simulação seja executada novamente.
    con.execute(
        "DELETE FROM resultados WHERE simulacao_id = ?",
        (simulacao_id,)
    )

    con.execute(
        "DELETE FROM crescimento_diario WHERE simulacao_id = ?",
        (simulacao_id,)
    )

    con.execute(
        """
        INSERT INTO resultados (
            simulacao_id,
            produtividade,
            produtividade_potencial,
            irrigacao_sazonal,
            biomassa,
            indice_colheita
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        resultados
    )

    crescimento.to_sql(
        "crescimento_diario",
        con,
        if_exists="append",
        index=False
    )

    con.commit()
    con.close()


# =====================================================
# 8. EXECUTAR AQUACROP
# =====================================================

def executar_simulacao(simulacao_id):

    print("\n========== SERTÃOCROP ==========")

    simulacao = buscar_simulacao(simulacao_id)

    atualizar_status(simulacao_id, "EXECUTANDO")

    try:

        print("\n1. CONSULTANDO PARÂMETROS...")

        parametros = buscar_parametros_cultura(
            simulacao["cultura_id"]
        )

        print("Cultura:", simulacao["cultura"])

        print("\n2. CONSULTANDO CLIMA...")

        clima = buscar_clima(
            simulacao["estacao_id"],
            simulacao["data_inicio"],
            simulacao["data_fim"]
        )

        print("Dias climáticos:", len(clima))

        print("\n3. CONSTRUINDO SOLO...")

        solo = construir_solo(
            simulacao["solo_id"]
        )

        print("\n4. CONFIGURANDO CULTURA...")

        data_plantio = pd.to_datetime(
            simulacao["data_plantio"]
        )

        plantio = data_plantio.strftime("%m/%d")

        # Cultura customizada com parâmetros obtidos do banco.
        cultura = Crop(
            "custom",
            planting_date=plantio,
            **parametros
        )

        print("\n5. CONFIGURANDO IRRIGAÇÃO...")

        irrigacao = construir_irrigacao(simulacao)

        print("\n6. DEFININDO ÁGUA INICIAL...")

        agua_inicial = InitialWaterContent(
            value=[simulacao["umidade_inicial"]]
        )

        print("\n7. CRIANDO MODELO AQUACROP...")

        modelo = AquaCropModel(
            sim_start_time=pd.to_datetime(
                simulacao["data_inicio"]
            ).strftime("%Y/%m/%d"),

            sim_end_time=pd.to_datetime(
                simulacao["data_fim"]
            ).strftime("%Y/%m/%d"),

            weather_df=clima,
            soil=solo,
            crop=cultura,
            initial_water_content=agua_inicial,
            irrigation_management=irrigacao
        )

        print("\n8. EXECUTANDO SIMULAÇÃO...")

        modelo.run_model(till_termination=True)

        # Resultado final da safra.
        resultado = modelo.get_simulation_results()

        if resultado is False or resultado.empty:
            raise RuntimeError("O AquaCrop não produziu resultado final.")

        linha = resultado.iloc[-1]

        produtividade = float(
            linha["Dry yield (tonne/ha)"]
        )

        produtividade_potencial = float(
            linha["Yield potential (tonne/ha)"]
        )

        irrigacao_sazonal = float(
            linha["Seasonal irrigation (mm)"]
        )

        crescimento = modelo.get_crop_growth().copy()

        # Guarda a data correspondente a cada passo diário.
        crescimento["data"] = (
            pd.to_datetime(simulacao["data_inicio"])
            + pd.to_timedelta(
                crescimento["time_step_counter"],
                unit="D"
            )
        ).dt.strftime("%Y-%m-%d")

        crescimento = crescimento.rename(
            columns={
                "dap": "dap",
                "canopy_cover": "cobertura_dossel",
                "biomass": "biomassa"
            }
        )

        crescimento = crescimento[
            ["data", "dap", "cobertura_dossel", "biomassa"]
        ].copy()

        crescimento["simulacao_id"] = simulacao_id

        # Ajusta a ordem para corresponder à tabela SQL.
        crescimento = crescimento[
            [
                "simulacao_id",
                "data",
                "dap",
                "cobertura_dossel",
                "biomassa"
            ]
        ]

        biomassa = float(
            crescimento["biomassa"].iloc[-1]
        )

        indice_colheita = float(
            linha["Dry yield (tonne/ha)"]
            / biomassa * 100
        ) if biomassa > 0 else 0

        dados_resultado = (
            simulacao_id,
            produtividade,
            produtividade_potencial,
            irrigacao_sazonal,
            biomassa,
            indice_colheita
        )

        print("\n9. SALVANDO RESULTADOS...")

        salvar_resultados(
            simulacao_id,
            dados_resultado,
            crescimento
        )

        atualizar_status(simulacao_id, "CONCLUIDA")

        print("\n========== SIMULAÇÃO CONCLUÍDA ==========")

        print("Produtividade:", produtividade, "ton/ha")
        print("Biomassa:", biomassa, "ton/ha")
        print("Irrigação sazonal:", irrigacao_sazonal, "mm")

        return resultado

    except Exception as erro:

        atualizar_status(simulacao_id, "ERRO")

        print("\nERRO NA SIMULAÇÃO:")
        print(erro)

        raise


# =====================================================
# 9. EXECUÇÃO
# =====================================================

if __name__ == "__main__":

    # Informe o ID de uma simulação já cadastrada.
    executar_simulacao(1)
