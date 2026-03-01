# PRD-003: Models e Database

**Status**: ✅ Implementado
**Prioridade**: 🔴 Crítica - Fundação Backend (Prioridade 1)
**Categoria**: Backend - Fundação
**Estimativa**: 8-10 horas

---

## 1. Objetivo

Implementar a camada de persistência do Toninho utilizando SQLAlchemy 2.0+ como ORM e Alembic para gerenciamento de migrations. Este PRD define as entidades do domínio (Models), enums, relacionamentos e configuração do banco de dados SQLite.

## 2. Contexto e Justificativa

O modelo de dados é a fundação do sistema. Todas as funcionalidades dependem dessas entidades para armazenar e recuperar informações. O design segue princípios de normalização e integridade referencial, com relacionamentos claros entre Process, Configuração, Execução, Log e PáginaExtraída.

**Decisões arquiteturais:**
- SQLAlchemy 2.0+ com estilo moderno (mapped_column, Mapped)
- SQLite para MVP (single-user, uso local)
- UUIDs como primary keys (distribuído-friendly, sem colisões)
- Timestamps automáticos (created_at, updated_at via eventos)
- Enums Python mapeados para strings no banco (legibilidade)
- JSON para dados semiestruturados (urls, contexto de logs)
- Soft-delete NÃO implementado (deleção física conforme escopo MVP)

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
toninho/models/
├── __init__.py              # Exporta todos os models
├── base.py                  # Base class e mixins
├── processo.py              # Model Processo
├── configuracao.py          # Model Configuracao
├── execucao.py              # Model Execucao
├── log.py                   # Model Log
├── pagina_extraida.py       # Model PaginaExtraida
└── enums.py                 # Enums compartilhados

toninho/core/
├── database.py              # Engine, SessionLocal, Base
└── config.py                # Settings (pydantic-settings)

migrations/                  # Alembic migrations
├── versions/
├── env.py
├── script.py.mako
└── alembic.ini
```

### 3.2. Enums (toninho/models/enums.py)

Todos os enums devem:
- Herdar de `str` e `enum.Enum` (serialização JSON automática)
- Ter valores string descritivos (não números)
- Ter docstring explicando cada valor

**ProcessoStatus**
```python
class ProcessoStatus(str, Enum):
    ATIVO = "ativo"           # Processo ativo e operacional
    INATIVO = "inativo"       # Processo desativado temporariamente
    ARQUIVADO = "arquivado"   # Processo arquivado (não aparece em listagens)
```

**FormatoSaida**
```python
class FormatoSaida(str, Enum):
    ARQUIVO_UNICO = "arquivo_unico"       # Todas as páginas em um único markdown
    MULTIPLOS_ARQUIVOS = "multiplos_arquivos"  # Uma página por arquivo
```

**AgendamentoTipo**
```python
class AgendamentoTipo(str, Enum):
    RECORRENTE = "recorrente"  # Execução recorrente via cron
    ONE_TIME = "one_time"      # Execução única agendada
    MANUAL = "manual"          # Sem agendamento, execução manual
```

**ExecucaoStatus**
```python
class ExecucaoStatus(str, Enum):
    CRIADO = "criado"                     # Execução criada, aguardando
    AGUARDANDO = "aguardando"             # Na fila, aguardando worker
    EM_EXECUCAO = "em_execucao"           # Sendo processada por worker
    PAUSADO = "pausado"                   # Pausada manualmente
    CONCLUIDO = "concluido"               # Finalizada com sucesso
    FALHOU = "falhou"                     # Finalizada com erro total
    CANCELADO = "cancelado"               # Cancelada pelo usuário
    CONCLUIDO_COM_ERROS = "concluido_com_erros"  # Sucesso parcial
```

**LogNivel**
```python
class LogNivel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
```

**PaginaStatus**
```python
class PaginaStatus(str, Enum):
    SUCESSO = "sucesso"    # Página extraída com sucesso
    FALHOU = "falhou"      # Falha na extração
    IGNORADO = "ignorado"  # Página ignorada (filtros, duplicada, etc)
```

### 3.3. Base e Mixins (toninho/models/base.py)

**Base Class**
- DeclarativeBase do SQLAlchemy
- Metadata configurado
- Convenção de nomenclatura para constraints

**TimestampMixin**
- `created_at`: DateTime com default=func.now()
- `updated_at`: DateTime com default=func.now(), onupdate=func.now()
- Timezone: UTC
- Evento SQLAlchemy para garantir updated_at

**UUIDMixin**
- `id`: UUID primary key com default=uuid.uuid4

### 3.4. Models

#### 3.4.1. Processo (toninho/models/processo.py)

**Tabela**: `processos`

**Campos**:
- `id`: UUID (PK) via UUIDMixin
- `nome`: String(200), not null, indexed
- `descricao`: Text, nullable
- `status`: Enum(ProcessoStatus), not null, default=ATIVO, indexed
- `created_at`: DateTime via TimestampMixin
- `updated_at`: DateTime via TimestampMixin

**Relacionamentos**:
- `configuracoes`: relationship → Configuracao (1:N), back_populates="processo", cascade="all, delete-orphan"
- `execucoes`: relationship → Execucao (1:N), back_populates="processo", cascade="all, delete-orphan"

**Constraints**:
- unique constraint em `nome` (nomes únicos)

**Índices**:
- idx_processo_nome (nome)
- idx_processo_status (status)
- idx_processo_created_at (created_at DESC) para ordenação

**Validações de Domínio**:
- nome: não vazio, max 200 caracteres
- status: deve ser valor válido de ProcessoStatus

#### 3.4.2. Configuracao (toninho/models/configuracao.py)

**Tabela**: `configuracoes`

**Campos**:
- `id`: UUID (PK) via UUIDMixin
- `processo_id`: UUID (FK → processos.id), not null, indexed
- `urls`: JSON, not null (lista de strings)
- `timeout`: Integer, not null, default=3600 (segundos)
- `max_retries`: Integer, not null, default=3
- `formato_saida`: Enum(FormatoSaida), not null, default=MULTIPLOS_ARQUIVOS
- `output_dir`: String(500), not null
- `agendamento_cron`: String(100), nullable (expressão cron)
- `agendamento_tipo`: Enum(AgendamentoTipo), not null, default=MANUAL
- `created_at`: DateTime via TimestampMixin
- `updated_at`: DateTime via TimestampMixin

**Relacionamentos**:
- `processo`: relationship → Processo (N:1), back_populates="configuracoes"

**Constraints**:
- FK para processos.id com ON DELETE CASCADE
- Check constraint: timeout > 0
- Check constraint: max_retries >= 0 AND max_retries <= 10

**Índices**:
- idx_configuracao_processo_id (processo_id)
- idx_configuracao_agendamento_tipo (agendamento_tipo)

**Validações de Domínio**:
- urls: JSON válido, lista não vazia de URLs
- timeout: > 0, <= 86400 (24h)
- max_retries: >= 0, <= 10
- output_dir: caminho válido
- agendamento_cron: validar sintaxe cron se tipo=RECORRENTE

#### 3.4.3. Execucao (toninho/models/execucao.py)

**Tabela**: `execucoes`

**Campos**:
- `id`: UUID (PK) via UUIDMixin
- `processo_id`: UUID (FK → processos.id), not null, indexed
- `status`: Enum(ExecucaoStatus), not null, default=CRIADO, indexed
- `iniciado_em`: DateTime, nullable
- `finalizado_em`: DateTime, nullable
- `paginas_processadas`: Integer, not null, default=0
- `bytes_extraidos`: BigInteger, not null, default=0
- `taxa_erro`: Float, not null, default=0.0 (percentual 0-100)
- `tentativa_atual`: Integer, not null, default=1
- `created_at`: DateTime via TimestampMixin
- `updated_at`: DateTime via TimestampMixin

**Relacionamentos**:
- `processo`: relationship → Processo (N:1), back_populates="execucoes"
- `logs`: relationship → Log (1:N), back_populates="execucao", cascade="all, delete-orphan", order_by="Log.timestamp"
- `paginas`: relationship → PaginaExtraida (1:N), back_populates="execucao", cascade="all, delete-orphan"

**Constraints**:
- FK para processos.id com ON DELETE CASCADE
- Check constraint: paginas_processadas >= 0
- Check constraint: bytes_extraidos >= 0
- Check constraint: taxa_erro >= 0.0 AND taxa_erro <= 100.0
- Check constraint: tentativa_atual > 0

**Índices**:
- idx_execucao_processo_id (processo_id)
- idx_execucao_status (status)
- idx_execucao_created_at (created_at DESC)
- idx_execucao_processo_created (processo_id, created_at DESC) composto

**Validações de Domínio**:
- iniciado_em < finalizado_em (se ambos presentes)
- status transicionável (máquina de estados válida)
- tentativa_atual <= max_retries do processo

**Computed Properties** (via @property, não persistido):
- `duracao`: finalizado_em - iniciado_em (timedelta)
- `em_andamento`: status in (AGUARDANDO, EM_EXECUCAO)
- `finalizado`: status in (CONCLUIDO, FALHOU, CANCELADO, CONCLUIDO_COM_ERROS)

#### 3.4.4. Log (toninho/models/log.py)

**Tabela**: `logs`

**Campos**:
- `id`: UUID (PK) via UUIDMixin
- `execucao_id`: UUID (FK → execucoes.id), not null, indexed
- `nivel`: Enum(LogNivel), not null, indexed
- `mensagem`: Text, not null
- `timestamp`: DateTime, not null, default=func.now(), indexed
- `contexto`: JSON, nullable (dados adicionais estruturados)

**Relacionamentos**:
- `execucao`: relationship → Execucao (N:1), back_populates="logs"

**Constraints**:
- FK para execucoes.id com ON DELETE CASCADE

**Índices**:
- idx_log_execucao_id (execucao_id)
- idx_log_timestamp (timestamp DESC)
- idx_log_nivel (nivel)
- idx_log_execucao_timestamp (execucao_id, timestamp DESC) composto

**Validações de Domínio**:
- mensagem: não vazia
- contexto: JSON válido se presente

**Observação**:
Logs são append-only. Nunca devem ser atualizados, apenas inseridos.

#### 3.4.5. PaginaExtraida (toninho/models/pagina_extraida.py)

**Tabela**: `paginas_extraidas`

**Campos**:
- `id`: UUID (PK) via UUIDMixin
- `execucao_id`: UUID (FK → execucoes.id), not null, indexed
- `url_original`: String(2048), not null
- `caminho_arquivo`: String(1000), not null
- `status`: Enum(PaginaStatus), not null, indexed
- `tamanho_bytes`: Integer, not null, default=0
- `timestamp`: DateTime, not null, default=func.now()
- `erro_mensagem`: Text, nullable

**Relacionamentos**:
- `execucao`: relationship → Execucao (N:1), back_populates="paginas"

**Constraints**:
- FK para execucoes.id com ON DELETE CASCADE
- Check constraint: tamanho_bytes >= 0

**Índices**:
- idx_pagina_execucao_id (execucao_id)
- idx_pagina_status (status)
- idx_pagina_url (url_original) para busca por URL
- idx_pagina_execucao_status (execucao_id, status) composto

**Validações de Domínio**:
- url_original: URL válida
- caminho_arquivo: caminho de arquivo válido
- erro_mensagem: obrigatória se status=FALHOU

### 3.5. Database Configuration (toninho/core/database.py)

**Engine**:
- SQLite via DATABASE_URL do settings
- connect_args: `{"check_same_thread": False}` (FastAPI threading)
- pool_pre_ping: True (detectar conexões fechadas)
- echo: True em DEBUG mode (log queries SQL)

**SessionLocal**:
- sessionmaker configurado com engine
- autocommit=False, autoflush=False (controle explícito)
- expire_on_commit=False (objetos usáveis após commit)

**Base**:
- DeclarativeBase exportado para uso nos models

**Dependency Injection**:
```python
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency para injetar sessão de banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.6. Alembic Migrations

#### 3.6.1. Configuração (alembic.ini)
- script_location = migrations
- sqlalchemy.url = (carregado de settings)
- file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s

#### 3.6.2. env.py
Configurar para:
- Importar Base e todos os models
- Carregar DATABASE_URL de settings
- Suportar online e offline migrations
- Incluir metadata.schema para todos os models

#### 3.6.3. Migration Inicial
Criar migration que:
- Cria todas as tabelas
- Cria todos os índices
- Cria todos os constraints
- Insere dados de seed se necessário (opcional)

Comando: `alembic revision --autogenerate -m "initial schema"`

#### 3.6.4. Scripts Úteis
- `alembic upgrade head`: aplica migrations
- `alembic downgrade -1`: reverte última migration
- `alembic current`: mostra versão atual
- `alembic history`: mostra histórico de migrations

### 3.7. Settings (toninho/core/config.py)

Configuração centralizada com Pydantic BaseSettings:

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./toninho.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"

    # Outros settings conforme necessário...

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()  # Singleton
```

## 4. Dependências

### 4.1. Pré-requisitos
- Python 3.11+ instalado
- SQLAlchemy 2.0+ instalado via Poetry
- Alembic instalado via Poetry
- pydantic-settings instalado

### 4.2. Dependências de Outros PRDs
- **PRD-001**: Setup do Projeto (estrutura de pastas)
- **PRD-002**: Ambiente de Desenvolvimento (Poetry, Docker)

### 4.3. PRDs Subsequentes
Todos os PRDs de implementação dependem dos models:
- PRD-004: Schemas e DTOs
- PRD-005 a PRD-009: Módulos de entidades
- PRD-010: Workers (usa models para persistência)
- PRD-011: Sistema de Extração (persiste dados)

## 5. Regras de Negócio

### 5.1. Integridade de Dados
- **Cascata de deleção**: Deletar Processo deleta Configurações e Execuções
- **Cascata de deleção**: Deletar Execução deleta Logs e PáginasExtraídas
- **Atomicidade**: Todas as operações devem usar transações
- **Validação**: Models validam dados antes de insert/update

### 5.2. Timestamps
- **created_at**: Setado automaticamente na criação, nunca atualizado
- **updated_at**: Atualizado automaticamente em toda modificação
- **Timezone**: Sempre UTC, conversão para local na apresentação

### 5.3. UUIDs
- **Geração**: uuid.uuid4() (random UUID)
- **Formato**: String no banco para compatibilidade SQLite
- **Exposição**: String em APIs, nunca int

### 5.4. Enums
- **Persistência**: String values no banco (não ordinals)
- **Validação**: SQLAlchemy valida valores via Enum Python
- **Serialização**: Automática para JSON via herança de str

### 5.5. Status Transitions (Execução)
Transições válidas de ExecucaoStatus:
- CRIADO → AGUARDANDO
- AGUARDANDO → EM_EXECUCAO
- EM_EXECUCAO → PAUSADO
- PAUSADO → EM_EXECUCAO
- EM_EXECUCAO → CONCLUIDO
- EM_EXECUCAO → FALHOU
- EM_EXECUCAO → CANCELADO
- EM_EXECUCAO → CONCLUIDO_COM_ERROS
- Qualquer estado terminal (CONCLUIDO, FALHOU, CANCELADO) → imutável

### 5.6. Constraints de Negócio
- **URLs**: Lista não vazia em Configuração
- **Timeout**: Máximo 24 horas (86400 segundos)
- **Retries**: Máximo 10 tentativas
- **Taxa de Erro**: Percentual entre 0-100
- **Nome de Processo**: Único no sistema

## 6. Casos de Teste

### 6.1. Testes de Models
- ✅ Criar cada model com dados válidos
- ✅ Validar defaults são aplicados
- ✅ Validar constraints são respeitados (unique, not null, check)
- ✅ Validar relacionamentos funcionam (lazy loading, eager loading)
- ✅ Validar cascata de deleção
- ✅ Validar enums aceitam apenas valores válidos
- ✅ Validar timestamps são setados automaticamente

### 6.2. Testes de Database
- ✅ Criar engine e conectar
- ✅ Criar tabelas via metadata.create_all()
- ✅ Inserir dados em cada tabela
- ✅ Queries básicas (select, filter, order_by)
- ✅ Transações commit e rollback
- ✅ Session lifecycle (create, use, close)

### 6.3. Testes de Migrations
- ✅ Alembic upgrade head aplica migrations
- ✅ Alembic downgrade base reverte migrations
- ✅ Schema resultante match models
- ✅ Índices são criados
- ✅ Constraints são criados

### 6.4. Testes de Relacionamentos
- ✅ Processo com múltiplas Configurações
- ✅ Processo com múltiplas Execuções
- ✅ Execução com múltiplos Logs
- ✅ Execução com múltiplas PáginasExtraídas
- ✅ Deletar Processo deleta cascata
- ✅ Deletar Execução deleta cascata

### 6.5. Testes de Validação
- ✅ Criar Processo com nome vazio (deve falhar)
- ✅ Criar Configuração com timeout negativo (deve falhar)
- ✅ Criar Execução com taxa_erro > 100 (deve falhar)
- ✅ Criar dois Processos com mesmo nome (deve falhar)

## 7. Critérios de Aceitação

### ✅ Models
- [ ] Todos os 5 models criados (Processo, Configuracao, Execucao, Log, PaginaExtraida)
- [ ] Todos os enums definidos
- [ ] Base class e mixins implementados
- [ ] Relacionamentos configurados
- [ ] Constraints e índices definidos
- [ ] Docstrings em todas as classes e campos

### ✅ Database
- [ ] database.py configurado com engine e session
- [ ] get_db() dependency funcional
- [ ] Conecta com SQLite sem erros

### ✅ Migrations
- [ ] Alembic configurado (alembic.ini, env.py)
- [ ] Migration inicial criada
- [ ] `alembic upgrade head` cria todas as tabelas
- [ ] `alembic downgrade base` remove todas as tabelas
- [ ] Schema no banco match models Python

### ✅ Settings
- [ ] config.py com Settings usando Pydantic
- [ ] Carrega variáveis de .env
- [ ] Defaults adequados

### ✅ Testes
- [ ] Testes unitários para cada model
- [ ] Testes de relacionamentos
- [ ] Testes de validação
- [ ] Testes de migrations
- [ ] Coverage > 90% para models/

### ✅ Documentação
- [ ] README em models/ explicando estrutura
- [ ] Docstrings em todos os models
- [ ] Comentários em constraints complexos
- [ ] Diagrama ER atualizado (se necessário)

## 8. Notas de Implementação

### 8.1. Ordem de Execução Sugerida
1. Criar enums.py com todos os enums
2. Criar base.py com Base, mixins
3. Criar models na ordem (Processo → Configuracao → Execucao → Log → PaginaExtraida)
4. Criar database.py com engine e session
5. Atualizar config.py com settings
6. Inicializar Alembic: `alembic init migrations`
7. Configurar env.py do Alembic
8. Criar migration inicial: `alembic revision --autogenerate -m "initial"`
9. Aplicar migration: `alembic upgrade head`
10. Verificar schema: sqlite3 toninho.db ".schema"
11. Escrever testes

### 8.2. SQLAlchemy 2.0 Style
Usar novo estilo (não legacy):
```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

class Processo(Base):
    __tablename__ = "processos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
```

### 8.3. JSON Fields
Para campos JSON (urls, contexto):
```python
from sqlalchemy import JSON
from typing import List, Dict, Any

urls: Mapped[List[str]] = mapped_column(JSON, nullable=False)
contexto: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
```

### 8.4. Validação Manual
```bash
# Entrar no container
./scripts/shell.sh

# Dentro do container
python

# No REPL Python
from toninho.core.database import engine, Base
from toninho.models import Processo, Configuracao, Execucao, Log, PaginaExtraida

# Criar tabelas
Base.metadata.create_all(engine)

# Verificar
from sqlalchemy import inspect
inspector = inspect(engine)
print(inspector.get_table_names())

# Testar inserção
from toninho.core.database import SessionLocal
db = SessionLocal()
p = Processo(nome="Teste", descricao="Teste")
db.add(p)
db.commit()
db.refresh(p)
print(p.id, p.created_at)
```

### 8.5. Pontos de Atenção
- **SQLAlchemy 2.0**: Usar estilo moderno, evitar legacy patterns
- **SQLite limitações**: Sem ALTER TABLE avançado, cuidado com migrations
- **UUIDs**: SQLite armazena como string, converter se necessário
- **JSON**: SQLite suporta JSON, mas queries JSON são limitadas
- **Timestamps**: Garantir UTC, timezone-aware
- **Cascade**: Testar bem antes de usar em produção
- **Indexes**: Não exagerar, balancear leitura vs escrita

## 9. Referências Técnicas

- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Pydantic Settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **SQLite**: https://www.sqlite.org/docs.html
- **FastAPI Database**: https://fastapi.tiangolo.com/tutorial/sql-databases/

## 10. Definição de Pronto

Este PRD estará completo quando:
- ✅ Todos os models criados e testados
- ✅ Alembic configurado e migration inicial aplicada
- ✅ Todas as tabelas existem no banco
- ✅ Relacionamentos funcionam corretamente
- ✅ Constraints e validações funcionais
- ✅ Timestamps automáticos funcionando
- ✅ Testes unitários com cobertura > 90%
- ✅ Pode inserir, atualizar, deletar registros
- ✅ Cascata de deleção funciona conforme esperado
- ✅ Enums serializam/deserializam corretamente
- ✅ Documentação completa nos models

---

**PRD Anterior**: PRD-002 - Ambiente de Desenvolvimento
**Próximo PRD**: PRD-004 - Schemas e DTOs
