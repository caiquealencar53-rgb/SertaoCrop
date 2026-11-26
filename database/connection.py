# -*- coding: utf-8 -*-
"""Conexão SQLite e aplicação do schema.

Uma conexão nova é aberta por operação, com ``foreign_keys = ON`` e
``row_factory = sqlite3.Row``. O arquivo .db nunca é criado na pasta atual
por efeito colateral de import.
"""

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from config.settings import DB_PATH, SCHEMA_PATH


@contextmanager
def connect(db_path=None):
    """Context manager que comita ou desfaz a transação conforme o resultado."""
    caminho = str(db_path or DB_PATH)
    with closing(sqlite3.connect(caminho, timeout=30)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def initialize_database(db_path=None):
    """Cria/atualiza as tabelas a partir de database/schema.sql."""
    caminho = Path(db_path or DB_PATH)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with connect(caminho) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return caminho
