"""
Módulo de extração de conteúdo web.

Responsável por buscar páginas, extrair conteúdo,
converter para markdown e salvar no filesystem.
"""

from toninho.extraction.extractor import PageExtractor
from toninho.extraction.storage import LocalFileSystemStorage, StorageInterface, get_storage

__all__ = [
    "PageExtractor",
    "StorageInterface",
    "LocalFileSystemStorage",
    "get_storage",
]
