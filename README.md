# Toninho - Sistema de Extração de Processos

Sistema de extração de dados de processos judiciais, desenvolvido com FastAPI, Celery e Docker.

## 🚀 Características

- 🔄 **Processamento Assíncrono**: Workers Celery para extração paralela
- 📊 **Monitoramento**: Interface Flower para acompanhamento de tasks
- 🐳 **Containerizado**: Deploy fácil com Docker e Docker Compose
- 🎯 **API RESTful**: Endpoints completos para CRUD e monitoramento
- 📝 **Logging Avançado**: Sistema de logs com Loguru
- ✅ **Qualidade de Código**: Pre-commit hooks, linters e formatadores
- 🧪 **Testes**: Cobertura com pytest

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
├── toninho/              # Código fonte principal
│   ├── api/             # Controllers (FastAPI routes)
│   ├── services/        # Lógica de negócio
│   ├── repositories/    # Acesso a dados
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # DTOs Pydantic
│   ├── workers/         # Celery tasks
│   ├── core/            # Configurações e utilitários
│   └── main.py          # Entry point
├── frontend/            # Interface web (HTMX + Alpine.js)
├── tests/               # Testes automatizados
├── migrations/          # Alembic migrations
├── scripts/             # Scripts utilitários
└── docs/                # Documentação
```

## 🎯 Uso

### Comandos Make

```bash
make help          # Lista todos os comandos disponíveis
make install       # Instala dependências
make run           # Executa aplicação
make test          # Executa testes
make lint          # Executa linters
make format        # Formata código
make clean         # Remove arquivos temporários
make docker-up     # Levanta ambiente Docker
make docker-down   # Derruba ambiente Docker
```

### API Endpoints

- `GET /` - Informações da API
- `GET /api/v1/health` - Health check
- `GET /docs` - Documentação Swagger
- `GET /redoc` - Documentação ReDoc

## 🧪 Testes

Execute os testes com:

```bash
make test
```

Para ver o relatório de cobertura:

```bash
make test
open htmlcov/index.html
```

## 🔨 Desenvolvimento

### Formatação de Código

O projeto usa Black e isort para formatação:

```bash
make format
```

### Linting

```bash
make lint
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

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Task Queue**: Celery + Redis
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Frontend**: HTMX, Alpine.js, TailwindCSS
- **Testing**: pytest, pytest-asyncio
- **Quality**: black, isort, flake8, mypy
- **Containerization**: Docker, Docker Compose
- **Logging**: Loguru

## 📖 Documentação

- [PRDs](docs/prd/) - Product Requirements Documents
- [Arquitetura](docs/architecture/) - Diagramas e decisões arquiteturais
- [API](docs/api/) - Documentação da API

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

## 🙏 Agradecimentos

Projeto desenvolvido como parte de um sistema de automação de extração de dados judiciais.
