# ADR-003: Estratégia de Banco de Dados

**Status**: Aceito
**Data**: 2025
**Contexto**: Sistema single-user, uso local em desenvolvimento; possibilidade de escala futura.

---

## Decisão

- **Desenvolvimento**: SQLite (arquivo `toninho.db` na raiz)
- **Produção**: PostgreSQL (via `DATABASE_URL` em variável de ambiente)
- **Migrations**: Alembic (agnóstico ao banco)

Configuração via `Settings.DATABASE_URL` (Pydantic BaseSettings + `.env`).

## Razões

- **SQLite dev**: zero dependências externas, sem Docker obrigatório para desenvolvimento local.
- **PostgreSQL prod**: concorrência, ACID completo, suporte nativo ao Celery/SQLAlchemy.
- **Alembic**: permite aplicar as mesmas migrations em ambos os bancos.

## Consequências

- Sem uso de features específicas do PostgreSQL no código (sem `ARRAY`, `JSONB` nativo).
- `db_data` volume Docker preserva o `.db` entre restarts de container.
- Desenvolvedores podem rodar sem Redis/Docker apenas para explorar models.
