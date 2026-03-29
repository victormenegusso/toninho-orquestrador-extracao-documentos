"""
Model Configuracao.

Representa as configurações de extração de um processo.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from toninho.models.base import Base, TimestampMixin, UUIDMixin
from toninho.models.enums import AgendamentoTipo, FormatoSaida, MetodoExtracao

if TYPE_CHECKING:
    from toninho.models.processo import Processo
    from toninho.models.volume import Volume


class Configuracao(Base, UUIDMixin, TimestampMixin):
    """
    Model que representa as configurações de extração de um processo.

    Uma configuração define como um processo deve extrair dados,
    incluindo URLs, timeouts, formato de saída e agendamento.

    Attributes:
        id: Identificador único (UUID)
        processo_id: ID do processo pai
        volume_id: ID do volume de saída
        urls: Lista de URLs para extração (JSON)
        timeout: Timeout em segundos (1-86400)
        max_retries: Número máximo de retentativas (0-10)
        formato_saida: Formato de saída (ARQUIVO_UNICO ou MULTIPLOS_ARQUIVOS)
        agendamento_cron: Expressão cron para agendamento recorrente
        agendamento_tipo: Tipo de agendamento (MANUAL, ONE_TIME, RECORRENTE)
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
        processo: Processo pai
        volume: Volume de saída
    """

    __tablename__ = "configuracoes"

    # Foreign Keys
    processo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processos.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID do processo ao qual esta configuração pertence",
    )

    volume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("volumes.id"),
        nullable=False,
        doc="ID do volume de saída dos arquivos extraídos",
    )

    # Campos
    urls: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, doc="Lista de URLs para extração"
    )

    timeout: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3600,
        doc="Timeout em segundos para a extração completa",
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        doc="Número máximo de retentativas em caso de falha",
    )

    formato_saida: Mapped[FormatoSaida] = mapped_column(
        nullable=False,
        default=FormatoSaida.MULTIPLOS_ARQUIVOS,
        doc="Formato de saída dos arquivos extraídos",
    )

    agendamento_cron: Mapped[str | None] = mapped_column(
        String(100), nullable=True, doc="Expressão cron para agendamento recorrente"
    )

    agendamento_tipo: Mapped[AgendamentoTipo] = mapped_column(
        nullable=False,
        default=AgendamentoTipo.MANUAL,
        doc="Tipo de agendamento da execução",
    )

    use_browser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Se True, usa Playwright (navegador headless) para renderizar páginas JS",
    )

    metodo_extracao: Mapped[MetodoExtracao] = mapped_column(
        nullable=False,
        default=MetodoExtracao.HTML2TEXT,
        doc=(
            "Motor de extração de HTML para Markdown. "
            "HTML2TEXT usa BeautifulSoup + html2text (atual). "
            "DOCLING usa IBM Docling para saída semântica estruturada."
        ),
    )

    respect_robots_txt: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Se True, verifica robots.txt antes de extrair cada URL",
    )

    # Relacionamentos
    processo: Mapped["Processo"] = relationship(
        back_populates="configuracoes",
        doc="Processo ao qual esta configuração pertence",
    )

    volume: Mapped["Volume"] = relationship(
        back_populates="configuracoes",
        doc="Volume de saída dos arquivos extraídos",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("timeout > 0", name="ck_configuracao_timeout_positive"),
        CheckConstraint("timeout <= 86400", name="ck_configuracao_timeout_max"),
        CheckConstraint("max_retries >= 0", name="ck_configuracao_retries_min"),
        CheckConstraint("max_retries <= 10", name="ck_configuracao_retries_max"),
        Index("idx_configuracao_processo_id", "processo_id"),
        Index("idx_configuracao_agendamento_tipo", "agendamento_tipo"),
        Index("idx_configuracao_volume_id", "volume_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Configuracao(id={self.id}, processo_id={self.processo_id}, "
            f"volume_id={self.volume_id}, agendamento_tipo={self.agendamento_tipo})>"
        )
