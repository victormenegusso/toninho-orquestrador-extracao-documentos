"""
Extrator baseado em IBM Docling.

Converte HTML (estático ou pré-renderizado) para Markdown estruturado
via Docling, preservando hierarquia semântica, tabelas e metadados.

Limitations:
    - Não suporta SPAs (renderização via JavaScript) nativamente.
      Quando use_browser=True, o Playwright pré-renderiza o HTML e
      este módulo converte o resultado. Qualidade pode variar.
"""

import asyncio
import tempfile
from datetime import UTC, datetime

from docling.document_converter import DocumentConverter
from loguru import logger

from toninho.extraction.storage import StorageInterface
from toninho.extraction.utils import sanitize_filename


class DoclingPageExtractor:
    """Extrai e converte páginas HTML para Markdown usando IBM Docling."""

    def __init__(self, storage: StorageInterface) -> None:
        """
        Inicializa o extrator.

        Args:
            storage: Interface de armazenamento para salvar os arquivos .md.

        Raises:
            ModuleNotFoundError: Se docling não estiver instalado.
        """
        self.storage = storage
        self._converter = DocumentConverter()

    async def extract(self, url: str, output_path: str | None = None) -> dict:
        """
        Converte uma URL em Markdown via Docling e salva no storage.

        O Docling realiza seu próprio fetch HTTP interno. Usar este método
        quando use_browser=False — o Docling acessa a URL diretamente.

        Args:
            url: URL pública a converter.
            output_path: Caminho relativo de saída. Gerado a partir da URL se None.

        Returns:
            Dict com keys:
                status (str): "sucesso" | "erro"
                url (str): URL de origem
                path (str | None): caminho do arquivo salvo
                bytes (int): tamanho em bytes
                title (str): título extraído do h1
                from_cache (bool): sempre False (Docling não usa cache interno)
                error (str | None): mensagem de erro, se houver
        """
        if output_path is None:
            output_path = sanitize_filename(url)

        logger.info(f"[docling] Convertendo: {url}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert_url, url)

            now = datetime.now(UTC).isoformat()
            final_content = self._build_with_frontmatter(
                content=result["markdown"],
                url=url,
                title=result["title"],
                extracted_at=now,
            )
            content_bytes = final_content.encode("utf-8")
            saved_path = await self.storage.save_file(output_path, content_bytes)

            logger.info(
                f"[docling] Salvo em: {saved_path} ({len(content_bytes)} bytes)"
            )

            return {
                "status": "sucesso",
                "url": url,
                "path": saved_path,
                "bytes": len(content_bytes),
                "title": result["title"],
                "from_cache": False,
                "error": None,
            }

        except Exception as exc:
            logger.error(f"[docling] Erro ao converter {url}: {exc}")
            return {
                "status": "erro",
                "url": url,
                "path": None,
                "bytes": 0,
                "title": "",
                "from_cache": False,
                "error": str(exc),
            }

    async def extract_from_html(
        self, html_content: bytes, url: str, output_path: str | None = None
    ) -> dict:
        """
        Converte HTML já obtido (ex: pré-renderizado via Playwright) usando Docling.

        Escreve o HTML em arquivo temporário e o entrega ao Docling.
        Usado quando use_browser=True: Playwright pré-renderiza, Docling converte.

        Args:
            html_content: Conteúdo HTML em bytes.
            url: URL de origem (usada nos metadados do frontmatter).
            output_path: Caminho relativo de saída.

        Returns:
            Mesmo formato de `extract()`.
        """
        if output_path is None:
            output_path = sanitize_filename(url)

        logger.info(f"[docling] Convertendo HTML pré-renderizado: {url}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert_html_bytes, html_content, url
            )

            now = datetime.now(UTC).isoformat()
            final_content = self._build_with_frontmatter(
                content=result["markdown"],
                url=url,
                title=result["title"],
                extracted_at=now,
            )
            content_bytes = final_content.encode("utf-8")
            saved_path = await self.storage.save_file(output_path, content_bytes)

            logger.info(
                f"[docling] Salvo em: {saved_path} ({len(content_bytes)} bytes)"
            )

            return {
                "status": "sucesso",
                "url": url,
                "path": saved_path,
                "bytes": len(content_bytes),
                "title": result["title"],
                "from_cache": False,
                "error": None,
            }

        except Exception as exc:
            logger.error(f"[docling] Erro ao converter HTML de {url}: {exc}")
            return {
                "status": "erro",
                "url": url,
                "path": None,
                "bytes": 0,
                "title": "",
                "from_cache": False,
                "error": str(exc),
            }

    async def close(self) -> None:
        """Compatibilidade de interface com PageExtractor. Sem recursos a liberar."""
        pass

    # ──────────────────────────────────────────── helpers síncronos ────────────
    # Executados em thread pool via run_in_executor para não bloquear o event loop.

    def _convert_url(self, url: str) -> dict:
        """Chama Docling passando a URL diretamente (Docling faz o fetch)."""
        result = self._converter.convert(url)
        markdown = result.document.export_to_markdown()
        title = self._extract_title_from_markdown(markdown)
        return {"markdown": markdown, "title": title}

    def _convert_html_bytes(self, html_content: bytes, url: str) -> dict:
        """
        Salva HTML em arquivo temporário e entrega ao Docling.

        O arquivo é removido automaticamente ao sair do bloco with.
        """
        with tempfile.NamedTemporaryFile(suffix=".html", delete=True) as tmp:
            tmp.write(html_content)
            tmp.flush()
            result = self._converter.convert(tmp.name)

        markdown = result.document.export_to_markdown()
        title = self._extract_title_from_markdown(markdown)
        return {"markdown": markdown, "title": title}

    @staticmethod
    def _extract_title_from_markdown(markdown: str) -> str:
        """Extrai o título do primeiro h1 do Markdown gerado pelo Docling."""
        for line in markdown.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    @staticmethod
    def _build_with_frontmatter(
        content: str, url: str, title: str, extracted_at: str
    ) -> str:
        """
        Adiciona frontmatter YAML ao Markdown.

        Mantém o mesmo formato do html2text (`extrator` difere para rastreabilidade).
        """
        frontmatter = [
            "---",
            f"url: {url}",
            f'titulo: "{title}"',
            f"extraido_em: {extracted_at}",
            "extrator: Toninho/Docling v1.0",
            "---",
            "",
        ]
        return "\n".join(frontmatter) + content
