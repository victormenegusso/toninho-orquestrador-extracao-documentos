# PRD-008: Módulo Log

**Status**: ✅ Concluído
**Prioridade**: 🟠 Alta - Backend Entidades Core (Prioridade 2)
**Categoria**: Backend - Entidades Core
**Estimativa**: 4-5 horas

---

## 1. Objetivo

Implementar o módulo de Logs (Repository, Service, API) para registrar e consultar logs de execuções em tempo real. Suporta persistência de logs, streaming via Server-Sent Events (SSE) e filtros avançados.

## 2. Contexto e Justificativa

Logs são essenciais para debug e monitoramento. Cada execução gera logs em tempo real durante processamento. Este módulo permite:
- Persistir logs no banco para consulta histórica
- Stream de logs em tempo real via SSE
- Filtros por nível, período, busca em mensagem
- Visualização de contexto estruturado (JSON)

**Particularidades:**
- Logs são append-only (nunca atualizados ou deletados individualmente)
- Grande volume de registros (indexação importante)
- Stream em tempo real (SSE)
- Contexto JSON para dados estruturados

## 3. Requisitos Técnicos

### 3.1. Repository (toninho/repositories/log_repository.py)

**Métodos:**
```python
create(db, log) -> Log
create_batch(db, logs: List[Log]) -> List[Log]
    # Inserção em lote para performance

get_by_id(db, log_id) -> Optional[Log]

get_by_execucao_id(
    db,
    execucao_id,
    skip=0,
    limit=100,
    nivel: Optional[LogNivel] = None,
    desde: Optional[datetime] = None,
    ate: Optional[datetime] = None,
    busca: Optional[str] = None
) -> Tuple[List[Log], int]
    # Logs de uma execução com filtros
    # busca: busca na mensagem (LIKE/ILIKE)
    # ordenação: timestamp DESC (mais recentes primeiro)

get_recent(db, execucao_id, limit=20) -> List[Log]
    # Últimos N logs da execução

count_by_nivel(db, execucao_id) -> Dict[LogNivel, int]
    # Conta logs por nível (DEBUG: 10, INFO: 50, ERROR: 2, etc)

delete_by_execucao_id(db, execucao_id) -> int
    # Deleta todos os logs de uma execução (cascata via FK)
    # Retorna quantidade deletada
```

### 3.2. Service (toninho/services/log_service.py)

**Métodos:**
```python
create_log(db, log_create: LogCreate) -> LogResponse
    # 1. Validar execução existe
    # 2. Criar log
    # 3. Retornar response

create_log_batch(db, logs_create: List[LogCreate]) -> List[LogResponse]
    # Inserção em lote otimizada

get_log(db, log_id) -> LogResponse

list_logs_by_execucao(
    db,
    execucao_id,
    page=1,
    per_page=100,
    filtro: Optional[LogFilter] = None
) -> SuccessListResponse[LogResponse]
    # LogFilter: nivel, desde, ate, busca

get_logs_recentes(db, execucao_id, limit=20) -> List[LogResponse]
    # Últimos N logs

get_estatisticas_logs(db, execucao_id) -> LogEstatisticas
    # Contagem por nível, percentuais

stream_logs(db, execucao_id) -> AsyncGenerator[LogResponse, None]
    # Generator assíncrono para SSE
    # Emite novos logs conforme aparecem
```

**LogEstatisticas** (novo schema):
```python
class LogEstatisticas(BaseModel):
    execucao_id: UUID
    total: int
    por_nivel: Dict[LogNivel, int]
    percentual_erros: float
    primeiro_log: Optional[datetime]
    ultimo_log: Optional[datetime]
```

### 3.3. API Routes (toninho/api/routes/logs.py)

**Router**: prefix="/api/v1", tags=["Logs"]

**Endpoints:**
```python
POST /api/v1/logs
    # Criar log (uso interno, geralmente via workers)
    # Request: LogCreate
    # Response: SuccessResponse[LogResponse]
    # Status: 201

POST /api/v1/logs/batch
    # Criar múltiplos logs em lote
    # Request: List[LogCreate]
    # Response: SuccessResponse[List[LogResponse]]
    # Status: 201

GET /api/v1/execucoes/{execucao_id}/logs
    # Listar logs da execução com paginação e filtros
    # Query params: page, per_page, nivel, desde, ate, busca
    # Response: SuccessListResponse[LogResponse]
    # Status: 200

GET /api/v1/execucoes/{execucao_id}/logs/stream
    # Stream de logs em tempo real via SSE
    # Response: text/event-stream
    # Status: 200
    # Event format: data: {JSON serializado de LogResponse}
    # Nota: Manter conexão aberta, emitir novos logs conforme chegam

GET /api/v1/execucoes/{execucao_id}/logs/recentes
    # Obter últimos N logs (default 20)
    # Query param: limit
    # Response: SuccessResponse[List[LogResponse]]
    # Status: 200

GET /api/v1/execucoes/{execucao_id}/logs/estatisticas
    # Obter estatísticas de logs
    # Response: SuccessResponse[LogEstatisticas]
    # Status: 200

GET /api/v1/logs/{log_id}
    # Obter log específico por ID
    # Response: SuccessResponse[LogResponse]
    # Status: 200
    # Status: 404
```

### 3.4. Server-Sent Events (SSE)

**Implementação de /logs/stream:**
```python
from fastapi.responses import StreamingResponse
from asyncio import sleep

@router.get("/execucoes/{execucao_id}/logs/stream")
async def stream_logs(
    execucao_id: UUID,
    db: Session = Depends(get_db),
    log_service: LogService = Depends(get_log_service)
):
    async def event_generator():
        ultimo_id = None
        while True:
            # Buscar novos logs desde ultimo_id
            novos_logs = await buscar_novos_logs(db, execucao_id, ultimo_id)
            for log in novos_logs:
                yield f"data: {log.model_dump_json()}\n\n"
                ultimo_id = log.id

            # Verificar se execução finalizou
            execucao = db.query(Execucao).get(execucao_id)
            if execucao.status in estados_finais:
                yield "event: done\ndata: {}\n\n"
                break

            await sleep(1)  # Poll a cada segundo

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-003: Models
- PRD-004: Schemas
- PRD-007: Módulo Execução

## 5. Regras de Negócio

### 5.1. Persistência
- Logs são append-only
- Nunca atualizados ou deletados individualmente
- Deletados em cascata quando execução é deletada

### 5.2. Níveis de Log
- DEBUG: Informações detalhadas para debug
- INFO: Informações gerais do fluxo
- WARNING: Avisos, não bloqueiam execução
- ERROR: Erros, podem indicar falha parcial

### 5.3. Contexto
- Campo JSON opcional para dados estruturados
- Exemplos: {"url": "...", "status_code": 404}, {"duration_ms": 1500}

### 5.4. Volume
- Execuções podem gerar centenas/milhares de logs
- Paginação obrigatória
- Indexação em execucao_id e timestamp

### 5.5. Streaming
- Manter conexão SSE aberta enquanto execução em andamento
- Emitir evento "done" ao finalizar
- Cliente pode reconectar em desconexão

## 6. Casos de Teste

### 6.1. Repository Tests
- ✅ create(): insere log
- ✅ create_batch(): insere múltiplos logs
- ✅ get_by_execucao_id(): retorna logs da execução
- ✅ get_by_execucao_id(): filtra por nível
- ✅ get_by_execucao_id(): filtra por período (desde/ate)
- ✅ get_by_execucao_id(): busca em mensagem
- ✅ get_recent(): retorna últimos N logs
- ✅ count_by_nivel(): conta por nível

### 6.2. Service Tests
- ✅ create_log(): cria log válido
- ✅ create_log(): valida execução existe
- ✅ create_log_batch(): inserção em lote
- ✅ list_logs_by_execucao(): pagina corretamente
- ✅ list_logs_by_execucao(): aplica filtros
- ✅ get_estatisticas_logs(): calcula estatísticas

### 6.3. API Tests
- ✅ POST /logs: cria log (201)
- ✅ POST /logs/batch: cria múltiplos (201)
- ✅ GET /execucoes/{id}/logs: lista com paginação
- ✅ GET: filtra por nivel
- ✅ GET: filtra por período
- ✅ GET: busca em mensagem
- ✅ GET /logs/recentes: retorna últimos N
- ✅ GET /logs/estatisticas: retorna estatísticas
- ✅ GET /logs/stream: stream via SSE funciona

### 6.4. SSE Tests
- ✅ Conecta e recebe eventos
- ✅ Recebe novos logs em tempo real
- ✅ Recebe evento "done" ao finalizar
- ✅ Reconecta após desconexão

## 7. Critérios de Aceitação

### ✅ Implementação
- [x] Repository com todos os métodos
- [x] Service com validações
- [x] API Routes implementadas
- [x] SSE streaming funcional

### ✅ Testes
- [x] Testes com cobertura > 90%
- [x] Testes de streaming

### ✅ Funcionalidades
- [x] Pode criar e consultar logs via API
- [x] Filtros funcionam corretamente
- [x] Streaming em tempo real funciona
- [x] Estatísticas calculadas

## 8. Notas de Implementação

### 8.1. Performance
- Criar índice composto: (execucao_id, timestamp DESC)
- Usar paginação sempre (max 100 por página)
- Batch inserts para múltiplos logs

### 8.2. SSE Client (JavaScript)
```javascript
const eventSource = new EventSource('/api/v1/execucoes/{id}/logs/stream');

eventSource.onmessage = (event) => {
    const log = JSON.parse(event.data);
    console.log(log);
};

eventSource.addEventListener('done', () => {
    eventSource.close();
});

eventSource.onerror = () => {
    // Reconectar
};
```

### 8.3. Pontos de Atenção
- SSE mantém conexões abertas, limitar ao necessário
- SQLite pode ter problemas com muitas escritas simultâneas
- Logs DEBUG podem gerar volume excessivo, considerar níveis de log
- Contexto JSON deve ter tamanho razoável (< 10KB)

## 9. Referências Técnicas

- **FastAPI SSE**: https://fastapi.tiangolo.com/advanced/custom-response/
- **Server-Sent Events**: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events

## 10. Definição de Pronto

- ✅ CRUD de Logs implementado
- ✅ Filtros avançados funcionais
- ✅ Streaming SSE em tempo real funciona
- ✅ Estatísticas de logs calculadas
- ✅ Testes com cobertura > 90%
- ✅ Pode criar, consultar e streamar logs via API

---

**PRD Anterior**: PRD-007 - Módulo Execução
**Próximo PRD**: PRD-009 - Módulo Página Extraída
