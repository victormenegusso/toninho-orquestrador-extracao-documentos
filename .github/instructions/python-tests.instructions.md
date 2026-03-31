---
applyTo: "**/tests/**/*.py"
---

# Python Test Conventions

## Framework & Configuration

- Use **pytest** as the test framework with fixtures defined in `conftest.py` at multiple directory levels.
- `asyncio_mode` is set to `"auto"` — do **not** use the `@pytest.mark.asyncio` decorator; async tests are detected automatically.

## Test Markers

Apply the appropriate markers to classify tests:

- `@pytest.mark.unit` — unit tests
- `@pytest.mark.integration` — integration tests
- `@pytest.mark.e2e` — end-to-end tests
- `@pytest.mark.slow` — long-running tests
- `@pytest.mark.requires_redis` — tests that depend on Redis
- `@pytest.mark.requires_celery` — tests that depend on Celery

## Coverage

- Minimum coverage threshold is **75%**, enforced by `--cov-fail-under=75`.

## Mocking

- Use **pytest-mock** for general mocking via the `mocker` fixture.
- Use **respx** for mocking HTTP requests made with `httpx`.

## Naming Conventions

| Element       | Pattern                          | Example                        |
|---------------|----------------------------------|--------------------------------|
| Test file     | `test_<module_name>.py`          | `test_processo_service.py`     |
| Test function | `test_<description_of_behavior>` | `test_retorna_erro_quando_processo_nao_encontrado` |
| Test class    | `Test<ClassName>`                | `TestProcessoService`          |

Group related tests inside a class to improve readability.

## Test Data & Fixtures

- Use factories and fixtures from `tests/fixtures/` for test data creation.
- Keep every test **independent and isolated** — no shared mutable state between tests.

## Domain Language

Domain terms must be written in **Portuguese** to match the codebase (e.g., `processo`, `execucao`, `configuracao`, `documento`, `extracao`).
