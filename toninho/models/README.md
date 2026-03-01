# Models

Este diretório contém os modelos do domínio (SQLAlchemy).

## Responsabilidades

Models devem:
- Representar tabelas do banco de dados
- Definir relacionamentos
- Ter validações de banco (constraints)
- Ser independentes de frameworks externos

## Convenções

### Nomenclatura
- Classes: PascalCase singular (ex: `Processo`, `Execucao`)
- Tabelas: snake_case plural (ex: `processos`, `execucoes`)
- Colunas: snake_case (ex: `created_at`, `processo_numero`)

### Estrutura

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from toninho.models.base import Base

class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    execucoes = relationship("Execucao", back_populates="processo")
```

## Padrões

- Herdar de `Base`
- Sempre definir `__tablename__`
- Primary key: `id` auto-incremento
- Timestamps: `created_at`, `updated_at`
- Usar relacionamentos SQLAlchemy
