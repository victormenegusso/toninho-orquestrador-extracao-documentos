"""
Cliente de navegador para extração de páginas com JavaScript (SPAs).

Usa Playwright para renderizar páginas que dependem de JavaScript,
como SPAs Angular/React, antes de extrair o HTML resultante.

Instalação opcional:
    pip install playwright
    playwright install chromium

Se o Playwright não estiver instalado, o BrowserClient lança
ImportError com instrução de instalação.
"""

from loguru import logger


class BrowserClient:
    """
    Cliente baseado em Playwright para páginas JavaScript.

    Renderiza a página completa em um navegador headless Chromium
    antes de retornar o HTML, permitindo extrair SPAs (React, Angular, Vue).

    Args:
        timeout: Timeout em milissegundos para carregamento da página (default 30s)
        wait_for: Evento do Playwright a aguardar antes de capturar HTML.
            Opções: "load", "domcontentloaded", "networkidle", "commit".
            "networkidle" é mais seguro para SPAs mas mais lento.

    Raises:
        ImportError: Se o pacote `playwright` não estiver instalado.
    """

    def __init__(
        self,
        timeout: int = 30_000,
        wait_for: str = "networkidle",
    ):
        try:
            import playwright  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "O pacote `playwright` não está instalado. "
                "Para usar o modo browser, instale-o com:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            ) from exc

        self.timeout = timeout
        self.wait_for = wait_for
        self._browser = None
        self._playwright = None

    async def start(self) -> None:
        """Inicia o Playwright e abre o navegador."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        logger.debug("BrowserClient iniciado (Chromium headless)")

    async def close(self) -> None:
        """Fecha o navegador e encerra o Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.debug("BrowserClient encerrado")

    async def get(self, url: str) -> dict:
        """
        Busca uma URL usando o navegador Playwright.

        Navega até a URL e aguarda o evento configurado antes
        de retornar o HTML renderizado.

        Args:
            url: URL a renderizar

        Returns:
            Dict com keys: content (bytes), status_code (int),
                           headers (dict), from_cache (bool)

        Raises:
            RuntimeError: Se o BrowserClient não foi iniciado via start()
        """
        if self._browser is None:
            raise RuntimeError(
                "BrowserClient não foi iniciado. "
                "Use `await client.start()` ou o gerenciador de contexto."
            )

        logger.debug(f"[browser] Navegando: {url}")
        page = await self._browser.new_page()
        try:
            response = await page.goto(
                url,
                timeout=self.timeout,
                wait_until=self.wait_for,
            )

            html = await page.content()
            status_code = response.status if response else 200

            logger.debug(
                f"[browser] HTML capturado: {len(html)} chars — status={status_code}"
            )

            return {
                "content": html.encode("utf-8"),
                "status_code": status_code,
                "headers": dict(response.headers) if response else {},
                "from_cache": False,
            }
        finally:
            await page.close()

    async def __aenter__(self) -> "BrowserClient":
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
