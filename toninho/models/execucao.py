"""
Model Execucao.

Representa uma execução de um processo de extração.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from toninho.models.base import Base, TimestampMixin, UUIDMixin
from toninho.models.enums import ExecucaoStatus

if TYPE_CHECKING:
    from toninho.models.log import Log
    from toninho.models.pagina_extraida import PaginaExtraida
    from toninho.models.processo import Processo


class Execucao(Base, UUIDMixin, TimestampMixin):
    """
    Model que representa uma execução de um processo de extração.

    Uma execução é uma instância concreta de processamento,
    contendo métricas, status e relacionamentos com logs e páginas extraídas.

    Attributes:
        id: Identificador único (UUID)
        processo_id: ID do processo sendo executado
        status: Status atual da execução
        iniciado_em: Data/hora de início da execução
        finalizado_em: Data/hora de finalização da execução
        paginas_processadas: Contador de páginas processadas
        bytes_extraidos: Total de bytes extraídos
        taxa_erro: Taxa de erro percentual (0-100)
        tentativa_atual: Número da tentativa atual (1-based)
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
        processo: Processo sendo executado
        logs: Lista de logs da execução
        paginas: Lista de páginas extraídas
    """

    __tablename__ = "execucoes"

    # Foreign Keys
    processo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID do processo sendo executado"
    )

    # Campos
    status: Mapped[ExecucaoStatus] = mapped_column(
        nullable=False,
        default=ExecucaoStatus.CRIADO,
        doc="Status atual da execução"
    )

    iniciado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Data/hora de início da execução"
    )

    finalizado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Data/hora de finalização da execução"
    )

    paginas_processadas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Número de páginas processadas"
    )

    bytes_extraidos: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        doc="Total de bytes extraídos"
    )

    taxa_erro: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        doc="Taxa de erro percentual (0-100)"
    )

    tentativa_atual: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Número da tentativa atual"
    )

    # Relacionamentos
    processo: Mapped["Processo"] = relationship(
        back_populates="execucoes",
        doc="Processo sendo executado"
    )

    logs: Mapped[List["Log"]] = relationship(
        back_populates="execucao",
        cascade="all, delete-orphan",
        order_by="Log.timestamp",
        doc="Logs gerados durante a execução"
    )

    paginas: Mapped[List["PaginaExtraida"]] = relationship(
        back_populates="execucao",
        cascade="all, delete-orphan",
        doc="Páginas extraídas durante a execução"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("paginas_processadas >= 0", name="ck_execucao_paginas_min"),
        CheckConstraint("bytes_extraidos >= 0", name="ck_execucao_bytes_min"),
        CheckConstraint("taxa_erro >= 0.0", name="ck_execucao_taxa_erro_min"),
        CheckConstraint("taxa_erro <= 100.0", name="ck_execucao_taxa_erro_max"),
        CheckConstraint("tentativa_atual > 0", name="ck_execucao_tentativa_positive"),
        Index("idx_execucao_processo_id", "processo_id"),
        Index("idx_execucao_status", "status"),
        Index("idx_execucao_created_at", "created_at"),
        Index("idx_execucao_processo_created", "processo_id", "created_at"),
    )

    @property
    def duracao(self) -> float | None:
        """
        Retorna a duração da execução em segundos.

        Returns:
            float | None: Duração em segundos, ou None se não finalizada
        """
        if self.iniciado_em and self.finalizado_em:
            return (self.finalizado_em - self.iniciado_em).total_seconds()
        return None

    @property
    def em_andamento(self) -> bool:
        """
        Verifica se a execução está em andamento.

        Returns:
            bool: True se status indica execução em andamento
        """
        return self.status in (
            ExecucaoStatus.AGUARDANDO,
            ExecucaoStatus.EM_EXECUCAO,
        )

    @property
    def finalizado(self) -> bool:
        """
        Verifica se a execução foi finalizada (com sucesso ou erro).

        Returns:
            bool: True se status indica finalização
        """
        return self.status in (
            ExecucaoStatus.CONCLUIDO,
            ExecucaoStatus.FALHOU,
            ExecucaoStatus.CANCELADO,
            ExecucaoStatus.CONCLUIDO_COM_ERROS,
        )

    def __repr__(self) -> str:
        return (
            f"<Execucao(id={self.id}, processo_id={self.processo_id}, "
            f"status={self.status})>"
        )
