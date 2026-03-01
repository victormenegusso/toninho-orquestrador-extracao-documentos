"""
Cliente HTTP com retry, timeout e cache in-memory.

Responsável por buscar conteúdo de URLs de forma resiliente,
com backoff exponencial e cache simples para evitar requests duplicados.
"""

import asyncio
from typing import Dict, Optional

import httpx
from loguru import logger


class HTTPClient:
    """Cliente HTTP com retry, timeout e cache in-memory."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_enabled: bool = True,
        user_agent: str = "Toninho/1.0",
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, bytes] = {}

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
