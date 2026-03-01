# Services

Este diretório contém a lógica de negócio da aplicação.

## Responsabilidades

Services devem:
- Implementar regras de negócio
- Orquestrar chamadas a repositories
- Validar dados de negócio
- Lançar exceções de domínio
- Ser independentes de framework

## Convenções

### Nomenclatura
- Classes: `NomeService` (ex: `ProcessoService`)
- Métodos: verbos de ação (ex: `create_processo`, `execute_extraction`)

### Estrutura

```python
from toninho.repositories.processo import ProcessoRepository
from toninho.schemas.processo import ProcessoCreate

class ProcessoService:
    def __init__(self, repo: ProcessoRepository):
        self.repo = repo

    async def create_processo(self, data: ProcessoCreate):
        # Validações de negócio
        # Chamadas a repositories
        # Retorno de dados
        pass
```

## Padrões

- Usar injeção de dependência
- Não acessar banco diretamente (usar repositories)
- Validar regras de negócio
- Retornar DTOs (schemas)
