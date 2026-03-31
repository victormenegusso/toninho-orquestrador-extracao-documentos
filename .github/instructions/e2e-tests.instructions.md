---
applyTo: "**/tests/e2e/**/*.py"
---

# End-to-End Test Conventions

## Framework

- Use **pytest-playwright** for browser automation.
- Tests run **headless** by default (`make test-e2e`); use headed mode for debugging (`make test-e2e-headed`).

## Locators

Use stable, resilient locators in order of preference:

1. `page.get_by_role()` — semantic role-based selection
2. `page.get_by_text()` — visible text content
3. `page.get_by_test_id()` — `data-testid` attributes
4. `page.locator()` — CSS/XPath as a last resort

## Navigation

- Use `page.goto()` with **relative paths** — the base URL is configured in `conftest.py`.

## Waiting & Assertions

- Leverage Playwright's **auto-wait** mechanism — avoid explicit `time.sleep()` calls.
- Use Playwright's `expect` API for assertions:
  - `expect(locator).to_be_visible()`
  - `expect(locator).to_have_text()`
  - `expect(locator).to_have_count()`
  - `expect(page).to_have_url()`
- For HTMX dynamic content, use `page.wait_for_load_state("networkidle")` when the auto-wait is not sufficient.

## Frontend Context

- The frontend uses **HTMX + Alpine.js** — account for dynamic content loading and partial page swaps in assertions and waits.

## Naming

- Test files: `test_<feature>_<scenario>.py` (e.g., `test_processo_criacao.py`)

## Isolation & Cleanup

- Each test must be **independent and isolated** — no shared state between tests.
- Use fixtures with **teardown** logic to clean up any test data created during the test.
