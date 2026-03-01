# PRD-009: Módulo Página Extraída

**Status**: ✅ Concluído
**Prioridade**: 🟠 Alta - Backend Entidades Core (Prioridade 2)
**Categoria**: Backend - Entidades Core
**Estimativa**: 4-5 horas

---

## 1. Objetivo

Implementar o módulo de Página Extraída (Repository, Service, API) para gerenciar metadados de páginas extraídas e fornecer endpoints de download dos arquivos markdown resultantes.

## 2. Contexto e Justificativa

Cada página extraída gera um arquivo markdown no filesystem. Este módulo persiste metadados (URL, path, status, tamanho) e fornece interface para listar e fazer download destas páginas.

**Funcionalidades:**
- Registrar página extraída com sucesso/falha/ignorada
- Listar páginas de uma execução
- Download de arquivo markdown
- Estatísticas de extração (taxa de sucesso, tamanho total)

**Particularidades:**
- Separação entre metadados (banco) e conteúdo (filesystem)
- Download via endpoint HTTP
- Status de extração por página (sucesso, falha, ignorado)
- Integração com storage interface (local filesystem no MVP)

## 3. Requisitos Técnicos

### 3.1. Repository (toninho/repositories/pagina_extraida_repository.py)

**Métodos:**
```python
create(db, pagina) -> PaginaExtraida
create_batch(db, paginas: List[PaginaExtraida]) -> List[PaginaExtraida]
    # Inserção em lote

get_by_id(db, pagina_id) -> Optional[PaginaExtraida]

get_by_execucao_id(
    db,
    execucao_id,
    skip=0,
    limit=100,
    status: Optional[PaginaStatus] = None
) -> Tuple[List[PaginaExtraida], int]
    # Listar páginas de uma execução
    # Filtro por status

get_by_url(db, execucao_id, url: str) -> Optional[PaginaExtraida]
    # Buscar página por URL dentro de uma execução

count_by_status(db, execucao_id) -> Dict[PaginaStatus, int]
    # Conta páginas por status

sum_tamanho_bytes(db, execucao_id) -> int
    # Soma total de bytes extraídos

delete_by_execucao_id(db, execucao_id) -> int
    # Deletar todas as páginas de uma execução
```

### 3.2. Service (toninho/services/pagina_extraida_service.py)

**Métodos:**
```python
create_pagina_extraida(db, pagina_create: PaginaExtraidaCreate) -> PaginaExtraidaResponse
    # 1. Validar execução existe
    # 2. Validar status=FALHOU tem erro_mensagem
    # 3. Criar registro
    # 4. Atualizar métricas da execução (incrementar bytes, paginas)
    # 5. Retornar response

create_pagina_extraida_batch(db, paginas_create: List[PaginaExtraidaCreate]) -> List[PaginaExtraidaResponse]
    # Inserção em lote otimizada
    # Atualizar métricas da execução em única operação

get_pagina_extraida(db, pagina_id) -> PaginaExtraidaDetail
    # Inclui download_url computed field

list_paginas_by_execucao(
    db,
    execucao_id,
    page=1,
    per_page=100,
    status: Optional[PaginaStatus] = None
) -> SuccessListResponse[PaginaExtraidaSummary]

get_estatisticas_paginas(db, execucao_id) -> EstatisticasPaginas
    # Estatísticas de extração

download_pagina(db, pagina_id) -> Tuple[bytes, str, str]
    # Retorna (conteúdo, content_type, filename)
    # Lê arquivo do filesystem
    # Exceção FileNotFoundError se arquivo não existe

delete_pagina(db, pagina_id) -> bool
    # Deleta registro E arquivo do filesystem
```

**EstatisticasPaginas** (novo schema):
```python
class EstatisticasPaginas(BaseModel):
    execucao_id: UUID
    total: int
    sucesso: int
    falhou: int
    ignorado: int
    taxa_sucesso: float  # percentual
    tamanho_total_bytes: int
    tamanho_medio_bytes: float
    maior_pagina_bytes: int
    menor_pagina_bytes: int
```

### 3.3. API Routes (toninho/api/routes/paginas_extraidas.py)

**Router**: prefix="/api/v1", tags=["Páginas Extraídas"]

**Endpoints:**
```python
POST /api/v1/paginas
    # Criar registro de página extraída (uso interno, via workers)
    # Request: PaginaExtraidaCreate
    # Response: SuccessResponse[PaginaExtraidaResponse]
    # Status: 201

POST /api/v1/paginas/batch
    # Criar múltiplos registros em lote
    # Request: List[PaginaExtraidaCreate]
    # Response: SuccessResponse[List[PaginaExtraidaResponse]]
    # Status: 201

GET /api/v1/execucoes/{execucao_id}/paginas
    # Listar páginas da execução
    # Query params: page, per_page, status
    # Response: SuccessListResponse[PaginaExtraidaSummary]
    # Status: 200

GET /api/v1/execucoes/{execucao_id}/paginas/estatisticas
    # Obter estatísticas de extração
    # Response: SuccessResponse[EstatisticasPaginas]
    # Status: 200

GET /api/v1/paginas/{pagina_id}
    # Obter metadados de página específica
    # Response: SuccessResponse[PaginaExtraidaDetail]
    # Status: 200
    # Status: 404

GET /api/v1/paginas/{pagina_id}/download
    # Download do arquivo markdown
    # Response: FileResponse (application/octet-stream ou text/markdown)
    # Headers: Content-Disposition: attachment; filename="..."
    # Status: 200
    # Status: 404 se página ou arquivo não existe

DELETE /api/v1/paginas/{pagina_id}
    # Deletar página (metadados + arquivo)
    # Response: 204 No Content
    # Status: 404
```

### 3.4. Download de Arquivo

**Implementação:**
```python
from fastapi.responses import FileResponse
from pathlib import Path

@router.get("/paginas/{pagina_id}/download")
async def download_pagina(
    pagina_id: UUID,
    db: Session = Depends(get_db),
    pagina_service: PaginaExtraidaService = Depends(get_pagina_extraida_service)
):
    try:
        pagina = pagina_service.get_pagina_extraida(db, pagina_id)

        # Verificar arquivo existe
        filepath = Path(pagina.caminho_arquivo)
        if not filepath.exists():
            raise HTTPException(404, "Arquivo não encontrado no filesystem")

        # Gerar nome de arquivo para download
        filename = filepath.name

        return FileResponse(
            path=str(filepath),
            media_type="text/markdown",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except FileNotFoundError:
        raise HTTPException(404, "Arquivo não encontrado")
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-003: Models
- PRD-004: Schemas
- PRD-007: Módulo Execução

### 4.2. Dependências Futuras
- PRD-011: Sistema de Extração (workers criam registros de páginas)

## 5. Regras de Negócio

### 5.1. Status de Página
- SUCESSO: Página extraída e arquivo salvo com sucesso
- FALHOU: Erro na extração (404, timeout, parsing error)
- IGNORADO: Página ignorada por filtros ou regras

### 5.2. Erro Obrigatório
- Se status=FALHOU, erro_mensagem é obrigatória
- Erro_mensagem deve ser descritiva (ex: "HTTP 404: Página não encontrada")

### 5.3. Tamanho de Arquivo
- Tamanho em bytes do arquivo markdown gerado
- Usado para estatísticas e controle de limites

### 5.4. Caminho de Arquivo
- Caminho relativo ao OUTPUT_DIR configurado
- Exemplo: "./output/github-copilot/quickstart.md"
- Validar arquivo existe antes de download

### 5.5. Deleção
- Deletar registro no banco
- Deletar arquivo físico no filesystem
- Operação atômica (transação + filesystem)

### 5.6. Atualização de Métricas
- Ao criar página, atualizar métricas da execução:
  - Incrementar paginas_processadas
  - Incrementar bytes_extraidos
  - Recalcular taxa_erro se falhou

## 6. Casos de Teste

### 6.1. Repository Tests
- ✅ create(): insere página
- ✅ create_batch(): insere múltiplas páginas
- ✅ get_by_execucao_id(): retorna páginas da execução
- ✅ get_by_execucao_id(): filtra por status
- ✅ get_by_url(): busca por URL
- ✅ count_by_status(): conta por status
- ✅ sum_tamanho_bytes(): soma tamanho total

### 6.2. Service Tests
- ✅ create_pagina_extraida(): cria com dados válidos
- ✅ create_pagina_extraida(): valida erro_mensagem se FALHOU
- ✅ create_pagina_extraida(): atualiza métricas da execução
- ✅ create_pagina_extraida_batch(): inserção em lote
- ✅ list_paginas_by_execucao(): pagina corretamente
- ✅ get_estatisticas_paginas(): calcula estatísticas
- ✅ download_pagina(): retorna conteúdo do arquivo

### 6.3. API Tests
- ✅ POST /paginas: cria página (201)
- ✅ POST /paginas/batch: cria múltiplas (201)
- ✅ GET /execucoes/{id}/paginas: lista com paginação
- ✅ GET: filtra por status
- ✅ GET /paginas/{id}: retorna metadados
- ✅ GET /paginas/{id}/download: retorna arquivo (200)
- ✅ GET /download: retorna 404 se arquivo não existe
- ✅ DELETE /paginas/{id}: deleta registro e arquivo (204)

### 6.4. Filesystem Tests
- ✅ Download retorna conteúdo correto
- ✅ Download de arquivo inexistente retorna 404
- ✅ Deletar remove arquivo do filesystem
- ✅ Headers de download corretos (Content-Disposition)

## 7. Critérios de Aceitação

### ✅ Implementação
- [x] Repository com todos os métodos
- [x] Service com validações
- [x] API Routes implementadas
- [x] Download de arquivos funcional

### ✅ Testes
- [x] Testes com cobertura > 90%
- [x] Testes de download de arquivo

### ✅ Funcionalidades
- [x] Pode criar e consultar páginas via API
- [x] Download de arquivos funciona
- [x] Filtros funcionam corretamente
- [x] Estatísticas calculadas
- [x] Deleção remove arquivo do filesystem

## 8. Notas de Implementação

### 8.1. Separação de Responsabilidades
- Repository: acesso ao banco (metadados)
- Service: lógica de negócio + acesso ao filesystem
- Storage Interface (futuro): abstração para local/S3/etc

### 8.2. Leitura de Arquivo
```python
from pathlib import Path

def ler_arquivo(caminho: str) -> bytes:
    filepath = Path(caminho)
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with open(filepath, 'rb') as f:
        return f.read()
```

### 8.3. Deleção de Arquivo
```python
def deletar_arquivo(caminho: str) -> bool:
    filepath = Path(caminho)
    if filepath.exists():
        filepath.unlink()
        return True
    return False
```

### 8.4. Content Type
- text/markdown para .md files
- application/octet-stream como fallback

### 8.5. Pontos de Atenção
- Validar arquivo existe antes de download
- Tratar permissões de arquivo (read access)
- Considerar arquivos grandes (streaming se > 10MB)
- Race condition: arquivo deletado entre query e download
- Path traversal: validar caminho não sai do OUTPUT_DIR

## 9. Referências Técnicas

- **FastAPI FileResponse**: https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse
- **Python Pathlib**: https://docs.python.org/3/library/pathlib.html

## 10. Definição de Pronto

- ✅ CRUD de Página Extraída implementado
- ✅ Download de arquivos funcional
- ✅ Estatísticas de extração calculadas
- ✅ Deleção remove metadados e arquivo
- ✅ Testes com cobertura > 90%
- ✅ Pode criar, consultar e baixar páginas via API

---

**PRD Anterior**: PRD-008 - Módulo Log
**Próximo PRD**: PRD-010 - Workers e Processamento Assíncrono
