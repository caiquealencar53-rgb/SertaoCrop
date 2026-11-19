# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
from string import Template

# ---------------------------------------------------------
# AJUSTE DO PATH PARA O IMPORT DO BACKEND FUNCIONAR
# ---------------------------------------------------------
raiz_projeto = Path(__file__).resolve().parent.parent.parent
if str(raiz_projeto) not in sys.path:
    sys.path.insert(0, str(raiz_projeto))

try:
    from backend.engine.simulador import executar_simulacao, executar_calibracao
except ImportError as e:
    print(f"AVISO: Não foi possível importar o simulador. Erro: {e}")
    def executar_simulacao(**kwargs): return {"sucesso": False, "erro": "Backend não encontrado"}
    def executar_calibracao(**kwargs): return {"sucesso": False, "erro": "Backend não encontrado"}

from PySide6.QtCore import Qt, QThread, Signal, QDate
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget
)

# ============================================================
# PALETA DE CORES (altere só aqui para mudar a identidade visual)
# ============================================================
PALETA = {
    # Estrutura
    "bg":             "#F4F7F4",  # fundo geral
    "surface":        "#FFFFFF",  # cards, tabelas, campos
    "surface_alt":    "#F8FAF8",  # linhas alternadas / cabeçalhos
    "border":         "#E1E8E2",
    "border_strong":  "#CBD6CD",

    # Sidebar
    "side_bg":        "#12372A",
    "side_hover":     "#1C4D3B",
    "side_text":      "#D5E6DC",
    "side_active_bg": "#DFF0E5",
    "side_active_tx": "#12372A",

    # Marca / ação
    "primary":        "#1F6F4A",
    "primary_hover":  "#17583A",
    "primary_press":  "#12472F",
    "primary_soft":   "#E3F1E8",
    "disabled_bg":    "#B7C6BC",
    "disabled_tx":    "#F1F5F2",

    # Texto
    "text":           "#1E2A23",
    "text_title":     "#14342A",
    "text_muted":     "#6B7B71",

    # Estados
    "danger":         "#B83227",
    "danger_bg":      "#FDEEEC",
    "danger_border":  "#F0B4AD",
    "danger_hover":   "#FADBD7",
    "accent":         "#D9A441",  # areia/dourado do sertão
}

QSS_TEMPLATE = Template("""
QWidget {
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 13px;
    color: $text;
}
QMainWindow, #Central { background: $bg; }
QDialog, QMessageBox { background: $surface; }

/* ---------- SIDEBAR ---------- */
#Sidebar { background: $side_bg; }
#Brand { color: #FFFFFF; font-size: 24px; font-weight: 800; }
QPushButton#NavButton {
    color: $side_text; background: transparent; border: none;
    border-radius: 8px; text-align: left; padding: 12px 14px;
}
QPushButton#NavButton:hover { background: $side_hover; color: #FFFFFF; }
QPushButton#NavButton:checked {
    background: $side_active_bg; color: $side_active_tx; font-weight: bold;
}

/* ---------- TOPBAR ---------- */
#Topbar { background: $surface; border-bottom: 1px solid $border; }
#TopbarTitle { font-size: 16px; font-weight: bold; color: $text_title; }
#SystemStatus { color: $primary; font-size: 12px; font-weight: 600; }

/* ---------- TEXTOS ---------- */
#PageTitle { color: $text_title; font-size: 26px; font-weight: 700; }
#MutedText { color: $text_muted; font-size: 12px; }
#SectionTitle { color: $text_title; font-size: 16px; font-weight: bold; }
QLabel { background: transparent; }

/* ---------- CARDS ---------- */
#MetricCard, #Panel {
    background: $surface; border: 1px solid $border; border-radius: 12px;
}
#MetricCard { border-top: 3px solid $accent; }
#MetricTitle { color: $text_muted; font-size: 12px; font-weight: 600; }
#MetricValue { color: $primary; font-size: 28px; font-weight: 700; }

/* ---------- BOTÕES ---------- */
QPushButton { border-radius: 6px; padding: 8px 16px; }
QPushButton#PrimaryButton {
    background: $primary; color: #FFFFFF; border: none; font-weight: bold;
}
QPushButton#PrimaryButton:hover   { background: $primary_hover; }
QPushButton#PrimaryButton:pressed { background: $primary_press; }
QPushButton#PrimaryButton:disabled { background: $disabled_bg; color: $disabled_tx; }

QPushButton#DangerButton {
    background: $danger_bg; color: $danger; border: 1px solid $danger_border;
    font-weight: bold;
}
QPushButton#DangerButton:hover { background: $danger_hover; }

QDialogButtonBox QPushButton, QMessageBox QPushButton {
    background: $surface; color: $text; border: 1px solid $border_strong;
    min-width: 70px;
}
QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover {
    background: $primary_soft; border-color: $primary;
}
QDialogButtonBox QPushButton:default, QMessageBox QPushButton:default {
    background: $primary; color: #FFFFFF; border: none;
}

/* ---------- TABELAS ---------- */
QTableWidget {
    background: $surface; alternate-background-color: $surface_alt;
    border: 1px solid $border; border-radius: 8px; gridline-color: $border;
    selection-background-color: $primary_soft; selection-color: $text_title;
}
QHeaderView::section {
    background: $surface_alt; color: $text_muted; font-weight: bold;
    padding: 8px; border: none; border-bottom: 1px solid $border;
}

/* ---------- CAMPOS ---------- */
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
    background: $surface; border: 1px solid $border_strong;
    border-radius: 6px; padding: 5px 8px; min-height: 20px;
    selection-background-color: $primary; selection-color: #FFFFFF;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
    border: 1px solid $primary;
}
QComboBox QAbstractItemView {
    background: $surface; border: 1px solid $border_strong;
    selection-background-color: $primary_soft; selection-color: $text_title;
    outline: 0;
}
QTextEdit#LogBox {
    background: $surface; border: 1px solid $border; border-radius: 8px;
    padding: 10px; font-family: "JetBrains Mono", "Consolas", monospace;
}

/* ---------- SCROLLBAR ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: $border_strong; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: $text_muted; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
""")

APP_QSS = QSS_TEMPLATE.substitute(PALETA)


# ============================================================
# ESTADO EM MEMÓRIA
# ============================================================
class AppState:
    def __init__(self):
        self.culturas = []
        self.solos = []
        self.estacoes = []
        self.experimentos = []
        self.simulacoes = []

STATE = AppState()


# ============================================================
# THREAD PARA O BACKEND
# ============================================================
class WorkerThread(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, **kwargs):
        super().__init__()
        self.func = func
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.func(**self.kwargs)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
# COMPONENTES VISUAIS BÁSICOS
# ============================================================
class MetricCard(QFrame):
    def __init__(self, title, value="0"):
        super().__init__()
        self.setObjectName("MetricCard")
        self.setMinimumHeight(125)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)

        title_label = QLabel(title); title_label.setObjectName("MetricTitle")
        self.value_label = QLabel(str(value)); self.value_label.setObjectName("MetricValue")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, v):
        self.value_label.setText(str(v))


class BasePage(QWidget):
    def __init__(self, title, subtitle):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(12)

        heading = QLabel(title); heading.setObjectName("PageTitle")
        subheading = QLabel(subtitle); subheading.setObjectName("MutedText"); subheading.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(subheading)
        layout.addSpacing(12)
        self.content_layout = layout


# ============================================================
# PÁGINAS (TELAS)
# ============================================================
class HomePage(BasePage):
    def __init__(self):
        super().__init__("Visão geral", "Acompanhe os cadastros e as atividades do SertãoCrop.")
        cards = QHBoxLayout()
        self.c_cult = MetricCard("Culturas")
        self.c_solo = MetricCard("Solos")
        self.c_est = MetricCard("Estações")
        self.c_sim = MetricCard("Simulações")
        for c in (self.c_cult, self.c_solo, self.c_est, self.c_sim):
            cards.addWidget(c)
        self.content_layout.addLayout(cards)
        self.content_layout.addStretch()

    def refresh(self):
        self.c_cult.set_value(len(STATE.culturas))
        self.c_solo.set_value(len(STATE.solos))
        self.c_est.set_value(len(STATE.estacoes))
        self.c_sim.set_value(len(STATE.simulacoes))


class TabelaPage(BasePage):
    def __init__(self, title, subtitle, colunas):
        super().__init__(title, subtitle)
        barra = QHBoxLayout()
        self.btn_add = QPushButton("+ Adicionar")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del = QPushButton("Remover Selecionado")
        self.btn_del.setObjectName("DangerButton")
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        barra.addWidget(self.btn_add); barra.addWidget(self.btn_del); barra.addStretch()
        self.content_layout.addLayout(barra)

        self.tabela = QTableWidget(0, len(colunas))
        self.tabela.setHorizontalHeaderLabels(colunas)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.content_layout.addWidget(self.tabela)

        self.btn_add.clicked.connect(self.adicionar)
        self.btn_del.clicked.connect(self.remover)

    def adicionar(self): pass
    def remover(self): pass
    def refresh(self): pass

    def preencher(self, linhas):
        self.tabela.setRowCount(0)
        for linha in linhas:
            r = self.tabela.rowCount()
            self.tabela.insertRow(r)
            for c, v in enumerate(linha):
                self.tabela.setItem(r, c, QTableWidgetItem(str(v)))


# --- DIÁLOGOS DE CADASTRO ---
class DialogCultura(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Cultura")
        f = QFormLayout(self)
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Ex: Milheto")
        self.cgc = QDoubleSpinBox(); self.cgc.setDecimals(4); self.cgc.setValue(0.05)
        self.cdc = QDoubleSpinBox(); self.cdc.setDecimals(4); self.cdc.setValue(0.05)
        self.wp = QDoubleSpinBox(); self.wp.setDecimals(2); self.wp.setValue(25.0)
        self.hi0 = QDoubleSpinBox(); self.hi0.setDecimals(3); self.hi0.setValue(0.35)
        f.addRow("Nome:", self.nome); f.addRow("CGC:", self.cgc); f.addRow("CDC:", self.cdc)
        f.addRow("WP:", self.wp); f.addRow("HI0:", self.hi0)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); f.addRow(b)

    def get_data(self):
        return {"nome": self.nome.text() or "Nova", "cgc": self.cgc.value(),
                "cdc": self.cdc.value(), "wp": self.wp.value(), "hi0": self.hi0.value()}


class DialogSolo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Solo")
        f = QFormLayout(self)
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Ex: Latossolo")
        self.thwp = QDoubleSpinBox(); self.thwp.setDecimals(3); self.thwp.setValue(0.08)
        self.thfc = QDoubleSpinBox(); self.thfc.setDecimals(3); self.thfc.setValue(0.17)
        f.addRow("Nome:", self.nome); f.addRow("θ WP:", self.thwp); f.addRow("θ FC:", self.thfc)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); f.addRow(b)

    def get_data(self):
        return {"nome": self.nome.text() or "Novo", "thwp": self.thwp.value(), "thfc": self.thfc.value()}


class DialogEstacao(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Estação")
        f = QFormLayout(self)
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Ex: Serra Talhada")
        self.arquivo = QLineEdit(); self.arquivo.setPlaceholderText("C:/caminho/Clima_Serra.txt")
        f.addRow("Nome:", self.nome); f.addRow("Arquivo:", self.arquivo)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); f.addRow(b)

    def get_data(self):
        return {"nome": self.nome.text() or "Nova", "arquivo": self.arquivo.text()}


class DialogExperimento(QDialog):
    def __init__(self, culturas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Experimento")
        f = QFormLayout(self)
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Ex: Ensaio 2019")
        self.cultura = QComboBox(); self.cultura.addItems(culturas)
        self.prod = QDoubleSpinBox(); self.prod.setValue(3.0)
        f.addRow("Nome:", self.nome); f.addRow("Cultura:", self.cultura)
        f.addRow("Produtividade (t/ha):", self.prod)
        b = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); f.addRow(b)

    def get_data(self):
        return {"nome": self.nome.text() or "Novo", "cultura": self.cultura.currentText(),
                "prod": self.prod.value()}


# --- PÁGINAS ESPECÍFICAS ---
class CulturasPage(TabelaPage):
    def __init__(self):
        super().__init__("Culturas", "Gerencie os parâmetros agronômicos.",
                         ["Nome", "CGC", "CDC", "WP", "HI0"])
        self.refresh()

    def adicionar(self):
        d = DialogCultura(self)
        if d.exec():
            STATE.culturas.append(d.get_data()); self.refresh()

    def remover(self):
        r = self.tabela.currentRow()
        if r >= 0:
            STATE.culturas.pop(r); self.refresh()

    def refresh(self):
        self.preencher([[c["nome"], c["cgc"], c["cdc"], c["wp"], c["hi0"]] for c in STATE.culturas])


class SolosPage(TabelaPage):
    def __init__(self):
        super().__init__("Solos", "Gerencie os perfis de solo.", ["Nome", "θ WP", "θ FC"])
        self.refresh()

    def adicionar(self):
        d = DialogSolo(self)
        if d.exec():
            STATE.solos.append(d.get_data()); self.refresh()

    def remover(self):
        r = self.tabela.currentRow()
        if r >= 0:
            STATE.solos.pop(r); self.refresh()

    def refresh(self):
        self.preencher([[s["nome"], s["thwp"], s["thfc"]] for s in STATE.solos])


class ClimaPage(TabelaPage):
    def __init__(self):
        super().__init__("Clima", "Gerencie estações meteorológicas.", ["Nome", "Arquivo"])
        self.refresh()

    def adicionar(self):
        d = DialogEstacao(self)
        if d.exec():
            STATE.estacoes.append(d.get_data()); self.refresh()

    def remover(self):
        r = self.tabela.currentRow()
        if r >= 0:
            STATE.estacoes.pop(r); self.refresh()

    def refresh(self):
        self.preencher([[e["nome"], e["arquivo"]] for e in STATE.estacoes])


class ExperimentosPage(TabelaPage):
    def __init__(self):
        super().__init__("Experimentos", "Registre observações de campo.",
                         ["Nome", "Cultura", "Prod. (t/ha)"])
        self.refresh()

    def adicionar(self):
        d = DialogExperimento([c["nome"] for c in STATE.culturas], self)
        if d.exec():
            STATE.experimentos.append(d.get_data()); self.refresh()

    def remover(self):
        r = self.tabela.currentRow()
        if r >= 0:
            STATE.experimentos.pop(r); self.refresh()

    def refresh(self):
        self.preencher([[e["nome"], e["cultura"], e["prod"]] for e in STATE.experimentos])


# --- SIMULAÇÃO E CALIBRAÇÃO ---
class SimulacaoPage(BasePage):
    def __init__(self):
        super().__init__("Nova Simulação", "Configure e execute uma simulação com AquaCrop.")
        panel = QFrame(); panel.setObjectName("Panel")
        f = QFormLayout(panel)
        f.setContentsMargins(18, 16, 18, 16)
        self.cultura = QComboBox(); self.solo = QComboBox(); self.estacao = QComboBox()
        self.dt_plantio = QDateEdit(QDate(2019, 2, 27)); self.dt_plantio.setCalendarPopup(True)
        self.dt_colheita = QDateEdit(QDate(2019, 5, 28)); self.dt_colheita.setCalendarPopup(True)
        f.addRow("Cultura:", self.cultura); f.addRow("Solo:", self.solo); f.addRow("Estação:", self.estacao)
        f.addRow("Plantio:", self.dt_plantio); f.addRow("Colheita:", self.dt_colheita)
        self.btn = QPushButton("▶ Executar Simulação"); self.btn.setObjectName("PrimaryButton")
        self.btn.clicked.connect(self.executar)
        f.addRow(self.btn)
        self.content_layout.addWidget(panel)

        self.out = QTextEdit(); self.out.setObjectName("LogBox")
        self.out.setReadOnly(True); self.out.setMinimumHeight(200)
        self.content_layout.addWidget(self.out)
        self.content_layout.addStretch()

    def refresh(self):
        self.cultura.clear(); self.solo.clear(); self.estacao.clear()
        self.cultura.addItems([c["nome"] for c in STATE.culturas] or ["(Nenhuma)"])
        self.solo.addItems([s["nome"] for s in STATE.solos] or ["(Nenhum)"])
        self.estacao.addItems([e["nome"] for e in STATE.estacoes] or ["(Nenhuma)"])

    def executar(self):
        if not STATE.culturas or not STATE.solos or not STATE.estacoes:
            QMessageBox.warning(self, "Aviso", "Cadastre cultura, solo e estação primeiro!")
            return

        est = STATE.estacoes[self.estacao.currentIndex()]
        if not os.path.exists(est["arquivo"]):
            QMessageBox.critical(self, "Erro", f"Arquivo climático não encontrado:\n{est['arquivo']}")
            return

        self.btn.setEnabled(False)
        self.out.setText("Rodando backend... Aguarde.")

        dados_solo = {"camadas": [{"espessura": 0.2, "th_wp": 0.08, "th_fc": 0.17,
                                   "th_s": 0.35, "ksat": 100}] * 4}
        dados_cultura = {
            "nome": self.cultura.currentText(),
            "data_plantio": self.dt_plantio.date().toString("MM/dd"),
            "data_colheita": self.dt_colheita.date().toString("MM/dd"),
            "ccx": 0.8, "cgc": 0.05, "cdc": 0.05, "wp": 25.0, "hi0": 0.35
        }

        self.worker = WorkerThread(
            executar_simulacao,
            dados_solo=dados_solo, dados_cultura=dados_cultura,
            caminho_clima=est["arquivo"], dados_irrigacao={"metodo": 0},
            sim_start="2019/02/27", sim_end="2019/06/30"
        )
        self.worker.finished.connect(self.finalizar)
        self.worker.error.connect(self._erro)
        self.worker.start()

    def _erro(self, e):
        self.out.setText(f"Erro:\n{e}")
        self.btn.setEnabled(True)

    def finalizar(self, res):
        self.btn.setEnabled(True)
        if not res.get("sucesso"):
            self.out.setText(f"Falha:\n{res.get('erro')}")
            return
        self.out.setText(
            f"Produtividade: {res['produtividade']:.2f} t/ha\n"
            f"Potencial: {res['produtividade_potencial']:.2f} t/ha"
        )
        STATE.simulacoes.append({
            "cultura": self.cultura.currentText(),
            "solo": self.solo.currentText(),
            "resultado": res["produtividade"],
        })


class CalibracaoPage(BasePage):
    def __init__(self):
        super().__init__("Calibração", "Ajuste parâmetros com SpotPy (SCE-UA).")
        panel = QFrame(); panel.setObjectName("Panel")
        f = QFormLayout(panel)
        f.setContentsMargins(18, 16, 18, 16)
        self.exp = QComboBox(); self.estacao = QComboBox()
        self.reps = QLineEdit("50")
        f.addRow("Experimento:", self.exp); f.addRow("Estação:", self.estacao)
        f.addRow("Repetições:", self.reps)
        self.btn = QPushButton("⚙ Iniciar Calibração"); self.btn.setObjectName("PrimaryButton")
        self.btn.clicked.connect(self.executar)
        f.addRow(self.btn)
        self.content_layout.addWidget(panel)

        self.log = QTextEdit(); self.log.setObjectName("LogBox")
        self.log.setReadOnly(True); self.log.setMinimumHeight(200)
        self.content_layout.addWidget(self.log)
        self.content_layout.addStretch()

    def refresh(self):
        self.exp.clear(); self.estacao.clear()
        self.exp.addItems([e["nome"] for e in STATE.experimentos] or ["(Nenhum)"])
        self.estacao.addItems([e["nome"] for e in STATE.estacoes] or ["(Nenhuma)"])

    def executar(self):
        if not STATE.experimentos or not STATE.estacoes:
            QMessageBox.warning(self, "Aviso", "Cadastre experimento e estação primeiro!")
            return

        est = STATE.estacoes[self.estacao.currentIndex()]
        exp = STATE.experimentos[self.exp.currentIndex()]

        try:
            repeticoes = int(self.reps.text() or 50)
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Repetições deve ser um número inteiro.")
            return

        self.btn.setEnabled(False)
        self.log.setText("Calibrando... (isso pode demorar)")

        dados_solo = {"camadas": [{"espessura": 0.2, "th_wp": 0.08, "th_fc": 0.17,
                                   "th_s": 0.35, "ksat": 100}] * 4}

        self.worker = WorkerThread(
            executar_calibracao,
            dados_solo=dados_solo, caminho_clima=est["arquivo"],
            dados_irrigacao={"metodo": 0}, sim_start="2019/02/27", sim_end="2019/06/30",
            produtividade_observada=exp["prod"], repeticoes=repeticoes
        )
        self.worker.finished.connect(self.finalizar)
        self.worker.error.connect(self._erro)
        self.worker.start()

    def _erro(self, e):
        self.log.setText(f"Erro:\n{e}")
        self.btn.setEnabled(True)

    def finalizar(self, res):
        self.btn.setEnabled(True)
        if not res.get("sucesso"):
            self.log.setText(f"Falha:\n{res.get('erro')}")
            return
        texto = "--- Parâmetros Encontrados ---\n"
        for k in ("WP", "CGC", "CDC", "HI0"):
            if k in res:
                texto += f"{k}: {res[k]:.4f}\n"
        self.log.setText(texto)


class ResultadosPage(TabelaPage):
    def __init__(self):
        super().__init__("Resultados", "Simulações executadas.",
                         ["Cultura", "Solo", "Produtividade (t/ha)"])
        self.btn_add.hide()
        self.btn_del.setText("Limpar Histórico")
        self.refresh()

    def remover(self):
        STATE.simulacoes.clear(); self.refresh()

    def refresh(self):
        self.preencher([[s["cultura"], s["solo"], f"{s['resultado']:.2f}"] for s in STATE.simulacoes])


# ============================================================
# JANELA PRINCIPAL
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SertãoCrop")
        self.resize(1280, 780)

        central = QWidget(); self.setCentralWidget(central)
        central.setObjectName("Central")

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame(); sidebar.setObjectName("Sidebar"); sidebar.setFixedWidth(245)
        sl = QVBoxLayout(sidebar); sl.setContentsMargins(18, 24, 18, 20)
        brand = QLabel("SertãoCrop"); brand.setObjectName("Brand")
        sl.addWidget(brand); sl.addSpacing(25)

        # Área de conteúdo
        content = QWidget()
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(0)

        # Barra superior
        topbar = QFrame(); topbar.setObjectName("Topbar"); topbar.setFixedHeight(66)
        tl = QHBoxLayout(topbar); tl.setContentsMargins(30, 0, 30, 0)
        self.title = QLabel("Início"); self.title.setObjectName("TopbarTitle")
        tl.addWidget(self.title); tl.addStretch()
        status = QLabel("●  Integrado"); status.setObjectName("SystemStatus")
        tl.addWidget(status)

        self.stack = QStackedWidget()
        self.pages = {}
        self.nav = {}

        defs = [
            ("Início", HomePage), ("Culturas", CulturasPage), ("Solos", SolosPage),
            ("Clima", ClimaPage), ("Experimentos", ExperimentosPage),
            ("Simulação", SimulacaoPage), ("Calibração", CalibracaoPage),
            ("Resultados", ResultadosPage),
        ]

        for name, cls in defs:
            btn = QPushButton(f"  {name}"); btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self.trocar_tela(n))
            sl.addWidget(btn); self.nav[name] = btn

            page = cls(); self.pages[name] = page; self.stack.addWidget(page)

        sl.addStretch()
        cl.addWidget(topbar); cl.addWidget(self.stack)
        root.addWidget(sidebar); root.addWidget(content, 1)

        self.setStyleSheet(APP_QSS)
        self.trocar_tela("Início")

    def trocar_tela(self, nome):
        self.stack.setCurrentWidget(self.pages[nome])
        self.title.setText(nome)
        for n, b in self.nav.items():
            b.setChecked(n == nome)
        if hasattr(self.pages[nome], "refresh"):
            self.pages[nome].refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())