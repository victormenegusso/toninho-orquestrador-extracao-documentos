"""
Schemas para a entidade Execucao.

Define schemas de entrada, saída e variações para operações com Execuções.
"""
import uuid
from datetime import datetime
from typing import List, Optional

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


class ProgressoResponse(BaseSchema):
    """
    Resposta de progresso em tempo real de uma execução.

    Attributes:
        execucao_id: UUID da execução
        status: Status atual
        paginas_processadas: Páginas processadas até agora
        total_paginas: Total de páginas (do número de URLs)
        progresso_percentual: Percentual concluído (0-100)
        tempo_decorrido_segundos: Segundos desde início
        tempo_estimado_restante_segundos: Estimativa de tempo restante
        ultima_atualizacao: Última atualização dos dados
    """

    execucao_id: uuid.UUID = Field(..., description="UUID da execução")
    status: ExecucaoStatus = Field(..., description="Status atual")
    paginas_processadas: int = Field(..., description="Páginas processadas")
    total_paginas: int = Field(..., description="Total de páginas da configuração")
    progresso_percentual: float = Field(..., description="Percentual concluído (0-100)")
    tempo_decorrido_segundos: Optional[int] = Field(
        None, description="Segundos desde o início"
    )
    tempo_estimado_restante_segundos: Optional[int] = Field(
        None, description="Estimativa de segundos restantes"
    )
    ultima_atualizacao: datetime = Field(..., description="Última atualização")


class ExecucaoMetricas(BaseSchema):
    """
    Métricas detalhadas de uma execução.

    Attributes:
        execucao_id: UUID da execução
        paginas_processadas: Total de páginas processadas
        bytes_extraidos: Total de bytes extraídos
        taxa_erro: Taxa de erro percentual
        duracao_segundos: Duração total em segundos
        tempo_medio_por_pagina_segundos: Tempo médio por página
        taxa_sucesso: Percentual de páginas com sucesso
    """

    execucao_id: uuid.UUID = Field(..., description="UUID da execução")
    paginas_processadas: int = Field(..., description="Total de páginas processadas")
    bytes_extraidos: int = Field(..., description="Total de bytes extraídos")
    taxa_erro: float = Field(..., description="Taxa de erro percentual (0-100)")
    duracao_segundos: Optional[int] = Field(None, description="Duração total em segundos")
    tempo_medio_por_pagina_segundos: Optional[float] = Field(
        None, description="Tempo médio por página em segundos"
    )
    taxa_sucesso: float = Field(..., description="Percentual de páginas com sucesso (0-100)")


class ExecucaoDetail(BaseSchema):
    """
    Detalhes completos de uma execução incluindo processo e métricas.

    Attributes:
        id: UUID da execução
        processo_id: UUID do processo
        status: Status atual
        iniciado_em: Data/hora de início
        finalizado_em: Data/hora de finalização
        paginas_processadas: Páginas processadas
        bytes_extraidos: Bytes extraídos
        taxa_erro: Taxa de erro
        tentativa_atual: Número da tentativa
        created_at: Data de criação
        updated_at: Última atualização
        metricas: Métricas calculadas
    """

    id: uuid.UUID
    processo_id: uuid.UUID
    status: ExecucaoStatus
    iniciado_em: Optional[datetime]
    finalizado_em: Optional[datetime]
    paginas_processadas: int
    bytes_extraidos: int
    taxa_erro: float
    tentativa_atual: int
    created_at: datetime
    updated_at: datetime
    metricas: Optional[ExecucaoMetricas] = None

    @computed_field
    @property
    def duracao_segundos(self) -> Optional[int]:
        """Duração em segundos."""
        if self.iniciado_em and self.finalizado_em:
            return int((self.finalizado_em - self.iniciado_em).total_seconds())
        return None
