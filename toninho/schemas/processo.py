"""
Schemas para a entidade Processo.

Define schemas de entrada, saída e variações para operações com Processos.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from toninho.models.enums import ProcessoStatus
from toninho.schemas.base import BaseSchema


class ProcessoCreate(BaseSchema):
    """
    Schema para criação de processo.

    Attributes:
        nome: Nome do processo (único, 1-200 caracteres)
        descricao: Descrição opcional do processo
        status: Status inicial (default: ATIVO)
    """

    nome: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nome do processo (único no sistema)",
        examples=["Extração Site Principal"],
    )
    descricao: Optional[str] = Field(
        None,
        description="Descrição opcional do processo",
        examples=["Processo para extrair dados do site principal da empresa"],
    )
    status: ProcessoStatus = Field(
        default=ProcessoStatus.ATIVO,
        description="Status inicial do processo",
    )

    @field_validator("nome")
    @classmethod
    def validate_nome_not_empty(cls, v: str) -> str:
        """Valida que nome não é vazio após strip."""
        if not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()


class ProcessoUpdate(BaseSchema):
    """
    Schema para atualização de processo.

    Todos os campos são opcionais para permitir atualização parcial.

    Attributes:
        nome: Novo nome do processo
        descricao: Nova descrição
        status: Novo status
    """

    nome: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Novo nome do processo",
    )
    descricao: Optional[str] = Field(
        None,
        description="Nova descrição",
    )
    status: Optional[ProcessoStatus] = Field(
        None,
        description="Novo status",
    )

    @field_validator("nome")
    @classmethod
    def validate_nome_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Valida que nome não é vazio se fornecido."""
        if v is not None and not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip() if v else None


class ProcessoResponse(BaseSchema):
    """
    Schema de resposta para processo.

    Representa um processo completo com todos os campos.

    Attributes:
        id: Identificador único
        nome: Nome do processo
        descricao: Descrição do processo
        status: Status atual
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
    """

    id: uuid.UUID = Field(..., description="Identificador único do processo")
    nome: str = Field(..., description="Nome do processo")
    descricao: Optional[str] = Field(None, description="Descrição do processo")
    status: ProcessoStatus = Field(..., description="Status atual")
    created_at: datetime = Field(..., description="Data/hora de criação")
    updated_at: datetime = Field(..., description="Data/hora da última atualização")


class ProcessoSummary(BaseSchema):
    """
    Schema resumido de processo para listagens.

    Versão compacta sem campos detalhados, ideal para listas e previews.

    Attributes:
        id: Identificador único
        nome: Nome do processo
        status: Status atual
        created_at: Data/hora de criação
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    nome: str = Field(..., description="Nome do processo")
    status: ProcessoStatus = Field(..., description="Status atual")
    created_at: datetime = Field(..., description="Data/hora de criação")


class ProcessoDetail(ProcessoResponse):
    """
    Schema detalhado de processo com relacionamentos.

    Inclui configurações e execuções recentes associadas.

    Attributes:
        configuracoes: Lista de configurações do processo
        execucoes_recentes: Últimas 5 execuções do processo
        total_execucoes: Número total de execuções
        ultima_execucao_em: Data/hora da última execução
    """

    configuracoes: List["ConfiguracaoResponse"] = Field(
        default_factory=list, description="Configurações do processo"
    )
    execucoes_recentes: List["ExecucaoResponse"] = Field(
        default_factory=list, description="Últimas execuções"
    )
    total_execucoes: int = Field(default=0, description="Total de execuções")
    ultima_execucao_em: Optional[datetime] = Field(
        None, description="Data/hora da última execução"
    )


class ProcessoMetricas(BaseSchema):
    """
    Schema com métricas agregadas de um processo.

    Attributes:
        processo_id: ID do processo
        total_execucoes: Número total de execuções
        execucoes_sucesso: Número de execuções bem-sucedidas
        execucoes_falha: Número de execuções falhadas
        taxa_sucesso: Taxa de sucesso em porcentagem (0-100)
        tempo_medio_execucao_segundos: Tempo médio de execução em segundos
        total_paginas_extraidas: Total de páginas extraídas
        total_bytes_extraidos: Total de bytes extraídos
        ultima_execucao_em: Data/hora da última execução
    """

    processo_id: uuid.UUID = Field(..., description="ID do processo")
    total_execucoes: int = Field(default=0, description="Total de execuções")
    execucoes_sucesso: int = Field(default=0, description="Execuções bem-sucedidas")
    execucoes_falha: int = Field(default=0, description="Execuções falhadas")
    taxa_sucesso: float = Field(
        default=0.0, description="Taxa de sucesso (%)", ge=0, le=100
    )
    tempo_medio_execucao_segundos: Optional[float] = Field(
        None, description="Tempo médio de execução (segundos)"
    )
    total_paginas_extraidas: int = Field(default=0, description="Total de páginas")
    total_bytes_extraidos: int = Field(default=0, description="Total de bytes")
    ultima_execucao_em: Optional[datetime] = Field(
        None, description="Última execução"
    )


# Aliases para manter compatibilidade e clareza
ProcessoInCreate = ProcessoCreate
ProcessoInUpdate = ProcessoUpdate
ProcessoOut = ProcessoResponse

