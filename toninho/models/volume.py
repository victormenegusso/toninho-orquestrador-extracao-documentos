"""
Model Volume.

Representa um volume de armazenamento onde os arquivos extraídos são salvos.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from toninho.models.base import Base, TimestampMixin, UUIDMixin
from toninho.models.enums import VolumeStatus, VolumeTipo

if TYPE_CHECKING:
    from toninho.models.configuracao import Configuracao


class Volume(Base, UUIDMixin, TimestampMixin):
    """
    Model que representa um volume de armazenamento.

    Um volume é um diretório validado onde os arquivos extraídos
    são salvos. Substitui o campo de texto livre output_dir.

    Attributes:
        id: Identificador único (UUID)
        nome: Nome amigável do volume (único)
        path: Caminho do diretório (único)
        tipo: Tipo de armazenamento (LOCAL, futuro: cloud, bd)
        status: Status atual (ATIVO, INATIVO)
        descricao: Descrição opcional
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
        configuracoes: Configurações que usam este volume
    """

    __tablename__ = "volumes"

    nome: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Nome amigável do volume (único)"
    )

    path: Mapped[str] = mapped_column(
        String(500), nullable=False, doc="Caminho do diretório de armazenamento"
    )

    tipo: Mapped[VolumeTipo] = mapped_column(
        nullable=False,
        default=VolumeTipo.LOCAL,
        doc="Tipo de backend de armazenamento",
    )

    status: Mapped[VolumeStatus] = mapped_column(
        nullable=False,
        default=VolumeStatus.ATIVO,
        doc="Status do volume (ativo/inativo)",
    )

    descricao: Mapped[str | None] = mapped_column(
        String, nullable=True, doc="Descrição opcional do volume"
    )

    # Relacionamentos
    configuracoes: Mapped[list["Configuracao"]] = relationship(
        back_populates="volume",
        doc="Configurações que usam este volume",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("nome", name="uq_volume_nome"),
        UniqueConstraint("path", name="uq_volume_path"),
        Index("idx_volume_nome", "nome"),
        Index("idx_volume_status", "status"),
        Index("idx_volume_tipo", "tipo"),
    )

    def __repr__(self) -> str:
        return f"<Volume(id={self.id}, nome={self.nome!r}, path={self.path!r}, status={self.status})>"
