"""E2E tests for download behavior using Playwright."""

import pytest
from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://localhost:8000"

# IDs from existing test data — we'll discover them dynamically
EXEC_WITH_CONSOLIDATED = None
EXEC_ANY = None


def get_execution_ids():
    """Get execution IDs from the running app."""
    import requests

    resp = requests.get(f"{BASE_URL}/api/v1/execucoes")
    data = resp.json()["data"]
    return [e["id"] for e in data]


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="module")
def page(browser):
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="module")
def exec_ids():
    ids = get_execution_ids()
    assert len(ids) > 0, "No executions found in running app"
    return ids


class TestDownloadButtons:
    """Test that download buttons actually trigger downloads instead of navigation."""

    def test_download_consolidated_triggers_download(self, page, exec_ids):
        """The 'Baixar Arquivo Único' button should trigger a file download."""
        exec_id = exec_ids[0]
        page.goto(f"{BASE_URL}/execucoes/{exec_id}/paginas")
        page.wait_for_load_state("networkidle")

        # Check if consolidated button exists
        consolidated_btn = page.locator("a:has-text('Baixar Arquivo Único')")
        if consolidated_btn.count() == 0:
            pytest.skip("No consolidated download button (not arquivo_unico mode)")

        # Click and expect a download event, NOT a navigation
        with page.expect_download(timeout=10000) as download_info:
            consolidated_btn.click()

        download = download_info.value
        assert download.suggested_filename == "resultado_completo.md"
        # Verify the page URL didn't change (no navigation happened)
        assert "/paginas" in page.url

    def test_download_zip_triggers_download(self, page, exec_ids):
        """The 'Baixar Todas (ZIP)' button should trigger a file download."""
        exec_id = exec_ids[0]
        page.goto(f"{BASE_URL}/execucoes/{exec_id}/paginas")
        page.wait_for_load_state("networkidle")

        zip_btn = page.locator("a:has-text('Baixar Todas (ZIP)')")
        assert zip_btn.count() > 0, "ZIP download button not found"

        with page.expect_download(timeout=10000) as download_info:
            zip_btn.click()

        download = download_info.value
        assert "zip" in download.suggested_filename.lower()
        assert "/paginas" in page.url

    def test_individual_page_download_triggers_download(self, page, exec_ids):
        """Individual page download buttons should trigger file downloads."""
        exec_id = exec_ids[0]
        page.goto(f"{BASE_URL}/execucoes/{exec_id}/paginas")
        page.wait_for_load_state("networkidle")

        download_links = page.locator("a[href*='/paginas/'][href*='/download']")
        if download_links.count() == 0:
            pytest.skip("No individual page download links found")

        with page.expect_download(timeout=10000) as download_info:
            download_links.first.click()

        download = download_info.value
        assert download.suggested_filename.endswith(".md")
        assert "/paginas" in page.url

    def test_download_buttons_have_hx_boost_false(self, page, exec_ids):
        """All download links must have hx-boost='false' to bypass HTMX interception."""
        exec_id = exec_ids[0]
        page.goto(f"{BASE_URL}/execucoes/{exec_id}/paginas")
        page.wait_for_load_state("networkidle")

        # Check all download-related <a> tags
        download_links = page.locator("a[download]")
        count = download_links.count()
        assert count > 0, "No links with download attribute found"

        for i in range(count):
            link = download_links.nth(i)
            hx_boost = link.get_attribute("hx-boost")
            href = link.get_attribute("href")
            assert hx_boost == "false", (
                f"Link {href} missing hx-boost='false' — "
                f"HTMX will intercept the click and prevent download"
            )


class TestPreviewConsolidated:
    """Test the consolidated file preview functionality."""

    def test_preview_button_opens_modal(self, page, exec_ids):
        """The 'Preview Arquivo Único' button should open the preview modal."""
        exec_id = exec_ids[0]
        page.goto(f"{BASE_URL}/execucoes/{exec_id}/paginas")
        page.wait_for_load_state("networkidle")

        preview_btn = page.locator("button:has-text('Preview Arquivo Único')")
        if preview_btn.count() == 0:
            pytest.skip("No consolidated preview button (not arquivo_unico mode)")

        preview_btn.click()

        # Modal should appear
        modal = page.locator("#preview-modal")
        expect(modal).to_be_visible(timeout=5000)

        # Title should be set
        title = page.locator("#preview-title")
        expect(title).to_have_text("Arquivo Consolidado")

    def test_preview_shows_content(self, page, exec_ids):
        """Preview modal should load and display the consolidated content."""
        exec_id = exec_ids[0]
        page.goto(f"{BASE_URL}/execucoes/{exec_id}/paginas")
        page.wait_for_load_state("networkidle")

        preview_btn = page.locator("button:has-text('Preview Arquivo Único')")
        if preview_btn.count() == 0:
            pytest.skip("No consolidated preview button")

        preview_btn.click()

        # Content should load (loading spinner hidden, content visible)
        content_area = page.locator("#preview-content")
        expect(content_area).to_be_visible(timeout=10000)

        text_el = page.locator("#preview-text")
        expect(text_el).not_to_be_empty(timeout=10000)
