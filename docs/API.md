# 📖 Toninho — Referência Completa da API

> Documentação de referência da API REST do **Toninho — Processo de Extração**.
> Todos os endpoints, schemas, exemplos e códigos de erro.

---

## Índice

1. [Introdução](#1-introdução)
2. [Formato Padrão de Resposta](#2-formato-padrão-de-resposta)
3. [Resumo de Endpoints](#3-resumo-de-endpoints)
4. [Detalhamento por Grupo](#4-detalhamento-por-grupo)
   - 4.1 [Health & Info](#41-health--info)
   - 4.2 [Processos](#42-processos)
   - 4.3 [Configurações](#43-configurações)
   - 4.4 [Execuções](#44-execuções)
   - 4.5 [Páginas Extraídas](#45-páginas-extraídas)
   - 4.6 [Logs](#46-logs)
   - 4.7 [Monitoramento](#47-monitoramento)
5. [Fluxo de Uso (3 Passos)](#5-fluxo-de-uso-3-passos)
6. [Códigos de Erro](#6-códigos-de-erro)
7. [Funcionalidades Especiais](#7-funcionalidades-especiais)
8. [Enums e Valores Válidos](#8-enums-e-valores-válidos)

---

## 1. Introdução

| Item              | Valor                          |
| ----------------- | ------------------------------ |
| **Base URL**      | `http://localhost:8000`        |
| **Versionamento** | `/api/v1/`                     |
| **Formato**       | JSON (`application/json`)      |
| **Autenticação**  | Nenhuma (aplicação single-user)|
| **Docs interativa** | Swagger UI em `/docs`        |

Todas as requisições e respostas utilizam JSON, exceto endpoints de download que retornam `application/octet-stream`, `text/plain` ou `text/event-stream`.

Os campos de data/hora seguem o formato **ISO 8601** (ex.: `2024-01-15T10:30:00Z`).

Identificadores usam **UUID v4** (ex.: `550e8400-e29b-41d4-a716-446655440000`).

---

## 2. Formato Padrão de Resposta

### Resposta de Sucesso (item único)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nome": "Minha Extração",
    "status": "ativo",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Resposta de Sucesso (lista paginada)

```json
{
  "data": [
    { "id": "...", "nome": "Processo 1", "status": "ativo", "created_at": "..." },
    { "id": "...", "nome": "Processo 2", "status": "inativo", "created_at": "..." }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "total_pages": 3
  }
}
```

### Resposta de Erro

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Processo não encontrado",
    "details": [
      {
        "field": "id",
        "message": "Nenhum processo com o ID informado"
      }
    ]
  }
}
```

---

## 3. Resumo de Endpoints

### Health & Info

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/info` | Informações da API |

### Processos

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `POST` | `/api/v1/processos` | Criar processo |
| `GET` | `/api/v1/processos` | Listar processos |
| `GET` | `/api/v1/processos/{id}` | Obter processo |
| `GET` | `/api/v1/processos/{id}/detalhes` | Obter detalhes completos |
| `PUT` | `/api/v1/processos/{id}` | Atualizar processo |
| `PATCH` | `/api/v1/processos/{id}` | Atualizar parcialmente |
| `DELETE` | `/api/v1/processos/{id}` | Deletar processo |
| `GET` | `/api/v1/processos/{id}/metricas` | Métricas agregadas |

### Configurações

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `POST` | `/api/v1/processos/{id}/configuracoes` | Criar configuração |
| `GET` | `/api/v1/processos/{id}/configuracoes` | Listar histórico de configurações |
| `GET` | `/api/v1/processos/{id}/configuracao` | Obter configuração atual |
| `GET` | `/api/v1/configuracoes/{id}` | Obter configuração por ID |
| `PUT` | `/api/v1/configuracoes/{id}` | Atualizar configuração |
| `DELETE` | `/api/v1/configuracoes/{id}` | Deletar configuração |
| `GET` | `/api/v1/configuracoes/{id}/validar-agendamento` | Validar expressão cron |

### Execuções

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `POST` | `/api/v1/processos/{id}/execucoes` | Criar e iniciar execução |
| `GET` | `/api/v1/processos/{id}/execucoes` | Listar execuções do processo |
| `GET` | `/api/v1/execucoes` | Listar todas as execuções |
| `GET` | `/api/v1/execucoes/{id}` | Obter execução |
| `GET` | `/api/v1/execucoes/{id}/detalhes` | Detalhes completos da execução |
| `PATCH` | `/api/v1/execucoes/{id}/status` | Atualizar status |
| `POST` | `/api/v1/execucoes/{id}/cancelar` | Cancelar execução |
| `POST` | `/api/v1/execucoes/{id}/pausar` | Pausar execução |
| `POST` | `/api/v1/execucoes/{id}/retomar` | Retomar execução pausada |
| `GET` | `/api/v1/execucoes/{id}/progresso` | Progresso em tempo real |
| `GET` | `/api/v1/execucoes/{id}/metricas` | Métricas detalhadas |
| `DELETE` | `/api/v1/execucoes/{id}` | Deletar execução |

### Páginas Extraídas

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `POST` | `/api/v1/paginas` | Criar página (uso interno) |
| `POST` | `/api/v1/paginas/batch` | Criar múltiplas em lote |
| `GET` | `/api/v1/execucoes/{id}/paginas` | Listar páginas da execução |
| `GET` | `/api/v1/execucoes/{id}/paginas/estatisticas` | Estatísticas de páginas |
| `GET` | `/api/v1/execucoes/{id}/download-all` | Download ZIP de todas as páginas |
| `GET` | `/api/v1/paginas/{id}` | Obter metadados da página |
| `GET` | `/api/v1/paginas/{id}/download` | Download do arquivo markdown |
| `GET` | `/api/v1/paginas/{id}/content` | Conteúdo como texto |
| `DELETE` | `/api/v1/paginas/{id}` | Deletar página |

### Logs

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `POST` | `/api/v1/logs` | Criar log (uso interno) |
| `POST` | `/api/v1/logs/batch` | Criar múltiplos em lote |
| `GET` | `/api/v1/execucoes/{id}/logs` | Listar logs da execução |
| `GET` | `/api/v1/execucoes/{id}/logs/recentes` | Últimos N logs |
| `GET` | `/api/v1/execucoes/{id}/logs/estatisticas` | Estatísticas de logs |
| `GET` | `/api/v1/execucoes/{id}/logs/stream` | Streaming de logs (SSE) |
| `GET` | `/api/v1/logs/{id}` | Obter log por ID |

### Monitoramento

| Método | Caminho | Descrição |
| ------ | ------- | --------- |
| `GET` | `/api/v1/monitoring/health` | Health check completo |
| `GET` | `/api/v1/monitoring/health/live` | Liveness probe |
| `GET` | `/api/v1/monitoring/health/ready` | Readiness probe |
| `GET` | `/api/v1/monitoring/metrics` | Métricas do sistema |
| `WebSocket` | `/api/v1/monitoring/ws` | Updates globais em tempo real |
| `WebSocket` | `/api/v1/monitoring/ws/execucao/{id}` | Updates de uma execução |

---

## 4. Detalhamento por Grupo

---

### 4.1 Health & Info

#### `GET /api/v1/health`

Health check simples da aplicação.

**Resposta `200 OK`:**

```json
{
  "status": "healthy",
  "service": "toninho"
}
```

**cURL:**

```bash
curl http://localhost:8000/api/v1/health
```

---

#### `GET /api/v1/info`

Informações gerais da API.

**Resposta `200 OK`:**

```json
{
  "name": "Toninho",
  "version": "0.1.0",
  "status": "operational",
  "docs": "/docs"
}
```

**cURL:**

```bash
curl http://localhost:8000/api/v1/info
```

---

### 4.2 Processos

Tag: **Processos**

#### `POST /api/v1/processos`

Cria um novo processo de extração.

**Request Body** — `ProcessoCreate`:

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| ----- | ---- | ----------- | ------ | --------- |
| `nome` | `string` | ✅ | — | Nome do processo (1-200 caracteres, único) |
| `descricao` | `string \| null` | ❌ | `null` | Descrição opcional |
| `status` | `ProcessoStatus` | ❌ | `"ativo"` | Status inicial |

**Resposta `201 Created`:**

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "nome": "Minha Extração",
    "descricao": null,
    "status": "ativo",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Erros:**

| Código | Motivo |
| ------ | ------ |
| `400` | Dados inválidos (nome vazio, etc.) |
| `409` | Nome duplicado |

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/processos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Minha Extração", "descricao": "Extração de documentos"}'
```

---

#### `GET /api/v1/processos`

Lista processos com paginação, filtros e ordenação.

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
| --------- | ---- | ------ | --------- |
| `page` | `int` (≥1) | `1` | Página atual |
| `per_page` | `int` (1-100) | `20` | Itens por página |
| `status` | `ProcessoStatus` | — | Filtrar por status |
| `busca` | `string` | — | Busca textual no nome/descrição |
| `order_by` | `string` | `"created_at"` | Campo de ordenação |
| `order_dir` | `"asc" \| "desc"` | `"desc"` | Direção da ordenação |

**Resposta `200 OK`:**

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "nome": "Minha Extração",
      "status": "ativo",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

**cURL:**

```bash
curl "http://localhost:8000/api/v1/processos?page=1&per_page=10&status=ativo&busca=extracao"
```

---

#### `GET /api/v1/processos/{processo_id}`

Obtém um processo pelo ID.

**Path Parameters:**

| Parâmetro | Tipo | Descrição |
| --------- | ---- | --------- |
| `processo_id` | `UUID` | ID do processo |

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-...",
    "nome": "Minha Extração",
    "descricao": "Extração de documentos",
    "status": "ativo",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Erros:** `404` — Processo não encontrado.

---

#### `GET /api/v1/processos/{processo_id}/detalhes`

Obtém detalhes completos do processo, incluindo configurações e execuções recentes.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-...",
    "nome": "Minha Extração",
    "descricao": "Extração de documentos",
    "status": "ativo",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "configuracoes": [
      {
        "id": "...",
        "urls": ["https://example.com"],
        "timeout": 3600,
        "output_dir": "./output"
      }
    ],
    "execucoes_recentes": [
      {
        "id": "...",
        "status": "concluido",
        "iniciado_em": "2024-01-15T11:00:00Z",
        "finalizado_em": "2024-01-15T11:05:00Z",
        "duracao_segundos": 300.0
      }
    ],
    "total_execucoes": 10,
    "ultima_execucao_em": "2024-01-15T11:00:00Z"
  }
}
```

---

#### `PUT /api/v1/processos/{processo_id}`

Atualiza todos os campos de um processo.

**Request Body** — `ProcessoUpdate`:

| Campo | Tipo | Obrigatório | Descrição |
| ----- | ---- | ----------- | --------- |
| `nome` | `string \| null` | ❌ | Novo nome (1-200 caracteres) |
| `descricao` | `string \| null` | ❌ | Nova descrição |
| `status` | `ProcessoStatus \| null` | ❌ | Novo status |

**Resposta `200 OK`:** `SuccessResponse[ProcessoResponse]`

**Erros:** `404`, `409` (nome duplicado).

**cURL:**

```bash
curl -X PUT http://localhost:8000/api/v1/processos/a1b2c3d4-... \
  -H "Content-Type: application/json" \
  -d '{"nome": "Nome Atualizado", "status": "inativo"}'
```

---

#### `PATCH /api/v1/processos/{processo_id}`

Atualização parcial — envia apenas os campos que deseja alterar.

**Request Body:** Mesmo schema de `ProcessoUpdate`, mas somente os campos enviados são atualizados.

**Resposta `200 OK`:** `SuccessResponse[ProcessoResponse]`

**cURL:**

```bash
curl -X PATCH http://localhost:8000/api/v1/processos/a1b2c3d4-... \
  -H "Content-Type: application/json" \
  -d '{"status": "arquivado"}'
```

---

#### `DELETE /api/v1/processos/{processo_id}`

Remove um processo e todos os seus dados associados.

**Resposta `204 No Content`** — Sem corpo de resposta.

**Erros:** `404` — Processo não encontrado.

**cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/processos/a1b2c3d4-...
```

---

#### `GET /api/v1/processos/{processo_id}/metricas`

Retorna métricas agregadas do processo.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "processo_id": "a1b2c3d4-...",
    "total_execucoes": 15,
    "execucoes_sucesso": 12,
    "execucoes_falha": 3,
    "taxa_sucesso": 80.0,
    "tempo_medio_execucao_segundos": 245.5,
    "total_paginas_extraidas": 1500,
    "total_bytes_extraidos": 52428800,
    "ultima_execucao_em": "2024-01-15T11:00:00Z"
  }
}
```

---

### 4.3 Configurações

Tag: **Configurações**

#### `POST /api/v1/processos/{processo_id}/configuracoes`

Cria uma nova configuração para o processo. Cada processo pode ter múltiplas configurações (histórico), mas somente a mais recente é a "atual".

**Path Parameters:**

| Parâmetro | Tipo | Descrição |
| --------- | ---- | --------- |
| `processo_id` | `UUID` | ID do processo |

**Request Body** — `ConfiguracaoCreate`:

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| ----- | ---- | ----------- | ------ | --------- |
| `urls` | `list[string]` | ✅ | — | Lista de URLs para extrair (1-100 itens) |
| `timeout` | `int` | ❌ | `3600` | Timeout em segundos (1-86400) |
| `max_retries` | `int` | ❌ | `3` | Número máximo de tentativas (0-10) |
| `formato_saida` | `FormatoSaida` | ❌ | `"multiplos_arquivos"` | Formato de saída |
| `output_dir` | `string` | ✅ | — | Diretório de saída |
| `agendamento_cron` | `string \| null` | ❌ | `null` | Expressão cron (obrigatório se `agendamento_tipo` = `"recorrente"`) |
| `agendamento_tipo` | `AgendamentoTipo` | ❌ | `"manual"` | Tipo de agendamento |
| `use_browser` | `bool` | ❌ | `false` | Usar Playwright para renderização JS |
| `metodo_extracao` | `MetodoExtracao` | ❌ | `"html2text"` | Método de extração |

**Validações:**

- URLs devem ser válidas (http/https)
- Se `agendamento_tipo` = `"recorrente"`, o campo `agendamento_cron` é obrigatório
- `output_dir` deve ser um caminho válido
- `timeout` deve estar entre 1 e 86400 segundos

**Resposta `201 Created`:**

```json
{
  "success": true,
  "data": {
    "id": "b2c3d4e5-...",
    "processo_id": "a1b2c3d4-...",
    "urls": ["https://example.com", "https://docs.example.com"],
    "timeout": 3600,
    "max_retries": 3,
    "formato_saida": "multiplos_arquivos",
    "output_dir": "./output",
    "agendamento_cron": null,
    "agendamento_tipo": "manual",
    "use_browser": false,
    "metodo_extracao": "html2text",
    "created_at": "2024-01-15T10:35:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

**Erros:** `404` (processo não encontrado), `400` (dados inválidos).

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/processos/a1b2c3d4-.../configuracoes \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://docs.example.com"],
    "timeout": 3600,
    "output_dir": "./output",
    "metodo_extracao": "html2text"
  }'
```

---

#### `GET /api/v1/processos/{processo_id}/configuracoes`

Lista o histórico de configurações do processo (ordenadas da mais recente para a mais antiga).

**Resposta `200 OK`:** `SuccessResponse[list[ConfiguracaoResponse]]`

---

#### `GET /api/v1/processos/{processo_id}/configuracao`

Obtém a configuração **atual** (mais recente) do processo.

> **Nota:** Este endpoint usa a forma singular `/configuracao` (sem "s" no final).

**Resposta `200 OK`:** `SuccessResponse[ConfiguracaoResponse]`

**Erros:** `404` — Processo não encontrado ou sem configuração.

**cURL:**

```bash
curl http://localhost:8000/api/v1/processos/a1b2c3d4-.../configuracao
```

---

#### `GET /api/v1/configuracoes/{config_id}`

Obtém uma configuração específica pelo seu ID.

**Resposta `200 OK`:** `SuccessResponse[ConfiguracaoResponse]`

---

#### `PUT /api/v1/configuracoes/{config_id}`

Atualiza uma configuração existente.

**Request Body** — `ConfiguracaoUpdate`:

Todos os campos de `ConfiguracaoCreate`, porém todos são opcionais. Somente os campos enviados são atualizados.

**Resposta `200 OK`:** `SuccessResponse[ConfiguracaoResponse]`

**cURL:**

```bash
curl -X PUT http://localhost:8000/api/v1/configuracoes/b2c3d4e5-... \
  -H "Content-Type: application/json" \
  -d '{"timeout": 7200, "max_retries": 5}'
```

---

#### `DELETE /api/v1/configuracoes/{config_id}`

Remove uma configuração.

**Resposta `204 No Content`**

---

#### `GET /api/v1/configuracoes/{config_id}/validar-agendamento`

Valida a expressão cron da configuração e retorna as próximas execuções agendadas.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "expressao_cron": "0 */6 * * *",
    "valida": true,
    "proximas_execucoes": [
      "2024-01-15T12:00:00Z",
      "2024-01-15T18:00:00Z",
      "2024-01-16T00:00:00Z",
      "2024-01-16T06:00:00Z",
      "2024-01-16T12:00:00Z"
    ],
    "descricao_legivel": "A cada 6 horas"
  }
}
```

---

### 4.4 Execuções

Tag: **Execuções**

#### `POST /api/v1/processos/{processo_id}/execucoes`

Cria e inicia uma nova execução para o processo. O processo deve ter uma configuração ativa.

**Path Parameters:**

| Parâmetro | Tipo | Descrição |
| --------- | ---- | --------- |
| `processo_id` | `UUID` | ID do processo |

**Resposta `201 Created`:**

```json
{
  "success": true,
  "data": {
    "id": "c3d4e5f6-...",
    "processo_id": "a1b2c3d4-...",
    "status": "aguardando",
    "iniciado_em": null,
    "finalizado_em": null,
    "paginas_processadas": 0,
    "bytes_extraidos": 0,
    "taxa_erro": 0.0,
    "tentativa_atual": 1,
    "duracao_segundos": null,
    "em_andamento": true,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

**Erros:**

| Código | Motivo |
| ------ | ------ |
| `404` | Processo não encontrado |
| `400` | Sem configuração ativa |
| `409` | Já existe uma execução em andamento |

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/processos/a1b2c3d4-.../execucoes
```

---

#### `GET /api/v1/processos/{processo_id}/execucoes`

Lista execuções de um processo específico.

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
| --------- | ---- | ------ | --------- |
| `page` | `int` (≥1) | `1` | Página |
| `per_page` | `int` (1-100) | `20` | Itens por página |
| `status` | `ExecucaoStatus` | — | Filtrar por status |

**Resposta `200 OK`:** `SuccessListResponse[ExecucaoSummary]`

---

#### `GET /api/v1/execucoes`

Lista todas as execuções do sistema.

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
| --------- | ---- | ------ | --------- |
| `page` | `int` (≥1) | `1` | Página |
| `per_page` | `int` (1-100) | `20` | Itens por página |
| `status` | `ExecucaoStatus` | — | Filtrar por status |
| `ordem` | `"asc" \| "desc"` | `"desc"` | Direção da ordenação |

**Resposta `200 OK`:**

```json
{
  "data": [
    {
      "id": "c3d4e5f6-...",
      "status": "concluido",
      "iniciado_em": "2024-01-15T11:00:00Z",
      "finalizado_em": "2024-01-15T11:05:00Z",
      "paginas_processadas": 25,
      "duracao_segundos": 300.123
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 3,
    "total_pages": 1
  }
}
```

**cURL:**

```bash
curl "http://localhost:8000/api/v1/execucoes?status=concluido&ordem=desc"
```

---

#### `GET /api/v1/execucoes/{execucao_id}`

Obtém informações básicas de uma execução.

**Resposta `200 OK`:** `SuccessResponse[ExecucaoResponse]`

**Campos computados:**

| Campo | Tipo | Descrição |
| ----- | ---- | --------- |
| `duracao_segundos` | `float \| null` | Duração calculada entre `iniciado_em` e `finalizado_em` (arredondada a 3 casas decimais) |
| `em_andamento` | `bool` | `true` se status é `aguardando` ou `em_execucao` |

---

#### `GET /api/v1/execucoes/{execucao_id}/detalhes`

Obtém detalhes completos da execução, incluindo métricas.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "id": "c3d4e5f6-...",
    "processo_id": "a1b2c3d4-...",
    "status": "concluido",
    "iniciado_em": "2024-01-15T11:00:00Z",
    "finalizado_em": "2024-01-15T11:05:00Z",
    "paginas_processadas": 25,
    "bytes_extraidos": 1048576,
    "taxa_erro": 4.0,
    "tentativa_atual": 1,
    "duracao_segundos": 300.123,
    "em_andamento": false,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:05:00Z",
    "metricas": {
      "execucao_id": "c3d4e5f6-...",
      "paginas_processadas": 25,
      "bytes_extraidos": 1048576,
      "taxa_erro": 4.0,
      "taxa_sucesso": 96.0,
      "duracao_segundos": 300,
      "tempo_medio_por_pagina_segundos": 12.0
    }
  }
}
```

---

#### `PATCH /api/v1/execucoes/{execucao_id}/status`

Atualiza o status de uma execução manualmente.

**Request Body** — `ExecucaoStatusUpdate`:

| Campo | Tipo | Obrigatório | Descrição |
| ----- | ---- | ----------- | --------- |
| `status` | `ExecucaoStatus` | ✅ | Novo status |

**Resposta `200 OK`:** `SuccessResponse[ExecucaoResponse]`

**Erros:** `400` (transição de status inválida), `404`.

**cURL:**

```bash
curl -X PATCH http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../status \
  -H "Content-Type: application/json" \
  -d '{"status": "concluido"}'
```

---

#### `POST /api/v1/execucoes/{execucao_id}/cancelar`

Cancela uma execução em andamento.

**Resposta `200 OK`:** `SuccessResponse[ExecucaoResponse]` — Com status `"cancelado"`.

**Erros:** `409` — Execução não está em andamento.

**cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../cancelar
```

---

#### `POST /api/v1/execucoes/{execucao_id}/pausar`

Pausa uma execução em andamento.

**Resposta `200 OK`:** `SuccessResponse[ExecucaoResponse]` — Com status `"pausado"`.

**Erros:** `409` — Execução não está em andamento.

---

#### `POST /api/v1/execucoes/{execucao_id}/retomar`

Retoma uma execução que foi pausada.

**Resposta `200 OK`:** `SuccessResponse[ExecucaoResponse]` — Com status `"em_execucao"`.

**Erros:** `409` — Execução não está pausada.

---

#### `GET /api/v1/execucoes/{execucao_id}/progresso`

Retorna o progresso em tempo real da execução.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "execucao_id": "c3d4e5f6-...",
    "status": "em_execucao",
    "paginas_processadas": 15,
    "total_paginas": 25,
    "progresso_percentual": 60.0,
    "tempo_decorrido_segundos": 180,
    "tempo_estimado_restante_segundos": 120,
    "ultima_atualizacao": "2024-01-15T11:03:00Z"
  }
}
```

---

#### `GET /api/v1/execucoes/{execucao_id}/metricas`

Retorna métricas detalhadas da execução.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "execucao_id": "c3d4e5f6-...",
    "paginas_processadas": 25,
    "bytes_extraidos": 1048576,
    "taxa_erro": 4.0,
    "taxa_sucesso": 96.0,
    "duracao_segundos": 300,
    "tempo_medio_por_pagina_segundos": 12.0
  }
}
```

---

#### `DELETE /api/v1/execucoes/{execucao_id}`

Remove uma execução e seus dados associados (páginas, logs).

**Resposta `204 No Content`**

**Erros:** `404`.

---

### 4.5 Páginas Extraídas

Tag: **Páginas Extraídas**

#### `POST /api/v1/paginas`

Cria um registro de página extraída. **Uso interno dos workers.**

**Request Body** — `PaginaExtraidaCreate`:

| Campo | Tipo | Obrigatório | Padrão | Descrição |
| ----- | ---- | ----------- | ------ | --------- |
| `execucao_id` | `UUID` | ✅ | — | ID da execução |
| `url_original` | `string` | ✅ | — | URL original da página |
| `caminho_arquivo` | `string` | ✅ | — | Caminho do arquivo salvo |
| `status` | `PaginaStatus` | ✅ | — | Status da extração |
| `tamanho_bytes` | `int` (≥0) | ❌ | `0` | Tamanho em bytes |
| `erro_mensagem` | `string \| null` | Condicional | `null` | Obrigatório se `status` = `"falhou"` |

**Resposta `201 Created`:** `SuccessResponse[PaginaExtraidaResponse]`

---

#### `POST /api/v1/paginas/batch`

Cria múltiplas páginas em lote. **Uso interno dos workers.**

**Request Body:** `list[PaginaExtraidaCreate]`

**Resposta `201 Created`:** `SuccessResponse[list[PaginaExtraidaResponse]]`

---

#### `GET /api/v1/execucoes/{execucao_id}/paginas`

Lista páginas extraídas de uma execução.

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
| --------- | ---- | ------ | --------- |
| `page` | `int` (≥1) | `1` | Página |
| `per_page` | `int` (1-100) | `20` | Itens por página |
| `status` | `PaginaStatus` | — | Filtrar por status |

**Resposta `200 OK`:**

```json
{
  "data": [
    {
      "id": "d4e5f6a7-...",
      "url_original": "https://example.com/page1",
      "status": "sucesso",
      "tamanho_bytes": 45678,
      "tamanho_legivel": "44.6 KB"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 25,
    "total_pages": 2
  }
}
```

---

#### `GET /api/v1/execucoes/{execucao_id}/paginas/estatisticas`

Estatísticas das páginas de uma execução.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "execucao_id": "c3d4e5f6-...",
    "total": 25,
    "sucesso": 24,
    "falhou": 1,
    "ignorado": 0,
    "taxa_sucesso": 96.0,
    "tamanho_total_bytes": 1048576,
    "tamanho_medio_bytes": 41943.04,
    "maior_pagina_bytes": 102400,
    "menor_pagina_bytes": 1024
  }
}
```

---

#### `GET /api/v1/execucoes/{execucao_id}/download-all`

Faz download de todas as páginas extraídas em um arquivo ZIP.

**Resposta `200 OK`:**

- **Content-Type:** `application/zip`
- **Content-Disposition:** `attachment; filename="execucao_{id}_paginas.zip"`

**cURL:**

```bash
curl -o paginas.zip http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../download-all
```

---

#### `GET /api/v1/paginas/{pagina_id}`

Obtém metadados de uma página extraída.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "id": "d4e5f6a7-...",
    "execucao_id": "c3d4e5f6-...",
    "url_original": "https://example.com/page1",
    "caminho_arquivo": "./output/page1.md",
    "status": "sucesso",
    "tamanho_bytes": 45678,
    "tamanho_legivel": "44.6 KB",
    "timestamp": "2024-01-15T11:02:00Z",
    "erro_mensagem": null,
    "download_url": "/api/v1/paginas/d4e5f6a7-.../download",
    "preview_disponivel": true
  }
}
```

**Campos computados:**

| Campo | Tipo | Descrição |
| ----- | ---- | --------- |
| `tamanho_legivel` | `string` | Tamanho formatado (B, KB, MB, GB, TB) |
| `download_url` | `string` | URL para download do arquivo |
| `preview_disponivel` | `bool` | `true` se tamanho < 1 MB |

---

#### `GET /api/v1/paginas/{pagina_id}/download`

Faz download do arquivo markdown da página.

**Resposta `200 OK`:**

- **Content-Type:** `application/octet-stream`

**cURL:**

```bash
curl -o pagina.md http://localhost:8000/api/v1/paginas/d4e5f6a7-.../download
```

---

#### `GET /api/v1/paginas/{pagina_id}/content`

Retorna o conteúdo da página como texto puro.

**Resposta `200 OK`:**

- **Content-Type:** `text/plain`

**cURL:**

```bash
curl http://localhost:8000/api/v1/paginas/d4e5f6a7-.../content
```

---

#### `DELETE /api/v1/paginas/{pagina_id}`

Remove uma página extraída.

**Resposta `204 No Content`**

---

### 4.6 Logs

Tag: **Logs**

#### `POST /api/v1/logs`

Cria um registro de log. **Uso interno dos workers.**

**Request Body** — `LogCreate`:

| Campo | Tipo | Obrigatório | Descrição |
| ----- | ---- | ----------- | --------- |
| `execucao_id` | `UUID` | ✅ | ID da execução |
| `nivel` | `LogNivel` | ✅ | Nível do log |
| `mensagem` | `string` | ✅ | Mensagem (min. 1 caractere) |
| `contexto` | `dict \| null` | ❌ | Dados estruturados adicionais (JSON) |

**Resposta `201 Created`:**

```json
{
  "success": true,
  "data": {
    "id": "e5f6a7b8-...",
    "execucao_id": "c3d4e5f6-...",
    "nivel": "info",
    "mensagem": "Iniciando extração da página https://example.com",
    "timestamp": "2024-01-15T11:01:00Z",
    "contexto": {
      "url": "https://example.com",
      "tentativa": 1
    }
  }
}
```

---

#### `POST /api/v1/logs/batch`

Cria múltiplos logs em lote. **Uso interno dos workers.**

**Request Body:** `list[LogCreate]`

**Resposta `201 Created`:** `SuccessResponse[list[LogResponse]]`

---

#### `GET /api/v1/execucoes/{execucao_id}/logs`

Lista logs de uma execução com filtros avançados.

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
| --------- | ---- | ------ | --------- |
| `page` | `int` (≥1) | `1` | Página |
| `per_page` | `int` (1-100) | `20` | Itens por página |
| `nivel` | `LogNivel` | — | Filtrar por nível |
| `desde` | `datetime` (ISO 8601) | — | Data/hora inicial |
| `ate` | `datetime` (ISO 8601) | — | Data/hora final |
| `busca` | `string` | — | Busca textual na mensagem (case-insensitive) |

**Resposta `200 OK`:** `SuccessListResponse[LogResponse]`

**cURL:**

```bash
curl "http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../logs?nivel=error&busca=timeout&page=1&per_page=50"
```

---

#### `GET /api/v1/execucoes/{execucao_id}/logs/recentes`

Retorna os últimos N logs de uma execução.

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
| --------- | ---- | ------ | --------- |
| `limit` | `int` (1-100) | `20` | Quantidade de logs |

**Resposta `200 OK`:** `SuccessResponse[list[LogResponse]]`

**cURL:**

```bash
curl "http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../logs/recentes?limit=50"
```

---

#### `GET /api/v1/execucoes/{execucao_id}/logs/estatisticas`

Estatísticas dos logs de uma execução.

**Resposta `200 OK`:**

```json
{
  "success": true,
  "data": {
    "execucao_id": "c3d4e5f6-...",
    "total": 150,
    "por_nivel": {
      "debug": 50,
      "info": 80,
      "warning": 15,
      "error": 5
    },
    "percentual_erros": 3.33,
    "primeiro_log": "2024-01-15T11:00:01Z",
    "ultimo_log": "2024-01-15T11:05:00Z"
  }
}
```

---

#### `GET /api/v1/execucoes/{execucao_id}/logs/stream`

Streaming de logs em tempo real via **Server-Sent Events (SSE)**.

**Resposta `200 OK`:**

- **Content-Type:** `text/event-stream`

Cada evento segue o formato SSE:

```
data: {"id": "...", "nivel": "info", "mensagem": "Processando página 5/25", "timestamp": "..."}

data: {"id": "...", "nivel": "info", "mensagem": "Processando página 6/25", "timestamp": "..."}
```

**cURL:**

```bash
curl -N http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../logs/stream
```

**JavaScript:**

```javascript
const source = new EventSource(
  "http://localhost:8000/api/v1/execucoes/c3d4e5f6-.../logs/stream"
);
source.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.nivel}] ${log.mensagem}`);
};
```

---

#### `GET /api/v1/logs/{log_id}`

Obtém um log específico pelo seu ID.

**Resposta `200 OK`:** `SuccessResponse[LogResponse]`

---

### 4.7 Monitoramento

Tag: **Monitoramento**

#### `GET /api/v1/monitoring/health`

Health check completo com status de cada componente do sistema.

**Resposta `200 OK`:**

```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "filesystem": "healthy"
  }
}
```

---

#### `GET /api/v1/monitoring/health/live`

Liveness probe para orquestração de containers (Kubernetes, Docker).

**Resposta `200 OK`:**

```json
{
  "status": "alive"
}
```

---

#### `GET /api/v1/monitoring/health/ready`

Readiness probe. Retorna `503` se o sistema não estiver pronto.

**Resposta `200 OK`:**

```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "filesystem": "healthy"
  }
}
```

**Resposta `503 Service Unavailable`:**

```json
{
  "status": "unhealthy",
  "components": {
    "database": "unhealthy",
    "filesystem": "healthy"
  }
}
```

---

#### `GET /api/v1/monitoring/metrics`

Métricas do sistema para dashboards de monitoramento.

**Resposta `200 OK`:**

```json
{
  "execucoes": {
    "total": 100,
    "em_andamento": 2,
    "concluidas": 85,
    "falhas": 13
  },
  "taxa_sucesso": 85.0,
  "duracao_media_segundos": 245.5,
  "atividade_recente": {
    "ultimas_24h": 5,
    "ultima_semana": 20
  }
}
```

**cURL:**

```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

---

#### `WebSocket /api/v1/monitoring/ws`

WebSocket para receber atualizações globais em tempo real (todas as execuções).

**Conexão:**

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/monitoring/ws");
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log("Atualização:", update);
};
```

**Mensagens recebidas:**

```json
{
  "type": "execution_update",
  "data": {
    "execucao_id": "c3d4e5f6-...",
    "status": "em_execucao",
    "progresso": 60.0
  }
}
```

---

#### `WebSocket /api/v1/monitoring/ws/execucao/{execucao_id}`

WebSocket para acompanhar uma execução específica em tempo real.

**Conexão:**

```javascript
const ws = new WebSocket(
  "ws://localhost:8000/api/v1/monitoring/ws/execucao/c3d4e5f6-..."
);
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Recebe: status, progresso, novos logs
};
```

---

## 5. Fluxo de Uso (3 Passos)

### Passo 1 — Criar o Processo

```bash
curl -X POST http://localhost:8000/api/v1/processos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Minha Extração"}'
```

> Anote o `id` retornado em `data.id`.

### Passo 2 — Configurar as URLs

```bash
curl -X POST http://localhost:8000/api/v1/processos/{id}/configuracoes \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://docs.example.com/guide"],
    "timeout": 3600,
    "output_dir": "./output",
    "metodo_extracao": "html2text",
    "formato_saida": "multiplos_arquivos"
  }'
```

### Passo 3 — Executar

```bash
curl -X POST http://localhost:8000/api/v1/processos/{id}/execucoes
```

### Acompanhar o Progresso

```bash
# Polling do progresso
curl http://localhost:8000/api/v1/execucoes/{execucao_id}/progresso

# Streaming de logs em tempo real
curl -N http://localhost:8000/api/v1/execucoes/{execucao_id}/logs/stream
```

### Baixar os Resultados

```bash
# Download de todas as páginas em ZIP
curl -o resultado.zip http://localhost:8000/api/v1/execucoes/{execucao_id}/download-all

# Ou ver o conteúdo de uma página específica
curl http://localhost:8000/api/v1/paginas/{pagina_id}/content
```

---

## 6. Códigos de Erro

### Códigos HTTP

| Código | Significado | Quando ocorre |
| ------ | ----------- | ------------- |
| `200` | OK | Operações de leitura e atualização bem-sucedidas |
| `201` | Created | Recurso criado com sucesso |
| `204` | No Content | Recurso deletado com sucesso |
| `400` | Bad Request | Dados inválidos, validação falhou |
| `404` | Not Found | Recurso não encontrado |
| `409` | Conflict | Nome duplicado, transição de status inválida, execução já em andamento |
| `422` | Unprocessable Entity | Erro de validação do corpo da requisição (FastAPI) |
| `503` | Service Unavailable | Sistema não está pronto (readiness check) |

### Códigos de Erro da Aplicação

| Código | Descrição |
| ------ | --------- |
| `NOT_FOUND` | Recurso não encontrado |
| `VALIDATION_ERROR` | Erro de validação dos dados |
| `CONFLICT` | Conflito com estado atual do recurso |
| `INTERNAL_ERROR` | Erro interno do servidor |

### Exemplo de Resposta de Erro

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos",
    "details": [
      {
        "field": "nome",
        "message": "O campo nome é obrigatório e não pode estar vazio"
      },
      {
        "field": "urls",
        "message": "Pelo menos uma URL deve ser informada"
      }
    ]
  }
}
```

---

## 7. Funcionalidades Especiais

### 7.1 Server-Sent Events (SSE)

O endpoint `GET /api/v1/execucoes/{id}/logs/stream` utiliza SSE para enviar logs em tempo real.

**Características:**

- Conexão HTTP de longa duração
- Formato `text/event-stream`
- Reconexão automática pelo navegador
- Cada evento contém um log serializado em JSON

**Exemplo com `EventSource` (JavaScript):**

```javascript
const source = new EventSource(
  "http://localhost:8000/api/v1/execucoes/{id}/logs/stream"
);

source.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.nivel.toUpperCase()}] ${log.mensagem}`);
};

source.onerror = () => {
  console.log("Conexão encerrada ou erro");
  source.close();
};
```

### 7.2 WebSocket

Dois endpoints WebSocket disponíveis para monitoramento em tempo real:

| Endpoint | Descrição |
| -------- | --------- |
| `/api/v1/monitoring/ws` | Atualizações de todas as execuções |
| `/api/v1/monitoring/ws/execucao/{id}` | Atualizações de uma execução específica |

**Exemplo de conexão:**

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/monitoring/ws");

ws.onopen = () => console.log("Conectado");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Update:", data.type, data.data);
};
ws.onclose = () => console.log("Desconectado");
```

### 7.3 Paginação

Todos os endpoints de listagem suportam paginação via query parameters:

| Parâmetro | Tipo | Padrão | Limites | Descrição |
| --------- | ---- | ------ | ------- | --------- |
| `page` | `int` | `1` | ≥ 1 | Número da página (1-indexed) |
| `per_page` | `int` | `20` | 1-100 | Itens por página |

A resposta inclui o objeto `meta` com informações de paginação:

```json
{
  "meta": {
    "page": 2,
    "per_page": 20,
    "total": 95,
    "total_pages": 5
  }
}
```

### 7.4 Filtros e Busca

**Processos:**

- `status` — Filtrar por `ProcessoStatus`
- `busca` — Busca textual no nome e descrição
- `order_by` — Campo de ordenação (ex.: `created_at`, `nome`)
- `order_dir` — Direção: `asc` ou `desc`

**Execuções:**

- `status` — Filtrar por `ExecucaoStatus`
- `ordem` — Direção: `asc` ou `desc`

**Páginas:**

- `status` — Filtrar por `PaginaStatus`

**Logs:**

- `nivel` — Filtrar por `LogNivel`
- `desde` / `ate` — Intervalo de data/hora (ISO 8601)
- `busca` — Busca textual na mensagem (case-insensitive)

### 7.5 Downloads

| Endpoint | Content-Type | Descrição |
| -------- | ------------ | --------- |
| `GET /api/v1/execucoes/{id}/download-all` | `application/zip` | ZIP com todas as páginas |
| `GET /api/v1/paginas/{id}/download` | `application/octet-stream` | Arquivo markdown individual |
| `GET /api/v1/paginas/{id}/content` | `text/plain` | Conteúdo como texto puro |

### 7.6 Estrutura de Diretórios de Output

Os arquivos Markdown extraídos são organizados na seguinte hierarquia no servidor:

```
{output_dir}/{processo_id}/{execucao_id}/{slug}.md
```

**Exemplo real:**

```
./output/
└── a1b2c3d4-5678-abcd-ef01-234567890abc/
    └── f9e8d7c6-5432-abcd-ef01-987654321fed/
        ├── exemplo-com.md
        ├── docs-exemplo-com-pagina2.md
        └── ...
```

- **`output_dir`**: Configurado na Configuração (default: `./output`). Caminhos com `./` são normalizados automaticamente.
- **`processo_id`**: UUID do processo
- **`execucao_id`**: UUID da execução
- **Nome do arquivo**: Slug seguro gerado a partir da URL via `sanitize_filename()`
- O campo `caminho_arquivo` na resposta de `PaginaExtraida` contém o caminho completo relativo

---

## 8. Enums e Valores Válidos

Todos os enums herdam de `str` e `Enum`, permitindo serialização automática em JSON.

### ProcessoStatus

Status do processo de extração.

| Valor | Descrição |
| ----- | --------- |
| `ativo` | Processo ativo e disponível para execução |
| `inativo` | Processo desativado temporariamente |
| `arquivado` | Processo arquivado (somente leitura) |

### ExecucaoStatus

Ciclo de vida de uma execução.

| Valor | Descrição |
| ----- | --------- |
| `criado` | Execução criada, ainda não iniciada |
| `aguardando` | Aguardando recursos para iniciar |
| `em_execucao` | Em execução ativa |
| `pausado` | Pausada pelo usuário |
| `concluido` | Finalizada com sucesso |
| `falhou` | Finalizada com erro fatal |
| `cancelado` | Cancelada pelo usuário |
| `concluido_com_erros` | Finalizada, mas com erros parciais |

**Diagrama de transições:**

```
criado → aguardando → em_execucao → concluido
                          ↓              ↑
                        pausado ─────────┘
                          ↓
                       em_execucao → concluido_com_erros
                          ↓
                        falhou
                          ↓
                       cancelado
```

### FormatoSaida

Formato de saída dos arquivos extraídos.

| Valor | Descrição |
| ----- | --------- |
| `arquivo_unico` | Todas as páginas concatenadas em um único arquivo |
| `multiplos_arquivos` | Um arquivo por página extraída |

### AgendamentoTipo

Tipo de agendamento da execução.

| Valor | Descrição |
| ----- | --------- |
| `manual` | Execução iniciada manualmente pelo usuário |
| `recorrente` | Execução agendada por expressão cron |
| `one_time` | Execução agendada para uma única vez |

### MetodoExtracao

Motor de extração de conteúdo.

| Valor | Descrição |
| ----- | --------- |
| `html2text` | Conversão HTML → Markdown via html2text |
| `docling` | Extração avançada via Docling |

### PaginaStatus

Resultado da extração de uma página individual.

| Valor | Descrição |
| ----- | --------- |
| `sucesso` | Página extraída com sucesso |
| `falhou` | Falha na extração (ver `erro_mensagem`) |
| `ignorado` | Página ignorada (duplicata, filtro, etc.) |

### LogNivel

Nível de severidade do log.

| Valor | Descrição |
| ----- | --------- |
| `debug` | Informações detalhadas para diagnóstico |
| `info` | Mensagens informativas de progresso |
| `warning` | Alertas que merecem atenção |
| `error` | Erros que afetam a execução |

---

> **Documentação gerada a partir do código-fonte do projeto Toninho.**
> Para a documentação interativa com Swagger UI, acesse `http://localhost:8000/docs`.
