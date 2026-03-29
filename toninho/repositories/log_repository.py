"""Repository para operações de banco de dados da entidade Log."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from toninho.models.enums import LogNivel
from toninho.models.log import Log


class LogRepository:
    """Repository para acesso a dados de Log."""

    def create(self, db: Session, log: Log) -> Log:
        """
        Insere um novo log.

        Args:
            db: Sessão do SQLAlchemy
            log: Instância do modelo Log

        Returns:
            Log criado com ID gerado
        """
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def create_batch(self, db: Session, logs: list[Log]) -> list[Log]:
        """
        Inserção em lote de logs.

        Args:
            db: Sessão do SQLAlchemy
            logs: Lista de instâncias do modelo Log

        Returns:
            Lista de Logs criados
        """
        db.add_all(logs)
        db.commit()
        for log in logs:
            db.refresh(log)
        return logs

    def get_by_id(self, db: Session, log_id: UUID) -> Log | None:
        """
        Busca um log por ID.

        Args:
            db: Sessão do SQLAlchemy
            log_id: UUID do log

        Returns:
            Log encontrado ou None
        """
        stmt = select(Log).where(Log.id == log_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_execucao_id(
        self,
        db: Session,
        execucao_id: UUID,
        skip: int = 0,
        limit: int = 100,
        nivel: LogNivel | None = None,
        desde: datetime | None = None,
        ate: datetime | None = None,
        busca: str | None = None,
    ) -> tuple[list[Log], int]:
        """
        Lista logs de uma execução com filtros e paginação.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            skip: Registros a pular
            limit: Máximo de registros
            nivel: Filtro por nível (opcional)
            desde: Filtro por data mínima (opcional)
            ate: Filtro por data máxima (opcional)
            busca: Busca textual na mensagem (opcional)

        Returns:
            Tupla (lista de logs, total)
        """
        stmt = select(Log).where(Log.execucao_id == execucao_id)

        if nivel is not None:
            stmt = stmt.where(Log.nivel == nivel)
        if desde is not None:
            stmt = stmt.where(Log.timestamp >= desde)
        if ate is not None:
            stmt = stmt.where(Log.timestamp <= ate)
        if busca is not None:
            stmt = stmt.where(Log.mensagem.ilike(f"%{busca}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(Log.timestamp.desc()).offset(skip).limit(limit)
        logs = list(db.execute(stmt).scalars().all())
        return logs, total

    def get_recent(self, db: Session, execucao_id: UUID, limit: int = 20) -> list[Log]:
        """
        Retorna os últimos N logs de uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            limit: Máximo de registros a retornar

        Returns:
            Lista de logs ordenados por timestamp desc
        """
        stmt = (
            select(Log)
            .where(Log.execucao_id == execucao_id)
            .order_by(Log.timestamp.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    def count_by_nivel(self, db: Session, execucao_id: UUID) -> dict[LogNivel, int]:
        """
        Conta logs por nível de uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução

        Returns:
            Dicionário {nivel: contagem}
        """
        stmt = (
            select(Log.nivel, func.count(Log.id).label("total"))
            .where(Log.execucao_id == execucao_id)
            .group_by(Log.nivel)
        )
        rows = db.execute(stmt).all()
        result: dict[LogNivel, int] = {nivel: 0 for nivel in LogNivel}
        for nivel, total in rows:
            result[nivel] = total
        return result

    def delete_by_execucao_id(self, db: Session, execucao_id: UUID) -> int:
        """
        Deleta todos os logs de uma execução via bulk DELETE.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução

        Returns:
            Quantidade de registros deletados
        """
        from sqlalchemy import delete

        stmt = delete(Log).where(Log.execucao_id == execucao_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
