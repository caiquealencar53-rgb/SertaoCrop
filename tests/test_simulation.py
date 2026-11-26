# -*- coding: utf-8 -*-
"""Testes de integração: AquaCrop real -> Pandas -> SQLite -> recuperação."""

from aquacrop.entities.crop import crop_params

from config.settings import AQUACROP_VERSION
from database import repositories as repo
from integracao_aquacrop import adapter, crop_parameters
from services import simulation_service, validation
from tests.base import TemporaryDatabaseTest


class TestCatalogoCulturas(TemporaryDatabaseTest):
    def test_aquacrop_nao_tem_milheto(self):
        self.assertIn("Sorghum", crop_params)
        self.assertNotIn("Millet", crop_params)
        self.assertNotIn("PearlMillet", crop_params)
        self.assertNotIn("Milheto", crop_parameters.culturas_suportadas())

    def test_cultura_nao_parametrizada_bloqueia_simulacao(self):
        self.importar_demo()
        config = self.config_simulacao()
        with self.conn() as conn:
            config["cultura_id"] = repo.get_cultura_por_nome(conn, "Milheto")["id"]
        with self.assertRaisesRegex(ValueError, "não possui parametrização"):
            simulation_service.executar(config, db_path=self.db_path)
        with self.conn() as conn:
            self.assertEqual(repo.list_simulacoes(conn), [])

    def test_sorgo_tem_parametros_embutidos(self):
        with self.conn() as conn:
            cultura_id = repo.get_cultura_por_nome(conn, "Sorgo")["id"]
            info = crop_parameters.verificar_cultura(conn, cultura_id)
        self.assertEqual(info["codigo_aquacrop"], "Sorghum")
        self.assertFalse(info["calibrada_localmente"])
        self.assertIn(AQUACROP_VERSION, info["origem"])


class TestSimulacaoReal(TemporaryDatabaseTest):
    def test_execucao_persistencia_e_recuperacao(self):
        self.importar_demo()
        config = self.config_simulacao()
        resultado = simulation_service.executar(config, db_path=self.db_path)

        self.assertTrue(resultado["sucesso"])
        self.assertTrue(resultado["metadados"]["concluido"])
        self.assertEqual(resultado["metadados"]["aquacrop_version"], AQUACROP_VERSION)
        self.assertEqual(resultado["metadados"]["cultura"], "Sorghum")
        self.assertAlmostEqual(resultado["metricas"]["produtividade"], 9.1776, places=2)

        with self.conn() as conn:
            simulacao = repo.get_simulacao(conn, resultado["simulacao_id"])
            metricas = repo.get_resultado(conn, resultado["simulacao_id"])
            diario = repo.get_crescimento_diario(conn, resultado["simulacao_id"])
            historico = repo.list_simulacoes(conn)

        self.assertEqual(simulacao["status"], "CONCLUIDA")
        self.assertIsNone(simulacao["erro"])
        self.assertAlmostEqual(metricas["produtividade"], 9.1776, places=2)
        self.assertEqual(metricas["unidade_produtividade"], "tonne/ha")
        self.assertGreater(len(diario), 90)
        self.assertEqual(historico[0]["cultura_nome"], "Sorgo")
        self.assertEqual(historico[0]["status"], "CONCLUIDA")

        with self.conn() as conn:
            recuperado = simulation_service.consultar_resultado(conn, resultado["simulacao_id"])
        self.assertEqual(recuperado["simulacao"]["id"], resultado["simulacao_id"])
        self.assertEqual(len(recuperado["diario"]), len(diario))
        self.assertIn("ET, WP e transpiração relativa", recuperado["resultado"]["observacoes"])

    def test_datas_derivadas_da_serie_real(self):
        self.importar_demo()
        resultado = simulation_service.executar(
            self.config_simulacao(), db_path=self.db_path
        )
        diario = resultado["diario"]
        self.assertIn("data", diario.columns)
        self.assertTrue((diario["data"] >= "2024-01-01").all())
        self.assertTrue((diario["data"] <= "2024-12-31").all())
        self.assertGreater(diario["biomassa_t_ha"].iloc[-1], 0)

    def test_falha_apos_validacao_e_registrada_como_erro(self):
        self.importar_demo()
        config = self.config_simulacao()
        config["data_colheita"] = "2024-02-30"  # data impossível: falha no adaptador
        with self.assertRaises(simulation_service.FalhaSimulacao):
            simulation_service.executar(config, db_path=self.db_path)
        with self.conn() as conn:
            simulacoes = repo.list_simulacoes(conn)
            self.assertEqual(len(simulacoes), 1)
            self.assertEqual(simulacoes[0]["status"], "ERRO")
            self.assertTrue(simulacoes[0]["erro"])
            self.assertIsNone(repo.get_resultado(conn, simulacoes[0]["id"]))


class TestIrrigacaoReais(TemporaryDatabaseTest):
    def test_intervalo_cadastrado_e_usado(self):
        with self.conn() as conn:
            manejo_id = repo.add_manejo(
                conn, "Intervalo 7 dias", 2, lamina_irrigacao=20, intervalo=7
            )
            manejo = repo.get_manejo(conn, manejo_id)
        irrigacao = adapter.preparar_irrigacao(
            {**manejo, "_inicio": "2024-01-01", "_fim": "2024-12-31"}
        )
        self.assertEqual(int(irrigacao.IrrInterval), 7)

    def test_limite_de_umidade_usado_nos_estagios(self):
        irrigacao = adapter.preparar_irrigacao({
            "metodo_aquacrop": 1, "limite_umidade": 65,
            "_inicio": "2024-01-01", "_fim": "2024-12-31",
        })
        self.assertEqual(list(irrigacao.SMT), [65, 65, 65, 65])

    def test_calendario_usa_datas_e_laminas_reais(self):
        irrigacao = adapter.preparar_irrigacao({
            "metodo_aquacrop": 3,
            "agenda": [{"data": "2024-03-25", "lamina": 30}],
            "_inicio": "2024-01-01", "_fim": "2024-12-31",
        })
        self.assertEqual(list(irrigacao.Schedule["Depth"]), [30])
        self.assertEqual(
            str(irrigacao.Schedule["Date"].iloc[0].date()), "2024-03-25"
        )

    def test_condicao_inicial_por_percentual(self):
        agua = adapter.preparar_agua_inicial("Pct", 60, 3)
        self.assertEqual(list(agua.value), [60, 60, 60])
        with self.assertRaises(ValueError):
            adapter.preparar_agua_inicial("Pct", None, 3)

    def test_validacao_irrigacao_rejeita_intervalo_invalido(self):
        with self.assertRaises(ValueError):
            validation.validar_irrigacao(
                {"metodo_aquacrop": 2, "intervalo": 0}, [],
                "2024-01-01", "2024-12-31",
            )
