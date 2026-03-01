# PRD-002: Ambiente de Desenvolvimento

**Status**: 📋 Pronto para implementação  
**Prioridade**: 🔴 Crítica - Bloqueante  
**Categoria**: Setup e Infraestrutura  
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Configurar o ambiente de desenvolvimento completo do projeto Toninho utilizando Poetry para gerenciamento de dependências Python e Docker/Docker Compose para containerização dos serviços (Redis, aplicação, workers). Este PRD garante que qualquer desenvolvedor consiga levantar o ambiente local de forma consistente e reproduzível.

## 2. Contexto e Justificativa

O Toninho depende de múltiplos serviços para funcionar (FastAPI, Celery Workers, Redis, Flower para monitoramento). Usar Docker Compose simplifica o gerenciamento desses serviços e garante que todos trabalhem no mesmo ambiente, independente de sistema operacional.

**Decisões arquiteturais:**
- Poetry: Gerenciamento moderno de dependências Python com lock file
- Docker Multi-stage: Builds otimizados e imagens menores
- Docker Compose: Orquestração local de serviços
- Hot-reload: Desenvolvimento ágil com recarregamento automático
- Separação de configuração: .env para desenvolvimento, variáveis de ambiente para produção

## 3. Requisitos Técnicos

### 3.1. Poetry - Gerenciamento de Dependências

#### 3.1.1. Configuração Poetry
O arquivo `pyproject.toml` (já criado no PRD-001) deve estar corretamente configurado com:

**Dependências de Produção:**
- fastapi (^0.109.0): Framework web
- uvicorn[standard] (^0.27.0): ASGI server
- sqlalchemy (^2.0.25): ORM
- alembic (^1.13.1): Database migrations
- pydantic (^2.5.3): Validação de dados
- pydantic-settings (^2.1.0): Gerenciamento de settings
- celery (^5.3.6): Task queue
- redis (^5.0.1): Message broker e cache
- httpx (^0.26.0): HTTP client assíncrono
- docling: Extração de conteúdo web (verificar versão disponível)
- loguru (^0.7.2): Logging simplificado
- python-dotenv (^1.0.1): Variáveis de ambiente
- jinja2 (^3.1.3): Template engine
- python-multipart (^0.0.6): Upload de arquivos
- flower (^2.0.1): Monitoramento Celery
- rich (^13.7.0): CLI output bonito

**Dependências de Desenvolvimento:**
- pytest (^7.4.4): Framework de testes
- pytest-asyncio (^0.23.3): Suporte async para pytest
- pytest-cov (^4.1.0): Coverage
- pytest-mock (^3.12.0): Mocking
- httpx-mock (^0.11.0): Mock para httpx
- black (^23.12.1): Formatação de código
- isort (^5.13.2): Organização de imports
- flake8 (^7.0.0): Linting
- mypy (^1.8.0): Type checking
- pre-commit (^3.6.0): Git hooks
- testcontainers (^3.7.1): Containers para testes
- ipython (^8.20.0): REPL melhorado
- ipdb (^0.13.13): Debugger

#### 3.1.2. Scripts Poetry
No `pyproject.toml`, adicionar seção de scripts:
```toml
[tool.poetry.scripts]
toninho = "toninho.main:cli"
```

#### 3.1.3. Comandos Poetry Essenciais
Desenvolvedores precisarão saber:
- `poetry install`: Instala dependências do lock file
- `poetry add <pacote>`: Adiciona nova dependência
- `poetry add --group dev <pacote>`: Adiciona dependência de desenvolvimento
- `poetry remove <pacote>`: Remove dependência
- `poetry update`: Atualiza dependências
- `poetry shell`: Ativa ambiente virtual
- `poetry run <comando>`: Executa comando no ambiente virtual
- `poetry export -f requirements.txt --output requirements.txt`: Gera requirements.txt

### 3.2. Docker - Containerização

#### 3.2.1. Dockerfile Multi-stage

**Estratégia:**
- Stage 1 (builder): Instala dependências e compila pacotes
- Stage 2 (runtime): Copia apenas necessário, imagem final otimizada
- Usuário não-root para segurança
- Health checks configurados

**Estrutura esperada:**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
# Instalar Poetry
# Copiar pyproject.toml e poetry.lock
# Instalar dependências (sem dev)
# Gerar requirements.txt (fallback)

# Stage 2: Runtime
FROM python:3.11-slim
# Criar usuário não-root
# Copiar dependências do builder
# Copiar código fonte
# Expor portas
# Health check
# CMD para executar aplicação
```

**Requisitos específicos:**
- Python 3.11-slim como base (menor)
- Poetry instalado apenas no builder stage
- Dependências instaladas sem cache do pip
- Timezone configurado (UTC)
- Usuário `toninho` (uid 1000) para execução
- Workdir: `/app`
- Porta 8000 exposta (FastAPI)
- Health check via `/api/v1/health`
- Logs escritos em stdout/stderr

#### 3.2.2. .dockerignore
Otimizar builds ignorando:
- `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
- `.git/`, `.github/`
- `.env`, `.env.local`
- `output/`
- `*.db`, `*.sqlite`
- `.vscode/`, `.idea/`
- `docs/`, `tests/`
- `README.md`, `LICENSE`
- `htmlcov/`, `.coverage`, `.pytest_cache/`

### 3.3. Docker Compose - Orquestração

#### 3.3.1. Arquitetura de Serviços
O `docker-compose.yml` deve orquestrar:

1. **redis**: Message broker e cache
2. **api**: Aplicação FastAPI
3. **worker**: Celery worker (processamento assíncrono)
4. **beat**: Celery beat (agendamento)
5. **flower**: Interface web para monitoramento Celery

#### 3.3.2. Configuração docker-compose.yml

**Serviço: redis**
- Imagem: redis:7-alpine
- Porta: 6379:6379
- Volume: redis_data (persistência)
- Health check: redis-cli ping
- Restart: unless-stopped
- Comando: redis-server --appendonly yes (durabilidade)

**Serviço: api**
- Build: . (Dockerfile local)
- Porta: 8000:8000
- Volumes:
  - ./toninho:/app/toninho (hot-reload em dev)
  - ./output:/app/output (arquivos extraídos)
- Env file: .env
- Variáveis de ambiente:
  - CELERY_BROKER_URL=redis://redis:6379/0
  - DATABASE_URL=sqlite:///./toninho.db
- Depends on: redis (com condition: service_healthy)
- Restart: unless-stopped
- Command: uvicorn toninho.main:app --host 0.0.0.0 --port 8000 --reload

**Serviço: worker**
- Build: . (mesma imagem que api)
- Volumes: mesmo que api
- Env file: .env
- Variáveis de ambiente: mesmas que api
- Depends on: redis, api
- Restart: unless-stopped
- Command: celery -A toninho.workers.celery_app worker --loglevel=info --concurrency=2

**Serviço: beat**
- Build: . (mesma imagem que api)
- Volumes: mesmo que api
- Env file: .env
- Variáveis de ambiente: mesmas que api
- Depends on: redis, worker
- Restart: unless-stopped
- Command: celery -A toninho.workers.celery_app beat --loglevel=info

**Serviço: flower**
- Build: . (mesma imagem que api)
- Porta: 5555:5555
- Env file: .env
- Variáveis de ambiente: mesmas que api
- Depends on: redis, worker
- Restart: unless-stopped
- Command: celery -A toninho.workers.celery_app flower --port=5555

**Volumes:**
- redis_data: Persistência Redis
- sqlite_data: Database SQLite (opcional, pode ser apenas bind mount)

**Networks:**
- toninho_network: Bridge network para comunicação entre serviços

#### 3.3.3. docker-compose.override.yml (Desenvolvimento)
Para facilitar desenvolvimento local, criar arquivo override:
- Hot-reload habilitado
- Debug logs
- Montagem de código fonte
- Portas expostas para debug (ex: 5678 para debugpy)
- Volumes de cache (\_\_pycache\_\_, .pytest\_cache)

### 3.4. Scripts Utilitários

#### 3.4.1. scripts/setup.sh
Script de setup inicial:
```bash
#!/bin/bash
# Verificar pré-requisitos (Poetry, Docker, Docker Compose)
# Copiar .env.example para .env
# Instalar dependências Poetry
# Instalar pre-commit hooks
# Criar diretório output/
# Build imagens Docker
# Executar migrations
# Mensagem de sucesso com próximos passos
```

#### 3.4.2. scripts/run_dev.sh
Executar ambiente de desenvolvimento:
```bash
#!/bin/bash
# Verificar se .env existe
# Docker compose up com rebuild
# Seguir logs
```

#### 3.4.3. scripts/run_tests.sh
Executar testes:
```bash
#!/bin/bash
# Executar pytest com coverage
# Gerar relatório HTML
# Exibir resumo
```

#### 3.4.4. scripts/migrate.sh
Executar migrations:
```bash
#!/bin/bash
# Executar alembic upgrade head dentro do container
```

#### 3.4.5. scripts/shell.sh
Abrir shell no container:
```bash
#!/bin/bash
# docker-compose exec api bash
```

Todos os scripts devem:
- Ter permissões de execução (chmod +x)
- Validar pré-condições antes de executar
- Exibir mensagens claras de erro
- Usar cores para saída (verde=sucesso, vermelho=erro)

### 3.5. Configuração de IDE

#### 3.5.1. VSCode (.vscode/settings.json)
Configurações recomendadas:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.rulers": [88]
  }
}
```

#### 3.5.2. VSCode (extensions.json)
Extensões recomendadas:
- ms-python.python
- ms-python.vscode-pylance
- ms-azuretools.vscode-docker
- tamasfe.even-better-toml
- charliermarsh.ruff

## 4. Dependências

### 4.1. Pré-requisitos de Sistema
- Docker 24.0+ instalado
- Docker Compose 2.20+ instalado
- Poetry 1.7+ instalado
- Python 3.11+ instalado
- Git instalado
- Make (opcional, mas recomendado)

### 4.2. Dependências de Outros PRDs
- **PRD-001**: Setup do Projeto (estrutura de diretórios, pyproject.toml)

### 4.3. PRDs Subsequentes
Todos os PRDs de implementação dependem deste para desenvolvimento local.

## 5. Regras de Negócio

### 5.1. Gestão de Dependências
- **Lock file obrigatório**: poetry.lock deve estar versionado
- **Dependências explícitas**: Todas as dependências diretas no pyproject.toml
- **Versões pinadas**: Usar ^ para compatibilidade semântica
- **Separação dev/prod**: Dependências de desenvolvimento isoladas

### 5.2. Configuração de Ambiente
- **Variáveis sensíveis**: Nunca commitar .env
- **Template atualizado**: .env.example sempre sincronizado
- **Valores default**: Settings devem ter defaults seguros
- **Documentação**: Cada variável documentada no .env.example

### 5.3. Docker
- **Builds otimizados**: Usar multi-stage para reduzir tamanho
- **Segurança**: Executar como usuário não-root
- **Health checks**: Todos os serviços devem ter health check
- **Logs**: Sempre em stdout/stderr (nunca em arquivos)
- **Restart policy**: unless-stopped para serviços persistentes

### 5.4. Desenvolvimento Local
- **Hot-reload**: Código deve recarregar automaticamente em dev
- **Consistência**: Todos devs trabalham no mesmo ambiente (Docker)
- **Isolamento**: Cada serviço em container separado
- **Limpeza**: `make clean` deve limpar todos os artefatos

## 6. Casos de Teste

### 6.1. Validação Poetry
- ✅ `poetry check` executa sem erros
- ✅ `poetry install` instala todas as dependências
- ✅ `poetry lock --check` confirma lock file atualizado
- ✅ `poetry show` lista todas as dependências instaladas
- ✅ Ambiente virtual é criado em .venv/

### 6.2. Validação Docker
- ✅ `docker build .` constrói imagem sem erros
- ✅ Imagem final tem tamanho razoável (< 500MB)
- ✅ Container executa como usuário não-root
- ✅ Health check retorna sucesso
- ✅ Logs aparecem em stdout

### 6.3. Validação Docker Compose
- ✅ `docker-compose config` valida sintaxe
- ✅ `docker-compose up` levanta todos os serviços
- ✅ Redis responde em localhost:6379
- ✅ API responde em localhost:8000
- ✅ Flower responde em localhost:5555
- ✅ Health checks de todos os serviços passam
- ✅ Workers Celery conectam ao Redis
- ✅ Logs aparecem corretamente

### 6.4. Validação Hot-reload
- ✅ Alterar código Python recarrega API automaticamente
- ✅ Workers reiniciam após mudança em tasks
- ✅ Templates Jinja2 recarregam sem rebuild

### 6.5. Validação Scripts
- ✅ `./scripts/setup.sh` executa setup completo
- ✅ `./scripts/run_dev.sh` levanta ambiente
- ✅ `./scripts/shell.sh` abre shell no container
- ✅ Todos os scripts exibem mensagens claras

## 7. Critérios de Aceitação

### ✅ Poetry
- [ ] pyproject.toml configurado com todas as dependências
- [ ] `poetry install` executa sem erros
- [ ] `poetry lock` gera lock file válido
- [ ] Ambiente virtual criado em .venv/
- [ ] Scripts Poetry funcionam

### ✅ Docker
- [ ] Dockerfile multi-stage criado
- [ ] .dockerignore completo
- [ ] Imagem constrói sem erros
- [ ] Imagem final otimizada (< 500MB)
- [ ] Container executa como não-root
- [ ] Health check funciona

### ✅ Docker Compose
- [ ] docker-compose.yml com todos os serviços
- [ ] docker-compose.override.yml para dev
- [ ] Volumes configurados corretamente
- [ ] Networks configuradas
- [ ] Variáveis de ambiente carregadas
- [ ] Todos os serviços startam sem erros
- [ ] Health checks passam

### ✅ Scripts
- [ ] scripts/setup.sh criado e funcional
- [ ] scripts/run_dev.sh criado e funcional
- [ ] scripts/run_tests.sh criado e funcional
- [ ] scripts/migrate.sh criado e funcional
- [ ] scripts/shell.sh criado e funcional
- [ ] Todos os scripts com permissões corretas

### ✅ Configuração IDE
- [ ] .vscode/settings.json criado
- [ ] .vscode/extensions.json criado
- [ ] Configurações funcionam no VSCode

### ✅ Documentação
- [ ] README.md atualizado com instruções Docker
- [ ] .env.example com todas as variáveis documentadas
- [ ] Comentários em docker-compose.yml

### ✅ Validação Final
- [ ] Novo desenvolvedor consegue rodar `./scripts/setup.sh` e `./scripts/run_dev.sh` sem erros
- [ ] API responde em http://localhost:8000
- [ ] Swagger disponível em http://localhost:8000/docs
- [ ] Flower disponível em http://localhost:5555
- [ ] Hot-reload funciona alterando código
- [ ] `make test` executa testes (mesmo sem implementação ainda)
- [ ] `docker-compose down -v` limpa ambiente completamente

## 8. Notas de Implementação

### 8.1. Ordem de Execução Sugerida
1. Finalizar configuração pyproject.toml
2. Executar `poetry install`
3. Criar Dockerfile multi-stage
4. Criar .dockerignore
5. Testar build da imagem: `docker build -t toninho:dev .`
6. Criar docker-compose.yml
7. Criar docker-compose.override.yml
8. Testar compose: `docker-compose config`
9. Criar scripts utilitários (setup.sh, run_dev.sh, etc)
10. Dar permissões: `chmod +x scripts/*.sh`
11. Criar configurações VSCode
12. Atualizar README.md
13. Atualizar .env.example
14. Executar setup completo: `./scripts/setup.sh`
15. Validar ambiente: `./scripts/run_dev.sh`

### 8.2. Validação Manual
```bash
# Setup inicial
./scripts/setup.sh

# Levantar ambiente
./scripts/run_dev.sh

# Em outro terminal, validar serviços
curl http://localhost:8000/api/v1/health
curl http://localhost:5555  # Flower

# Validar hot-reload
# Editar toninho/main.py, adicionar rota de teste
# Verificar se API recarregou automaticamente

# Abrir shell
./scripts/shell.sh

# Dentro do container
python -c "import toninho; print('OK')"

# Validar workers
docker-compose logs worker

# Derrubar ambiente
docker-compose down -v
```

### 8.3. Pontos de Atenção
- **M1/ARM Macs**: Algumas imagens Docker podem ter problemas, usar plataforma linux/amd64 se necessário
- **Permissões**: Volumes montados podem ter problemas de permissão, garantir uid 1000
- **Redis persistência**: Redis deve usar AOF (appendonly yes) para durabilidade
- **SQLite**: Em container, garantir que arquivo .db está em volume persistente
- **Logs**: Configurar log level apropriado para dev (DEBUG) vs prod (INFO)
- **Memory**: Docker Compose pode precisar de limites de memória em ambientes restritos
- **Networking**: Garantir que portas 8000, 6379, 5555 não estão em uso

### 8.4. Troubleshooting Comum
- **"Permission denied" em scripts**: Executar `chmod +x scripts/*.sh`
- **"Port already in use"**: Verificar com `lsof -i :8000` e matar processo
- **"Cannot connect to Redis"**: Verificar health do Redis com `docker-compose ps`
- **Hot-reload não funciona**: Verificar volume mount no docker-compose.yml
- **Poetry não encontrado**: Instalar via `curl -sSL https://install.python-poetry.org | python3 -`

## 9. Referências Técnicas

- **Poetry**: https://python-poetry.org/docs/
- **Docker Multi-stage**: https://docs.docker.com/build/building/multi-stage/
- **Docker Compose**: https://docs.docker.com/compose/
- **Celery**: https://docs.celeryproject.org/
- **Flower**: https://flower.readthedocs.io/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/docker/
- **Redis Docker**: https://hub.docker.com/_/redis
- **Uvicorn**: https://www.uvicorn.org/

## 10. Definição de Pronto

Este PRD estará completo quando:
- ✅ Poetry instalado e todas as dependências resolvidas
- ✅ Dockerfile multi-stage criado e testado
- ✅ Docker Compose levanta todos os serviços sem erros
- ✅ API responde em localhost:8000
- ✅ Flower (monitoramento Celery) acessível em localhost:5555
- ✅ Workers Celery conectados e funcionais
- ✅ Redis persistente e funcionando
- ✅ Hot-reload funciona durante desenvolvimento
- ✅ Scripts utilitários criados e testados
- ✅ Novo desenvolvedor consegue executar setup em < 10 minutos
- ✅ Documentação completa no README.md
- ✅ .env.example atualizado
- ✅ Configurações VSCode facilitam desenvolvimento
- ✅ `make test` executa (mesmo sem testes implementados ainda)

---

**PRD Anterior**: PRD-001 - Setup do Projeto  
**Próximo PRD**: PRD-003 - Models e Database
