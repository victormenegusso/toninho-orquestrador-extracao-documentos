---
applyTo: "**/api/routes/*.py,**/api/dependencies/*.py"
---

# API Routes & Dependencies Conventions

## Dependency Injection

- FastAPI routes use dependency injection via `Depends()` with providers defined in `toninho/api/dependencies/`.
- Each route module follows the pattern: **import dependencies → define router → define endpoints**.

## Request & Response Schemas

- Use Pydantic schemas from `toninho/schemas/` for all request and response models.
- Standard response format is `{"data": ..., "message": "..."}` provided by `toninho/schemas/responses.py`.

## Error Handling

- Raise custom exceptions defined in `toninho/core/exceptions.py`.
- Never return raw error dicts — always use the exception classes so error responses are consistent.

## Route Design

- All route paths follow REST conventions under the `/api/v1/` prefix.
- Use appropriate HTTP status codes:
  - `201` for resource creation
  - `204` for deletion (no content)
  - `200` for successful reads and updates
  - `422` for validation errors (handled automatically by FastAPI)

## Layered Architecture

- Dependencies inject **services**, which in turn inject **repositories**.
- **Never** access the database directly from route handlers — always go through the service layer.

## OpenAPI Documentation

- Include proper OpenAPI metadata on every endpoint:
  - `summary` — short one-line description
  - `description` — detailed explanation when needed
  - `response_model` — Pydantic schema for the response body
