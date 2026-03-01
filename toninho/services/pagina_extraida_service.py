"""Service para lógica de negócio de PaginaExtraida."""

import math
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from toninho.core.exceptions import NotFoundError, ValidationError
from toninho.models.enums import PaginaStatus
from toninho.models.execucao import Execucao
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.repositories.execucao_repository import ExecucaoRepository
from toninho.repositories.pagina_extraida_repository import PaginaExtraidaRepository
from toninho.schemas.pagina_extraida import (
    EstatisticasPaginas,
    PaginaExtraidaCreate,
    PaginaExtraidaDetail,
    PaginaExtraidaResponse,
    PaginaExtraidaSummary,
)
from toninho.schemas.responses import PaginationMeta, SuccessListResponse


class PaginaExtraidaService:
    """Service para operações de negócio com PaginaExtraida."""

    def __init__(
        self,
        repository: PaginaExtraidaRepository,
        execucao_repository: ExecucaoRepository,
    ):
        """
        Inicializa o service.

        Args:
            repository: Repository de PaginaExtraida
            execucao_repository: Repository de Execucao
        """
        self.repository = repository
        self.execucao_repository = execucao_repository

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_pagina_extraida(
        self, db: Session, pagina_create: PaginaExtraidaCreate
    ) -> PaginaExtraidaResponse:
        """
        Cria uma página extraída.

        Args:
            db: Sessão do banco de dados
            pagina_create: Dados de criação

        Returns:
            PaginaExtraidaResponse

        Raises:
            NotFoundError: Se a execução não existe
            ValidationError: Se status=FALHOU sem erro_mensagem
        """
        execucao = self.execucao_repository.get_by_id(db, pagina_create.execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(pagina_create.execucao_id))

        if pagina_create.status == PaginaStatus.FALHOU and not pagina_create.erro_mensagem:
            raise ValidationError("erro_mensagem é obrigatória quando status=FALHOU")

        pagina = PaginaExtraida(
            execucao_id=pagina_create.execucao_id,
            url_original=pagina_create.url_original,
            caminho_arquivo=pagina_create.caminho_arquivo,
            status=pagina_create.status,
            tamanho_bytes=pagina_create.tamanho_bytes,
            erro_mensagem=pagina_create.erro_mensagem,
        )
        pagina = self.repository.create(db, pagina)

        # Atualizar métricas da execução
        self._atualizar_metricas_execucao(db, execucao, paginas_novas=[pagina])

        return PaginaExtraidaResponse.model_validate(pagina)

    def create_pagina_extraida_batch(
        self, db: Session, paginas_create: List[PaginaExtraidaCreate]
    ) -> List[PaginaExtraidaResponse]:
        """
        Cria múltiplas páginas extraídas em lote.

        Args:
            db: Sessão do banco de dados
            paginas_create: Lista de dados de criação

        Returns:
            Lista de PaginaExtraidaResponse

        Raises:
            NotFoundError: Se alguma execução não existe
        """
        execucao_ids = {pc.execucao_id for pc in paginas_create}
        execucoes = {}
        for execucao_id in execucao_ids:
            execucao = self.execucao_repository.get_by_id(db, execucao_id)
            if not execucao:
                raise NotFoundError("Execucao", str(execucao_id))
            execucoes[execucao_id] = execucao

        paginas = [
            PaginaExtraida(
                execucao_id=pc.execucao_id,
                url_original=pc.url_original,
                caminho_arquivo=pc.caminho_arquivo,
                status=pc.status,
                tamanho_bytes=pc.tamanho_bytes,
                erro_mensagem=pc.erro_mensagem,
            )
            for pc in paginas_create
        ]
        paginas = self.repository.create_batch(db, paginas)

        # Atualizar métricas para cada execução
        for execucao_id, execucao in execucoes.items():
            paginas_da_execucao = [p for p in paginas if p.execucao_id == execucao_id]
            self._atualizar_metricas_execucao(db, execucao, paginas_novas=paginas_da_execucao)

        return [PaginaExtraidaResponse.model_validate(p) for p in paginas]

    def get_pagina_extraida(
        self, db: Session, pagina_id: UUID
    ) -> PaginaExtraidaDetail:
        """
        Busca uma página extraída por ID.

        Args:
            db: Sessão do banco de dados
            pagina_id: UUID da página

        Returns:
            PaginaExtraidaDetail (inclui download_url)

        Raises:
            NotFoundError: Se a página não existe
        """
        pagina = self.repository.get_by_id(db, pagina_id)
        if not pagina:
            raise NotFoundError("PaginaExtraida", str(pagina_id))
        return PaginaExtraidaDetail.model_validate(pagina)

    def list_paginas_by_execucao(
        self,
        db: Session,
        execucao_id: UUID,
        page: int = 1,
        per_page: int = 100,
        status: Optional[PaginaStatus] = None,
    ) -> SuccessListResponse[PaginaExtraidaSummary]:
        """
        Lista páginas de uma execução com paginação.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução
            page: Número da página (1-indexed)
            per_page: Itens por página
            status: Filtro por status

        Returns:
            SuccessListResponse paginado

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.execucao_repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        skip = (page - 1) * per_page
        paginas, total = self.repository.get_by_execucao_id(
            db, execucao_id, skip=skip, limit=per_page, status=status
        )

        total_pages = math.ceil(total / per_page) if per_page else 1

        data = [PaginaExtraidaSummary.model_validate(p) for p in paginas]

        return SuccessListResponse(
            data=data,
            meta=PaginationMeta(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
        )

    def get_estatisticas_paginas(
        self, db: Session, execucao_id: UUID
    ) -> EstatisticasPaginas:
        """
        Obtém estatísticas de extração de páginas de uma execução.

        Args:
            db: Sessão do banco de dados
            execucao_id: UUID da execução

        Returns:
            EstatisticasPaginas

        Raises:
            NotFoundError: Se a execução não existe
        """
        execucao = self.execucao_repository.get_by_id(db, execucao_id)
        if not execucao:
            raise NotFoundError("Execucao", str(execucao_id))

        contagem = self.repository.count_by_status(db, execucao_id)
        total = sum(contagem.values())
        sucesso = contagem.get(PaginaStatus.SUCESSO, 0)
        falhou = contagem.get(PaginaStatus.FALHOU, 0)
        ignorado = contagem.get(PaginaStatus.IGNORADO, 0)

        taxa_sucesso = (sucesso / total * 100) if total > 0 else 0.0
        tamanho_total = self.repository.sum_tamanho_bytes(db, execucao_id)

        # Tamanho médio, maior, menor
        if total > 0:
            tamanho_medio = tamanho_total / total

            from toninho.models.pagina_extraida import PaginaExtraida as PaginaModel

            stmt_max = select(func.max(PaginaModel.tamanho_bytes)).where(
                PaginaModel.execucao_id == execucao_id
            )
            maior_pagina = db.execute(stmt_max).scalar() or 0

            stmt_min = select(func.min(PaginaModel.tamanho_bytes)).where(
                PaginaModel.execucao_id == execucao_id
            )
            menor_pagina = db.execute(stmt_min).scalar() or 0
        else:
            tamanho_medio = 0.0
            maior_pagina = 0
            menor_pagina = 0

        return EstatisticasPaginas(
            execucao_id=execucao_id,
            total=total,
            sucesso=sucesso,
            falhou=falhou,
            ignorado=ignorado,
            taxa_sucesso=round(taxa_sucesso, 2),
            tamanho_total_bytes=tamanho_total,
            tamanho_medio_bytes=round(tamanho_medio, 2),
            maior_pagina_bytes=maior_pagina,
            menor_pagina_bytes=menor_pagina,
        )

    def download_pagina(
        self, db: Session, pagina_id: UUID
    ) -> Tuple[bytes, str, str]:
        """
        Retorna o conteúdo do arquivo de uma página extraída.

        Args:
            db: Sessão do banco de dados
            pagina_id: UUID da página

        Returns:
            Tupla (conteúdo bytes, content_type, filename)

        Raises:
            NotFoundError: Se a página não existe
            FileNotFoundError: Se o arquivo não existe no filesystem
        """
        pagina = self.repository.get_by_id(db, pagina_id)
        if not pagina:
            raise NotFoundError("PaginaExtraida", str(pagina_id))

        filepath = Path(pagina.caminho_arquivo)
        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {pagina.caminho_arquivo}")

        with open(filepath, "rb") as f:
            conteudo = f.read()

        content_type = "text/markdown"
        filename = filepath.name

        return conteudo, content_type, filename

    def delete_pagina(self, db: Session, pagina_id: UUID) -> bool:
        """
        Deleta uma página extraída (metadados + arquivo do filesystem).

        Args:
            db: Sessão do banco de dados
            pagina_id: UUID da página

        Returns:
            True se deletado com sucesso

        Raises:
            NotFoundError: Se a página não existe
        """
        pagina = self.repository.get_by_id(db, pagina_id)
        if not pagina:
            raise NotFoundError("PaginaExtraida", str(pagina_id))

        # Deletar arquivo do filesystem (best-effort)
        filepath = Path(pagina.caminho_arquivo)
        if filepath.exists():
            filepath.unlink()

        # Deletar registro do banco
        db.delete(pagina)
        db.commit()
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _atualizar_metricas_execucao(
        self,
        db: Session,
        execucao: Execucao,
        paginas_novas: List[PaginaExtraida],
    ) -> None:
        """
        Atualiza métricas da execução após inserção de páginas.

        Args:
            db: Sessão do banco de dados
            execucao: Instância da execução
            paginas_novas: Páginas recém inseridas
        """
        bytes_novos = sum(p.tamanho_bytes for p in paginas_novas)
        execucao.paginas_processadas = (execucao.paginas_processadas or 0) + len(paginas_novas)
        execucao.bytes_extraidos = (execucao.bytes_extraidos or 0) + bytes_novos

        # Recalcular taxa de erro com base no status atual
        falhas = sum(1 for p in paginas_novas if p.status == PaginaStatus.FALHOU)
        total_processadas = execucao.paginas_processadas
        if total_processadas > 0:
            # Calcular taxa de erro total reconsultando banco
            contagem = self.repository.count_by_status(db, execucao.id)
            total = sum(contagem.values())
            erros = contagem.get(PaginaStatus.FALHOU, 0)
            execucao.taxa_erro = round((erros / total * 100) if total > 0 else 0.0, 2)

        db.commit()
