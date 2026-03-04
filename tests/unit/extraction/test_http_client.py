"""
Testes unitários para o HTTPClient.
"""

import httpx
import pytest

from toninho.extraction.http_client import HTTPClient

SAMPLE_URL = "https://example.com/page"
SAMPLE_HTML = b"<html><body><h1>Test</h1></body></html>"


class TestHTTPClientGetSuccess:
    """Testes de sucesso do método get()."""

    @pytest.mark.asyncio
    async def test_get_success_returns_content(self, respx_mock):
        """get() deve retornar conteúdo e status 200."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(200, content=SAMPLE_HTML)
        )

        async with HTTPClient(cache_enabled=False) as client:
            result = await client.get(SAMPLE_URL)

        assert result["content"] == SAMPLE_HTML
        assert result["status_code"] == 200
        assert result["from_cache"] is False

    @pytest.mark.asyncio
    async def test_get_caches_response(self, respx_mock):
        """Segundo get() para a mesma URL deve vir do cache."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(200, content=SAMPLE_HTML)
        )

        async with HTTPClient(cache_enabled=True) as client:
            first = await client.get(SAMPLE_URL)
            second = await client.get(SAMPLE_URL)

        assert first["from_cache"] is False
        assert second["from_cache"] is True
        assert second["content"] == SAMPLE_HTML

    @pytest.mark.asyncio
    async def test_get_no_cache_disabled(self, respx_mock):
        """Com cache_enabled=False, nunca usa cache."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(200, content=SAMPLE_HTML)
        )

        async with HTTPClient(cache_enabled=False) as client:
            first = await client.get(SAMPLE_URL)
            # Segunda chamada deve também fazer request
            respx_mock.get(SAMPLE_URL).mock(
                return_value=httpx.Response(200, content=b"new content")
            )
            second = await client.get(SAMPLE_URL)

        assert first["from_cache"] is False
        assert second["from_cache"] is False

    @pytest.mark.asyncio
    async def test_get_returns_headers(self, respx_mock):
        """get() deve retornar os headers da resposta."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(
                200,
                content=SAMPLE_HTML,
                headers={"content-type": "text/html"},
            )
        )

        async with HTTPClient(cache_enabled=False) as client:
            result = await client.get(SAMPLE_URL)

        assert "content-type" in result["headers"]


class TestHTTPClientErrors:
    """Testes de tratamento de erros."""

    @pytest.mark.asyncio
    async def test_404_raises_immediately(self, respx_mock):
        """404 não deve fazer retry — deve levantar imediatamente."""
        respx_mock.get(SAMPLE_URL).mock(return_value=httpx.Response(404))

        async with HTTPClient(max_retries=3, cache_enabled=False) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get(SAMPLE_URL)

        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_403_raises_immediately(self, respx_mock):
        """403 não deve fazer retry."""
        respx_mock.get(SAMPLE_URL).mock(return_value=httpx.Response(403))

        async with HTTPClient(max_retries=3, cache_enabled=False) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get(SAMPLE_URL)

        assert exc_info.value.response.status_code == 403

    @pytest.mark.asyncio
    async def test_500_retries_and_eventually_raises(self, respx_mock):
        """500 deve fazer retry e levantar após esgotar tentativas."""
        respx_mock.get(SAMPLE_URL).mock(return_value=httpx.Response(500))

        async with HTTPClient(max_retries=2, cache_enabled=False) as client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.get(SAMPLE_URL)

    @pytest.mark.asyncio
    async def test_timeout_retries_and_raises(self, respx_mock):
        """Timeout deve fazer retry e levantar após esgotar tentativas."""
        respx_mock.get(SAMPLE_URL).mock(side_effect=httpx.TimeoutException("timeout"))

        async with HTTPClient(max_retries=2, cache_enabled=False) as client:
            with pytest.raises(httpx.TimeoutException):
                await client.get(SAMPLE_URL)

    @pytest.mark.asyncio
    async def test_connect_error_retries_and_raises(self, respx_mock):
        """ConnectError deve fazer retry e levantar após esgotar tentativas."""
        respx_mock.get(SAMPLE_URL).mock(
            side_effect=httpx.ConnectError("connection refused")
        )

        async with HTTPClient(max_retries=2, cache_enabled=False) as client:
            with pytest.raises(httpx.ConnectError):
                await client.get(SAMPLE_URL)

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, respx_mock):
        """Se falhar uma vez mas succeeder na segunda, deve retornar OK."""
        call_count = {"n": 0}

        def side_effect(request):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return httpx.Response(503)
            return httpx.Response(200, content=SAMPLE_HTML)

        respx_mock.get(SAMPLE_URL).mock(side_effect=side_effect)

        async with HTTPClient(max_retries=3, cache_enabled=False) as client:
            result = await client.get(SAMPLE_URL)

        assert result["status_code"] == 200
        assert call_count["n"] == 2


class TestHTTPClientCache:
    """Testes específicos de cache."""

    @pytest.mark.asyncio
    async def test_clear_cache(self, respx_mock):
        """clear_cache deve limpar o cache."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(200, content=SAMPLE_HTML)
        )

        async with HTTPClient(cache_enabled=True) as client:
            await client.get(SAMPLE_URL)
            client.clear_cache()

            # Próxima chamada deve fazer novo request
            respx_mock.get(SAMPLE_URL).mock(
                return_value=httpx.Response(200, content=b"fresh content")
            )
            result = await client.get(SAMPLE_URL)

        assert result["from_cache"] is False
        assert result["content"] == b"fresh content"


class TestHTTPClientRateLimit:
    """Testes de rate limiting por domínio (MH-005)."""

    def test_delay_between_requests_default_zero(self):
        """delay_between_requests deve ser 0.0 por padrão (sem rate limit)."""
        client = HTTPClient()
        assert client.delay_between_requests == 0.0

    def test_delay_between_requests_configured(self):
        """delay_between_requests deve ser configurável."""
        client = HTTPClient(delay_between_requests=1.5)
        assert client.delay_between_requests == 1.5

    @pytest.mark.asyncio
    async def test_rate_limit_applies_delay(self, respx_mock):
        """Com delay configurado, segunda request ao mesmo domínio deve esperar."""
        import time

        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"

        respx_mock.get(url1).mock(return_value=httpx.Response(200, content=b"p1"))
        respx_mock.get(url2).mock(return_value=httpx.Response(200, content=b"p2"))

        delay = 0.1  # 100ms para o teste ser rápido
        async with HTTPClient(
            cache_enabled=False, delay_between_requests=delay
        ) as client:
            t0 = time.monotonic()
            await client.get(url1)
            await client.get(url2)
            elapsed = time.monotonic() - t0

        # O delay total deve ser >= delay (segunda request espera)
        assert elapsed >= delay

    @pytest.mark.asyncio
    async def test_no_rate_limit_different_domains(self, respx_mock):
        """Requests a domínios diferentes não devem aplicar delay entre si."""
        import time

        url_a = "https://domain-a.com/page"
        url_b = "https://domain-b.com/page"

        respx_mock.get(url_a).mock(return_value=httpx.Response(200, content=b"a"))
        respx_mock.get(url_b).mock(return_value=httpx.Response(200, content=b"b"))

        delay = 1.0  # 1 segundo — mas domínios diferentes, então não deve esperar
        async with HTTPClient(
            cache_enabled=False, delay_between_requests=delay
        ) as client:
            t0 = time.monotonic()
            await client.get(url_a)
            await client.get(url_b)
            elapsed = time.monotonic() - t0

        # Sem delay entre domínios diferentes — deve ser bem mais rápido que 1s
        assert elapsed < delay
