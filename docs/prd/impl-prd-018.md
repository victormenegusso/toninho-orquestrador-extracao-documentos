# Plano de Implementação — PRD-018: Integração Docling

**PRD de referência:** `docs/prd/PRD-018-Integracao-Docling.md`
**Última revisão do plano:** 2026-03-12

---

## Resumo da Ordem de Implementação

| Passo | Camada(s) | Casos de Uso |
|---|---|---|
| 1 | Models + Migrations | UC-06 |
| 2 | Schemas + Frontend + API (integração) | UC-01, UC-05, UC-07, UC-08, UC-09 |
| 3 | Infraestrutura Python | — |
| 4 | Extraction | UC-02, UC-03, UC-04 |
| 5 | Workers | UC-02, UC-03, UC-04, UC-10 |
| 6 | Infra Docker + Testes de Integração | UC-02 a UC-10 |

> **Por que Passo 3 (dependência) vem antes do Passo 4 (extractor)?**
> Os testes unitários de `DoclingPageExtractor` usam `patch("docling.document_converter.DocumentConverter")`,
> que exige que o pacote `docling` seja importável. Sem ele instalado, o `patch` falha na resolução do módulo.

---

## Passo 1 — Fundação: Enum + Model + Migration

**Casos de uso cobertos:** UC-06 (aplicar migration em banco existente)
**Camadas:** `models/`, `migrations/`

### O que implementar

#### `toninho/models/enums.py` — ALTERAR

Adicionar ao final do arquivo, após o enum `PaginaStatus`:

```python
class MetodoExtracao(str, Enum):
    """Motor de extração de HTML para Markdown."""

    HTML2TEXT = "html2text"  # Método atual: BeautifulSoup + html2text (rápido, suporta SPA)
    DOCLING = "docling"      # IBM Docling: saída semântica estruturada (não suporta SPA)
```

#### `toninho/models/configuracao.py` — ALTERAR

1. Adicionar `MetodoExtracao` ao import existente:
   ```python
   from toninho.models.enums import AgendamentoTipo, FormatoSaida, MetodoExtracao
   ```

2. Adicionar campo após `use_browser` (antes dos relacionamentos):
   ```python
   metodo_extracao: Mapped[MetodoExtracao] = mapped_column(
       nullable=False,
       default=MetodoExtracao.HTML2TEXT,
       doc=(
           "Motor de extração de HTML para Markdown. "
           "HTML2TEXT usa BeautifulSoup + html2text (atual). "
           "DOCLING usa IBM Docling para saída semântica estruturada."
       ),
   )
   ```

#### `migrations/versions/20260312_add_metodo_extracao_to_configuracoes.py` — CRIAR

Seguir o padrão da migration `20260303_2230_add_use_browser_to_configuracoes.py`:

```python
"""add metodo_extracao to configuracoes

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "configuracoes",
        sa.Column(
            "metodo_extracao",
            sa.String(length=20),
            nullable=False,
            server_default="html2text",
            comment="Motor de extração: html2text (padrão) ou docling",
        ),
    )


def downgrade() -> None:
    op.drop_column("configuracoes", "metodo_extracao")
```

> **Crítico:** `server_default="html2text"` garante que todos os registros existentes
> sejam preenchidos automaticamente sem intervenção manual. ADR-003 exige isso em toda
> nova coluna `NOT NULL`.

### Testes a escrever

#### `tests/unit/test_models.py` — ALTERAR (adicionar ao final)

```python
# ── Passo 1 — MetodoExtracao + Configuracao.metodo_extracao ──────────────

class TestMetodoExtracaoEnum:
    def test_enum_possui_valor_html2text(self):
        assert MetodoExtracao.HTML2TEXT == "html2text"

    def test_enum_possui_valor_docling(self):
        assert MetodoExtracao.DOCLING == "docling"

    def test_enum_e_string(self):
        assert isinstance(MetodoExtracao.HTML2TEXT, str)


class TestConfiguracaoMetodoExtracao:
    def test_cria_com_default_html2text(self, db, processo, tmp_path):
        config = Configuracao(
            processo_id=processo.id,
            urls=["https://x.com"],
            timeout=60,
            max_retries=1,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir=str(tmp_path),
            agendamento_tipo=AgendamentoTipo.MANUAL,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        assert config.metodo_extracao == MetodoExtracao.HTML2TEXT

    def test_cria_com_metodo_docling(self, db, processo, tmp_path):
        config = Configuracao(
            processo_id=processo.id,
            urls=["https://x.com"],
            timeout=60,
            max_retries=1,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir=str(tmp_path),
            agendamento_tipo=AgendamentoTipo.MANUAL,
            metodo_extracao=MetodoExtracao.DOCLING,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        assert config.metodo_extracao == MetodoExtracao.DOCLING

    def test_metodo_extracao_salvo_como_string_no_banco(self, db, processo, tmp_path):
        """Garante que o enum é salvo como string (ADR-003)."""
        from sqlalchemy import text
        config = Configuracao(
            processo_id=processo.id,
            urls=["https://x.com"],
            timeout=60,
            max_retries=1,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir=str(tmp_path),
            agendamento_tipo=AgendamentoTipo.MANUAL,
        )
        db.add(config)
        db.commit()
        raw = db.execute(
            text("SELECT metodo_extracao FROM configuracoes WHERE id = :id"),
            {"id": str(config.id)},
        ).scalar()
        assert raw == "html2text"
```

#### `tests/unit/test_migrations.py` — CRIAR

```python
"""Testes da migration add_metodo_extracao."""
import pytest
from sqlalchemy import create_engine, inspect, text


def test_migration_upgrade_adiciona_coluna():
    """upgrade() deve adicionar a coluna metodo_extracao com default html2text."""
    from alembic.config import Config
    from alembic import command

    engine = create_engine("sqlite:///:memory:")
    # Aplicar apenas até a migration anterior
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")
    # (Teste simplificado: verificar que a coluna existe após create_all)
    from toninho.models import Base
    Base.metadata.create_all(engine)
    insp = inspect(engine)
    columns = {col["name"] for col in insp.get_columns("configuracoes")}
    assert "metodo_extracao" in columns


def test_coluna_metodo_extracao_tem_default_html2text():
    """O default da coluna deve ser html2text."""
    from sqlalchemy import create_engine, text
    from toninho.models import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        # Inserir sem metodo_extracao via SQL puro para validar server_default
        conn.execute(text(
            "INSERT INTO processos (id, nome, status, created_at, updated_at) "
            "VALUES ('aaaaaaaa-0000-0000-0000-000000000001', 'T', 'ativo', "
            "datetime('now'), datetime('now'))"
        ))
        conn.execute(text(
            "INSERT INTO configuracoes "
            "(id, processo_id, urls, timeout, max_retries, formato_saida, "
            " output_dir, agendamento_tipo, use_browser, created_at, updated_at) "
            "VALUES ('bbbbbbbb-0000-0000-0000-000000000001', "
            "'aaaaaaaa-0000-0000-0000-000000000001', "
            "'[\"https://x.com\"]', 60, 1, 'multiplos_arquivos', "
            "'output', 'manual', 0, datetime('now'), datetime('now'))"
        ))
        conn.commit()
        valor = conn.execute(
            text("SELECT metodo_extracao FROM configuracoes LIMIT 1")
        ).scalar()
    assert valor == "html2text"
```

> **Nota:** O teste de migration completo (upgrade/downgrade real com Alembic) é coberto
> pelos testes de integração na etapa de CI/CD (`alembic upgrade head && alembic downgrade -1`).
> Os testes unitários acima validam o comportamento via `Base.metadata.create_all`.

### Verificação

```bash
# Importações OK
python -c "from toninho.models.enums import MetodoExtracao; print(MetodoExtracao.HTML2TEXT)"
# → html2text

python -c "from toninho.models.configuracao import Configuracao; print('OK')"
# → OK

# Testes unitários passam
pytest tests/unit/test_models.py tests/unit/test_migrations.py -v

# Migration aplica sem erros
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

---

## Passo 2 — Schema + API + Frontend: Configuração com Novo Motor

**Casos de uso cobertos:** UC-01, UC-05, UC-07, UC-08, UC-09
**Camadas:** `schemas/`, `frontend/templates/`, testes de API (camada API é passthrough — sem alteração em routes nem services, pois o SQLAlchemy lê/grava o novo campo automaticamente via schema)

> **Por que não alterar services/routes?**
> `ConfiguracaoService` cria/atualiza `Configuracao` usando `**data` vindo do schema.
> Com o campo `metodo_extracao` presente no schema (e no model), o SQLAlchemy o resolve
> automaticamente. As rotas já retornam `ConfiguracaoResponse`, que incluirá o campo.
> Nenhuma lógica de negócio nova é necessária nesta camada.

### O que implementar

#### `toninho/schemas/configuracao.py` — ALTERAR (3 lugares)

**1. Import** — adicionar `MetodoExtracao`:
```python
from toninho.models.enums import AgendamentoTipo, FormatoSaida, MetodoExtracao
```

**2. `ConfiguracaoCreate`** — adicionar campo após o campo `use_browser`:
```python
metodo_extracao: MetodoExtracao = Field(
    default=MetodoExtracao.HTML2TEXT,
    description=(
        "Motor de extração. "
        "'html2text': método atual (compatível com SPAs via use_browser). "
        "'docling': IBM Docling, saída estruturada para RAG — não suporta SPAs."
    ),
)
```

**3. `ConfiguracaoUpdate`** — adicionar campo após o campo `use_browser` (todos opcionais):
```python
metodo_extracao: MetodoExtracao | None = Field(
    None,
    description="Novo motor de extração (opcional).",
)
```

**4. `ConfiguracaoResponse`** — adicionar campo após `use_browser`:
```python
metodo_extracao: MetodoExtracao = Field(..., description="Motor de extração ativo")
```

> **Atenção:** Atualizar também o docstring da classe `ConfiguracaoResponse` adicionando
> `metodo_extracao` à lista de `Attributes`.

#### `frontend/templates/pages/processos/create.html` — ALTERAR (4 pontos)

**Ponto 1 — `initial_config` Jinja2** (bloco `{% set initial_config = { ... } %}`, ~linha 13):
Adicionar após `'use_browser': ...`:
```jinja2
'metodo_extracao': processo.configuracoes[0].metodo_extracao.value if processo and processo.configuracoes else 'html2text',
```

**Ponto 2 — Alpine.js `config` object** (dentro de `processoForm()`, na seção `config: { ... }`):
Adicionar após `use_browser: Boolean(initialConfig.use_browser)`:
```javascript
metodo_extracao: initialConfig.metodo_extracao || 'html2text',
```

**Ponto 3 — `loadCurrentConfig()` function** (onde os campos são atribuídos de `data`):
Adicionar após `this.config.use_browser = ...` (ou no final dos assignments):
```javascript
this.config.metodo_extracao = data.metodo_extracao || 'html2text';
```

**Ponto 4 — HTML do formulário** (após o `<label>` do checkbox `use_browser`, antes de fechar o bloco de "Configuração de Extração"):
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">
        Motor de Extração
    </label>
    <select x-model="config.metodo_extracao"
            class="w-full px-3 py-2 border border-gray-300 rounded-md
                   focus:outline-none focus:ring-2 focus:ring-blue-500">
        <option value="html2text">HTML2Text (padrão — compatível com SPAs)</option>
        <option value="docling">Docling — estruturado, ideal para RAG</option>
    </select>
    <p class="mt-1 text-xs text-gray-500">
        Docling produz Markdown semântico com tabelas bem formatadas.
    </p>
</div>

<div x-show="config.metodo_extracao === 'docling'"
     x-cloak
     class="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
    <strong>⚠ Atenção:</strong> O Docling não suporta páginas que dependem de
    JavaScript para renderizar conteúdo (SPAs). Ative "Usar navegador (Playwright)"
    apenas como pré-renderizador opcional; a qualidade pode variar.
</div>
```

> **`x-cloak`:** previne flash do aviso no carregamento inicial da página.
> Certifique-se de que o CSS do Alpine contém `[x-cloak] { display: none !important; }`
> (já deve estar no layout base).

### Testes a escrever

#### `tests/unit/test_schemas.py` — ALTERAR (adicionar nova classe)

```python
# ── Passo 2 — Schemas: metodo_extracao ───────────────────────────────────

class TestConfiguracaoCreateMetodoExtracao:
    def test_default_e_html2text(self):
        schema = ConfiguracaoCreate(
            urls=["https://x.com"],
            output_dir="output",
            agendamento_tipo="manual",
        )
        assert schema.metodo_extracao == MetodoExtracao.HTML2TEXT

    def test_aceita_docling(self):
        schema = ConfiguracaoCreate(
            urls=["https://x.com"],
            output_dir="output",
            agendamento_tipo="manual",
            metodo_extracao="docling",
        )
        assert schema.metodo_extracao == MetodoExtracao.DOCLING

    def test_rejeita_valor_invalido(self):
        with pytest.raises(ValidationError):
            ConfiguracaoCreate(
                urls=["https://x.com"],
                output_dir="output",
                agendamento_tipo="manual",
                metodo_extracao="invalido",
            )


class TestConfiguracaoUpdateMetodoExtracao:
    def test_campo_opcional_ausente(self):
        schema = ConfiguracaoUpdate()
        assert schema.metodo_extracao is None

    def test_aceita_docling(self):
        schema = ConfiguracaoUpdate(metodo_extracao="docling")
        assert schema.metodo_extracao == MetodoExtracao.DOCLING

    def test_aceita_html2text(self):
        schema = ConfiguracaoUpdate(metodo_extracao="html2text")
        assert schema.metodo_extracao == MetodoExtracao.HTML2TEXT


class TestConfiguracaoResponseMetodoExtracao:
    def test_response_inclui_campo(self):
        """ConfiguracaoResponse deve ter o campo metodo_extracao."""
        import inspect
        fields = ConfiguracaoResponse.model_fields
        assert "metodo_extracao" in fields
```

#### `tests/integration/test_api_configuracoes.py` — ALTERAR (adicionar nova classe)

```python
class TestConfigMetodoExtracao:
    """UC-07, UC-08, UC-09 — integração com metodo_extracao."""

    def test_post_com_docling_persiste_e_retorna(self, client, processo):
        payload = {
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "output_dir": "/tmp/output",
            "agendamento_tipo": "manual",
            "metodo_extracao": "docling",
        }
        resp = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes", json=payload
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["metodo_extracao"] == "docling"

    def test_post_sem_metodo_usa_html2text(self, client, processo):
        payload = {
            "urls": ["https://exemplo.com"],
            "timeout": 3600,
            "max_retries": 3,
            "output_dir": "/tmp/output",
            "agendamento_tipo": "manual",
        }
        resp = client.post(
            f"/api/v1/processos/{processo.id}/configuracoes", json=payload
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["metodo_extracao"] == "html2text"

    def test_get_configuracao_retorna_metodo_extracao(self, client, config_factory):
        config = config_factory(metodo_extracao=MetodoExtracao.DOCLING)
        resp = client.get(f"/api/v1/processos/{config.processo_id}/configuracao")
        assert resp.status_code == 200
        assert resp.json()["data"]["metodo_extracao"] == "docling"

    def test_put_atualiza_metodo_de_html2text_para_docling(
        self, client, config_factory
    ):
        config = config_factory()  # default: html2text
        resp = client.put(
            f"/api/v1/configuracoes/{config.id}",
            json={"metodo_extracao": "docling"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["metodo_extracao"] == "docling"

    def test_put_com_metodo_invalido_retorna_422(self, client, config_factory):
        config = config_factory()
        resp = client.put(
            f"/api/v1/configuracoes/{config.id}",
            json={"metodo_extracao": "nao_existe"},
        )
        assert resp.status_code == 422
```

#### `tests/integration/test_frontend_processos.py` — ALTERAR (adicionar ao final)

```python
def test_form_criacao_exibe_seletor_motor_extracao(client):
    """Página de criação deve conter o select de motor e as duas opções."""
    resp = client.get("/processos/novo")
    assert resp.status_code == 200
    assert 'value="html2text"' in resp.text
    assert 'value="docling"' in resp.text


def test_form_edicao_carrega_metodo_extracao(client, processo_com_config_docling):
    """Página de edição deve carregar metodo_extracao='docling' no initial_config."""
    resp = client.get(f"/processos/{processo_com_config_docling.id}/editar")
    assert resp.status_code == 200
    assert '"metodo_extracao": "docling"' in resp.text
```

> `processo_com_config_docling` é uma fixture que cria um processo com `Configuracao(metodo_extracao=MetodoExtracao.DOCLING)`.

### Verificação

```bash
python -c "
from toninho.schemas.configuracao import ConfiguracaoCreate
s = ConfiguracaoCreate(urls=['https://x.com'], output_dir='out', agendamento_tipo='manual')
print(s.metodo_extracao)  # → html2text
s2 = ConfiguracaoCreate(urls=['https://x.com'], output_dir='out', agendamento_tipo='manual', metodo_extracao='docling')
print(s2.metodo_extracao)  # → docling
"

pytest tests/unit/test_schemas.py -v
pytest tests/integration/test_api_configuracoes.py::TestConfigMetodoExtracao -v
pytest tests/integration/test_frontend_processos.py -v -k "motor"
```

---

## Passo 3 — Dependência Python: Docling

**Casos de uso cobertos:** pré-requisito para Passo 4
**Camadas:** infraestrutura

> Este passo deve ser executado **antes** do Passo 4 para que `uv sync` / `pip install -e .`
> torne `docling` importável — necessário para os mocks nos testes unitários do extrator.

### O que implementar

#### `pyproject.toml` — ALTERAR

Adicionar ao array de dependências principais do projeto (seção `[project].dependencies` ou equivalente):

```toml
"docling>=2.0.0",
```

> **Aviso de tamanho:** o Docling baixa modelos de deep learning (~300 MB) em
> `~/.cache/docling` no primeiro uso. Em CI, configure cache da pasta para evitar
> re-download a cada pipeline.
>
> **Alternativa para ambientes restritos:** mover para dependência opcional:
> ```toml
> [project.optional-dependencies]
> docling = ["docling>=2.0.0"]
> ```
> Neste caso, a importação lazy em `DoclingPageExtractor.__init__` já gera erro descritivo:
> `ModuleNotFoundError: No module named 'docling'`.
> Para instalar: `pip install -e ".[docling]"`.

### Verificação

```bash
# Após editar pyproject.toml:
uv sync            # ou: pip install -e .

python -c "from docling.document_converter import DocumentConverter; print('OK')"
# → OK
```

---

## Passo 4 — Novo Módulo de Extração: DoclingPageExtractor

**Casos de uso cobertos:** UC-02 (HTML estático), UC-03 (SPA + Playwright), UC-04 (falha)
**Camadas:** `extraction/`

### O que implementar

#### `toninho/extraction/docling_extractor.py` — CRIAR

```python
"""
Extrator baseado em IBM Docling.

Converte HTML (estático ou pré-renderizado) para Markdown estruturado
via Docling, preservando hierarquia semântica, tabelas e metadados.

Limitations:
    - Não suporta SPAs (renderização via JavaScript) nativamente.
      Quando use_browser=True, o Playwright pré-renderiza o HTML e
      este módulo converte o resultado. Qualidade pode variar.
"""

import asyncio
import tempfile
from datetime import UTC, datetime

from loguru import logger

from toninho.extraction.storage import StorageInterface
from toninho.extraction.utils import sanitize_filename


class DoclingPageExtractor:
    """Extrai e converte páginas HTML para Markdown usando IBM Docling."""

    def __init__(self, storage: StorageInterface) -> None:
        """
        Inicializa o extrator.

        Args:
            storage: Interface de armazenamento para salvar os arquivos .md.

        Raises:
            ModuleNotFoundError: Se docling não estiver instalado.
        """
        # Importação lazy: não força instalação em ambientes que não usam Docling
        from docling.document_converter import DocumentConverter

        self.storage = storage
        self._converter = DocumentConverter()

    async def extract(self, url: str, output_path: str | None = None) -> dict:
        """
        Converte uma URL em Markdown via Docling e salva no storage.

        O Docling realiza seu próprio fetch HTTP interno. Usar este método
        quando use_browser=False — o Docling acessa a URL diretamente.

        Args:
            url: URL pública a converter.
            output_path: Caminho relativo de saída. Gerado a partir da URL se None.

        Returns:
            Dict com keys:
                status (str): "sucesso" | "erro"
                url (str): URL de origem
                path (str | None): caminho do arquivo salvo
                bytes (int): tamanho em bytes
                title (str): título extraído do h1
                from_cache (bool): sempre False (Docling não usa cache interno)
                error (str | None): mensagem de erro, se houver
        """
        if output_path is None:
            output_path = sanitize_filename(url)

        logger.info(f"[docling] Convertendo: {url}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert_url, url)

            now = datetime.now(UTC).isoformat()
            final_content = self._build_with_frontmatter(
                content=result["markdown"],
                url=url,
                title=result["title"],
                extracted_at=now,
            )
            content_bytes = final_content.encode("utf-8")
            saved_path = await self.storage.save_file(output_path, content_bytes)

            logger.info(
                f"[docling] Salvo em: {saved_path} ({len(content_bytes)} bytes)"
            )

            return {
                "status": "sucesso",
                "url": url,
                "path": saved_path,
                "bytes": len(content_bytes),
                "title": result["title"],
                "from_cache": False,
                "error": None,
            }

        except Exception as exc:
            logger.error(f"[docling] Erro ao converter {url}: {exc}")
            return {
                "status": "erro",
                "url": url,
                "path": None,
                "bytes": 0,
                "title": "",
                "from_cache": False,
                "error": str(exc),
            }

    async def extract_from_html(
        self, html_content: bytes, url: str, output_path: str | None = None
    ) -> dict:
        """
        Converte HTML já obtido (ex: pré-renderizado via Playwright) usando Docling.

        Escreve o HTML em arquivo temporário e o entrega ao Docling.
        Usado quando use_browser=True: Playwright pré-renderiza, Docling converte.

        Args:
            html_content: Conteúdo HTML em bytes.
            url: URL de origem (usada nos metadados do frontmatter).
            output_path: Caminho relativo de saída.

        Returns:
            Mesmo formato de `extract()`.
        """
        if output_path is None:
            output_path = sanitize_filename(url)

        logger.info(f"[docling] Convertendo HTML pré-renderizado: {url}")

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert_html_bytes, html_content, url
            )

            now = datetime.now(UTC).isoformat()
            final_content = self._build_with_frontmatter(
                content=result["markdown"],
                url=url,
                title=result["title"],
                extracted_at=now,
            )
            content_bytes = final_content.encode("utf-8")
            saved_path = await self.storage.save_file(output_path, content_bytes)

            logger.info(
                f"[docling] Salvo em: {saved_path} ({len(content_bytes)} bytes)"
            )

            return {
                "status": "sucesso",
                "url": url,
                "path": saved_path,
                "bytes": len(content_bytes),
                "title": result["title"],
                "from_cache": False,
                "error": None,
            }

        except Exception as exc:
            logger.error(f"[docling] Erro ao converter HTML de {url}: {exc}")
            return {
                "status": "erro",
                "url": url,
                "path": None,
                "bytes": 0,
                "title": "",
                "from_cache": False,
                "error": str(exc),
            }

    async def close(self) -> None:
        """Compatibilidade de interface com PageExtractor. Sem recursos a liberar."""
        pass

    # ──────────────────────────────────────────── helpers síncronos ────────────
    # Executados em thread pool via run_in_executor para não bloquear o event loop.

    def _convert_url(self, url: str) -> dict:
        """Chama Docling passando a URL diretamente (Docling faz o fetch)."""
        result = self._converter.convert(url)
        markdown = result.document.export_to_markdown()
        title = self._extract_title_from_markdown(markdown)
        return {"markdown": markdown, "title": title}

    def _convert_html_bytes(self, html_content: bytes, url: str) -> dict:
        """
        Salva HTML em arquivo temporário e entrega ao Docling.

        O arquivo é removido automaticamente ao sair do bloco with.
        """
        with tempfile.NamedTemporaryFile(suffix=".html", delete=True) as tmp:
            tmp.write(html_content)
            tmp.flush()
            result = self._converter.convert(tmp.name)

        markdown = result.document.export_to_markdown()
        title = self._extract_title_from_markdown(markdown)
        return {"markdown": markdown, "title": title}

    @staticmethod
    def _extract_title_from_markdown(markdown: str) -> str:
        """Extrai o título do primeiro h1 do Markdown gerado pelo Docling."""
        for line in markdown.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    @staticmethod
    def _build_with_frontmatter(
        content: str, url: str, title: str, extracted_at: str
    ) -> str:
        """
        Adiciona frontmatter YAML ao Markdown.

        Mantém o mesmo formato do html2text (`extrator` difere para rastreabilidade).
        """
        frontmatter = [
            "---",
            f"url: {url}",
            f'titulo: "{title}"',
            f"extraido_em: {extracted_at}",
            "extrator: Toninho/Docling v1.0",
            "---",
            "",
        ]
        return "\n".join(frontmatter) + content
```

### Testes a escrever

#### `tests/unit/extraction/test_docling_extractor.py` — CRIAR

```python
"""Testes unitários para DoclingPageExtractor."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from toninho.extraction.storage import LocalFileSystemStorage


SAMPLE_MARKDOWN = "# Título da Página\n\nConteúdo do documento."
MOCK_RESULT = MagicMock()
MOCK_RESULT.document.export_to_markdown.return_value = SAMPLE_MARKDOWN


@pytest.fixture
def storage(tmp_path):
    return LocalFileSystemStorage(base_dir=str(tmp_path))


@pytest.fixture
def extractor(storage):
    with patch("toninho.extraction.docling_extractor.DocumentConverter") as mock_cls:
        mock_cls.return_value = MagicMock()
        from toninho.extraction.docling_extractor import DoclingPageExtractor
        ext = DoclingPageExtractor(storage)
        ext._converter.convert.return_value = MOCK_RESULT
        yield ext


class TestDoclingPageExtractorExtract:
    @pytest.mark.asyncio
    async def test_retorna_status_sucesso(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["status"] == "sucesso"

    @pytest.mark.asyncio
    async def test_retorna_bytes_positivos(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["bytes"] > 0

    @pytest.mark.asyncio
    async def test_retorna_titulo_do_h1(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["title"] == "Título da Página"

    @pytest.mark.asyncio
    async def test_from_cache_sempre_false(self, extractor):
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["from_cache"] is False

    @pytest.mark.asyncio
    async def test_arquivo_salvo_contém_frontmatter_docling(
        self, extractor, tmp_path
    ):
        await extractor.extract("https://exemplo.com", "out.md")
        content = (tmp_path / "out.md").read_text()
        assert "extrator: Toninho/Docling v1.0" in content
        assert "---" in content

    @pytest.mark.asyncio
    async def test_retorna_erro_quando_docling_falha(self, extractor):
        extractor._converter.convert.side_effect = Exception("timeout docling")
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["status"] == "erro"
        assert "timeout docling" in result["error"]
        assert result["bytes"] == 0
        assert result["path"] is None

    @pytest.mark.asyncio
    async def test_erro_nao_propaga_excecao(self, extractor):
        """extract() deve capturar exceptions e retornar dict, não propagar."""
        extractor._converter.convert.side_effect = RuntimeError("crash")
        result = await extractor.extract("https://exemplo.com", "out.md")
        assert result["status"] == "erro"


class TestDoclingPageExtractorExtractFromHtml:
    @pytest.mark.asyncio
    async def test_retorna_status_sucesso(self, extractor):
        html = b"<html><body><h1>Test</h1></body></html>"
        result = await extractor.extract_from_html(html, "https://x.com", "out.md")
        assert result["status"] == "sucesso"

    @pytest.mark.asyncio
    async def test_chama_convert_com_arquivo_temporario(self, extractor):
        """_convert_html_bytes deve chamar convert() com um path de arquivo, não URL."""
        html = b"<html><body></body></html>"
        extractor._converter.convert.return_value = MOCK_RESULT

        await extractor.extract_from_html(html, "https://x.com", "out.md")

        call_arg = extractor._converter.convert.call_args[0][0]
        # O argumento é um path de arquivo temporário, não a URL
        assert call_arg != "https://x.com"
        assert call_arg.endswith(".html")

    @pytest.mark.asyncio
    async def test_retorna_erro_quando_docling_falha(self, extractor):
        extractor._converter.convert.side_effect = ValueError("parse error")
        html = b"<html><body></body></html>"
        result = await extractor.extract_from_html(html, "https://x.com", "out.md")
        assert result["status"] == "erro"
        assert "parse error" in result["error"]


class TestDoclingPageExtractorHelpers:
    def test_extract_title_retorna_h1(self, extractor):
        md = "# Meu Título\n\nConteúdo aqui."
        assert extractor._extract_title_from_markdown(md) == "Meu Título"

    def test_extract_title_sem_h1_retorna_vazio(self, extractor):
        md = "## Subtítulo\n\nSem H1."
        assert extractor._extract_title_from_markdown(md) == ""

    def test_extract_title_h1_com_espacos(self, extractor):
        md = "#  Título com espaços extras  \n\nBody."
        assert extractor._extract_title_from_markdown(md) == "Título com espaços extras"

    def test_build_frontmatter_contem_campos_obrigatorios(self, extractor):
        result = extractor._build_with_frontmatter(
            content="# Body",
            url="https://x.com",
            title="Título",
            extracted_at="2026-03-12T00:00:00Z",
        )
        assert "url: https://x.com" in result
        assert 'titulo: "Título"' in result
        assert "extrator: Toninho/Docling v1.0" in result
        assert result.startswith("---")

    def test_build_frontmatter_nao_contem_extrator_html2text(self, extractor):
        result = extractor._build_with_frontmatter(
            content="body", url="https://x.com", title="T", extracted_at="2026"
        )
        assert "Toninho v1.0" not in result
        assert "Toninho/Docling v1.0" in result

    @pytest.mark.asyncio
    async def test_close_nao_levanta_excecao(self, extractor):
        await extractor.close()  # deve completar sem erros
```

### Verificação

```bash
pytest tests/unit/extraction/test_docling_extractor.py -v
# Todos os testes devem passar com mocks (sem chamar Docling real)
```

---

## Passo 5 — Worker: Roteamento no ExtractionOrchestrator

**Casos de uso cobertos:** UC-02, UC-03, UC-04, UC-10 (logs com identificação do motor)
**Camadas:** `workers/`

### O que implementar

#### `toninho/workers/utils.py` — ALTERAR (3 pontos)

**Ponto 1 — Import no topo do arquivo:**
Adicionar `MetodoExtracao` ao import de enums:
```python
from toninho.models.enums import ExecucaoStatus, LogNivel, MetodoExtracao, PaginaStatus
```

**Ponto 2 — Método `run()`, após a linha `use_browser = getattr(...)`:**
```python
use_browser = getattr(configuracao, "use_browser", False)
metodo_extracao = getattr(configuracao, "metodo_extracao", MetodoExtracao.HTML2TEXT)
```

Atualizar o log inicial para incluir o motor:
```python
self._add_log(
    db,
    execucao_id,
    LogNivel.INFO,
    f"Iniciando extração de {total} URLs com motor={metodo_extracao.value}",
    contexto={
        "total_urls": total,
        "urls": urls,
        "metodo_extracao": metodo_extracao.value,
    },
)
```

Atualizar a chamada de `asyncio.run(self._extract_url(...))`:
```python
resultado = asyncio.run(
    self._extract_url(
        storage,
        url,
        output_path,
        use_browser=use_browser,
        metodo_extracao=metodo_extracao,
    )
)
```

**Ponto 3 — Método estático `_extract_url()`:**

Substituir a implementação atual:
```python
@staticmethod
async def _extract_url(
    storage: StorageInterface,
    url: str,
    output_path: str,
    use_browser: bool = False,
    metodo_extracao: MetodoExtracao = MetodoExtracao.HTML2TEXT,
) -> dict:
    """Executa extração async de uma URL, escolhendo o motor correto.

    Args:
        storage: Interface de armazenamento.
        url: URL a extrair.
        output_path: Caminho relativo de saída.
        use_browser: Se True, usa Playwright para pré-renderizar (ambos os motores).
        metodo_extracao: Motor de conversão HTML→Markdown.

    Returns:
        Dict com status, url, path, bytes, title, from_cache, error.
    """
    if metodo_extracao == MetodoExtracao.DOCLING:
        from toninho.extraction.docling_extractor import DoclingPageExtractor

        extractor = DoclingPageExtractor(storage)

        if use_browser:
            # Playwright pré-renderiza → HTML bytes → Docling converte
            from toninho.extraction.browser_client import BrowserClient

            browser = BrowserClient(timeout=60_000)
            await browser.start()
            try:
                response = await browser.get(url)
            finally:
                await browser.close()
            return await extractor.extract_from_html(
                response["content"], url, output_path
            )
        else:
            # Docling faz o fetch HTTP interno
            return await extractor.extract(url, output_path)

    else:
        # Método padrão: PageExtractor (httpx + html2text)
        extractor_h2t = PageExtractor(
            storage, timeout=60, max_retries=3, use_browser=use_browser
        )
        try:
            return await extractor_h2t.extract(url, output_path)
        finally:
            await extractor_h2t.close()
```

> **Atenção:** o import de `MetodoExtracao` no topo do arquivo torna desnecessário o import
> local dentro de `_extract_url`. O import de `DoclingPageExtractor` permanece lazy
> (dentro do if) para não forçar a dependência em ambientes sem Docling.

### Testes a escrever

#### `tests/unit/workers/test_orchestrator.py` — ALTERAR (adicionar nova classe)

```python
class TestExtractionOrchestratorMetodoExtracao:
    """Passo 5 — testes de roteamento de motor."""

    @pytest.mark.asyncio
    async def test_extract_url_html2text_instancia_page_extractor(
        self, mock_storage
    ):
        """Deve usar PageExtractor quando metodo=HTML2TEXT."""
        with patch(
            "toninho.workers.utils.PageExtractor"
        ) as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.extract.return_value = {
                "status": "sucesso", "url": "https://x.com",
                "path": "out.md", "bytes": 100, "title": "T",
                "from_cache": False, "error": None,
            }
            mock_cls.return_value = mock_instance

            await ExtractionOrchestrator._extract_url(
                mock_storage,
                "https://x.com",
                "out.md",
                use_browser=False,
                metodo_extracao=MetodoExtracao.HTML2TEXT,
            )

            mock_cls.assert_called_once()
            mock_instance.extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_url_docling_sem_browser_chama_extract(
        self, mock_storage
    ):
        """DOCLING + use_browser=False deve chamar DoclingPageExtractor.extract()."""
        with patch(
            "toninho.workers.utils.DoclingPageExtractor"  # import lazy no módulo
        ) as mock_cls:
            # Note: o import lazy faz o patch ser no namespace do módulo worker
            # Alternativa: patch("toninho.extraction.docling_extractor.DoclingPageExtractor")
            pass

        # Abordagem alternativa usando patch no módulo de extração:
        with patch(
            "toninho.extraction.docling_extractor.DoclingPageExtractor"
        ) as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.extract.return_value = {
                "status": "sucesso", "url": "https://x.com",
                "path": "out.md", "bytes": 200, "title": "T",
                "from_cache": False, "error": None,
            }
            mock_cls.return_value = mock_instance

            await ExtractionOrchestrator._extract_url(
                mock_storage,
                "https://x.com",
                "out.md",
                use_browser=False,
                metodo_extracao=MetodoExtracao.DOCLING,
            )

            mock_instance.extract.assert_called_once_with(
                "https://x.com", "out.md"
            )
            mock_instance.extract_from_html.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_url_docling_com_browser_chama_extract_from_html(
        self, mock_storage
    ):
        """DOCLING + use_browser=True deve chamar extract_from_html com HTML do browser."""
        mock_html = b"<html><body>rendered</body></html>"

        with (
            patch(
                "toninho.extraction.docling_extractor.DoclingPageExtractor"
            ) as mock_docling_cls,
            patch(
                "toninho.extraction.browser_client.BrowserClient"
            ) as mock_browser_cls,
        ):
            mock_browser = AsyncMock()
            mock_browser.get.return_value = {"content": mock_html}
            mock_browser_cls.return_value = mock_browser

            mock_docling = AsyncMock()
            mock_docling.extract_from_html.return_value = {
                "status": "sucesso", "url": "https://x.com",
                "path": "out.md", "bytes": 300, "title": "T",
                "from_cache": False, "error": None,
            }
            mock_docling_cls.return_value = mock_docling

            await ExtractionOrchestrator._extract_url(
                mock_storage,
                "https://x.com",
                "out.md",
                use_browser=True,
                metodo_extracao=MetodoExtracao.DOCLING,
            )

            mock_docling.extract_from_html.assert_called_once_with(
                mock_html, "https://x.com", "out.md"
            )

    def test_run_com_docling_inclui_motor_no_log(
        self, db, processo, mock_storage, tmp_path
    ):
        """Log inicial deve identificar o motor docling."""
        from toninho.models.log import Log

        config = Configuracao(
            processo_id=processo.id,
            urls=["https://x.com"],
            timeout=30,
            max_retries=1,
            formato_saida=FormatoSaida.MULTIPLOS_ARQUIVOS,
            output_dir=str(tmp_path),
            agendamento_tipo=AgendamentoTipo.MANUAL,
            metodo_extracao=MetodoExtracao.DOCLING,
        )
        db.add(config)
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()

        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = {
                "status": "sucesso", "url": "https://x.com",
                "path": "out.md", "bytes": 100, "title": "T",
                "from_cache": False, "error": None,
            }
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

        logs = db.query(Log).filter(Log.execucao_id == execucao.id).all()
        log_inicial = next(
            (l for l in logs if "Iniciando" in l.mensagem), None
        )
        assert log_inicial is not None
        assert "docling" in log_inicial.mensagem.lower()

    def test_run_html2text_nao_quebra_comportamento_existente(
        self, db, processo, configuracao, mock_storage
    ):
        """Configurações sem metodo_extracao (ou com HTML2TEXT) devem funcionar igual ao anterior."""
        # configuracao fixture não tem metodo_extracao explícito → default HTML2TEXT
        execucao = Execucao(processo_id=processo.id, status=ExecucaoStatus.CRIADO)
        db.add(execucao)
        db.commit()

        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = {
                "status": "sucesso", "url": "https://x.com",
                "path": "out.md", "bytes": 100, "title": "T",
                "from_cache": False, "error": None,
            }
            resultado = ExtractionOrchestrator(db, storage=mock_storage).run(
                execucao.id
            )

        assert resultado["status"] == ExecucaoStatus.CONCLUIDO
```

### Verificação

```bash
# Todos os testes existentes do orchestrator devem continuar passando
pytest tests/unit/workers/test_orchestrator.py -v

# Verificar que o import de MetodoExtracao no topo do módulo não quebra nada
python -c "from toninho.workers.utils import ExtractionOrchestrator; print('OK')"
```

---

## Passo 6 — Infraestrutura Docker + Testes de Integração + Cobertura

**Casos de uso cobertos:** todos (UC-01 a UC-10), validação final
**Camadas:** infraestrutura + integração

### O que implementar

#### `docker-compose.override.yml` — ALTERAR

Adicionar volume persistente para cache dos modelos do Docling no worker:

```yaml
services:
  worker:
    volumes:
      - docling_cache:/root/.cache/docling

volumes:
  docling_cache:
```

> **Por quê:** O Docling faz download de modelos de ML (~300 MB) em `~/.cache/docling`
> no primeiro uso. Sem volume persistente, cada restart do container re-baixa os modelos,
> tornando o cold start muito lento (5-10 min em conexões lentas).

#### `tests/integration/test_workers_docling.py` — CRIAR

Testes de integração que cobrem o fluxo completo com banco SQLite em memória e Docling mockado:

```python
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
    eng = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
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
    "status": "sucesso", "url": "https://x.com", "path": "x.md",
    "bytes": 512, "title": "X", "from_cache": False, "error": None,
}
ERRO = {
    "status": "erro", "url": "https://x.com/falha", "path": None,
    "bytes": 0, "title": "", "from_cache": False,
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
        execucao = self._make_execucao(
            db, ["https://x.com"], MetodoExtracao.DOCLING
        )
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

    def test_run_docling_falha_parcial_gera_concluido_com_erros(
        self, db, mock_storage
    ):
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
        execucao = self._make_execucao(
            db, ["https://x.com"], MetodoExtracao.DOCLING
        )
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

    def test_run_docling_extract_url_chamado_com_metodo_docling(
        self, db, mock_storage
    ):
        """Garante que _extract_url recebe metodo_extracao=DOCLING."""
        execucao = self._make_execucao(
            db, ["https://x.com"], MetodoExtracao.DOCLING
        )
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
        execucao = self._make_execucao(
            db, ["https://x.com"], MetodoExtracao.HTML2TEXT
        )
        with patch.object(
            ExtractionOrchestrator, "_extract_url", new_callable=AsyncMock
        ) as m:
            m.return_value = SUCESSO
            ExtractionOrchestrator(db, storage=mock_storage).run(execucao.id)

            _, kwargs = m.call_args
            assert kwargs.get("metodo_extracao") == MetodoExtracao.HTML2TEXT
```

### Verificação Final

```bash
# Docker: validar YAML
docker compose -f docker-compose.yml -f docker-compose.override.yml config

# Testes de integração do worker com Docling
pytest tests/integration/test_workers_docling.py -v

# Suite completa com cobertura
make test
# ou:
pytest tests/ --cov=toninho --cov-report=term-missing --cov-fail-under=90

# Linter + type check (ADR-007)
ruff check toninho/
mypy toninho/
bandit -r toninho/ -ll
```

---

## Checklist de Conclusão

Ao finalizar todos os passos, verificar os critérios de aceite do PRD:

- [ ] `MetodoExtracao` enum com valores `"html2text"` e `"docling"` em `enums.py`
- [ ] Model `Configuracao` com campo `metodo_extracao` (default `HTML2TEXT`)
- [ ] Migration com `server_default="html2text"` aplicada sem erros em banco existente
- [ ] `ConfiguracaoCreate` / `ConfiguracaoUpdate` / `ConfiguracaoResponse` incluem `metodo_extracao`
- [ ] Formulário front-end exibe seletor de motor com aviso de SPA para Docling
- [ ] `DoclingPageExtractor` implementado com `extract()`, `extract_from_html()` e `close()`
- [ ] Frontmatter gerado contém `extrator: Toninho/Docling v1.0`
- [ ] `ExtractionOrchestrator._extract_url()` roteia para o motor correto
- [ ] Log inicial da execução identifica o motor em uso
- [ ] `docling>=2.0.0` em `pyproject.toml`
- [ ] Volume `docling_cache` em `docker-compose.override.yml`
- [ ] Cobertura de testes ≥ 90% (`make test`)
- [ ] `ruff check toninho/` sem erros
- [ ] `mypy toninho/` sem erros
- [ ] Execução com `html2text` funciona sem regressão

---

## Diagrama de Dependências entre Passos

```
Passo 1 (Enum + Model + Migration)
    └─► Passo 2 (Schema + API + Frontend)
            └─► Passo 3 (pyproject.toml — instalar docling)
                    └─► Passo 4 (DoclingPageExtractor)
                            └─► Passo 5 (Worker: roteamento)
                                    └─► Passo 6 (Docker + Integração + Cobertura)
```

Cada passo depende do anterior. Não é possível pular etapas:
- Passo 2 exige o enum `MetodoExtracao` do Passo 1 para o schema.
- Passo 4 exige o pacote instalado (Passo 3) para que os mocks funcionem.
- Passo 5 exige `DoclingPageExtractor` existente (Passo 4) para o import lazy no worker.
- Passo 6 exige tudo implementado para validar o fluxo end-to-end.
