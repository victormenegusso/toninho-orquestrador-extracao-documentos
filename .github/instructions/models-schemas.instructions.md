---
applyTo: "**/models/*.py,**/schemas/*.py"
---

# Models & Schemas Conventions

## SQLAlchemy Models (2.x)

- Inherit from the base model defined in `toninho/models/base.py`.
- Use the **declarative mapping** style for all model definitions.
- Use proper SQLAlchemy column types (`String`, `Integer`, `DateTime`, `Text`, `Boolean`, etc.).
- Define relationships with `relationship()` and configure back-references as needed.
- Enums used in models are defined in `toninho/models/enums.py`.
- Table names and column names must be in **Portuguese** using `snake_case` (e.g., `processos`, `data_criacao`, `tipo_documento`).

### Example Structure

```python
class Processo(Base):
    __tablename__ = "processos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    status: Mapped[StatusProcesso] = mapped_column(SQLAlchemyEnum(StatusProcesso))
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    execucoes: Mapped[list["Execucao"]] = relationship(back_populates="processo")
```

## Pydantic Schemas (v2)

- Enable ORM mode with `model_config = ConfigDict(from_attributes=True)`.
- Create **separate schemas** for each use case:
  - `<Entity>Create` — input for creation
  - `<Entity>Update` — input for updates (fields are optional)
  - `<Entity>Response` — single entity output
  - `<Entity>List` — paginated list output
- Shared validators live in `toninho/schemas/validators.py`.
- Use `Field()` for validation constraints and OpenAPI descriptions.
- Domain field names must be in **Portuguese**, matching the corresponding model fields.

### Example Structure

```python
class ProcessoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255, description="Nome do processo")
    tipo: TipoProcesso = Field(..., description="Tipo do processo")

class ProcessoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    status: StatusProcesso
    data_criacao: datetime
```
