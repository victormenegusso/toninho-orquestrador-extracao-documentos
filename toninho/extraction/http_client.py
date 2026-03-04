"""
Cliente HTTP com retry, timeout, cache in-memory e rate limiting.

Responsável por buscar conteúdo de URLs de forma resiliente,
com backoff exponencial, cache simples e controle de taxa por domínio.
"""

import asyncio
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger


class HTTPClient:
    """Cliente HTTP com retry, timeout, cache in-memory e rate limiting por domínio."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_enabled: bool = True,
        user_agent: str = "Toninho/1.0",
        delay_between_requests: float = 0.0,
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
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.delay_between_requests = delay_between_requests
        self._cache: Dict[str, bytes] = {}
        self._last_request_time: Dict[str, float] = {}  # domínio -> timestamp

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )

    async def get(self, url: str) -> Dict:
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

        last_exc: Optional[Exception] = None

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
            logger.debug(f"Rate limit: aguardando {remaining:.2f}s antes de acessar {domain}")
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
