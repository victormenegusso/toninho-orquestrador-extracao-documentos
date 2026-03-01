"""
Testes unitários para a configuração do Celery app.
"""

import pytest

from toninho.workers.celery_app import celery_app

# Import tasks so they register themselves in celery_app
import toninho.workers.tasks.execucao_task  # noqa: F401
import toninho.workers.tasks.agendamento_task  # noqa: F401
import toninho.workers.tasks.limpeza_task  # noqa: F401


class TestCeleryAppConfig:
    """Testes da configuração do celery_app."""

    def test_celery_app_name(self):
        assert celery_app.main == "toninho"

    def test_task_serializer_json(self):
        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer_json(self):
        assert celery_app.conf.result_serializer == "json"

    def test_accept_content_includes_json(self):
        assert "json" in celery_app.conf.accept_content

    def test_utc_enabled(self):
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.timezone == "UTC"

    def test_task_track_started(self):
        assert celery_app.conf.task_track_started is True

    def test_acks_late_enabled(self):
        assert celery_app.conf.task_acks_late is True

    def test_reject_on_worker_lost(self):
        assert celery_app.conf.task_reject_on_worker_lost is True

    def test_prefetch_multiplier_is_one(self):
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_max_tasks_per_child(self):
        assert celery_app.conf.worker_max_tasks_per_child == 100

    def test_task_time_limit_two_hours(self):
        assert celery_app.conf.task_time_limit == 7200

    def test_soft_time_limit(self):
        assert celery_app.conf.task_soft_time_limit == 7000

    def test_beat_schedule_has_agendamentos(self):
        assert "verificar-agendamentos" in celery_app.conf.beat_schedule

    def test_beat_schedule_has_limpeza(self):
        assert "limpar-logs-antigos" in celery_app.conf.beat_schedule

    def test_verificar_agendamentos_interval(self):
        schedule = celery_app.conf.beat_schedule["verificar-agendamentos"]
        assert schedule["schedule"] == 60.0

    def test_limpar_logs_interval(self):
        schedule = celery_app.conf.beat_schedule["limpar-logs-antigos"]
        assert schedule["schedule"] == 86400.0

    def test_tasks_are_registered(self):
        registered = list(celery_app.tasks.keys())
        assert any("executar_processo" in t or "executar-processo" in t or "executar_processo" in t for t in registered), f"Tasks registradas: {registered}"

    def test_include_task_modules(self):
        includes = celery_app.conf.include
        assert any("execucao_task" in i for i in includes)
        assert any("agendamento_task" in i for i in includes)
        assert any("limpeza_task" in i for i in includes)
