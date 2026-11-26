# -*- coding: utf-8 -*-
"""Compatibilidade: a janela ativa está em ``frontand.app_window``.

O arquivo original (com estado em memória, valores hardcoded e fallback que
devolvia resultados simulados) foi preservado em
``frontand/legacy/ui_main_window_original.py``. Ele não era funcional e não
deve mais ser usado: este módulo redireciona qualquer import antigo para a
implementação real, que persiste dados no SQLite e executa o AquaCrop.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from frontand.app_window import MainWindow, criar_aplicacao, main

__all__ = ["MainWindow", "criar_aplicacao", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
