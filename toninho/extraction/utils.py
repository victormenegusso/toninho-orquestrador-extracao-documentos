"""
Utilitários para o módulo de extração.
"""

import re
from urllib.parse import urlparse


def sanitize_filename(url: str, max_length: int = 100) -> str:
    """
    Gera um nome de arquivo seguro a partir de uma URL.

    Args:
        url: URL de origem
        max_length: Comprimento máximo do nome (sem extensão)

    Returns:
        Nome de arquivo com extensão .md
    """
    parsed = urlparse(url)

    # Usar path da URL, ou "index" se vazio
    path = parsed.path.strip("/")
    if not path:
        # Usar hostname quando não há path
        path = parsed.netloc.replace(".", "_") if parsed.netloc else "index"
    else:
        # Substituir separadores de path por hífen
        path = path.replace("/", "-")

    # Remover caracteres inválidos (manter apenas letras, dígitos, - e _)
    path = re.sub(r"[^\w\-]", "_", path)

    # Remover múltiplos underscores/hifens consecutivos
    path = re.sub(r"[-_]{2,}", "_", path)

    # Truncar se necessário
    if len(path) > max_length:
        path = path[:max_length]

    # Limpar bordas
    path = path.strip("-_")

    if not path:
        path = "index"

    return f"{path}.md"


def build_output_path(processo_id: str, execucao_id: str, url: str) -> str:
    """
    Constrói o caminho relativo de saída para um arquivo extraído.

    Formato: <processo_id>/<execucao_id>/<filename>

    Args:
        processo_id: UUID do processo
        execucao_id: UUID da execução
        url: URL da página extraída

    Returns:
        Caminho relativo para salvar o arquivo
    """
    filename = sanitize_filename(url)
    return f"{processo_id}/{execucao_id}/{filename}"
