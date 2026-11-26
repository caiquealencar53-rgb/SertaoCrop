"""Integração com a biblioteca AquaCrop.

O nome do pacote não é ``aquacrop`` para não sombrear o pacote instalado
(``import aquacrop`` precisa continuar resolvendo para a biblioteca FAO).
"""

from . import adapter, crop_parameters

__all__ = ["adapter", "crop_parameters"]
