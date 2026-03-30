"""Repository para operações de banco de dados da entidade PaginaExtraida."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from toninho.models.enums import PaginaStatus
from toninho.models.pagina_extraida import PaginaExtraida


class PaginaExtraidaRepository:
    """Repository para acesso a dados de PaginaExtraida."""

    def create(self, db: Session, pagina: PaginaExtraida) -> PaginaExtraida:
        """
        Insere uma nova página extraída.

        Args:
            db: Sessão do SQLAlchemy
            pagina: Instância do modelo PaginaExtraida

        Returns:
            PaginaExtraida criada com ID gerado
        """
        db.add(pagina)
        db.commit()
        db.refresh(pagina)
        return pagina

    def create_batch(
        self, db: Session, paginas: list[PaginaExtraida]
    ) -> list[PaginaExtraida]:
        """
        Inserção em lote de páginas extraídas.

        Args:
            db: Sessão do SQLAlchemy
            paginas: Lista de instâncias do modelo PaginaExtraida

        Returns:
            Lista de PaginasExtraidas criadas
        """
        db.add_all(paginas)
        db.commit()
        for pagina in paginas:
            db.refresh(pagina)
        return paginas

    def get_by_id(self, db: Session, pagina_id: UUID) -> PaginaExtraida | None:
        """
        Busca uma página extraída por ID.

        Args:
            db: Sessão do SQLAlchemy
            pagina_id: UUID da página

        Returns:
            PaginaExtraida encontrada ou None
        """
        stmt = select(PaginaExtraida).where(PaginaExtraida.id == pagina_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_execucao_id(
        self,
        db: Session,
        execucao_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: PaginaStatus | None = None,
    ) -> tuple[list[PaginaExtraida], int]:
        """
        Lista páginas extraídas de uma execução com paginação e filtro.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            skip: Registros a pular
            limit: Máximo de registros
            status: Filtro por status (opcional)

        Returns:
            Tupla (lista de páginas, total)
        """
        stmt = select(PaginaExtraida).where(PaginaExtraida.execucao_id == execucao_id)
        if status is not None:
            stmt = stmt.where(PaginaExtraida.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(PaginaExtraida.timestamp.desc()).offset(skip).limit(limit)
        paginas = list(db.execute(stmt).scalars().all())
        return paginas, total

    def get_by_url(
        self, db: Session, execucao_id: UUID, url: str
    ) -> PaginaExtraida | None:
        """
        Busca uma página pelo URL dentro de uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução
            url: URL original da página

        Returns:
            PaginaExtraida encontrada ou None
        """
        stmt = select(PaginaExtraida).where(
            PaginaExtraida.execucao_id == execucao_id,
            PaginaExtraida.url_original == url,
        )
        return db.execute(stmt).scalar_one_or_none()

    def count_by_status(
        self, db: Session, execucao_id: UUID
    ) -> dict[PaginaStatus, int]:
        """
        Conta páginas por status de uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução

        Returns:
            Dicionário {status: contagem}
        """
        stmt = (
            select(PaginaExtraida.status, func.count(PaginaExtraida.id).label("total"))
            .where(PaginaExtraida.execucao_id == execucao_id)
            .group_by(PaginaExtraida.status)
        )
        rows = db.execute(stmt).all()
        result: dict[PaginaStatus, int] = {s: 0 for s in PaginaStatus}
        for status, total in rows:
            result[status] = total
        return result

    def sum_tamanho_bytes(self, db: Session, execucao_id: UUID) -> int:
        """
        Soma total de bytes extraídos de uma execução.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução

        Returns:
            Soma total de bytes (0 se nenhuma página)
        """
        stmt = select(func.coalesce(func.sum(PaginaExtraida.tamanho_bytes), 0)).where(
            PaginaExtraida.execucao_id == execucao_id
        )
        return db.execute(stmt).scalar() or 0

    def delete_by_execucao_id(self, db: Session, execucao_id: UUID) -> int:
        """
        Deleta todas as páginas de uma execução via bulk DELETE.

        Args:
            db: Sessão do SQLAlchemy
            execucao_id: UUID da execução

        Returns:
            Quantidade de registros deletados
        """
        from sqlalchemy import delete

        stmt = delete(PaginaExtraida).where(PaginaExtraida.execucao_id == execucao_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount
