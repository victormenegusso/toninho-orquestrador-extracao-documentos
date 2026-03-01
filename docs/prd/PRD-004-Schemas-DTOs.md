# PRD-004: Schemas e DTOs

**Status**: ✅ Implementado
**Prioridade**: 🔴 Crítica - Fundação Backend (Prioridade 1)
**Categoria**: Backend - Fundação
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Implementar a camada de validação e serialização de dados utilizando Pydantic. Os schemas (DTOs - Data Transfer Objects) definem contratos de entrada e saída da API, separando a representação de dados da persistência (models).

## 2. Contexto e Justificativa

Schemas Pydantic garantem validação automática de dados recebidos pela API e serialização consistente dos responses. Esta separação entre models (persistência) e schemas (API) é crucial para:
- Não expor internos do banco diretamente
- Validar dados antes de chegar aos services
- Documentação automática da API (OpenAPI)
- Type safety em todo o fluxo
- Transformações e computed fields

**Decisões arquiteturais:**
- Pydantic V2 (performance e features modernas)
- Schemas separados para Request e Response
- Config compartilhado via BaseSchema
- Validators customizados para regras de negócio
- Field aliases para nomenclatura da API vs banco
- Computed fields via @computed_field
- Suporte a JSON Schema para documentação

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
toninho/schemas/
├── __init__.py              # Exporta todos os schemas
├── base.py                  # BaseSchema e configs compartilhados
├── processo.py              # Schemas de Processo
├── configuracao.py          # Schemas de Configuração
├── execucao.py              # Schemas de Execução
├── log.py                   # Schemas de Log
├── pagina_extraida.py       # Schemas de Página Extraída
├── responses.py             # Response wrappers padrão
└── validators.py            # Validators reutilizáveis
```

### 3.2. Base Schema (toninho/schemas/base.py)

**BaseSchema**
- ConfigDict padrão para todos os schemas
- from_attributes=True (conversão de ORM models)
- use_enum_values=True (serializar enums como valores)
- populate_by_name=True (aceitar aliases)
- str_strip_whitespace=True (limpar strings)
- validate_assignment=True (validar em atribuições)

**Padrão de Nomenclatura**:
- `*Create`: Request para criar recurso
- `*Update`: Request para atualizar recurso
- `*Response`: Response da API
- `*InDB`: Representação completa do banco (raramente exposto)
- `*Summary`: Versão resumida (listas)

### 3.3. Validators Compartilhados (toninho/schemas/validators.py)

**url_validator**
- Valida formato de URL
- Aceita http, https
- Valida domínio válido

**cron_validator**
- Valida sintaxe de expressão cron
- 5 campos: minuto hora dia mês dia_semana
- Aceita wildcards, ranges, steps

**path_validator**
- Valida caminho de diretório
- Verifica caracteres inválidos
- Normaliza path

**timeout_validator**
- Valida timeout em range (1 a 86400 segundos)

**email_validator** (futuro)
- Valida formato de email

### 3.4. Response Wrappers (toninho/schemas/responses.py)

**SuccessResponse[T]**
```python
class SuccessResponse(BaseModel, Generic[T]):
    data: T
```

**SuccessListResponse[T]**
```python
class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int

class SuccessListResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta
```

**ErrorResponse**
```python
class ErrorDetail(BaseModel):
    field: Optional[str]
    message: str

class ErrorResponse(BaseModel):
    error: dict
        code: str
        message: str
        details: Optional[List[ErrorDetail]]
```

### 3.5. Schemas por Entidade

#### 3.5.1. Processo (toninho/schemas/processo.py)

**ProcessoCreate**
- nome: str (min_length=1, max_length=200)
- descricao: Optional[str]
- status: Optional[ProcessoStatus] = ProcessoStatus.ATIVO

**ProcessoUpdate**
- nome: Optional[str] (min_length=1, max_length=200)
- descricao: Optional[str]
- status: Optional[ProcessoStatus]

**ProcessoResponse**
- id: UUID
- nome: str
- descricao: Optional[str]
- status: ProcessoStatus
- created_at: datetime
- updated_at: datetime
- total_execucoes: int (computed via @computed_field)
- ultima_execucao_em: Optional[datetime] (computed)

**ProcessoSummary** (para listagens)
- id: UUID
- nome: str
- status: ProcessoStatus
- created_at: datetime
- total_execucoes: int

**ProcessoDetail** (com relacionamentos)
- Herda ProcessoResponse
- configuracoes: List[ConfiguracaoResponse]
- execucoes_recentes: List[ExecucaoSummary] (últimas 5)

#### 3.5.2. Configuracao (toninho/schemas/configuracao.py)

**ConfiguracaoCreate**
- processo_id: Optional[UUID] (setado na rota)
- urls: List[HttpUrl] (min_length=1, max_length=100)
- timeout: int = 3600 (ge=1, le=86400)
- max_retries: int = 3 (ge=0, le=10)
- formato_saida: FormatoSaida = FormatoSaida.MULTIPLOS_ARQUIVOS
- output_dir: str (validator: path válido)
- agendamento_cron: Optional[str] (validator: cron válido se presente)
- agendamento_tipo: AgendamentoTipo = AgendamentoTipo.MANUAL

Validator customizado:
- Se agendamento_tipo=RECORRENTE, agendamento_cron obrigatório
- Se agendamento_tipo!=RECORRENTE, agendamento_cron deve ser None

**ConfiguracaoUpdate**
- Todos os campos opcionais (exceto processo_id)
- Mesmas validações do Create

**ConfiguracaoResponse**
- id: UUID
- processo_id: UUID
- urls: List[str]
- timeout: int
- max_retries: int
- formato_saida: FormatoSaida
- output_dir: str
- agendamento_cron: Optional[str]
- agendamento_tipo: AgendamentoTipo
- created_at: datetime
- updated_at: datetime
- proxima_execucao: Optional[datetime] (computed, se agendado)

#### 3.5.3. Execucao (toninho/schemas/execucao.py)

**ExecucaoCreate**
- processo_id: UUID
- Sem outros campos (tudo default ou setado pelo sistema)

**ExecucaoUpdate**
- status: ExecucaoStatus (para transições de estado)
- Validar transições permitidas via validator

**ExecucaoResponse**
- id: UUID
- processo_id: UUID
- status: ExecucaoStatus
- iniciado_em: Optional[datetime]
- finalizado_em: Optional[datetime]
- paginas_processadas: int
- bytes_extraidos: int
- taxa_erro: float
- tentativa_atual: int
- created_at: datetime
- updated_at: datetime
- duracao_segundos: Optional[int] (computed)
- em_andamento: bool (computed)
- progresso_percentual: float (computed, estimado)

**ExecucaoSummary** (para listagens)
- id: UUID
- status: ExecucaoStatus
- iniciado_em: Optional[datetime]
- finalizado_em: Optional[datetime]
- paginas_processadas: int
- duracao_segundos: Optional[int]

**ExecucaoDetail** (com relacionamentos)
- Herda ExecucaoResponse
- processo: ProcessoSummary
- logs_recentes: List[LogResponse] (últimos 20)
- paginas: List[PaginaExtraidaSummary]
- metricas: ExecucaoMetricas

**ExecucaoMetricas**
- tempo_medio_por_pagina: float (segundos)
- taxa_sucesso: float (percentual)
- bytes_por_segundo: float
- paginas_sucesso: int
- paginas_falha: int
- paginas_ignoradas: int

**ExecucaoStatusUpdate** (para endpoints de ação)
- status: ExecucaoStatus (para cancelar, pausar, retomar)

#### 3.5.4. Log (toninho/schemas/log.py)

**LogCreate**
- execucao_id: UUID
- nivel: LogNivel
- mensagem: str (min_length=1)
- contexto: Optional[Dict[str, Any]]

**LogResponse**
- id: UUID
- execucao_id: UUID
- nivel: LogNivel
- mensagem: str
- timestamp: datetime
- contexto: Optional[Dict[str, Any]]

**LogSummary** (para listagens)
- id: UUID
- nivel: LogNivel
- mensagem: str (truncar se > 200 chars)
- timestamp: datetime

**LogFilter** (para queries)
- nivel: Optional[LogNivel]
- desde: Optional[datetime]
- ate: Optional[datetime]
- busca: Optional[str] (busca na mensagem)

#### 3.5.5. Página Extraída (toninho/schemas/pagina_extraida.py)

**PaginaExtraidaCreate**
- execucao_id: UUID
- url_original: HttpUrl
- caminho_arquivo: str
- status: PaginaStatus
- tamanho_bytes: int = 0 (ge=0)
- erro_mensagem: Optional[str]

Validator:
- Se status=FALHOU, erro_mensagem obrigatória

**PaginaExtraidaResponse**
- id: UUID
- execucao_id: UUID
- url_original: str
- caminho_arquivo: str
- status: PaginaStatus
- tamanho_bytes: int
- timestamp: datetime
- erro_mensagem: Optional[str]
- tamanho_legivel: str (computed: "1.5 MB")

**PaginaExtraidaSummary** (para listagens)
- id: UUID
- url_original: str
- status: PaginaStatus
- tamanho_bytes: int
- tamanho_legivel: str

**PaginaExtraidaDetail** (com download link)
- Herda PaginaExtraidaResponse
- download_url: str (computed: `/api/v1/paginas/{id}/download`)
- preview_disponivel: bool (computed: tamanho < 1MB)

#### 3.5.6. Health Check

**HealthResponse**
- status: str ("ok" | "degraded" | "unhealthy")
- timestamp: datetime
- version: str
- services: Dict[str, ServiceHealth]

**ServiceHealth**
- status: str ("ok" | "unhealthy")
- latency_ms: Optional[float]
- message: Optional[str]

**WorkersHealthResponse**
- total_workers: int
- workers_ativos: int
- workers_inativos: int
- tasks_pending: int
- tasks_running: int
- redis_connected: bool

### 3.6. Validators Customizados

#### URL List Validator
```python
@field_validator('urls')
@classmethod
def validate_urls(cls, v: List[str]) -> List[str]:
    if not v:
        raise ValueError("Lista de URLs não pode ser vazia")
    if len(v) > 100:
        raise ValueError("Máximo de 100 URLs permitido")
    # Validar cada URL
    for url in v:
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"URL inválida: {url}")
    return v
```

#### Cron Expression Validator
```python
@field_validator('agendamento_cron')
@classmethod
def validate_cron(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    # Validar sintaxe cron (5 campos)
    parts = v.split()
    if len(parts) != 5:
        raise ValueError("Expressão cron deve ter 5 campos")
    # Validar ranges, wildcards, etc
    return v
```

#### Status Transition Validator
```python
@field_validator('status')
@classmethod
def validate_status_transition(cls, v: ExecucaoStatus, info: ValidationInfo) -> ExecucaoStatus:
    # Validar se transição é permitida baseado em status atual
    # Implementar lógica de máquina de estados
    return v
```

#### Path Validator
```python
@field_validator('output_dir')
@classmethod
def validate_output_dir(cls, v: str) -> str:
    # Validar caracteres inválidos
    # Normalizar path
    # Verificar não é path absoluto perigoso (/etc, /sys, etc)
    return v
```

### 3.7. Computed Fields

**Exemplo: Duração da Execução**
```python
@computed_field
@property
def duracao_segundos(self) -> Optional[int]:
    if self.iniciado_em and self.finalizado_em:
        return int((self.finalizado_em - self.iniciado_em).total_seconds())
    return None
```

**Exemplo: Tamanho Legível**
```python
@computed_field
@property
def tamanho_legivel(self) -> str:
    bytes = self.tamanho_bytes
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"
```

**Exemplo: Download URL**
```python
@computed_field
@property
def download_url(self) -> str:
    return f"/api/v1/paginas/{self.id}/download"
```

### 3.8. Model Serialization

Converter de Model (SQLAlchemy) para Schema (Pydantic):
```python
# Automático via from_attributes=True
processo_model = db.query(Processo).first()
processo_response = ProcessoResponse.model_validate(processo_model)

# Manual se necessário
processo_response = ProcessoResponse(
    id=processo_model.id,
    nome=processo_model.nome,
    # ...
)
```

## 4. Dependências

### 4.1. Pré-requisitos
- Pydantic V2 instalado via Poetry
- Models implementados (PRD-003)

### 4.2. Dependências de Outros PRDs
- **PRD-003**: Models e Database (schemas mapeiam models)

### 4.3. PRDs Subsequentes
Todos os PRDs de API dependem de schemas:
- PRD-005 a PRD-009: Módulos de entidades (usam schemas)
- PRD-012: Monitoramento (schemas de health, métricas)

## 5. Regras de Negócio

### 5.1. Validação de Entrada
- **Strings**: Trim automático de whitespace
- **URLs**: Validar formato e protocolo
- **Ranges**: Validar min/max conforme regras
- **Cron**: Validar sintaxe se agendamento recorrente
- **Status**: Validar transições permitidas

### 5.2. Serialização de Saída
- **Datas**: ISO 8601 format (YYYY-MM-DDTHH:MM:SS.sssZ)
- **UUIDs**: String format
- **Enums**: String values (não ordinais)
- **Nulls**: Omitir campos null em responses (exclude_none)
- **Computed fields**: Calculados dinamicamente, não persistidos

### 5.3. Documentação Automática
- **Field descriptions**: Todas as fields com description
- **Examples**: Fornecer examples para documentação OpenAPI
- **Tags**: Usar tags para organizar documentação
- **Summaries**: Docstrings claros em schemas

### 5.4. Versionamento
- **Schema changes**: Mudanças breaking = nova versão da API
- **Backward compatibility**: Manter compatibilidade quando possível
- **Deprecation**: Marcar campos deprecated antes de remover

## 6. Casos de Teste

### 6.1. Testes de Validação
- ✅ Criar schema com dados válidos
- ✅ Criar schema com dados inválidos (deve levantar ValidationError)
- ✅ Validar ranges (min/max)
- ✅ Validar formato de URL
- ✅ Validar cron expression
- ✅ Validar status transitions
- ✅ Validar campos obrigatórios
- ✅ Validar tipo de dados

### 6.2. Testes de Serialização
- ✅ Model → Schema conversion
- ✅ Schema → dict
- ✅ Schema → JSON
- ✅ Enums serializados como strings
- ✅ Datas no formato ISO 8601
- ✅ Computed fields calculados corretamente

### 6.3. Testes de Validators
- ✅ URL validator aceita URLs válidas
- ✅ URL validator rejeita URLs inválidas
- ✅ Cron validator aceita expressões válidas
- ✅ Cron validator rejeita expressões inválidas
- ✅ Path validator normaliza caminhos
- ✅ Timeout validator respeita ranges

### 6.4. Testes de Computed Fields
- ✅ duracao_segundos calculado corretamente
- ✅ tamanho_legivel formatado corretamente
- ✅ download_url gerado corretamente
- ✅ Computed fields não causam N+1 queries

### 6.5. Testes de Response Wrappers
- ✅ SuccessResponse[T] serializa data
- ✅ SuccessListResponse[T] inclui meta de paginação
- ✅ ErrorResponse formata erros corretamente

## 7. Critérios de Aceitação

### ✅ Schemas
- [ ] Todos os schemas criados (Processo, Configuracao, Execucao, Log, PaginaExtraida)
- [ ] Schemas Create, Update, Response para cada entidade
- [ ] BaseSchema configurado
- [ ] Response wrappers criados
- [ ] Validators compartilhados implementados

### ✅ Validação
- [ ] Todos os campos com validação apropriada
- [ ] Validators customizados funcionais
- [ ] Validação de URLs
- [ ] Validação de cron expressions
- [ ] Validação de ranges
- [ ] Field constraints (min/max length, ge/le)

### ✅ Serialização
- [ ] Models convertem para schemas sem erros
- [ ] Schemas serializam para JSON corretamente
- [ ] Datas no formato ISO 8601
- [ ] Enums como strings
- [ ] Computed fields funcionais

### ✅ Documentação
- [ ] Todas as fields com description
- [ ] Examples fornecidos
- [ ] Docstrings em schemas
- [ ] OpenAPI schema gerado corretamente

### ✅ Testes
- [ ] Testes de validação com cobertura > 90%
- [ ] Testes de serialização
- [ ] Testes de validators customizados
- [ ] Testes de computed fields
- [ ] Testes de conversão model → schema

## 8. Notas de Implementação

### 8.1. Ordem de Execução Sugerida
1. Criar base.py com BaseSchema
2. Criar validators.py com validators compartilhados
3. Criar responses.py com wrappers
4. Criar schemas na ordem (Processo → Configuracao → Execucao → Log → PaginaExtraida)
5. Criar schemas auxiliares (Health, Metricas, Filters)
6. Testar validação de cada schema
7. Testar serialização model → schema
8. Testar computed fields
9. Validar documentação OpenAPI gerada

### 8.2. Pydantic V2 Features
```python
from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict

class ProcessoCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str = Field(..., min_length=1, max_length=200, description="Nome do processo")

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()

    @computed_field
    @property
    def nome_upper(self) -> str:
        return self.nome.upper()
```

### 8.3. Conversão Model → Schema
```python
# Simples
from toninho.models import Processo
from toninho.schemas import ProcessoResponse

processo = db.query(Processo).first()
schema = ProcessoResponse.model_validate(processo)

# Com relacionamentos (eager loading)
from sqlalchemy.orm import selectinload

processo = db.query(Processo)\
    .options(selectinload(Processo.configuracoes))\
    .first()
schema = ProcessoDetail.model_validate(processo)
```

### 8.4. Validação Manual
```bash
# No REPL Python
from toninho.schemas import ProcessoCreate, ProcessoResponse

# Teste Create schema
data = {"nome": "Teste", "descricao": "Desc"}
schema = ProcessoCreate(**data)
print(schema.model_dump())

# Teste validação falha
try:
    ProcessoCreate(nome="")  # Deve falhar
except ValidationError as e:
    print(e.errors())

# Teste conversão de model
from toninho.models import Processo
from toninho.core.database import SessionLocal

db = SessionLocal()
p = Processo(nome="Test", descricao="Test")
db.add(p)
db.commit()

schema = ProcessoResponse.model_validate(p)
print(schema.model_dump_json())
```

### 8.5. Pontos de Atenção
- **Pydantic V2**: API diferente da V1, consultar documentação
- **Circular imports**: Cuidado com schemas que referenciam outros, usar ForwardRef se necessário
- **Performance**: Computed fields calculados toda vez, cachear se pesado
- **Validators**: Ordem de execução pode importar
- **from_attributes**: Necessário para converter ORM models
- **Exclude**: Usar exclude_none, exclude_unset conforme caso
- **JSON Schema**: OpenAPI gerado automaticamente, verificar se está legível

## 9. Referências Técnicas

- **Pydantic V2**: https://docs.pydantic.dev/latest/
- **Pydantic Validators**: https://docs.pydantic.dev/latest/concepts/validators/
- **Computed Fields**: https://docs.pydantic.dev/latest/concepts/computed_fields/
- **FastAPI Response Models**: https://fastapi.tiangolo.com/tutorial/response-model/
- **OpenAPI Schema**: https://swagger.io/specification/

## 10. Definição de Pronto

Este PRD estará completo quando:
- ✅ Todos os schemas criados e documentados
- ✅ Validação funciona para todos os campos
- ✅ Validators customizados implementados e testados
- ✅ Serialização model → schema funciona sem erros
- ✅ Computed fields calculados corretamente
- ✅ Response wrappers padronizam respostas
- ✅ Testes com cobertura > 90%
- ✅ OpenAPI documentation gerada e legível
- ✅ Examples fornecidos para principais schemas
- ✅ Pode criar instâncias de schemas com dados válidos
- ✅ Pode serializar para JSON sem erros

---

**PRD Anterior**: PRD-003 - Models e Database
**Próximo PRD**: PRD-005 - Módulo Processo
