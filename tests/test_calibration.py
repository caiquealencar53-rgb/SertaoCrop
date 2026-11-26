# -*- coding: utf-8 -*-
"""Testes da calibração opcional e das suas restrições científicas."""

from pathlib import Path

from config.settings import PROJECT_ROOT
from database import repositories as repo
from services import calibration_service
from tests.base import TemporaryDatabaseTest


class TestCalibracao(TemporaryDatabaseTest):
    def test_milheto_nao_pode_ser_calibrado(self):
        self.importar_demo()
        config = self.config_simulacao()
        config["experimento_id"] = 1
        config["produtividade_observada"] = 3.0
        with self.conn() as conn:
            config["cultura_id"] = repo.get_cultura_por_nome(conn, "Milheto")["id"]
        with self.assertRaisesRegex(ValueError, "parametrização"):
            calibration_service.calibrar(config, db_path=self.db_path)

    def test_produtividade_observada_e_obrigatoria(self):
        self.importar_demo()
        config = self.config_simulacao()
        config.update({
            "experimento_id": 1,
            "produtividade_observada": 0,
            "repeticoes": 5,
        })
        with self.assertRaisesRegex(ValueError, "observada"):
            calibration_service.calibrar(config, db_path=self.db_path)

    def test_spotpy_declarado_nos_requisitos(self):
        requisitos = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("spotpy==", requisitos)

    def test_schema_guarda_calibracao_como_experimental(self):
        with self.conn() as conn:
            experimento_id = repo.add_experimento(conn, "Experimento de teste")
            cultura_id = repo.get_cultura_por_nome(conn, "Sorgo")["id"]
            conn.execute(
                """INSERT INTO calibracoes
                   (experimento_id, cultura_id, versao_aquacrop, metodo_otimizacao, status)
                   VALUES (?, ?, '3.1.0', 'SCE-UA', 'EXPERIMENTAL')""",
                (experimento_id, cultura_id),
            )
            linhas = conn.execute("SELECT status FROM calibracoes").fetchall()
        self.assertEqual(linhas[0]["status"], "EXPERIMENTAL")
