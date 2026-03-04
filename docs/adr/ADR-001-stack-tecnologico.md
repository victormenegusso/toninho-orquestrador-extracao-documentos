# ADR-001: Stack Tecnológico Principal

**Status**: Aceito
**Data**: 2025
**Contexto**: Escolha da stack para sistema de extração web com processamento assíncrono.

---

## Decisão

| Camada | Tecnologia |
|---|---|
| API | FastAPI 0.100+ |
| ORM | SQLAlchemy 2.x |
| Validação/DTOs | Pydantic v2 |
| Task queue | Celery + Redis |
| Banco (dev) | SQLite |
| Banco (prod) | PostgreSQL |
| Frontend | HTMX + Alpine.js + TailwindCSS |
| Logging | Loguru |
| Containerização | Docker + Docker Compose |

## Razões

- **FastAPI**: tipagem nativa, async, geração automática de OpenAPI, alta performance.
- **SQLAlchemy 2.x**: suporte async, tipagem, migrations via Alembic.
- **Pydantic v2**: validação em runtime + serialização com performance superior à v1.
- **Celery + Redis**: maturidade, suporte a retry, agendamento (Celery Beat), monitoramento (Flower).
- **Loguru**: API simples, estruturação de logs, rotação automática.

## Consequências

- Stack Python-first, sem microserviços.
- Redis obrigatório em todos os ambientes.
- SQLite apenas para desenvolvimento local; migrações Alembic mantêm compatibilidade.
