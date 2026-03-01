# Repositories

Este diretório contém a camada de acesso a dados.

## Responsabilidades

Repositories devem:
- Abstrair acesso ao banco de dados
- Implementar queries SQLAlchemy
- Retornar modelos do domínio
- Não conter lógica de negócio

## Convenções

### Nomenclatura
- Classes: `NomeRepository` (ex: `ProcessoRepository`)
- Métodos: CRUD padrão (get, list, create, update, delete)

### Estrutura

```python
from sqlalchemy.orm import Session
from toninho.models.processo import Processo

class ProcessoRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_by_id(self, id: int) -> Processo | None:
        return self.db.query(Processo).filter(Processo.id == id).first()

    async def list_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Processo).offset(skip).limit(limit).all()

    async def create(self, processo: Processo) -> Processo:
        self.db.add(processo)
        self.db.commit()
        self.db.refresh(processo)
        return processo
```

## Padrões

- Usar Session do SQLAlchemy
- Sempre fazer commit após mudanças
- Usar refresh após insert/update
- Tratar exceções de banco
