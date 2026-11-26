# -*- coding: utf-8 -*-
"""Fluxo de nova simulação: cadastros -> validação -> AquaCrop -> SQLite."""

from __future__ import annotations

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
    QLineEdit, QMessageBox, QTextEdit, QVBoxLayout,
)

from config.settings import AQUACROP_VERSION, DEMO_WEATHER_PATH
from database import connect
from database import repositories as repo
from frontand.components import BasePage, MutedLabel, SectionTitle, WarningPanel, WorkerThread
from frontand.screens.cadastros import _combobox_com_ids
from services import climate_service, simulation_service


class SimulacaoPage(BasePage):
    simulacao_concluida = Signal(int)

    def __init__(self, db_path):
        super().__init__("Nova simulação", "Selecione os dados cadastrados e execute o AquaCrop.")
        self.db_path = db_path
        self.worker = None
        self._carregado = False
        # Inicializados antes de conectar os sinais: popular os combos em
        # refresh() emite currentIndexChanged, e o slot precisa das listas.
        self._ids_area = []
        self._ids_cultura = []
        self._ids_solo = []
        self._ids_estacao = []
        self._ids_manejo = []
        self._culturas = []
        self._estacoes = []

        painel = QFrame()
        painel.setObjectName("Panel")
        form = QFormLayout(painel)
        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Opcional — ex.: Sequeiro Sorgo 2024")
        self.area = QComboBox()
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
        self.umidade = QComboBox()
        self.umidade.addItems(["FC - capacidade de campo", "WP - ponto de murcha",
                               "SAT - saturação", "Pct - percentual da água disponível"])
        self.valor_umidade = QDoubleSpinBox()
        self.valor_umidade.setRange(0, 100)
        self.valor_umidade.setValue(50)
        self.valor_umidade.setEnabled(False)
        self.umidade.currentIndexChanged.connect(
            lambda i: self.valor_umidade.setEnabled(i == 3)
        )

        for rotulo, widget in (
            ("Nome da simulação:", self.nome), ("Área agrícola:", self.area),
            ("Cultura*:", self.cultura), ("Solo*:", self.solo),
            ("Estação climática*:", self.estacao), ("Manejo de irrigação*:", self.manejo),
            ("Início*:", self.inicio), ("Plantio*:", self.plantio), ("Fim*:", self.fim),
            ("Umidade inicial:", self.umidade), ("Percentual:", self.valor_umidade),
        ):
            form.addRow(rotulo, widget)

        self.content_layout.addWidget(painel)
        self.content_layout.addWidget(
            WarningPanel(
                "A simulação usa somente dados cadastrados. Milheto permanece indisponível "
                "até parametrização documentada; nenhum resultado é gerado em caso de erro."
            )
        )

        barra = QHBoxLayout()
        self.botao_revisar = self._botao(barra, "Revisar parâmetros", "SecondaryButton", self._revisar)
        self.botao_executar = self._botao(barra, "Executar simulação", "PrimaryButton", self._executar)
        self.botao_demo = self._botao(
            barra, "Importar clima demo", "SecondaryButton", self._importar_demo
        )
        barra.addStretch()
        self.content_layout.addLayout(barra)

        self.content_layout.addWidget(SectionTitle("Saída da execução"))
        self.saida = QTextEdit()
        self.saida.setObjectName("LogBox")
        self.saida.setReadOnly(True)
        self.saida.setMinimumHeight(180)
        self.content_layout.addWidget(self.saida)
        self.content_layout.addWidget(
            MutedLabel(f"Versão do modelo: AquaCrop {AQUACROP_VERSION}")
        )
        self.estacao.currentIndexChanged.connect(self._sincronizar_datas)
        self.refresh()

    def _botao(self, layout, texto, object_name, callback):
        from PySide6.QtWidgets import QPushButton
        botao = QPushButton(texto)
        botao.setObjectName(object_name)
        botao.clicked.connect(callback)
        layout.addWidget(botao)
        return botao

    def refresh(self):
        # Guarda as escolhas antes de limpar os combos: show_page() chama
        # refresh() de novo e uma repopulação sem isso volta ao índice 0.
        anterior = {
            "area": self._id_atual(self.area, self._ids_area),
            "cultura": self._id_atual(self.cultura, self._ids_cultura),
            "solo": self._id_atual(self.solo, self._ids_solo),
            "estacao": self._id_atual(self.estacao, self._ids_estacao),
            "manejo": self._id_atual(self.manejo, self._ids_manejo),
        }
        primeira = not self._carregado
        with connect(self.db_path) as conn:
            areas = repo.list_areas(conn)
            culturas = repo.list_culturas(conn)
            solos = repo.list_solos(conn)
            estacoes = repo.list_estacoes(conn)
            manejos = repo.list_manejos(conn)
        for combo in (self.area, self.cultura, self.solo, self.estacao, self.manejo):
            combo.blockSignals(True)
        self._ids_area = _combobox_com_ids(self.area, areas)
        self._ids_cultura = _combobox_com_ids(self.cultura, culturas)
        self._ids_solo = _combobox_com_ids(self.solo, solos)
        self._ids_estacao = _combobox_com_ids(self.estacao, estacoes, incluir_vazio=False)
        self._ids_manejo = _combobox_com_ids(self.manejo, manejos, incluir_vazio=False)
        self._culturas = culturas
        self._estacoes = estacoes
        self._manejos = manejos
        self._restaurar_selecao(anterior, primeira)
        self._sincronizar_datas()
        for combo in (self.area, self.cultura, self.solo, self.estacao, self.manejo):
            combo.blockSignals(False)
        self._carregado = True

    @staticmethod
    def _id_atual(combo, ids):
        idx = combo.currentIndex()
        return ids[idx] if 0 <= idx < len(ids) else None

    @staticmethod
    def _selecionar(combo, ids, desejado, padrao=None):
        for id_ in (desejado, padrao):
            if id_ is not None and id_ in ids:
                combo.setCurrentIndex(ids.index(id_))
                return

    def _metodo_manejo(self, manejo_id):
        for manejo in self._manejos:
            if manejo["id"] != manejo_id:
                continue
            metodo = manejo.get("metodo_aquacrop")
            # 0 é válido (sequeiro): não usar ``metodo or -1``.
            return int(metodo) if metodo is not None else -1
        return -1

    def _restaurar_selecao(self, anterior, primeira):
        """Mantém escolhas válidas e aplica padrões executáveis quando falta uma."""
        self._selecionar(self.area, self._ids_area, anterior["area"])
        self._selecionar(
            self.solo, self._ids_solo, anterior["solo"],
            padrao=next((i for i in self._ids_solo if i is not None), None),
        )
        # Sorgo tem parâmetros embutidos; Milheto está bloqueado.
        self._selecionar(
            self.cultura, self._ids_cultura, anterior["cultura"],
            padrao=next(
                (cid for cid in self._ids_cultura if cid is not None and any(
                    c["id"] == cid and c.get("codigo_aquacrop") for c in self._culturas
                )),
                None,
            ),
        )
        self._selecionar(
            self.estacao, self._ids_estacao, anterior["estacao"],
            padrao=next((i for i in self._ids_estacao if i is not None), None),
        )
        # Calendário sem eventos é o primeiro em ordem alfabética e falha.
        manejo = anterior["manejo"]
        if (manejo is None or manejo not in self._ids_manejo
                or (primeira and self._metodo_manejo(manejo) == 3)):
            manejo = None
        self._selecionar(
            self.manejo, self._ids_manejo, manejo,
            padrao=next(
                (mid for mid in self._ids_manejo
                 if mid is not None and self._metodo_manejo(mid) == 0),
                None,
            ),
        )

    def _sincronizar_datas(self):
        idx = self.estacao.currentIndex()
        if idx < 0 or idx >= len(self._ids_estacao) or not self._ids_estacao[idx]:
            return
        with connect(self.db_path) as conn:
            linhas = repo.get_clima(conn, self._ids_estacao[idx])
        if not linhas:
            return
        inicio = QDate.fromString(linhas[0]["data"], "yyyy-MM-dd")
        fim = QDate.fromString(linhas[-1]["data"], "yyyy-MM-dd")
        self.inicio.setDate(inicio)
        self.fim.setDate(fim)
        plantio = inicio.addDays(min(30, max(1, inicio.daysTo(fim) - 30)))
        self.plantio.setDate(plantio)

    def _config(self):
        def selecionado(combo, ids):
            idx = combo.currentIndex()
            return ids[idx] if 0 <= idx < len(ids) else None

        cultura_id = selecionado(self.cultura, self._ids_cultura)
        solo_id = selecionado(self.solo, self._ids_solo)
        estacao_id = selecionado(self.estacao, self._ids_estacao)
        manejo_id = selecionado(self.manejo, self._ids_manejo)
        faltando = [
            nome for nome, valor in (
                ("cultura", cultura_id), ("solo", solo_id),
                ("estação climática", estacao_id), ("manejo", manejo_id),
            ) if valor is None
        ]
        if faltando:
            raise ValueError("Selecione: " + ", ".join(faltando) + ".")
        tipo = ["FC", "WP", "SAT", "Pct"][self.umidade.currentIndex()]
        return {
            "nome": self.nome.text().strip() or None,
            "area_id": selecionado(self.area, self._ids_area),
            "cultura_id": cultura_id,
            "solo_id": solo_id,
            "estacao_id": estacao_id,
            "manejo_id": manejo_id,
            "data_inicio": self.inicio.date().toString("yyyy-MM-dd"),
            "data_plantio": self.plantio.date().toString("yyyy-MM-dd"),
            "data_fim": self.fim.date().toString("yyyy-MM-dd"),
            "umidade_inicial_tipo": tipo,
            "umidade_inicial_valor": self.valor_umidade.value() if tipo == "Pct" else None,
        }

    def _revisar(self):
        try:
            config = self._config()
            with connect(self.db_path) as conn:
                preparado = simulation_service.validar_configuracao(conn, config)
        except Exception as exc:
            self._falha_validacao(exc)
            return
        cultura = preparado["verificacao"]
        resumo = climate_service_resumo(preparado["weather"])
        texto = (
            f"Nome: {config['nome'] or '(sem nome)'}\n"
            f"Cultura: {cultura['cultura']['nome']} ({cultura['codigo_aquacrop']})\n"
            f"Origem dos parâmetros: {cultura['origem']}\n"
            f"Solo: {preparado['solo']['nome']} — "
            f"{len(preparado['solo']['camadas'])} camada(s) cadastrada(s)\n"
            f"Estação: {preparado['estacao']['nome']} — {resumo}\n"
            f"Manejo: {preparado['manejo']['nome']} "
            f"(método {preparado['manejo']['metodo_aquacrop']})\n"
            f"Período: {config['data_inicio']} a {config['data_fim']} "
            f"(plantio em {config['data_plantio']})\n"
            f"Umidade inicial: {config['umidade_inicial_tipo']}\n"
            f"AquaCrop: {AQUACROP_VERSION}\n\n"
            "Parâmetros da cultura não foram calibrados localmente."
        )
        self.saida.setText(texto)

    def _importar_demo(self):
        """Atalho para destravar a tela quando ainda não há estação climática."""
        try:
            with connect(self.db_path) as conn:
                _, total = climate_service.importar_csv(
                    conn, DEMO_WEATHER_PATH, "Demonstração (origem não documentada)",
                    "DEMO-2024", eh_demonstracao=1,
                    fonte="data/demo/clima_demo.csv",
                )
        except Exception as exc:
            QMessageBox.critical(self, "Falha na importação", str(exc))
            return
        self.refresh()
        self.saida.setText(
            f"{total} dia(s) importados e marcados como DEMONSTRACAO.\n"
            "Não são dados validados do Semiárido. Confira as datas e execute a simulação."
        )

    def _falha_validacao(self, exc):
        mensagem = str(exc)
        if not self._ids_estacao:
            mensagem += (
                "\n\nNenhuma estação climática cadastrada. Abra a tela Clima e "
                "use 'Importar demonstração' ou importe um CSV medido."
            )
        self.saida.setText(f"Não foi possível continuar:\n{mensagem}")
        QMessageBox.warning(self, "Validação", mensagem)

    def _executar(self):
        try:
            config = self._config()
        except Exception as exc:
            self._falha_validacao(exc)
            return
        self.botao_executar.setEnabled(False)
        self.saida.setText("Executando AquaCrop em segundo plano...")
        self.worker = WorkerThread(simulation_service.executar, config, db_path=self.db_path)
        self.worker.resultado.connect(self._finalizar)
        self.worker.falhou.connect(self._erro)
        self.worker.start()

    def _erro(self, mensagem):
        self.botao_executar.setEnabled(True)
        self.saida.setText(f"Falha registrada:\n{mensagem}")
        QMessageBox.critical(self, "Erro na simulação", mensagem)

    def _finalizar(self, resultado):
        self.botao_executar.setEnabled(True)
        if not resultado.get("sucesso"):
            self._erro(str(resultado.get("erro")))
            return
        m = resultado["metricas"]
        fmt = lambda valor, casas=3: (
            f"{valor:.{casas}f}" if isinstance(valor, (int, float)) else "—"
        )
        self.saida.setText(
            f"Simulação #{resultado['simulacao_id']} concluída e salva.\n\n"
            f"Produtividade: {fmt(m.get('produtividade'))} t/ha\n"
            f"Produtividade potencial: {fmt(m.get('produtividade_potencial'))} t/ha\n"
            f"Biomassa final: {fmt(m.get('biomassa_final'))} t/ha\n"
            f"Irrigação: {fmt(m.get('irrigacao_sazonal'), 1)} mm\n"
            f"ET (derivada): {fmt(m.get('evapotranspiracao'), 1)} mm\n\n"
            + (m.get("observacoes") or "")
        )
        self.simulacao_concluida.emit(resultado["simulacao_id"])


def climate_service_resumo(weather):
    """Resume a série usada sem expor dados fictícios."""
    return (
        f"{len(weather)} dia(s), {weather['Date'].min():%Y-%m-%d} a "
        f"{weather['Date'].max():%Y-%m-%d}, "
        f"precipitação {weather['Precipitation'].sum():.1f} mm"
    )
