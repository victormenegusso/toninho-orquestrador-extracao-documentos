"""
Configuração de logging usando Loguru.

Este módulo configura o sistema de logs da aplicação com formatação
personalizada e níveis de log apropriados.
"""

import sys
from pathlib import Path

from loguru import logger

from toninho.core.config import settings


def setup_logging():
    """
    Configura o sistema de logging da aplicação.

    Remove handlers padrão e adiciona handlers personalizados com
    formatação colorida para console e arquivo rotativo para produção.
    """
    # Remove handler padrão
    logger.remove()

    # Formato personalizado
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Handler para console (stdout)
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # Handler para arquivo (apenas em produção)
    if not settings.DEBUG:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)

        logger.add(
            "logs/toninho_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="INFO",
            rotation="00:00",  # Rotação diária à meia-noite
            retention="30 days",  # Manter logs por 30 dias
            compression="zip",  # Comprimir logs antigos
        )

    logger.info("Sistema de logging configurado")
    return logger
