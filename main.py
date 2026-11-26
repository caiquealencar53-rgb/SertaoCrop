# -*- coding: utf-8 -*-
"""Entry point da aplicação SertãoCrop (PySide6).

Uso:
    venv/bin/python main.py

O roteiro de estudo da API do AquaCrop que estava aqui foi preservado em
``scripts/estudo_api_aquacrop.py``. Ele usa o clima de Túnis embutido no pacote
e serve apenas para entendimento da API — não é a aplicação nem dado local.
"""

from frontand.app_window import main

if __name__ == "__main__":
    raise SystemExit(main())
