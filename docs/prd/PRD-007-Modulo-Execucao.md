# PRD-007: Módulo Execução

**Status**: 📋 Pronto para implementação  
**Prioridade**: 🟠 Alta - Backend Entidades Core (Prioridade 2)  
**Categoria**: Backend - Entidades Core  
**Estimativa**: 7-9 horas

---

## 1. Objetivo

Implementar o módulo de Execução (Repository, Service, API), que representa instâncias de execução de um processo de extração. Gerencia o ciclo de vida da execução (estados), métricas e ações (cancelar, pausar, retomar).

## 2. Contexto e Justificativa

Execução é a entidade que representa uma instância de processamento. Cada vez que um processo é executado, uma Execução é criada. Este módulo gerencia:
- Criação de execuções (manual ou agendada)
- Transições de estado (CRIADO → AGUARDANDO → EM_EXECUCAO → final)
- Ações de controle (cancelar, pausar, retomar)
- Métricas em tempo real (progresso, páginas processadas, bytes)

**Particularidades:**
- Máquina de estados rígida (transições permitidas)
- Relacionamentos complexos (1:N com Logs e Páginas)
- Métricas computadas (duração, taxa de erro, progresso)
- Ações assíncronas via Celery (cancelar task)

## 3. Requisitos Técnicos

### 3.1. Repository (toninho/repositories/execucao_repository.py)

**Métodos:**
```python
create(db, execucao) -> Execucao
get_by_id(db, execucao_id, with_relations=False) -> Optional[Execucao]
    # with_relations: eager load logs e paginas
get_all_by_processo_id(db, processo_id, skip, limit) -> Tuple[List[Execucao], int]
get_all(db, skip, limit, status, ordem) -> Tuple[List[Execucao], int]
update(db, execucao) -> Execucao
update_status(db, execucao_id, novo_status) -> Execucao
    # Helper para transição de status
increment_metrics(db, execucao_id, paginas=0, bytes=0, errors=0) -> Execucao
    # Incrementa métricas atomicamente
get_em_execucao(db, processo_id) -> Optional[Execucao]
    # Retorna execução EM_EXECUCAO do processo (se houver)
count_by_status(db, status) -> int
delete(db, execucao_id) -> bool
```

### 3.2. Service (toninho/services/execucao_service.py)

**Métodos:**
```python
create_execucao(db, execucao_create) -> ExecucaoResponse
    # 1. Validar processo existe
    # 2. Validar não há execução EM_EXECUCAO do mesmo processo (limite 1 por processo)
    # 3. Criar execução com status=CRIADO
    # 4. Enfileirar task Celery para execução
    # 5. Retornar response

get_execucao(db, execucao_id) -> ExecucaoResponse
get_execucao_detail(db, execucao_id) -> ExecucaoDetail
    # Inclui processo, logs recentes, páginas, métricas

list_execucoes(db, page, per_page, processo_id, status, ordem) -> SuccessListResponse
    # Filtro por processo_id e/ou status
    # Ordenação por created_at, iniciado_em, finalizado_em

update_execucao_status(db, execucao_id, status_update) -> ExecucaoResponse
    # Validar transição de estado permitida
    # Atualizar status

cancelar_execucao(db, execucao_id) -> ExecucaoResponse
    # 1. Validar execução está EM_EXECUCAO ou AGUARDANDO
    # 2. Revogar task Celery
    # 3. Atualizar status para CANCELADO
    # 4. Setar finalizado_em

pausar_execucao(db, execucao_id) -> ExecucaoResponse
    # 1. Validar execução está EM_EXECUCAO
    # 2. Pausar task Celery (se possível)
    # 3. Atualizar status para PAUSADO

retomar_execucao(db, execucao_id) -> ExecucaoResponse
    # 1. Validar execução está PAUSADO
    # 2. Retomar task Celery
    # 3. Atualizar status para EM_EXECUCAO

get_execucao_metricas(db, execucao_id) -> ExecucaoMetricas
    # Métricas detalhadas: tempo_medio_por_pagina, taxa_sucesso, etc

get_progresso(db, execucao_id) -> ProgressoResponse
    # Para polling de progresso em tempo real
```

**ProgressoResponse** (novo schema):
```python
class ProgressoResponse(BaseModel):
    execucao_id: UUID
    status: ExecucaoStatus
    paginas_processadas: int
    total_paginas: int  # do configuração.urls
    progresso_percentual: float
    tempo_decorrido_segundos: Optional[int]
    tempo_estimado_restante_segundos: Optional[int]
    ultima_atualizacao: datetime
```

**Validações de transição de estado:**
```python
TRANSICOES_PERMITIDAS = {
    ExecucaoStatus.CRIADO: [ExecucaoStatus.AGUARDANDO],
    ExecucaoStatus.AGUARDANDO: [ExecucaoStatus.EM_EXECUCAO, ExecucaoStatus.CANCELADO],
    ExecucaoStatus.EM_EXECUCAO: [
        ExecucaoStatus.PAUSADO,
        ExecucaoStatus.CONCLUIDO,
        ExecucaoStatus.FALHOU,
        ExecucaoStatus.CANCELADO,
        ExecucaoStatus.CONCLUIDO_COM_ERROS
    ],
    ExecucaoStatus.PAUSADO: [ExecucaoStatus.EM_EXECUCAO, ExecucaoStatus.CANCELADO],
    # Estados finais não permitem transições
    ExecucaoStatus.CONCLUIDO: [],
    ExecucaoStatus.FALHOU: [],
    ExecucaoStatus.CANCELADO: [],
    ExecucaoStatus.CONCLUIDO_COM_ERROS: []
}

def validar_transicao(status_atual, status_novo) -> bool:
    return status_novo in TRANSICOES_PERMITIDAS.get(status_atual, [])
```

### 3.3. API Routes (toninho/api/routes/execucoes.py)

**Router**: prefix="/api/v1", tags=["Execuções"]

**Endpoints:**
```python
POST /api/v1/processos/{processo_id}/execucoes
    # Criar e iniciar execução do processo
    # Request: ExecucaoCreate (pode ser vazio, tudo default)
    # Response: SuccessResponse[ExecucaoResponse]
    # Status: 201
    # Nota: Automaticamente enfileira task Celery

GET /api/v1/processos/{processo_id}/execucoes
    # Listar execuções do processo
    # Query: page, per_page, status
    # Response: SuccessListResponse[ExecucaoSummary]
    # Status: 200

GET /api/v1/execucoes
    # Listar todas as execuções (global)
    # Query: page, per_page, status
    # Response: SuccessListResponse[ExecucaoSummary]
    # Status: 200

GET /api/v1/execucoes/{execucao_id}
    # Obter detalhes básicos da execução
    # Response: SuccessResponse[ExecucaoResponse]
    # Status: 200

GET /api/v1/execucoes/{execucao_id}/detalhes
    # Obter detalhes completos (com logs, páginas, métricas)
    # Response: SuccessResponse[ExecucaoDetail]
    # Status: 200

PATCH /api/v1/execucoes/{execucao_id}/status
    # Atualizar status manualmente (uso interno, geralmente)
    # Request: ExecucaoStatusUpdate
    # Response: SuccessResponse[ExecucaoResponse]
    # Status: 200

POST /api/v1/execucoes/{execucao_id}/cancelar
    # Cancelar execução em andamento
    # Response: SuccessResponse[ExecucaoResponse]
    # Status: 200
    # Status: 409 se não pode cancelar (já finalizada)

POST /api/v1/execucoes/{execucao_id}/pausar
    # Pausar execução em andamento
    # Response: SuccessResponse[ExecucaoResponse]
    # Status: 200
    # Status: 409 se não pode pausar

POST /api/v1/execucoes/{execucao_id}/retomar
    # Retomar execução pausada
    # Response: SuccessResponse[ExecucaoResponse]
    # Status: 200
    # Status: 409 se não pode retomar

GET /api/v1/execucoes/{execucao_id}/progresso
    # Obter progresso em tempo real
    # Response: SuccessResponse[ProgressoResponse]
    # Status: 200
    # Nota: Para polling, chamar periodicamente

GET /api/v1/execucoes/{execucao_id}/metricas
    # Obter métricas detalhadas
    # Response: SuccessResponse[ExecucaoMetricas]
    # Status: 200

DELETE /api/v1/execucoes/{execucao_id}
    # Deletar execução (apenas se não EM_EXECUCAO)
    # Response: 204 No Content
    # Status: 409 se EM_EXECUCAO
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-003: Models
- PRD-004: Schemas
- PRD-005: Módulo Processo
- PRD-010: Workers (para enfileirar tasks Celery) - implementação parcial pode ser feita sem workers

## 5. Regras de Negócio

### 5.1. Criação de Execução
- Ao criar, status inicial é CRIADO
- Automaticamente muda para AGUARDANDO quando enfileirada
- Apenas 1 execução EM_EXECUCAO por processo (validar)

### 5.2. Máquina de Estados
- Transições devem respeitar TRANSICOES_PERMITIDAS
- Estados finais (CONCLUIDO, FALHOU, CANCELADO) são imutáveis
- EM_EXECUCAO pode ir para PAUSADO, mas PAUSADO só volta para EM_EXECUCAO (não pode pular)

### 5.3. Cancelamento
- Apenas se AGUARDANDO ou EM_EXECUCAO
- Revoga task Celery se existir
- Seta finalizado_em
- Status final: CANCELADO

### 5.4. Pausar/Retomar
- Apenas MVP: funcionalidade opcional, pode lançar NotImplementedError
- Se implementado: salvar estado intermediário, retomar de onde parou

### 5.5. Métricas
- paginas_processadas: incrementado conforme páginas são processadas
- bytes_extraidos: soma dos tamanhos dos arquivos
- taxa_erro: (páginas falhadas / total processadas) * 100
- Atualizações atômicas para evitar race conditions

### 5.6. Deleção
- Não permitir deletar se EM_EXECUCAO
- Cascata para Logs e Páginas Extraídas
- Arquivos no filesystem não são deletados automaticamente

## 6. Casos de Teste

### 6.1. Service Tests
- ✅ create_execucao(): cria com processo válido
- ✅ create_execucao(): bloqueia se já há execução EM_EXECUCAO do mesmo processo
- ✅ cancelar_execucao(): cancela se EM_EXECUCAO
- ✅ cancelar_execucao(): falha se já CONCLUIDO
- ✅ update_execucao_status(): aceita transições válidas
- ✅ update_execucao_status(): rejeita transições inválidas
- ✅ get_progresso(): calcula progresso corretamente
- ✅ get_execucao_metricas(): calcula métricas

### 6.2. API Tests
- ✅ POST /processos/{id}/execucoes: cria (201)
- ✅ POST: bloqueia se já há execução EM_EXECUCAO
- ✅ GET /execucoes: lista com paginação
- ✅ GET /execucoes: filtra por status
- ✅ GET /execucoes/{id}: retorna detalhes
- ✅ POST /execucoes/{id}/cancelar: cancela (200)
- ✅ POST /cancelar: retorna 409 se já finalizada
- ✅ GET /execucoes/{id}/progresso: retorna progresso

### 6.3. Transições de Estado
- ✅ CRIADO → AGUARDANDO (válido)
- ✅ AGUARDANDO → EM_EXECUCAO (válido)
- ✅ EM_EXECUCAO → CONCLUIDO (válido)
- ✅ CONCLUIDO → EM_EXECUCAO (inválido)
- ✅ EM_EXECUCAO → PAUSADO (válido)
- ✅ PAUSADO → EM_EXECUCAO (válido)

## 7. Critérios de Aceitação

### ✅ Implementação
- [ ] Repository com todos os métodos
- [ ] Service com validações de estado
- [ ] API Routes implementadas
- [ ] Ações de controle (cancelar, pausar, retomar)
- [ ] Métricas em tempo real

### ✅ Testes
- [ ] Testes com cobertura > 90%
- [ ] Transições de estado testadas
- [ ] Ações de controle testadas

### ✅ Funcionalidades
- [ ] Pode criar execução via API
- [ ] Pode cancelar execução
- [ ] Progresso retorna dados corretos
- [ ] Métricas calculadas corretamente

## 8. Notas de Implementação

### 8.1. Integração com Celery
Enfileirar task na criação:
```python
from toninho.workers.celery_app import executar_processo_task

# No service
task = executar_processo_task.delay(str(execucao.id))
# Salvar task.id na execução se necessário
```

Cancelar task:
```python
from celery import current_app

current_app.control.revoke(task_id, terminate=True)
```

### 8.2. Atualização Atômica de Métricas
Usar SQL direto para atomicidade:
```python
from sqlalchemy import update

stmt = (
    update(Execucao)
    .where(Execucao.id == execucao_id)
    .values(
        paginas_processadas=Execucao.paginas_processadas + incremento,
        bytes_extraidos=Execucao.bytes_extraidos + bytes_inc
    )
)
db.execute(stmt)
```

### 8.3. Pontos de Atenção
- Race conditions: múltiplas atualizações simultâneas
- Task IDs: armazenar Celery task ID para controle
- Polling: endpoint de progresso pode ser chamado frequentemente, otimizar
- Estados finais: garantir imutabilidade

## 9. Referências Técnicas

- **Celery Task Management**: https://docs.celeryproject.org/en/stable/userguide/workers.html
- **State Machines**: https://en.wikipedia.org/wiki/Finite-state_machine

## 10. Definição de Pronto

- ✅ CRUD completo de Execução
- ✅ Máquina de estados implementada
- ✅ Ações de controle funcionais
- ✅ Métricas em tempo real
- ✅ Progresso calculado corretamente
- ✅ Testes com cobertura > 90%
- ✅ Pode criar, controlar e monitorar execuções via API

---

**PRD Anterior**: PRD-006 - Módulo Configuração  
**Próximo PRD**: PRD-008 - Módulo Log
