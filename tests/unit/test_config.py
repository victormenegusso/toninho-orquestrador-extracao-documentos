"""
Testes para o módulo de configuração.
"""

import pytest
from toninho.core.config import Settings, get_settings


def test_settings_default_values():
    """Testa se as configurações têm valores padrão corretos."""
    settings = Settings()

    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "INFO"


def test_settings_singleton():
    """Testa se get_settings retorna sempre a mesma instância."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_settings_can_be_overridden(monkeypatch):
    """Testa se configurações podem ser sobrescritas por variáveis de ambiente."""
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEBUG", "false")

    # Limpar cache do lru_cache
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.PORT == 9000
    assert settings.DEBUG is False

    # Limpar cache novamente
    get_settings.cache_clear()
