# Toninho - Sistema de Extração de Documentos

Sistema de extração de dados de documentos web, convertendo HTML em Markdown. Desenvolvido com FastAPI, Celery e Docker.

## 🚀 Características

- 🔄 **Processamento Assíncrono**: Workers Celery para extração paralela
- 📊 **Monitoramento**: Interface Flower + WebSocket para acompanhamento em tempo real
- 🐳 **Containerizado**: Deploy fácil com Docker e Docker Compose
- 🎯 **API RESTful**: 40+ endpoints para CRUD, monitoramento e streaming
- 🌐 **Extração Inteligente**: HTML2Text, IBM Docling e Playwright (SPAs)
- 📝 **Logging Avançado**: Sistema de logs com Loguru + SSE streaming
- ✅ **Qualidade de Código**: Pre-commit hooks, Ruff, mypy, bandit
- 🧪 **Testes**: Unit, Integration e E2E com Playwright (cobertura 90%)
- 🖥️ **Interface Web**: HTMX + Alpine.js + TailwindCSS

## 📋 Pré-requisitos

- Python 3.11+
- Poetry 1.7+
- Docker 24.0+
- Docker Compose 2.20+
- Redis (ou via Docker)

## 🔧 Instalação

### Instalação Local (Desenvolvimento)

1. Clone o repositório:
```bash
git clone <repository-url>
cd toninho-processo-extracao
```

2. Configure o ambiente:
```bash
# Copie o arquivo de exemplo de variáveis de ambiente
cp .env.example .env

# Instale as dependências
make install
```

3. Execute a aplicação:
```bash
make run
```

A API estará disponível em http://localhost:8000

### Instalação com Docker

```bash
# Configure o ambiente
cp .env.example .env

# Levante todos os serviços
make docker-up
```

Serviços disponíveis:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Flower (Monitoring): http://localhost:5555

## 📁 Estrutura do Projeto

```
toninho-processo-extracao/
├── toninho/              # Código fonte principal (backend)
│   ├── api/             # Camada de API (FastAPI routes)
│   ├── services/        # Camada de Serviço (lógica de negócio)
│   ├── repositories/    # Camada de Repositório (acesso a dados)
│   ├── models/          # Modelos SQLAlchemy (ORM)
│   ├── schemas/         # Schemas Pydantic (DTOs)
│   ├── workers/         # Celery workers e tasks
│   ├── extraction/      # Módulo de extração (HTTP, Browser, Markdown)
│   ├── monitoring/      # Health checks e métricas
│   ├── core/            # Configurações e infraestrutura
│   └── main.py          # Entry point FastAPI
├── frontend/            # Interface web (HTMX + Alpine.js)
│   ├── templates/       # Templates Jinja2
│   └── static/          # CSS, JS, imagens
├── tests/               # Testes automatizados
│   ├── unit/            # Testes unitários
│   ├── integration/     # Testes de integração
│   └── e2e/             # Testes E2E (Playwright)
├── migrations/          # Alembic migrations
├── scripts/             # Scripts utilitários
└── docs/                # Documentação completa
```

📖 [Visão completa da arquitetura](docs/ARCHITECTURE.md)

## 🎯 Uso

### Comandos Make

```bash
make help              # Lista todos os comandos disponíveis
make install           # Instala dependências
make run               # Executa aplicação
make test              # Executa testes unitários + integração (cobertura 90%)
make test-e2e          # Executa testes E2E com Playwright (headless)
make test-e2e-headed   # Executa testes E2E com browser visível
make lint              # Executa linters (ruff + mypy)
make format            # Formata código (ruff format)
make security          # Analisa segurança (bandit)
make audit             # Verifica vulnerabilidades (pip-audit)
make quality           # Todas as verificações de qualidade
make clean             # Remove arquivos temporários
make docker-up         # Levanta ambiente Docker
make docker-down       # Derruba ambiente Docker
```

### API Endpoints Principais

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/processos` | Criar processo |
| `GET` | `/api/v1/processos` | Listar processos |
| `POST` | `/api/v1/processos/{id}/configuracoes` | Configurar extração |
| `POST` | `/api/v1/processos/{id}/execucoes` | Iniciar execução |
| `GET` | `/api/v1/execucoes/{id}` | Status da execução |
| `GET` | `/api/v1/execucoes/{id}/progresso` | Progresso em tempo real |
| `POST` | `/api/v1/execucoes/{id}/cancelar` | Cancelar execução |
| `GET` | `/api/v1/execucoes/{id}/logs/stream` | Logs via SSE |

📖 [Documentação completa da API](docs/API.md) — 40+ endpoints documentados

## 🧪 Testes

```bash
make test              # Testes unitários + integração (cobertura 90%)
make test-e2e          # Testes E2E com Playwright (headless)
make test-e2e-headed   # Testes E2E com browser visível
```

O projeto conta com 15 suítes de testes E2E cobrindo criação de processos, validação de formulários, execuções, logs SSE, navegação e mais.

📖 [Guia completo de testes](docs/TESTING.md)

## 🔨 Desenvolvimento

### Formatação de Código

O projeto usa Ruff para linting e formatação:

```bash
make format    # Auto-formata código
make lint      # Verifica linting e tipagem (ruff + mypy)
```

### Linting

```bash
make lint      # ruff check + mypy
make security  # bandit (análise de segurança)
make check     # Verifica sem alterar arquivos
```

### Pre-commit Hooks

Pre-commit hooks são executados automaticamente antes de cada commit:

```bash
# Instalar hooks
make pre-commit

# Executar manualmente
poetry run pre-commit run --all-files
```

## 🛠️ Tecnologias

- **Backend**: FastAPI, SQLAlchemy 2.x, Pydantic 2.x
- **Task Queue**: Celery + Redis
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Extração**: html2text, BeautifulSoup4, IBM Docling, Playwright
- **Frontend**: HTMX, Alpine.js, TailwindCSS, Jinja2
- **Testing**: pytest, pytest-asyncio, pytest-playwright
- **Quality**: ruff (linter + formatter), mypy (type checker), bandit (security)
- **Containerization**: Docker, Docker Compose
- **Logging**: Loguru
- **Monitoramento**: Flower, WebSocket, SSE

## 📖 Documentação

- [Arquitetura](docs/ARCHITECTURE.md) - Visão completa do sistema
- [API](docs/API.md) - Referência dos endpoints REST
- [Testes](docs/TESTING.md) - Guia de testes e cobertura E2E
- [ADRs](docs/adr/) - Architecture Decision Records
- [PRDs](docs/prd/) - Product Requirements Documents
- [Índice Completo](docs/README.md) - Navegação de toda a documentação

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Convenções de Commit

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `refactor:` - Refatoração
- `test:` - Testes
- `chore:` - Tarefas de manutenção

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- Victor Menegusso
