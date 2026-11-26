# -*- coding: utf-8 -*-
"""Testes de esquema, integridade referencial e repositórios."""

import sqlite3

from database import connect
from database import repositories as repo
from tests.base import TemporaryDatabaseTest


class TestSchema(TemporaryDatabaseTest):
    def test_tabelas_principais_existem(self):
        with self.conn() as conn:
            tabelas = {
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        esperadas = {
            "agricultores", "propriedades", "areas_agricolas", "culturas",
            "parametros_cultura", "estacoes", "dados_climaticos", "solos",
            "camadas_solo", "manejo_irrigacao", "agenda_irrigacao",
            "simulacoes", "resultados", "crescimento_diario", "experimentos",
            "observacoes_experimentais", "calibracoes", "parametros_calibrados",
        }
        self.assertTrue(esperadas.issubset(tabelas), esperadas - tabelas)

    def test_seed_sem_parametro_cientifico_inventado(self):
        with self.conn() as conn:
            culturas = {c["nome"]: c for c in repo.list_culturas(conn, False)}
        self.assertEqual(culturas["Sorgo"]["codigo_aquacrop"], "Sorghum")
        self.assertEqual(culturas["Sorgo"]["validada"], 1)
        self.assertIsNone(culturas["Milheto"]["codigo_aquacrop"])
        self.assertEqual(culturas["Milheto"]["validada"], 0)
        with self.conn() as conn:
            self.assertEqual(repo.list_parametros_cultura(conn, culturas["Milheto"]["id"]), [])

    def test_chave_estrangeira_e_ativada(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.conn() as conn:
                repo.create_simulacao(
                    conn,
                    {
                        "nome": None, "area_id": None, "cultura_id": 99999,
                        "solo_id": 1, "estacao_id": 1, "manejo_id": 1,
                        "data_inicio": "2024-01-01", "data_plantio": "2024-03-01",
                        "data_fim": "2024-12-31", "umidade_inicial_tipo": "FC",
                        "umidade_inicial_valor": None, "aquacrop_version": "3.1.0",
                    },
                )


class TestCadastros(TemporaryDatabaseTest):
    def test_cadeia_produtor_propriedade_area(self):
        with self.conn() as conn:
            produtor = repo.add_agricultor(
                conn, "  Maria Silva  ", cpf_cnpj="000.000.000-00"
            )
            propriedade = repo.add_propriedade(
                conn, "Sítio Verde", produtor, municipio="Petrolina", uf="PE",
                area_total_ha=12.5,
            )
            area = repo.add_area(
                conn, propriedade, "Talhão 1", area_ha=3.2, observacoes="sequeiro"
            )
            self.assertEqual(repo.list_agricultores(conn)[0]["nome"], "Maria Silva")
            self.assertEqual(
                repo.list_propriedades(conn)[0]["agricultor_nome"], "Maria Silva"
            )
            self.assertEqual(repo.list_areas(conn)[0]["propriedade_nome"], "Sítio Verde")

            repo.delete_propriedade(conn, propriedade)
            self.assertEqual(repo.list_areas(conn), [])

    def test_solo_com_camadas(self):
        with self.conn() as conn:
            solo_id = repo.add_solo(conn, "Solo de teste", textura="franco-arenoso")
            repo.add_camada_solo(
                conn, solo_id, 1, 0.2, 0.11, 0.24, 0.42, 900, 100
            )
            solo = repo.get_solo(conn, solo_id)
        self.assertEqual(len(solo["camadas"]), 1)
        self.assertEqual(solo["camadas"][0]["th_fc"], 0.24)

    def test_manejo_com_agenda_e_remocao_em_cascata(self):
        with self.conn() as conn:
            manejo_id = repo.add_manejo(
                conn, "Calendário teste", 3, lamina_irrigacao=20
            )
            repo.set_agenda_irrigacao(
                conn, manejo_id, [("2024-03-15", 20), ("2024-04-15", 25)]
            )
            manejo = repo.get_manejo(conn, manejo_id)
        self.assertEqual(len(manejo["agenda"]), 2)
        self.assertEqual(manejo["agenda"][1]["lamina"], 25)

    def test_datas_simulacao(self):
        ini, plantio, fim, dias = repo.datas_simulacao(
            "2024-01-01", "2024-01-02", "2024-01-03"
        )
        self.assertEqual(str(ini), "2024-01-01")
        self.assertEqual(str(plantio), "2024-01-02")
        self.assertEqual(str(fim), "2024-01-03")
        self.assertEqual(len(dias), 3)
        with self.assertRaises(ValueError):
            repo.datas_simulacao("2024-05-01", "2024-03-01", "2024-12-31")

    def test_parametro_registrado_com_fonte(self):
        with self.conn() as conn:
            cultura_id = repo.get_cultura_por_nome(conn, "Sorgo")["id"]
            repo.set_parametros_cultura(
                conn, cultura_id, "estudo-1", {"CCx": 0.7},
                fonte="Documento fictício apenas para teste de persistência",
                validado=0,
            )
            parametros = repo.list_parametros_cultura(conn, cultura_id, "estudo-1")
        self.assertEqual(parametros[0]["valor"], 0.7)
        self.assertIn("teste", parametros[0]["fonte"])
        self.assertEqual(parametros[0]["validado"], 0)
