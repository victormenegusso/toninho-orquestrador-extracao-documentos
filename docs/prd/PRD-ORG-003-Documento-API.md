# PRD-ORG-003: Documento da API

**Status**: 📋 Planejado
**Prioridade**: 🟠 Média
**Categoria**: Documentação
**Tipo**: Novo Documento

---

## 1. Objetivo

Criar o documento `docs/API.md` com a referência completa de todos os endpoints REST do sistema Toninho, incluindo métodos, paths, request/response, códigos de erro e fluxo de uso.

## 2. Contexto e Justificativa

O README atual lista apenas 4 endpoints. O projeto tem 20+ endpoints REST. A única documentação de API é o Swagger auto-gerado (`/docs`), que não é acessível offline nem por agentes de IA que leem o repositório.

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: D3

---

## 3. Conteúdo Obrigatório

### 3.1. Introdução

- Base URL: `http://localhost:8000`
- Versionamento: `/api/v1/`
- Formato: JSON
- Autenticação: Nenhuma (single-user)

### 3.2. Formato Padrão de Resposta

**Sucesso:**
```json
{
  "success": true,
  "data": { },
  "meta": { "page": 1, "per_page": 10, "total": 5 }
}
```

**Erro:**
```json
{
  "success": false,
  "error": "Mensagem de erro",
  "details": "Contexto adicional"
}
```

### 3.3. Tabela Completa de Endpoints

O agente deve gerar esta tabela **lendo o código fonte** dos arquivos em `toninho/api/routes/`. A tabela deve conter:

| Método | Path | Descrição | Request Body | Response |
|--------|------|-----------|-------------|----------|

Endpoints esperados (verificar no código real):

**Health & Info:**
- `GET /api/v1/health`

**Processos:**
- `POST /api/v1/processos`
- `GET /api/v1/processos`
- `GET /api/v1/processos/{id}`
- `PATCH /api/v1/processos/{id}`
- `DELETE /api/v1/processos/{id}`

**Configurações:**
- `POST /api/v1/processos/{id}/configuracoes`
- `GET /api/v1/processos/{id}/configuracao`

**Execuções:**
- `POST /api/v1/processos/{id}/execucoes`
- `GET /api/v1/processos/{id}/execucoes`
- `GET /api/v1/execucoes/{id}`
- `GET /api/v1/execucoes/{id}/paginas`
- `GET /api/v1/execucoes/{id}/logs`

**Páginas Extraídas:**
- `GET /api/v1/paginas/{id}`
- `GET /api/v1/paginas/{id}/download`

**Monitoramento:**
- `GET /api/v1/monitoring/metrics`
- `GET /api/v1/monitoring/tasks`

### 3.4. Detalhamento por Endpoint

Para cada endpoint, documentar:

1. **Path e método**
2. **Descrição** (o que faz)
3. **Parâmetros** (path params, query params)
4. **Request Body** (JSON schema com campos obrigatórios e opcionais)
5. **Response** (JSON de exemplo)
6. **Códigos de status** (200, 201, 400, 404, 409, 500)
7. **Exemplo cURL**

As informações devem ser extraídas dos arquivos:
- `toninho/api/routes/*.py` → endpoints e parâmetros
- `toninho/schemas/*.py` → request/response schemas
- `toninho/models/enums.py` → valores válidos de enums

### 3.5. Fluxo de Uso (3 Passos)

Documentar o workflow completo com exemplos cURL:

```bash
# Passo 1: Criar processo
curl -X POST http://localhost:8000/api/v1/processos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Minha Extração", "descricao": "Teste"}'

# Passo 2: Configurar URLs
curl -X POST http://localhost:8000/api/v1/processos/{id}/configuracoes \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"], "timeout": 60}'

# Passo 3: Executar
curl -X POST http://localhost:8000/api/v1/processos/{id}/execucoes
```

### 3.6. Códigos de Erro

Tabela de códigos de erro comuns:

| Código | Significado | Causa Comum |
|--------|------------|-------------|
| 400 | Bad Request | Validação falhou (campo obrigatório, formato inválido) |
| 404 | Not Found | Processo/Execução não encontrado |
| 409 | Conflict | Nome de processo duplicado |
| 422 | Unprocessable Entity | Dados inválidos (Pydantic validation) |
| 500 | Internal Server Error | Erro inesperado |

### 3.7. Funcionalidades Especiais

- **SSE (Server-Sent Events)**: Endpoint de logs suporta streaming em tempo real
- **Paginação**: Query params `page` e `per_page` nos endpoints de listagem
- **Filtros**: Documentar filtros disponíveis em cada endpoint de listagem

---

## 4. Critérios de Aceite

- [ ] Arquivo `docs/API.md` criado
- [ ] Todos os endpoints listados (verificar contagem vs código real)
- [ ] Cada endpoint tem: path, método, descrição, parâmetros, exemplo de response
- [ ] Fluxo de 3 passos com exemplos cURL
- [ ] Tabela de códigos de erro
- [ ] Informação extraída do código real (não inventada)
- [ ] Documento em Português (PT-BR)

---

## 5. Fontes de Informação

O agente deve ler:
- `toninho/api/routes/*.py` — definição dos endpoints
- `toninho/schemas/*.py` — schemas de request/response
- `toninho/models/enums.py` — enums válidos
- `toninho/core/exceptions.py` — exceções e códigos de erro
- `docs/como-usar.md` — exemplos existentes (não duplicar, mas usar como referência)
