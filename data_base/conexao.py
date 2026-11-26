# -*- coding: utf-8 -*-
"""Compatibilidade: o módulo ativo é ``database.connection``.

O script original criava ``sertaocrop.db`` na pasta atual como efeito colateral
de import, misturava DDL com dados e imprimia no console. Foi preservado em
``data_base/conexao_original.py``. A aplicação agora usa
``data_base/dados/sertaocrop.db`` e o schema versionado em ``database/schema.sql``.
"""

from config.settings import DB_PATH
from database.connection import connect, initialize_database

__all__ = ["connect", "initialize_database", "DB_PATH"]
