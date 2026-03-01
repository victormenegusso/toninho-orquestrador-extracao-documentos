# Toninho - Processo de Extração

## Introdução

Toninho é um agente orquestrador de processos de extração de dados voltado para uso local e estudo. Seu objetivo é facilitar a coleta, transformação e armazenamento de dados de sites web, com foco em documentações técnicas e conteúdo relevante para processamento por IA. O sistema prioriza simplicidade, facilidade de uso e acompanhamento eficiente dos processos.

### Características Principais

- **Single-user**: Sistema voltado para uso local, sem necessidade de autenticação
- **Assíncrono**: Processamento em background com workers dedicados
- **Tempo Real**: Acompanhamento do progresso via WebSockets/SSE
- **Containerizado**: Deploy facilitado com Docker e Docker Compose
- **Extensível**: Arquitetura preparada para futuras integrações (storage, notificações)

## Funcionalidades

### Versão Inicial (MVP)

1. **Criar Processos de Extração**
   - Configuração de URL para extração
   - Definição de parâmetros (timeout, tentativas, formato de saída)
   - Armazenamento em filesystem local (markdown)
   - Interface via formulário único

2. **Gerenciar Processos**
   - Listar processos com status em tempo real
   - Editar configurações de processos existentes
   - Deletar processos (deleção física)
   - Monitorar progresso e visualizar logs

3. **Executar Extrações**
   - Processamento em background via workers
   - Até 5 processos simultâneos (configurável)
   - Estados: Criado → Aguardando → Em Execução → Concluído/Falhou/Cancelado
   - Timeout padrão: 1 hora (configurável)
   - Retry automático: 3 tentativas com backoff exponencial
   - Cancelamento de processos em execução

4. **Agendamento**
   - Suporte a cron expressions (execuções recorrentes)
   - Execuções one-time (agendamento único)
   - Gerenciamento de filas quando há sobreposição

5. **Monitoramento**
   - Logs em tempo real (stdout)
   - Métricas via API: tempo de execução, páginas processadas, taxa de erro, tamanho
   - Progresso em tempo real via WebSockets/SSE

### Funcionalidades Futuras

- **Exploração de Sites**: Descoberta automática de páginas filhas com regras customizáveis
- **Notificações**: Email, webhooks, Slack, Discord, Telegram
- **Versionamento**: Histórico de extrações com controle de versões
- **Templates**: Configurações pré-definidas para sites comuns
- **Integrações**: Obsidian, Notion, Confluence
- **Dashboard de Métricas**: Visualização com Grafana
- **Autenticação em Sites**: Login, cookies, tokens API

## Casos de Uso

### Exemplo 1: Documentação Spring Cloud
O usuário fornece URLs da documentação do Spring Cloud, configura o processo para extrair o conteúdo em markdown. O sistema acessa as páginas, extrai o conteúdo usando docling e salva em arquivos markdown organizados (ou em um único arquivo, conforme configuração).

### Exemplo 2: GitHub Copilot Docs
Páginas relacionadas como:
- `https://docs.github.com/en/copilot/get-started/quickstart`
- `https://docs.github.com/en/copilot/get-started/what-is-github-copilot`

O usuário configura a extração dessas URLs específicas, e o sistema processa cada uma, gerando arquivos markdown estruturados com metadados (título, URL fonte, data de extração).

### Objetivo Principal
Extrair conteúdo de sites técnicos para formato markdown, facilitando:
- Leitura offline
- Processamento por modelos de IA
- Organização de conhecimento
- Análise e busca em documentações

## Arquitetura

### Visão Geral
- **Estilo**: Monolito com backend e frontend separados
- **Comunicação**: REST API + WebSockets/SSE para tempo real
- **Processamento**: Workers assíncronos separados do servidor web
- **Padrão**: Arquitetura em camadas (Controller → Service → Repository)

### Componentes

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Frontend   │ ←REST→  │   Backend    │ ←API→   │   Workers   │
│ (HTMX/Vue)  │ ←WSS→   │   (FastAPI)  │         │  (Celery)   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │                          │
                              ↓                          ↓
                        ┌──────────┐              ┌──────────┐
                        │  SQLite  │              │  Redis   │
                        │   (BD)   │              │ (Queue)  │
                        └──────────┘              └──────────┘
```

### Estrutura de Diretórios (Backend)

```
toninho/
├── api/
│   ├── routes/          # Controllers (endpoints)
│   └── dependencies/    # DI e validações
├── services/            # Lógica de negócio
├── repositories/        # Acesso a dados
├── models/              # Entidades do domínio
├── schemas/             # DTOs (Pydantic)
├── workers/             # Celery tasks
├── core/                # Configurações, logging
└── tests/               # Testes (90% cobertura)
```

## Tecnologias Utilizadas

### Backend
- **Framework**: FastAPI
  - Moderno, rápido e com type hints
  - Documentação automática (Swagger/OpenAPI)
  - Suporte nativo a async/await
  - Validação com Pydantic

- **Task Queue**: Celery + Redis
  - Processamento assíncrono robusto
  - Celery Beat para agendamento (cron)
  - Monitoramento com Flower
  - Retry e error handling nativos
  
  **Por que Redis?**
  - Celery precisa de um message broker (não funciona sozinho)
  - Redis serve como broker (fila de mensagens) e backend de resultados
  - Alternativas: RabbitMQ (mais complexo), Amazon SQS (cloud)
  - Redis é leve, rápido e também útil para cache HTTP
  - Facilita comunicação entre FastAPI e workers Celery

- **ORM**: SQLAlchemy 2.0+ com Alembic
  - Padrão da indústria Python
  - Suporte a migrations gerenciadas
  - Integração com FastAPI

- **Extração**: Docling
  - Extração de conteúdo web para markdown
  - Suporte a JavaScript dinâmico (headless browser)
  - Estrutura padronizada com metadados

- **HTTP Client**: httpx
  - Cliente async para requisições
  - Cache de requisições
  - Retry e timeout configuráveis

### Frontend
**HTMX + Alpine.js + Tailwind CSS + Jinja2**
- Interatividade sem JavaScript complexo
- Server-side rendering com Jinja2
- Interface leve baseada em cards
- Atualização parcial de páginas via HTMX
- Reatividade leve com Alpine.js
- Estilização rápida com Tailwind CSS
- Ideal para projetos de estudo e uso local

### Banco de Dados
- **Desenvolvimento/Produção**: SQLite
  - Zero configuração
  - Arquivo único
  - Suficiente para uso local single-user
  
- **Opção Futura**: PostgreSQL (se houver necessidade de multi-user)

### DevOps & Tooling
- **Containerização**: Docker + Docker Compose
- **Gerenciamento de Deps**: Poetry ou pip-tools
- **Logs**: Loguru (logging simplificado)
- **CLI**: Rich (output terminal bonito)
- **Testes**: pytest + pytest-asyncio + testcontainers
- **Variáveis de Ambiente**: python-dotenv

### Instalação
1. **Docker Compose** (recomendado): `docker-compose up`
2. **Local**: `pip install toninho && toninho start`

## Interfaces e Abstrações

### Estratégia de Extensibilidade

Para facilitar a adição de novas integrações no futuro (storage, notificações, etc), o sistema utilizará **Design Patterns** e **Abstrações**:

### Storage Interface

```python
from abc import ABC, abstractmethod
from typing import BinaryIO, List

class StorageInterface(ABC):
    """Interface abstrata para diferentes tipos de armazenamento"""
    
    @abstractmethod
    async def save_file(self, path: str, content: BinaryIO) -> str:
        """Salva arquivo e retorna o caminho/URL"""
        pass
    
    @abstractmethod
    async def get_file(self, path: str) -> BinaryIO:
        """Recupera arquivo do storage"""
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Deleta arquivo do storage"""
        pass
    
    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """Lista arquivos em um diretório"""
        pass

# Implementação para filesystem local (MVP)
class LocalFileSystemStorage(StorageInterface):
    async def save_file(self, path: str, content: BinaryIO) -> str:
        # Implementação para salvar localmente
        ...

# Implementação futura para S3
class S3Storage(StorageInterface):
    async def save_file(self, path: str, content: BinaryIO) -> str:
        # Implementação para salvar no S3
        ...
```

### Notification Interface

```python
from abc import ABC, abstractmethod
from enum import Enum

class NotificationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationInterface(ABC):
    """Interface abstrata para diferentes canais de notificação"""
    
    @abstractmethod
    async def send(self, title: str, message: str, level: NotificationLevel) -> bool:
        """Envia notificação"""
        pass

# Implementação futura para Email
class EmailNotification(NotificationInterface):
    async def send(self, title: str, message: str, level: NotificationLevel) -> bool:
        # Implementação para enviar email
        ...

# Implementação futura para Webhook
class WebhookNotification(NotificationInterface):
    async def send(self, title: str, message: str, level: NotificationLevel) -> bool:
        # Implementação para webhook
        ...
```

### Dependency Injection

As implementações serão injetadas via **FastAPI Depends**:

```python
from fastapi import Depends
from typing import Annotated

def get_storage() -> StorageInterface:
    """Factory para criar instância de storage baseado em config"""
    storage_type = settings.STORAGE_TYPE  # 'local', 's3', etc
    
    if storage_type == 'local':
        return LocalFileSystemStorage(settings.OUTPUT_DIR)
    elif storage_type == 's3':
        return S3Storage(settings.S3_BUCKET)
    # ...

# Uso nos endpoints
@router.post("/processos/{processo_id}/executar")
async def executar_processo(
    processo_id: str,
    storage: Annotated[StorageInterface, Depends(get_storage)]
):
    # O código não precisa saber qual implementação está sendo usada
    await storage.save_file(...)
```

### Benefícios

✅ **Baixo Acoplamento**: Código não depende de implementações concretas
✅ **Testabilidade**: Fácil criar mocks para testes
✅ **Extensibilidade**: Adicionar nova integração = criar nova classe implementando a interface
✅ **Configurável**: Trocar implementação via variável de ambiente
✅ **SOLID Principles**: Seguindo Open/Closed Principle

### Exemplo de Adição Futura

Para adicionar suporte a Google Cloud Storage:

1. Criar nova classe `GCSStorage(StorageInterface)`
2. Implementar os métodos da interface
3. Adicionar no factory `get_storage()`
4. Configurar via env: `STORAGE_TYPE=gcs`
5. **Nenhuma mudança** no código dos serviços!

## Modelo de Dados

### Diagrama de Relacionamentos

```
┌─────────────────┐
│    Processo     │
├─────────────────┤
│ id (PK)         │
│ nome            │
│ descricao       │
│ status          │
│ criado_em       │
│ atualizado_em   │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐       ┌─────────────────┐
│  Configuracao   │       │    Execucao     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ processo_id(FK) │◄──┐   │ processo_id(FK) │
│ urls (JSON)     │   │   │ status          │
│ timeout         │   │   │ iniciado_em     │
│ max_retries     │   │   │ finalizado_em   │
│ formato_saida   │   │   │ pag_processadas │
│ output_dir      │   │   │ bytes_extraidos │
└─────────────────┘   │   │ taxa_erro       │
                      │   └────────┬────────┘
                      │            │ 1
                      │            │
                      │            │ N
                      │   ┌────────▼────────┐
                      │   │      Log        │
                      │   ├─────────────────┤
                      │   │ id (PK)         │
                      │   │ execucao_id(FK) │
                      │   │ nivel           │
                      │   │ mensagem        │
                      └───┤ timestamp       │
                          └─────────────────┘
                                   │ 1
                                   │
                                   │ N
                          ┌────────▼────────┐
                          │ PaginaExtraida  │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ execucao_id(FK) │
                          │ url_original    │
                          │ caminho_arquivo │
                          │ status          │
                          │ tamanho_bytes   │
                          │ timestamp       │
                          └─────────────────┘
```

### Entidades Principais

**Processo**
- `id` (UUID): Identificador único
- `nome` (String): Nome do processo
- `descricao` (Text): Descrição detalhada
- `status` (Enum): Ativo, Inativo, Arquivado
- `criado_em` (DateTime): Data de criação
- `atualizado_em` (DateTime): Última atualização
- **Relacionamento**: 1-N com Configuração e Execuções

**Configuração**
- `id` (UUID): Identificador único
- `processo_id` (UUID FK): Referência ao processo
- `urls` (JSON): Lista de URLs para extração
- `timeout` (Integer): Timeout em segundos (default: 3600)
- `max_retries` (Integer): Máximo de tentativas (default: 3)
- `formato_saida` (Enum): ARQUIVO_UNICO, MULTIPLOS_ARQUIVOS
- `output_dir` (String): Diretório de saída
- `agendamento_cron` (String, nullable): Expressão cron
- `agendamento_tipo` (Enum): RECORRENTE, ONE_TIME, MANUAL
- **Relacionamento**: N-1 com Processo

**Execução**
- `id` (UUID): Identificador único
- `processo_id` (UUID FK): Referência ao processo
- `status` (Enum): Criado, Aguardando, Em Execução, Pausado, Concluído, Falhou, Cancelado, Concluído com Erros
- `iniciado_em` (DateTime, nullable): Quando iniciou
- `finalizado_em` (DateTime, nullable): Quando finalizou
- `paginas_processadas` (Integer): Contador de páginas
- `bytes_extraidos` (BigInteger): Total de bytes
- `taxa_erro` (Float): Percentual de erros
- `tentativa_atual` (Integer): Número da tentativa
- **Relacionamento**: N-1 com Processo, 1-N com Logs e Páginas Extraídas

**Log**
- `id` (UUID): Identificador único
- `execucao_id` (UUID FK): Referência à execução
- `nivel` (Enum): DEBUG, INFO, WARNING, ERROR
- `mensagem` (Text): Conteúdo do log
- `timestamp` (DateTime): Momento do log
- `contexto` (JSON, nullable): Dados adicionais
- **Relacionamento**: N-1 com Execução

**Página Extraída**
- `id` (UUID): Identificador único
- `execucao_id` (UUID FK): Referência à execução
- `url_original` (String): URL da página
- `caminho_arquivo` (String): Path do arquivo markdown gerado
- `status` (Enum): Sucesso, Falhou, Ignorado
- `tamanho_bytes` (Integer): Tamanho do arquivo
- `timestamp` (DateTime): Quando foi extraída
- `erro_mensagem` (Text, nullable): Mensagem de erro se falhou
- **Relacionamento**: N-1 com Execução

### Exemplo de Dados no Banco

**Cenário**: Processo para extrair documentação do GitHub Copilot

```sql
-- Tabela: processo
INSERT INTO processo VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Docs GitHub Copilot',
  'Extração da documentação oficial do GitHub Copilot',
  'Ativo',
  '2026-02-28 10:00:00',
  '2026-02-28 10:00:00'
);

-- Tabela: configuracao
INSERT INTO configuracao VALUES (
  '550e8400-e29b-41d4-a716-446655440001',
  '550e8400-e29b-41d4-a716-446655440000',
  '["https://docs.github.com/en/copilot/get-started/quickstart", "https://docs.github.com/en/copilot/get-started/what-is-github-copilot"]',
  3600,
  3,
  'MULTIPLOS_ARQUIVOS',
  './output/github-copilot',
  '0 2 * * *',  -- Executa diariamente às 2h
  'RECORRENTE'
);

-- Tabela: execucao
INSERT INTO execucao VALUES (
  '550e8400-e29b-41d4-a716-446655440002',
  '550e8400-e29b-41d4-a716-446655440000',
  'Concluído',
  '2026-02-28 10:05:00',
  '2026-02-28 10:07:32',
  2,              -- 2 páginas processadas
  245760,         -- ~240KB extraídos
  0.0,            -- 0% de erro
  1               -- Primeira tentativa
);

-- Tabela: log
INSERT INTO log VALUES
  ('550e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440002', 'INFO', 'Iniciando extração do processo', '2026-02-28 10:05:00', NULL),
  ('550e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 'INFO', 'Processando URL: https://docs.github.com/en/copilot/get-started/quickstart', '2026-02-28 10:05:05', '{"url": "..."}'),
  ('550e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'INFO', 'Página extraída com sucesso', '2026-02-28 10:06:15', '{"size": 122880}'),
  ('550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'INFO', 'Processando URL: https://docs.github.com/en/copilot/get-started/what-is-github-copilot', '2026-02-28 10:06:20', NULL),
  ('550e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440002', 'INFO', 'Página extraída com sucesso', '2026-02-28 10:07:30', '{"size": 122880}'),
  ('550e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440002', 'INFO', 'Extração concluída com sucesso', '2026-02-28 10:07:32', '{"total_pages": 2, "total_size": 245760}');

-- Tabela: pagina_extraida
INSERT INTO pagina_extraida VALUES
  ('550e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440002', 'https://docs.github.com/en/copilot/get-started/quickstart', './output/github-copilot/quickstart.md', 'Sucesso', 122880, '2026-02-28 10:06:15', NULL),
  ('550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440002', 'https://docs.github.com/en/copilot/get-started/what-is-github-copilot', './output/github-copilot/what-is-github-copilot.md', 'Sucesso', 122880, '2026-02-28 10:07:30', NULL);
```

**Resultado**: 
- 1 Processo criado
- 1 Configuração com 2 URLs e agendamento diário
- 1 Execução concluída em ~2min30s
- 6 Logs registrados
- 2 Páginas extraídas com sucesso (240KB total)

## Configurações do Sistema

Definidas via variáveis de ambiente (`.env`):

```env
# Servidor
PORT=8000
HOST=0.0.0.0

# Banco de Dados
DATABASE_URL=sqlite:///./toninho.db

# Workers
MAX_CONCURRENT_PROCESSES=5
CELERY_BROKER_URL=redis://localhost:6379/0

# Extração
DEFAULT_TIMEOUT=3600  # 1 hora em segundos
MAX_RETRIES=3
MAX_SIZE_PER_EXTRACTION=1073741824  # 1GB em bytes
OUTPUT_DIR=./output

# Cache
CACHE_HTTP_REQUESTS=true
CACHE_EXPIRATION=3600

# Processamento
PARALLEL_THREADS=4

# Logs
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Testes

### Estratégia
- **Cobertura**: Mínimo 90%
- **Unit Tests**: Funções e métodos individuais (pytest)
- **Integration Tests**: Interação entre componentes (testcontainers)
- **Mock Server**: Para testar extração de sites
  - httpx-mock para requisições HTTP
  - Fixtures com respostas pré-definidas
  - Cenários: páginas estáticas, JS dinâmico, erros (404, 500, timeout)

### Ferramentas
- pytest + pytest-asyncio
- pytest-cov (cobertura)
- testcontainers (Redis, SQLite)
- httpx-mock (mocking HTTP)

## Escopo e Limitações

### MVP (Versão Inicial)
✅ Extração de URLs específicas (sem exploração automática)
✅ Single-user, uso local
✅ Armazenamento em filesystem local
✅ Logs apenas em stdout (não persistidos)
✅ Sem autenticação em sites
✅ Sem versionamento de dados
✅ Sem busca/filtros na UI
✅ Download de arquivos (sem preview)
✅ Deleção física (sem soft-delete)

### Fora do Escopo Inicial
❌ Exploração automática de sites (descoberta de páginas filhas)
❌ Notificações (email, webhooks, etc)
❌ Autenticação em sites (login, cookies, tokens)
❌ Seletores CSS/XPath customizados
❌ Transformações personalizadas
❌ Templates pré-configurados
❌ Dashboard de métricas (Grafana)
❌ Multi-usuário
❌ Integrações externas (Obsidian, Notion, etc)
❌ API pública para integração
❌ Preview de arquivos markdown na UI
❌ Busca e filtros avançados

## Tratamento de Erros

### Tipos de Erro
- **Recuperáveis**: Timeout, falha de rede, rate limiting
  - Ação: Retry com backoff exponencial (até 3 tentativas)
  
- **Irrecuperáveis**: 404, 403, conteúdo inválido, erro de parsing
  - Ação: Marcar como falho e alertar usuário

### Estratégias
- **Falha Parcial**: Salva dados extraídos até o momento, marca como "Concluído com Erros"
- **Timeout**: Interrompe processo após 1h (configurável), marca como falhado
- **Cancelamento**: Usuário pode cancelar, sistema limpa recursos alocados
- **Rate Limiting**: Backoff exponencial automático, monitora headers HTTP

## Guidelines de API REST

### Convenções de Rotas

Seguindo padrões RESTful e boas práticas:

```
Recurso: Processos
GET    /api/v1/processos              - Listar todos os processos
POST   /api/v1/processos              - Criar novo processo
GET    /api/v1/processos/{id}         - Obter detalhes de um processo
PUT    /api/v1/processos/{id}         - Atualizar processo completo
PATCH  /api/v1/processos/{id}         - Atualizar parcialmente
DELETE /api/v1/processos/{id}         - Deletar processo

Recurso: Execuções
GET    /api/v1/processos/{id}/execucoes           - Listar execuções do processo
POST   /api/v1/processos/{id}/execucoes           - Criar nova execução (executar)
GET    /api/v1/execucoes/{id}                     - Obter detalhes da execução
POST   /api/v1/execucoes/{id}/cancelar            - Cancelar execução
POST   /api/v1/execucoes/{id}/pausar              - Pausar execução
POST   /api/v1/execucoes/{id}/retomar             - Retomar execução

Recurso: Logs
GET    /api/v1/execucoes/{id}/logs                - Obter logs da execução
GET    /api/v1/execucoes/{id}/logs/stream         - Stream de logs (SSE)

Recurso: Páginas Extraídas
GET    /api/v1/execucoes/{id}/paginas             - Listar páginas extraídas
GET    /api/v1/paginas/{id}/download              - Download do arquivo markdown

Recurso: Métricas
GET    /api/v1/processos/{id}/metricas            - Métricas do processo
GET    /api/v1/execucoes/{id}/metricas            - Métricas da execução

Recurso: Agendamentos
GET    /api/v1/processos/{id}/agendamento         - Obter agendamento
PUT    /api/v1/processos/{id}/agendamento         - Configurar agendamento
DELETE /api/v1/processos/{id}/agendamento      - Remover agendamento

Health Check
GET    /api/v1/health                             - Status da API
GET    /api/v1/health/workers                     - Status dos workers
```

### HTTP Status Codes

**2xx - Sucesso**
- `200 OK`: Requisição bem-sucedida (GET, PUT, PATCH)
- `201 Created`: Recurso criado (POST)
- `204 No Content`: Sucesso sem conteúdo (DELETE)

**4xx - Erros do Cliente**
- `400 Bad Request`: Dados inválidos, validação falhou
- `404 Not Found`: Recurso não encontrado
- `409 Conflict`: Conflito (ex: processo já em execução)
- `422 Unprocessable Entity`: Validação Pydantic falhou
- `429 Too Many Requests`: Rate limiting atingido

**5xx - Erros do Servidor**
- `500 Internal Server Error`: Erro inesperado
- `503 Service Unavailable`: Serviço temporariamente indisponível (workers offline)

### Formato de Resposta

**Sucesso (200/201):**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nome": "Docs GitHub Copilot",
    "status": "Ativo",
    "criado_em": "2026-02-28T10:00:00Z"
  }
}
```

**Lista com Paginação:**
```json
{
  "data": [
    {"id": "...", "nome": "..."},
    {"id": "...", "nome": "..."}
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

**Erro (4xx/5xx):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos fornecidos",
    "details": [
      {
        "field": "url",
        "message": "URL inválida"
      }
    ]
  }
}
```

### Versionamento
- Versionamento via URL: `/api/v1/...`
- Facilita manutenção de múltiplas versões
- Breaking changes = nova versão (v2, v3, etc)

### Headers Importantes
- `Content-Type: application/json`
- `X-Request-ID`: UUID para rastreamento
- `X-RateLimit-Limit`: Limite de requisições
- `X-RateLimit-Remaining`: Requisições restantes

### Documentação Automática
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Próximos Passos

1. ✅ Definir escolha final de frontend (HTMX)
2. ☐ Criar repositório e estrutura inicial do projeto
3. ☐ Configurar ambiente de desenvolvimento (Poetry, Docker)
4. ☐ Implementar modelos e schemas básicos
5. ☐ Criar migrations iniciais com Alembic
6. ☐ Implementar serviços core (CRUD de processos)
7. ☐ Integrar Celery + Redis para workers
8. ☐ Integrar docling para extração
9. ☐ Criar endpoints REST básicos
10. ☐ Implementar UI inicial
11. ☐ Configurar testes e CI/CD
12. ☐ Criar Docker Compose para deploy

---

**Referências:**
- Docling: https://github.com/docling-project/docling
- FastAPI: https://fastapi.tiangolo.com/
- Celery: https://docs.celeryproject.org/
- SQLAlchemy: https://www.sqlalchemy.org/




