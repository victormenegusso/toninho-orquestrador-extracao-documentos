"""Service para lógica de negócio de Processo."""

from uuid import UUID

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from toninho.core.exceptions import ConflictError, NotFoundError, ValidationError
from toninho.models.enums import ExecucaoStatus, ProcessoStatus
from toninho.models.execucao import Execucao
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.models.processo import Processo
from toninho.repositories.processo_repository import ProcessoRepository
from toninho.schemas.configuracao import ConfiguracaoResponse
from toninho.schemas.execucao import ExecucaoResponse
from toninho.schemas.processo import (
    ProcessoCreate,
    ProcessoDetail,
    ProcessoMetricas,
    ProcessoResponse,
    ProcessoSummary,
    ProcessoUpdate,
)
from toninho.schemas.responses import PaginationMeta, SuccessListResponse


class ProcessoService:
    """Service para operações de negócio com Processo."""

    def __init__(self, repository: ProcessoRepository):
        """
        Inicializa o service.

        Args:
            repository: Repository de Processo
        """
        self.repository = repository

    def create_processo(
        self, db: Session, processo_create: ProcessoCreate
    ) -> ProcessoResponse:
        """
        Cria um novo processo.

        Args:
            db: Sessão do banco de dados
            processo_create: Dados para criação

        Returns:
            ProcessoResponse com dados do processo criado

        Raises:
            ConflictError: Se já existe processo com o mesmo nome
        """
        # Validar nome único
        if self.repository.exists_by_nome(db, processo_create.nome):
            raise ConflictError(
                f"Já existe um processo com o nome '{processo_create.nome}'"
            )

        # Criar model
        processo = Processo(
            nome=processo_create.nome,
            descricao=processo_create.descricao,
            status=processo_create.status,
        )

        # Salvar no banco
        processo = self.repository.create(db, processo)

        # Converter para response
        return ProcessoResponse.model_validate(processo)

    def get_processo(self, db: Session, processo_id: UUID) -> ProcessoResponse:
        """
        Busca um processo por ID.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo

        Returns:
            ProcessoResponse com dados do processo

        Raises:
            NotFoundError: Se processo não existe
        """
        processo = self.repository.get_by_id(db, processo_id)

        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        return ProcessoResponse.model_validate(processo)

    def get_processo_detail(self, db: Session, processo_id: UUID) -> ProcessoDetail:
        """
        Busca um processo por ID com detalhes completos.

        Inclui configurações e últimas 5 execuções.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo

        Returns:
            ProcessoDetail com dados completos

        Raises:
            NotFoundError: Se processo não existe
        """
        processo = self.repository.get_by_id_with_details(db, processo_id)

        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        # Converter configurações
        configuracoes = [
            ConfiguracaoResponse.model_validate(config)
            for config in processo.configuracoes
        ]

        # Adicionar últimas 5 execuções ordenadas por data (mais recentes primeiro)
        execucoes_ordenadas = sorted(
            processo.execucoes, key=lambda e: e.created_at, reverse=True
        )[:5]
        execucoes_recentes = [
            ExecucaoResponse.model_validate(exec) for exec in execucoes_ordenadas
        ]

        # Calcular métricas básicas
        total_execucoes = len(processo.execucoes)
        ultima_execucao_em = (
            max(e.created_at for e in processo.execucoes)
            if processo.execucoes
            else None
        )

        # Criar ProcessoDetail manualmente
        detail = ProcessoDetail(
            id=processo.id,
            nome=processo.nome,
            descricao=processo.descricao,
            status=processo.status,
            created_at=processo.created_at,
            updated_at=processo.updated_at,
            configuracoes=configuracoes,
            execucoes_recentes=execucoes_recentes,
            total_execucoes=total_execucoes,
            ultima_execucao_em=ultima_execucao_em,
        )

        return detail

    def list_processos(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        status: ProcessoStatus | None = None,
        busca: str | None = None,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> SuccessListResponse:
        """
        Lista processos com paginação e filtros.

        Args:
            db: Sessão do banco de dados
            page: Número da página (1-indexed)
            per_page: Registros por página (1-100)
            status: Filtro por status (opcional)
            busca: Busca por nome (opcional)
            order_by: Campo para ordenação
            order_dir: Direção da ordenação ("asc" ou "desc")

        Returns:
            SuccessListResponse com lista paginada

        Raises:
            ValidationError: Se parâmetros inválidos
        """
        # Validar parâmetros
        if page < 1:
            raise ValidationError("Número da página deve ser maior que 0")

        if per_page < 1 or per_page > 100:
            raise ValidationError("Registros por página deve estar entre 1 e 100")

        # Calcular skip
        skip = (page - 1) * per_page

        # Buscar processos
        processos, total = self.repository.get_all(
            db=db,
            skip=skip,
            limit=per_page,
            status=status,
            busca=busca,
            order_by=order_by,
            order_dir=order_dir,
        )

        # Converter para summary
        items = [ProcessoSummary.model_validate(p) for p in processos]

        # Criar metadata de paginação
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        meta = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        )

        return SuccessListResponse(data=items, meta=meta)

    def update_processo(
        self, db: Session, processo_id: UUID, processo_update: ProcessoUpdate
    ) -> ProcessoResponse:
        """
        Atualiza um processo existente.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo
            processo_update: Dados para atualização

        Returns:
            ProcessoResponse com dados atualizados

        Raises:
            NotFoundError: Se processo não existe
            ConflictError: Se nome duplicado
            ValidationError: Se nenhum campo fornecido
        """
        # Buscar processo
        processo = self.repository.get_by_id(db, processo_id)

        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        # Verificar se ao menos um campo foi fornecido
        update_data = processo_update.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("Nenhum campo fornecido para atualização")

        # Validar nome único se foi alterado
        if (
            processo_update.nome
            and processo_update.nome != processo.nome
            and self.repository.exists_by_nome(
                db, processo_update.nome, exclude_id=processo_id
            )
        ):
            raise ConflictError(
                f"Já existe um processo com o nome '{processo_update.nome}'"
            )

        # Aplicar mudanças
        for field, value in update_data.items():
            setattr(processo, field, value)

        # Salvar
        processo = self.repository.update(db, processo)

        return ProcessoResponse.model_validate(processo)

    def delete_processo(self, db: Session, processo_id: UUID) -> bool:
        """
        Deleta um processo.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo

        Returns:
            True se deletado com sucesso

        Raises:
            NotFoundError: Se processo não existe
            ConflictError: Se há execuções em andamento
        """
        # Buscar processo
        processo = self.repository.get_by_id_with_details(db, processo_id)

        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        # Verificar se há execuções em andamento
        execucoes_em_andamento = [
            e for e in processo.execucoes if e.status == ExecucaoStatus.EM_EXECUCAO
        ]

        if execucoes_em_andamento:
            raise ConflictError(
                f"Não é possível deletar processo com {len(execucoes_em_andamento)} "
                "execução(ões) em andamento"
            )

        # Deletar
        return self.repository.delete(db, processo_id)

    def get_processo_metricas(self, db: Session, processo_id: UUID) -> ProcessoMetricas:
        """
        Calcula métricas agregadas de um processo.

        Args:
            db: Sessão do banco de dados
            processo_id: UUID do processo

        Returns:
            ProcessoMetricas com estatísticas

        Raises:
            NotFoundError: Se processo não existe
        """
        # Buscar processo
        processo = self.repository.get_by_id(db, processo_id)

        if not processo:
            raise NotFoundError("Processo", str(processo_id))

        # Query para métricas de execuções
        exec_stats = (
            db.query(
                func.count(Execucao.id).label("total"),
                func.sum(
                    case(
                        (Execucao.status == ExecucaoStatus.CONCLUIDO, 1),
                        else_=0,
                    )
                ).label("sucesso"),
                func.sum(
                    case(
                        (Execucao.status == ExecucaoStatus.FALHOU, 1),
                        else_=0,
                    )
                ).label("falha"),
                func.avg(
                    case(
                        (
                            and_(
                                Execucao.finalizado_em.isnot(None),
                                Execucao.iniciado_em.isnot(None),
                            ),
                            func.extract(
                                "epoch",
                                Execucao.finalizado_em - Execucao.iniciado_em,
                            ),
                        ),
                        else_=None,
                    )
                ).label("tempo_medio"),
                func.max(Execucao.created_at).label("ultima_execucao"),
            )
            .filter(Execucao.processo_id == processo_id)
            .first()
        )

        total_execucoes = exec_stats.total or 0
        execucoes_sucesso = exec_stats.sucesso or 0
        execucoes_falha = exec_stats.falha or 0
        tempo_medio = exec_stats.tempo_medio
        ultima_execucao_em = exec_stats.ultima_execucao

        # Calcular taxa de sucesso
        taxa_sucesso = (
            (execucoes_sucesso / total_execucoes * 100) if total_execucoes > 0 else 0.0
        )

        # Query para métricas de páginas extraídas
        pagina_stats = (
            db.query(
                func.count(PaginaExtraida.id).label("total_paginas"),
                func.sum(PaginaExtraida.tamanho_bytes).label("total_bytes"),
            )
            .join(Execucao, PaginaExtraida.execucao_id == Execucao.id)
            .filter(Execucao.processo_id == processo_id)
            .first()
        )

        total_paginas = pagina_stats.total_paginas or 0
        total_bytes = pagina_stats.total_bytes or 0

        return ProcessoMetricas(
            processo_id=processo_id,
            total_execucoes=total_execucoes,
            execucoes_sucesso=execucoes_sucesso,
            execucoes_falha=execucoes_falha,
            taxa_sucesso=round(taxa_sucesso, 2),
            tempo_medio_execucao_segundos=round(tempo_medio, 2)
            if tempo_medio
            else None,
            total_paginas_extraidas=total_paginas,
            total_bytes_extraidos=total_bytes,
            ultima_execucao_em=ultima_execucao_em,
        )
