# -*- coding: utf-8 -*-
"""Testes de importação, persistência e preparação de clima."""

import pandas as pd

from config.settings import DEMO_WEATHER_PATH
from database import repositories as repo
from services import climate_service
from tests.base import TemporaryDatabaseTest


class TestClimateService(TemporaryDatabaseTest):
    def test_importacao_marcada_como_demonstracao(self):
        estacao_id, total = self.importar_demo()
        self.assertEqual(total, 366)
        with self.conn() as conn:
            estacao = repo.get_estacao(conn, estacao_id)
            linhas = repo.get_clima(conn, estacao_id)
        self.assertEqual(estacao["eh_demonstracao"], 1)
        self.assertEqual(linhas[0]["origem"], "DEMONSTRACAO")
        self.assertEqual(linhas[-1]["data"], "2024-12-31")
        self.assertEqual(linhas[0]["umidade_relativa"], 48.7)
        self.assertEqual(len(linhas), 366)

    def test_ordem_exigida_pelo_aquacrop(self):
        self.importar_demo()
        with self.conn() as conn:
            linhas = repo.get_clima(conn, repo.list_estacoes(conn)[0]["id"])
        weather = climate_service.weather_from_rows(linhas)
        self.assertEqual(
            list(weather.columns),
            ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"],
        )
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(weather["Date"]))
        self.assertGreaterEqual(weather["ReferenceET"].min(), 0.1)

    def test_resumo_sem_valores_inventados(self):
        estacao_id, total = self.importar_demo()
        with self.conn() as conn:
            resumo = climate_service.resumo(repo.get_clima(conn, estacao_id))
        self.assertEqual(resumo["dias"], 366)
        self.assertEqual(resumo["inicio"], "2024-01-01")
        self.assertEqual(resumo["origem"], "DEMONSTRACAO")
        self.assertAlmostEqual(resumo["precipitacao_total_mm"], 2137.1, places=1)

    def test_arquivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            climate_service.ler_csv("nao_existe.csv")

    def test_planilha_invalida_nao_cria_estacao(self):
        caminho = self._tmp.name + "/clima_invalido.csv"
        pd.DataFrame({
            "Date": ["2024-01-01", "2024-01-03"],
            "Tmin": [20, 21], "Tmax": [30, 31], "Rain": [0, 0], "ETo": [4, 4],
        }).to_csv(caminho, index=False)
        with self.conn() as conn:
            with self.assertRaises(ValueError):
                climate_service.importar_csv(conn, caminho, "Inválida", "INV")
            self.assertEqual(repo.list_estacoes(conn), [])

    def test_csv_do_projeto_e_importavel(self):
        dados = climate_service.ler_csv(DEMO_WEATHER_PATH)
        normalizado = climate_service.weather_from_dataframe(dados)
        self.assertEqual(len(normalizado), 366)
        self.assertEqual(normalizado["Date"].iloc[0], pd.Timestamp("2024-01-01"))
