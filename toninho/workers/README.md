# Workers

Este diretório contém as tasks assíncronas do Celery.

## Responsabilidades

Workers devem:
- Processar tarefas assíncronas
- Realizar extrações de dados
- Enviar notificações
- Processar arquivos

## Convenções

### Nomenclatura
- Tasks: verbos de ação (ex: `extract_processo`, `send_notification`)
- Usar decorator `@celery_app.task`

### Estrutura

```python
from toninho.workers.celery_app import celery_app
from toninho.services.processo import ProcessoService

@celery_app.task(bind=True, max_retries=3)
def extract_processo(self, processo_id: int):
    try:
        # Lógica de extração
        pass
    except Exception as exc:
        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

## Padrões

- Sempre usar `bind=True` para retry
- Definir `max_retries`
- Tratar exceções
- Usar backoff exponencial
- Logar progresso com `update_state`
