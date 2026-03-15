"""Testes unitários para DoclingPageExtractor."""

from unittest.mock import MagicMock, patch

import pytest

from toninho.extraction.storage import LocalFileSystemStorage

SAMPLE_MARKDOWN = "# Título da Página\n\nConteúdo do documento."
MOCK_RESULT = MagicMock()
MOCK_RESULT.document.export_to_markdown.return_value = SAMPLE_MARKDOWN


@pytest.fixture
def storage(tmp_path):
    return LocalFileSystemStorage(base_dir=str(tmp_path))


@pytest.fixture
def extractor(storage):
    with patch("toninho.extraction.docling_extractor.DocumentConverter") as mock_cls:
        mock_cls.return_value = MagicMock()
        from toninho.extraction.docling_extractor import DoclingPageExtractor

        ext = DoclingPageExtractor(storage)
        ext._converter.convert.return_value = MOCK_RESULT
        yield ext


class TestDoclingPageExtractorExtract:
    @pytest.mark.asyncio
    async def test_retorna_status_sucesso(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["status"] == "sucesso"

    @pytest.mark.asyncio
    async def test_retorna_bytes_positivos(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["bytes"] > 0

    @pytest.mark.asyncio
    async def test_retorna_titulo_do_h1(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["title"] == "Título da Página"

    @pytest.mark.asyncio
    async def test_from_cache_sempre_false(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["from_cache"] is False

    @pytest.mark.asyncio
    async def test_arquivo_salvo_contem_frontmatter_docling(self, extractor, tmp_path):
        await extractor.extract("https://exemplo.com", "out.md")
        content = (tmp_path / "out.md").read_text()
        assert "extrator: Toninho/Docling v1.0" in content
        assert "---" in content

    @pytest.mark.asyncio
    async def test_retorna_erro_quando_docling_falha(self, extractor):
        extractor._converter.convert.side_effect = Exception("timeout docling")
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["status"] == "erro"
        assert "timeout docling" in result["error"]
        assert result["bytes"] == 0
        assert result["path"] is None

    @pytest.mark.asyncio
    async def test_erro_nao_propaga_excecao(self, extractor):
        """extract() deve capturar exceptions e retornar dict, não propagar."""
        extractor._converter.convert.side_effect = RuntimeError("crash")
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["status"] == "erro"


class TestDoclingPageExtractorExtractFromHtml:
    @pytest.mark.asyncio
    async def test_retorna_status_sucesso(self, extractor):
        html = b"<html><body><h1>Test</h1></body></html>"
        result = await extractor.extract_from_html(html, "https://x.com", "out.md")
        assert result["status"] == "sucesso"

    @pytest.mark.asyncio
    async def test_chama_convert_com_arquivo_temporario(self, extractor):
        """_convert_html_bytes deve chamar convert() com um path de arquivo, não URL."""
        html = b"<html><body></body></html>"
        extractor._converter.convert.return_value = MOCK_RESULT

        await extractor.extract_from_html(html, "https://x.com", "out.md")

        call_arg = extractor._converter.convert.call_args[0][0]
        # O argumento é um path de arquivo temporário, não a URL
        assert call_arg != "https://x.com"
        assert call_arg.endswith(".html")

    @pytest.mark.asyncio
    async def test_retorna_erro_quando_docling_falha(self, extractor):
        extractor._converter.convert.side_effect = ValueError("parse error")
        html = b"<html><body></body></html>"
        result = await extractor.extract_from_html(html, "https://x.com", "out.md")
        assert result["status"] == "erro"
        assert "parse error" in result["error"]


class TestDoclingPageExtractorHelpers:
    def test_extract_title_retorna_h1(self, extractor):
        md = "# Meu Título\n\nConteúdo aqui."
        assert extractor._extract_title_from_markdown(md) == "Meu Título"

    def test_extract_title_sem_h1_retorna_vazio(self, extractor):
        md = "## Subtítulo\n\nSem H1."
        assert extractor._extract_title_from_markdown(md) == ""

    def test_extract_title_h1_com_espacos(self, extractor):
        md = "#  Título com espaços extras  \n\nBody."
        assert extractor._extract_title_from_markdown(md) == "Título com espaços extras"

    def test_build_frontmatter_contem_campos_obrigatorios(self, extractor):
        result = extractor._build_with_frontmatter(
            content="# Body",
            url="https://x.com",
            title="Título",
            extracted_at="2026-03-12T00:00:00Z",
        )
        assert "url: https://x.com" in result
        assert 'titulo: "Título"' in result
        assert "extrator: Toninho/Docling v1.0" in result
        assert result.startswith("---")

    def test_build_frontmatter_nao_contem_extrator_html2text(self, extractor):
        result = extractor._build_with_frontmatter(
            content="body", url="https://x.com", title="T", extracted_at="2026"
        )
        assert "Toninho v1.0" not in result
        assert "Toninho/Docling v1.0" in result

    @pytest.mark.asyncio
    async def test_close_nao_levanta_excecao(self, extractor):
        await extractor.close()  # deve completar sem erros
