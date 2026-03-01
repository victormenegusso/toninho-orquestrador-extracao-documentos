"""
Model Processo.

Representa um processo de extração configurável no sistema Toninho.
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from toninho.models.base import Base, TimestampMixin, UUIDMixin
from toninho.models.enums import ProcessoStatus

if TYPE_CHECKING:
    from toninho.models.configuracao import Configuracao
    from toninho.models.execucao import Execucao


class Processo(Base, UUIDMixin, TimestampMixin):
    """
    Model que representa um processo de extração.

    Um processo é uma entidade de alto nível que agrupa configurações
    e execuções de extração de dados de websites.

    Attributes:
        id: Identificador único (UUID)
        nome: Nome do processo (único no sistema)
        descricao: Descrição opcional do processo
        status: Status atual (ATIVO, INATIVO, ARQUIVADO)
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
        configuracoes: Lista de configurações associadas
        execucoes: Lista de execuções do processo
    """

    __tablename__ = "processos"

    # Campos
    nome: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Nome do processo (único)"
    )

    descricao: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Descrição opcional do processo"
    )

    status: Mapped[ProcessoStatus] = mapped_column(
        nullable=False,
        default=ProcessoStatus.ATIVO,
        doc="Status atual do processo"
    )

    # Relacionamentos
    configuracoes: Mapped[List["Configuracao"]] = relationship(
        back_populates="processo",
        cascade="all, delete-orphan",
        doc="Configurações associadas ao processo"
    )

    execucoes: Mapped[List["Execucao"]] = relationship(
        back_populates="processo",
        cascade="all, delete-orphan",
        doc="Execuções do processo"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("nome", name="uq_processo_nome"),
        Index("idx_processo_nome", "nome"),
        Index("idx_processo_status", "status"),
        Index("idx_processo_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Processo(id={self.id}, nome={self.nome!r}, status={self.status})>"
