"""
Constantes do sistema Toninho.

Este módulo centraliza todas as constantes utilizadas na aplicação.
"""


# Status de processo
class ProcessStatus:
    """Status possíveis de um processo de extração."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Status de execução
class ExecutionStatus:
    """Status possíveis de uma execução."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


# Tipos de log
class LogLevel:
    """Níveis de log."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Limites do sistema
MAX_FILE_SIZE = 1073741824  # 1GB em bytes
MAX_PAGES_PER_PROCESS = 10000
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Timeouts (em segundos)
DEFAULT_REQUEST_TIMEOUT = 30
DEFAULT_EXTRACTION_TIMEOUT = 3600
MAX_EXTRACTION_TIMEOUT = 7200

# Regex patterns comuns
PROCESSO_PATTERN = r"\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}"
URL_PATTERN = r"https?://[^\s]+"
