"""
Model Log.

Representa um log gerado durante uma execução.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from toninho.models.base import Base, UUIDMixin
from toninho.models.enums import LogNivel

if TYPE_CHECKING:
    from toninho.models.execucao import Execucao


class Log(Base, UUIDMixin):
    """
    Model que representa um log de execução.

    Logs são append-only e nunca devem ser atualizados após criação.
    Registram eventos, erros, warnings e informações durante a execução.

    Attributes:
        id: Identificador único (UUID)
        execucao_id: ID da execução que gerou o log
        nivel: Nível do log (DEBUG, INFO, WARNING, ERROR)
        mensagem: Mensagem do log
        timestamp: Data/hora do log
        contexto: Dados adicionais estruturados (JSON)
        execucao: Execução que gerou o log

    Note:
        Logs não têm updated_at pois são imutáveis após criação.
    """

    __tablename__ = "logs"

    # Foreign Keys
    execucao_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("execucoes.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID da execução que gerou este log",
    )

    # Campos
    nivel: Mapped[LogNivel] = mapped_column(
        nullable=False, doc="Nível do log (DEBUG, INFO, WARNING, ERROR)"
    )

    mensagem: Mapped[str] = mapped_column(String, nullable=False, doc="Mensagem do log")

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Data/hora em que o log foi gerado",
    )

    contexto: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        doc="Dados adicionais estruturados (variável por tipo de log)",
    )

    # Relacionamentos
    execucao: Mapped["Execucao"] = relationship(
        back_populates="logs", doc="Execução que gerou este log"
    )

    # Constraints
    __table_args__ = (
        Index("idx_log_execucao_id", "execucao_id"),
        Index("idx_log_timestamp", "timestamp"),
        Index("idx_log_nivel", "nivel"),
        Index("idx_log_execucao_timestamp", "execucao_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<Log(id={self.id}, nivel={self.nivel}, "
            f"mensagem={self.mensagem[:50]!r}...)>"
        )
