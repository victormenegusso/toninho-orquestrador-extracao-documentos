"""
Testes de integração Models↔Schemas.

Valida que a conversão entre models e schemas funciona perfeitamente,
incluindo relacionamentos e computed fields.
"""

from sqlalchemy.orm import Session

from toninho.models import (
    AgendamentoTipo,
    Configuracao,
    Execucao,
    FormatoSaida,
    Log,
    LogNivel,
    PaginaExtraida,
    PaginaStatus,
    Processo,
    ProcessoStatus,
)
from toninho.schemas import (
    ConfiguracaoResponse,
    ExecucaoResponse,
    LogResponse,
    PaginaExtraidaResponse,
    ProcessoResponse,
)


def test_full_workflow_model_to_schema(db: Session) -> None:
    """
    Testa workflow completo: criar models, converter para schemas.

    Simula um fluxo real de criação de processo, configuração,
    execução, logs e páginas, e valida conversão para schemas.
    """
    # Criar processo
    processo = Processo(
        nome="Processo Integração",
        descricao="Teste de integração completa",
        status=ProcessoStatus.ATIVO,
    )
    db.add(processo)
    db.commit()
    db.refresh(processo)

    # Converter processo para schema
    processo_schema = ProcessoResponse.model_validate(processo)
    assert processo_schema.id == processo.id
    assert processo_schema.nome == processo.nome

    # Criar configuração
    config = Configuracao(
        processo_id=processo.id,
        urls=["https://exemplo.com", "https://exemplo.com/pagina2"],
        timeout=1800,
        max_retries=3,
        formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
        output_dir="/tmp/output",
        agendamento_tipo=AgendamentoTipo.MANUAL,
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    # Converter configuração para schema
    config_schema = ConfiguracaoResponse.model_validate(config)
    assert config_schema.processo_id == processo.id
    assert len(config_schema.urls) == 2

    # Criar execução
    execucao = Execucao(
        processo_id=processo.id,
        paginas_processadas=2,
        bytes_extraidos=2048,
    )
    db.add(execucao)
    db.commit()
    db.refresh(execucao)

    # Converter execução para schema
    execucao_schema = ExecucaoResponse.model_validate(execucao)
    assert execucao_schema.processo_id == processo.id
    assert execucao_schema.paginas_processadas == 2
    assert execucao_schema.em_andamento is False  # status default é CRIADO

    # Criar logs
    log1 = Log(
        execucao_id=execucao.id,
        nivel=LogNivel.INFO,
        mensagem="Início da execução",
    )
    log2 = Log(
        execucao_id=execucao.id,
        nivel=LogNivel.INFO,
        mensagem="Página 1 extraída",
        contexto={"url": "https://exemplo.com"},
    )
    db.add_all([log1, log2])
    db.commit()
    db.refresh(log1)
    db.refresh(log2)

    # Converter logs para schemas
    log1_schema = LogResponse.model_validate(log1)
    log2_schema = LogResponse.model_validate(log2)
    assert log1_schema.execucao_id == execucao.id
    assert log2_schema.contexto["url"] == "https://exemplo.com"

    # Criar páginas extraídas
    pagina1 = PaginaExtraida(
        execucao_id=execucao.id,
        url_original="https://exemplo.com",
        caminho_arquivo="/tmp/output/pagina1.md",
        status=PaginaStatus.SUCESSO,
        tamanho_bytes=1024,
    )
    pagina2 = PaginaExtraida(
        execucao_id=execucao.id,
        url_original="https://exemplo.com/pagina2",
        caminho_arquivo="/tmp/output/pagina2.md",
        status=PaginaStatus.SUCESSO,
        tamanho_bytes=1024,
    )
    db.add_all([pagina1, pagina2])
    db.commit()
    db.refresh(pagina1)
    db.refresh(pagina2)

    # Converter páginas para schemas
    pagina1_schema = PaginaExtraidaResponse.model_validate(pagina1)
    _pagina2_schema = PaginaExtraidaResponse.model_validate(pagina2)
    assert pagina1_schema.execucao_id == execucao.id
    assert "KB" in pagina1_schema.tamanho_legivel  # computed field

    # Verificar relacionamentos via refresh
    db.refresh(processo)
    assert len(processo.configuracoes) == 1
    assert len(processo.execucoes) == 1

    db.refresh(execucao)
    assert len(execucao.logs) == 2
    assert len(execucao.paginas) == 2


def test_cascade_delete_with_schemas(db: Session) -> None:
    """
    Testa que cascade delete funciona e não afeta conversão de schemas.
    """
    # Criar processo com dependências
    processo = Processo(nome="Processo Cascade")
    db.add(processo)
    db.commit()
    db.refresh(processo)

    config = Configuracao(
        processo_id=processo.id,
        urls=["https://exemplo.com"],
        output_dir="/tmp",
    )
    execucao = Execucao(processo_id=processo.id)
    db.add_all([config, execucao])
    db.commit()

    # Converter para schemas antes de deletar
    processo_schema = ProcessoResponse.model_validate(processo)
    config_schema = ConfiguracaoResponse.model_validate(config)

    # Schemas devem estar válidos
    assert processo_schema.id == processo.id
    assert config_schema.processo_id == processo.id

    # Deletar processo
    processo_id = processo.id
    config_id = config.id
    execucao_id = execucao.id

    db.delete(processo)
    db.commit()

    # Verificar cascade delete
    assert db.query(Processo).filter_by(id=processo_id).first() is None
    assert db.query(Configuracao).filter_by(id=config_id).first() is None
    assert db.query(Execucao).filter_by(id=execucao_id).first() is None


def test_json_serialization(db: Session) -> None:
    """
    Testa que schemas serializam corretamente para JSON.
    """
    processo = Processo(nome="Processo JSON")
    db.add(processo)
    db.commit()
    db.refresh(processo)

    # Converter para schema
    schema = ProcessoResponse.model_validate(processo)

    # Serializar para dict
    data = schema.model_dump()
    assert isinstance(data, dict)
    assert "id" in data
    assert "nome" in data
    assert data["nome"] == "Processo JSON"

    # Serializar para JSON string
    json_str = schema.model_dump_json()
    assert isinstance(json_str, str)
    assert "Processo JSON" in json_str

    # Enum deve ser serializado como valor
    assert data["status"] == "ativo"  # não ProcessoStatus.ATIVO


def test_computed_fields_performance(db: Session) -> None:
    """
    Testa que computed fields não causam N+1 queries.
    """
    # Criar execução com múltiplas páginas
    processo = Processo(nome="Processo Performance")
    db.add(processo)
    db.commit()

    execucao = Execucao(processo_id=processo.id)
    db.add(execucao)
    db.commit()

    # Adicionar 10 páginas
    for i in range(10):
        pagina = PaginaExtraida(
            execucao_id=execucao.id,
            url_original=f"https://exemplo.com/pagina{i}",
            caminho_arquivo=f"/tmp/pagina{i}.md",
            status=PaginaStatus.SUCESSO,
            tamanho_bytes=1024 * (i + 1),
        )
        db.add(pagina)
    db.commit()

    # Buscar execução do banco
    execucao_from_db = db.query(Execucao).filter_by(id=execucao.id).first()

    # Converter para schema
    schema = ExecucaoResponse.model_validate(execucao_from_db)

    # Computed fields devem funcionar sem queries adicionais
    assert schema.em_andamento is False
    assert schema.duracao_segundos is None  # não iniciado

    # Buscar páginas e converter
    paginas = db.query(PaginaExtraida).filter_by(execucao_id=execucao.id).all()
    paginas_schemas = [PaginaExtraidaResponse.model_validate(p) for p in paginas]

    # Computed fields devem funcionar
    assert all(p.tamanho_legivel.endswith(("KB", "B")) for p in paginas_schemas)
    assert len(paginas_schemas) == 10
