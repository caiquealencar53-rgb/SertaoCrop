# -*- coding: utf-8 -*-
"""Descoberta e verificação da parametrização de culturas.

A lista de culturas suportadas vem da própria biblioteca instalada — nunca é
hardcoded. Isso evita apresentar resultados de uma cultura que o modelo não
sabe simular.
"""

from __future__ import annotations

from aquacrop import Crop
from aquacrop.entities.crop import crop_params

from config.settings import AQUACROP_VERSION
from database import repositories as repo

# Mapeamento entre os nomes usados na interface e os códigos do AquaCrop.
NOMES_INTERFACE = {
    "Sorgo": "Sorghum",
    "Milheto": None,  # sem parametrização no AquaCrop 3.x
}


class CulturaIndisponivel(ValueError):
    """A cultura não possui parametrização utilizável no modelo instalado."""


def culturas_suportadas() -> list[str]:
    return sorted(crop_params.keys())


def verificar_cultura(conn, cultura_id: int) -> dict:
    """Verifica se a cultura cadastrada pode ser simulada.

    Levanta ``CulturaIndisponivel`` quando não há parametrização compatível.
    """
    cultura = repo.get_cultura(conn, cultura_id)
    if not cultura:
        raise CulturaIndisponivel("Cultura não encontrada.")

    codigo = cultura.get("codigo_aquacrop") or NOMES_INTERFACE.get(cultura["nome"])
    if not codigo or codigo not in crop_params:
        raise CulturaIndisponivel(
            f"'{cultura['nome']}' não possui parametrização no AquaCrop "
            f"{AQUACROP_VERSION}. Culturas disponíveis: "
            + ", ".join(culturas_suportadas())
            + ". Para habilitar, registre parâmetros documentados em parametros_cultura "
            "e marque a cultura como validada."
        )
    if not cultura["validada"]:
        raise CulturaIndisponivel(
            f"'{cultura['nome']}' está desativada para simulação até que a origem "
            "de seus parâmetros seja confirmada."
        )
    return {
        "cultura": cultura,
        "codigo_aquacrop": codigo,
        "parametros": dict(crop_params[codigo]),
        "versao_aquacrop": AQUACROP_VERSION,
        "origem": f"parâmetros embutidos do aquacrop {AQUACROP_VERSION}",
        "calibrada_localmente": False,
    }


def parametros_efetivos(codigo: str) -> dict:
    """Parâmetros reais que o AquaCrop usará para uma cultura embutida."""
    return dict(crop_params[codigo])


def criar_crop(verificacao: dict, data_plantio: str, data_colheita: str | None = None,
               overrides: dict | None = None) -> Crop:
    """Instancia ``Crop`` sem passar valores ``None`` (que corromperiam os padrões)."""
    kwargs = {}
    for nome, valor in (overrides or {}).items():
        if valor is not None:
            kwargs[nome] = valor
    return Crop(
        verificacao["codigo_aquacrop"],
        planting_date=data_plantio,
        harvest_date=data_colheita,
        **kwargs,
    )
