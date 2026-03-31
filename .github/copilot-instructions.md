# Toninho — Copilot Instructions

## Project Overview

Toninho is a web document extraction orchestrator that converts HTML pages to Markdown. It is built with **FastAPI**, **Celery**, **Redis**, **SQLAlchemy**, and **Docker**. The frontend uses **HTMX**, **Alpine.js**, and **TailwindCSS** with Jinja2 templates.

## Tech Stack

- **Language:** Python 3.11+
- **Web Framework:** FastAPI ^0.135.2
- **ORM:** SQLAlchemy 2.x (SQLite for dev, PostgreSQL for prod)
- **Validation:** Pydantic 2.x
- **Task Queue:** Celery + Redis
- **Extraction:** html2text, BeautifulSoup4, IBM Docling, Playwright
- **Frontend:** HTMX, Alpine.js, TailwindCSS, Jinja2
- **Testing:** pytest, pytest-asyncio, pytest-playwright (target 90% coverage)
- **Quality:** Ruff (linter + formatter), mypy, bandit, pip-audit, pre-commit
- **Logging:** Loguru
- **Migrations:** Alembic
- **Containerization:** Docker, Docker Compose

## Architecture

The project follows a **layered architecture** with clear separation of concerns:

| Layer | Path | Responsibility |
|---|---|---|
| Routes | `toninho/api/routes/` | FastAPI endpoints with `Depends()` injection |
| Dependencies | `toninho/api/dependencies/` | FastAPI dependency injection factories |
| Services | `toninho/services/` | Business logic |
| Repositories | `toninho/repositories/` | Data access (SQLAlchemy) |
| Models | `toninho/models/` | SQLAlchemy ORM models |
| Schemas | `toninho/schemas/` | Pydantic v2 DTOs and validators |
| Extraction | `toninho/extraction/` | Web extraction (HTTP, Browser, Docling, Markdown) |
| Workers | `toninho/workers/` | Celery workers and tasks |
| Monitoring | `toninho/monitoring/` | Health checks, metrics, WebSocket |
| Core | `toninho/core/` | Config, database, exceptions, logging, constants |
| Frontend | `frontend/` | HTMX + Alpine.js + TailwindCSS templates |
| Tests | `tests/unit/`, `tests/integration/`, `tests/e2e/` | Organized by scope |
| Migrations | `migrations/` | Alembic database migrations |

**Data flow:** Route → Service → Repository → Model

## Code Standards

- **Ruff config:** `line-length = 88`, `target-version = "py311"`, double quotes, space indentation.
- **Ruff lint rules:** E, W, F, I, B, C4, UP, SIM, TCH, RUF.
- **mypy:** `python_version = "3.11"`, `ignore_missing_imports = true`.
- **Bandit:** security scanning (excludes `tests/` and `migrations/`).
- **Commits:** follow [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

## Naming Conventions

- **Domain names are in Portuguese:** `processo`, `execucao`, `configuracao`, `pagina_extraida`, `volume`, `log`.
- **Technical terms remain in English:** service, repository, schema, model, route, worker, task.
- Code, comments, docstrings, and documentation are written in **English**.

## Key Patterns

- FastAPI routes receive dependencies via `Depends()` from `toninho/api/dependencies/`.
- Pydantic v2 schemas with shared validators in `toninho/schemas/validators.py`.
- Custom exception hierarchy in `toninho/core/exceptions.py`.
- Configuration loaded via `pydantic-settings` in `toninho/core/config.py`.
- Celery tasks live in `toninho/workers/tasks/`.
- Tests use `asyncio_mode = "auto"` for async test support.

## Key Commands (Makefile)

| Command | Description |
|---|---|
| `make install` | Install dependencies (Poetry) + pre-commit hooks |
| `make run` | Start dev server (uvicorn on `0.0.0.0:8000`) |
| `make test` | Run unit + integration tests with coverage (min 75%) |
| `make test-e2e` | Run E2E tests with Playwright (headless) |
| `make lint` | Run `ruff check` + `mypy` |
| `make format` | Auto-format with `ruff format` |
| `make security` | Run bandit security scan |
| `make audit` | Run pip-audit vulnerability check |
| `make quality` | Run all quality checks (lint + security + audit) |
| `make migrate` | Run Alembic migrations |
| `make docker-up` / `make docker-down` | Manage Docker Compose stack |

## CI/CD

- **`ci.yml`:** Quality job (ruff, mypy, bandit, pip-audit) + Test job (pytest on Python 3.11 and 3.12).
- **`test.yml`:** Test workflow for PRs to `main` with a Redis service container.
