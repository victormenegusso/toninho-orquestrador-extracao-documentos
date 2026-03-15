"""
Enumerações compartilhadas entre os models do Toninho.

Todos os enums herdam de str e enum.Enum para serialização
automática em JSON e compatibilidade com SQLAlchemy.
"""

from enum import Enum


class ProcessoStatus(str, Enum):
    """Status de um processo no sistema."""

    ATIVO = "ativo"  # Processo ativo e operacional
    INATIVO = "inativo"  # Processo desativado temporariamente
    ARQUIVADO = "arquivado"  # Processo arquivado (não aparece em listagens)


class FormatoSaida(str, Enum):
    """Formato de saída dos arquivos extraídos."""

    ARQUIVO_UNICO = "arquivo_unico"  # Todas as páginas em um único markdown
    MULTIPLOS_ARQUIVOS = "multiplos_arquivos"  # Uma página por arquivo


class AgendamentoTipo(str, Enum):
    """Tipo de agendamento de execução."""

    RECORRENTE = "recorrente"  # Execução recorrente via cron
    ONE_TIME = "one_time"  # Execução única agendada
    MANUAL = "manual"  # Sem agendamento, execução manual


class ExecucaoStatus(str, Enum):
    """Status de uma execução."""

    CRIADO = "criado"  # Execução criada, aguardando
    AGUARDANDO = "aguardando"  # Na fila, aguardando worker
    EM_EXECUCAO = "em_execucao"  # Sendo processada por worker
    PAUSADO = "pausado"  # Pausada manualmente
    CONCLUIDO = "concluido"  # Finalizada com sucesso
    FALHOU = "falhou"  # Finalizada com erro total
    CANCELADO = "cancelado"  # Cancelada pelo usuário
    CONCLUIDO_COM_ERROS = "concluido_com_erros"  # Sucesso parcial


class LogNivel(str, Enum):
    """Nível de log."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class PaginaStatus(str, Enum):
    """Status de extração de uma página."""

    SUCESSO = "sucesso"  # Página extraída com sucesso
    FALHOU = "falhou"  # Falha na extração
    IGNORADO = "ignorado"  # Página ignorada (filtros, duplicada, etc)


class MetodoExtracao(str, Enum):
    """Motor de extração de HTML para Markdown."""

    HTML2TEXT = (
        "html2text"  # Método atual: BeautifulSoup + html2text (rápido, suporta SPA)
    )
    DOCLING = "docling"  # IBM Docling: saída semântica estruturada (não suporta SPA)
