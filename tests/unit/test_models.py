"""
Testes unitários para os models do Toninho.

Testa criação, validações, relacionamentos e constraints dos models.
"""
import uuid
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from toninho.models import (
    AgendamentoTipo,
    Configuracao,
    Execucao,
    ExecucaoStatus,
    FormatoSaida,
    Log,
    LogNivel,
    PaginaExtraida,
    PaginaStatus,
    Processo,
    ProcessoStatus,
)


class TestProcesso:
    """Testes para o model Processo."""

    def test_criar_processo_valido(self, db: Session) -> None:
        """Testa criação de processo com dados válidos."""
        processo = Processo(
            nome="Teste Processo",
            descricao="Descrição do processo",
            status=ProcessoStatus.ATIVO,
        )
        db.add(processo)
        db.commit()
        db.refresh(processo)

        assert processo.id is not None
        assert isinstance(processo.id, uuid.UUID)
        assert processo.nome == "Teste Processo"
        assert processo.descricao == "Descrição do processo"
        assert processo.status == ProcessoStatus.ATIVO
        assert processo.created_at is not None
        assert processo.updated_at is not None

    def test_processo_nome_unico(self, db: Session) -> None:
        """Testa constraint de nome único."""
        processo1 = Processo(nome="Processo Único")
        db.add(processo1)
        db.commit()

        processo2 = Processo(nome="Processo Único")
        db.add(processo2)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_processo_status_default(self, db: Session) -> None:
        """Testa status default como ATIVO."""
        processo = Processo(nome="Processo Default")
        db.add(processo)
        db.commit()
        db.refresh(processo)

        assert processo.status == ProcessoStatus.ATIVO

    def test_processo_timestamps_automaticos(self, db: Session) -> None:
        """Testa que timestamps são setados automaticamente."""
        processo = Processo(nome="Processo Timestamps")
        db.add(processo)
        db.commit()
        db.refresh(processo)

        assert processo.created_at is not None
        assert processo.updated_at is not None
        assert isinstance(processo.created_at, datetime)
        assert isinstance(processo.updated_at, datetime)


class TestConfiguracao:
    """Testes para o model Configuracao."""

    def test_criar_configuracao_valida(self, db: Session, processo_factory) -> None:
        """Testa criação de configuração com dados válidos."""
        processo = processo_factory()

        configuracao = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            timeout=1800,
            max_retries=3,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir="/tmp/output",
            agendamento_tipo=AgendamentoTipo.MANUAL,
        )
        db.add(configuracao)
        db.commit()
        db.refresh(configuracao)

        assert configuracao.id is not None
        assert configuracao.processo_id == processo.id
        assert configuracao.urls == ["https://exemplo.com"]
        assert configuracao.timeout == 1800
        assert configuracao.max_retries == 3

    def test_configuracao_timeout_constraint(self, db: Session, processo_factory) -> None:
        """Testa constraints de timeout."""
        processo = processo_factory()

        # Timeout negativo deve falhar
        configuracao = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            timeout=-1,
            output_dir="/tmp",
        )
        db.add(configuracao)

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()

        # Timeout > 86400 deve falhar
        configuracao2 = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            timeout=100000,
            output_dir="/tmp",
        )
        db.add(configuracao2)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_configuracao_max_retries_constraint(self, db: Session, processo_factory) -> None:
        """Testa constraints de max_retries."""
        processo = processo_factory()

        # max_retries > 10 deve falhar
        configuracao = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            max_retries=15,
            output_dir="/tmp",
        )
        db.add(configuracao)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_configuracao_defaults(self, db: Session, processo_factory) -> None:
        """Testa valores default."""
        processo = processo_factory()

        configuracao = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            output_dir="/tmp",
        )
        db.add(configuracao)
        db.commit()
        db.refresh(configuracao)

        assert configuracao.timeout == 3600
        assert configuracao.max_retries == 3
        assert configuracao.formato_saida == FormatoSaida.MULTIPLOS_ARQUIVOS
        assert configuracao.agendamento_tipo == AgendamentoTipo.MANUAL


class TestExecucao:
    """Testes para o model Execucao."""

    def test_criar_execucao_valida(self, db: Session, processo_factory) -> None:
        """Testa criação de execução com dados válidos."""
        processo = processo_factory()

        execucao = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.CRIADO,
        )
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        assert execucao.id is not None
        assert execucao.processo_id == processo.id
        assert execucao.status == ExecucaoStatus.CRIADO
        assert execucao.paginas_processadas == 0
        assert execucao.bytes_extraidos == 0
        assert execucao.taxa_erro == 0.0
        assert execucao.tentativa_atual == 1

    def test_execucao_taxa_erro_constraint(self, db: Session, processo_factory) -> None:
        """Testa constraints de taxa_erro."""
        processo = processo_factory()

        # Taxa erro > 100 deve falhar
        execucao = Execucao(
            processo_id=processo.id,
            taxa_erro=150.0,
        )
        db.add(execucao)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_execucao_property_duracao(self, db: Session, processo_factory) -> None:
        """Testa computed property duracao."""
        processo = processo_factory()

        inicio = datetime.utcnow()
        fim = datetime.utcnow()

        execucao = Execucao(
            processo_id=processo.id,
            iniciado_em=inicio,
            finalizado_em=fim,
        )
        db.add(execucao)
        db.commit()
        db.refresh(execucao)

        assert execucao.duracao is not None
        assert execucao.duracao >= 0

    def test_execucao_property_em_andamento(self, db: Session, processo_factory) -> None:
        """Testa computed property em_andamento."""
        processo = processo_factory()

        execucao = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.EM_EXECUCAO,
        )

        assert execucao.em_andamento is True

        execucao.status = ExecucaoStatus.CONCLUIDO
        assert execucao.em_andamento is False

    def test_execucao_property_finalizado(self, db: Session, processo_factory) -> None:
        """Testa computed property finalizado."""
        processo = processo_factory()

        execucao = Execucao(
            processo_id=processo.id,
            status=ExecucaoStatus.CONCLUIDO,
        )

        assert execucao.finalizado is True

        execucao.status = ExecucaoStatus.EM_EXECUCAO
        assert execucao.finalizado is False


class TestLog:
    """Testes para o model Log."""

    def test_criar_log_valido(self, db: Session, execucao_factory) -> None:
        """Testa criação de log com dados válidos."""
        execucao = execucao_factory()

        log = Log(
            execucao_id=execucao.id,
            nivel=LogNivel.INFO,
            mensagem="Teste de log",
            contexto={"chave": "valor"},
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        assert log.id is not None
        assert log.execucao_id == execucao.id
        assert log.nivel == LogNivel.INFO
        assert log.mensagem == "Teste de log"
        assert log.contexto == {"chave": "valor"}
        assert log.timestamp is not None

    def test_log_timestamp_automatico(self, db: Session, execucao_factory) -> None:
        """Testa que timestamp é setado automaticamente."""
        execucao = execucao_factory()

        log = Log(
            execucao_id=execucao.id,
            nivel=LogNivel.ERROR,
            mensagem="Erro",
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        assert log.timestamp is not None
        assert isinstance(log.timestamp, datetime)


class TestPaginaExtraida:
    """Testes para o model PaginaExtraida."""

    def test_criar_pagina_valida(self, db: Session, execucao_factory) -> None:
        """Testa criação de página extraída com dados válidos."""
        execucao = execucao_factory()

        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com/pagina",
            caminho_arquivo="/tmp/pagina.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=1024,
        )
        db.add(pagina)
        db.commit()
        db.refresh(pagina)

        assert pagina.id is not None
        assert pagina.execucao_id == execucao.id
        assert pagina.url_original == "https://exemplo.com/pagina"
        assert pagina.caminho_arquivo == "/tmp/pagina.md"
        assert pagina.status == PaginaStatus.SUCESSO
        assert pagina.tamanho_bytes == 1024
        assert pagina.timestamp is not None

    def test_pagina_tamanho_constraint(self, db: Session, execucao_factory) -> None:
        """Testa constraint de tamanho_bytes."""
        execucao = execucao_factory()

        # Tamanho negativo deve falhar
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://exemplo.com",
            caminho_arquivo="/tmp/file",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=-1,
        )
        db.add(pagina)

        with pytest.raises(IntegrityError):
            db.commit()


class TestRelacionamentos:
    """Testes para relacionamentos entre models."""

    def test_processo_configuracoes(self, db: Session, processo_factory) -> None:
        """Testa relacionamento Processo -> Configuracoes."""
        processo = processo_factory()

        config1 = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo1.com"],
            output_dir="/tmp",
        )
        config2 = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo2.com"],
            output_dir="/tmp",
        )
        db.add_all([config1, config2])
        db.commit()
        db.refresh(processo)

        assert len(processo.configuracoes) == 2

    def test_processo_execucoes(self, db: Session, processo_factory) -> None:
        """Testa relacionamento Processo -> Execucoes."""
        processo = processo_factory()

        exec1 = Execucao(processo_id=processo.id)
        exec2 = Execucao(processo_id=processo.id)
        db.add_all([exec1, exec2])
        db.commit()
        db.refresh(processo)

        assert len(processo.execucoes) == 2

    def test_execucao_logs(self, db: Session, execucao_factory) -> None:
        """Testa relacionamento Execucao -> Logs."""
        execucao = execucao_factory()

        log1 = Log(execucao_id=execucao.id, nivel=LogNivel.INFO, mensagem="Log 1")
        log2 = Log(execucao_id=execucao.id, nivel=LogNivel.ERROR, mensagem="Log 2")
        db.add_all([log1, log2])
        db.commit()
        db.refresh(execucao)

        assert len(execucao.logs) == 2

    def test_execucao_paginas(self, db: Session, execucao_factory) -> None:
        """Testa relacionamento Execucao -> PaginasExtraidas."""
        execucao = execucao_factory()

        pag1 = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://ex1.com",
            caminho_arquivo="/tmp/1",
            status=PaginaStatus.SUCESSO,
        )
        pag2 = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://ex2.com",
            caminho_arquivo="/tmp/2",
            status=PaginaStatus.SUCESSO,
        )
        db.add_all([pag1, pag2])
        db.commit()
        db.refresh(execucao)

        assert len(execucao.paginas) == 2

    def test_cascade_delete_processo(self, db: Session, processo_factory) -> None:
        """Testa cascade delete de Processo."""
        processo = processo_factory()

        config = Configuracao(
            processo_id=processo.id,
            urls=["https://exemplo.com"],
            output_dir="/tmp",
        )
        execucao = Execucao(processo_id=processo.id)
        db.add_all([config, execucao])
        db.commit()

        config_id = config.id
        execucao_id = execucao.id

        # Deletar processo deve deletar configuracoes e execucoes
        db.delete(processo)
        db.commit()

        assert db.query(Configuracao).filter_by(id=config_id).first() is None
        assert db.query(Execucao).filter_by(id=execucao_id).first() is None

    def test_cascade_delete_execucao(self, db: Session, execucao_factory) -> None:
        """Testa cascade delete de Execucao."""
        execucao = execucao_factory()

        log = Log(execucao_id=execucao.id, nivel=LogNivel.INFO, mensagem="Test")
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original="https://test.com",
            caminho_arquivo="/tmp/test",
            status=PaginaStatus.SUCESSO,
        )
        db.add_all([log, pagina])
        db.commit()

        log_id = log.id
        pagina_id = pagina.id

        # Deletar execução deve deletar logs e páginas
        db.delete(execucao)
        db.commit()

        assert db.query(Log).filter_by(id=log_id).first() is None
        assert db.query(PaginaExtraida).filter_by(id=pagina_id).first() is None
