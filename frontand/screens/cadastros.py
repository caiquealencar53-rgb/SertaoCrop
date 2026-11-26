# -*- coding: utf-8 -*-
"""Telas de cadastro: propriedades, culturas, clima, solo e irrigação."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QInputDialog, QLineEdit, QMessageBox,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from config.settings import DEMO_WEATHER_PATH
from database import connect
from database import repositories as repo
from frontand.components import (
    BasePage, DataTable, MutedLabel, SectionTitle, Toolbar, WarningPanel,
)
from services import climate_service, validation


def _float(texto, nome):
    texto = (texto or "").strip().replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError as exc:
        raise ValueError(f"{nome} deve ser um número.") from exc


def _inteiro(texto, nome):
    valor = _float(texto, nome)
    return None if valor is None else int(valor)


def _combobox_com_ids(combo, registros, campo="nome", incluir_vazio=True):
    combo.clear()
    ids = []
    if incluir_vazio:
        combo.addItem("— selecione —")
        ids.append(None)
    for registro in registros:
        combo.addItem(str(registro[campo]))
        ids.append(registro["id"])
    return ids


class CadastroAgricolaPage(BasePage):
    """Produtor -> propriedade -> área agrícola, com dados persistentes."""

    def __init__(self, db_path):
        super().__init__("Cadastro agrícola", "Produtores, propriedades e áreas de cultivo.")
        self.db_path = db_path
        abas = QTabWidget()
        abas.addTab(self._pagina_produtor(), "Produtor")
        abas.addTab(self._pagina_propriedade(), "Propriedade")
        abas.addTab(self._pagina_area(), "Área agrícola")
        abas.addTab(self._pagina_experimento(), "Experimento")
        self.content_layout.addWidget(abas)
        self.refresh()

    def _painel(self, campos, salvar, remover):
        painel = QFrame()
        painel.setObjectName("Panel")
        layout = QVBoxLayout(painel)
        form = QFormLayout()
        campos_widgets = {}
        for rotulo, widget in campos:
            form.addRow(rotulo, widget)
            campos_widgets[rotulo] = widget
        layout.addLayout(form)
        barra = Toolbar()
        barra.add_primary("Salvar", salvar)
        barra.add_danger("Remover selecionado", remover)
        layout.addLayout(barra)
        return painel, campos_widgets

    def _pagina_produtor(self):
        self.prod_nome = QLineEdit()
        self.prod_cpf = QLineEdit()
        self.prod_tel = QLineEdit()
        self.prod_email = QLineEdit()
        painel, _ = self._painel(
            [("Nome*", self.prod_nome), ("CPF/CNPJ", self.prod_cpf),
             ("Telefone", self.prod_tel), ("E-mail", self.prod_email)],
            self._salvar_produtor, self._remover_produtor,
        )
        self.tb_prod = DataTable(["ID", "Nome", "CPF/CNPJ", "Telefone"])
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(painel)
        layout.addWidget(self.tb_prod)
        return widget

    def _pagina_propriedade(self):
        self.prop_nome = QLineEdit()
        self.prop_municipio = QLineEdit()
        self.prop_uf = QLineEdit()
        self.prop_lat = QLineEdit()
        self.prop_lon = QLineEdit()
        self.prop_area = QLineEdit()
        self.prop_produtor = QComboBox()
        painel, _ = self._painel(
            [("Nome*", self.prop_nome), ("Produtor", self.prop_produtor),
             ("Município", self.prop_municipio), ("UF", self.prop_uf),
             ("Latitude", self.prop_lat), ("Longitude", self.prop_lon),
             ("Área total (ha)", self.prop_area)],
            self._salvar_propriedade, self._remover_propriedade,
        )
        self.tb_prop = DataTable(["ID", "Nome", "Produtor", "Município", "UF"])
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(painel)
        layout.addWidget(self.tb_prop)
        return widget

    def _pagina_area(self):
        self.area_nome = QLineEdit()
        self.area_prop = QComboBox()
        self.area_solo = QComboBox()
        self.area_lat = QLineEdit()
        self.area_lon = QLineEdit()
        self.area_ha = QLineEdit()
        self.area_obs = QLineEdit()
        painel, _ = self._painel(
            [("Nome*", self.area_nome), ("Propriedade*", self.area_prop),
             ("Solo", self.area_solo), ("Latitude", self.area_lat),
             ("Longitude", self.area_lon), ("Área (ha)", self.area_ha),
             ("Observações", self.area_obs)],
            self._salvar_area, self._remover_area,
        )
        self.tb_area = DataTable(["ID", "Área", "Propriedade", "Solo", "Ha"])
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(painel)
        layout.addWidget(self.tb_area)
        return widget

    def _pagina_experimento(self):
        self.exp_nome = QLineEdit()
        self.exp_instituicao = QLineEdit()
        self.exp_local = QLineEdit()
        self.exp_fonte = QLineEdit()
        painel, _ = self._painel(
            [("Nome*", self.exp_nome), ("Instituição", self.exp_instituicao),
             ("Local", self.exp_local), ("Fonte", self.exp_fonte)],
            self._salvar_experimento, self._remover_experimento,
        )
        self.tb_exp = DataTable(["ID", "Nome", "Instituição", "Fonte"])
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(painel)
        layout.addWidget(self.tb_exp)
        return widget

    def refresh(self):
        with connect(self.db_path) as conn:
            produtores = repo.list_agricultores(conn)
            propriedades = repo.list_propriedades(conn)
            solos = repo.list_solos(conn)
            areas = repo.list_areas(conn)
            experimentos = repo.list_experimentos(conn)
        self._ids_prod = _combobox_com_ids(self.prop_produtor, produtores)
        self._ids_prop = _combobox_com_ids(self.area_prop, propriedades)
        self._ids_solo = _combobox_com_ids(self.area_solo, solos)

        self.tb_prod.preencher([[p["id"], p["nome"], p["cpf_cnpj"], p["telefone"]] for p in produtores])
        self.tb_prop.preencher(
            [[p["id"], p["nome"], p["agricultor_nome"] or "—", p["municipio"], p["uf"]]
             for p in propriedades]
        )
        self.tb_area.preencher(
            [[a["id"], a["nome"], a["propriedade_nome"], a["solo_nome"] or "—", a["area_ha"]]
             for a in areas]
        )
        self.tb_exp.preencher(
            [[e["id"], e["nome"], e["instituicao"] or "—", e["fonte"] or "—"]
             for e in experimentos]
        )

    def _salvar_experimento(self):
        if not self.exp_nome.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe o nome do experimento.")
            return
        with connect(self.db_path) as conn:
            repo.add_experimento(
                conn, self.exp_nome.text(),
                instituicao=self.exp_instituicao.text() or None,
                local=self.exp_local.text() or None,
                fonte=self.exp_fonte.text() or None,
            )
        self.exp_nome.clear()
        self.refresh()

    def _remover_experimento(self):
        with connect(self.db_path) as conn:
            experimentos = repo.list_experimentos(conn)
        linha = self.tb_exp.currentRow()
        if linha < 0 or linha >= len(experimentos):
            QMessageBox.information(self, "Seleção", "Selecione um experimento.")
            return
        with connect(self.db_path) as conn:
            conn.execute("DELETE FROM experimentos WHERE id = ?", (experimentos[linha]["id"],))
        self.refresh()

    def _id_selecionado(self, tabela, atributo):
        linha = tabela.currentRow()
        ids = getattr(self, atributo, [])
        if linha < 0 or linha >= len(ids) or ids[linha] is None:
            QMessageBox.information(self, "Seleção", "Selecione um registro na tabela.")
            return None
        return ids[linha]

    def _salvar_produtor(self):
        if not self.prod_nome.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe o nome do produtor.")
            return
        with connect(self.db_path) as conn:
            repo.add_agricultor(
                conn, self.prod_nome.text(), cpf_cnpj=self.prod_cpf.text() or None,
                telefone=self.prod_tel.text() or None, email=self.prod_email.text() or None,
            )
        self.prod_nome.clear()
        self.refresh()

    def _remover_produtor(self):
        with connect(self.db_path) as conn:
            produtores = repo.list_agricultores(conn)
        linha = self.tb_prod.currentRow()
        if linha < 0 or linha >= len(produtores):
            QMessageBox.information(self, "Seleção", "Selecione um produtor.")
            return
        with connect(self.db_path) as conn:
            repo.delete_agricultor(conn, produtores[linha]["id"])
        self.refresh()

    def _salvar_propriedade(self):
        if not self.prop_nome.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe o nome da propriedade.")
            return
        idx = self.prop_produtor.currentIndex()
        produtor_id = self._ids_prod[idx] if 0 <= idx < len(self._ids_prod) else None
        try:
            with connect(self.db_path) as conn:
                repo.add_propriedade(
                    conn, self.prop_nome.text(), produtor_id,
                    municipio=self.prop_municipio.text() or None,
                    uf=self.prop_uf.text() or None,
                    latitude=_float(self.prop_lat.text(), "Latitude"),
                    longitude=_float(self.prop_lon.text(), "Longitude"),
                    area_total_ha=_float(self.prop_area.text(), "Área total"),
                )
        except ValueError as exc:
            QMessageBox.warning(self, "Aviso", str(exc))
            return
        self.prop_nome.clear()
        self.refresh()

    def _remover_propriedade(self):
        with connect(self.db_path) as conn:
            propriedades = repo.list_propriedades(conn)
        linha = self.tb_prop.currentRow()
        if linha < 0 or linha >= len(propriedades):
            QMessageBox.information(self, "Seleção", "Selecione uma propriedade.")
            return
        with connect(self.db_path) as conn:
            repo.delete_propriedade(conn, propriedades[linha]["id"])
        self.refresh()

    def _salvar_area(self):
        idx_prop = self.area_prop.currentIndex()
        if not self.area_nome.text().strip() or idx_prop <= 0:
            QMessageBox.warning(self, "Aviso", "Informe o nome e selecione a propriedade.")
            return
        idx_solo = self.area_solo.currentIndex()
        solo_id = self._ids_solo[idx_solo] if idx_solo > 0 else None
        try:
            with connect(self.db_path) as conn:
                repo.add_area(
                    conn, self._ids_prop[idx_prop], self.area_nome.text(),
                    solo_id=solo_id,
                    latitude=_float(self.area_lat.text(), "Latitude"),
                    longitude=_float(self.area_lon.text(), "Longitude"),
                    area_ha=_float(self.area_ha.text(), "Área"),
                    observacoes=self.area_obs.text() or None,
                )
        except ValueError as exc:
            QMessageBox.warning(self, "Aviso", str(exc))
            return
        self.area_nome.clear()
        self.refresh()

    def _remover_area(self):
        with connect(self.db_path) as conn:
            areas = repo.list_areas(conn)
        linha = self.tb_area.currentRow()
        if linha < 0 or linha >= len(areas):
            QMessageBox.information(self, "Seleção", "Selecione uma área.")
            return
        with connect(self.db_path) as conn:
            repo.delete_area(conn, areas[linha]["id"])
        self.refresh()


class CulturasPage(BasePage):
    """Culturas e rastreabilidade dos parâmetros (sem valores inventados)."""

    def __init__(self, db_path):
        super().__init__("Culturas", "Sorgo e milheto: disponibilidade real de parâmetros.")
        self.db_path = db_path
        self.content_layout.addWidget(
            WarningPanel(
                "Milheto não possui parametrização no AquaCrop 3.1.0: o cadastro existe, "
                "mas a simulação permanece bloqueada até que parâmetros documentados sejam registrados."
            )
        )
        self.tabela = DataTable(
            ["ID", "Cultura", "Nome científico", "Código AquaCrop", "Parâmetro disponível", "Observações"]
        )
        self.content_layout.addWidget(self.tabela)
        barra = Toolbar()
        barra.add_primary("Registrar parâmetro documentado", self._adicionar_parametro)
        self.content_layout.addLayout(barra)
        self.content_layout.addWidget(SectionTitle("Parâmetros registrados"))
        self.tb_parametros = DataTable(
            ["Cultura", "Versão", "Parâmetro", "Valor", "Fonte", "Validado"]
        )
        self.content_layout.addWidget(self.tb_parametros)
        self.tabela.itemSelectionChanged.connect(self._carregar_parametros)
        self.refresh()

    def refresh(self):
        with connect(self.db_path) as conn:
            culturas = repo.list_culturas(conn, apenas_ativas=False)
            parametros = [
                (c["nome"], p)
                for c in culturas
                for p in repo.list_parametros_cultura(conn, c["id"])
            ]
        self._culturas = culturas
        self.tabela.preencher(
            [
                [c["id"], c["nome"], c["nome_cientifico"] or "—",
                 c["codigo_aquacrop"] or "—", "Sim" if c["validada"] else "Não",
                 c["observacoes"] or ""]
                for c in culturas
            ]
        )
        self.tb_parametros.preencher(
            [[nome, p["versao"], p["nome_parametro"], p["valor"],
              p["fonte"] or "—", "Sim" if p["validado"] else "Não"]
             for nome, p in parametros]
        )

    def _carregar_parametros(self):
        self.refresh()

    def _adicionar_parametro(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma cultura.")
            return
        cultura = self._culturas[linha]
        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"Parâmetro documentado — {cultura['nome']}")
        form = QFormLayout(dialogo)
        nome = QLineEdit()
        valor = QDoubleSpinBox()
        valor.setDecimals(6)
        valor.setRange(-1e6, 1e6)
        unidade = QLineEdit()
        fonte = QLineEdit()
        fonte.setPlaceholderText("Publicação, manual ou planilha de origem")
        validado = QCheckBox("Parâmetro validado cientificamente")
        form.addRow("Parâmetro:", nome)
        form.addRow("Valor:", valor)
        form.addRow("Unidade:", unidade)
        form.addRow("Fonte:*", fonte)
        form.addRow("", validado)
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialogo.accept)
        botoes.rejected.connect(dialogo.reject)
        form.addRow(botoes)
        if not dialogo.exec() or not nome.text().strip() or not fonte.text().strip():
            QMessageBox.warning(self, "Aviso", "Parâmetro e fonte são obrigatórios.")
            return
        with connect(self.db_path) as conn:
            repo.set_parametros_cultura(
                conn, cultura["id"], "documentada-1",
                {nome.text().strip(): valor.value()},
                fonte=fonte.text().strip(), validado=int(validado.isChecked()),
            )
        self.refresh()


class ClimaPage(BasePage):
    """Importação e consulta de séries climáticas persistidas."""

    def __init__(self, db_path):
        super().__init__("Dados climáticos", "Temperatura, precipitação e ETo por estação.")
        self.db_path = db_path
        # currentIndexChanged dispara ao popular o combo em refresh().
        self._ids_est = []
        self._estacoes = []
        painel = QFrame()
        painel.setObjectName("Panel")
        form = QFormLayout(painel)
        self.estacoes = QComboBox()
        form.addRow("Estação:", self.estacoes)
        self.resumo_label = MutedLabel("")
        form.addRow("Resumo:", self.resumo_label)
        self.content_layout.addWidget(painel)

        self.tabela = DataTable(
            ["Data", "Tmin (°C)", "Tmax (°C)", "Precip. (mm)", "ETo (mm)", "Origem"]
        )
        self.content_layout.addWidget(self.tabela)
        barra = Toolbar()
        barra.add_primary("Importar CSV", self._importar_csv)
        barra.add_primary("Importar demonstração", self._importar_demo)
        barra.add_primary("Inserir dia manualmente", self._inserir_manual)
        barra.add_danger("Remover estação", self._remover_estacao)
        self.content_layout.addLayout(barra)
        self.content_layout.addWidget(
            WarningPanel(
                "O AquaCrop exige série diária contínua e ETo positivo. "
                "Dados de demonstração ficam marcados como DEMONSTRACAO."
            )
        )
        self.estacoes.currentIndexChanged.connect(self._carregar_dados)
        self.refresh()

    def refresh(self):
        with connect(self.db_path) as conn:
            estacoes = repo.list_estacoes(conn)
        self.estacoes.blockSignals(True)
        self._ids_est = _combobox_com_ids(self.estacoes, estacoes, incluir_vazio=False)
        self._estacoes = estacoes
        self.estacoes.blockSignals(False)
        self._carregar_dados()

    def _carregar_dados(self):
        idx = self.estacoes.currentIndex()
        if idx < 0 or idx >= len(self._ids_est) or self._ids_est[idx] is None:
            self.tabela.preencher([])
            self.resumo_label.setText("Nenhuma estação cadastrada.")
            return
        with connect(self.db_path) as conn:
            linhas = repo.get_clima(conn, self._ids_est[idx])
        self.tabela.preencher(
            [[l["data"], l["temperatura_min"], l["temperatura_max"],
              l["precipitacao"], l["eto"], l["origem"]] for l in linhas]
        )
        resumo = climate_service.resumo(linhas)
        self.resumo_label.setText(
            f"{resumo['dias']} dia(s) • {resumo.get('inicio', '—')} a {resumo.get('fim', '—')} "
            f"• precipitação total {resumo.get('precipitacao_total_mm', 0):.1f} mm "
            f"• origem: {resumo.get('origem', '—')}"
        )

    def _importar_csv(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo climático", "", "CSV/TXT (*.csv *.txt)"
        )
        if not caminho:
            return
        nome, ok = QInputDialog.getText(self, "Estação", "Nome da estação:")
        if not ok or not nome.strip():
            return
        codigo, ok = QInputDialog.getText(self, "Estação", "Código único:")
        if not ok or not codigo.strip():
            return
        try:
            with connect(self.db_path) as conn:
                estacao_id, total = climate_service.importar_csv(
                    conn, caminho, nome, codigo, fonte=str(caminho)
                )
        except Exception as exc:
            QMessageBox.critical(self, "Falha na importação", str(exc))
            return
        self.refresh()
        idx = self._ids_est.index(estacao_id)
        self.estacoes.setCurrentIndex(idx)
        QMessageBox.information(self, "Importação concluída", f"{total} dia(s) importados.")

    def _importar_demo(self):
        try:
            with connect(self.db_path) as conn:
                estacao_id, total = climate_service.importar_csv(
                    conn, DEMO_WEATHER_PATH, "Demonstração (origem não documentada)",
                    "DEMO-2024", eh_demonstracao=1,
                    fonte="data/demo/clima_demo.csv",
                )
        except Exception as exc:
            QMessageBox.critical(self, "Falha", str(exc))
            return
        self.refresh()
        self.estacoes.setCurrentIndex(self._ids_est.index(estacao_id))
        QMessageBox.information(
            self, "Demonstração importada",
            f"{total} dia(s) marcados como DEMONSTRACAO. Não usar como dado científico.",
        )

    def _inserir_manual(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Inserir dia climático")
        form = QFormLayout(dialogo)
        data_edit = QDateEdit(QDate.currentDate())
        data_edit.setCalendarPopup(True)
        tmin = QDoubleSpinBox(); tmin.setRange(-50, 60); tmin.setDecimals(2)
        tmax = QDoubleSpinBox(); tmax.setRange(-50, 60); tmax.setDecimals(2)
        chuva = QDoubleSpinBox(); chuva.setRange(0, 2000); chuva.setDecimals(2)
        eto = QDoubleSpinBox(); eto.setRange(0.1, 100); eto.setDecimals(2)
        form.addRow("Data:", data_edit)
        form.addRow("Tmin (°C):", tmin)
        form.addRow("Tmax (°C):", tmax)
        form.addRow("Precipitação (mm):", chuva)
        form.addRow("ETo (mm):", eto)
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialogo.accept)
        botoes.rejected.connect(dialogo.reject)
        form.addRow(botoes)
        if not dialogo.exec():
            return
        idx = self.estacoes.currentIndex()
        estacao_id = self._ids_est[idx] if idx >= 0 else None
        if estacao_id is None:
            QMessageBox.information(self, "Aviso", "Cadastre ou importe uma estação primeiro.")
            return
        registro = {
            "data": validation.parse_date(data_edit.date().toString("yyyy-MM-dd")),
            "temperatura_min": tmin.value(),
            "temperatura_max": tmax.value(),
            "precipitacao": chuva.value(),
            "eto": eto.value(),
        }
        try:
            with connect(self.db_path) as conn:
                repo.upsert_clima(conn, estacao_id, [registro], origem="MANUAL", validado=0)
        except Exception as exc:
            QMessageBox.critical(self, "Falha", str(exc))
            return
        self._carregar_dados()

    def _remover_estacao(self):
        idx = self.estacoes.currentIndex()
        if idx < 0:
            return
        estacao_id = self._ids_est[idx]
        with connect(self.db_path) as conn:
            usada = conn.execute(
                "SELECT COUNT(*) AS n FROM simulacoes WHERE estacao_id = ?", (estacao_id,)
            ).fetchone()["n"]
        if usada:
            QMessageBox.warning(self, "Aviso", "Estação usada em simulações; não é possível remover.")
            return
        if QMessageBox.question(self, "Confirmar", "Remover a estação e todos os seus dados?") \
                != QMessageBox.StandardButton.Yes:
            return
        with connect(self.db_path) as conn:
            repo.delete_estacao(conn, estacao_id)
        self.refresh()


class SolosPage(BasePage):
    """Perfis de solo com camadas validadas."""

    def __init__(self, db_path):
        super().__init__("Dados do solo", "Perfis embutidos do AquaCrop e perfis cadastrados.")
        self.db_path = db_path
        self.tabela = DataTable(
            ["ID", "Nome", "Tipo", "Textura", "Código AquaCrop", "Camadas", "Origem"]
        )
        self.content_layout.addWidget(self.tabela)
        barra = Toolbar()
        barra.add_primary("Novo perfil com camadas", self._novo_perfil)
        barra.add_danger("Remover selecionado", self._remover)
        self.content_layout.addLayout(barra)
        self.content_layout.addWidget(
            MutedLabel(
                "Regra física exigida pelo AquaCrop: 0 < th_wp < th_fc < th_s < 1 e Ksat > 0."
            )
        )
        self.refresh()

    def refresh(self):
        with connect(self.db_path) as conn:
            solos = repo.list_solos(conn)
            perfis = [repo.get_solo(conn, s["id"]) for s in solos]
        self._solos = perfis
        self.tabela.preencher(
            [[s["id"], s["nome"], s["tipo"] or "—", s["textura"] or "—",
              s["codigo_aquacrop"] or "—", len(s["camadas"]),
              "cadastrado" if s["camadas"] else "AquaCrop (embutido)"]
             for s in perfis]
        )

    def _novo_perfil(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Novo perfil de solo")
        layout = QVBoxLayout(dialogo)
        form = QFormLayout()
        nome = QLineEdit()
        tipo = QLineEdit()
        textura = QLineEdit()
        form.addRow("Nome*:", nome)
        form.addRow("Tipo:", tipo)
        form.addRow("Textura:", textura)
        layout.addLayout(form)

        tabela = DataTable(
            ["Espessura (m)", "th_wp", "th_fc", "th_s", "Ksat", "Penetrab."], False
        )
        layout.addWidget(tabela)
        barra = Toolbar()
        barra.add_primary("Adicionar camada", lambda: tabela.preencher(
            [["0.20", "0.110", "0.240", "0.420", "900", "100"]]
            + [[tabela.item(r, c).text() for c in range(tabela.columnCount())]
               for r in range(tabela.rowCount())]
        ))
        barra.add_secondary("Remover última", lambda: tabela.setRowCount(max(0, tabela.rowCount() - 1)))
        layout.addLayout(barra)
        botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botoes.accepted.connect(dialogo.accept)
        botoes.rejected.connect(dialogo.reject)
        layout.addWidget(botoes)
        if not dialogo.exec():
            return
        camadas = []
        for r in range(tabela.rowCount()):
            camadas.append({
                "espessura": _float(tabela.item(r, 0).text(), "espessura"),
                "th_wp": _float(tabela.item(r, 1).text(), "th_wp"),
                "th_fc": _float(tabela.item(r, 2).text(), "th_fc"),
                "th_s": _float(tabela.item(r, 3).text(), "th_s"),
                "ksat": _float(tabela.item(r, 4).text(), "Ksat"),
                "penetrabilidade": _float(tabela.item(r, 5).text(), "penetrabilidade"),
            })
        try:
            camadas = validation.validar_camadas(camadas)
            if not nome.text().strip():
                raise ValueError("Informe o nome do perfil.")
            with connect(self.db_path) as conn:
                solo_id = repo.add_solo(
                    conn, nome.text().strip(), tipo=tipo.text() or None,
                    textura=textura.text() or None, validado=1,
                )
                for i, camada in enumerate(camadas, start=1):
                    repo.add_camada_solo(conn, solo_id, i, **camada)
        except Exception as exc:
            QMessageBox.critical(self, "Falha ao salvar", str(exc))
            return
        self.refresh()

    def _remover(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return
        solo = self._solos[linha]
        with connect(self.db_path) as conn:
            usado = conn.execute(
                "SELECT COUNT(*) AS n FROM simulacoes WHERE solo_id = ?", (solo["id"],)
            ).fetchone()["n"]
        if usado:
            QMessageBox.warning(self, "Aviso", "Solo usado em simulações; não é possível remover.")
            return
        with connect(self.db_path) as conn:
            repo.delete_solo(conn, solo["id"])
        self.refresh()


class IrrigacaoPage(BasePage):
    """Manejos de irrigação e calendários de aplicação."""

    def __init__(self, db_path):
        super().__init__("Manejo de irrigação", "Sequeiro, umidade, intervalo e calendário.")
        self.db_path = db_path
        painel = QFrame()
        painel.setObjectName("Panel")
        form = QFormLayout(painel)
        self.nome = QLineEdit()
        self.metodo = QComboBox()
        self.metodo.addItems(["0 - Sequeiro", "1 - Por umidade", "2 - Por intervalo", "3 - Calendário"])
        self.limite = QDoubleSpinBox(); self.limite.setRange(0, 100); self.limite.setValue(70)
        self.intervalo = QSpinBox(); self.intervalo.setRange(1, 365); self.intervalo.setValue(3)
        self.lamina = QDoubleSpinBox(); self.lamina.setRange(0, 500); self.lamina.setValue(20)
        form.addRow("Nome*:", self.nome)
        form.addRow("Método:", self.metodo)
        form.addRow("Limite de umidade (%):", self.limite)
        form.addRow("Intervalo (dias):", self.intervalo)
        form.addRow("Lâmina (mm):", self.lamina)
        barra = Toolbar()
        barra.add_primary("Salvar manejo", self._salvar)
        form.addRow(barra)
        self.content_layout.addWidget(painel)

        self.tabela = DataTable(["ID", "Nome", "Método", "Limite", "Lâmina", "Intervalo"])
        self.content_layout.addWidget(self.tabela)
        self.content_layout.addWidget(SectionTitle("Calendário do manejo selecionado"))
        self.tb_agenda = DataTable(["Data", "Lâmina (mm)"])
        self.content_layout.addWidget(self.tb_agenda)
        barra2 = Toolbar()
        barra2.add_primary("Adicionar evento", self._adicionar_evento)
        barra2.add_secondary("Limpar calendário", self._limpar_agenda)
        self.content_layout.addLayout(barra2)
        self.tabela.itemSelectionChanged.connect(self._carregar_agenda)
        self.refresh()

    def refresh(self):
        with connect(self.db_path) as conn:
            manejos = repo.list_manejos(conn)
        self._manejos = manejos
        self.tabela.preencher(
            [[m["id"], m["nome"], m["metodo_aquacrop"], m["limite_umidade"],
              m["lamina_irrigacao"], m["intervalo"]] for m in manejos]
        )
        self._carregar_agenda()

    def _carregar_agenda(self):
        linha = self.tabela.currentRow()
        if linha < 0 or linha >= len(getattr(self, "_manejos", [])):
            self.tb_agenda.preencher([])
            return
        with connect(self.db_path) as conn:
            manejo = repo.get_manejo(conn, self._manejos[linha]["id"])
        self.tb_agenda.preencher(
            [[e["data"], e["lamina"]] for e in manejo["agenda"]]
        )

    def _salvar(self):
        if not self.nome.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe o nome do manejo.")
            return
        metodo = self.metodo.currentIndex()
        try:
            with connect(self.db_path) as conn:
                repo.add_manejo(
                    conn, self.nome.text().strip(), metodo,
                    limite_umidade=self.limite.value() if metodo == 1 else None,
                    lamina_irrigacao=self.lamina.value() if metodo in (2, 3) else None,
                    intervalo=self.intervalo.value() if metodo == 2 else None,
                    descricao="Cadastrado pelo usuário",
                )
        except Exception as exc:
            QMessageBox.critical(self, "Falha ao salvar", str(exc))
            return
        self.nome.clear()
        self.refresh()

    def _adicionar_evento(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.information(self, "Seleção", "Selecione um manejo.")
            return
        manejo = self._manejos[linha]
        if manejo["metodo_aquacrop"] != 3:
            QMessageBox.information(self, "Aviso", "Calendário só se aplica ao método 3.")
            return
        data, ok = QInputDialog.getText(self, "Data", "Data da irrigação (AAAA-MM-DD):")
        if not ok:
            return
        valor, ok = QInputDialog.getDouble(self, "Lâmina", "Lâmina (mm):", 20, 0, 500, 2)
        if not ok:
            return
        try:
            validation.parse_date(data)
            with connect(self.db_path) as conn:
                atual = repo.get_manejo(conn, manejo["id"])["agenda"]
                eventos = [(e["data"], e["lamina"]) for e in atual] + [(data, valor)]
                repo.set_agenda_irrigacao(conn, manejo["id"], eventos)
        except Exception as exc:
            QMessageBox.critical(self, "Falha", str(exc))
            return
        self._carregar_agenda()

    def _limpar_agenda(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return
        with connect(self.db_path) as conn:
            repo.set_agenda_irrigacao(conn, self._manejos[linha]["id"], [])
        self._carregar_agenda()
