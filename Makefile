.PHONY: help install run test test-e2e test-e2e-headed test-e2e-debug lint format check security audit quality clean pre-commit migrate shell docker-up docker-down check-poetry

help: ## Mostra esta mensagem de ajuda
	@echo "Comandos disponíveis:"
	@echo "  make install      - Instala dependências com Poetry"
	@echo "  make run          - Executa aplicação em modo desenvolvimento"
	@echo "  make test         - Executa testes com coverage"
	@echo "  make test-e2e     - Executa testes E2E com Playwright (headless)"
	@echo "  make test-e2e-headed - Executa testes E2E com browser visível"
	@echo "  make test-e2e-debug TEST=<path> - Executa um teste E2E específico em modo debug"
	@echo "  make lint         - Executa linters (ruff + mypy)"
	@echo "  make format       - Formata código (ruff format)"
	@echo "  make check        - Verifica linting e formatação sem alterar"
	@echo "  make security     - Analisa segurança do código (bandit)"
	@echo "  make audit        - Verifica vulnerabilidades nas dependências (pip-audit)"
	@echo "  make quality      - Executa todas as verificações de qualidade"
	@echo "  make clean        - Remove arquivos temporários"
	@echo "  make pre-commit   - Instala pre-commit hooks"
	@echo "  make migrate      - Executa migrations do banco de dados"
	@echo "  make shell        - Abre shell Python no ambiente"
	@echo "  make docker-up    - Levanta ambiente Docker"
	@echo "  make docker-down  - Derruba ambiente Docker"

check-poetry:
	@which poetry > /dev/null || (echo "❌ Poetry não está instalado!" && echo "Instale com: curl -sSL https://install.python-poetry.org | python3 -" && echo "Ou use: ./scripts/setup.sh" && exit 1)

install: check-poetry ## Instala dependências
	poetry install
	poetry run pre-commit install
	@echo "✓ Dependências instaladas com sucesso!"

run: check-poetry ## Executa aplicação
	poetry run uvicorn toninho.main:app --reload --host 0.0.0.0 --port 8000

test: check-poetry ## Executa testes com coverage
	poetry run pytest -v

test-e2e: check-poetry ## Executa testes E2E com Playwright (headless)
	poetry run pytest tests/e2e/ -m e2e --browser chromium --no-cov -v

test-e2e-headed: check-poetry ## Executa testes E2E com browser visível
	poetry run pytest tests/e2e/ -m e2e --browser chromium --headed --slowmo 300 --no-cov -v

test-e2e-debug: check-poetry ## Executa teste E2E específico com browser visível
	poetry run pytest $(TEST) -m e2e --browser chromium --headed --slowmo 500 --no-cov -v -s

lint: check-poetry ## Executa linters (ruff + mypy)
	poetry run ruff check toninho tests
	poetry run mypy toninho
	@echo "✓ Lint concluído!"

format: check-poetry ## Formata código com ruff
	poetry run ruff format toninho tests
	poetry run ruff check --fix toninho tests
	@echo "✓ Código formatado!"

check: check-poetry ## Verifica linting e formatação sem alterar
	poetry run ruff format --check toninho tests
	poetry run ruff check toninho tests
	poetry run mypy toninho
	@echo "✓ Verificação concluída!"

security: check-poetry ## Analisa segurança do código com bandit
	poetry run bandit -c pyproject.toml -r toninho
	@echo "✓ Análise de segurança concluída!"

audit: check-poetry ## Verifica vulnerabilidades nas dependências
	poetry run pip-audit
	@echo "✓ Auditoria de dependências concluída!"

quality: check lint security audit test ## Executa todas as verificações de qualidade
	@echo ""
	@echo "✅ Todas as verificações de qualidade passaram!"

clean: ## Remove arquivos temporários
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	@echo "✓ Arquivos temporários removidos!"

pre-commit: check-poetry ## Instala pre-commit hooks
	poetry run pre-commit install
	@echo "✓ Pre-commit hooks instalados!"

migrate: check-poetry ## Executa migrations
	poetry run alembic upgrade head

shell: check-poetry ## Abre shell Python
	poetry run ipython

docker-up: ## Levanta ambiente Docker
	docker-compose up --build

docker-down: ## Derruba ambiente Docker
	docker-compose down -v
