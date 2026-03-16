"""Fixtures E2E para testes com Playwright."""

import os
import subprocess
import tempfile
import time
from collections.abc import Generator
from uuid import uuid4

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


@pytest.fixture
def create_processo(api_client: httpx.Client):
    """Cria processos via API para seeding de cenarios E2E."""
    counter = 0

    def _create(**kwargs) -> dict:
        nonlocal counter
        counter += 1

        payload = {
            "nome": kwargs.pop("nome", f"Processo E2E {counter}-{uuid4().hex[:8]}"),
            "descricao": kwargs.pop("descricao", "Processo criado para teste E2E"),
            "status": kwargs.pop("status", "ativo"),
        }
        payload.update(kwargs)

        response = api_client.post("/api/v1/processos", json=payload)
        assert response.status_code == 201, f"Falha ao criar processo: {response.text}"
        return response.json()["data"]

    return _create


@pytest.fixture
def create_processo_com_config(api_client: httpx.Client, create_processo):
    """Cria processo e configuracao padrao via API para testes E2E."""

    def _create(
        processo_kwargs: dict | None = None,
        config_kwargs: dict | None = None,
    ) -> tuple[dict, dict]:
        processo_kwargs = processo_kwargs or {}
        config_kwargs = config_kwargs or {}

        processo = create_processo(**processo_kwargs)
        processo_id = processo["id"]

        config_payload = {
            "urls": config_kwargs.pop("urls", ["https://example.com"]),
            "timeout": config_kwargs.pop("timeout", 3600),
            "max_retries": config_kwargs.pop("max_retries", 3),
            "formato_saida": config_kwargs.pop("formato_saida", "multiplos_arquivos"),
            "output_dir": config_kwargs.pop("output_dir", "./output"),
            "agendamento_tipo": config_kwargs.pop("agendamento_tipo", "manual"),
            "agendamento_cron": config_kwargs.pop("agendamento_cron", None),
            "use_browser": config_kwargs.pop("use_browser", False),
            "metodo_extracao": config_kwargs.pop("metodo_extracao", "html2text"),
        }
        config_payload.update(config_kwargs)

        response = api_client.post(
            f"/api/v1/processos/{processo_id}/configuracoes",
            json=config_payload,
        )
        assert (
            response.status_code == 201
        ), f"Falha ao criar configuracao: {response.text}"

        return processo, response.json()["data"]

    return _create


@pytest.fixture
def create_execucao(api_client: httpx.Client, create_processo_com_config):
    """Cria uma execucao via API para um processo com configuracao valida."""

    def _create(processo_id: str | None = None) -> dict:
        if processo_id is None:
            processo, _ = create_processo_com_config()
            processo_id = processo["id"]

        response = api_client.post(f"/api/v1/processos/{processo_id}/execucoes")
        assert response.status_code == 201, f"Falha ao criar execucao: {response.text}"
        return response.json()["data"]

    return _create


@pytest.fixture
def update_execucao_status(api_client: httpx.Client):
    """Atualiza status de execucao via endpoint PATCH da API."""

    def _update(execucao_id: str, status: str) -> dict:
        response = api_client.patch(
            f"/api/v1/execucoes/{execucao_id}/status",
            json={"status": status},
        )
        assert (
            response.status_code == 200
        ), f"Falha ao atualizar status da execucao: {response.text}"
        return response.json()["data"]

    return _update


@pytest.fixture
def create_logs_batch(api_client: httpx.Client):
    """Cria logs em lote para uma execucao via API."""

    def _create(execucao_id: str, logs: list[dict]) -> list[dict]:
        payload = [
            {
                "execucao_id": execucao_id,
                "nivel": log.get("nivel", "info"),
                "mensagem": log.get("mensagem", "Log de teste E2E"),
                "contexto": log.get("contexto"),
            }
            for log in logs
        ]
        response = api_client.post("/api/v1/logs/batch", json=payload)
        assert response.status_code == 201, f"Falha ao criar logs: {response.text}"
        return response.json()["data"]

    return _create


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
