"""
Cliente HTTP com retry, timeout, cache in-memory e rate limiting.

Responsável por buscar conteúdo de URLs de forma resiliente,
com backoff exponencial, cache simples e controle de taxa por domínio.
"""

import asyncio
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from loguru import logger


class RobotsChecker:
    """Verifica permissões do robots.txt por domínio, com cache."""

    def __init__(self, user_agent: str, timeout: int = 10):
        self._user_agent = user_agent
        self._timeout = timeout
        self._parsers: dict[str, RobotFileParser | None] = {}

    async def is_allowed(self, url: str) -> bool:
        """Retorna True se a URL é permitida pelo robots.txt do domínio."""
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        if origin not in self._parsers:
            await self._fetch_robots(origin)

        parser = self._parsers.get(origin)
        if parser is None:
            return True  # Se não conseguiu ler robots.txt, permite

        return parser.can_fetch(self._user_agent, url)

    async def _fetch_robots(self, origin: str) -> None:
        """Busca e parseia o robots.txt de um domínio."""
        robots_url = f"{origin}/robots.txt"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(robots_url, follow_redirects=True)
                if response.status_code == 200:
                    parser = RobotFileParser()
                    parser.parse(response.text.splitlines())
                    self._parsers[origin] = parser
                    logger.debug(f"robots.txt carregado: {robots_url}")
                else:
                    self._parsers[origin] = None
                    logger.debug(
                        f"robots.txt não encontrado ({response.status_code}): {robots_url}"
                    )
        except Exception as exc:
            self._parsers[origin] = None
            logger.debug(f"Erro ao buscar robots.txt de {origin}: {exc}")


class HTTPClient:
    """Cliente HTTP com retry, timeout, cache in-memory e rate limiting por domínio."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_enabled: bool = True,
        user_agent: str = "Toninho/1.0",
        delay_between_requests: float = 0.0,
        respect_robots_txt: bool = False,
    ):
        """
        Inicializa o cliente HTTP.

        Args:
            timeout: Timeout em segundos para cada requisição
            max_retries: Número máximo de tentativas
            cache_enabled: Se True, usa cache in-memory para evitar requests duplicados
            user_agent: User-Agent enviado nas requisições
            delay_between_requests: Delay mínimo em segundos entre requisições
                ao mesmo domínio. Use 1.0 para 1 req/s, 0.0 para sem limite.
            respect_robots_txt: Se True, verifica robots.txt antes de cada request
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.delay_between_requests = delay_between_requests
        self._cache: dict[str, bytes] = {}
        self._last_request_time: dict[str, float] = {}  # domínio -> timestamp
        self._robots: RobotsChecker | None = None
        if respect_robots_txt:
            self._robots = RobotsChecker(user_agent=user_agent, timeout=timeout)

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )

    async def get(self, url: str) -> dict:
        """
        Executa GET request com retry e cache.

        Args:
            url: URL a buscar

        Returns:
            Dict com keys: content (bytes), status_code (int),
                           headers (dict), from_cache (bool)

        Raises:
            httpx.HTTPStatusError: Em erros 4xx/5xx não recuperáveis
            httpx.TimeoutException: Após esgotar retries por timeout
            httpx.ConnectError: Após esgotar retries por falha de conexão
        """
        # Verificar robots.txt
        if self._robots and not await self._robots.is_allowed(url):
            logger.info(f"Bloqueado por robots.txt: {url}")
            raise PermissionError(f"URL bloqueada pelo robots.txt: {url}")

        # Verificar cache
        if self.cache_enabled and url in self._cache:
            logger.debug(f"Cache hit: {url}")
            return {
                "content": self._cache[url],
                "status_code": 200,
                "headers": {},
                "from_cache": True,
            }

        # Rate limiting por domínio
        if self.delay_between_requests > 0:
            await self._apply_rate_limit(url)

        last_exc: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.get(url)
                response.raise_for_status()

                content = response.content

                # Armazenar em cache
                if self.cache_enabled and response.status_code == 200:
                    self._cache[url] = content

                return {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "from_cache": False,
                }

            except httpx.HTTPStatusError as exc:
                # Não fazer retry em erros de autenticação/cliente
                if exc.response.status_code in (401, 403, 404):
                    raise
                last_exc = exc
                logger.warning(
                    f"HTTP {exc.response.status_code} na tentativa "
                    f"{attempt + 1}/{self.max_retries}: {url}"
                )

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = exc
                logger.warning(
                    f"Erro de rede na tentativa "
                    f"{attempt + 1}/{self.max_retries}: {url} — {exc}"
                )

            # Backoff exponencial entre retries (1s, 2s, 4s…)
            if attempt < self.max_retries - 1:
                wait = 2**attempt
                logger.debug(f"Aguardando {wait}s antes da próxima tentativa…")
                await asyncio.sleep(wait)

        raise last_exc or Exception(
            f"Falha ao buscar {url} após {self.max_retries} tentativas"
        )

    async def _apply_rate_limit(self, url: str) -> None:
        """
        Aplica rate limiting por domínio.

        Garante que o intervalo mínimo entre requisições ao mesmo
        domínio seja respeitado.

        Args:
            url: URL alvo (domínio é extraído automaticamente)
        """
        import time

        domain = urlparse(url).netloc
        last_time = self._last_request_time.get(domain, 0.0)
        elapsed = time.monotonic() - last_time
        remaining = self.delay_between_requests - elapsed

        if remaining > 0:
            logger.debug(
                f"Rate limit: aguardando {remaining:.2f}s antes de acessar {domain}"
            )
            await asyncio.sleep(remaining)

        self._last_request_time[domain] = time.monotonic()

    def clear_cache(self) -> None:
        """Limpa o cache in-memory."""
        self._cache.clear()

    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        await self._client.aclose()

    async def __aenter__(self) -> "HTTPClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
