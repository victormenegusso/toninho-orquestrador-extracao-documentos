"""Repository para operações de banco de dados da entidade Execucao."""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from toninho.models.enums import ExecucaoStatus
from toninho.models.execucao import Execucao


class ExecucaoRepository:
    """Repository para acesso a dados de Execucao."""

    def create(self, db: Session, execucao: Execucao) -> Execucao:
        """
        Insere uma nova execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao: Instância do modelo Execucao

        Returns:
            Execucao criada com ID gerado
        """
        db.add(execucao)
        db.commit()
        db.refresh(execucao)
        return execucao

    def get_by_id(
        self,
        db: Session,
        execucao_id: UUID,
        with_relations: bool = False,
    ) -> Execucao | None:
        """
        Busca uma execução por ID.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            with_relations: Carregar logs e páginas via eager load

        Returns:
            Execucao encontrada ou None
        """
        stmt = select(Execucao).where(Execucao.id == execucao_id)
        if with_relations:
            stmt = stmt.options(
                joinedload(Execucao.logs),
                joinedload(Execucao.paginas),
            )
            return db.execute(stmt).unique().scalar_one_or_none()
        return db.execute(stmt).scalar_one_or_none()

    def get_all_by_processo_id(
        self,
        db: Session,
        processo_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: ExecucaoStatus | None = None,
    ) -> tuple[list[Execucao], int]:
        """
        Lista execuções de um processo com paginação.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo
            skip: Registros a pular
            limit: Máximo de registros
            status: Filtro por status (opcional)

        Returns:
            Tupla (lista de execuções, total)
        """
        stmt = select(Execucao).where(Execucao.processo_id == processo_id)
        if status:
            stmt = stmt.where(Execucao.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(Execucao.created_at.desc()).offset(skip).limit(limit)
        execucoes = list(db.execute(stmt).scalars().all())
        return execucoes, total

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: ExecucaoStatus | None = None,
        ordem: str = "desc",
    ) -> tuple[list[Execucao], int]:
        """
        Lista todas as execuções com paginação e filtros.

        Args:
            db: Sessão do SQLAlchemy
            skip: Registros a pular
            limit: Máximo de registros
            status: Filtro por status (opcional)
            ordem: "asc" ou "desc" por created_at

        Returns:
            Tupla (lista de execuções, total)
        """
        stmt = select(Execucao)
        if status:
            stmt = stmt.where(Execucao.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        if ordem == "asc":
            stmt = stmt.order_by(Execucao.created_at.asc())
        else:
            stmt = stmt.order_by(Execucao.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)
        execucoes = list(db.execute(stmt).scalars().all())
        return execucoes, total

    def update(self, db: Session, execucao: Execucao) -> Execucao:
        """
        Salva alterações em uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao: Execucao com dados atualizados

        Returns:
            Execucao atualizada
        """
        db.add(execucao)
        db.commit()
        db.refresh(execucao)
        return execucao

    def update_status(
        self,
        db: Session,
        execucao_id: UUID,
        novo_status: ExecucaoStatus,
    ) -> Execucao | None:
        """
        Atualiza apenas o status de uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            novo_status: Novo status

        Returns:
            Execucao atualizada ou None se não encontrada
        """
        execucao = self.get_by_id(db, execucao_id)
        if not execucao:
            return None
        execucao.status = novo_status
        db.add(execucao)
        db.commit()
        db.refresh(execucao)
        return execucao

    def increment_metrics(
        self,
        db: Session,
        execucao_id: UUID,
        paginas: int = 0,
        bytes_inc: int = 0,
        errors: int = 0,
    ) -> Execucao | None:
        """
        Incrementa métricas de forma atômica.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            paginas: Incremento de páginas processadas
            bytes_inc: Incremento de bytes extraídos
            errors: Incremento de erros (usado para atualizar taxa_erro)

        Returns:
            Execucao atualizada ou None
        """
        stmt = (
            update(Execucao)
            .where(Execucao.id == execucao_id)
            .values(
                paginas_processadas=Execucao.paginas_processadas + paginas,
                bytes_extraidos=Execucao.bytes_extraidos + bytes_inc,
            )
        )
        db.execute(stmt)
        db.commit()
        return self.get_by_id(db, execucao_id)

    def get_em_execucao(self, db: Session, processo_id: UUID) -> Execucao | None:
        """
        Retorna a execução EM_EXECUCAO de um processo, se houver.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Execucao em execução ou None
        """
        stmt = select(Execucao).where(
            Execucao.processo_id == processo_id,
            Execucao.status == ExecucaoStatus.EM_EXECUCAO,
        )
        return db.execute(stmt).scalar_one_or_none()

    def count_by_status(self, db: Session, status: ExecucaoStatus) -> int:
        """
        Conta execuções por status.

        Args:
            db: Sessão do SQLAlchemy
            status: Status a contar

        Returns:
            Total de execuções com o status informado
        """
        stmt = select(func.count()).where(Execucao.status == status)
        return db.execute(stmt).scalar() or 0

    def delete(self, db: Session, execucao_id: UUID) -> bool:
        """
        Remove uma execução pelo ID.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução

        Returns:
            True se removida, False se não encontrada
        """
        execucao = self.get_by_id(db, execucao_id)
        if not execucao:
            return False
        db.delete(execucao)
        db.commit()
        return True
