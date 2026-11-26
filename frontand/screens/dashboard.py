# -*- coding: utf-8 -*-
"""Dashboard com indicadores lidos do SQLite."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from config.settings import AQUACROP_VERSION
from database import connect
from database import repositories as repo
from frontand.components import (
    BasePage, DataTable, MetricCard, MutedLabel, SectionTitle, Toolbar, WarningPanel,
)


class DashboardPage(BasePage):
    nova_simulacao_solicitada = Signal()

    def __init__(self, db_path):
        super().__init__("Visão geral", "Dados reais do banco local do SertãoCrop.")
        self.db_path = db_path

        cards = QHBoxLayout()
        self.card_sim = MetricCard("Simulações realizadas")
        self.card_cult = MetricCard("Culturas cadastradas")
        self.card_solo = MetricCard("Perfis de solo")
        self.card_est = MetricCard("Estações climáticas")
        self.card_prod = MetricCard("Última produtividade", "—", "t/ha (resultado do modelo)")
        for card in (self.card_sim, self.card_cult, self.card_solo, self.card_est, self.card_prod):
            cards.addWidget(card)
        self.content_layout.addLayout(cards)

        self.aviso = WarningPanel("")
        self.aviso.hide()
        self.content_layout.addWidget(self.aviso)

        self.content_layout.addWidget(SectionTitle("Últimas simulações"))
        self.tabela = DataTable(
            ["ID", "Cultura", "Área", "Status", "Produtividade (t/ha)", "Execução"]
        )
        self.content_layout.addWidget(self.tabela)

        barra = Toolbar()
        self.botao_nova = barra.add_primary("+ Nova simulação", self.nova_simulacao_solicitada.emit)
        self.content_layout.addLayout(barra)
        self.content_layout.addWidget(
            MutedLabel(f"Motor: AquaCrop {AQUACROP_VERSION} • dados persistidos em SQLite")
        )

    def refresh(self):
        with connect(self.db_path) as conn:
            simulacoes = repo.list_simulacoes(conn, limite=8)
            culturas = repo.list_culturas(conn, apenas_ativas=False)
            solos = repo.list_solos(conn)
            estacoes = repo.list_estacoes(conn)
            demonstracao = [e for e in estacoes if e.get("eh_demonstracao")]

        concluidas = [s for s in simulacoes if s["status"] == "CONCLUIDA"]
        self.card_sim.set_value(len(simulacoes))
        self.card_cult.set_value(len(culturas))
        self.card_solo.set_value(len(solos))
        self.card_est.set_value(len(estacoes))
        self.card_prod.set_value(
            f"{concluidas[0]['produtividade']:.2f}" if concluidas and concluidas[0]["produtividade"] else "—"
        )

        self.tabela.preencher(
            [
                [
                    s["id"], s["cultura_nome"], s["area_nome"] or "—", s["status"],
                    f"{s['produtividade']:.3f}" if s["produtividade"] is not None else "—",
                    s["data_execucao"],
                ]
                for s in simulacoes
            ]
        )
        if demonstracao:
            self.aviso.setText(
                "Atenção: existe série de demonstração cadastrada ("
                + ", ".join(e["nome"] for e in demonstracao)
                + "). Ela não é dado validado do Semiárido e não deve ser usada como resultado científico."
            )
            self.aviso.show()
        else:
            self.aviso.hide()
