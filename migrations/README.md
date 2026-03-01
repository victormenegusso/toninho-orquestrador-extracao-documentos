# Migrations

Este diretório contém as migrations do Alembic para gerenciamento do schema do banco de dados.

## Comandos Úteis

### Criar nova migration
```bash
poetry run alembic revision --autogenerate -m "descrição da mudança"
```

### Aplicar migrations
```bash
poetry run alembic upgrade head
```

### Reverter migration
```bash
poetry run alembic downgrade -1
```

### Ver histórico
```bash
poetry run alembic history
```

## Convenções

- Sempre revisar migrations auto-geradas
- Testar migrations antes de commitar
- Prover rollback (downgrade) funcional
- Usar nomes descritivos

## Estrutura

Cada migration tem:
- `upgrade()`: aplica mudanças
- `downgrade()`: reverte mudanças
