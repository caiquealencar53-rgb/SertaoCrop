# -*- coding: utf-8 -*-
"""Componentes visuais reutilizáveis (sem regras de negócio)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MetricCard(QFrame):
    def __init__(self, titulo, valor="—", descricao=""):
        super().__init__()
        self.setObjectName("MetricCard")
        self.setMinimumHeight(112)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        titulo_label = QLabel(titulo)
        titulo_label.setObjectName("MetricTitle")
        self.valor_label = QLabel(str(valor))
        self.valor_label.setObjectName("MetricValue")
        layout.addWidget(titulo_label)
        layout.addWidget(self.valor_label)
        if descricao:
            desc = QLabel(descricao)
            desc.setObjectName("MutedText")
            desc.setWordWrap(True)
            layout.addWidget(desc)
        layout.addStretch()

    def set_value(self, valor):
        self.valor_label.setText(str(valor))


class BasePage(QWidget):
    def __init__(self, titulo, subtitulo):
        super().__init__()
        # As telas podem ser mais altas que a janela; sem QScrollArea os
        # botões e a saída ficam cortados (principalmente em telas pequenas).
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("PageScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        conteudo = QWidget()
        conteudo.setObjectName("PageContent")
        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(12)
        titulo_label = QLabel(titulo)
        titulo_label.setObjectName("PageTitle")
        subtitulo_label = QLabel(subtitulo)
        subtitulo_label.setObjectName("MutedText")
        subtitulo_label.setWordWrap(True)
        layout.addWidget(titulo_label)
        layout.addWidget(subtitulo_label)
        layout.addSpacing(10)
        self.scroll.setWidget(conteudo)
        raiz.addWidget(self.scroll)
        # API usada pelas telas: continua recebendo os widgets da página.
        self.content_layout = layout

    def refresh(self):
        """Sobrescrito pelas telas que exibem dados do banco."""


class SectionTitle(QLabel):
    def __init__(self, texto):
        super().__init__(texto)
        self.setObjectName("SectionTitle")


class MutedLabel(QLabel):
    def __init__(self, texto):
        super().__init__(texto)
        self.setObjectName("MutedText")
        self.setWordWrap(True)


class WarningPanel(QLabel):
    def __init__(self, texto):
        super().__init__(texto)
        self.setObjectName("WarningPanel")
        self.setWordWrap(True)


class Toolbar(QHBoxLayout):
    def __init__(self):
        super().__init__()
        self.addStretch()

    def add_primary(self, texto, callback):
        botao = QPushButton(texto)
        botao.setObjectName("PrimaryButton")
        botao.setCursor(Qt.CursorShape.PointingHandCursor)
        botao.clicked.connect(callback)
        self.addWidget(botao)
        return botao

    def add_secondary(self, texto, callback):
        botao = QPushButton(texto)
        botao.setObjectName("SecondaryButton")
        botao.clicked.connect(callback)
        self.addWidget(botao)
        return botao

    def add_danger(self, texto, callback):
        botao = QPushButton(texto)
        botao.setObjectName("DangerButton")
        botao.clicked.connect(callback)
        self.addWidget(botao)
        return botao


class DataTable(QTableWidget):
    def __init__(self, colunas, selecao_linha=True):
        super().__init__(0, len(colunas))
        self.setHorizontalHeaderLabels(colunas)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(
            QTableWidget.SelectRows if selecao_linha else QTableWidget.SelectItems
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def preencher(self, linhas):
        self.setRowCount(0)
        for linha in linhas:
            linha = ["" if v is None else v for v in linha]
            r = self.rowCount()
            self.insertRow(r)
            for c, valor in enumerate(linha):
                self.setItem(r, c, QTableWidgetItem(str(valor)))


class WorkerThread(QThread):
    """Executa funções blocking fora da thread da interface."""

    # Não redefinimos ``finished``: esse nome já é um sinal do QThread.
    resultado = Signal(object)
    falhou = Signal(str)

    def __init__(self, funcao, *args, **kwargs):
        super().__init__()
        self.funcao = funcao
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.resultado.emit(self.funcao(*self.args, **self.kwargs))
        except Exception as exc:  # a thread não pode propagar exceção
            self.falhou.emit(f"{type(exc).__name__}: {exc}")


class PlotCanvas(FigureCanvasQTAgg):
    """Gráfico simples com Matplotlib (já usado pelo projeto)."""

    def __init__(self, parent=None):
        self.figura = Figure(figsize=(8, 3.4), dpi=100)
        super().__init__(self.figura)
        self.setParent(parent)
        self.eixos = self.figura.add_subplot(111)

    def limpar(self):
        self.eixos.clear()

    def desenhar(self):
        self.figura.tight_layout()
        self.draw()
