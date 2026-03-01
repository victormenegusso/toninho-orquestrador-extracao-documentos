"""
Schemas para a entidade Execucao.

Define schemas de entrada, saída e variações para operações com Execuções.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field, computed_field

from toninho.models.enums import ExecucaoStatus
from toninho.schemas.base import BaseSchema


class ExecucaoCreate(BaseSchema):
    """
    Schema para criação de execução.

    Execuções são criadas automaticamente pelo sistema,
    portanto apenas o processo_id é necessário.

    Attributes:
        processo_id: ID do processo a ser executado
    """

    processo_id: uuid.UUID = Field(
        ...,
        description="ID do processo a ser executado",
    )


class ExecucaoUpdate(BaseSchema):
    """
    Schema para atualização de execução.

    Permite atualização de status e métricas durante execução.

    Attributes:
        status: Novo status
        paginas_processadas: Contador de páginas
        bytes_extraidos: Total de bytes
        taxa_erro: Taxa de erro percentual
    """

    status: Optional[ExecucaoStatus] = Field(
        None,
        description="Novo status da execução",
    )
    paginas_processadas: Optional[int] = Field(
        None,
        ge=0,
        description="Número de páginas processadas",
    )
    bytes_extraidos: Optional[int] = Field(
        None,
        ge=0,
        description="Total de bytes extraídos",
    )
    taxa_erro: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Taxa de erro percentual (0-100)",
    )


class ExecucaoResponse(BaseSchema):
    """
    Schema de resposta para execução.

    Attributes:
        id: Identificador único
        processo_id: ID do processo
        status: Status atual
        iniciado_em: Data/hora de início
        finalizado_em: Data/hora de finalização
        paginas_processadas: Contador de páginas
        bytes_extraidos: Total de bytes
        taxa_erro: Taxa de erro
        tentativa_atual: Número da tentativa
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
        duracao_segundos: Duração em segundos (computed)
        em_andamento: Se está em andamento (computed)
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    processo_id: uuid.UUID = Field(..., description="ID do processo")
    status: ExecucaoStatus = Field(..., description="Status atual")
    iniciado_em: Optional[datetime] = Field(None, description="Data/hora de início")
    finalizado_em: Optional[datetime] = Field(None, description="Data/hora de finalização")
    paginas_processadas: int = Field(..., description="Número de páginas processadas")
    bytes_extraidos: int = Field(..., description="Total de bytes extraídos")
    taxa_erro: float = Field(..., description="Taxa de erro percentual")
    tentativa_atual: int = Field(..., description="Número da tentativa atual")
    created_at: datetime = Field(..., description="Data/hora de criação")
    updated_at: datetime = Field(..., description="Data/hora da última atualização")

    @computed_field
    @property
    def duracao_segundos(self) -> Optional[int]:
        """
        Calcula duração da execução em segundos.

        Returns:
            int | None: Duração em segundos, ou None se não finalizada
        """
        if self.iniciado_em and self.finalizado_em:
            return int((self.finalizado_em - self.iniciado_em).total_seconds())
        return None

    @computed_field
    @property
    def em_andamento(self) -> bool:
        """
        Verifica se execução está em andamento.

        Returns:
            bool: True se status indica execução ativa
        """
        return self.status in (
            ExecucaoStatus.AGUARDANDO,
            ExecucaoStatus.EM_EXECUCAO,
        )


class ExecucaoSummary(BaseSchema):
    """
    Schema resumido de execução para listagens.

    Attributes:
        id: Identificador único
        status: Status atual
        iniciado_em: Data/hora de início
        finalizado_em: Data/hora de finalização
        paginas_processadas: Número de páginas
        duracao_segundos: Duração em segundos (computed)
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    status: ExecucaoStatus = Field(..., description="Status atual")
    iniciado_em: Optional[datetime] = Field(None, description="Data/hora de início")
    finalizado_em: Optional[datetime] = Field(None, description="Data/hora de finalização")
    paginas_processadas: int = Field(..., description="Número de páginas processadas")

    @computed_field
    @property
    def duracao_segundos(self) -> Optional[int]:
        """Calcula duração em segundos."""
        if self.iniciado_em and self.finalizado_em:
            return int((self.finalizado_em - self.iniciado_em).total_seconds())
        return None


class ExecucaoStatusUpdate(BaseSchema):
    """
    Schema para atualização de status em endpoints de ação.

    Usado em endpoints como /execucoes/{id}/cancel, /pause, etc.

    Attributes:
        status: Novo status desejado
    """

    status: ExecucaoStatus = Field(
        ...,
        description="Novo status (ex: CANCELADO, PAUSADO)",
    )


# Aliases
ExecucaoInCreate = ExecucaoCreate
ExecucaoInUpdate = ExecucaoUpdate
ExecucaoOut = ExecucaoResponse
