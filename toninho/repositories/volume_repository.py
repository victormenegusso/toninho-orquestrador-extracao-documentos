"""Repository para operações de banco de dados da entidade Volume."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from toninho.models.configuracao import Configuracao
from toninho.models.enums import VolumeStatus
from toninho.models.volume import Volume


class VolumeRepository:
    """Repository para acesso a dados de Volume."""

    def create(self, db: Session, volume: Volume) -> Volume:
        """
        Insere um novo volume no banco de dados.

        Args:
            db: Sessão do SQLAlchemy
            volume: Instância do modelo Volume

        Returns:
            Volume criado com ID gerado
        """
        db.add(volume)
        db.commit()
        db.refresh(volume)
        return volume

    def get_by_id(self, db: Session, volume_id: UUID) -> Volume | None:
        """
        Busca um volume por ID.

        Args:
            db: Sessão do SQLAlchemy
            volume_id: UUID do volume

        Returns:
            Volume encontrado ou None
        """
        stmt = select(Volume).where(Volume.id == volume_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_nome(self, db: Session, nome: str) -> Volume | None:
        """
        Busca um volume por nome.

        Args:
            db: Sessão do SQLAlchemy
            nome: Nome do volume

        Returns:
            Volume encontrado ou None
        """
        stmt = select(Volume).where(Volume.nome == nome)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_path(self, db: Session, path: str) -> Volume | None:
        """
        Busca um volume por path.

        Args:
            db: Sessão do SQLAlchemy
            path: Caminho do volume

        Returns:
            Volume encontrado ou None
        """
        stmt = select(Volume).where(Volume.path == path)
        return db.execute(stmt).scalar_one_or_none()

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: VolumeStatus | None = None,
        busca: str | None = None,
    ) -> tuple[list[Volume], int]:
        """
        Lista volumes com paginação e filtros.

        Args:
            db: Sessão do SQLAlchemy
            skip: Número de registros para pular
            limit: Número máximo de registros
            status: Filtro por status (opcional)
            busca: Filtro por nome (LIKE, opcional)

        Returns:
            Tupla (lista de volumes, total de registros)
        """
        stmt = select(Volume)

        if status:
            stmt = stmt.where(Volume.status == status)

        if busca:
            stmt = stmt.where(Volume.nome.ilike(f"%{busca}%"))

        # Contar total antes da paginação
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar()

        # Ordenação e paginação
        stmt = stmt.order_by(Volume.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = db.execute(stmt)
        volumes = result.scalars().all()

        return list(volumes), total

    def get_ativos(self, db: Session) -> list[Volume]:
        """
        Retorna todos os volumes com status ATIVO.

        Args:
            db: Sessão do SQLAlchemy

        Returns:
            Lista de volumes ativos ordenados por nome
        """
        stmt = (
            select(Volume)
            .where(Volume.status == VolumeStatus.ATIVO)
            .order_by(Volume.nome.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def update(self, db: Session, volume: Volume) -> Volume:
        """
        Atualiza um volume no banco de dados.

        Args:
            db: Sessão do SQLAlchemy
            volume: Volume com dados atualizados

        Returns:
            Volume atualizado
        """
        db.add(volume)
        db.commit()
        db.refresh(volume)
        return volume

    def delete(self, db: Session, volume_id: UUID) -> bool:
        """
        Remove um volume pelo ID.

        Args:
            db: Sessão do SQLAlchemy
            volume_id: UUID do volume a ser removido

        Returns:
            True se removido, False se não encontrado
        """
        volume = self.get_by_id(db, volume_id)
        if not volume:
            return False
        db.delete(volume)
        db.commit()
        return True

    def exists_by_nome(
        self, db: Session, nome: str, exclude_id: UUID | None = None
    ) -> bool:
        """
        Verifica se já existe um volume com o nome informado.

        Args:
            db: Sessão do SQLAlchemy
            nome: Nome do volume
            exclude_id: ID do volume a ser ignorado (opcional, para updates)

        Returns:
            True se existe, False caso contrário
        """
        stmt = select(Volume).where(Volume.nome == nome)

        if exclude_id:
            stmt = stmt.where(Volume.id != exclude_id)

        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def exists_by_path(
        self, db: Session, path: str, exclude_id: UUID | None = None
    ) -> bool:
        """
        Verifica se já existe um volume com o path informado.

        Args:
            db: Sessão do SQLAlchemy
            path: Caminho do volume
            exclude_id: ID do volume a ser ignorado (opcional, para updates)

        Returns:
            True se existe, False caso contrário
        """
        stmt = select(Volume).where(Volume.path == path)

        if exclude_id:
            stmt = stmt.where(Volume.id != exclude_id)

        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def count_configuracoes(self, db: Session, volume_id: UUID) -> int:
        """
        Conta quantas configurações estão vinculadas a um volume.

        Args:
            db: Sessão do SQLAlchemy
            volume_id: UUID do volume

        Returns:
            Total de configurações vinculadas
        """
        stmt = select(func.count(Configuracao.id)).where(
            Configuracao.volume_id == volume_id
        )
        result = db.execute(stmt)
        return result.scalar() or 0
