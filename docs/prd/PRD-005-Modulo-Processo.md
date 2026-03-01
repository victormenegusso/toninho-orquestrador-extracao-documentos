# PRD-005: Módulo Processo

**Status**: ✅ Implementado
**Prioridade**: 🟠 Alta - Backend Entidades Core (Prioridade 2)
**Categoria**: Backend - Entidades Core
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Implementar o módulo completo de gerenciamento de Processos, incluindo Repository (acesso a dados), Service (lógica de negócio) e API Routes (endpoints REST). Este módulo é o núcleo do sistema, representando os processos de extração que os usuários gerenciam.

## 2. Contexto e Justificativa

Processo é a entidade principal do Toninho. Um processo representa uma configuração de extração que pode ser executada múltiplas vezes. Este módulo implementa o CRUD completo com validações de negócio, paginação, filtros e métricas agregadas.

**Funcionalidades:**
- Criar processo com configuração inicial
- Listar processos com filtros (status, busca por nome)
- Obter detalhes de um processo com estatísticas
- Atualizar processo (nome, descrição, status)
- Deletar processo (deleção física em cascata)
- Métricas do processo (total de execuções, taxa de sucesso, etc)

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
toninho/repositories/
└── processo_repository.py

toninho/services/
└── processo_service.py

toninho/api/routes/
└── processos.py

toninho/api/dependencies/
└── processo_deps.py (opcional, se necessário)
```

### 3.2. Repository Layer (toninho/repositories/processo_repository.py)

**Responsabilidade**: Acesso direto ao banco de dados, queries SQLAlchemy.

**Classe ProcessoRepository**

**Métodos obrigatórios:**

```python
def create(db: Session, processo: Processo) -> Processo
    # Insere processo no banco
    # Retorna processo com id gerado

def get_by_id(db: Session, processo_id: UUID) -> Optional[Processo]
    # Busca processo por ID
    # Retorna None se não encontrado

def get_by_nome(db: Session, nome: str) -> Optional[Processo]
    # Busca processo por nome (unique constraint)
    # Usado para validar duplicatas
    # Retorna None se não encontrado

def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[ProcessoStatus] = None,
    busca: Optional[str] = None,
    order_by: str = "created_at",
    order_dir: str = "desc"
) -> Tuple[List[Processo], int]
    # Lista processos com paginação e filtros
    # Retorna (lista de processos, total de registros)
    # busca: busca por nome (LIKE/ILIKE)
    # order_by: campo para ordenação
    # order_dir: "asc" ou "desc"

def update(db: Session, processo: Processo) -> Processo
    # Atualiza processo existente
    # Atualiza timestamp updated_at automaticamente
    # Retorna processo atualizado

def delete(db: Session, processo_id: UUID) -> bool
    # Deleta processo (cascata para configurações e execuções)
    # Retorna True se deletado, False se não encontrado

def exists_by_nome(db: Session, nome: str, exclude_id: Optional[UUID] = None) -> bool
    # Verifica se já existe processo com nome
    # exclude_id: usado para update (ignorar próprio ID)

def count_total(db: Session) -> int
    # Conta total de processos

def count_by_status(db: Session, status: ProcessoStatus) -> int
    # Conta processos por status
```

**Implementação sugerida:**
- Usar SQLAlchemy Session para queries
- Usar joinedload/selectinload para eager loading quando necessário
- Queries readonly devem usar execution_options(synchronize_session=False)
- Tratamento de exceções SQLAlchemy (IntegrityError, etc)

### 3.3. Service Layer (toninho/services/processo_service.py)

**Responsabilidade**: Lógica de negócio, validações, orquestração, transformações.

**Classe ProcessoService**

**Métodos obrigatórios:**

```python
def create_processo(
    db: Session,
    processo_create: ProcessoCreate
) -> ProcessoResponse
    # 1. Validar nome único
    # 2. Criar model Processo
    # 3. Chamar repository.create()
    # 4. Converter model → schema Response
    # 5. Retornar ProcessoResponse
    # Exceção: ValueError se nome já existe

def get_processo(
    db: Session,
    processo_id: UUID
) -> ProcessoResponse
    # 1. Buscar via repository
    # 2. Validar se existe
    # 3. Converter para ProcessoResponse
    # 4. Calcular computed fields (total_execucoes, ultima_execucao_em)
    # Exceção: NotFoundError se não existe

def get_processo_detail(
    db: Session,
    processo_id: UUID
) -> ProcessoDetail
    # 1. Buscar via repository com eager loading (configurações, execuções)
    # 2. Validar se existe
    # 3. Converter para ProcessoDetail
    # 4. Incluir configurações e últimas 5 execuções
    # Exceção: NotFoundError se não existe

def list_processos(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    status: Optional[ProcessoStatus] = None,
    busca: Optional[str] = None,
    order_by: str = "created_at",
    order_dir: str = "desc"
) -> SuccessListResponse[ProcessoSummary]
    # 1. Validar parâmetros (page > 0, per_page entre 1-100)
    # 2. Calcular skip offset
    # 3. Chamar repository.get_all()
    # 4. Converter lista de models → ProcessoSummary
    # 5. Montar PaginationMeta
    # 6. Retornar SuccessListResponse

def update_processo(
    db: Session,
    processo_id: UUID,
    processo_update: ProcessoUpdate
) -> ProcessoResponse
    # 1. Buscar processo via repository
    # 2. Validar se existe
    # 3. Se nome mudou, validar não há duplicata
    # 4. Aplicar mudanças (merge de campos não-None)
    # 5. Chamar repository.update()
    # 6. Converter para ProcessoResponse
    # Exceção: NotFoundError se não existe
    # Exceção: ValueError se nome duplicado

def delete_processo(
    db: Session,
    processo_id: UUID
) -> bool
    # 1. Buscar processo via repository
    # 2. Validar se existe
    # 3. Validar se há execuções em andamento (opcional: pode bloquear)
    # 4. Chamar repository.delete()
    # 5. Retornar True
    # Exceção: NotFoundError se não existe
    # Exceção: ConflictError se há execuções em andamento (opcional)

def get_processo_metricas(
    db: Session,
    processo_id: UUID
) -> ProcessoMetricas
    # 1. Buscar processo via repository
    # 2. Validar se existe
    # 3. Agregar métricas:
    #    - total_execucoes
    #    - execucoes_sucesso, execucoes_falha
    #    - taxa_sucesso (%)
    #    - tempo_medio_execucao (segundos)
    #    - total_paginas_extraidas
    #    - total_bytes_extraidos
    #    - ultima_execucao_em
    # 4. Retornar ProcessoMetricas
```

**ProcessoMetricas Schema** (criar em schemas/processo.py):
```python
class ProcessoMetricas(BaseModel):
    processo_id: UUID
    total_execucoes: int
    execucoes_sucesso: int
    execucoes_falha: int
    taxa_sucesso: float  # 0-100
    tempo_medio_execucao_segundos: Optional[float]
    total_paginas_extraidas: int
    total_bytes_extraidos: int
    ultima_execucao_em: Optional[datetime]
```

**Validações de negócio:**
- Nome de processo único
- Transições de status permitidas (ATIVO ⇔ INATIVO ⇔ ARQUIVADO)
- Não permitir deletar processo com execuções em andamento (opcional)

**Exceções customizadas** (criar em toninho/core/exceptions.py):
```python
class NotFoundError(Exception): pass
class ConflictError(Exception): pass
class ValidationError(Exception): pass
```

### 3.4. API Routes (toninho/api/routes/processos.py)

**Responsabilidade**: Endpoints HTTP, validação de entrada, serialização de saída.

**Router**: APIRouter com prefix="/api/v1/processos", tags=["Processos"]

**Endpoints obrigatórios:**

```python
POST /api/v1/processos
    # Criar novo processo
    # Request body: ProcessoCreate
    # Response: SuccessResponse[ProcessoResponse]
    # Status: 201 Created
    # Headers: Location: /api/v1/processos/{id}

GET /api/v1/processos
    # Listar processos
    # Query params: page, per_page, status, busca, order_by, order_dir
    # Response: SuccessListResponse[ProcessoSummary]
    # Status: 200 OK

GET /api/v1/processos/{processo_id}
    # Obter detalhes de um processo (sem relacionamentos)
    # Path param: processo_id (UUID)
    # Response: SuccessResponse[ProcessoResponse]
    # Status: 200 OK
    # Status: 404 Not Found se não existe

GET /api/v1/processos/{processo_id}/detalhes
    # Obter detalhes completos (com configurações e execuções recentes)
    # Path param: processo_id (UUID)
    # Response: SuccessResponse[ProcessoDetail]
    # Status: 200 OK
    # Status: 404 Not Found se não existe

PUT /api/v1/processos/{processo_id}
    # Atualizar processo (substituição completa de campos presentes)
    # Path param: processo_id (UUID)
    # Request body: ProcessoUpdate
    # Response: SuccessResponse[ProcessoResponse]
    # Status: 200 OK
    # Status: 404 Not Found se não existe
    # Status: 409 Conflict se nome duplicado

PATCH /api/v1/processos/{processo_id}
    # Atualizar processo parcialmente (mesma implementação que PUT)
    # Path param: processo_id (UUID)
    # Request body: ProcessoUpdate (campos opcionais)
    # Response: SuccessResponse[ProcessoResponse]
    # Status: 200 OK

DELETE /api/v1/processos/{processo_id}
    # Deletar processo
    # Path param: processo_id (UUID)
    # Response: 204 No Content
    # Status: 404 Not Found se não existe
    # Status: 409 Conflict se há execuções em andamento (opcional)

GET /api/v1/processos/{processo_id}/metricas
    # Obter métricas agregadas do processo
    # Path param: processo_id (UUID)
    # Response: SuccessResponse[ProcessoMetricas]
    # Status: 200 OK
    # Status: 404 Not Found se não existe
```

**Error Handling:**
Cada endpoint deve capturar exceções e retornar ErrorResponse apropriado:
- NotFoundError → 404
- ConflictError → 409
- ValidationError → 400
- IntegrityError → 409
- Exception genérico → 500

**Dependency Injection:**
- db: Session = Depends(get_db)
- processo_service: ProcessoService = Depends(get_processo_service)

**OpenAPI Documentation:**
- Docstrings descritivos em cada endpoint
- Examples em request/response schemas
- Tags e summaries apropriados

### 3.5. Dependency Injection (toninho/api/dependencies/processo_deps.py)

```python
def get_processo_service(db: Session = Depends(get_db)) -> ProcessoService:
    return ProcessoService(ProcessoRepository())
```

## 4. Dependências

### 4.1. Pré-requisitos
- Models implementados (PRD-003)
- Schemas implementados (PRD-004)
- Database configurado (PRD-003)

### 4.2. Dependências de Outros PRDs
- **PRD-003**: Models e Database
- **PRD-004**: Schemas e DTOs

### 4.3. PRDs Subsequentes
Outros módulos de entidades (Configuração, Execução, Log, Página Extraída) podem seguir este padrão.

## 5. Regras de Negócio

### 5.1. Nome de Processo
- Único no sistema (constraint de banco + validação)
- Min 1 caractere, max 200 caracteres
- Trim de whitespace automático

### 5.2. Status de Processo
- Default: ATIVO
- Transições permitidas: qualquer → qualquer (flexível)
- Processos ARQUIVADOS não aparecem em listagens padrão (filtro)

### 5.3. Deleção de Processo
- Deleção física (não soft-delete no MVP)
- Cascata para Configurações e Execuções
- Arquivos extraídos no filesystem NÃO são deletados (limpeza manual)
- Opcional: Bloquear deleção se há execuções EM_EXECUCAO

### 5.4. Paginação
- Default: page=1, per_page=20
- Máximo per_page: 100
- Mínimo per_page: 1

### 5.5. Ordenação
- Campos permitidos: created_at, updated_at, nome, status
- Direções: asc, desc
- Default: created_at desc (mais recentes primeiro)

### 5.6. Busca
- Case-insensitive
- Busca apenas em campo "nome"
- Usa LIKE/ILIKE (%busca%)

## 6. Casos de Teste

### 6.1. Repository Tests
- ✅ create(): insere processo no banco
- ✅ get_by_id(): retorna processo correto
- ✅ get_by_id(): retorna None se não existe
- ✅ get_by_nome(): encontra por nome
- ✅ get_all(): lista processos com paginação
- ✅ get_all(): filtra por status
- ✅ get_all(): busca por nome
- ✅ get_all(): ordena corretamente
- ✅ update(): atualiza processo
- ✅ delete(): remove processo
- ✅ exists_by_nome(): detecta duplicatas
- ✅ count_total(): conta processos

### 6.2. Service Tests
- ✅ create_processo(): cria processo válido
- ✅ create_processo(): levanta erro se nome duplicado
- ✅ get_processo(): retorna processo existente
- ✅ get_processo(): levanta NotFoundError se não existe
- ✅ get_processo_detail(): inclui relacionamentos
- ✅ list_processos(): retorna lista paginada
- ✅ list_processos(): aplica filtros corretamente
- ✅ update_processo(): atualiza campos
- ✅ update_processo(): valida nome duplicado
- ✅ delete_processo(): remove processo
- ✅ get_processo_metricas(): calcula métricas corretas

### 6.3. API Tests (Integration)
- ✅ POST /processos: cria processo (201)
- ✅ POST /processos: retorna 409 se nome duplicado
- ✅ GET /processos: lista processos (200)
- ✅ GET /processos: pagina corretamente
- ✅ GET /processos: filtra por status
- ✅ GET /processos: busca por nome
- ✅ GET /processos/{id}: retorna processo (200)
- ✅ GET /processos/{id}: retorna 404 se não existe
- ✅ GET /processos/{id}/detalhes: inclui relacionamentos
- ✅ PUT /processos/{id}: atualiza processo (200)
- ✅ PATCH /processos/{id}: atualiza parcialmente (200)
- ✅ DELETE /processos/{id}: deleta processo (204)
- ✅ DELETE /processos/{id}: retorna 404 se não existe
- ✅ GET /processos/{id}/metricas: retorna métricas (200)

### 6.4. Edge Cases
- ✅ Processar com nome vazio
- ✅ Processar com nome > 200 chars
- ✅ Pagina com page=0 ou negativo
- ✅ Pagina com per_page > 100
- ✅ Update com todos os campos None (deve retornar erro)
- ✅ Get de processo deletado

## 7. Critérios de Aceitação

### ✅ Repository
- [ ] ProcessoRepository implementado com todos os métodos
- [ ] Queries SQLAlchemy corretas e otimizadas
- [ ] Paginação funciona
- [ ] Filtros aplicados corretamente
- [ ] Testes unitários com cobertura > 90%

### ✅ Service
- [ ] ProcessoService implementado com todos os métodos
- [ ] Validações de negócio funcionam
- [ ] Exceções customizadas levantadas apropriadamente
- [ ] Métricas calculadas corretamente
- [ ] Testes unitários com mocks do repository

### ✅ API
- [ ] Todos os endpoints implementados
- [ ] Status codes corretos
- [ ] Error handling funcional
- [ ] OpenAPI documentation gerada
- [ ] Testes de integração end-to-end

### ✅ Documentação
- [ ] Docstrings em todos os métodos
- [ ] OpenAPI examples fornecidos
- [ ] README atualizado

### ✅ Validação End-to-End
- [ ] Pode criar processo via API
- [ ] Pode listar processos via API
- [ ] Pode obter detalhes via API
- [ ] Pode atualizar via API
- [ ] Pode deletar via API
- [ ] Swagger UI funciona (/docs)

## 8. Notas de Implementação

### 8.1. Ordem de Execução
1. Criar ProcessoRepository com métodos básicos (create, get_by_id, get_all)
2. Testar repository isoladamente
3. Criar ProcessoService com métodos básicos
4. Testar service com mocks
5. Criar endpoints API
6. Testar endpoints end-to-end
7. Adicionar métodos avançados (métricas, detalhes)
8. Documentar

### 8.2. Exemplo de Teste
```python
def test_create_processo(client, db):
    payload = {
        "nome": "Teste Processo",
        "descricao": "Descrição teste"
    }
    response = client.post("/api/v1/processos", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["nome"] == payload["nome"]
    assert "id" in data
```

### 8.3. Pontos de Atenção
- **Transações**: Garantir commit após operações de escrita
- **Validação dupla**: Schemas validam formato, Service valida negócio
- **N+1 queries**: Usar eager loading quando necessário
- **Exceções**: Não deixar exceções SQLAlchemy vazarem para API
- **UUID validation**: FastAPI valida automaticamente se type hint correto
- **Error messages**: Mensagens claras e úteis

## 9. Referências Técnicas

- **FastAPI Bigger Applications**: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- **Repository Pattern**: https://martinfowler.com/eaaCatalog/repository.html
- **SQLAlchemy Queries**: https://docs.sqlalchemy.org/en/20/orm/queryguide/

## 10. Definição de Pronto

Este PRD estará completo quando:
- ✅ Repository, Service e Routes implementados
- ✅ Todos os endpoints funcionais
- ✅ CRUD completo testado
- ✅ Paginação, filtros e ordenação funcionam
- ✅ Métricas agregadas calculadas
- ✅ Validações de negócio aplicadas
- ✅ Error handling robusto
- ✅ Testes com cobertura > 90%
- ✅ OpenAPI documentation completa
- ✅ Pode executar operações via Swagger UI

---

**PRD Anterior**: PRD-004 - Schemas e DTOs
**Próximo PRD**: PRD-006 - Módulo Configuração
