"""Repository para operações de banco de dados da entidade Processo."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from toninho.models.configuracao import Configuracao
from toninho.models.enums import ProcessoStatus
from toninho.models.processo import Processo


class ProcessoRepository:
    """Repository para acesso a dados de Processo."""

    def create(self, db: Session, processo: Processo) -> Processo:
        """
        Insere um novo processo no banco de dados.

        Args:
            db: Sessão do SQLAlchemy
            processo: Instância do modelo Processo

        Returns:
            Processo criado com ID gerado
        """
        db.add(processo)
        db.commit()
        db.refresh(processo)
        return processo

    def get_by_id(self, db: Session, processo_id: UUID) -> Processo | None:
        """
        Busca um processo por ID.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Processo encontrado ou None
        """
        stmt = select(Processo).where(Processo.id == processo_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_nome(self, db: Session, nome: str) -> Processo | None:
        """
        Busca um processo por nome.

        Args:
            db: Sessão do SQLAlchemy
            nome: Nome do processo

        Returns:
            Processo encontrado ou None
        """
        stmt = select(Processo).where(Processo.nome == nome)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: ProcessoStatus | None = None,
        busca: str | None = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> tuple[list[Processo], int]:
        """
        Lista processos com paginação e filtros.

        Args:
            db: Sessão do SQLAlchemy
            skip: Número de registros para pular
            limit: Número máximo de registros
            status: Filtro por status (opcional)
            busca: Filtro por nome (LIKE, opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ("asc" ou "desc")

        Returns:
            Tupla (lista de processos, total de registros)
        """
        # Query base
        stmt = select(Processo)

        # Aplicar filtros
        if status:
            stmt = stmt.where(Processo.status == status)

        if busca:
            stmt = stmt.where(Processo.nome.ilike(f"%{busca}%"))

        # Contar total antes da paginação
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar()

        # Ordenação
        order_column = getattr(Processo, order_by, Processo.created_at)
        if order_dir.lower() == "desc":
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())

        # Paginação
        stmt = stmt.offset(skip).limit(limit)

        # Executar query
        result = db.execute(stmt)
        processos = result.scalars().all()

        return list(processos), total

    def update(self, db: Session, processo: Processo) -> Processo:
        """
        Atualiza um processo existente.

        Args:
            db: Sessão do SQLAlchemy
            processo: Instância do modelo Processo com mudanças

        Returns:
            Processo atualizado
        """
        db.add(processo)
        db.commit()
        db.refresh(processo)
        return processo

    def delete(self, db: Session, processo_id: UUID) -> bool:
        """
        Deleta um processo do banco de dados.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            True se deletado, False se não encontrado
        """
        processo = self.get_by_id(db, processo_id)
        if not processo:
            return False

        db.delete(processo)
        db.commit()
        return True

    def exists_by_nome(
        self, db: Session, nome: str, exclude_id: UUID | None = None
    ) -> bool:
        """
        Verifica se já existe um processo com o nome informado.

        Args:
            db: Sessão do SQLAlchemy
            nome: Nome do processo
            exclude_id: ID do processo a ser ignorado (opcional, para updates)

        Returns:
            True se existe, False caso contrário
        """
        stmt = select(Processo).where(Processo.nome == nome)

        if exclude_id:
            stmt = stmt.where(Processo.id != exclude_id)

        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def count_total(self, db: Session) -> int:
        """
        Conta o total de processos.

        Args:
            db: Sessão do SQLAlchemy

        Returns:
            Total de processos
        """
        stmt = select(func.count(Processo.id))
        result = db.execute(stmt)
        return result.scalar()

    def count_by_status(self, db: Session, status: ProcessoStatus) -> int:
        """
        Conta processos por status.

        Args:
            db: Sessão do SQLAlchemy
            status: Status para filtrar

        Returns:
            Total de processos com o status informado
        """
        stmt = select(func.count(Processo.id)).where(Processo.status == status)
        result = db.execute(stmt)
        return result.scalar()

    def get_by_id_with_details(self, db: Session, processo_id: UUID) -> Processo | None:
        """
        Busca um processo por ID com eager loading de configurações.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Processo encontrado com configurações, ou None
        """
        stmt = (
            select(Processo)
            .where(Processo.id == processo_id)
            .options(
                joinedload(Processo.configuracoes).joinedload(Configuracao.volume),
            )
        )
        result = db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def count_execucoes(self, db: Session, processo_id: UUID) -> int:
        """
        Conta total de execuções de um processo.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Total de execuções
        """
        from toninho.models.execucao import Execucao

        stmt = select(func.count(Execucao.id)).where(
            Execucao.processo_id == processo_id
        )
        return db.execute(stmt).scalar() or 0

    def get_recent_execucoes(
        self, db: Session, processo_id: UUID, limit: int = 5
    ) -> list:
        """
        Retorna as execuções mais recentes de um processo.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo
            limit: Número máximo de execuções

        Returns:
            Lista de execuções ordenadas por created_at desc
        """
        from toninho.models.execucao import Execucao

        stmt = (
            select(Execucao)
            .where(Execucao.processo_id == processo_id)
            .order_by(Execucao.created_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    def has_execucoes_em_andamento(self, db: Session, processo_id: UUID) -> int:
        """
        Conta execuções em andamento de um processo.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Número de execuções EM_EXECUCAO
        """
        from toninho.models.enums import ExecucaoStatus
        from toninho.models.execucao import Execucao

        stmt = select(func.count(Execucao.id)).where(
            Execucao.processo_id == processo_id,
            Execucao.status == ExecucaoStatus.EM_EXECUCAO,
        )
        return db.execute(stmt).scalar() or 0
