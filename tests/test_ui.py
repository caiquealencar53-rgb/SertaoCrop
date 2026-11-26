# -*- coding: utf-8 -*-
"""Testes de interface Qt (PySide6) em modo offscreen."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from database import initialize_database  # noqa: E402
from frontand.app_window import MainWindow  # noqa: E402
from frontand.components import WorkerThread  # noqa: E402
from frontand.theme import APP_QSS  # noqa: E402


class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "ui.db"
        initialize_database(self.db_path)
        self.window = MainWindow(self.db_path)
        self.window.setStyleSheet(APP_QSS)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self._tmp.cleanup()

    def test_todas_as_telas_estao_ligadas(self):
        esperadas = {
            "Início", "Cadastro agrícola", "Culturas", "Clima", "Solo",
            "Irrigação", "Nova simulação", "Resultados", "Histórico", "Calibração",
        }
        self.assertEqual(set(self.window.pages), esperadas)
        self.assertEqual(self.window.stack.count(), len(esperadas))
        for nome in esperadas:
            self.window.show_page(nome)
            self.assertIs(self.window.stack.currentWidget(), self.window.pages[nome])
            self.assertEqual(self.window.current_section.text(), nome)
            self.assertTrue(self.window.nav_buttons[nome].isChecked())

    def test_sinal_da_dashboard_abre_nova_simulacao(self):
        self.window.pages["Início"].nova_simulacao_solicitada.emit()
        self.assertEqual(self.window.current_section.text(), "Nova simulação")

    def test_sinais_de_resultado_e_historico(self):
        self.window.pages["Nova simulação"].simulacao_concluida.emit(1)
        self.assertEqual(self.window.current_section.text(), "Resultados")
        self.window.pages["Histórico"].historico_selecionado.emit(1)
        self.assertEqual(self.window.current_section.text(), "Resultados")

    def test_componente_thread_devolve_resultado(self):
        recebido = []
        worker = WorkerThread(lambda valor: valor * 2, 21)
        worker.resultado.connect(recebido.append)
        worker.run()  # chamada direta para teste determinístico
        self.assertEqual(recebido, [42])

    def test_componente_thread_comunica_erro(self):
        def falhar():
            raise RuntimeError("erro proposital")

        recebido = []
        worker = WorkerThread(falhar)
        worker.falhou.connect(recebido.append)
        worker.run()
        self.assertEqual(len(recebido), 1)
        self.assertIn("erro proposital", recebido[0])

    def test_combos_inicializam_antes_dos_sinais(self):
        """Popular combos em __init__ não pode estourar AttributeError no slot."""
        clima = self.window.pages["Clima"]
        simulacao = self.window.pages["Nova simulação"]
        self.assertTrue(hasattr(clima, "_ids_est"))
        self.assertTrue(hasattr(simulacao, "_ids_estacao"))
        self.assertEqual(clima.resumo_label.text(), "Nenhuma estação cadastrada.")

    def test_todas_as_paginas_tem_area_de_rolagem(self):
        for pagina in self.window.pages.values():
            self.assertIs(pagina.scroll.widget().layout(), pagina.content_layout)
            self.assertTrue(pagina.scroll.widgetResizable())

    def test_importar_demo_da_propria_tela_de_simulacao(self):
        pagina = self.window.pages["Nova simulação"]
        self.assertEqual(pagina.estacao.count(), 0)
        pagina._importar_demo()
        self.assertGreater(pagina.estacao.count(), 0)
        self.assertIn("demonstracao", pagina.saida.toPlainText().lower())
        self.assertIsNotNone(pagina._config()["estacao_id"])

    def test_simulacao_tem_padrao_valido_e_mantem_escolha(self):
        from config.settings import DEMO_WEATHER_PATH
        from database import connect
        from services import climate_service

        with connect(self.db_path) as conn:
            climate_service.importar_csv(
                conn, DEMO_WEATHER_PATH, "Demo", "PADRAO-UI", eh_demonstracao=1
            )
        pagina = self.window.pages["Nova simulação"]
        self.window.show_page("Nova simulação")  # refresh repetition feito pela janela
        self.assertEqual(pagina.cultura.currentText(), "Sorgo")
        self.assertEqual(pagina.manejo.currentText(), "Sequeiro")
        self.assertNotIn("selecione", pagina.solo.currentText())
        config = pagina._config()
        self.assertIsNotNone(config["cultura_id"])
        self.assertIsNotNone(config["solo_id"])
        self.assertIsNotNone(config["estacao_id"])
        self.assertIsNotNone(config["manejo_id"])
        self.assertEqual(config["data_inicio"], "2024-01-01")

        milheto = next(
            i for i in range(pagina.cultura.count())
            if pagina.cultura.itemText(i) == "Milheto"
        )
        pagina.cultura.setCurrentIndex(milheto)
        pagina.refresh()
        self.assertEqual(pagina.cultura.currentText(), "Milheto")

    def test_simulacao_executada_aparece_em_resultados(self):
        from config.settings import DEMO_WEATHER_PATH
        from database import connect
        from services import climate_service, simulation_service

        with connect(self.db_path) as conn:
            climate_service.importar_csv(
                conn, DEMO_WEATHER_PATH, "Demo", "RESULTADO-UI", eh_demonstracao=1
            )
        pagina = self.window.pages["Nova simulação"]
        self.window.show_page("Nova simulação")
        resultado = simulation_service.executar(pagina._config(), db_path=self.db_path)
        pagina._finalizar(resultado)

        self.assertEqual(self.window.current_section.text(), "Resultados")
        self.assertIn("concluída", pagina.saida.toPlainText())
        resultados = self.window.pages["Resultados"]
        self.assertEqual(resultados.simulacoes.count(), 1)
        self.assertNotEqual(resultados.labels["produtividade"].text(), "—")
        self.assertGreater(resultados.tabela.rowCount(), 0)

    def test_dashboard_sinaliza_dados_de_demonstracao(self):
        from services import climate_service
        from database import connect

        with connect(self.db_path) as conn:
            climate_service.importar_csv(
                conn, "data/demo/clima_demo.csv", "Demo teste", "UI-DEMO",
                eh_demonstracao=1,
            )
        self.window.pages["Início"].refresh()
        aviso = self.window.pages["Início"].aviso
        self.assertFalse(aviso.isHidden())
        self.assertIn("demonstração", aviso.text().lower())
        self.assertIn("não é dado validado", aviso.text())


if __name__ == "__main__":
    unittest.main()
