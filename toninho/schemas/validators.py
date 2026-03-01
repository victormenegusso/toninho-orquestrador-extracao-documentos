"""
Validators reutilizáveis para schemas Pydantic.

Fornece funções de validação customizadas compartilhadas entre schemas.
"""
import os
from typing import Any
from urllib.parse import urlparse

from pydantic import field_validator


def validate_url(url: str) -> str:
    """
    Valida formato de URL.

    Args:
        url: URL a ser validada

    Returns:
        str: URL validada

    Raises:
        ValueError: Se URL for inválida
    """
    if not url:
        raise ValueError("URL não pode ser vazia")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL deve usar protocolo http ou https: {url}")

    if not parsed.netloc:
        raise ValueError(f"URL deve ter um domínio válido: {url}")

    return url


def validate_cron_expression(cron: str) -> str:
    """
    Valida sintaxe básica de expressão cron.

    Args:
        cron: Expressão cron a ser validada

    Returns:
        str: Expressão cron validada

    Raises:
        ValueError: Se expressão cron for inválida
    """
    if not cron:
        raise ValueError("Expressão cron não pode ser vazia")

    parts = cron.split()

    if len(parts) != 5:
        raise ValueError(
            f"Expressão cron deve ter 5 campos (minuto hora dia mês dia_semana), "
            f"encontrados {len(parts)}: {cron}"
        )

    # Validação básica de caracteres permitidos
    allowed_chars = set("0123456789*,-/")
    for part in parts:
        if not all(c in allowed_chars for c in part):
            raise ValueError(f"Expressão cron contém caracteres inválidos: {cron}")

    return cron


def validate_path(path: str) -> str:
    """
    Valida e normaliza caminho de diretório.

    Args:
        path: Caminho a ser validado

    Returns:
        str: Caminho normalizado

    Raises:
        ValueError: Se caminho for inválido
    """
    if not path:
        raise ValueError("Caminho não pode ser vazio")

    # Normaliza o path
    normalized = os.path.normpath(path)

    # Verifica caracteres inválidos (básico para Unix/Linux)
    if "\0" in normalized:
        raise ValueError(f"Caminho contém caracteres nulos: {path}")

    # Previne paths perigosos
    dangerous_paths = ["/etc", "/sys", "/proc", "/dev", "/boot"]
    if any(normalized.startswith(dp) for dp in dangerous_paths):
        raise ValueError(f"Caminho não permitido por segurança: {path}")

    return normalized


def validate_timeout(timeout: int) -> int:
    """
    Valida valor de timeout.

    Args:
        timeout: Timeout em segundos

    Returns:
        int: Timeout validado

    Raises:
        ValueError: Se timeout for inválido
    """
    if timeout < 1:
        raise ValueError("Timeout deve ser maior que 0")

    if timeout > 86400:
        raise ValueError("Timeout não pode exceder 24 horas (86400 segundos)")

    return timeout


def validate_urls_list(urls: list[str]) -> list[str]:
    """
    Valida lista de URLs.

    Args:
        urls: Lista de URLs

    Returns:
        list[str]: Lista de URLs validadas

    Raises:
        ValueError: Se lista for inválida
    """
    if not urls:
        raise ValueError("Lista de URLs não pode ser vazia")

    if len(urls) > 100:
        raise ValueError("Máximo de 100 URLs permitido")

    # Valida cada URL
    validated = []
    seen: set[str] = set()
    for url in urls:
        if len(url) > 2048:
            raise ValueError(
                f"URL excede o comprimento máximo de 2048 caracteres: {url[:50]}..."
            )
        validated_url = validate_url(url)
        if validated_url in seen:
            raise ValueError(f"URL duplicada na lista: {validated_url}")
        seen.add(validated_url)
        validated.append(validated_url)

    return validated
