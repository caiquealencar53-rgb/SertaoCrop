# -*- coding: utf-8 -*-
"""Resultados e histórico de simulações persistidas."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QLabel, QMessageBox,
    QVBoxLayout,
)

from database import connect
from database import repositories as repo
from frontand.components import BasePage, DataTable, MutedLabel, PlotCanvas, SectionTitle, Toolbar
from services.simulation_service import consultar_resultado

METRICAS = [
    ("produtividade", "Produtividade (t/ha)"),
    ("produtividade_potencial", "Potencial (t/ha)"),
    ("biomassa_final", "Biomassa final (t/ha)"),
    ("indice_colheita", "Índice de colheita"),
    ("irrigacao_sazonal", "Irrigação (mm)"),
    ("precipitacao_total", "Precipitação no período (mm)"),
    ("evapotranspiracao", "ET derivada (mm)"),
    ("produtividade_agua", "WP biomassa derivada (kg/m³)"),
    ("transpiracao_relativa_media", "Tr/TrPot médio (derivado)"),
]


class ResultadosPage(BasePage):
    def __init__(self, db_path):
        super().__init__("Resultados", "Métricas e séries diárias lidas do banco.")
        self.db_path = db_path

        painel = QFrame()
        painel.setObjectName("Panel")
        form = QFormLayout(painel)
        self.simulacoes = QComboBox()
        form.addRow("Simulação:", self.simulacoes)
        self.metadados = MutedLabel("")
        form.addRow("Origem:", self.metadados)
        self.content_layout.addWidget(painel)

        self.labels = {}
        # 3 colunas mantêm os cartões legíveis em janelas estreitas.
        grade = QGridLayout()
        for i, (chave, rotulo) in enumerate(METRICAS):
            caixa = QFrame()
            caixa.setObjectName("MetricCard")
            layout = QVBoxLayout(caixa)
            layout.addWidget(QLabel(rotulo))
            valor = QLabel("—")
            valor.setObjectName("MetricValue")
            layout.addWidget(valor)
            self.labels[chave] = valor
            grade.addWidget(caixa, i // 3, i % 3)
        self.content_layout.addLayout(grade)

        self.content_layout.addWidget(SectionTitle("Evolução temporal (dados reais da simulação)"))
        self.grafico = PlotCanvas()
        self.content_layout.addWidget(self.grafico)

        self.tabela = DataTable(
            ["Data", "DAP", "Cobertura", "Biomassa (t/ha)", "Índice colheita",
             "Raiz (m)", "Água no solo (mm)", "Tr/TrPot"]
        )
        self.content_layout.addWidget(self.tabela)
        barra = Toolbar()
        barra.add_secondary("Atualizar", self.refresh)
        barra.add_primary("Exportar série (CSV)", self._exportar)
        self.content_layout.addLayout(barra)
        self.simulacoes.currentIndexChanged.connect(self._carregar)
        self.refresh()

    def refresh(self, simulacao_id=None):
        with connect(self.db_path) as conn:
            simulacoes = repo.list_simulacoes(conn)
        self._ids = [s["id"] for s in simulacoes]
        self.simulacoes.blockSignals(True)
        self.simulacoes.clear()
        for s in simulacoes:
            self.simulacoes.addItem(
                f"#{s['id']} — {s['cultura_nome']} — {s['status']} — {s['data_execucao']}"
            )
        self.simulacoes.blockSignals(False)
        if simulacao_id is not None and simulacao_id in self._ids:
            self.simulacoes.setCurrentIndex(self._ids.index(simulacao_id))
        elif self.simulacoes.count():
            self.simulacoes.setCurrentIndex(0)
        self._carregar()

    def _carregar(self):
        idx = self.simulacoes.currentIndex()
        if idx < 0 or idx >= len(self._ids):
            self.tabela.preencher([])
            for label in self.labels.values():
                label.setText("—")
            self.grafico.limpar()
            self.grafico.desenhar()
            self.metadados.setText("Nenhuma simulação concluída.")
            return
        with connect(self.db_path) as conn:
            dados = consultar_resultado(conn, self._ids[idx])
        sim = dados["simulacao"]
        res = dados["resultado"] or {}
        self.metadados.setText(
            f"Cultura {sim['cultura_nome']} • solo {sim['solo_nome']} • "
            f"estação {sim['estacao_nome']} • manejo {sim['manejo_nome']} • "
            f"AquaCrop {sim['aquacrop_version'] or '—'} • status {sim['status']}"
            + (f" • erro: {sim['erro']}" if sim["erro"] else "")
        )
        for chave, _ in METRICAS:
            valor = res.get(chave)
            self.labels[chave].setText(f"{valor:.3f}" if isinstance(valor, (int, float)) else "—")
        if res.get("observacoes"):
            self.metadados.setText(self.metadados.text() + " • " + res["observacoes"])

        diario = dados["diario"]
        self.tabela.preencher(
            [[d["data"], d["dap"], f"{d['cobertura_dossel']:.3f}",
              f"{d['biomassa']:.3f}", f"{d['indice_colheita']:.3f}",
              f"{d['profundidade_raiz']:.2f}",
              f"{d['umidade_solo']:.1f}" if d["umidade_solo"] is not None else "—",
              f"{d['transpiracao_relativa']:.3f}"
              if d["transpiracao_relativa"] is not None else "—"]
             for d in diario]
        )

        self.grafico.limpar()
        if diario:
            from datetime import date
            eixo_x = [date.fromisoformat(d["data"]) for d in diario]
            self.grafico.eixos.plot(
                eixo_x, [d["biomassa"] for d in diario], color="#1F6F4A", label="Biomassa (t/ha)"
            )
            self.grafico.eixos.set_ylabel("Biomassa (t/ha)", color="#1F6F4A")
            eixo_direito = self.grafico.eixos.twinx()
            eixo_direito.plot(
                eixo_x, [d["cobertura_dossel"] for d in diario],
                color="#D9A441", label="Cobertura do dossel",
            )
            eixo_direito.set_ylabel("Cobertura do dossel (0-1)", color="#D9A441")
            self.grafico.eixos.set_title("Crescimento da cultura — saídas do AquaCrop")
            self.grafico.eixos.grid(alpha=0.2)
        self.grafico.desenhar()

    def _exportar(self):
        idx = self.simulacoes.currentIndex()
        if idx < 0:
            return
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Exportar série diária", "simulacao.csv", "CSV (*.csv)"
        )
        if not caminho:
            return
        with connect(self.db_path) as conn:
            dados = consultar_resultado(conn, self._ids[idx])
        import pandas as pd
        pd.DataFrame(dados["diario"]).to_csv(caminho, index=False)
        QMessageBox.information(self, "Exportado", f"Série salva em {caminho}.")


class HistoricoPage(BasePage):
    historico_selecionado = Signal(int)

    def __init__(self, db_path):
        super().__init__("Histórico", "Todas as simulações registradas no SQLite.")
        self.db_path = db_path
        self.tabela = DataTable(
            ["ID", "Nome", "Cultura", "Área", "Solo", "Estação", "Manejo",
             "Status", "Produtividade", "Execução", "Erro"]
        )
        self.content_layout.addWidget(self.tabela)
        barra = Toolbar()
        barra.add_secondary("Atualizar", self.refresh)
        barra.add_primary("Ver resultado", self._ver_resultado)
        self.content_layout.addLayout(barra)
        self.tabela.doubleClicked.connect(self._ver_resultado)
        self.refresh()

    def refresh(self):
        with connect(self.db_path) as conn:
            simulacoes = repo.list_simulacoes(conn)
        self._linhas = simulacoes
        self.tabela.preencher(
            [[s["id"], s["nome"] or "—", s["cultura_nome"], s["area_nome"] or "—",
              s["solo_nome"], s["estacao_nome"], s["manejo_nome"], s["status"],
              f"{s['produtividade']:.3f}" if s["produtividade"] is not None else "—",
              s["data_execucao"], s["erro"] or ""] for s in simulacoes]
        )

    def _ver_resultado(self):
        linha = self.tabela.currentRow()
        if linha < 0 or linha >= len(self._linhas):
            QMessageBox.information(self, "Seleção", "Selecione uma simulação.")
            return
        self.historico_selecionado.emit(self._linhas[linha]["id"])
