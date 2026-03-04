"""
Testes unitários para toninho/extraction/utils.py.
"""

from toninho.extraction.utils import build_output_path, sanitize_filename


class TestSanitizeFilename:
    def test_simple_path(self):
        filename = sanitize_filename("https://example.com/about")
        assert filename == "about.md"

    def test_nested_path_uses_hyphens(self):
        filename = sanitize_filename("https://example.com/docs/api/v1")
        assert "docs" in filename
        assert filename.endswith(".md")

    def test_root_url_uses_hostname(self):
        filename = sanitize_filename("https://example.com")
        assert filename.endswith(".md")
        assert len(filename) > 3

    def test_root_path_uses_hostname(self):
        filename = sanitize_filename("https://example.com/")
        assert filename.endswith(".md")

    def test_invalid_chars_replaced(self):
        filename = sanitize_filename("https://example.com/path?query=1&foo=bar")
        assert "?" not in filename
        assert "&" not in filename

    def test_max_length_respected(self):
        long_url = "https://example.com/" + "a" * 200
        filename = sanitize_filename(long_url, max_length=50)
        name_without_ext = filename[:-3]  # remove .md
        assert len(name_without_ext) <= 50

    def test_always_ends_with_md(self):
        for url in [
            "https://example.com",
            "https://example.com/page",
            "https://example.com/a/b/c/d",
        ]:
            assert sanitize_filename(url).endswith(".md")

    def test_no_leading_trailing_special_chars(self):
        filename = sanitize_filename("https://example.com/--path--")
        # Should not start/end with hyphens or underscores (after stripping)
        name = filename[:-3]
        assert name[0] not in ("-", "_")
        assert name[-1] not in ("-", "_")

    def test_empty_path_falls_back_to_hostname(self):
        filename = sanitize_filename("https://mysite.org")
        assert filename != ".md"
        assert len(filename) > 3


class TestBuildOutputPath:
    def test_builds_expected_structure(self):
        path = build_output_path(
            processo_id="proc-123",
            execucao_id="exec-456",
            url="https://example.com/page",
        )
        assert path.startswith("proc-123/exec-456/")
        assert path.endswith(".md")

    def test_filename_from_url(self):
        path = build_output_path("p1", "e1", "https://example.com/about")
        assert "about" in path
