# ADR-004: Arquitetura em Camadas

**Status**: Aceito
**Data**: 2025
**Contexto**: Necessidade de separação de responsabilidades, testabilidade e manutenibilidade.

---

## Decisão

Arquitetura em 4 camadas:

```
API (routes/) → Services (services/) → Repositories (repositories/) → Models (models/)
```

| Camada | Responsabilidade |
|---|---|
| `api/routes/` | HTTP: parsing request, validação schema, HTTP response |
| `services/` | Regras de negócio, orquestração entre entidades |
| `repositories/` | Queries SQL via SQLAlchemy, sem lógica de negócio |
| `models/` | Entidades SQLAlchemy + Enums do domínio |
| `schemas/` | DTOs Pydantic para input/output |
| `workers/` | Celery tasks; orquestra `ExtractionOrchestrator` |
| `extraction/` | Módulo autônomo: HTTP fetch, parse, markdown, storage |

## Razões

- Testabilidade: cada camada mockável independentemente.
- Services são injetados via FastAPI `Depends()` → sem acoplamento direto.
- `extraction/` desacoplado: pode ser usado standalone ou como biblioteca.

## Consequências

- Verbosidade maior (mais arquivos/classes).
- Mudanças de banco afetam apenas `repositories/` e `models/`.
- `ExtractionOrchestrator` nos workers conecta as duas "fronteiras" (DB ↔ extraction).
