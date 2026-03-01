"""
Testes unitários para o HTTPClient.
"""

import pytest
import httpx
import pytest_asyncio

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
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(404)
        )

        async with HTTPClient(max_retries=3, cache_enabled=False) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get(SAMPLE_URL)

        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_403_raises_immediately(self, respx_mock):
        """403 não deve fazer retry."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(403)
        )

        async with HTTPClient(max_retries=3, cache_enabled=False) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get(SAMPLE_URL)

        assert exc_info.value.response.status_code == 403

    @pytest.mark.asyncio
    async def test_500_retries_and_eventually_raises(self, respx_mock):
        """500 deve fazer retry e levantar após esgotar tentativas."""
        respx_mock.get(SAMPLE_URL).mock(
            return_value=httpx.Response(500)
        )

        async with HTTPClient(max_retries=2, cache_enabled=False) as client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.get(SAMPLE_URL)

    @pytest.mark.asyncio
    async def test_timeout_retries_and_raises(self, respx_mock):
        """Timeout deve fazer retry e levantar após esgotar tentativas."""
        respx_mock.get(SAMPLE_URL).mock(
            side_effect=httpx.TimeoutException("timeout")
        )

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
