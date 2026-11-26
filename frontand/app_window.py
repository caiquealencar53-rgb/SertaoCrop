# -*- coding: utf-8 -*-
"""Janela principal PySide6 do SertãoCrop.

Todas as telas leem/escrevem através de serviços e repositórios; nenhuma dele
chama o AquaCrop na thread da interface. A identidade visual (verde/bege) está
em ``frontand/theme.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite executar este arquivo diretamente (ex.: "Run" na IDE), além de
# "python main.py". Sem isso, o Python colocaria apenas frontand/ no sys.path.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from config.settings import AQUACROP_VERSION, DB_PATH
from frontand.screens.calibracao import CalibracaoPage
from frontand.screens.cadastros import (
    CadastroAgricolaPage, ClimaPage, CulturasPage, IrrigacaoPage, SolosPage,
)
from frontand.screens.dashboard import DashboardPage
from frontand.screens.resultados import HistoricoPage, ResultadosPage
from frontand.screens.simulacao import SimulacaoPage
from frontand.theme import APP_QSS


class MainWindow(QMainWindow):
    def __init__(self, db_path=DB_PATH):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("SertãoCrop — Simulação agrícola com AquaCrop")
        self.resize(1400, 860)
        self.setMinimumSize(1080, 660)

        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._sidebar())
        root.addWidget(self._content_area(), 1)
        self.setStyleSheet(APP_QSS)
        self.show_page("Início")

    def _sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(245)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(6)

        brand = QLabel("SertãoCrop")
        brand.setObjectName("Brand")
        tagline = QLabel("SIMULAÇÃO AGRÍCOLA")
        tagline.setObjectName("SidebarCaption")
        layout.addWidget(brand)
        layout.addWidget(tagline)
        layout.addSpacing(24)

        titulo_menu = QLabel("MENU PRINCIPAL")
        titulo_menu.setObjectName("SidebarCaption")
        layout.addWidget(titulo_menu)

        self.nav_buttons = {}
        paginas = [
            ("Início", "⌂", DashboardPage),
            ("Cadastro agrícola", "▦", CadastroAgricolaPage),
            ("Culturas", "▧", CulturasPage),
            ("Clima", "☁", ClimaPage),
            ("Solo", "▤", SolosPage),
            ("Irrigação", "◉", IrrigacaoPage),
            ("Nova simulação", "▶", SimulacaoPage),
            ("Resultados", "▥", ResultadosPage),
            ("Histórico", "☰", HistoricoPage),
            ("Calibração", "⚙", CalibracaoPage),
        ]

        self.stack = QStackedWidget()
        self.pages = {}
        for nome, simbolo, classe in paginas:
            botao = QPushButton(f"{simbolo}    {nome}")
            botao.setObjectName("NavButton")
            botao.setCursor(Qt.CursorShape.PointingHandCursor)
            botao.setCheckable(True)
            botao.clicked.connect(lambda checked=False, n=nome: self.show_page(n))
            layout.addWidget(botao)
            self.nav_buttons[nome] = botao

            pagina = classe(self.db_path)
            self.pages[nome] = pagina
            self.stack.addWidget(pagina)

        layout.addStretch()
        rodape = QLabel(f"AquaCrop {AQUACROP_VERSION} • SQLite local")
        rodape.setObjectName("SidebarCaption")
        layout.addWidget(rodape)
        return sidebar

    def _content_area(self):
        area = QWidget()
        area.setObjectName("ContentArea")
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(64)
        barra = QHBoxLayout(topbar)
        barra.setContentsMargins(30, 0, 30, 0)
        self.current_section = QLabel("Início")
        self.current_section.setObjectName("TopbarTitle")
        status = QLabel(f"●  Banco: {self.db_path.name}")
        status.setObjectName("SystemStatus")
        barra.addWidget(self.current_section)
        barra.addStretch()
        barra.addWidget(status)

        layout.addWidget(topbar)
        layout.addWidget(self.stack, 1)

        self.pages["Início"].nova_simulacao_solicitada.connect(
            lambda: self.show_page("Nova simulação")
        )
        self.pages["Nova simulação"].simulacao_concluida.connect(
            self._abrir_resultado
        )
        self.pages["Histórico"].historico_selecionado.connect(
            self._abrir_resultado
        )
        return area

    def _abrir_resultado(self, simulacao_id):
        self.show_page("Resultados")
        self.pages["Resultados"].refresh(simulacao_id)

    def show_page(self, nome):
        if nome not in self.pages:
            return
        pagina = self.pages[nome]
        if nome not in ("Resultados",):  # resultado já é recarregado via sinal
            pagina.refresh()
        self.stack.setCurrentWidget(pagina)
        self.current_section.setText(nome)
        for nome_botao, botao in self.nav_buttons.items():
            botao.setChecked(nome_botao == nome)


def criar_aplicacao():
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("SertãoCrop")
    app.setFont(QFont("Noto Sans", 10))
    return app


def main(db_path=DB_PATH):
    from database import initialize_database

    initialize_database(db_path)
    app = criar_aplicacao()
    janela = MainWindow(db_path)
    janela.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
