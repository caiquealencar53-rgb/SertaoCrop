# -*- coding: utf-8 -*-
"""Compatibilidade: o schema está em ``database/schema.sql``.

Este arquivo era vazio. Agora ele apenas aplica o schema versionado ao banco
ativo, sem duplicar DDL em Python.
"""

from config.settings import DB_PATH
from database import initialize_database


def criar_tabelas(caminho=DB_PATH):
    return initialize_database(caminho)


if __name__ == "__main__":
    print(f"Schema aplicado em {criar_tabelas()}")
