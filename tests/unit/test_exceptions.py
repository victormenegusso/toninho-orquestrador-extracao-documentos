"""
Testes para as exceções customizadas.
"""

from toninho.core.exceptions import (
    ConfigurationNotFoundError,
    ExecutionNotFoundError,
    ExtractionError,
    MaxRetriesExceededError,
    ProcessNotFoundError,
    StorageError,
    TimeoutError,
    ToninhoBaseException,
    ValidationError,
    WorkerError,
)


def test_base_exception():
    """Testa exceção base."""
    exc = ToninhoBaseException("Erro teste")
    assert str(exc) == "Erro teste"
    assert isinstance(exc, Exception)


def test_process_not_found_error():
    """Testa exceção de processo não encontrado."""
    exc = ProcessNotFoundError(123)
    assert "123" in str(exc)
    assert "não encontrado" in str(exc)


def test_execution_not_found_error():
    """Testa exceção de execução não encontrada."""
    exc = ExecutionNotFoundError(456)
    assert "456" in str(exc)


def test_configuration_not_found_error():
    """Testa exceção de configuração não encontrada."""
    exc = ConfigurationNotFoundError(789)
    assert "789" in str(exc)


def test_extraction_error():
    """Testa exceção de erro de extração."""
    exc = ExtractionError("Falha ao extrair")
    assert "extrair" in str(exc).lower()


def test_validation_error():
    """Testa exceção de validação."""
    exc = ValidationError("Campo inválido")
    assert "validação" in str(exc).lower()


def test_storage_error():
    """Testa exceção de armazenamento."""
    exc = StorageError("Falha ao salvar")
    assert "armazenar" in str(exc).lower()


def test_worker_error():
    """Testa exceção de worker."""
    exc = WorkerError("Falha no processamento")
    assert "processamento" in str(exc).lower()


def test_timeout_error():
    """Testa exceção de timeout."""
    exc = TimeoutError("operacao_teste", 30)
    assert "operacao_teste" in str(exc)
    assert "30" in str(exc)


def test_max_retries_exceeded_error():
    """Testa exceção de máximo de tentativas excedido."""
    exc = MaxRetriesExceededError("download", 3)
    assert "download" in str(exc)
    assert "3" in str(exc)


def test_all_exceptions_inherit_from_base():
    """Testa que todas as exceções herdam da base."""
    exceptions = [
        ProcessNotFoundError(1),
        ExecutionNotFoundError(1),
        ConfigurationNotFoundError(1),
        ExtractionError(),
        ValidationError(),
        StorageError(),
        WorkerError(),
        TimeoutError("test", 1),
        MaxRetriesExceededError("test", 1),
    ]

    for exc in exceptions:
        assert isinstance(exc, ToninhoBaseException)
        assert isinstance(exc, Exception)
