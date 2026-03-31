# Agent Instructions

## Project Overview

Toninho is a web document extraction orchestrator that converts HTML pages to Markdown. It provides a REST API for managing extraction processes, scheduling, and monitoring.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI + Uvicorn
- **ORM:** SQLAlchemy 2.x (SQLite dev / PostgreSQL prod)
- **Validation:** Pydantic 2.x
- **Task Queue:** Celery + Redis
- **Extraction:** html2text, BeautifulSoup4, IBM Docling, Playwright
- **Frontend:** HTMX + Alpine.js + TailwindCSS + Jinja2
- **Testing:** pytest (unit, integration, E2E with Playwright)

## Essential Commands

| Command | Purpose |
|---------|---------|
| `make install` | Install all dependencies |
| `make run` | Start development server |
| `make test` | Run unit + integration tests |
| `make test-e2e` | Run E2E tests (Playwright) |
| `make lint` | Lint code (ruff + mypy) |
| `make format` | Format code (ruff) |
| `make quality` | All quality checks |
| `make migrate` | Run database migrations |

## Architecture

Layered architecture with strict dependency direction:

```
Routes (API) → Services (Business Logic) → Repositories (Data Access) → Models (ORM)
```

- `toninho/api/routes/` — FastAPI endpoints with `Depends()` injection
- `toninho/services/` — Business logic (never import routes)
- `toninho/repositories/` — Database operations (never import services)
- `toninho/models/` — SQLAlchemy models
- `toninho/schemas/` — Pydantic DTOs
- `toninho/extraction/` — Web extraction engines
- `toninho/workers/tasks/` — Celery background tasks
- `toninho/core/` — Config, database, exceptions, logging

## Code Conventions

- **Formatter/Linter:** Ruff (line-length=88, double quotes)
- **Type checker:** mypy
- **Commits:** Conventional Commits (feat:, fix:, docs:, refactor:, test:, chore:)
- **Domain terms:** Portuguese (processo, execucao, configuracao, pagina_extraida, volume, log)
- **Technical terms:** English
- **Tests:** pytest with markers (unit, integration, e2e)
- **Coverage:** Minimum 75%

## Anti-patterns to Avoid

- Do NOT access the database directly from route handlers — use the service layer
- Do NOT import from `toninho/api/` in service or repository modules
- Do NOT use `time.sleep()` in tests — use Playwright auto-wait or pytest fixtures
- Do NOT hardcode configuration values — use `toninho/core/config.py` (pydantic-settings)
- Do NOT create new Celery tasks outside `toninho/workers/tasks/`
- Do NOT modify database models without creating an Alembic migration

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — Full system architecture
- [API Reference](docs/API.md) — 40+ REST endpoints
- [Testing Guide](docs/TESTING.md) — Test strategy and coverage
- [ADRs](docs/adr/) — Architecture Decision Records
