"""
Extrator principal de páginas web.

Orquestra o fluxo de extração: HTTP fetch → parse HTML →
converter markdown → adicionar metadados → salvar no storage.

Suporta dois modos de extração:
- HTTP simples via httpx (padrão, rápido, sem JS)
- Navegador headless via Playwright (use_browser=True, suporta SPAs)
"""

from datetime import UTC, datetime

from loguru import logger

from toninho.extraction.http_client import HTTPClient
from toninho.extraction.markdown_converter import (
    build_markdown_with_metadata,
    extract_from_html,
)
from toninho.extraction.storage import StorageInterface
from toninho.extraction.utils import sanitize_filename


class PageExtractor:
    """Extrai páginas web e salva como markdown no storage."""

    def __init__(
        self,
        storage: StorageInterface,
        timeout: int = 30,
        max_retries: int = 3,
        cache_enabled: bool = True,
        user_agent: str = "Toninho/1.0",
        use_browser: bool = False,
        browser_wait_for: str = "networkidle",
        respect_robots_txt: bool = False,
    ):
        """
        Inicializa o extrator.

        Args:
            storage: Interface de armazenamento
            timeout: Timeout em segundos para requisições
            max_retries: Número máximo de tentativas (somente modo HTTP)
            cache_enabled: Habilitar cache in-memory (somente modo HTTP)
            user_agent: User-Agent enviado nas requisições
            use_browser: Se True, usa Playwright para renderizar JS/SPAs.
                Requer `playwright` instalado e `playwright install chromium`.
            browser_wait_for: Evento Playwright a aguardar antes de capturar HTML.
                Opções: "load", "domcontentloaded", "networkidle" (padrão), "commit".
            respect_robots_txt: Se True, verifica robots.txt antes de extrair cada URL.
        """
        self.storage = storage
        self.use_browser = use_browser
        self._http = HTTPClient(
            timeout=timeout,
            max_retries=max_retries,
            cache_enabled=cache_enabled,
            user_agent=user_agent,
            respect_robots_txt=respect_robots_txt,
        )
        self._browser_client = None
        if use_browser:
            from toninho.extraction.browser_client import BrowserClient

            self._browser_client = BrowserClient(
                timeout=timeout * 1000,  # Playwright usa milissegundos
                wait_for=browser_wait_for,
            )

    async def extract(self, url: str, output_path: str | None = None) -> dict:
        """
        Extrai uma URL e salva como markdown.

        Args:
            url: URL a extrair
            output_path: Caminho relativo de saída. Se None, gera a partir da URL.

        Returns:
            Dict com keys:
                status (str): "sucesso" | "erro"
                url (str)
                path (str | None): caminho do arquivo salvo
                bytes (int): tamanho em bytes
                title (str)
                from_cache (bool)
                error (str | None): mensagem de erro, se houver
        """
        if output_path is None:
            output_path = sanitize_filename(url)

        logger.info(f"Extraindo: {url}")
        if self.use_browser:
            logger.debug(f"[browser mode] Renderizando JS: {url}")

        try:
            # 1. Buscar HTML (HTTP ou browser)
            if self.use_browser and self._browser_client:
                if self._browser_client._browser is None:
                    await self._browser_client.start()
                response = await self._browser_client.get(url)
            else:
                response = await self._http.get(url)
            html_content: bytes = response["content"]

            # 2. Extrair título e markdown
            extracted = extract_from_html(html_content, base_url=url)

            # 3. Montar timestamp
            now = datetime.now(UTC)
            extracted_at = now.isoformat()

            # 4. Adicionar metadados (frontmatter)
            final_content = build_markdown_with_metadata(
                content=extracted["markdown"],
                url=url,
                title=extracted["title"],
                extracted_at=extracted_at,
            )

            content_bytes = final_content.encode("utf-8")

            # 5. Salvar no storage
            saved_path = await self.storage.save_file(output_path, content_bytes)

            logger.info(f"Salvo em: {saved_path} ({len(content_bytes)} bytes)")

            return {
                "status": "sucesso",
                "url": url,
                "path": saved_path,
                "bytes": len(content_bytes),
                "title": extracted["title"],
                "from_cache": response.get("from_cache", False),
                "error": None,
            }

        except Exception as exc:
            logger.error(f"Erro ao extrair {url}: {exc}")
            return {
                "status": "erro",
                "url": url,
                "path": None,
                "bytes": 0,
                "title": "",
                "from_cache": False,
                "error": str(exc),
            }

    def generate_filename(self, url: str) -> str:
        """Gera nome de arquivo seguro a partir de uma URL."""
        return sanitize_filename(url)

    async def close(self) -> None:
        """Fecha recursos internos (HTTP client e/ou navegador)."""
        await self._http.close()
        if self._browser_client:
            await self._browser_client.close()

    async def __aenter__(self) -> "PageExtractor":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
