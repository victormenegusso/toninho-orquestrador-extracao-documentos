"""
Schemas para a entidade Volume.

Define schemas de entrada, saída e variações para operações com Volumes.
"""

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from toninho.models.enums import VolumeStatus, VolumeTipo
from toninho.schemas.base import BaseSchema
from toninho.schemas.validators import validate_path


class VolumeCreate(BaseSchema):
    """
    Schema para criação de volume.

    Attributes:
        nome: Nome amigável do volume (único)
        path: Caminho do diretório
        descricao: Descrição opcional
    """

    nome: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nome amigável do volume",
        examples=["Saída Principal", "Volume Temporário"],
    )
    path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Caminho do diretório de armazenamento",
        examples=["./output", "/app/output"],
    )
    descricao: str | None = Field(
        None,
        description="Descrição opcional do volume",
    )

    @field_validator("path")
    @classmethod
    def validate_volume_path(cls, v: str) -> str:
        """Valida e normaliza o path do volume."""
        return validate_path(v)


class VolumeUpdate(BaseSchema):
    """
    Schema para atualização de volume.

    Todos os campos são opcionais para permitir atualização parcial.
    """

    nome: str | None = Field(None, min_length=1, max_length=200)
    path: str | None = Field(None, min_length=1, max_length=500)
    status: VolumeStatus | None = Field(None, description="Novo status do volume")
    descricao: str | None = Field(None, description="Nova descrição")

    @field_validator("path")
    @classmethod
    def validate_volume_path(cls, v: str | None) -> str | None:
        """Valida path se fornecido."""
        if v is not None:
            return validate_path(v)
        return v


class VolumeResponse(BaseSchema):
    """
    Schema de resposta completa para volume.

    Attributes:
        id: Identificador único
        nome: Nome amigável
        path: Caminho do diretório
        tipo: Tipo de armazenamento
        status: Status atual
        descricao: Descrição
        total_processos: Quantidade de configurações vinculadas
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    nome: str = Field(..., description="Nome amigável")
    path: str = Field(..., description="Caminho do diretório")
    tipo: VolumeTipo = Field(..., description="Tipo de armazenamento")
    status: VolumeStatus = Field(..., description="Status atual")
    descricao: str | None = Field(None, description="Descrição")
    total_processos: int = Field(0, description="Configurações vinculadas")
    created_at: datetime = Field(..., description="Data/hora de criação")
    updated_at: datetime = Field(..., description="Data/hora da última atualização")


class VolumeSummary(BaseSchema):
    """Schema resumido de volume para uso em combos/selects."""

    id: uuid.UUID = Field(..., description="Identificador único")
    nome: str = Field(..., description="Nome amigável")
    path: str = Field(..., description="Caminho do diretório")
    tipo: VolumeTipo = Field(..., description="Tipo de armazenamento")
    status: VolumeStatus = Field(..., description="Status atual")


class VolumeValidationResult(BaseSchema):
    """Resultado da validação de acesso a um path de volume."""

    path: str = Field(..., description="Caminho validado")
    valido: bool = Field(
        ..., description="Se o path é acessível para leitura e escrita"
    )
    pode_ler: bool = Field(False, description="Se tem permissão de leitura")
    pode_escrever: bool = Field(False, description="Se tem permissão de escrita")
    existe: bool = Field(False, description="Se o diretório já existia")
    criado: bool = Field(
        False, description="Se o diretório foi criado durante validação"
    )
    erro: str | None = Field(None, description="Mensagem de erro, se houver")
