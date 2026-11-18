# -*- coding: utf-8 -*-
"""Interface inicial do SertãoCrop. Requer: pip install PySide6
Execute com: python interface_sertaocrop.py

Esta é uma interface visual inicial. Ainda não está conectada ao SQLite ou AquaCrop.
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget
)


class MetricCard(QFrame):
    def __init__(self, title, value="—", description="Aguardando integração com o banco"):
        super().__init__()
        self.setObjectName("MetricCard")
        self.setMinimumHeight(125)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        description_label = QLabel(description)
        description_label.setObjectName("MutedText")
        description_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(description_label)
        layout.addStretch()


class BasePage(QWidget):
    def __init__(self, title, subtitle):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        subheading = QLabel(subtitle)
        subheading.setObjectName("MutedText")
        subheading.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(subheading)
        layout.addSpacing(12)
        self.content_layout = layout


class HomePage(BasePage):
    def __init__(self):
        super().__init__(
            "Visão geral",
            "Acompanhe os cadastros e as atividades do SertãoCrop."
        )

        cards = QHBoxLayout()
        cards.setSpacing(14)
        cards.addWidget(MetricCard("Culturas cadastradas"))
        cards.addWidget(MetricCard("Perfis de solo"))
        cards.addWidget(MetricCard("Estações meteorológicas"))
        cards.addWidget(MetricCard("Simulações realizadas"))
        self.content_layout.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 18, 20, 18)
        panel_layout.setSpacing(10)

        title = QLabel("Comece por aqui")
        title.setObjectName("SectionTitle")
        text = QLabel(
            "1. Cadastre ou importe os dados climáticos.\n"
            "2. Confira os parâmetros das culturas e os perfis de solo.\n"
            "3. Configure uma simulação quando os dados necessários estiverem disponíveis.\n\n"
            "Os módulos ainda serão conectados ao banco de dados e ao AquaCrop."
        )
        text.setObjectName("BodyText")
        text.setWordWrap(True)

        panel_layout.addWidget(title)
        panel_layout.addWidget(text)
        self.content_layout.addWidget(panel)
        self.content_layout.addStretch()


class PlaceholderPage(BasePage):
    def __init__(self, title, subtitle, details):
        super().__init__(title, subtitle)
        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(22, 20, 22, 20)
        panel_layout.setSpacing(10)

        status = QLabel("MÓDULO EM CONSTRUÇÃO")
        status.setObjectName("StatusLabel")
        message = QLabel(details)
        message.setObjectName("BodyText")
        message.setWordWrap(True)

        panel_layout.addWidget(status)
        panel_layout.addWidget(message)
        self.content_layout.addWidget(panel)
        self.content_layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SertãoCrop")
        self.resize(1280, 780)
        self.setMinimumSize(1000, 650)

        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(245)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 24, 18, 20)
        side_layout.setSpacing(8)

        brand = QLabel("SertãoCrop")
        brand.setObjectName("Brand")
        tagline = QLabel("SIMULAÇÃO AGRÍCOLA")
        tagline.setObjectName("SidebarCaption")
        menu_heading = QLabel("MENU PRINCIPAL")
        menu_heading.setObjectName("SidebarCaption")

        side_layout.addWidget(brand)
        side_layout.addWidget(tagline)
        side_layout.addSpacing(25)
        side_layout.addWidget(menu_heading)
        side_layout.addSpacing(5)

        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(66)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(30, 0, 30, 0)

        self.current_section = QLabel("Início")
        self.current_section.setObjectName("TopbarTitle")
        system_status = QLabel("●  Sistema local")
        system_status.setObjectName("SystemStatus")
        top_layout.addWidget(self.current_section)
        top_layout.addStretch()
        top_layout.addWidget(system_status)

        self.stack = QStackedWidget()
        self.pages = {}
        self.nav_buttons = {}

        page_definitions = [
            ("Início", "⌂", lambda: HomePage()),
            ("Culturas", "▧", lambda: PlaceholderPage(
                "Culturas", "Gerencie as culturas e seus parâmetros agronômicos.",
                "Cadastro de sorgo e milheto, parâmetros do AquaCrop, fontes bibliográficas "
                "e versões dos parâmetros."
            )),
            ("Solos", "▤", lambda: PlaceholderPage(
                "Solos", "Gerencie os perfis e as propriedades físicas do solo.",
                "Cadastro de tipos de solo, camadas, profundidade, textura e propriedades hidráulicas."
            )),
            ("Clima", "☁", lambda: PlaceholderPage(
                "Dados climáticos", "Organize estações meteorológicas e séries históricas.",
                "Importação de CSV e Excel e consulta de precipitação, temperatura, "
                "evapotranspiração e demais variáveis."
            )),
            ("Experimentos", "⚗", lambda: PlaceholderPage(
                "Experimentos", "Registre observações agrícolas.",
                "Cadastro de experimentos, condições de campo e produtividades observadas "
                "para avaliação e calibração."
            )),
            ("Simulação", "▶", lambda: PlaceholderPage(
                "Nova simulação", "Configure e execute uma simulação agrícola.",
                "Seleção de cultura, solo, clima, datas, água inicial e manejo de irrigação. "
                "Este módulo será conectado ao AquaCrop."
            )),
            ("Calibração", "⚙", lambda: PlaceholderPage(
                "Calibração", "Ajuste parâmetros do modelo usando dados experimentais.",
                "Integração futura com SPOTPY/SCE-UA, métricas e registro dos parâmetros encontrados."
            )),
            ("Resultados", "▥", lambda: PlaceholderPage(
                "Resultados", "Consulte simulações, métricas e gráficos.",
                "Exibição de produtividade simulada, irrigação sazonal, crescimento diário "
                "e exportação de relatórios."
            )),
        ]

        for name, symbol, factory in page_definitions:
            button = QPushButton(f"{symbol}    {name}")
            button.setObjectName("NavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, page_name=name: self.show_page(page_name)
            )
            side_layout.addWidget(button)
            self.nav_buttons[name] = button

            page = factory()
            self.pages[name] = page
            self.stack.addWidget(page)

        side_layout.addStretch()
        footer = QLabel("Versão inicial • Offline")
        footer.setObjectName("SidebarCaption")
        side_layout.addWidget(footer)

        content_layout.addWidget(topbar)
        content_layout.addWidget(self.stack)
        root.addWidget(sidebar)
        root.addWidget(content_area, 1)

        self.apply_styles()
        self.show_page("Início")

    def show_page(self, name):
        self.stack.setCurrentWidget(self.pages[name])
        self.current_section.setText(name)
        for button_name, button in self.nav_buttons.items():
            button.setChecked(button_name == name)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: "Inter", "Noto Sans", sans-serif;
                font-size: 13px;
                color: #1f2937;
            }
            #Central, #ContentArea { background-color: #f5f7f6; }
            #Sidebar { background-color: #173b32; }
            #Brand {
                color: white; font-size: 25px; font-weight: 800;
            }
            #SidebarCaption {
                color: #a9c2b8; font-size: 10px; font-weight: 700;
                letter-spacing: 1px;
            }
            QPushButton#NavButton {
                color: #dce9e3; background: transparent; border: none;
                border-radius: 8px; text-align: left; padding: 12px 13px;
            }
            QPushButton#NavButton:hover {
                background-color: #285448; color: white;
            }
            QPushButton#NavButton:checked {
                background-color: #d8eee2; color: #173b32; font-weight: 700;
            }
            #Topbar {
                background: white; border-bottom: 1px solid #e5eae7;
            }
            #TopbarTitle { font-size: 15px; font-weight: 700; color: #263b33; }
            #SystemStatus { color: #39765a; font-size: 12px; font-weight: 600; }
            #PageTitle { color: #183c32; font-size: 27px; font-weight: 750; }
            #MutedText { color: #718078; font-size: 12px; }
            #MetricCard, #Panel {
                background: white; border: 1px solid #e4eae6; border-radius: 12px;
            }
            #MetricTitle { color: #697970; font-size: 12px; font-weight: 600; }
            #MetricValue { color: #1d493a; font-size: 29px; font-weight: 750; }
            #SectionTitle { color: #234438; font-size: 16px; font-weight: 700; }
            #BodyText { color: #52635a; font-size: 13px; }
            #StatusLabel {
                color: #a16a20; font-size: 10px; font-weight: 800;
                letter-spacing: 1px;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SertãoCrop")
    app.setFont(QFont("Noto Sans", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()