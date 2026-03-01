"""
Schemas para a entidade PaginaExtraida.

Define schemas de entrada, saída e variações para operações com Páginas Extraídas.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field, computed_field, field_validator

from toninho.models.enums import PaginaStatus
from toninho.schemas.base import BaseSchema


class PaginaExtraidaCreate(BaseSchema):
    """
    Schema para criação de página extraída.

    Attributes:
        execucao_id: ID da execução
        url_original: URL da página
        caminho_arquivo: Caminho do arquivo salvo
        status: Status da extração
        tamanho_bytes: Tamanho do arquivo em bytes
        erro_mensagem: Mensagem de erro (obrigatória se status=FALHOU)
    """

    execucao_id: uuid.UUID = Field(
        ...,
        description="ID da execução que extraiu a página",
    )
    url_original: str = Field(
        ...,
        description="URL original da página",
        examples=["https://exemplo.com/pagina"],
    )
    caminho_arquivo: str = Field(
        ...,
        description="Caminho do arquivo salvo",
        examples=["/tmp/output/pagina.md"],
    )
    status: PaginaStatus = Field(
        ...,
        description="Status da extração (SUCESSO, FALHOU, IGNORADO)",
    )
    tamanho_bytes: int = Field(
        default=0,
        ge=0,
        description="Tamanho do arquivo em bytes",
    )
    erro_mensagem: Optional[str] = Field(
        None,
        description="Mensagem de erro (obrigatória se status=FALHOU)",
    )

    def model_post_init(self, __context) -> None:
        """Valida que erro_mensagem é obrigatória quando status=FALHOU."""
        if self.status == PaginaStatus.FALHOU and not self.erro_mensagem:
            raise ValueError(
                "erro_mensagem é obrigatória quando status=FALHOU"
            )


class PaginaExtraidaResponse(BaseSchema):
    """
    Schema de resposta para página extraída.

    Attributes:
        id: Identificador único
        execucao_id: ID da execução
        url_original: URL original
        caminho_arquivo: Caminho do arquivo
        status: Status da extração
        tamanho_bytes: Tamanho em bytes
        timestamp: Data/hora da extração
        erro_mensagem: Mensagem de erro
        tamanho_legivel: Tamanho formatado (computed)
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    execucao_id: uuid.UUID = Field(..., description="ID da execução")
    url_original: str = Field(..., description="URL original da página")
    caminho_arquivo: str = Field(..., description="Caminho do arquivo salvo")
    status: PaginaStatus = Field(..., description="Status da extração")
    tamanho_bytes: int = Field(..., description="Tamanho do arquivo em bytes")
    timestamp: datetime = Field(..., description="Data/hora da extração")
    erro_mensagem: Optional[str] = Field(None, description="Mensagem de erro")

    @computed_field
    @property
    def tamanho_legivel(self) -> str:
        """
        Formata tamanho em formato human-readable.

        Returns:
            str: Tamanho formatado (ex: "1.5 MB", "256 KB")
        """
        bytes_val = float(self.tamanho_bytes)

        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0

        return f"{bytes_val:.1f} TB"


class PaginaExtraidaSummary(BaseSchema):
    """
    Schema resumido de página extraída para listagens.

    Attributes:
        id: Identificador único
        url_original: URL original
        status: Status da extração
        tamanho_bytes: Tamanho em bytes
        tamanho_legivel: Tamanho formatado (computed)
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    url_original: str = Field(..., description="URL original")
    status: PaginaStatus = Field(..., description="Status da extração")
    tamanho_bytes: int = Field(..., description="Tamanho em bytes")

    @computed_field
    @property
    def tamanho_legivel(self) -> str:
        """Formata tamanho em formato human-readable."""
        bytes_val = float(self.tamanho_bytes)

        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0

        return f"{bytes_val:.1f} TB"


class PaginaExtraidaDetail(PaginaExtraidaResponse):
    """
    Schema detalhado de página extraída com links de download.

    Extends PaginaExtraidaResponse com campos adicionais.

    Attributes:
        download_url: URL para download do arquivo (computed)
        preview_disponivel: Se preview está disponível (computed)
    """

    @computed_field
    @property
    def download_url(self) -> str:
        """
        Gera URL para download do arquivo.

        Returns:
            str: URL do endpoint de download
        """
        return f"/api/v1/paginas/{self.id}/download"

    @computed_field
    @property
    def preview_disponivel(self) -> bool:
        """
        Verifica se preview está disponível.

        Preview disponível apenas para arquivos < 1MB.

        Returns:
            bool: True se preview disponível
        """
        return self.tamanho_bytes < 1024 * 1024  # 1MB


# Aliases
PaginaExtraidaInCreate = PaginaExtraidaCreate
PaginaExtraidaOut = PaginaExtraidaResponse
