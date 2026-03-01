"""
Tasks do módulo de workers.
"""

from toninho.workers.tasks.execucao_task import executar_processo_task
from toninho.workers.tasks.agendamento_task import verificar_agendamentos
from toninho.workers.tasks.limpeza_task import limpar_logs_antigos

__all__ = [
    "executar_processo_task",
    "verificar_agendamentos",
    "limpar_logs_antigos",
]
