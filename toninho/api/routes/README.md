# API Routes

Este diretório contém todos os endpoints REST da aplicação.

## Estrutura

Cada módulo de rotas deve:
- Usar `APIRouter` do FastAPI
- Ser registrado no `main.py`
- Seguir padrão REST
- Ter validação via Pydantic schemas

## Convenções

### Nomenclatura
- Arquivos: `nome_do_recurso.py` (ex: `processos.py`)
- Routers: `router` (variável padrão)

### Padrões REST
- `GET /recursos` - Listar todos
- `GET /recursos/{id}` - Obter um
- `POST /recursos` - Criar
- `PUT /recursos/{id}` - Atualizar completo
- `PATCH /recursos/{id}` - Atualizar parcial
- `DELETE /recursos/{id}` - Deletar

### Exemplo

```python
from fastapi import APIRouter, Depends
from toninho.schemas.processo import ProcessoCreate, ProcessoResponse

router = APIRouter()

@router.get("/", response_model=list[ProcessoResponse])
async def list_processos():
    pass

@router.post("/", response_model=ProcessoResponse, status_code=201)
async def create_processo(processo: ProcessoCreate):
    pass
```
