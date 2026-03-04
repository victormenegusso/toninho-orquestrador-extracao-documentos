"""
Testes unitários para PageExtractor.
"""

import httpx
import pytest

from toninho.extraction.extractor import PageExtractor
from toninho.extraction.storage import LocalFileSystemStorage

SAMPLE_HTML = (
    b"<html>"
    b"<head><title>Test Page</title></head>"
    b"<body>"
    b"<h1>Main Heading</h1>"
    b"<p>This is a test paragraph.</p>"
    b"</body>"
    b"</html>"
)


@pytest.fixture
def storage(tmp_path):
    return LocalFileSystemStorage(base_dir=str(tmp_path))


@pytest.fixture
def extractor(storage):
    return PageExtractor(storage, timeout=10, max_retries=1, cache_enabled=False)


class TestPageExtractorSuccess:
    """Testes de extração bem-sucedida."""

    @pytest.mark.asyncio
    async def test_extract_returns_sucesso_status(self, extractor, respx_mock):
        url = "https://example.com/page"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        result = await extractor.extract(url, "output.md")

        assert result["status"] == "sucesso"

    @pytest.mark.asyncio
    async def test_extract_saves_file(self, extractor, storage, respx_mock, tmp_path):
        url = "https://example.com/page"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        await extractor.extract(url, "output.md")

        assert (tmp_path / "output.md").exists()

    @pytest.mark.asyncio
    async def test_extract_returns_title(self, extractor, respx_mock):
        url = "https://example.com/page"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        result = await extractor.extract(url, "output.md")

        assert result["title"] == "Test Page"

    @pytest.mark.asyncio
    async def test_extract_returns_bytes_count(self, extractor, respx_mock):
        url = "https://example.com/page"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        result = await extractor.extract(url, "output.md")

        assert result["bytes"] > 0

    @pytest.mark.asyncio
    async def test_extract_saved_file_has_frontmatter(
        self, extractor, storage, respx_mock, tmp_path
    ):
        url = "https://example.com/page"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        await extractor.extract(url, "output.md")

        content = (tmp_path / "output.md").read_text()
        assert content.startswith("---")
        assert f"url: {url}" in content

    @pytest.mark.asyncio
    async def test_extract_generates_filename_when_not_provided(
        self, extractor, respx_mock, tmp_path
    ):
        url = "https://example.com/about"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        result = await extractor.extract(url)

        # Deve ter gerado caminho a partir da URL
        assert result["path"] is not None
        assert "about" in result["path"]

    @pytest.mark.asyncio
    async def test_extract_url_is_in_result(self, extractor, respx_mock):
        url = "https://example.com/page"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        result = await extractor.extract(url, "output.md")

        assert result["url"] == url


class TestPageExtractorErrors:
    """Testes de tratamento de erros."""

    @pytest.mark.asyncio
    async def test_extract_returns_erro_on_404(self, extractor, respx_mock):
        url = "https://example.com/missing"
        respx_mock.get(url).mock(return_value=httpx.Response(404))

        result = await extractor.extract(url, "output.md")

        assert result["status"] == "erro"
        assert result["error"] is not None
        assert result["bytes"] == 0
        assert result["path"] is None

    @pytest.mark.asyncio
    async def test_extract_returns_erro_on_connection_error(
        self, extractor, respx_mock
    ):
        url = "https://unreachable.example.com/page"
        respx_mock.get(url).mock(side_effect=httpx.ConnectError("refused"))

        result = await extractor.extract(url, "output.md")

        assert result["status"] == "erro"
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_extract_error_result_has_all_keys(self, extractor, respx_mock):
        url = "https://example.com/missing"
        respx_mock.get(url).mock(return_value=httpx.Response(404))

        result = await extractor.extract(url, "output.md")

        assert all(
            k in result
            for k in ("status", "url", "path", "bytes", "title", "from_cache", "error")
        )


class TestPageExtractorFilename:
    """Testes para generate_filename."""

    def test_generate_filename_returns_md(self, extractor):
        name = extractor.generate_filename("https://example.com/about")
        assert name.endswith(".md")

    def test_generate_filename_different_urls(self, extractor):
        a = extractor.generate_filename("https://example.com/a")
        b = extractor.generate_filename("https://example.com/b")
        assert a != b


class TestPageExtractorContextManager:
    """Testes do context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self, storage, respx_mock):
        url = "https://example.com/cm"
        respx_mock.get(url).mock(return_value=httpx.Response(200, content=SAMPLE_HTML))

        async with PageExtractor(
            storage, max_retries=1, cache_enabled=False
        ) as extractor:
            result = await extractor.extract(url, "cm.md")

        assert result["status"] == "sucesso"
