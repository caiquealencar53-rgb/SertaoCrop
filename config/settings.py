# -*- coding: utf-8 -*-
"""Caminhos e constantes do projeto.

O banco fica em ``data_base/dados/`` e os scripts SQL em ``database/``,
separados conforme solicitado. O único arquivo SQLite usado pela aplicação
é ``data_base/dados/sertaocrop.db``; cópias legadas foram removidas.
"""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data_base" / "dados" / "sertaocrop.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
DEMO_WEATHER_PATH = PROJECT_ROOT / "data" / "demo" / "clima_demo.csv"

try:
    AQUACROP_VERSION = version("aquacrop")
except PackageNotFoundError:  # pragma: no cover - apenas se o pacote faltar
    AQUACROP_VERSION = "desconhecida"
