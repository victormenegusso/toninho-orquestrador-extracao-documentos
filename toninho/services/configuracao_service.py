"""Service para lógica de negócio de Configuracao."""

from datetime import datetime
from typing import List
from uuid import UUID

from croniter import croniter
from sqlalchemy.orm import Session

from toninho.core.exceptions import NotFoundError, ValidationError
from toninho.models.configuracao import Configuracao
from toninho.repositories.configuracao_repository import ConfiguracaoRepository
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.schemas.configuracao import (
    AgendamentoInfo,
    ConfiguracaoCreate,
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
)


class ConfiguracaoService:
    """Service para operações de negócio com Configuracao."""

    def __init__(
        self,
        repository: ConfiguracaoRepository,
        processo_repository: ProcessoRepository,
    ):
        """
        Inicializa o service.

        Args:
            repository: Repository de Configuracao
            processo_repository: Repository de Processo (para validações)
        """
        self.repository = repository
        self.processo_repository = processo_repository

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_configuracao(
        self,
        db: Session,
        processo_id: UUID,
        config_create: ConfiguracaoCreate,
    ) -> ConfiguracaoResponse:
        """
        Cria uma nova configuração para um processo.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo
            config_create: Dados de criação

        Returns:
            ConfiguracaoResponse

        Raises:
            NotFoundError: Se processo não existe
            ValidationError: Dados inválidos
        """
        # 1. Validar processo existe
        processo = self.processo_repository.get_by_id(db, processo_id)
        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        # 2. Aplicar processo_id ao schema
        config_data = config_create.model_dump()
        config_data["processo_id"] = processo_id

        # 3. Criar model
        configuracao = Configuracao(**config_data)

        # 4. Salvar
        configuracao = self.repository.create(db, configuracao)

        return ConfiguracaoResponse.model_validate(configuracao)

    def get_configuracao(self, db: Session, config_id: UUID) -> ConfiguracaoResponse:
        """
        Busca uma configuração por ID.

        Args:
            db: Sessão do banco de dados
            config_id: UUID da configuração

        Returns:
            ConfiguracaoResponse

        Raises:
            NotFoundError: Se a configuração não existe
        """
        configuracao = self.repository.get_by_id(db, config_id)
        if not configuracao:
            raise NotFoundError("Configuracao", str(config_id))
        return ConfiguracaoResponse.model_validate(configuracao)

    def get_configuracao_by_processo(
        self, db: Session, processo_id: UUID
    ) -> ConfiguracaoResponse:
        """
        Retorna a configuração mais recente de um processo.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo

        Returns:
            ConfiguracaoResponse

        Raises:
            NotFoundError: Se processo não existe ou não tem configuração
        """
        # Validar processo existe
        processo = self.processo_repository.get_by_id(db, processo_id)
        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        configuracao = self.repository.get_by_processo_id(db, processo_id)
        if not configuracao:
            raise NotFoundError(
                "Configuracao",
                f"processo {processo_id} não tem configuração",
            )
        return ConfiguracaoResponse.model_validate(configuracao)

    def list_configuracoes_by_processo(
        self, db: Session, processo_id: UUID
    ) -> List[ConfiguracaoResponse]:
        """
        Lista o histórico de configurações de um processo.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo

        Returns:
            Lista de ConfiguracaoResponse (mais recentes primeiro)

        Raises:
            NotFoundError: Se processo não existe
        """
        processo = self.processo_repository.get_by_id(db, processo_id)
        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        configuracoes = self.repository.get_all_by_processo_id(db, processo_id)
        return [ConfiguracaoResponse.model_validate(c) for c in configuracoes]

    def update_configuracao(
        self,
        db: Session,
        config_id: UUID,
        config_update: ConfiguracaoUpdate,
    ) -> ConfiguracaoResponse:
        """
        Atualiza uma configuração existente.

        Args:
            db: Sessão do banco de dados
            config_id: UUID da configuração
            config_update: Dados de atualização

        Returns:
            ConfiguracaoResponse atualizada

        Raises:
            NotFoundError: Se a configuração não existe
            ValidationError: Dados inválidos
        """
        configuracao = self.repository.get_by_id(db, config_id)
        if not configuracao:
            raise NotFoundError("Configuracao", str(config_id))

        # Aplicar campos fornecidos
        update_data = config_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(configuracao, field, value)

        # Validar consistência cron/agendamento_tipo após update
        from toninho.models.enums import AgendamentoTipo

        agendamento_tipo = getattr(configuracao, "agendamento_tipo", None)
        agendamento_cron = getattr(configuracao, "agendamento_cron", None)

        if agendamento_tipo == AgendamentoTipo.RECORRENTE and not agendamento_cron:
            raise ValidationError(
                "agendamento_cron é obrigatório quando agendamento_tipo=RECORRENTE"
            )

        configuracao = self.repository.update(db, configuracao)
        return ConfiguracaoResponse.model_validate(configuracao)

    def delete_configuracao(self, db: Session, config_id: UUID) -> bool:
        """
        Remove uma configuração pelo ID.

        Args:
            db: Sessão do banco de dados
            config_id: UUID da configuração

        Returns:
            True se removida

        Raises:
            NotFoundError: Se a configuração não existe
        """
        configuracao = self.repository.get_by_id(db, config_id)
        if not configuracao:
            raise NotFoundError("Configuracao", str(config_id))

        return self.repository.delete(db, config_id)

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def validar_agendamento(self, expressao_cron: str) -> AgendamentoInfo:
        """
        Valida uma expressão cron e retorna informações de agendamento.

        Args:
            expressao_cron: Expressão cron a ser validada

        Returns:
            AgendamentoInfo com próximas execuções
        """
        try:
            cron = croniter(expressao_cron, datetime.now())
            proximas = [cron.get_next(datetime) for _ in range(5)]
            valida = True
            descricao = self._descrever_cron(expressao_cron)
        except (ValueError, KeyError):
            proximas = []
            valida = False
            descricao = "Expressão cron inválida"

        return AgendamentoInfo(
            expressao_cron=expressao_cron,
            valida=valida,
            proximas_execucoes=proximas,
            descricao_legivel=descricao,
        )

    @staticmethod
    def _descrever_cron(expressao: str) -> str:
        """Gera descrição legível simplificada de uma expressão cron."""
        try:
            parts = expressao.split()
            minuto, hora, dia, mes, dia_semana = parts

            if minuto.startswith("*/"):
                intervalo = minuto[2:]
                return f"A cada {intervalo} minuto(s)"
            if dia_semana == "1-5":
                return f"Dias úteis às {hora.zfill(2)}:{minuto.zfill(2)}"
            if dia == "*" and mes == "*" and dia_semana == "*":
                return f"Diariamente às {hora.zfill(2)}:{minuto.zfill(2)}"
            if dia == "1" and mes == "*":
                return f"Todo primeiro dia do mês às {hora.zfill(2)}:{minuto.zfill(2)}"
            return expressao
        except Exception:
            return expressao
