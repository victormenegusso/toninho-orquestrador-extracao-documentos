# ADR-002: Processamento Assíncrono via Celery

**Status**: Aceito
**Data**: 2025
**Contexto**: Extração de múltiplas URLs pode levar minutos/horas; bloqueio da API é inaceitável.

---

## Decisão

Usar **Celery** com broker **Redis** para processamento de tarefas em background.

Fluxo:
```
POST /execucoes → ExecucaoService → dispatch Celery task → retorna 201 imediatamente
Worker Celery → ExtractionOrchestrator → extrai URLs → persiste resultados
```

## Alternativas Rejeitadas

| Alternativa | Motivo rejeição |
|---|---|
| `asyncio` puro (BackgroundTasks FastAPI) | Sem retry, sem persistência de estado, perde tarefa se API reiniciar |
| RQ (Redis Queue) | Menos recursos, sem Beat scheduler nativo |
| APScheduler | Sem suporte a workers distribuídos |

## Consequências

- Redis é dependência obrigatória.
- Flower disponível em `:5555` para monitoramento.
- Celery Beat gerencia agendamentos recorrentes sem código adicional.
- Retry automático configurável por tarefa (`max_retries`, `countdown`).
