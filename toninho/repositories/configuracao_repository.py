"""Repository para operações de banco de dados da entidade Configuracao."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from toninho.models.configuracao import Configuracao


class ConfiguracaoRepository:
    """Repository para acesso a dados de Configuracao."""

    def create(self, db: Session, configuracao: Configuracao) -> Configuracao:
        """
        Insere uma nova configuração no banco de dados.

        Args:
            db: Sessão do SQLAlchemy
            configuracao: Instância do modelo Configuracao

        Returns:
            Configuracao criada com ID gerado
        """
        db.add(configuracao)
        db.commit()
        db.refresh(configuracao)
        return configuracao

    def get_by_id(self, db: Session, config_id: UUID) -> Configuracao | None:
        """
        Busca uma configuração por ID.

        Args:
            db: Sessão do SQLAlchemy
            config_id: UUID da configuração

        Returns:
            Configuracao encontrada ou None
        """
        stmt = select(Configuracao).where(Configuracao.id == config_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_processo_id(self, db: Session, processo_id: UUID) -> Configuracao | None:
        """
        Retorna a configuração mais recente de um processo.

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Configuracao mais recente ou None
        """
        stmt = (
            select(Configuracao)
            .where(Configuracao.processo_id == processo_id)
            .order_by(Configuracao.created_at.desc())
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_all_by_processo_id(
        self, db: Session, processo_id: UUID
    ) -> list[Configuracao]:
        """
        Retorna o histórico de configurações de um processo (mais recentes primeiro).

        Args:
            db: Sessão do SQLAlchemy
            processo_id: UUID do processo

        Returns:
            Lista de configurações ordenada por created_at desc
        """
        stmt = (
            select(Configuracao)
            .where(Configuracao.processo_id == processo_id)
            .order_by(Configuracao.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def update(self, db: Session, configuracao: Configuracao) -> Configuracao:
        """
        Atualiza uma configuração no banco de dados.

        Args:
            db: Sessão do SQLAlchemy
            configuracao: Configuracao com dados atualizados

        Returns:
            Configuracao atualizada
        """
        db.add(configuracao)
        db.commit()
        db.refresh(configuracao)
        return configuracao

    def delete(self, db: Session, config_id: UUID) -> bool:
        """
        Remove uma configuração pelo ID.

        Args:
            db: Sessão do SQLAlchemy
            config_id: UUID da configuração a ser removida

        Returns:
            True se removida, False se não encontrada
        """
        configuracao = self.get_by_id(db, config_id)
        if not configuracao:
            return False
        db.delete(configuracao)
        db.commit()
        return True
