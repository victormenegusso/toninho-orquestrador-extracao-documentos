"""Testes para o HealthCheckService."""

from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from toninho.monitoring.health import HealthCheckService


class TestHealthCheckService:
    """Testes para o HealthCheckService."""

    def test_check_database_healthy(self, db: Session):
        """check_all retorna database healthy quando DB está ok."""
        service = HealthCheckService(db=db)
        result = service.check_all()

        assert "database" in result["checks"]
        assert result["checks"]["database"]["status"] == "healthy"
        assert "latency_ms" in result["checks"]["database"]

    def test_check_database_unhealthy(self):
        """_check_database retorna unhealthy se houver erro."""
        bad_db = MagicMock()
        bad_db.execute.side_effect = Exception("Connection failed")

        service = HealthCheckService(db=bad_db)
        result = service._check_database()

        assert result["status"] == "unhealthy"
        assert "error" in result

    def test_overall_status_healthy(self, db: Session):
        """Retorna status healthy quando tudo está ok."""
        service = HealthCheckService(db=db)
        result = service.check_all()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "checks" in result

    def test_overall_status_includes_timestamp(self, db: Session):
        """Resultado inclui timestamp ISO."""
        service = HealthCheckService(db=db)
        result = service.check_all()

        assert result["timestamp"] is not None
        assert "T" in result["timestamp"]  # ISO format

    def test_check_redis_healthy(self, db: Session):
        """_check_redis retorna healthy quando Redis responde."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "uptime_in_seconds": 120,
            "connected_clients": 3,
        }

        service = HealthCheckService(db=db, redis_client=mock_redis)
        result = service._check_redis()

        assert result["status"] == "healthy"
        assert "latency_ms" in result
        assert result["uptime_seconds"] == 120
        assert result["connected_clients"] == 3

    def test_check_redis_unhealthy(self, db: Session):
        """_check_redis retorna unhealthy quando Redis falha."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Redis not available")

        service = HealthCheckService(db=db, redis_client=mock_redis)
        result = service._check_redis()

        assert result["status"] == "unhealthy"
        assert "error" in result

    def test_check_redis_not_included_when_no_client(self, db: Session):
        """Redis check não incluído quando redis_client é None."""
        service = HealthCheckService(db=db)
        result = service.check_all()

        assert "redis" not in result["checks"]

    def test_check_celery_healthy(self, db: Session):
        """_check_celery_workers retorna healthy quando workers disponíveis."""
        mock_celery = MagicMock()
        mock_inspect = MagicMock()
        mock_celery.control.inspect.return_value = mock_inspect
        mock_inspect.stats.return_value = {
            "worker1@host": {"total": {}},
            "worker2@host": {"total": {}},
        }
        mock_inspect.active.return_value = {
            "worker1@host": ["task1"],
            "worker2@host": [],
        }

        service = HealthCheckService(db=db, celery_app=mock_celery)
        result = service._check_celery_workers()

        assert result["status"] == "healthy"
        assert result["worker_count"] == 2
        assert result["active_tasks"] == 1
        assert len(result["workers"]) == 2

    def test_check_celery_no_workers(self, db: Session):
        """_check_celery_workers retorna degraded quando não há workers."""
        mock_celery = MagicMock()
        mock_inspect = MagicMock()
        mock_celery.control.inspect.return_value = mock_inspect
        mock_inspect.stats.return_value = None

        service = HealthCheckService(db=db, celery_app=mock_celery)
        result = service._check_celery_workers()

        assert result["status"] == "degraded"
        assert result["worker_count"] == 0

    def test_check_celery_exception(self, db: Session):
        """_check_celery_workers retorna degraded em caso de exceção."""
        mock_celery = MagicMock()
        mock_celery.control.inspect.side_effect = Exception("Celery unavailable")

        service = HealthCheckService(db=db, celery_app=mock_celery)
        result = service._check_celery_workers()

        assert result["status"] == "degraded"
        assert "error" in result

    def test_celery_not_included_when_no_app(self, db: Session):
        """Celery check não incluído quando celery_app é None."""
        service = HealthCheckService(db=db)
        result = service.check_all()

        assert "celery_workers" not in result["checks"]

    def test_overall_status_degraded_when_celery_degraded(self, db: Session):
        """Status geral é degraded quando Celery está degraded."""
        mock_celery = MagicMock()
        mock_inspect = MagicMock()
        mock_celery.control.inspect.return_value = mock_inspect
        mock_inspect.stats.return_value = None

        service = HealthCheckService(db=db, celery_app=mock_celery)
        result = service.check_all()

        assert result["status"] == "degraded"

    def test_overall_status_unhealthy_when_db_fails(self):
        """Status geral é unhealthy quando DB falha."""
        bad_db = MagicMock()
        bad_db.execute.side_effect = Exception("DB down")

        service = HealthCheckService(db=bad_db)
        result = service.check_all()

        assert result["status"] == "unhealthy"
