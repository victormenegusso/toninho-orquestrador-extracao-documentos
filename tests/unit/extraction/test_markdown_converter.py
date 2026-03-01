"""
Testes unitários para o módulo markdown_converter.
"""

import pytest

from toninho.extraction.markdown_converter import (
    build_markdown_with_metadata,
    clean_markdown,
    extract_from_html,
    extract_title,
    html_to_markdown,
)


SIMPLE_HTML = (
    "<html>"
    "<head><title>Minha Pagina</title></head>"
    "<body>"
    "<h1>Titulo Principal</h1>"
    "<p>Paragrafo de exemplo.</p>"
    '<a href="https://example.com">Link</a>'
    "</body>"
    "</html>"
).encode("utf-8")

H1_ONLY_HTML = (
    "<html><head></head><body><h1>Somente H1</h1></body></html>"
).encode("utf-8")

NO_TITLE_HTML = b"<html><body><p>Sem titulo</p></body></html>"


class TestExtractTitle:
    def test_extracts_title_tag(self):
        title = extract_title(SIMPLE_HTML)
        assert title == "Minha Pagina"

    def test_falls_back_to_h1(self):
        title = extract_title(H1_ONLY_HTML)
        assert title == "Somente H1"

    def test_returns_empty_when_no_title(self):
        title = extract_title(NO_TITLE_HTML)
        assert title == ""

    def test_handles_empty_bytes(self):
        title = extract_title(b"")
        assert title == ""


class TestHtmlToMarkdown:
    def test_converts_heading(self):
        html = b"<h1>Hello</h1>"
        md = html_to_markdown(html)
        assert "Hello" in md

    def test_converts_paragraph(self):
        html = b"<p>A paragraph</p>"
        md = html_to_markdown(html)
        assert "A paragraph" in md

    def test_converts_anchor_link(self):
        html = b'<a href="https://example.com">Click me</a>'
        md = html_to_markdown(html)
        assert "Click me" in md
        assert "example.com" in md

    def test_returns_string(self):
        md = html_to_markdown(SIMPLE_HTML)
        assert isinstance(md, str)
        assert len(md) > 0


class TestCleanMarkdown:
    def test_removes_trailing_spaces(self):
        md = "line with space   \nanother   "
        result = clean_markdown(md)
        for line in result.split("\n"):
            assert not line.endswith(" ")

    def test_collapses_multiple_blank_lines(self):
        md = "a\n\n\n\n\nb"
        result = clean_markdown(md)
        assert "\n\n\n" not in result

    def test_ends_with_newline(self):
        result = clean_markdown("content")
        assert result.endswith("\n")

    def test_normalises_crlf(self):
        md = "line1\r\nline2\r\nline3"
        result = clean_markdown(md)
        assert "\r" not in result


class TestBuildMarkdownWithMetadata:
    def test_includes_frontmatter(self):
        result = build_markdown_with_metadata(
            content="# Title\nContent",
            url="https://example.com",
            title="Example",
            extracted_at="2026-01-01T00:00:00+00:00",
        )
        assert result.startswith("---")
        assert "url: https://example.com" in result
        assert 'title: "Example"' in result
        assert "extracted_at: 2026-01-01T00:00:00+00:00" in result
        assert "Toninho v1.0" in result

    def test_content_after_frontmatter(self):
        result = build_markdown_with_metadata(
            content="Hello world",
            url="https://x.com",
            title="X",
            extracted_at="2026-01-01T00:00:00+00:00",
        )
        assert "Hello world" in result
        # Frontmatter deve vir primeiro
        assert result.index("---") < result.index("Hello world")


class TestExtractFromHtml:
    def test_returns_title_and_markdown(self):
        result = extract_from_html(SIMPLE_HTML)
        assert "title" in result
        assert "markdown" in result
        assert result["title"] == "Minha Pagina"

    def test_markdown_contains_heading(self):
        result = extract_from_html(SIMPLE_HTML)
        assert "Titulo Principal" in result["markdown"]

    def test_empty_html(self):
        result = extract_from_html(b"")
        assert result["title"] == ""
        assert isinstance(result["markdown"], str)
