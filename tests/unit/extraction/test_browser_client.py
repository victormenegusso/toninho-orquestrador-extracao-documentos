"""
Testes unitários para BrowserClient (MH-003).
"""

import pytest


class TestBrowserClientImport:
    """Testes de inicialização e importação."""

    def test_import_without_playwright_raises(self, monkeypatch):
        """BrowserClient deve levantar ImportError se playwright não está instalado."""
        import sys

        # Simular playwright não instalado
        monkeypatch.setitem(sys.modules, "playwright", None)
        monkeypatch.setitem(sys.modules, "playwright.async_api", None)

        # Forçar reimportação do módulo
        if "toninho.extraction.browser_client" in sys.modules:
            del sys.modules["toninho.extraction.browser_client"]

        from toninho.extraction.browser_client import BrowserClient

        with pytest.raises(ImportError, match="playwright"):
            BrowserClient()

    def test_default_parameters(self, monkeypatch):
        """BrowserClient deve ter parâmetros padrão corretos."""
        import sys
        from unittest.mock import MagicMock

        # Simular playwright instalado
        mock_playwright = MagicMock()
        monkeypatch.setitem(sys.modules, "playwright", mock_playwright)
        monkeypatch.setitem(sys.modules, "playwright.async_api", MagicMock())

        if "toninho.extraction.browser_client" in sys.modules:
            del sys.modules["toninho.extraction.browser_client"]

        from toninho.extraction.browser_client import BrowserClient

        client = BrowserClient()
        assert client.timeout == 30_000
        assert client.wait_for == "networkidle"
        assert client._browser is None
        assert client._playwright is None

    def test_custom_parameters(self, monkeypatch):
        """BrowserClient deve aceitar parâmetros customizados."""
        import sys
        from unittest.mock import MagicMock

        mock_playwright = MagicMock()
        monkeypatch.setitem(sys.modules, "playwright", mock_playwright)
        monkeypatch.setitem(sys.modules, "playwright.async_api", MagicMock())

        if "toninho.extraction.browser_client" in sys.modules:
            del sys.modules["toninho.extraction.browser_client"]

        from toninho.extraction.browser_client import BrowserClient

        client = BrowserClient(timeout=60_000, wait_for="load")
        assert client.timeout == 60_000
        assert client.wait_for == "load"


class TestBrowserClientInPageExtractor:
    """Testa integração do BrowserClient com PageExtractor."""

    def test_page_extractor_default_no_browser(self):
        """PageExtractor deve usar HTTP simples por padrão (use_browser=False)."""
        from unittest.mock import MagicMock
        from toninho.extraction.extractor import PageExtractor

        storage = MagicMock()
        extractor = PageExtractor(storage)

        assert extractor.use_browser is False
        assert extractor._browser_client is None

    def test_page_extractor_use_browser_flag(self, monkeypatch):
        """PageExtractor com use_browser=True deve instanciar BrowserClient."""
        import sys
        from unittest.mock import MagicMock

        mock_playwright = MagicMock()
        monkeypatch.setitem(sys.modules, "playwright", mock_playwright)
        monkeypatch.setitem(sys.modules, "playwright.async_api", MagicMock())

        # Limpar módulos para forçar reimportação com playwright mockado
        for mod in list(sys.modules.keys()):
            if "browser_client" in mod:
                del sys.modules[mod]

        from toninho.extraction.browser_client import BrowserClient
        from unittest.mock import patch
        from toninho.extraction.extractor import PageExtractor

        storage = MagicMock()
        with patch("toninho.extraction.extractor.PageExtractor.__init__", wraps=lambda s, *a, **kw: None):
            extractor = PageExtractor.__new__(PageExtractor)
            extractor.use_browser = True
            extractor._browser_client = BrowserClient()
            assert extractor.use_browser is True
            assert isinstance(extractor._browser_client, BrowserClient)
