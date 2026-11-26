# -*- coding: utf-8 -*-
"""Tela de calibração opcional (SpotPy/SCE-UA), com alerta experimental."""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QFrame, QLineEdit,
    QMessageBox, QSpinBox, QTextEdit,
)

from database import connect
from database import repositories as repo
from frontand.components import BasePage, Toolbar, WarningPanel, WorkerThread
from frontand.screens.cadastros import _combobox_com_ids
from services import calibration_service


class CalibracaoPage(BasePage):
    def __init__(self, db_path):
        super().__init__("Calibração", "Ajuste de parâmetros do Sorghum com observações de campo.")
        self.db_path = db_path
        self.worker = None
        self.content_layout.addWidget(
            WarningPanel(
                "Parâmetros calibrados por otimização são experimentais. "
                "A convergência do algoritmo não valida cientificamente a cultura. "
                "Milheto não é suportado nesta calibração."
            )
        )
        painel = QFrame()
        painel.setObjectName("Panel")
        form = QFormLayout(painel)
        self.experimento = QComboBox()
        self.cultura = QComboBox()
        self.solo = QComboBox()
        self.estacao = QComboBox()
        self.manejo = QComboBox()
        self.inicio = QDateEdit(QDate(2024, 1, 1))
        self.plantio = QDateEdit(QDate(2024, 3, 1))
        self.fim = QDateEdit(QDate(2024, 12, 31))
        for data in (self.inicio, self.plantio, self.fim):
            data.setCalendarPopup(True)
            data.setDisplayFormat("yyyy-MM-dd")
        self.observada = QDoubleSpinBox()
        self.observada.setRange(0, 50)
        self.observada.setDecimals(3)
        self.repeticoes = QSpinBox()
        self.repeticoes.setRange(5, 500)
        self.repeticoes.setValue(30)
        for rotulo, widget in (
            ("Experimento*:", self.experimento), ("Cultura*:", self.cultura),
            ("Solo*:", self.solo), ("Estação*:", self.estacao),
            ("Manejo*:", self.manejo), ("Início:", self.inicio),
            ("Plantio:", self.plantio), ("Fim:", self.fim),
            ("Prod. observada (t/ha)*:", self.observada),
            ("Repetições:", self.repeticoes),
        ):
            form.addRow(rotulo, widget)
        barra = Toolbar()
        barra.add_primary("Iniciar calibração", self._executar)
        form.addRow(barra)
        self.content_layout.addWidget(painel)
        self.saida = QTextEdit()
        self.saida.setObjectName("LogBox")
        self.saida.setReadOnly(True)
        self.content_layout.addWidget(self.saida)
        self.refresh()

    def refresh(self):
        with connect(self.db_path) as conn:
            experimentos = repo.list_experimentos(conn)
            culturas = repo.list_culturas(conn)
            solos = repo.list_solos(conn)
            estacoes = repo.list_estacoes(conn)
            manejos = repo.list_manejos(conn)
        self._ids_exp = _combobox_com_ids(self.experimento, experimentos, incluir_vazio=False)
        self._ids_cult = _combobox_com_ids(self.cultura, culturas, incluir_vazio=False)
        self._ids_solo = _combobox_com_ids(self.solo, solos, incluir_vazio=False)
        self._ids_est = _combobox_com_ids(self.estacao, estacoes, incluir_vazio=False)
        self._ids_manejo = _combobox_com_ids(self.manejo, manejos, incluir_vazio=False)

    def _config(self):
        def sel(combo, ids):
            idx = combo.currentIndex()
            return ids[idx] if 0 <= idx < len(ids) else None
        valores = (
            sel(self.experimento, self._ids_exp), sel(self.cultura, self._ids_cult),
            sel(self.solo, self._ids_solo), sel(self.estacao, self._ids_est),
            sel(self.manejo, self._ids_manejo),
        )
        if None in valores or self.observada.value() <= 0:
            raise ValueError("Preencha todos os cadastros e a produtividade observada.")
        return {
            "experimento_id": valores[0], "cultura_id": valores[1], "solo_id": valores[2],
            "estacao_id": valores[3], "manejo_id": valores[4],
            "data_inicio": self.inicio.date().toString("yyyy-MM-dd"),
            "data_plantio": self.plantio.date().toString("yyyy-MM-dd"),
            "data_fim": self.fim.date().toString("yyyy-MM-dd"),
            "produtividade_observada": self.observada.value(),
            "repeticoes": self.repeticoes.value(),
        }

    def _executar(self):
        try:
            config = self._config()
        except Exception as exc:
            QMessageBox.warning(self, "Validação", str(exc))
            return
        self.saida.setText("Calibrando (isso pode demorar)...")
        self.worker = WorkerThread(calibration_service.calibrar, config, db_path=self.db_path)
        self.worker.resultado.connect(self._finalizar)
        self.worker.falhou.connect(lambda msg: self.saida.setText(f"Erro:\n{msg}"))
        self.worker.start()

    def _finalizar(self, resultado):
        if not resultado.get("sucesso"):
            self.saida.setText(str(resultado))
            return
        texto = f"Calibração #{resultado['calibracao_id']} — {resultado['status']}\n\n"
        for nome, valor in resultado["parametros"].items():
            texto += f"{nome}: {valor:.6f}\n"
        texto += "\n" + resultado["observacoes"]
        self.saida.setText(texto)
