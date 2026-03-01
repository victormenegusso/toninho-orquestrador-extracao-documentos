"""
Classes base e mixins para os models do Toninho.

Fornece funcionalidades compartilhadas como timestamps automáticos
e geração de UUIDs para primary keys.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Classe base para todos os models do Toninho.

    Configura metadata e convenções de nomenclatura para constraints.
    """

    # Convenção de nomenclatura para constraints
    # Facilita debug e migrations
    __abstract__ = True


class UUIDMixin:
    """
    Mixin que adiciona um campo id UUID como primary key.

    UUIDs são gerados automaticamente usando uuid4 (random).
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        doc="Identificador único do registro"
    )


class TimestampMixin:
    """
    Mixin que adiciona campos de timestamp automáticos.

    - created_at: timestamp de criação (never updated)
    - updated_at: timestamp de última atualização (auto-updated)

    Todos os timestamps são em UTC.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Data/hora de criação do registro"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Data/hora da última atualização do registro"
    )


# Event listener para garantir que updated_at seja atualizado
@event.listens_for(TimestampMixin, "before_update", propagate=True)
def receive_before_update(mapper: Any, connection: Any, target: TimestampMixin) -> None:
    """
    Event listener que garante updated_at seja sempre atualizado.

    Este listener é executado antes de qualquer UPDATE no banco,
    garantindo que updated_at reflita a última modificação.
    """
    target.updated_at = datetime.utcnow()
