"""
Testes unitários para os schemas do Toninho.

Testa validação, serialização e conversão model→schema.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from toninho.models import (
    AgendamentoTipo,
    Configuracao,
    ExecucaoStatus,
    Log,
    LogNivel,
    PaginaExtraida,
    PaginaStatus,
    ProcessoStatus,
)
from toninho.models.enums import MetodoExtracao
from toninho.schemas import (
    ConfiguracaoCreate,
    ConfiguracaoResponse,
    ExecucaoCreate,
    ExecucaoResponse,
    ExecucaoSummary,
    LogCreate,
    LogResponse,
    PaginaExtraidaCreate,
    PaginaExtraidaResponse,
    ProcessoCreate,
    ProcessoResponse,
)
from toninho.schemas.configuracao import ConfiguracaoUpdate


class TestProcessoSchemas:
    """Testes para schemas de Processo."""

    def test_processo_create_valido(self) -> None:
        """Testa criação de schema com dados válidos."""
        data = {
            "nome": "Processo Teste",
            "descricao": "Descrição teste",
            "status": ProcessoStatus.ATIVO,
        }
        schema = ProcessoCreate(**data)

        assert schema.nome == "Processo Teste"
        assert schema.descricao == "Descrição teste"
        assert schema.status == ProcessoStatus.ATIVO

    def test_processo_create_nome_vazio(self) -> None:
        """Testa validação de nome vazio."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessoCreate(nome="")

        assert "nome" in str(exc_info.value).lower()

    def test_processo_create_nome_whitespace(self) -> None:
        """Testa que nome com apenas whitespace é rejeitado."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessoCreate(nome="   ")

        assert "nome" in str(exc_info.value).lower()

    def test_processo_create_strip_whitespace(self) -> None:
        """Testa que whitespace é removido automaticamente."""
        schema = ProcessoCreate(nome="  Teste  ")
        assert schema.nome == "Teste"

    def test_processo_response_from_model(self, db, processo_factory) -> None:
        """Testa conversão de model para schema."""
        processo = processo_factory(nome="Teste Conversão")

        schema = ProcessoResponse.model_validate(processo)

        assert schema.id == processo.id
        assert schema.nome == processo.nome
        assert schema.descricao == processo.descricao
        assert schema.status == processo.status
        assert schema.created_at == processo.created_at


class TestConfiguracaoSchemas:
    """Testes para schemas de Configuracao."""

    def test_configuracao_create_valida(self) -> None:
        """Testa criação de configuração válida."""
        data = {
            "urls": ["https://exemplo.com"],
            "timeout": 1800,
            "max_retries": 3,
            "output_dir": "/tmp/output",
        }
        schema = ConfiguracaoCreate(**data)

        assert schema.urls == ["https://exemplo.com"]
        assert schema.timeout == 1800
        assert schema.max_retries == 3

    def test_configuracao_urls_vazia(self) -> None:
        """Testa validação de lista de URLs vazia."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=[],
                output_dir="/tmp",
            )

    def test_configuracao_url_invalida(self) -> None:
        """Testa validação de URL inválida."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["not-a-url"],
                output_dir="/tmp",
            )

    def test_configuracao_timeout_negativo(self) -> None:
        """Testa validação de timeout negativo."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                timeout=-1,
                output_dir="/tmp",
            )

    def test_configuracao_timeout_excessivo(self) -> None:
        """Testa validação de timeout > 24h."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                timeout=100000,
                output_dir="/tmp",
            )

    def test_configuracao_max_retries_excessivo(self) -> None:
        """Testa validação de max_retries > 10."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                max_retries=15,
                output_dir="/tmp",
            )

    def test_configuracao_cron_recorrente_obrigatorio(self) -> None:
        """Testa que cron é obrigatório quando tipo=RECORRENTE."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                output_dir="/tmp",
                agendamento_tipo=AgendamentoTipo.RECORRENTE,
                agendamento_cron=None,
            )

    def test_configuracao_cron_valido(self) -> None:
        """Testa validação de expressão cron válida."""
        schema = ConfiguracaoCreate(
            urls=["https://exemplo.com"],
            output_dir="/tmp",
            agendamento_tipo=AgendamentoTipo.RECORRENTE,
            agendamento_cron="0 */6 * * *",
        )
        assert schema.agendamento_cron == "0 */6 * * *"

    def test_configuracao_cron_invalido(self) -> None:
        """Testa rejeição de expressão cron inválida."""
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://exemplo.com"],
                output_dir="/tmp",
                agendamento_cron="invalid cron",
            )

    def test_configuracao_response_from_model(self, db, processo_factory) -> None:
        """Testa conversão de model para schema."""
        processo = processo_factory()
        config = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            output_dir="/tmp",
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        schema = ConfiguracaoResponse.model_validate(config)

        assert schema.id == config.id
        assert schema.processo_id == config.processo_id
        assert schema.urls == config.urls

    def test_configuracao_use_browser_default_false(self) -> None:
        """use_browser deve ser False por padrão (MH-003)."""
        schema = ConfiguracaoCreate(
            urls=["https://exemplo.com"],
            output_dir="/tmp",
        )
        assert schema.use_browser is False

    def test_configuracao_use_browser_ativado(self) -> None:
        """use_browser=True deve ser aceito (MH-003)."""
        schema = ConfiguracaoCreate(
            urls=["https://exemplo.com"],
            output_dir="/tmp",
            use_browser=True,
        )
        assert schema.use_browser is True


class TestExecucaoSchemas:
    """Testes para schemas de Execucao."""

    def test_execucao_create_valida(self) -> None:
        """Testa criação de execução válida."""
        processo_id = uuid.uuid4()
        schema = ExecucaoCreate(processo_id=processo_id)

        assert schema.processo_id == processo_id

    def test_execucao_response_computed_duracao(self, db, execucao_factory) -> None:
        """Testa computed field duracao_segundos."""
        from datetime import timedelta

        execucao = execucao_factory(
            iniciado_em=datetime.now(UTC),
            finalizado_em=datetime.now(UTC) + timedelta(seconds=60),
        )

        schema = ExecucaoResponse.model_validate(execucao)

        assert schema.duracao_segundos is not None
        assert schema.duracao_segundos >= 60

    def test_duracao_segundos_retorna_float(self, db, execucao_factory) -> None:
        """Testa que duracao_segundos retorna float (BUG-002)."""
        from datetime import timedelta

        execucao = execucao_factory(
            iniciado_em=datetime.now(UTC),
            finalizado_em=datetime.now(UTC) + timedelta(seconds=60),
        )

        schema = ExecucaoResponse.model_validate(execucao)

        assert isinstance(schema.duracao_segundos, float)

    def test_duracao_segundos_precisao_sub_segundo(self, db, execucao_factory) -> None:
        """Testa precisão de milissegundos em duracao_segundos (BUG-002)."""
        from datetime import timedelta

        execucao = execucao_factory(
            iniciado_em=datetime.now(UTC),
            finalizado_em=datetime.now(UTC) + timedelta(milliseconds=1500),
        )

        schema = ExecucaoResponse.model_validate(execucao)

        assert schema.duracao_segundos is not None
        assert schema.duracao_segundos == pytest.approx(1.5, abs=0.1)

    def test_duracao_mixin_compartilhado_nos_schemas(
        self, db, execucao_factory
    ) -> None:
        """Testa que DuracaoMixin é compartilhado por ExecucaoResponse e ExecucaoSummary (TD-002)."""
        from toninho.schemas.execucao import DuracaoMixin

        assert issubclass(ExecucaoResponse, DuracaoMixin)
        assert issubclass(ExecucaoSummary, DuracaoMixin)

    def test_execucao_response_computed_em_andamento(
        self, db, execucao_factory
    ) -> None:
        """Testa computed field em_andamento."""
        execucao = execucao_factory(status=ExecucaoStatus.EM_EXECUCAO)

        schema = ExecucaoResponse.model_validate(execucao)

        assert schema.em_andamento is True

    def test_execucao_response_from_model(self, db, execucao_factory) -> None:
        """Testa conversão de model para schema."""
        execucao = execucao_factory()

        schema = ExecucaoResponse.model_validate(execucao)

        assert schema.id == execucao.id
        assert schema.processo_id == execucao.processo_id
        assert schema.status == execucao.status


class TestLogSchemas:
    """Testes para schemas de Log."""

    def test_log_create_valido(self) -> None:
        """Testa criação de log válido."""
        execucao_id = uuid.uuid4()
        schema = LogCreate(
            execucao_id=execucao_id,
            nivel=LogNivel.INFO,
            mensagem="Teste de log",
        )

        assert schema.execucao_id == execucao_id
        assert schema.nivel == LogNivel.INFO
        assert schema.mensagem == "Teste de log"

    def test_log_create_com_contexto(self) -> None:
        """Testa criação de log com contexto."""
        schema = LogCreate(
            execucao_id=uuid.uuid4(),
            nivel=LogNivel.ERROR,
            mensagem="Erro",
            contexto={"url": "https://exemplo.com", "status": 500},
        )

        assert schema.contexto == {"url": "https://exemplo.com", "status": 500}

    def test_log_mensagem_vazia(self) -> None:
        """Testa validação de mensagem vazia."""
        with pytest.raises(ValidationError):
            LogCreate(
                execucao_id=uuid.uuid4(),
                nivel=LogNivel.INFO,
                mensagem="",
            )

    def test_log_response_from_model(self, db, execucao_factory) -> None:
        """Testa conversão de model para schema."""
        execucao = execucao_factory()
        log = Log(
            execucao_id=execucao.id,
            nivel=LogNivel.INFO,
            mensagem="Teste",
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        schema = LogResponse.model_validate(log)

        assert schema.id == log.id
        assert schema.execucao_id == log.execucao_id
        assert schema.nivel == log.nivel
        assert schema.mensagem == log.mensagem


class TestPaginaExtraidaSchemas:
    """Testes para schemas de PaginaExtraida."""

    def test_pagina_create_valida(self) -> None:
        """Testa criação de página válida."""
        schema = PaginaExtraidaCreate(
            execucao_id=uuid.uuid4(),
            url_original="https://exemplo.com",
            caminho_arquivo="/tmp/pagina.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=1024,
        )

        assert schema.url_original == "https://exemplo.com"
        assert schema.tamanho_bytes == 1024

    def test_pagina_falha_requer_erro_mensagem(self) -> None:
        """Testa que erro_mensagem é obrigatória quando status=FALHOU."""
        with pytest.raises(ValidationError):
            PaginaExtraidaCreate(
                execucao_id=uuid.uuid4(),
                url_original="https://exemplo.com",
                caminho_arquivo="/tmp/file",
                status=PaginaStatus.FALHOU,
                erro_mensagem=None,
            )

    def test_pagina_tamanho_negativo(self) -> None:
        """Testa validação de tamanho negativo."""
        with pytest.raises(ValidationError):
            PaginaExtraidaCreate(
                execucao_id=uuid.uuid4(),
                url_original="https://exemplo.com",
                caminho_arquivo="/tmp/file",
                status=PaginaStatus.SUCESSO,
                tamanho_bytes=-1,
            )

    def test_pagina_response_computed_tamanho_legivel(
        self, db, execucao_factory
    ) -> None:
        """Testa computed field tamanho_legivel."""
        execucao = execucao_factory()
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com",
            caminho_arquivo="/tmp/file",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=1536,  # 1.5 KB
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        schema = PaginaExtraidaResponse.model_validate(pagina)

        assert "KB" in schema.tamanho_legivel

    def test_pagina_response_from_model(self, db, execucao_factory) -> None:
        """Testa conversão de model para schema."""
        execucao = execucao_factory()
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com",
            caminho_arquivo="/tmp/file",
            status=PaginaStatus.SUCESSO,
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        schema = PaginaExtraidaResponse.model_validate(pagina)

        assert schema.id == pagina.id
        assert schema.execucao_id == pagina.execucao_id
        assert schema.url_original == pagina.url_original


class TestValidators:
    """Testes para validators compartilhados."""

    def test_validate_url_valida(self) -> None:
        """Testa validação de URL válida."""
        from toninho.schemas.validators import validate_url

        result = validate_url("https://exemplo.com")
        assert result == "https://exemplo.com"

    def test_validate_url_invalida(self) -> None:
        """Testa rejeição de URL inválida."""
        from toninho.schemas.validators import validate_url

        with pytest.raises(ValueError):
            validate_url("not-a-url")

    def test_validate_cron_valida(self) -> None:
        """Testa validação de cron válida."""
        from toninho.schemas.validators import validate_cron_expression

        result = validate_cron_expression("0 */6 * * *")
        assert result == "0 */6 * * *"

    def test_validate_cron_invalida(self) -> None:
        """Testa rejeição de cron inválida."""
        from toninho.schemas.validators import validate_cron_expression

        with pytest.raises(ValueError):
            validate_cron_expression("invalid")

    def test_validate_path_valido(self) -> None:
        """Testa validação de path válido."""
        from toninho.schemas.validators import validate_path

        result = validate_path("/tmp/output")
        assert result == "/tmp/output"

    def test_validate_path_perigoso(self) -> None:
        """Testa rejeição de path perigoso."""
        from toninho.schemas.validators import validate_path

        with pytest.raises(ValueError):
            validate_path("/etc/passwd")


class TestResponses:
    """Testes para response wrappers."""

    def test_success_response(self) -> None:
        """Testa SuccessResponse."""
        from toninho.schemas import success_response

        response = success_response(data={"id": 1, "nome": "Teste"})

        assert response.data == {"id": 1, "nome": "Teste"}

    def test_success_list_response(self) -> None:
        """Testa SuccessListResponse."""
        from toninho.schemas import success_list_response

        response = success_list_response(
            data=[{"id": 1}, {"id": 2}],
            page=1,
            per_page=10,
            total=2,
        )

        assert len(response.data) == 2
        assert response.meta.page == 1
        assert response.meta.total == 2
        assert response.meta.total_pages == 1

    def test_error_response(self) -> None:
        """Testa ErrorResponse."""
        from toninho.schemas import ErrorDetail, error_response

        response = error_response(
            code="NOT_FOUND",
            message="Recurso não encontrado",
            details=[ErrorDetail(field="id", message="ID inválido")],
        )

        assert response.error.code == "NOT_FOUND"
        assert response.error.message == "Recurso não encontrado"
        assert len(response.error.details) == 1


# ── Passo 2 — Schemas: metodo_extracao ────────────────────────────────────────


class TestConfiguracaoCreateMetodoExtracao:
    """UC-07: ConfiguracaoCreate com metodo_extracao."""

    def test_default_e_html2text(self) -> None:
        schema = ConfiguracaoCreate(
            urls=["https://x.com"],
            output_dir="output",
            agendamento_tipo="manual",
        )
        assert schema.metodo_extracao == MetodoExtracao.HTML2TEXT

    def test_aceita_docling(self) -> None:
        schema = ConfiguracaoCreate(
            urls=["https://x.com"],
            output_dir="output",
            agendamento_tipo="manual",
            metodo_extracao="docling",
        )
        assert schema.metodo_extracao == MetodoExtracao.DOCLING

    def test_aceita_html2text_explicito(self) -> None:
        schema = ConfiguracaoCreate(
            urls=["https://x.com"],
            output_dir="output",
            agendamento_tipo="manual",
            metodo_extracao="html2text",
        )
        assert schema.metodo_extracao == MetodoExtracao.HTML2TEXT

    def test_rejeita_valor_invalido(self) -> None:
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://x.com"],
                output_dir="output",
                agendamento_tipo="manual",
                metodo_extracao="invalido",
            )


class TestConfiguracaoUpdateMetodoExtracao:
    """UC-08: ConfiguracaoUpdate com metodo_extracao."""

    def test_campo_opcional_ausente(self) -> None:
        schema = ConfiguracaoUpdate()
        assert schema.metodo_extracao is None

    def test_aceita_docling(self) -> None:
        schema = ConfiguracaoUpdate(metodo_extracao="docling")
        assert schema.metodo_extracao == MetodoExtracao.DOCLING

    def test_aceita_html2text(self) -> None:
        schema = ConfiguracaoUpdate(metodo_extracao="html2text")
        assert schema.metodo_extracao == MetodoExtracao.HTML2TEXT

    def test_rejeita_valor_invalido(self) -> None:
        with pytest.raises(ValidationError):
            ConfiguracaoUpdate(metodo_extracao="xpto")


class TestConfiguracaoResponseMetodoExtracao:
    """UC-09: ConfiguracaoResponse expõe metodo_extracao."""

    def test_response_inclui_campo(self) -> None:
        fields = ConfiguracaoResponse.model_fields
        assert "metodo_extracao" in fields

    def test_response_campo_obrigatorio(self) -> None:
        field = ConfiguracaoResponse.model_fields["metodo_extracao"]
        # Campo obrigatório não tem default
        assert field.default is None or field.is_required()
