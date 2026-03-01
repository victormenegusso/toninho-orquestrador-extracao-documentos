"""
Model PaginaExtraida.

Representa uma página extraída durante uma execução.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from toninho.models.base import Base, UUIDMixin
from toninho.models.enums import PaginaStatus

if TYPE_CHECKING:
    from toninho.models.execucao import Execucao


class PaginaExtraida(Base, UUIDMixin):
    """
    Model que representa uma página extraída durante uma execução.

    Cada registro representa uma tentativa de extração de uma URL,
    contendo informações sobre sucesso, falha ou ignoramento.

    Attributes:
        id: Identificador único (UUID)
        execucao_id: ID da execução que extraiu a página
        url_original: URL original da página
        caminho_arquivo: Caminho do arquivo salvo
        status: Status da extração (SUCESSO, FALHOU, IGNORADO)
        tamanho_bytes: Tamanho do arquivo em bytes
        timestamp: Data/hora da extração
        erro_mensagem: Mensagem de erro (se status=FALHOU)
        execucao: Execução que extraiu a página

    Note:
        PaginaExtraida não tem updated_at pois é imutável após criação.
    """

    __tablename__ = "paginas_extraidas"

    # Foreign Keys
    execucao_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("execucoes.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID da execução que extraiu esta página"
    )

    # Campos
    url_original: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        doc="URL original da página extraída"
    )

    caminho_arquivo: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        doc="Caminho do arquivo salvo no sistema"
    )

    status: Mapped[PaginaStatus] = mapped_column(
        nullable=False,
        doc="Status da extração (SUCESSO, FALHOU, IGNORADO)"
    )

    tamanho_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Tamanho do arquivo em bytes"
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Data/hora da extração"
    )

    erro_mensagem: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Mensagem de erro (obrigatória se status=FALHOU)"
    )

    # Relacionamentos
    execucao: Mapped["Execucao"] = relationship(
        back_populates="paginas",
        doc="Execução que extraiu esta página"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("tamanho_bytes >= 0", name="ck_pagina_tamanho_min"),
        Index("idx_pagina_execucao_id", "execucao_id"),
        Index("idx_pagina_status", "status"),
        Index("idx_pagina_url", "url_original"),
        Index("idx_pagina_execucao_status", "execucao_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<PaginaExtraida(id={self.id}, url={self.url_original[:50]!r}..., "
            f"status={self.status})>"
        )
