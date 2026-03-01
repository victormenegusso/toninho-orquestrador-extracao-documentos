"""
Exceções customizadas do sistema Toninho.

Este módulo define todas as exceções específicas da aplicação,
facilitando tratamento de erros e debugging.
"""


class ToninhoBaseException(Exception):
    """Exceção base para todas as exceções do Toninho."""

    def __init__(self, message: str = "Erro no sistema Toninho"):
        self.message = message
        super().__init__(self.message)


class ProcessNotFoundError(ToninhoBaseException):
    """Exceção lançada quando um processo não é encontrado."""

    def __init__(self, process_id: int):
        super().__init__(f"Processo com ID {process_id} não encontrado")


class ExecutionNotFoundError(ToninhoBaseException):
    """Exceção lançada quando uma execução não é encontrada."""

    def __init__(self, execution_id: int):
        super().__init__(f"Execução com ID {execution_id} não encontrada")


class ConfigurationNotFoundError(ToninhoBaseException):
    """Exceção lançada quando uma configuração não é encontrada."""

    def __init__(self, config_id: int):
        super().__init__(f"Configuração com ID {config_id} não encontrada")


class ExtractionError(ToninhoBaseException):
    """Exceção lançada quando há erro na extração de dados."""

    def __init__(self, message: str = "Erro ao extrair dados"):
        super().__init__(message)


class ValidationError(ToninhoBaseException):
    """Exceção lançada quando há erro de validação."""

    def __init__(self, message: str = "Erro de validação"):
        super().__init__(f"Erro de validação: {message}")


class StorageError(ToninhoBaseException):
    """Exceção lançada quando há erro no armazenamento."""

    def __init__(self, message: str = "Erro ao armazenar dados"):
        super().__init__(f"Erro ao armazenar: {message}")


class WorkerError(ToninhoBaseException):
    """Exceção lançada quando há erro no worker Celery."""

    def __init__(self, message: str = "Erro no processamento assíncrono"):
        super().__init__(message)


class TimeoutError(ToninhoBaseException):
    """Exceção lançada quando uma operação excede o timeout."""

    def __init__(self, operation: str, timeout: int):
        super().__init__(f"Timeout na operação '{operation}' após {timeout}s")


class MaxRetriesExceededError(ToninhoBaseException):
    """Exceção lançada quando o número máximo de tentativas é excedido."""

    def __init__(self, operation: str, retries: int):
        super().__init__(
            f"Número máximo de tentativas ({retries}) excedido para '{operation}'"
        )


class NotFoundError(ToninhoBaseException):
    """Exceção lançada quando um recurso não é encontrado."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} com identificador '{identifier}' não encontrado")


class ConflictError(ToninhoBaseException):
    """Exceção lançada quando há conflito de dados."""

    def __init__(self, message: str = "Conflito de dados"):
        super().__init__(message)
