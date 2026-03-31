# Contribuindo com o Toninho

## Pré-requisitos

- Python 3.11+
- Poetry 1.7+
- Docker 24.0+ e Docker Compose 2.20+ (para ambiente completo)
- Redis (ou via Docker)

## Setup do Ambiente

1. Clone o repositório
2. `cp .env.example .env`
3. `make install` (instala dependências + pre-commit hooks)
4. `make migrate` (roda migrations)
5. `make run` (inicia servidor de desenvolvimento)

## Fluxo de Contribuição

1. Crie uma branch a partir de `main`: `git checkout -b tipo/descricao`
   - Tipos: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`
2. Faça suas alterações
3. Garanta que os checks passam: `make quality`
4. Rode os testes: `make test`
5. Commit com Conventional Commits
6. Abra um Pull Request

## Convenções de Commit

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `refactor:` Refatoração (sem mudança de comportamento)
- `test:` Adição/correção de testes
- `chore:` Manutenção, dependências, CI

## Requisitos de Qualidade

Todo PR deve:

- [ ] Passar no linting (`make lint` — ruff + mypy)
- [ ] Passar nos testes (`make test` — cobertura mínima 75%)
- [ ] Passar na análise de segurança (`make security` — bandit)
- [ ] Seguir os padrões de código do projeto
- [ ] Incluir testes para novas funcionalidades
- [ ] Atualizar documentação se necessário

## Estrutura do Projeto

Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para a arquitetura completa.

### Camadas

- **Routes** (`toninho/api/routes/`): Endpoints FastAPI
- **Services** (`toninho/services/`): Lógica de negócio
- **Repositories** (`toninho/repositories/`): Acesso a dados
- **Models** (`toninho/models/`): Modelos SQLAlchemy
- **Schemas** (`toninho/schemas/`): DTOs Pydantic

### Testes

- `tests/unit/` — Testes unitários
- `tests/integration/` — Testes de integração (API)
- `tests/e2e/` — Testes end-to-end (Playwright)

## Code Review

- Todo PR precisa de pelo menos 1 aprovação
- Use comentários construtivos e específicos
- Verifique: lógica, testes, performance, segurança

## Dúvidas?

Abra uma issue ou entre em contato com os maintainers.
