"""Fixtures E2E para testes com Playwright."""

import os
import subprocess
import tempfile
import time
from collections.abc import Generator

import httpx
import pytest

E2E_HOST = "127.0.0.1"
E2E_PORT = 8089
E2E_BASE_URL = f"http://{E2E_HOST}:{E2E_PORT}"
SERVER_STARTUP_TIMEOUT = 30


@pytest.fixture(scope="session")
def _e2e_db_path() -> Generator[str, None, None]:
    """Cria banco SQLite temporario para a sessao E2E."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="toninho_e2e_")
    os.close(db_fd)
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="session")
def _e2e_env(_e2e_db_path: str) -> dict[str, str]:
    """Variaveis de ambiente para o servidor E2E."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{_e2e_db_path}"
    env["DEBUG"] = "false"
    env["LOG_LEVEL"] = "WARNING"
    env["SQL_ECHO"] = "false"
    return env


@pytest.fixture(scope="session")
def _run_migrations(_e2e_env: dict[str, str]) -> None:
    """Executa migrations no banco E2E antes de subir o servidor."""
    result = subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        env=_e2e_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Falha ao executar migrations:\n{result.stderr}")


@pytest.fixture(scope="session")
def live_server(
    _e2e_env: dict[str, str],
    _run_migrations: None,
) -> Generator[str, None, None]:
    """Sobe servidor FastAPI em processo separado para os testes E2E."""
    process = subprocess.Popen(
        [
            "poetry",
            "run",
            "uvicorn",
            "toninho.main:app",
            "--host",
            E2E_HOST,
            "--port",
            str(E2E_PORT),
            "--log-level",
            "warning",
        ],
        env=_e2e_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_server(E2E_BASE_URL, timeout=SERVER_STARTUP_TIMEOUT)
        yield E2E_BASE_URL
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


@pytest.fixture(scope="session")
def base_url(live_server: str) -> str:
    """URL base reconhecida automaticamente pelo pytest-playwright."""
    return live_server


@pytest.fixture(scope="session")
def api_client(live_server: str) -> Generator[httpx.Client, None, None]:
    """Cliente HTTP para seeding de dados via API durante os testes E2E."""
    with httpx.Client(base_url=live_server, timeout=30.0) as client:
        yield client


def _wait_for_server(url: str, timeout: int = 30) -> None:
    """Aguarda o servidor responder ao endpoint de health check."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{url}/api/v1/health", timeout=2.0)
            if response.status_code == 200:
                return
        except (httpx.ConnectError, httpx.ReadTimeout) as exc:
            last_error = exc
        time.sleep(0.5)

    raise RuntimeError(
        f"Servidor nao respondeu em {timeout}s. "
        f"URL: {url}/api/v1/health. Ultimo erro: {last_error}"
    )
