"""
Testes para o módulo de constantes.
"""

from toninho.core import constants


def test_process_status_constants():
    """Testa constantes de status de processo."""
    assert constants.ProcessStatus.PENDING == "pending"
    assert constants.ProcessStatus.RUNNING == "running"
    assert constants.ProcessStatus.COMPLETED == "completed"
    assert constants.ProcessStatus.FAILED == "failed"
    assert constants.ProcessStatus.CANCELLED == "cancelled"


def test_execution_status_constants():
    """Testa constantes de status de execução."""
    assert constants.ExecutionStatus.PENDING == "pending"
    assert constants.ExecutionStatus.RUNNING == "running"
    assert constants.ExecutionStatus.SUCCESS == "success"
    assert constants.ExecutionStatus.FAILED == "failed"
    assert constants.ExecutionStatus.TIMEOUT == "timeout"


def test_log_level_constants():
    """Testa constantes de nível de log."""
    assert constants.LogLevel.DEBUG == "debug"
    assert constants.LogLevel.INFO == "info"
    assert constants.LogLevel.WARNING == "warning"
    assert constants.LogLevel.ERROR == "error"
    assert constants.LogLevel.CRITICAL == "critical"


def test_limits_constants():
    """Testa constantes de limites do sistema."""
    assert constants.MAX_FILE_SIZE == 1073741824  # 1GB
    assert constants.MAX_PAGES_PER_PROCESS == 10000
    assert constants.DEFAULT_PAGE_SIZE == 50
    assert constants.MAX_PAGE_SIZE == 100


def test_timeout_constants():
    """Testa constantes de timeout."""
    assert constants.DEFAULT_REQUEST_TIMEOUT == 30
    assert constants.DEFAULT_EXTRACTION_TIMEOUT == 3600
    assert constants.MAX_EXTRACTION_TIMEOUT == 7200


def test_regex_patterns():
    """Testa padrões regex."""
    import re

    # Testar padrão de processo
    processo_valido = "1234567-89.2024.1.23.4567"
    assert re.match(constants.PROCESSO_PATTERN, processo_valido)

    # Testar padrão de URL
    url_valida = "https://example.com/test"
    assert re.search(constants.URL_PATTERN, url_valida)
