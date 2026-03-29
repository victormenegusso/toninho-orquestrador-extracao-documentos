# PRD-026: Módulo Volume — Gerenciamento de Volumes de Saída

**Status**: 📋 Planejado
**Prioridade**: 🟠 Alta — Infraestrutura de Armazenamento
**Categoria**: Backend + Frontend — Nova Entidade
**Depende de**: PRD-003, PRD-004, PRD-005, PRD-006, PRD-014, PRD-015

---

## 1. Objetivo

Implementar um módulo completo de **gerenciamento de volumes** para substituir o campo de texto livre `output_dir` na configuração de processos. Volumes são diretórios de saída cadastrados, validados (leitura/escrita) e reutilizáveis, eliminando problemas recorrentes de configuração de paths em ambientes Docker/VPN.

## 2. Contexto e Justificativa

### 2.1. Problema Atual

Hoje o campo `output_dir` no model `Configuracao` é um `String(500)` de texto livre. O frontend oferece dois atalhos (`./output` e `/tmp/output`), mas o usuário pode digitar qualquer path. Isso gera:

- **Erros de acesso em Docker**: paths como `/tmp/` não são persistidos entre restarts de containers.
- **Erros de VPN/rede**: paths montados via rede podem estar inacessíveis.
- **Inconsistência**: cada processo pode apontar para um path diferente sem validação prévia.
- **Sem feedback**: o sistema não valida se o path existe ou se tem permissões de leitura/escrita até a hora da execução, quando já é tarde.
- **Difícil gerenciamento**: não há visibilidade centralizada de quais diretórios estão sendo usados.

### 2.2. Solução Proposta

Criar uma entidade **Volume** que:

1. Cadastra diretórios de saída com **nome amigável** + **path**.
2. **Valida** leitura/escrita no momento do cadastro/edição.
3. Possui **tipo** (local, cloud, bd) preparado para expansão futura — inicialmente apenas `local`.
4. Possui **status** (ativo/inativo) para desativar sem deletar.
5. Substitui o campo texto livre por um **combo/select** no formulário de processo.
6. **Migra automaticamente** configurações existentes.

### 2.3. Stack de Referência

| Componente | Tecnologia | Uso neste PRD |
|---|---|---|
| Model | SQLAlchemy 2.0+ (mapped_column, Mapped) | Entidade Volume |
| Schema | Pydantic v2 (BaseModel) | DTOs de entrada/saída |
| API | FastAPI (APIRouter) | Endpoints REST |
| Frontend | HTMX + Alpine.js + TailwindCSS | CRUD de volumes + combo no form de processo |
| Migração | Alembic | Novo model + migração de dados |
| Validação | pathlib + os | Checar leitura/escrita em paths |
| DB | SQLite (MVP) | Persistência |

---

## 3. Requisitos Funcionais

### RF-01: Cadastro de Volume
- Usuário pode criar um volume informando **nome** e **path**.
- O sistema valida se o path é acessível (leitura + escrita) no momento do cadastro.
- O campo **tipo** é definido automaticamente como `local` (único disponível no MVP).
- Nomes de volumes devem ser únicos.
- Paths devem ser únicos (não permitir dois volumes apontando para o mesmo diretório).

### RF-02: Validação de Acesso
- Ao criar ou editar um volume, o sistema tenta:
  1. Verificar se o diretório existe (se não, tenta criar).
  2. Escrever um arquivo temporário de teste.
  3. Ler o arquivo temporário.
  4. Deletar o arquivo temporário.
- Se qualquer etapa falhar, retorna erro descritivo (ex: "Sem permissão de escrita em /app/data").
- A validação ocorre **somente na criação/edição** do volume.

### RF-03: Listagem de Volumes
- Listar todos os volumes com: nome, path, tipo, status, quantidade de processos vinculados.
- Filtrar por status (ativo/inativo).

### RF-04: Edição de Volume
- Permitir editar nome, path e status.
- Revalidar acesso ao alterar o path.
- Não permitir alterar o tipo (futuro: migração entre tipos).

### RF-05: Exclusão de Volume
- **Bloquear exclusão** se o volume está sendo usado por alguma configuração de processo.
- Informar quais processos estão usando o volume na mensagem de erro.

### RF-06: Status Ativo/Inativo
- Volumes inativos **não aparecem** no combo de seleção ao criar/editar processo.
- Volumes inativos ainda podem ser usados por processos já configurados (não quebra existente).
- Volumes inativos aparecem na listagem de volumes com indicação visual.

### RF-07: Combo no Formulário de Processo
- No formulário de criação/edição de processo, o campo `output_dir` (texto livre) é substituído por um **select/combo** com os volumes ativos.
- Exibe: `{nome} — {path}`.
- Se o processo já tem configuração com volume, vem pré-selecionado.

### RF-08: Volume Padrão
- Na primeira execução (seed/migração), criar automaticamente um volume padrão:
  - **Nome**: "Saída Padrão"
  - **Path**: `./output`
  - **Tipo**: `local`
  - **Status**: `ativo`
- Configurações existentes com `output_dir` são migradas para referenciar volumes criados automaticamente.

### RF-09: Migração Automática de Dados
- A migração Alembic deve:
  1. Criar a tabela `volumes`.
  2. Extrair paths únicos de `configuracoes.output_dir`.
  3. Criar um Volume para cada path único encontrado (nome auto-gerado a partir do path).
  4. Adicionar coluna `volume_id` (FK) em `configuracoes`.
  5. Popular `volume_id` baseado no `output_dir` de cada configuração.
  6. Remover a coluna `output_dir` de `configuracoes` (ou manter como deprecated/nullable para rollback seguro).

### RF-10: Tela de Gerenciamento (Frontend)
- Nova entrada na **sidebar**: "Volumes" (ícone de disco/armazenamento).
- Tela de listagem com tabela: nome, path, tipo, status, processos vinculados, ações.
- Modal ou página para criar/editar volume.
- Indicação visual de status (badge verde/cinza).
- Botão de "testar conexão" que revalida o acesso ao path.

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos

```
toninho/models/
└── volume.py                    # Model Volume

toninho/models/enums.py          # Adicionar VolumeStatus e VolumeTipo

toninho/schemas/
└── volume.py                    # Schemas VolumeCreate, VolumeUpdate, VolumeResponse

toninho/repositories/
└── volume_repository.py         # Repository Layer

toninho/services/
└── volume_service.py            # Service Layer (com validação de path)

toninho/api/routes/
└── volumes.py                   # API Routes

frontend/templates/pages/volumes/
├── index.html                   # Listagem de volumes
├── create.html                  # Criar volume
└── edit.html                    # Editar volume

frontend/templates/components/
└── volume_select.html           # Componente combo para formulários

migrations/versions/
└── xxx_add_volume_model.py      # Migração Alembic
```

### 4.2. Enums (toninho/models/enums.py)

```python
class VolumeStatus(str, Enum):
    ATIVO = "ativo"       # Volume disponível para uso
    INATIVO = "inativo"   # Volume desativado (não aparece no combo)

class VolumeTipo(str, Enum):
    LOCAL = "local"       # Diretório local no filesystem
    # Futuros tipos:
    # CLOUD_S3 = "cloud_s3"       # Amazon S3
    # CLOUD_GCS = "cloud_gcs"     # Google Cloud Storage
    # CLOUD_AZURE = "cloud_azure" # Azure Blob Storage
    # DATABASE = "database"       # Armazenamento em banco de dados
```

### 4.3. Model Volume (toninho/models/volume.py)

**Tabela**: `volumes`

**Campos**:
- `id`: UUID (PK) via UUIDMixin
- `nome`: String(200), not null, unique, indexed
- `path`: String(500), not null, unique, indexed
- `tipo`: Enum(VolumeTipo), not null, default=LOCAL
- `status`: Enum(VolumeStatus), not null, default=ATIVO, indexed
- `descricao`: Text, nullable
- `created_at`: DateTime via TimestampMixin
- `updated_at`: DateTime via TimestampMixin

**Relacionamentos**:
- `configuracoes`: relationship → Configuracao (1:N), back_populates="volume"

**Constraints**:
- unique constraint em `nome`
- unique constraint em `path`

**Índices**:
- idx_volume_nome (nome)
- idx_volume_status (status)
- idx_volume_tipo (tipo)

### 4.4. Alteração no Model Configuracao

```python
# Adicionar em configuracao.py
volume_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("volumes.id"),
    nullable=False,
    index=True,
    doc="Volume de saída vinculado"
)

# Novo relacionamento
volume: Mapped["Volume"] = relationship(back_populates="configuracoes")

# Remover ou deprecar:
# output_dir: Mapped[str]  → campo será removido após migração
```

### 4.5. Schemas (toninho/schemas/volume.py)

```python
class VolumeCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200, description="Nome amigável do volume")
    path: str = Field(..., min_length=1, max_length=500, description="Caminho do diretório")
    descricao: Optional[str] = Field(None, description="Descrição opcional")

class VolumeUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    path: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[VolumeStatus] = None
    descricao: Optional[str] = None

class VolumeResponse(BaseModel):
    id: UUID
    nome: str
    path: str
    tipo: VolumeTipo
    status: VolumeStatus
    descricao: Optional[str]
    total_processos: int  # Computed: count de configurações vinculadas
    created_at: datetime
    updated_at: datetime

class VolumeSummary(BaseModel):
    id: UUID
    nome: str
    path: str
    tipo: VolumeTipo
    status: VolumeStatus

class VolumeValidationResult(BaseModel):
    path: str
    valido: bool
    pode_ler: bool
    pode_escrever: bool
    existe: bool
    criado: bool  # True se o diretório foi criado durante validação
    erro: Optional[str]
```

### 4.6. Alteração em Schemas de Configuração

```python
# Em configuracao.py schemas — substituir output_dir por volume_id
class ConfiguracaoCreate(BaseModel):
    # ... campos existentes ...
    volume_id: UUID  # Substitui output_dir: str
    # output_dir: str  → REMOVIDO

class ConfiguracaoResponse(BaseModel):
    # ... campos existentes ...
    volume_id: UUID
    volume: VolumeSummary  # Inclui dados do volume para exibição
    # output_dir: str  → REMOVIDO
```

### 4.7. Repository (toninho/repositories/volume_repository.py)

```python
class VolumeRepository:
    def create(db: Session, volume: Volume) -> Volume
    def get_by_id(db: Session, volume_id: UUID) -> Optional[Volume]
    def get_by_nome(db: Session, nome: str) -> Optional[Volume]
    def get_by_path(db: Session, path: str) -> Optional[Volume]
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[VolumeStatus] = None,
        busca: Optional[str] = None
    ) -> Tuple[List[Volume], int]
    def get_ativos(db: Session) -> List[Volume]
        # Retorna apenas volumes ativos (para combo/select)
    def update(db: Session, volume: Volume) -> Volume
    def delete(db: Session, volume_id: UUID) -> bool
    def exists_by_nome(db: Session, nome: str, exclude_id: Optional[UUID] = None) -> bool
    def exists_by_path(db: Session, path: str, exclude_id: Optional[UUID] = None) -> bool
    def count_configuracoes(db: Session, volume_id: UUID) -> int
        # Conta quantas configurações usam este volume
```

### 4.8. Service (toninho/services/volume_service.py)

```python
class VolumeService:
    def create_volume(db: Session, volume_create: VolumeCreate) -> VolumeResponse
        # 1. Normalizar path (resolver ./, ../, trailing slash)
        # 2. Validar nome único
        # 3. Validar path único
        # 4. Validar acesso ao path (leitura + escrita)
        # 5. Criar model Volume
        # 6. Retornar VolumeResponse

    def validate_path(path: str) -> VolumeValidationResult
        # 1. Verificar se diretório existe
        # 2. Se não, tentar criar (mkdir -p)
        # 3. Tentar escrever arquivo temporário
        # 4. Tentar ler arquivo temporário
        # 5. Deletar arquivo temporário
        # 6. Retornar resultado detalhado

    def get_volume(db: Session, volume_id: UUID) -> VolumeResponse
    def list_volumes(db: Session, ...) -> SuccessListResponse[VolumeResponse]
    def get_volumes_ativos(db: Session) -> List[VolumeSummary]
        # Para popular combo/select no frontend

    def update_volume(db: Session, volume_id: UUID, update: VolumeUpdate) -> VolumeResponse
        # Se path mudou, revalidar acesso

    def delete_volume(db: Session, volume_id: UUID) -> bool
        # 1. Verificar se está em uso
        # 2. Se sim, levantar ConflictError com lista de processos
        # 3. Se não, deletar

    def test_volume(db: Session, volume_id: UUID) -> VolumeValidationResult
        # Revalidar acesso ao path de um volume existente
```

### 4.9. API Routes (toninho/api/routes/volumes.py)

**Router**: prefix="/api/v1/volumes", tags=["Volumes"]

```python
POST /api/v1/volumes
    # Criar volume
    # Request: VolumeCreate
    # Response: SuccessResponse[VolumeResponse]
    # Status: 201
    # Validação: nome único, path único, acesso OK

GET /api/v1/volumes
    # Listar volumes (paginado)
    # Query params: page, per_page, status, busca
    # Response: SuccessListResponse[VolumeResponse]
    # Status: 200

GET /api/v1/volumes/ativos
    # Listar volumes ativos (para combo/select)
    # Response: SuccessResponse[List[VolumeSummary]]
    # Status: 200
    # Nota: sem paginação, retorna todos os ativos

GET /api/v1/volumes/{volume_id}
    # Obter volume por ID
    # Response: SuccessResponse[VolumeResponse]
    # Status: 200 / 404

PUT /api/v1/volumes/{volume_id}
    # Atualizar volume
    # Request: VolumeUpdate
    # Response: SuccessResponse[VolumeResponse]
    # Status: 200 / 404 / 409

DELETE /api/v1/volumes/{volume_id}
    # Deletar volume
    # Status: 204 / 404 / 409 (em uso)

POST /api/v1/volumes/{volume_id}/testar
    # Testar acesso ao volume (revalidar)
    # Response: SuccessResponse[VolumeValidationResult]
    # Status: 200

POST /api/v1/volumes/validar-path
    # Validar um path sem criar volume (preview)
    # Request: { "path": "/app/output" }
    # Response: SuccessResponse[VolumeValidationResult]
    # Status: 200
```

### 4.10. Frontend Routes

```python
# Em toninho/api/routes/frontend.py ou equivalente

GET /volumes                  # Listagem de volumes
GET /volumes/criar            # Formulário de criação
GET /volumes/{id}/editar      # Formulário de edição
```

### 4.11. Alteração na Extração (toninho/workers/utils.py)

```python
# Antes:
storage = get_storage("local", base_dir=configuracao.output_dir or "./output")

# Depois:
storage = get_storage(
    configuracao.volume.tipo,
    base_dir=configuracao.volume.path
)
```

---

## 5. Migração de Dados (Alembic)

### 5.1. Estratégia de Migração

A migração deve ser **segura e reversível**:

```python
def upgrade():
    # 1. Criar tabela volumes
    op.create_table('volumes', ...)

    # 2. Extrair paths únicos de configurações existentes
    # SELECT DISTINCT output_dir FROM configuracoes
    # Para cada path único:
    #   INSERT INTO volumes (id, nome, path, tipo, status)
    #   Nome auto-gerado: "Volume - {path}" (ex: "Volume - ./output")

    # 3. Garantir volume padrão existe
    # Se "./output" não existia, criar "Saída Padrão" com path "./output"

    # 4. Adicionar coluna volume_id em configuracoes (nullable temporariamente)
    op.add_column('configuracoes', sa.Column('volume_id', UUID, nullable=True))

    # 5. Popular volume_id baseado em output_dir
    # UPDATE configuracoes SET volume_id = (SELECT id FROM volumes WHERE path = configuracoes.output_dir)

    # 6. Tornar volume_id NOT NULL
    op.alter_column('configuracoes', 'volume_id', nullable=False)

    # 7. Criar FK constraint
    op.create_foreign_key(...)

    # 8. Remover coluna output_dir (ou manter nullable para rollback)
    op.drop_column('configuracoes', 'output_dir')

def downgrade():
    # Reverter: recriar output_dir, popular com volume.path, remover volume_id, dropar volumes
```

---

## 6. Regras de Negócio

### 6.1. Nome do Volume
- Único no sistema (constraint de banco + validação).
- Min 1 caractere, max 200 caracteres.
- Trim de whitespace automático.

### 6.2. Path do Volume
- Único no sistema.
- Normalizado: resolver `./`, `../`, remover trailing slash.
- Max 500 caracteres.
- Deve ser um path válido no SO.

### 6.3. Validação de Acesso
- Apenas no momento de criação/edição.
- Tenta criar o diretório se não existe (`mkdir -p`).
- Escreve arquivo temporário `.toninho_volume_test`.
- Lê arquivo temporário.
- Deleta arquivo temporário.
- Retorna resultado detalhado com flags: `existe`, `criado`, `pode_ler`, `pode_escrever`.

### 6.4. Status
- Default: ATIVO.
- Volumes inativos não aparecem no combo de seleção de novos processos.
- Volumes inativos continuam funcionando para processos já vinculados.

### 6.5. Deleção
- Bloqueada se há configurações vinculadas (retorna 409 Conflict).
- Mensagem de erro inclui lista de processos afetados.

### 6.6. Tipo
- MVP: apenas `LOCAL`.
- Campo já existe no model para extensão futura (cloud, bd).
- Frontend não exibe seletor de tipo no MVP (fixo como "Local").

### 6.7. Volume Padrão
- Criado automaticamente na migração ou seed.
- Nome: "Saída Padrão", Path: `./output`, Tipo: LOCAL, Status: ATIVO.
- Não pode ser deletado (regra de negócio ou flag `is_default`).

---

## 7. Frontend — Detalhamento

### 7.1. Sidebar
- Nova entrada: **"Volumes"** com ícone de disco/HDD.
- Posição: após "Processos" e antes de "Monitoramento".

### 7.2. Tela de Listagem (`/volumes`)
- Tabela com colunas: Nome, Path, Tipo, Status (badge), Processos vinculados, Ações.
- Ações: Editar, Testar conexão, Deletar.
- Filtro por status (ativo/inativo/todos).
- Busca por nome/path.
- Botão "Novo Volume".
- HTMX para paginação e filtros sem reload.

### 7.3. Formulário de Criação (`/volumes/criar`)
- Campos: Nome, Path, Descrição (opcional).
- Botão "Validar Path" que chama `POST /api/v1/volumes/validar-path` via HTMX.
- Feedback visual: ícone verde/vermelho após validação.
- Tipo exibido como badge "Local" (não editável no MVP).

### 7.4. Formulário de Edição (`/volumes/{id}/editar`)
- Mesmos campos da criação + Status (toggle ativo/inativo).
- Se path mudou, revalida automaticamente.

### 7.5. Combo no Formulário de Processo
- Substituir o `<input type="text" x-model="config.output_dir">` por:
```html
<select x-model="config.volume_id">
    <option value="">Selecione um volume...</option>
    <template x-for="vol in volumes" :key="vol.id">
        <option :value="vol.id" x-text="`${vol.nome} — ${vol.path}`"></option>
    </template>
</select>
```
- Carregar volumes ativos via `GET /api/v1/volumes/ativos`.
- Remover botões de atalho (`./output`, `/tmp/output`).
- Link "Gerenciar volumes" abaixo do select para acesso rápido.

---

## 8. Casos de Teste

### 8.1. Model Tests
- ✅ Criar Volume com todos os campos
- ✅ Constraint unique em nome
- ✅ Constraint unique em path
- ✅ Relacionamento com Configuracao (1:N)
- ✅ Enum VolumeStatus e VolumeTipo

### 8.2. Repository Tests
- ✅ create(): insere volume no banco
- ✅ get_by_id(): retorna volume correto
- ✅ get_by_nome(): encontra por nome
- ✅ get_by_path(): encontra por path
- ✅ get_all(): lista com paginação e filtros
- ✅ get_ativos(): retorna apenas ativos
- ✅ update(): atualiza volume
- ✅ delete(): remove volume
- ✅ exists_by_nome(): detecta duplicatas
- ✅ exists_by_path(): detecta paths duplicados
- ✅ count_configuracoes(): conta processos vinculados

### 8.3. Service Tests
- ✅ create_volume(): cria volume válido com validação de path
- ✅ create_volume(): falha se path inacessível
- ✅ create_volume(): falha se nome duplicado
- ✅ create_volume(): falha se path duplicado
- ✅ validate_path(): retorna resultado correto para path válido
- ✅ validate_path(): retorna erro para path sem permissão
- ✅ validate_path(): cria diretório se não existe
- ✅ update_volume(): atualiza e revalida path
- ✅ delete_volume(): bloqueia se em uso
- ✅ delete_volume(): remove se não está em uso
- ✅ test_volume(): revalida path existente
- ✅ get_volumes_ativos(): exclui inativos

### 8.4. API Tests
- ✅ POST /volumes: cria volume (201)
- ✅ POST /volumes: retorna 409 se nome duplicado
- ✅ POST /volumes: retorna 400 se path inválido
- ✅ GET /volumes: lista volumes (200)
- ✅ GET /volumes/ativos: retorna apenas ativos (200)
- ✅ GET /volumes/{id}: retorna volume (200)
- ✅ GET /volumes/{id}: retorna 404 se não existe
- ✅ PUT /volumes/{id}: atualiza volume (200)
- ✅ DELETE /volumes/{id}: deleta volume (204)
- ✅ DELETE /volumes/{id}: retorna 409 se em uso
- ✅ POST /volumes/{id}/testar: testa conexão (200)
- ✅ POST /volumes/validar-path: valida path (200)

### 8.5. Migração Tests
- ✅ Migração cria tabela volumes
- ✅ Migração extrai paths únicos de configurações
- ✅ Migração cria volume padrão
- ✅ Migração popula volume_id em configurações
- ✅ Downgrade reverte corretamente

### 8.6. Frontend Tests
- ✅ Listagem de volumes exibe dados corretos
- ✅ Formulário de criação valida campos obrigatórios
- ✅ Botão "Validar Path" funciona via HTMX
- ✅ Combo de volumes carrega no formulário de processo
- ✅ Seleção de volume persiste ao salvar processo
- ✅ Volume inativo não aparece no combo

### 8.7. Integração (Worker)
- ✅ Worker usa volume.path em vez de output_dir
- ✅ Extração salva arquivos no path do volume correto

---

## 9. Critérios de Aceitação

### ✅ Backend
- [ ] Model Volume implementado com enums
- [ ] Repository com CRUD completo
- [ ] Service com validação de path (leitura/escrita)
- [ ] API REST com todos endpoints
- [ ] Migração Alembic com migração de dados
- [ ] Testes com cobertura > 90%

### ✅ Frontend
- [ ] Sidebar com link "Volumes"
- [ ] Tela de listagem funcional
- [ ] Formulário de criação/edição com validação de path
- [ ] Combo substituindo texto livre no form de processo
- [ ] Feedback visual de status e validação

### ✅ Integração
- [ ] Workers usam volume.path para armazenar extrações
- [ ] Processos existentes continuam funcionando após migração
- [ ] Volume padrão criado automaticamente

---

## 10. Ordem de Implementação Sugerida

1. **Enums e Model** — Criar `VolumeStatus`, `VolumeTipo`, `Volume` model.
2. **Schemas** — Criar DTOs de entrada/saída.
3. **Migração Alembic** — Criar tabela + migrar dados existentes.
4. **Repository** — Implementar acesso a dados.
5. **Service** — Implementar lógica de negócio + validação de path.
6. **API Routes** — Endpoints REST.
7. **Alterar Configuracao** — Substituir `output_dir` por `volume_id`.
8. **Alterar Worker** — Usar `volume.path` na extração.
9. **Frontend — CRUD Volumes** — Tela de listagem, criação, edição.
10. **Frontend — Combo no Processo** — Substituir texto livre por select.
11. **Testes** — Unitários, integração, E2E.

---

## 11. Riscos e Considerações

### 11.1. Migração de Dados
- **Risco**: configurações com paths inválidos ou inacessíveis.
- **Mitigação**: migração cria volumes sem validar acesso (validação é responsabilidade do usuário após migração). Status definido como ATIVO.

### 11.2. Docker Volumes
- **Risco**: path válido no host pode não ser válido no container.
- **Mitigação**: documentar que paths devem ser relativos ao contexto do container (ex: `./output` → `/app/output`).

### 11.3. Permissões
- **Risco**: em ambientes restritivos (Docker rootless, SELinux), a validação pode falhar.
- **Mitigação**: mensagens de erro claras e documentação de troubleshooting.

### 11.4. Extensibilidade (Tipos Futuros)
- **Preparação**: o campo `tipo` e a `StorageInterface` já existente permitem implementar novos backends sem alterar o model.
- **Quando cloud**: adicionar campos condicionais (bucket, credentials, region) via JSON ou tabela auxiliar.

---

## 12. Referências

- **PRD-003**: Models e Database (base para novo model)
- **PRD-004**: Schemas e DTOs (padrão para novos schemas)
- **PRD-005**: Módulo Processo (padrão Repository/Service/Routes)
- **PRD-006**: Módulo Configuração (entidade que será alterada)
- **PRD-011**: Sistema de Extração (usa output_dir/storage)
- **PRD-015**: Interface CRUD Processos (formulário que será alterado)

---

## 13. Definição de Pronto

Este PRD estará completo quando:
- ✅ Model Volume criado e migrado
- ✅ CRUD de volumes funcional (API + Frontend)
- ✅ Validação de path com feedback claro
- ✅ Combo substituiu texto livre no form de processo
- ✅ Migração automática de dados existentes
- ✅ Workers usam volume.path para extrações
- ✅ Volume padrão criado automaticamente
- ✅ Testes com cobertura > 90%
- ✅ Documentação atualizada

---

**PRD Anterior**: PRD-025 — Implementação Playwright — Páginas, Notificações e Navegação
**Próximo PRD**: (a definir)
