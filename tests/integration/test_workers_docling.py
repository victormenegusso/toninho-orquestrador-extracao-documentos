"""
Testes de integração para ExtractionOrchestrator com motor Docling.

Usa SQLite em memória e mock do DoclingPageExtractor para validar
o fluxo end-to-end sem dependência de rede ou modelo Docling real.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from toninho.models import Base, Configuracao, Execucao, Processo
from toninho.models.enums import (
    AgendamentoTipo,
    ExecucaoStatus,
    FormatoSaida,
    MetodoExtracao,
    PaginaStatus,
)
from toninho.models.pagina_extraida import PaginaExtraida
from toninho.workers.utils import ExtractionOrchestrator


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_storage(tmp_path):
    from toninho.extraction.storage import LocalFileSystemStorage

    return LocalFileSystemStorage(base_dir=str(tmp_path))


SUCESSO = {
    "status": "sucesso",
    "url": "https://x.com",
    "path": "x.md",
    "bytes": 512,
    "title": "X",
    "from_cache": False,
    "error": None,
}
ERRO = {
    "status": "erro",
    "url": "https://x.com/falha",
    "path": None,
    "bytes": 0,
    "title": "",
    "from_cache": False,
    "error": "Docling timeout",
}


class TestOrchestratorComDocling:
    def _make_execucao(self, db, urls, metodo):
        p = Processo(nome=f"test-{uuid.uuid4().hex[:6]}", descricao="d")
        db.add(p)
        db.flush()
        c = Configuracao(
            processo_id=p.id,
            urls=urls,
            timeout=30,
            max_retries=1,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir="output",
            agendamento_tipo=AgendamentoTipo.MANUAL,
            metodo_extracao=metodo,
        )
        db.add(c)
        e = Execucao(processo_id=p.id, status=ExecucaoStatus.CRIADO)
        db.add(e)
        db.commit()
        db.refresh(e)
        return e

    def test_run_docling_conclui_com_sucesso(self, db, mock_storage):
        execucao = self._make_execucao(db, ["https://x.com"], MetodoExtracao.DOCLING)
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.return_value = SUCESSO
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(
                execucao.id
            )

        assert resultado["status"] == ExecucaoStatus.CONCLUIDO
        assert resultado["paginas_sucesso"] == 1
        assert resultado["paginas_falha"] == 0

    def test_run_docling_falha_parcial_gera_concluido_com_erros(self, db, mock_storage):
        execucao = self._make_execucao(
            db,
            ["https://x.com/ok", "https://x.com/falha"],
            MetodoExtracao.DOCLING,
        )
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.side_effect = [SUCESSO, ERRO]
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(
                execucao.id
            )

        assert resultado["status"] == ExecucaoStatus.CONCLUIDO_COM_ERROS
        assert resultado["paginas_sucesso"] == 1
        assert resultado["paginas_falha"] == 1

    def test_run_docling_falha_total_gera_status_falhou(self, db, mock_storage):
        execucao = self._make_execucao(
            db, ["https://x.com/falha"], MetodoExtracao.DOCLING
        )
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.return_value = ERRO
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(
                execucao.id
            )

        assert resultado["status"] == ExecucaoStatus.FALHOU

    def test_run_docling_registra_paginas_no_banco(self, db, mock_storage):
        execucao = self._make_execucao(db, ["https://x.com"], MetodoExtracao.DOCLING)
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.return_value = SUCESSO
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        paginas = (
            db.query(PaginaExtraida)
            .filter(PaginaExtraida.execucao_id == execucao.id)
            .all()
        )
        assert len(paginas) == 1
        assert paginas[0].status == PaginaStatus.SUCESSO

    def test_run_docling_extract_url_chamado_com_metodo_docling(self, db, mock_storage):
        """Garante que _extract_url recebe metodo_extracao=DOCLING."""
        execucao = self._make_execucao(db, ["https://x.com"], MetodoExtracao.DOCLING)
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.return_value = SUCESSO
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

            _, kwargs = m.call_args
            assert kwargs.get("metodo_extracao") == MetodoExtracao.DOCLING

    def test_run_html2text_extract_url_chamado_com_metodo_html2text(
        self, db, mock_storage
    ):
        """Garante compatibilidade retroativa: HTML2TEXT continua sendo passado."""
        execucao = self._make_execucao(db, ["https://x.com"], MetodoExtracao.HTML2TEXT)
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.return_value = SUCESSO
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

            _, kwargs = m.call_args
            assert kwargs.get("metodo_extracao") == MetodoExtracao.HTML2TEXT
