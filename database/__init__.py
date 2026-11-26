"""Camada de persistência do SertãoCrop."""

from .connection import connect, initialize_database

__all__ = ["connect", "initialize_database"]
