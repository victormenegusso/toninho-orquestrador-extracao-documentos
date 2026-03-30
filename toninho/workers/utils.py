"""
Orquestrador de extração para uso nos workers Celery.

ExtractionOrchestrator coordena a extração de múltiplas URLs,
registrando logs, páginas extraídas e métricas da execução.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from toninho.extraction.extractor import PageExtractor
from toninho.extraction.storage import StorageInterface, get_storage
from toninho.extraction.utils import build_output_path
from toninho.models.enums import (
    ExecucaoStatus,
    FormatoSaida,
    LogNivel,
    MetodoExtracao,
    PaginaStatus,
)


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

    def run(self, execucao_id: uuid.UUID) -> dict:
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
        from toninho.models.pagina_extraida import PaginaExtraida

        db = self.db

        # 1. Buscar execução
        execucao = db.get(Execucao, execucao_id)
        if not execucao:
            raise ValueError(f"Execucao não encontrada: {execucao_id}")

        # 2. Atualizar status → EM_EXECUCAO
        execucao.status = ExecucaoStatus.EM_EXECUCAO
        execucao.iniciado_em = datetime.now(UTC)
        db.commit()

        # 3. Buscar configuração mais recente do processo
        configuracao = (
            db.query(Configuracao)
            .filter(Configuracao.processo_id == execucao.processo_id)
            .options(joinedload(Configuracao.volume))
            .order_by(Configuracao.created_at.desc())
            .first()
        )

        if configuracao is None:
            # Registrar erro e encerrar
            self._add_log(
                db, execucao_id, LogNivel.ERROR, "Processo sem configuração de extração"
            )
            execucao.status = ExecucaoStatus.FALHOU
            execucao.finalizado_em = datetime.now(UTC)
            db.commit()
            return {
                "status": ExecucaoStatus.FALHOU,
                "paginas_sucesso": 0,
                "paginas_falha": 0,
                "total": 0,
                "bytes_extraidos": 0,
            }

        urls = configuracao.urls or []
        total = len(urls)
        sucesso = 0
        falha = 0
        bytes_total = 0

        # 4. Preparar storage
        volume_path = configuracao.volume.path if configuracao.volume else "./output"
        storage = self.storage or get_storage(
            "local",
            base_dir=volume_path,
        )

        # 4b. Preparar extractor com modo browser se configurado
        use_browser = getattr(configuracao, "use_browser", False)
        metodo_extracao = getattr(
            configuracao, "metodo_extracao", MetodoExtracao.HTML2TEXT
        )
        respect_robots_txt = getattr(configuracao, "respect_robots_txt", False)

        # 5. Log inicial
        self._add_log(
            db,
            execucao_id,
            LogNivel.INFO,
            f"Iniciando extração de {total} URLs com motor={metodo_extracao.value}",
            contexto={
                "total_urls": total,
                "urls": urls,
                "metodo_extracao": metodo_extracao.value,
            },
        )

        # 6. Extrair cada URL
        for idx, url in enumerate(urls, 1):
            self._add_log(
                db,
                execucao_id,
                LogNivel.INFO,
                f"[{idx}/{total}] Extraindo: {url}",
                contexto={"url": url, "indice": idx, "total": total},
            )

            output_path = build_output_path(
                str(execucao.processo_id),
                str(execucao_id),
                url,
            )

            resultado = asyncio.run(
                self._extract_url(
                    storage,
                    url,
                    output_path,
                    use_browser=use_browser,
                    metodo_extracao=metodo_extracao,
                    respect_robots_txt=respect_robots_txt,
                )
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
                    db,
                    execucao_id,
                    LogNivel.ERROR,
                    f"Erro ao extrair {url}: {erro_msg}",
                    contexto={"url": url, "indice": idx, "erro": erro_msg},
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

        # 6b. Consolidar em arquivo único se configurado
        if configuracao.formato_saida == FormatoSaida.ARQUIVO_UNICO and sucesso > 0:
            self._consolidate_files(
                db=db,
                storage=storage,
                execucao_id=execucao_id,
                processo_id=str(execucao.processo_id),
            )

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
        execucao.finalizado_em = datetime.now(UTC)
        db.commit()

        self._add_log(
            db,
            execucao_id,
            LogNivel.INFO,
            f"Extração finalizada: {sucesso} sucesso, {falha} falhas — status={status_final.value}",
            contexto={
                "status": status_final.value,
                "paginas_sucesso": sucesso,
                "paginas_falha": falha,
                "total": total,
                "bytes_extraidos": bytes_total,
            },
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

    def _consolidate_files(
        self,
        db: Session,
        storage: StorageInterface,
        execucao_id: uuid.UUID,
        processo_id: str,
    ) -> str | None:
        """
        Consolida arquivos extraídos com sucesso em um único markdown.

        Lê cada arquivo individual, concatena com separadores e salva
        como resultado_completo.md.

        Returns:
            Caminho do arquivo consolidado, ou None se nada consolidado.
        """
        from toninho.models.pagina_extraida import PaginaExtraida

        paginas = (
            db.query(PaginaExtraida)
            .filter(
                PaginaExtraida.execucao_id == execucao_id,
                PaginaExtraida.status == PaginaStatus.SUCESSO,
            )
            .order_by(PaginaExtraida.timestamp)
            .all()
        )

        if not paginas:
            return None

        parts: list[str] = []
        for pagina in paginas:
            relative_path = build_output_path(
                processo_id, str(execucao_id), pagina.url_original
            )
            try:
                content_bytes = asyncio.run(storage.get_file(relative_path))
                text = content_bytes.decode("utf-8", errors="replace")
                parts.append(f"---\n\n# URL: {pagina.url_original}\n\n{text}")
            except FileNotFoundError:
                self._add_log(
                    db,
                    execucao_id,
                    LogNivel.WARNING,
                    f"Arquivo não encontrado ao consolidar: {relative_path}",
                    contexto={"caminho": relative_path},
                )
                continue

        if not parts:
            return None

        consolidated_content = "\n\n".join(parts)
        output_path = f"{processo_id}/{execucao_id}/resultado_completo.md"

        saved_path = asyncio.run(
            storage.save_file(output_path, consolidated_content.encode("utf-8"))
        )

        self._add_log(
            db,
            execucao_id,
            LogNivel.INFO,
            f"Arquivo único consolidado: {output_path} ({len(parts)} páginas)",
            contexto={
                "caminho": output_path,
                "paginas_consolidadas": len(parts),
                "tamanho_bytes": len(consolidated_content.encode("utf-8")),
            },
        )
        db.flush()

        return saved_path

    @staticmethod
    async def _extract_url(
        storage: StorageInterface,
        url: str,
        output_path: str,
        use_browser: bool = False,
        metodo_extracao: MetodoExtracao = MetodoExtracao.HTML2TEXT,
        respect_robots_txt: bool = False,
    ) -> dict:
        """Executa extração async de uma URL, escolhendo o motor correto.

        Args:
            storage: Interface de armazenamento.
            url: URL a extrair.
            output_path: Caminho relativo de saída.
            use_browser: Se True, usa Playwright para pré-renderizar (ambos os motores).
            metodo_extracao: Motor de conversão HTML→Markdown.
            respect_robots_txt: Se True, verifica robots.txt antes de extrair.

        Returns:
            Dict com status, url, path, bytes, title, from_cache, error.
        """
        if metodo_extracao == MetodoExtracao.DOCLING:
            from toninho.extraction.docling_extractor import DoclingPageExtractor

            extractor = DoclingPageExtractor(storage)

            if use_browser:
                # Playwright pré-renderiza → HTML bytes → Docling converte
                from toninho.extraction.browser_client import BrowserClient

                browser = BrowserClient(timeout=60_000)
                await browser.start()
                try:
                    response = await browser.get(url)
                finally:
                    await browser.close()
                return await extractor.extract_from_html(
                    response["content"], url, output_path
                )
            else:
                # Docling faz o fetch HTTP interno
                return await extractor.extract(url, output_path)

        else:
            # Método padrão: PageExtractor (httpx + html2text)
            extractor_h2t = PageExtractor(
                storage,
                timeout=60,
                max_retries=3,
                use_browser=use_browser,
                respect_robots_txt=respect_robots_txt,
            )
            try:
                return await extractor_h2t.extract(url, output_path)
            finally:
                await extractor_h2t.close()

    @staticmethod
    def _add_log(
        db: Session,
        execucao_id: uuid.UUID,
        nivel: LogNivel,
        mensagem: str,
        contexto: dict | None = None,
    ) -> None:
        """Adiciona log à execução no banco."""
        from toninho.models.log import Log

        log = Log(
            execucao_id=execucao_id,
            nivel=nivel,
            mensagem=mensagem,
            contexto=contexto,
        )
        db.add(log)
        db.flush()
