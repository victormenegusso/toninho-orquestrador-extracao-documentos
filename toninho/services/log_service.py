"""Service para lógica de negócio de Log."""

import math
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from datetime import datetime

from sqlalchemy.orm import Session

from toninho.core.exceptions import NotFoundError
from toninho.models.enums import LogNivel
from toninho.models.log import Log
from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.log_repository import LogRepository
from toninho.schemas.log import LogCreate, LogEstatisticas, LogFilter, LogResponse
from toninho.schemas.responses import PaginationMeta, SuccessListResponse


class LogService:
    """Service para operações de negócio com Log."""

    def __init__(
        self,
        repository: LogRepository,
        execucao_repository: ExecucaoRepository,
    ):
        """
        Inicializa o service.

        Args:
            repository: Repository de Log
            execucao_repository: Repository de Execucao
        """
        self.repository = repository
        self.execucao_repository = execucao_repository

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_log(self, db: Session, log_create: LogCreate) -> LogResponse:
        """
        Cria um log.

        Args:
            db: Sessão do banco de dados
            log_create: Dados de criação do log

        Returns:
            LogResponse

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.execucao_repository.get_by_id(db, log_create.execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(log_create.execucao_id))

        log = Log(
            execucao_id=log_create.execucao_id,
            nivel=log_create.nivel,
            mensagem=log_create.mensagem,
            contexto=log_create.contexto,
        )
        log = self.repository.create(db, log)
        return LogResponse.model_validate(log)

    def create_log_batch(
        self, db: Session, logs_create: list[LogCreate]
    ) -> list[LogResponse]:
        """
        Cria múltiplos logs em lote.

        Args:
            db: Sessão do banco de dados
            logs_create: Lista de dados de criação

        Returns:
            Lista de LogResponse

        Raises:
            NotFoundError: Se alguma execução não existe
        """
        # Validar que todas as execuções existem (unique set)
        execucao_ids = {lc.execucao_id for lc in logs_create}
        for execucao_id in execucao_ids:
            execucao = self.execucao_repository.get_by_id(db, execucao_id)
            if not execucao:
                raise NotFoundError("Execucao", str(execucao_id))

        logs = [
            Log(
                execucao_id=lc.execucao_id,
                nivel=lc.nivel,
                mensagem=lc.mensagem,
                contexto=lc.contexto,
            )
            for lc in logs_create
        ]
        logs = self.repository.create_batch(db, logs)
        return [LogResponse.model_validate(log) for log in logs]

    def get_log(self, db: Session, log_id: UUID) -> LogResponse:
        """
        Busca um log por ID.

        Args:
            db: Sessão do banco de dados
            log_id: UUID do log

        Returns:
            LogResponse

        Raises:
            NotFoundError: Se o log não existe
        """
        log = self.repository.get_by_id(db, log_id)
        if not log:
            raise NotFoundError("Log", str(log_id))
        return LogResponse.model_validate(log)

    def list_logs_by_execucao(
        self,
        db: Session,
        execucao_id: UUID,
        page: int = 1,
        per_page: int = 100,
        filtro: LogFilter | None = None,
    ) -> SuccessListResponse[LogResponse]:
        """
        Lista logs de uma execução com paginação e filtros.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução
            page: Número da página (1-indexed)
            per_page: Itens por página
            filtro: Filtros opcionais

        Returns:
            SuccessListResponse paginado

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.execucao_repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        skip = (page - 1) * per_page
        nivel = filtro.nivel if filtro else None
        desde = filtro.desde if filtro else None
        ate = filtro.ate if filtro else None
        busca = filtro.busca if filtro else None

        logs, total = self.repository.get_by_execucao_id(
            db,
            execucao_id,
            skip=skip,
            limit=per_page,
            nivel=nivel,
            desde=desde,
            ate=ate,
            busca=busca,
        )

        total_pages = math.ceil(total / per_page) if per_page else 1

        data = [LogResponse.model_validate(log) for log in logs]

        return SuccessListResponse(
            data=data,
            meta=PaginationMeta(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )

    def get_logs_recentes(
        self, db: Session, execucao_id: UUID, limit: int = 20
    ) -> list[LogResponse]:
        """
        Retorna os últimos N logs de uma execução.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução
            limit: Máximo de logs a retornar

        Returns:
            Lista de LogResponse

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.execucao_repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        logs = self.repository.get_recent(db, execucao_id, limit=limit)
        return [LogResponse.model_validate(log) for log in logs]

    def get_estatisticas_logs(self, db: Session, execucao_id: UUID) -> LogEstatisticas:
        """
        Obtém estatísticas de logs de uma execução.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            LogEstatisticas

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.execucao_repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        por_nivel = self.repository.count_by_nivel(db, execucao_id)
        total = sum(por_nivel.values())

        total_errors = por_nivel.get(LogNivel.ERROR, 0)
        percentual_erros = (total_errors / total * 100) if total > 0 else 0.0

        # Buscar primeiro e último log
        logs_asc, _ = self.repository.get_by_execucao_id(
            db, execucao_id, skip=0, limit=1
        )
        # get_by_execucao_id returns desc, so we get the last. For first, reverse
        from toninho.models.log import Log as LogModel

        # Primeiro log
        primeiro_log_dt: datetime | None = None
        ultimo_log_dt: datetime | None = None

        if total > 0:
            from sqlalchemy import select as sa_select

            stmt_first = (
                sa_select(LogModel)
                .where(LogModel.execucao_id == execucao_id)
                .order_by(LogModel.timestamp.asc())
                .limit(1)
            )
            first_log = db.execute(stmt_first).scalar_one_or_none()
            if first_log:
                primeiro_log_dt = first_log.timestamp

            stmt_last = (
                sa_select(LogModel)
                .where(LogModel.execucao_id == execucao_id)
                .order_by(LogModel.timestamp.desc())
                .limit(1)
            )
            last_log = db.execute(stmt_last).scalar_one_or_none()
            if last_log:
                ultimo_log_dt = last_log.timestamp

        return LogEstatisticas(
            execucao_id=execucao_id,
            total=total,
            por_nivel=por_nivel,
            percentual_erros=round(percentual_erros, 2),
            primeiro_log=primeiro_log_dt,
            ultimo_log=ultimo_log_dt,
        )
