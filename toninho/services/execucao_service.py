"""Service para lógica de negócio de Execucao."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import ExecucaoStatus
from toninho.models.execucao import Execucao
from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.schemas.execucao import (
    ExecucaoCreate,
    ExecucaoDetail,
    ExecucaoMetricas,
    ExecucaoResponse,
    ExecucaoStatusUpdate,
    ExecucaoSummary,
    ProgressoResponse,
)
from toninho.schemas.responses import PaginationMeta, SuccessListResponse

# ---------------------------------------------------------------------------
# Máquina de estados
# ---------------------------------------------------------------------------

TRANSICOES_PERMITIDAS: dict[ExecucaoStatus, list[ExecucaoStatus]] = {
    ExecucaoStatus.CRIADO: [ExecucaoStatus.AGUARDANDO],
    ExecucaoStatus.AGUARDANDO: [
        ExecucaoStatus.EM_EXECUCAO,
        ExecucaoStatus.CANCELADO,
    ],
    ExecucaoStatus.EM_EXECUCAO: [
        ExecucaoStatus.PAUSADO,
        ExecucaoStatus.CONCLUIDO,
        ExecucaoStatus.FALHOU,
        ExecucaoStatus.CANCELADO,
        ExecucaoStatus.CONCLUIDO_COM_ERROS,
    ],
    ExecucaoStatus.PAUSADO: [
        ExecucaoStatus.EM_EXECUCAO,
        ExecucaoStatus.CANCELADO,
    ],
    # Estados finais não permitem transições
    ExecucaoStatus.CONCLUIDO: [],
    ExecucaoStatus.FALHOU: [],
    ExecucaoStatus.CANCELADO: [],
    ExecucaoStatus.CONCLUIDO_COM_ERROS: [],
}


def validar_transicao(status_atual: ExecucaoStatus, status_novo: ExecucaoStatus) -> bool:
    """Verifica se a transição de status é permitida."""
    return status_novo in TRANSICOES_PERMITIDAS.get(status_atual, [])


class ExecucaoService:
    """Service para operações de negócio com Execucao."""

    def __init__(
        self,
        repository: ExecucaoRepository,
        processo_repository: ProcessoRepository,
    ):
        """
        Inicializa o service.

        Args:
            repository: Repository de Execucao
            processo_repository: Repository de Processo
        """
        self.repository = repository
        self.processo_repository = processo_repository

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_execucao(
        self,
        db: Session,
        processo_id: UUID,
        execucao_create: Optional[ExecucaoCreate] = None,
    ) -> ExecucaoResponse:
        """
        Cria e enfileira uma nova execução para um processo.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo
            execucao_create: Dados de criação (opcional)

        Returns:
            ExecucaoResponse

        Raises:
            NotFoundError: Se processo não existe
            ConflictError: Se já há execução EM_EXECUCAO do mesmo processo
        """
        # 1. Validar processo existe
        processo = self.processo_repository.get_by_id(db, processo_id)
        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        # 2. Validar que não há execução ativa do mesmo processo
        execucao_ativa = self.repository.get_em_execucao(db, processo_id)
        if execucao_ativa:
            raise ConflictError(
                f"Já existe uma execução em andamento para o processo {processo_id}"
            )

        # 3. Criar execução com status CRIADO
        execucao = Execucao(
            processo_id=processo_id,
            status=ExecucaoStatus.CRIADO,
        )
        execucao = self.repository.create(db, execucao)

        # 4. Tentar enfileirar task Celery (best-effort)
        execucao = self._enfileirar_task(db, execucao)

        return ExecucaoResponse.model_validate(execucao)

    def _enfileirar_task(self, db: Session, execucao: Execucao) -> Execucao:
        """
        Tenta enfileirar a task Celery para execução.

        Em ambiente sem Celery configurado, apenas atualiza para AGUARDANDO.

        Args:
            db: Sessão do banco de dados
            execucao: Execução a ser enfileirada

        Returns:
            Execucao atualizada
        """
        try:
            from toninho.workers.tasks.execucao_task import executar_processo_task

            task = executar_processo_task.delay(str(execucao.id))
            execucao.celery_task_id = str(task.id) if hasattr(task, "id") else None
        except Exception:
            pass  # Celery não disponível; execução fica em CRIADO

        execucao.status = ExecucaoStatus.AGUARDANDO
        return self.repository.update(db, execucao)

    def get_execucao(self, db: Session, execucao_id: UUID) -> ExecucaoResponse:
        """
        Busca uma execução por ID.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ExecucaoResponse

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))
        return ExecucaoResponse.model_validate(execucao)

    def get_execucao_detail(self, db: Session, execucao_id: UUID) -> ExecucaoDetail:
        """
        Busca uma execução com detalhes completos.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ExecucaoDetail

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.repository.get_by_id(db, execucao_id, with_relations=True)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        metricas = self._calcular_metricas(execucao)

        return ExecucaoDetail(
            id=execucao.id,
            processo_id=execucao.processo_id,
            status=execucao.status,
            iniciado_em=execucao.iniciado_em,
            finalizado_em=execucao.finalizado_em,
            paginas_processadas=execucao.paginas_processadas,
            bytes_extraidos=execucao.bytes_extraidos,
            taxa_erro=execucao.taxa_erro,
            tentativa_atual=execucao.tentativa_atual,
            created_at=execucao.created_at,
            updated_at=execucao.updated_at,
            metricas=metricas,
        )

    def list_execucoes(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        processo_id: Optional[UUID] = None,
        status: Optional[ExecucaoStatus] = None,
        ordem: str = "desc",
    ) -> SuccessListResponse:
        """
        Lista execuções com paginação e filtros.

        Args:
            db: Sessão do banco de dados
            page: Número da página (1-indexed)
            per_page: Itens por página
            processo_id: Filtro por processo (opcional)
            status: Filtro por status (opcional)
            ordem: "asc" ou "desc"

        Returns:
            SuccessListResponse paginado
        """
        skip = (page - 1) * per_page

        if processo_id:
            execucoes, total = self.repository.get_all_by_processo_id(
                db, processo_id, skip=skip, limit=per_page, status=status
            )
        else:
            execucoes, total = self.repository.get_all(
                db, skip=skip, limit=per_page, status=status, ordem=ordem
            )

        import math

        total_pages = math.ceil(total / per_page) if per_page else 1

        data = [ExecucaoSummary.model_validate(e) for e in execucoes]

        return SuccessListResponse(
            data=data,
            meta=PaginationMeta(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )

    def update_execucao_status(
        self,
        db: Session,
        execucao_id: UUID,
        status_update: ExecucaoStatusUpdate,
    ) -> ExecucaoResponse:
        """
        Atualiza o status de uma execução, validando a transição.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução
            status_update: Novo status desejado

        Returns:
            ExecucaoResponse atualizada

        Raises:
            NotFoundError: Se execução não existe
            ValidationError: Se transição de estado é inválida
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        if not validar_transicao(execucao.status, status_update.status):
            raise ValidationError(
                f"Transição inválida: {execucao.status} → {status_update.status}"
            )

        execucao.status = status_update.status
        execucao = self.repository.update(db, execucao)
        return ExecucaoResponse.model_validate(execucao)

    # ------------------------------------------------------------------
    # Ações de controle
    # ------------------------------------------------------------------

    def cancelar_execucao(self, db: Session, execucao_id: UUID) -> ExecucaoResponse:
        """
        Cancela uma execução em andamento.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ExecucaoResponse atualizada

        Raises:
            NotFoundError: Se execução não existe
            ConflictError: Se execução já está finalizada
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        if not validar_transicao(execucao.status, ExecucaoStatus.CANCELADO):
            raise ConflictError(
                f"Execução não pode ser cancelada. Status atual: {execucao.status}"
            )

        # Tentar revogar task Celery
        self._revogar_task(execucao)

        execucao.status = ExecucaoStatus.CANCELADO
        execucao.finalizado_em = datetime.now(timezone.utc)
        execucao = self.repository.update(db, execucao)
        return ExecucaoResponse.model_validate(execucao)

    def pausar_execucao(self, db: Session, execucao_id: UUID) -> ExecucaoResponse:
        """
        Pausa uma execução em andamento.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ExecucaoResponse atualizada

        Raises:
            NotFoundError: Se execução não existe
            ConflictError: Se execução não está EM_EXECUCAO
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        if not validar_transicao(execucao.status, ExecucaoStatus.PAUSADO):
            raise ConflictError(
                f"Execução não pode ser pausada. Status atual: {execucao.status}"
            )

        execucao.status = ExecucaoStatus.PAUSADO
        execucao = self.repository.update(db, execucao)
        return ExecucaoResponse.model_validate(execucao)

    def retomar_execucao(self, db: Session, execucao_id: UUID) -> ExecucaoResponse:
        """
        Retoma uma execução pausada.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ExecucaoResponse atualizada

        Raises:
            NotFoundError: Se execução não existe
            ConflictError: Se execução não está PAUSADO
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        if execucao.status != ExecucaoStatus.PAUSADO:
            raise ConflictError(
                f"Execução não pode ser retomada. Status atual: {execucao.status}"
            )

        execucao.status = ExecucaoStatus.EM_EXECUCAO
        execucao = self.repository.update(db, execucao)
        return ExecucaoResponse.model_validate(execucao)

    # ------------------------------------------------------------------
    # Métricas e progresso
    # ------------------------------------------------------------------

    def get_execucao_metricas(
        self, db: Session, execucao_id: UUID
    ) -> ExecucaoMetricas:
        """
        Retorna métricas detalhadas de uma execução.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ExecucaoMetricas

        Raises:
            NotFoundError: Se execução não existe
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))
        return self._calcular_metricas(execucao)

    def get_progresso(self, db: Session, execucao_id: UUID) -> ProgressoResponse:
        """
        Retorna progresso em tempo real de uma execução.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            ProgressoResponse

        Raises:
            NotFoundError: Se execução não existe
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        # Tentar obter total de páginas da configuração mais recente
        total_paginas = self._get_total_paginas(db, execucao)

        paginas = execucao.paginas_processadas
        progresso = (paginas / total_paginas * 100) if total_paginas > 0 else 0.0

        # Calcular tempo decorrido
        tempo_decorrido: Optional[int] = None
        tempo_estimado: Optional[int] = None
        if execucao.iniciado_em:
            agora = datetime.now(timezone.utc)
            iniciado = execucao.iniciado_em
            if iniciado.tzinfo is None:
                from datetime import timezone as tz
                iniciado = iniciado.replace(tzinfo=tz.utc)
            tempo_decorrido = int((agora - iniciado).total_seconds())
            if paginas > 0 and total_paginas > 0:
                segundos_por_pagina = tempo_decorrido / paginas
                restantes = total_paginas - paginas
                tempo_estimado = int(segundos_por_pagina * restantes)

        return ProgressoResponse(
            execucao_id=execucao.id,
            status=execucao.status,
            paginas_processadas=paginas,
            total_paginas=total_paginas,
            progresso_percentual=round(progresso, 2),
            tempo_decorrido_segundos=tempo_decorrido,
            tempo_estimado_restante_segundos=tempo_estimado,
            ultima_atualizacao=execucao.updated_at,
        )

    # ------------------------------------------------------------------
    # Deleção
    # ------------------------------------------------------------------

    def delete_execucao(self, db: Session, execucao_id: UUID) -> bool:
        """
        Remove uma execução (apenas se não EM_EXECUCAO).

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            True se removida

        Raises:
            NotFoundError: Se execução não existe
            ConflictError: Se execução está EM_EXECUCAO
        """
        execucao = self.repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        if execucao.status == ExecucaoStatus.EM_EXECUCAO:
            raise ConflictError(
                "Não é possível deletar uma execução em andamento"
            )

        return self.repository.delete(db, execucao_id)

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    @staticmethod
    def _calcular_metricas(execucao: Execucao) -> ExecucaoMetricas:
        """Calcula métricas a partir do model de execução."""
        duracao: Optional[int] = None
        tempo_medio: Optional[float] = None

        if execucao.iniciado_em and execucao.finalizado_em:
            ini = execucao.iniciado_em
            fim = execucao.finalizado_em
            duracao = int((fim - ini).total_seconds())
            if execucao.paginas_processadas > 0:
                tempo_medio = duracao / execucao.paginas_processadas

        taxa_sucesso = max(0.0, 100.0 - execucao.taxa_erro)

        return ExecucaoMetricas(
            execucao_id=execucao.id,
            paginas_processadas=execucao.paginas_processadas,
            bytes_extraidos=execucao.bytes_extraidos,
            taxa_erro=execucao.taxa_erro,
            duracao_segundos=duracao,
            tempo_medio_por_pagina_segundos=tempo_medio,
            taxa_sucesso=taxa_sucesso,
        )

    def _get_total_paginas(self, db: Session, execucao: Execucao) -> int:
        """Tenta obter o total de URLs da configuração mais recente do processo."""
        try:
            from toninho.repositories.configuracao_repository import (
                ConfiguracaoRepository,
            )

            config_repo = ConfiguracaoRepository()
            config = config_repo.get_by_processo_id(db, execucao.processo_id)
            if config and config.urls:
                return len(config.urls)
        except Exception:
            pass
        return 0

    @staticmethod
    def _revogar_task(execucao: Execucao) -> None:
        """Tenta revogar a task Celery associada (best-effort)."""
        try:
            task_id = getattr(execucao, "celery_task_id", None)
            if task_id:
                from celery import current_app  # type: ignore

                current_app.control.revoke(task_id, terminate=True)
        except Exception:
            pass
