# -*- coding: utf-8 -*-
"""Utilitários compartilhados pelos testes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config.settings import DEMO_WEATHER_PATH
from database import connect, initialize_database
from database import repositories as repo
from services import climate_service


class TemporaryDatabaseTest(unittest.TestCase):
    """Cria um banco SQLite isolado por teste."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "sertaocrop_test.db"
        initialize_database(self.db_path)

    def tearDown(self):
        self._tmp.cleanup()

    def conn(self):
        """Nova conexão para ser usada em ``with``."""
        return connect(self.db_path)

    def importar_demo(self, codigo="TEST-DEMO"):
        with self.conn() as conn:
            return climate_service.importar_csv(
                conn,
                DEMO_WEATHER_PATH,
                "Demonstração de teste",
                codigo,
                eh_demonstracao=1,
                fonte="data/demo/clima_demo.csv",
            )

    def ids_padrao(self):
        """IDs de Sorgo, solo embutido, estação demo e manejo sequeiro."""
        with self.conn() as conn:
            cultura_id = repo.get_cultura_por_nome(conn, "Sorgo")["id"]
            solo_id = repo.list_solos(conn)[0]["id"]
            estacao_id = repo.list_estacoes(conn)[0]["id"]
            manejo_id = next(
                m["id"] for m in repo.list_manejos(conn) if m["nome"] == "Sequeiro"
            )
        return cultura_id, solo_id, estacao_id, manejo_id

    def config_simulacao(self):
        cultura_id, solo_id, estacao_id, manejo_id = self.ids_padrao()
        return {
            "nome": "Simulação de teste",
            "cultura_id": cultura_id,
            "solo_id": solo_id,
            "estacao_id": estacao_id,
            "manejo_id": manejo_id,
            "data_inicio": "2024-01-01",
            "data_plantio": "2024-03-01",
            "data_fim": "2024-12-31",
            "umidade_inicial_tipo": "FC",
        }
