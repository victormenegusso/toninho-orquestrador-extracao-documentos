# Schemas

Este diretório contém os DTOs (Data Transfer Objects) usando Pydantic.

## Responsabilidades

Schemas devem:
- Validar dados de entrada/saída
- Serializar/deserializar JSON
- Documentar API (Swagger)
- Ser independentes de modelos de banco

## Convenções

### Nomenclatura
- Classes base: `NomeBase` (campos comuns)
- Create: `NomeCreate` (input para criar)
- Update: `NomeUpdate` (input para atualizar)
- Response: `NomeResponse` (output da API)

### Estrutura

```python
from pydantic import BaseModel, Field
from datetime import datetime

class ProcessoBase(BaseModel):
    numero: str = Field(..., description="Número do processo")
    descricao: str | None = None

class ProcessoCreate(ProcessoBase):
    pass

class ProcessoUpdate(BaseModel):
    descricao: str | None = None

class ProcessoResponse(ProcessoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

## Padrões

- Usar type hints
- Adicionar `Field` com descrição
- `Response` deve ter `from_attributes = True`
- Validações customizadas com `@validator`
