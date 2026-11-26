# -*- coding: utf-8 -*-
"""Testes das validações científicas e de entrada."""

from datetime import date

import pandas as pd

from services import climate_service, validation
from tests.base import TemporaryDatabaseTest


class TestDatas(TemporaryDatabaseTest):
    def test_parse_date(self):
        self.assertEqual(validation.parse_date("2024-03-01"), date(2024, 3, 1))
        self.assertEqual(validation.parse_date("01/03/2024"), date(2024, 3, 1))
        with self.assertRaises(ValueError):
            validation.parse_date("data inválida")

    def test_ordem_das_datas(self):
        with self.assertRaisesRegex(ValueError, "entre o início e o fim"):
            validation.validar_datas("2024-03-01", "2024-01-01", "2024-12-31")


class TestClima(TemporaryDatabaseTest):
    def _planilha(self, datas=None, **kwargs):
        datas = datas or pd.date_range("2024-01-01", periods=3).strftime("%Y-%m-%d")
        dados = {
            "Date": list(datas),
            "Tmin": kwargs.get("tmin", [20, 21, 22]),
            "Tmax": kwargs.get("tmax", [30, 31, 32]),
            "Rain": kwargs.get("rain", [0, 5, 0]),
            "ETo": kwargs.get("eto", [4, 4.2, 3.8]),
        }
        return pd.DataFrame(dados)

    def test_aliases_e_ordenacao(self):
        df = self._planilha(datas=["2024-01-03", "2024-01-01", "2024-01-02"])
        resultado = validation.validar_planilha_clima(df)
        self.assertEqual(list(resultado["data"]), [
            date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)
        ])
        self.assertIn("temperatura_min", resultado.columns)

    def test_coluna_obrigatoria_ausente(self):
        df = self._planilha().drop(columns=["ETo"])
        with self.assertRaisesRegex(ValueError, "ETo"):
            validation.validar_planilha_clima(df)

    def test_data_duplicada(self):
        df = self._planilha(datas=["2024-01-01", "2024-01-01", "2024-01-03"])
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            validation.validar_planilha_clima(df)

    def test_lacuna_na_serie(self):
        df = self._planilha(datas=["2024-01-01", "2024-01-03", "2024-01-04"])
        with self.assertRaisesRegex(ValueError, "lacuna"):
            validation.validar_planilha_clima(df)

    def test_temperatura_invertida(self):
        df = self._planilha(tmin=[31, 21, 22])
        with self.assertRaisesRegex(ValueError, "mínima maior"):
            validation.validar_planilha_clima(df)

    def test_eto_invalido(self):
        df = self._planilha(eto=[4, 0, 3.8])
        with self.assertRaisesRegex(ValueError, "ETo"):
            validation.validar_planilha_clima(df)

    def test_cobertura_do_periodo(self):
        clima = climate_service.weather_from_dataframe(self._planilha()).rename(
            columns={"Date": "data"}
        )
        validation.validar_cobertura_clima(clima, "2024-01-01", "2024-01-03")
        with self.assertRaises(ValueError):
            validation.validar_cobertura_clima(clima, "2024-01-01", "2024-01-10")


class TestSolo(TemporaryDatabaseTest):
    def test_camadas_validas(self):
        camadas = validation.validar_camadas([
            {"espessura": 0.2, "th_wp": 0.11, "th_fc": 0.24, "th_s": 0.42, "ksat": 900}
        ])
        self.assertEqual(camadas[0]["penetrabilidade"], 100)

    def test_ordem_fisica_invalida(self):
        with self.assertRaisesRegex(ValueError, "th_wp < th_fc < th_s"):
            validation.validar_camadas([
                {"espessura": 0.2, "th_wp": 0.3, "th_fc": 0.24, "th_s": 0.42, "ksat": 900}
            ])

    def test_sem_camadas(self):
        with self.assertRaises(ValueError):
            validation.validar_camadas([])


class TestIrrigacao(TemporaryDatabaseTest):
    def test_sequeiro(self):
        self.assertEqual(validation.validar_irrigacao(
            {"metodo_aquacrop": 0}, [], "2024-01-01", "2024-12-31"
        ), 0)

    def test_umidade_sem_limite(self):
        with self.assertRaisesRegex(ValueError, "limite de umidade"):
            validation.validar_irrigacao(
                {"metodo_aquacrop": 1}, [], "2024-01-01", "2024-12-31"
            )

    def test_calendario_sem_evento(self):
        with self.assertRaisesRegex(ValueError, "calendário"):
            validation.validar_irrigacao(
                {"metodo_aquacrop": 3}, [], "2024-01-01", "2024-12-31"
            )

    def test_evento_fora_do_periodo(self):
        with self.assertRaisesRegex(ValueError, "fora do período"):
            validation.validar_irrigacao(
                {"metodo_aquacrop": 3},
                [{"data": "2025-01-01", "lamina": 20}],
                "2024-01-01", "2024-12-31",
            )
