"""
Orquestrador de extração para uso nos workers Celery.

ExtractionOrchestrator coordena a extração de múltiplas URLs,
registrando logs, páginas extraídas e métricas da execução.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict

from loguru import logger
from sqlalchemy.orm import Session

from toninho.extraction.extractor import PageExtractor
from toninho.extraction.storage import StorageInterface, get_storage
from toninho.extraction.utils import build_output_path
from toninho.models.enums import ExecucaoStatus, LogNivel, PaginaStatus


class ExtractionOrchestrator:
    """
    Orquestra a extração de múltiplas URLs para uma execução.

    Responsável por:
    - Buscar execução e configuração no banco
    - Iterar sobre URLs e extrair cada uma
    - Registrar PaginaExtraida e Log no banco
    - Atualizar métricas e status final da execução
    """

    def __init__(self, db: Session, storage: StorageInterface | None = None):
        self.db = db
        self.storage = storage

    def run(self, execucao_id: uuid.UUID) -> Dict:
        """
        Executa a extração completa para a execucao indicada.

        Args:
            execucao_id: UUID da execução a processar

        Returns:
            Dict com resultado da execução:
                status (ExecucaoStatus)
                paginas_sucesso (int)
                paginas_falha (int)
                total (int)
                bytes_extraidos (int)
        """
        from toninho.models.configuracao import Configuracao
        from toninho.models.execucao import Execucao
        from toninho.models.log import Log
        from toninho.models.pagina_extraida import PaginaExtraida

        db = self.db

        # 1. Buscar execução
        execucao = db.get(Execucao, execucao_id)
        if not execucao:
            raise ValueError(f"Execucao não encontrada: {execucao_id}")

        # 2. Atualizar status → EM_EXECUCAO
        execucao.status = ExecucaoStatus.EM_EXECUCAO
        execucao.iniciado_em = datetime.now(timezone.utc)
        db.commit()

        # 3. Buscar configuração mais recente do processo
        configuracao = (
            db.query(Configuracao)
            .filter(Configuracao.processo_id == execucao.processo_id)
            .order_by(Configuracao.created_at.desc())
            .first()
        )

        if configuracao is None:
            # Registrar erro e encerrar
            self._add_log(db, execucao_id, LogNivel.ERROR, "Processo sem configuração de extração")
            execucao.status = ExecucaoStatus.FALHOU
            execucao.finalizado_em = datetime.now(timezone.utc)
            db.commit()
            return {"status": ExecucaoStatus.FALHOU, "paginas_sucesso": 0, "paginas_falha": 0, "total": 0, "bytes_extraidos": 0}

        urls = configuracao.urls or []
        total = len(urls)
        sucesso = 0
        falha = 0
        bytes_total = 0

        # 4. Preparar storage
        storage = self.storage or get_storage(
            "local",
            base_dir=configuracao.output_dir or "./output",
        )

        # 5. Log inicial
        self._add_log(db, execucao_id, LogNivel.INFO, f"Iniciando extração de {total} URLs")

        # 6. Extrair cada URL
        for idx, url in enumerate(urls, 1):
            self._add_log(db, execucao_id, LogNivel.INFO, f"[{idx}/{total}] Extraindo: {url}")

            output_path = build_output_path(
                str(execucao.processo_id),
                str(execucao_id),
                url,
            )

            resultado = asyncio.run(
                self._extract_url(storage, url, output_path)
            )

            if resultado["status"] == "sucesso":
                sucesso += 1
                bytes_total += resultado["bytes"]
                status_pagina = PaginaStatus.SUCESSO
                erro_msg = None
                caminho = resultado["path"] or output_path
            else:
                falha += 1
                status_pagina = PaginaStatus.FALHOU
                erro_msg = resultado.get("error")
                caminho = output_path
                self._add_log(
                    db, execucao_id, LogNivel.ERROR,
                    f"Erro ao extrair {url}: {erro_msg}"
                )

            # Registrar PaginaExtraida
            pagina = PaginaExtraida(
                execucao_id=execucao_id,
                url_original=url,
                caminho_arquivo=caminho,
                status=status_pagina,
                tamanho_bytes=resultado["bytes"],
                erro_mensagem=erro_msg,
            )
            db.add(pagina)

            # Atualizar métricas parciais
            execucao.paginas_processadas = sucesso + falha
            execucao.bytes_extraidos = bytes_total

            db.commit()

        # 7. Calcular taxa de erro e status final
        if total > 0:
            execucao.taxa_erro = round((falha / total) * 100, 2)

        if falha == 0:
            status_final = ExecucaoStatus.CONCLUIDO
        elif sucesso > 0:
            status_final = ExecucaoStatus.CONCLUIDO_COM_ERROS
        else:
            status_final = ExecucaoStatus.FALHOU

        execucao.status = status_final
        execucao.finalizado_em = datetime.now(timezone.utc)
        db.commit()

        self._add_log(
            db, execucao_id, LogNivel.INFO,
            f"Extração finalizada: {sucesso} sucesso, {falha} falhas — status={status_final.value}"
        )
        db.commit()

        return {
            "status": status_final,
            "paginas_sucesso": sucesso,
            "paginas_falha": falha,
            "total": total,
            "bytes_extraidos": bytes_total,
        }

    # ──────────────────────────────────────────────── helpers ────────────

    @staticmethod
    async def _extract_url(storage: StorageInterface, url: str, output_path: str) -> Dict:
        """Executa extração async de uma URL."""
        extractor = PageExtractor(storage, timeout=60, max_retries=3)
        try:
            return await extractor.extract(url, output_path)
        finally:
            await extractor.close()

    @staticmethod
    def _add_log(db: Session, execucao_id: uuid.UUID, nivel: LogNivel, mensagem: str) -> None:
        """Adiciona log à execução no banco."""
        from toninho.models.log import Log
        log = Log(
            execucao_id=execucao_id,
            nivel=nivel,
            mensagem=mensagem,
        )
        db.add(log)
        db.flush()
