"""
Schemas para a entidade Log.

Define schemas de entrada, saída e variações para operações com Logs.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from toninho.models.enums import LogNivel
from toninho.schemas.base import BaseSchema


class LogCreate(BaseSchema):
    """
    Schema para criação de log.

    Attributes:
        execucao_id: ID da execução
        nivel: Nível do log
        mensagem: Mensagem do log
        contexto: Dados adicionais estruturados (opcional)
    """

    execucao_id: uuid.UUID = Field(
        ...,
        description="ID da execução que gerou o log",
    )
    nivel: LogNivel = Field(
        ...,
        description="Nível do log (DEBUG, INFO, WARNING, ERROR)",
    )
    mensagem: str = Field(
        ...,
        min_length=1,
        description="Mensagem do log",
        examples=["Página extraída com sucesso", "Erro ao acessar URL"],
    )
    contexto: Optional[Dict[str, Any]] = Field(
        None,
        description="Dados adicionais estruturados (JSON)",
        examples=[{"url": "https://exemplo.com", "status_code": 200}],
    )


class LogResponse(BaseSchema):
    """
    Schema de resposta para log.

    Attributes:
        id: Identificador único
        execucao_id: ID da execução
        nivel: Nível do log
        mensagem: Mensagem
        timestamp: Data/hora do log
        contexto: Dados adicionais
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    execucao_id: uuid.UUID = Field(..., description="ID da execução")
    nivel: LogNivel = Field(..., description="Nível do log")
    mensagem: str = Field(..., description="Mensagem do log")
    timestamp: datetime = Field(..., description="Data/hora do log")
    contexto: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais")


class LogSummary(BaseSchema):
    """
    Schema resumido de log para listagens.

    Trunca mensagens longas para economizar largura de banda.

    Attributes:
        id: Identificador único
        nivel: Nível do log
        mensagem: Mensagem (truncada se > 200 chars)
        timestamp: Data/hora do log
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    nivel: LogNivel = Field(..., description="Nível do log")
    mensagem: str = Field(..., description="Mensagem do log")
    timestamp: datetime = Field(..., description="Data/hora do log")

    def __init__(self, **data):
        """Trunca mensagem se necessário."""
        super().__init__(**data)
        if len(self.mensagem) > 200:
            self.mensagem = self.mensagem[:197] + "..."


class LogFilter(BaseSchema):
    """
    Schema para filtrar logs em queries.

    Usado em endpoints de listagem para filtrar por critérios.

    Attributes:
        nivel: Filtrar por nível
        desde: Filtrar logs após esta data
        ate: Filtrar logs antes desta data
        busca: Busca textual na mensagem
    """

    nivel: Optional[LogNivel] = Field(
        None,
        description="Filtrar por nível de log",
    )
    desde: Optional[datetime] = Field(
        None,
        description="Filtrar logs após esta data/hora",
    )
    ate: Optional[datetime] = Field(
        None,
        description="Filtrar logs antes desta data/hora",
    )
    busca: Optional[str] = Field(
        None,
        description="Busca textual na mensagem (case-insensitive)",
        examples=["erro", "sucesso"],
    )


# Aliases
LogInCreate = LogCreate
LogOut = LogResponse
