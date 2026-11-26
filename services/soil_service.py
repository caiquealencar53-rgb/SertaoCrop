# -*- coding: utf-8 -*-
"""Serviço de solos: converte perfis cadastrados em objetos do AquaCrop."""

from __future__ import annotations

from aquacrop import Soil

from services.validation import validar_camadas


def criar_solo(solo: dict) -> Soil:
    """Cria ``Soil`` a partir de um perfil do banco.

    Perfis com ``codigo_aquacrop`` usam o conjunto embutido; perfis com camadas
    cadastradas usam ``Soil('custom')`` e ``add_layer``.
    """
    camadas = solo.get("camadas") or []
    if camadas:
        objetos = validar_camadas(camadas)
        solo_obj = Soil("custom")
        for camada in objetos:
            solo_obj.add_layer(
                thickness=camada["espessura"],
                thWP=camada["th_wp"],
                thFC=camada["th_fc"],
                thS=camada["th_s"],
                Ksat=camada["ksat"],
                penetrability=camada["penetrabilidade"],
            )
        return solo_obj

    codigo = solo.get("codigo_aquacrop")
    if not codigo:
        raise ValueError(
            f"O solo '{solo.get('nome')}' não tem camadas cadastradas nem código AquaCrop."
        )
    return Soil(codigo)


def descricao_perfil(solo: dict) -> str:
    camadas = solo.get("camadas") or []
    if camadas:
        valores = validar_camadas(camadas)
        total = sum(c["espessura"] for c in valores)
        return (
            f"{len(valores)} camada(s), {total:.2f} m de profundidade, "
            f"th_fc={valores[0]['th_fc']:.3f}, th_wp={valores[0]['th_wp']:.3f}"
        )
    return f"Perfil embutido AquaCrop: {solo.get('codigo_aquacrop')}"
