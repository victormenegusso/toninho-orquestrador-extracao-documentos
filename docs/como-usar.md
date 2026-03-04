# Como Usar o Toninho — Guia Rápido

Sistema de extração de páginas web para Markdown via API REST.

---

## Pré-requisitos

- Docker e Docker Compose instalados
- Portas `8000` (API) e `5555` (Flower) livres

---

## 1. Subir o ambiente

```bash
make docker-up
```

Serviços levantados:

| Serviço | URL |
|---|---|
| API + Swagger | http://localhost:8000/docs |
| Interface Web | http://localhost:8000 |
| Flower (tasks) | http://localhost:5555 |

Aguarde todos os containers ficarem `healthy`:

```bash
docker compose ps
```

---

## 2. Fluxo completo de extração

O fluxo tem 3 etapas: **Processo → Configuração → Execução**.

```
POST /processos → POST /processos/{id}/configuracoes → POST /processos/{id}/execucoes
```

---

### Etapa 1 — Criar o Processo

```bash
curl -s -X POST http://localhost:8000/api/v1/processos \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Spring Cloud GCP Docs",
    "descricao": "Documentação oficial Spring Cloud GCP 7.4.5"
  }' | jq .
```

Resposta esperada (`201 Created`):

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "nome": "Spring Cloud GCP Docs",
    "descricao": "Documentação oficial Spring Cloud GCP 7.4.5",
    "status": "ativo",
    "created_at": "2026-03-04T00:40:55",
    "updated_at": "2026-03-04T00:40:55"
  }
}
```

> Salve o `id` retornado — você vai precisar nas etapas seguintes.

---

### Etapa 2 — Criar a Configuração

Associa URLs e parâmetros ao processo criado:

```bash
PROCESSO_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -s -X POST http://localhost:8000/api/v1/processos/${PROCESSO_ID}/configuracoes \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://googlecloudplatform.github.io/spring-cloud-gcp/7.4.5/reference/html/index.html"
    ],
    "timeout": 60,
    "max_retries": 3,
    "output_dir": "./output"
  }' | jq .
```

Resposta esperada (`201 Created`):

```json
{
  "success": true,
  "data": {
    "id": "c3d4e5f6-a1b2-3456-cdef-789012345678",
    "processo_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "urls": [
      "https://googlecloudplatform.github.io/spring-cloud-gcp/7.4.5/reference/html/index.html"
    ],
    "timeout": 60,
    "max_retries": 3,
    "formato_saida": "multiplos_arquivos",
    "output_dir": "output",
    "agendamento_tipo": "manual",
    "agendamento_cron": null,
    "created_at": "2026-03-04T00:41:16",
    "updated_at": "2026-03-04T00:41:16"
  }
}
```

> **Nota**: o campo `output_dir` normaliza `./output` → `output` automaticamente.

---

### Etapa 3 — Iniciar a Execução

Dispara o processamento assíncrono:

```bash
curl -s -X POST http://localhost:8000/api/v1/processos/${PROCESSO_ID}/execucoes \
  -H "Content-Type: application/json" | jq .
```

Resposta esperada (`201 Created`):

```json
{
  "success": true,
  "data": {
    "id": "e5f6a1b2-c3d4-5678-ef01-234567890abc",
    "processo_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "aguardando",
    "paginas_processadas": 0,
    "bytes_extraidos": 0,
    "taxa_erro": 0.0,
    "tentativa_atual": 1,
    "em_andamento": true,
    "duracao_segundos": null,
    "iniciado_em": null,
    "finalizado_em": null,
    "created_at": "2026-03-04T00:41:21",
    "updated_at": "2026-03-04T00:41:21"
  }
}
```

---

## 3. Acompanhar o progresso

### Via API

```bash
EXECUCAO_ID="e5f6a1b2-c3d4-5678-ef01-234567890abc"

curl -s http://localhost:8000/api/v1/execucoes/${EXECUCAO_ID} | jq '{status: .data.status, paginas: .data.paginas_processadas, bytes: .data.bytes_extraidos}'
```

Ciclo de status: `aguardando` → `em_execucao` → `concluido` | `falhou` | `concluido_com_erros`

### Via Flower (UI)

Acesse http://localhost:5555 para ver as tasks Celery em tempo real.

### Via Interface Web

Acesse http://localhost:8000 para a interface de monitoramento com atualização automática.

---

## 4. Ver resultados

### Páginas extraídas da execução

```bash
curl -s "http://localhost:8000/api/v1/execucoes/${EXECUCAO_ID}/paginas" | jq .
```

Resposta:

```json
{
  "data": [
    {
      "id": "5ee9f72f-db47-4400-ab00-714e5608c85d",
      "url_original": "https://googlecloudplatform.github.io/spring-cloud-gcp/7.4.5/reference/html/index.html",
      "status": "sucesso",
      "tamanho_bytes": 386806,
      "tamanho_legivel": "377.7 KB"
    }
  ],
  "meta": { "page": 1, "per_page": 100, "total": 1, "total_pages": 1 }
}
```

Para ver detalhes completos (incluindo caminho do arquivo e URL de download):

```bash
PAGINA_ID="5ee9f72f-db47-4400-ab00-714e5608c85d"
curl -s "http://localhost:8000/api/v1/paginas/${PAGINA_ID}" | jq .
```

Resposta:

```json
{
  "success": true,
  "data": {
    "id": "5ee9f72f-db47-4400-ab00-714e5608c85d",
    "execucao_id": "e5f6a1b2-c3d4-5678-ef01-234567890abc",
    "url_original": "https://googlecloudplatform.github.io/spring-cloud-gcp/7.4.5/reference/html/index.html",
    "caminho_arquivo": "output/{processo_id}/{execucao_id}/spring-cloud-gcp-7_4_5-reference-html-index_html.md",
    "status": "sucesso",
    "tamanho_bytes": 386806,
    "tamanho_legivel": "377.7 KB",
    "timestamp": "2026-03-04T00:41:22",
    "erro_mensagem": null,
    "download_url": "/api/v1/paginas/{pagina_id}/download",
    "preview_disponivel": true
  }
}
```

### Arquivo gerado (Markdown)

Os arquivos são salvos no volume Docker (`./output/`) com estrutura:

```
./output/{processo_id}/{execucao_id}/{nome_sanitizado}.md
```

```bash
# No host (output montado via volume Docker)
ls ./output/
```

O arquivo começa com YAML frontmatter:

```markdown
---
url: https://googlecloudplatform.github.io/spring-cloud-gcp/7.4.5/reference/html/index.html
title: "Spring Framework on Google Cloud"
extracted_at: 2026-03-04T00:41:22+00:00
extractor: Toninho v1.0
---

# Spring Framework on Google Cloud

...conteúdo convertido em Markdown...
```

Para baixar via API:

```bash
curl -O http://localhost:8000/api/v1/paginas/${PAGINA_ID}/download
```

### Logs da execução

```bash
curl -s "http://localhost:8000/api/v1/execucoes/${EXECUCAO_ID}/logs" | jq .
```

Resposta:

```json
{
  "data": [
    { "nivel": "info", "mensagem": "Extração finalizada: 1 sucesso, 0 falhas — status=concluido", "timestamp": "2026-03-04T00:41:22" },
    { "nivel": "info", "mensagem": "[1/1] Extraindo: https://...", "timestamp": "2026-03-04T00:41:21" },
    { "nivel": "info", "mensagem": "Iniciando extração de 1 URLs", "timestamp": "2026-03-04T00:41:21" }
  ],
  "meta": { "total": 3 }
}
```

---

## 5. Operações adicionais

### Listar todos os processos

```bash
curl -s "http://localhost:8000/api/v1/processos?page=1&per_page=10" | jq .
```

### Listar execuções de um processo

```bash
curl -s "http://localhost:8000/api/v1/processos/${PROCESSO_ID}/execucoes" | jq .
```

### Atualizar processo

```bash
curl -s -X PATCH http://localhost:8000/api/v1/processos/${PROCESSO_ID} \
  -H "Content-Type: application/json" \
  -d '{"descricao": "Nova descrição"}' | jq .
```

### Health check

```bash
curl -s http://localhost:8000/api/v1/health | jq .
```

---

## 6. Parar o ambiente

```bash
make docker-down
```

---

## Referência rápida de endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/api/v1/processos` | Criar processo |
| `GET` | `/api/v1/processos` | Listar processos |
| `GET` | `/api/v1/processos/{id}` | Detalhar processo |
| `PATCH` | `/api/v1/processos/{id}` | Atualizar processo |
| `DELETE` | `/api/v1/processos/{id}` | Remover processo |
| `POST` | `/api/v1/processos/{id}/configuracoes` | Criar configuração |
| `GET` | `/api/v1/processos/{id}/configuracao` | Configuração atual |
| `POST` | `/api/v1/processos/{id}/execucoes` | Iniciar execução |
| `GET` | `/api/v1/processos/{id}/execucoes` | Listar execuções |
| `GET` | `/api/v1/execucoes/{id}` | Detalhar execução |
| `GET` | `/api/v1/execucoes/{id}/paginas` | Páginas extraídas |
| `GET` | `/api/v1/execucoes/{id}/logs` | Logs da execução |
| `GET` | `/api/v1/health` | Health check |

Documentação interativa completa: http://localhost:8000/docs
