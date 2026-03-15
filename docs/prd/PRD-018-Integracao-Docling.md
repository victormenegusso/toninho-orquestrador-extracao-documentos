# PRD-018: Integração Docling como Motor de Extração

**Status**: 📋 Planejado
**Prioridade**: 🟡 Média - Backend Features Avançadas
**Categoria**: Backend + Frontend - Feature
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Introduzir o **Docling** (IBM Research) como segundo motor de extração, permitindo que o usuário escolha, por configuração de processo, entre dois métodos:

| Método | Engine | Quando usar |
|---|---|---|
| `html2text` | BeautifulSoup + html2text (atual) | Sites simples, SPAs, texto corrido |
| `docling` | IBM Docling | HTML estático rico em tabelas, estrutura semântica, RAG |

O método de extração é configurado **por processo** e mantido no histórico de configurações, garantindo rastreabilidade de longo prazo dos dois motores em paralelo.

---

## 2. Contexto e Justificativa

### 2.1. Problema Atual

O motor atual (`html2text`) é eficiente para extração textual, mas tem limitações conhecidas:
- Tabelas HTML são convertidas de forma inconsistente para Markdown.
- A hierarquia semântica (títulos, rodapés, blocos de código) nem sempre é preservada.
- O output bruto exige pós-processamento adicional para uso em pipelines de RAG.

### 2.2. Proposta

O Docling realiza **Document Layout Analysis (DLA)**: identifica blocos semânticos (títulos, parágrafos, tabelas, listas), reconstrói a hierarquia e exporta um Markdown limpo e estruturado, ideal para LLMs e sistemas RAG.

### 2.3. Premissas Confirmadas

- Escopo inicial: **apenas HTML**. Nenhuma mudança no suporte a PDF, DOCX ou imagens.
- O **fluxo geral do Toninho é mantido**: lista de URLs → extração → salvar → registrar `PaginaExtraida`.
- Docling **não suporta SPAs** (renderização via JavaScript). O usuário é avisado no front-end.
- `use_browser` (Playwright) e `metodo_extracao` são ortogonais; `use_browser` apenas pré-renderiza HTML antes da conversão — quando Docling estiver ativo e `use_browser=True`, o HTML renderizado é salvo em disco temporário e passado ao Docling.
- Os **dois métodos coexistirão por longo prazo**. Dados históricos de ambos são preservados.
- Fallback em caso de falha: mesmo comportamento já existente (registrar `PaginaStatus.FALHOU`).
- Validação de qualidade: **manual**, pelo time responsável.

---

## 3. Casos de Uso

### UC-01 — Configurar processo com motor Docling

**Ator:** Usuário do Toninho
**Pré-condição:** Processo já existe ou está sendo criado.
**Fluxo principal:**
1. Usuário acessa o formulário de criação ou edição de um processo.
2. Na seção "Configuração de Extração", localiza o campo **Motor de Extração**.
3. Seleciona a opção **Docling — estruturado, ideal para RAG**.
4. Sistema exibe o aviso: _"⚠ Atenção: O Docling não suporta páginas que dependem de JavaScript para renderizar conteúdo (SPAs)."_
5. Usuário preenche as demais configurações (URLs, timeout, agendamento) e salva.
6. Sistema persiste `metodo_extracao = "docling"` na `Configuracao` do processo.

**Pós-condição:** A próxima execução do processo usará o motor Docling.
**Fluxo alternativo:** Usuário mantém a seleção padrão (**HTML2Text**) — nenhum aviso é exibido e o comportamento é idêntico ao anterior.

---

### UC-02 — Executar processo com motor Docling (HTML estático)

**Ator:** Sistema (worker Celery)
**Pré-condição:** Processo tem `metodo_extracao = "docling"` e `use_browser = false`.
**Fluxo principal:**
1. Worker inicia a tarefa `executar_processo_task`.
2. `ExtractionOrchestrator` lê a configuração e identifica `metodo_extracao = DOCLING`.
3. Para cada URL na lista:
   a. `DoclingPageExtractor.extract(url)` é chamado.
   b. Docling faz o fetch da URL e executa Document Layout Analysis.
   c. Markdown estruturado (com tabelas, hierarquia de títulos) é gerado.
   d. Frontmatter YAML é adicionado (`extrator: Toninho/Docling v1.0`).
   e. Arquivo `.md` é salvo no storage.
   f. `PaginaExtraida` é registrada no banco com `status = SUCESSO`.
4. Execução é marcada como `CONCLUIDO`.

**Pós-condição:** Arquivos `.md` com Markdown semântico estão disponíveis para download.

---

### UC-03 — Executar processo com motor Docling + pré-renderização (SPA)

**Ator:** Sistema (worker Celery)
**Pré-condição:** Processo tem `metodo_extracao = "docling"` e `use_browser = true`.
**Fluxo principal:**
1. Worker inicia a tarefa.
2. Para cada URL:
   a. Playwright (BrowserClient) renderiza a página completa e retorna o HTML.
   b. HTML é salvo em arquivo temporário.
   c. `DoclingPageExtractor.extract_from_html(html, url)` é chamado com o arquivo temporário.
   d. Docling converte o HTML pré-renderizado para Markdown.
   e. Arquivo temporário é deletado automaticamente.
   f. Fluxo segue igual ao UC-02 (salvar, registrar `PaginaExtraida`).

**Pós-condição:** Mesmo que UC-02. Qualidade pode variar em SPAs complexas (avisado no front-end).

---

### UC-04 — Falha de extração com motor Docling

**Ator:** Sistema (worker Celery)
**Pré-condição:** Processo com `metodo_extracao = "docling"` em execução.
**Fluxo principal:**
1. Docling lança exceção ao processar uma URL (URL inacessível, timeout, erro de layout).
2. `DoclingPageExtractor.extract()` captura a exceção e retorna `status = "erro"`.
3. Worker registra `PaginaExtraida` com `status = FALHOU` e `erro_mensagem` preenchido.
4. Log de nível `ERROR` é gravado na execução.
5. Worker **continua para a próxima URL** da lista.
6. Ao final, se houver mix de sucesso e falha, execução é marcada `CONCLUIDO_COM_ERROS`.

**Pós-condição:** Execução não é abortada. Usuário pode verificar os erros no log da execução.
**Nota:** Não há fallback automático para `html2text`. Para mudar de motor, o usuário edita a configuração.

---

### UC-05 — Trocar motor de extração de um processo existente

**Ator:** Usuário do Toninho
**Pré-condição:** Processo já usa `metodo_extracao = "html2text"` e houve execuções anteriores.
**Fluxo principal:**
1. Usuário acessa a edição do processo.
2. Altera o campo **Motor de Extração** de `html2text` para `docling`.
3. Salva a configuração.
4. Sistema persiste nova `Configuracao` (ou atualiza a existente) com `metodo_extracao = "docling"`.
5. Execuções e páginas extraídas **anteriores não são deletadas nem reprocessadas**.
6. A partir da próxima execução disparada manualmente ou por agendamento, o motor Docling é usado.

**Pós-condição:** Histórico de extrações com `html2text` é preservado. Novas extrações usam Docling.

---

### UC-06 — Aplicar migration em banco existente

**Ator:** Administrador / CI-CD
**Pré-condição:** Banco com registros de `Configuracao` criados antes desta feature.
**Fluxo principal:**
1. `alembic upgrade head` é executado.
2. Migration adiciona coluna `metodo_extracao VARCHAR(20) DEFAULT 'html2text'`.
3. Todos os registros existentes recebem automaticamente `metodo_extracao = "html2text"`.
4. Sistema continua funcionando sem qualquer intervenção manual.

**Pós-condição:** Nenhuma configuração existente é afetada. Rollback via `alembic downgrade` remove a coluna sem perda de dados relevantes.

---

### UC-07 — Criar configuração com motor Docling via API

**Ator:** Integração externa / cliente da API REST
**Endpoint:** `POST /api/v1/processos/{processo_id}/configuracoes`
**Pré-condição:** Processo existe.

**Request body:**
```json
{
  "urls": ["https://exemplo.com/relatorio"],
  "metodo_extracao": "docling",
  "use_browser": false,
  "timeout": 3600,
  "max_retries": 3,
  "formato_saida": "multiplos_arquivos",
  "output_dir": "./output",
  "agendamento_tipo": "manual"
}
```

**Fluxo principal:**
1. Cliente envia `POST` com `metodo_extracao = "docling"`.
2. Schema `ConfiguracaoCreate` valida e deserializa o campo.
3. Service persiste `Configuracao` com `metodo_extracao = DOCLING`.
4. API retorna `201 Created` com `ConfiguracaoResponse` incluindo `metodo_extracao: "docling"`.

**Response body (201):**
```json
{
  "data": {
    "id": "<uuid>",
    "processo_id": "<uuid>",
    "urls": ["https://exemplo.com/relatorio"],
    "metodo_extracao": "docling",
    "use_browser": false,
    "timeout": 3600,
    "max_retries": 3,
    "formato_saida": "multiplos_arquivos",
    "output_dir": "output",
    "agendamento_tipo": "manual",
    "agendamento_cron": null,
    "created_at": "2026-03-11T10:00:00Z",
    "updated_at": "2026-03-11T10:00:00Z"
  }
}
```

**Fluxo alternativo — campo omitido:** cliente não envia `metodo_extracao`; sistema usa default `"html2text"`. Comportamento idêntico ao anterior.

---

### UC-08 — Atualizar motor de extração via API

**Ator:** Integração externa / cliente da API REST
**Endpoint:** `PUT /api/v1/configuracoes/{config_id}`
**Pré-condição:** Configuração existe com `metodo_extracao = "html2text"`.

**Request body (campos parciais):**
```json
{
  "metodo_extracao": "docling"
}
```

**Fluxo principal:**
1. Cliente envia `PUT` com apenas `metodo_extracao`.
2. `ConfiguracaoUpdate` aceita o campo (todos opcionais).
3. Service aplica o merge — somente `metodo_extracao` é alterado.
4. API retorna `200 OK` com `ConfiguracaoResponse` atualizado.

**Pós-condição:** Próxima execução do processo usará Docling. Execuções anteriores não são afetadas.

---

### UC-09 — Consultar configuração atual e verificar motor via API

**Ator:** Integração externa / dashboard
**Endpoint:** `GET /api/v1/processos/{processo_id}/configuracao`
**Pré-condição:** Processo tem ao menos uma configuração.

**Fluxo principal:**
1. Cliente faz `GET` para obter a configuração mais recente.
2. API retorna `ConfiguracaoResponse` com o campo `metodo_extracao` preenchido.
3. Cliente usa o valor para exibir o motor ativo no dashboard ou tomar decisões programáticas.

**Response body (200):**
```json
{
  "data": {
    "id": "<uuid>",
    "metodo_extracao": "docling",
    "use_browser": false,
    ...
  }
}
```

---

### UC-10 — Disparar execução e confirmar motor usado via Logs da API

**Ator:** Integração externa
**Endpoints:** `POST /api/v1/processos/{processo_id}/execucoes` → `GET /api/v1/execucoes/{execucao_id}/detalhes`
**Pré-condição:** Configuração ativa tem `metodo_extracao = "docling"`.

**Fluxo principal:**
1. Cliente dispara execução via `POST /api/v1/processos/{id}/execucoes`.
2. API retorna `201` com `execucao_id` e `status = "criado"`.
3. Worker processa e registra logs com mensagem `"[docling] Convertendo: <url>"`.
4. Cliente consulta `GET /api/v1/execucoes/{execucao_id}/detalhes` após conclusão.
5. Response inclui logs com a identificação do motor Docling e páginas com `status = "sucesso"` ou `"falhou"`.

**Pós-condição:** Integração pode rastrear qual motor foi usado auditando os logs da execução.

---

## 4. Requisitos Técnicos

### 4.1. Estrutura de Arquivos Afetados / Criados

```
toninho/models/
└── enums.py                        ← ALTERAR: novo enum MetodoExtracao

toninho/models/
└── configuracao.py                 ← ALTERAR: novo campo metodo_extracao

toninho/schemas/
└── configuracao.py                 ← ALTERAR: metodo_extracao em Create/Update/Response

toninho/extraction/
└── docling_extractor.py            ← CRIAR: DoclingPageExtractor

toninho/workers/
└── utils.py                        ← ALTERAR: ExtractionOrchestrator usa metodo_extracao

frontend/templates/pages/processos/
└── create.html                     ← ALTERAR: seletor de metodo_extracao + aviso SPA

migrations/versions/
└── <hash>_add_metodo_extracao.py   ← CRIAR: nova migration Alembic

pyproject.toml                      ← ALTERAR: adicionar dependência docling
```

---

### 4.2. Novo Enum (toninho/models/enums.py)

Adicionar ao arquivo:

```python
class MetodoExtracao(str, Enum):
    """Motor de extração de HTML para Markdown."""

    HTML2TEXT = "html2text"  # Método atual: BeautifulSoup + html2text (rápido, suporta SPA)
    DOCLING = "docling"      # IBM Docling: saída semântica estruturada (não suporta SPA)
```

---

### 4.3. Model Configuracao (toninho/models/configuracao.py)

**Novo campo** na tabela `configuracoes`:

```python
from toninho.models.enums import MetodoExtracao  # adicionar ao import

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

**Migration correspondente** — ver §4.8.

---

### 4.4. Schemas de Configuração (toninho/schemas/configuracao.py)

Adicionar `metodo_extracao` nos três schemas existentes:

**ConfiguracaoCreate** — campo novo:
```python
from toninho.models.enums import MetodoExtracao  # adicionar ao import

metodo_extracao: MetodoExtracao = Field(
    default=MetodoExtracao.HTML2TEXT,
    description=(
        "Motor de extração. "
        "'html2text': método atual (compatível com SPAs via use_browser). "
        "'docling': IBM Docling, saída estruturada para RAG — não suporta SPAs."
    ),
)
```

**ConfiguracaoUpdate** — campo opcional:
```python
metodo_extracao: MetodoExtracao | None = Field(
    None,
    description="Novo motor de extração (opcional).",
)
```

**ConfiguracaoResponse** — campo de leitura:
```python
metodo_extracao: MetodoExtracao
```

---

### 4.5. Novo Módulo de Extração (toninho/extraction/docling_extractor.py)

**Responsabilidade**: encapsular o Docling, mantendo a mesma interface de `PageExtractor.extract()`.

```python
"""
Extrator baseado em IBM Docling.

Converte HTML (estático) para Markdown estruturado via Docling,
preservando hierarquia semântica, tabelas e metadados.

Limitações:
- Não suporta SPAs (páginas renderizadas via JavaScript).
  Use use_browser=True na configuração para pré-renderizar e então
  passar o HTML ao Docling, mas a qualidade pode variar.
"""

import asyncio
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from toninho.extraction.storage import StorageInterface
from toninho.extraction.utils import sanitize_filename


class DoclingPageExtractor:
    """Extrai páginas HTML para Markdown usando IBM Docling."""

    def __init__(self, storage: StorageInterface):
        """
        Args:
            storage: Interface de armazenamento para salvar o arquivo .md resultante.
        """
        self.storage = storage
        # Importação lazy para não forçar instalação em ambientes que não usam Docling
        from docling.document_converter import DocumentConverter
        self._converter = DocumentConverter()

    # ------------------------------------------------------------------
    # API pública — mesma interface que PageExtractor
    # ------------------------------------------------------------------

    async def extract(self, url: str, output_path: str | None = None) -> dict:
        """
        Converte uma URL em Markdown via Docling e salva no storage.

        Args:
            url: URL pública a converter.
            output_path: Caminho relativo de saída. Gerado a partir da URL se None.

        Returns:
            Dict com keys:
                status (str): "sucesso" | "erro"
                url (str)
                path (str | None): caminho do arquivo salvo
                bytes (int): tamanho em bytes
                title (str)
                from_cache (bool): sempre False (Docling não usa cache interno)
                error (str | None)
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

            logger.info(f"[docling] Salvo em: {saved_path} ({len(content_bytes)} bytes)")

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

        O HTML é escrito em arquivo temporário e passado ao Docling.

        Args:
            html_content: Conteúdo HTML em bytes.
            url: URL de origem (usada nos metadados).
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
        """Compatibilidade com interface PageExtractor (sem recursos a liberar)."""
        pass

    # ------------------------------------------------------------------
    # Helpers síncronos (executados em thread pool via run_in_executor)
    # ------------------------------------------------------------------

    def _convert_url(self, url: str) -> dict:
        """
        Chama Docling de forma síncrona passando a URL diretamente.
        Executado em thread pool (não bloqueia o event loop).
        """
        result = self._converter.convert(url)
        markdown = result.document.export_to_markdown()
        title = self._extract_title_from_markdown(markdown)
        return {"markdown": markdown, "title": title}

    def _convert_html_bytes(self, html_content: bytes, url: str) -> dict:
        """
        Salva HTML em arquivo temporário e passa ao Docling.
        Executado em thread pool.
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
        """Extrai o título do h1 do Markdown gerado pelo Docling."""
        for line in markdown.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    @staticmethod
    def _build_with_frontmatter(
        content: str, url: str, title: str, extracted_at: str
    ) -> str:
        """Adiciona frontmatter YAML ao Markdown (mesmo formato do html2text)."""
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

**Notas de implementação:**
- Docling é **síncrono**. Toda chamada usa `asyncio.run_in_executor(None, ...)` para não bloquear o event loop.
- `extract_from_html()` é usado quando `use_browser=True` + `metodo_extracao=DOCLING`: o Playwright pré-renderiza o HTML, e o Docling o converte.
- Para `use_browser=False` + `DOCLING`, a URL é passada diretamente ao Docling (ele faz o fetch interno).

---

### 4.6. Worker / Orquestrador (toninho/workers/utils.py)

**Alteração em `ExtractionOrchestrator.run()`** — seção *"4b. Preparar extractor"*:

```python
# Antes (atual):
use_browser = getattr(configuracao, "use_browser", False)

# Depois — adicionar leitura de metodo_extracao:
use_browser = getattr(configuracao, "use_browser", False)
metodo_extracao = getattr(configuracao, "metodo_extracao", MetodoExtracao.HTML2TEXT)
```

**Alteração em `ExtractionOrchestrator._extract_url()`** — aceitar `metodo_extracao`:

```python
@staticmethod
async def _extract_url(
    storage: StorageInterface,
    url: str,
    output_path: str,
    use_browser: bool = False,
    metodo_extracao: MetodoExtracao = MetodoExtracao.HTML2TEXT,
) -> dict:
    """Executa extração async de uma URL, escolhendo o motor correto."""
    from toninho.models.enums import MetodoExtracao as ME

    if metodo_extracao == ME.DOCLING:
        from toninho.extraction.docling_extractor import DoclingPageExtractor

        extractor = DoclingPageExtractor(storage)

        if use_browser:
            # Pré-renderiza com Playwright, depois repassa HTML ao Docling
            from toninho.extraction.browser_client import BrowserClient
            from toninho.extraction.http_client import HTTPClient

            browser = BrowserClient(timeout=60_000)
            await browser.start()
            try:
                response = await browser.get(url)
            finally:
                await browser.close()
            return await extractor.extract_from_html(response["content"], url, output_path)
        else:
            return await extractor.extract(url, output_path)

    else:
        # Método atual: PageExtractor (html2text)
        extractor = PageExtractor(
            storage, timeout=60, max_retries=3, use_browser=use_browser
        )
        try:
            return await extractor.extract(url, output_path)
        finally:
            await extractor.close()
```

**Atualizar chamada em `run()`**:
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

---

### 4.7. Frontend — Formulário de Criação/Edição (frontend/templates/pages/processos/create.html)

**Alterações no bloco "Configuração de Extração":**

1. Adicionar `metodo_extracao` ao objeto `initial_config`:
```javascript
'metodo_extracao': processo.configuracoes[0].metodo_extracao.value
    if processo and processo.configuracoes else 'html2text',
```

2. Adicionar campo de seleção após o campo `use_browser`:
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

<!-- Aviso de limitação exibido somente ao selecionar Docling -->
<div x-show="config.metodo_extracao === 'docling'"
     class="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
    <strong>⚠ Atenção:</strong> O Docling não suporta páginas que dependem de
    JavaScript para renderizar conteúdo (SPAs). Ative "Usar navegador (Playwright)"
    apenas como pré-renderizador opcional; a qualidade pode variar.
</div>
```

---

### 4.8. Migration Alembic

Criar nova migration em `migrations/versions/`:

```python
"""add metodo_extracao to configuracoes

Revision ID: <gerado pelo alembic>
Revises: <revision anterior>
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.add_column(
        "configuracoes",
        sa.Column(
            "metodo_extracao",
            sa.String(length=20),
            nullable=False,
            server_default="html2text",
        ),
    )

def downgrade() -> None:
    op.drop_column("configuracoes", "metodo_extracao")
```

> **Importante:** `server_default="html2text"` garante que todas as configurações existentes continuem funcionando com o método atual sem nenhuma ação manual.

---

### 4.9. Dependência Python (pyproject.toml)

Adicionar ao grupo de dependências principais:

```toml
"docling>=2.0.0",
```

> Docling tem dependências pesadas (modelos de deep learning). Se o ambiente de produção for restrito em armazenamento, avaliar instalar sob dependência opcional:
> ```toml
> [project.optional-dependencies]
> docling = ["docling>=2.0.0"]
> ```
> Neste caso, a importação lazy em `DoclingPageExtractor.__init__` já garante que o erro seja descritivo: `ImportError: Instale docling com: pip install docling`.

---

## 5. Dependências

### 5.1. PRDs Anteriores Impactados

| PRD | Módulo | Tipo de Impacto |
|---|---|---|
| PRD-003 | `toninho/models/enums.py` + `configuracao.py` | Novo enum + nova coluna |
| PRD-004 | `toninho/schemas/configuracao.py` | Novo campo em Create/Update/Response |
| PRD-006 | Módulo Configuração (service, API) | Passthrough automático via schema |
| PRD-011 | Sistema de Extração | Novo extrator, alteração no orquestrador |
| PRD-015 | Interface CRUD Processos | Novo campo no formulário + aviso SPA |

### 5.2. Dependências Externas

| Pacote | Versão mínima | Observação |
|---|---|---|
| `docling` | ≥ 2.0.0 | Apache 2.0. Download de modelos leves no primeiro uso (~300 MB) |
| `docling-core` | (transitiva) | Instalada automaticamente com `docling` |

---

## 6. Regras de Negócio

### 6.1. Escolha do Motor

- `metodo_extracao` é definido **por configuração de processo** e pode ser alterado a qualquer momento via PUT.
- A configuração mais recente é usada na próxima execução (comportamento já existente).
- Alterar `metodo_extracao` não reprocessa execuções antigas.

### 6.2. Coexistência de Dados

- `PaginaExtraida` **não armazena qual motor foi usado**. O histórico do motor é rastreado via `configuracao.metodo_extracao` + `configuracao.created_at`.
- Não haverá campo `metodo_extracao` em `PaginaExtraida` por ora — o escopo é na configuração.

### 6.3. Comportamento de `use_browser`

`use_browser` é um campo **já existente** na `Configuracao`. Ele controla **como o HTML é obtido**, independentemente de qual motor irá convertê-lo. O campo `metodo_extracao` (novo) controla **quem faz a conversão** para Markdown. Os dois campos são ortogonais.

#### Como `use_browser` funciona hoje (html2text)

```
use_browser = false  →  httpx.get(url) → HTML bytes → html2text → Markdown
use_browser = true   →  Playwright.get(url) → HTML bytes → html2text → Markdown
```

- `false` (padrão): usa `HTTPClient` (httpx) com retry e cache in-memory. Rápido, sem overhead de browser. Não executa JavaScript.
- `true`: inicia Playwright (Chromium headless), aguarda `networkidle`, captura o HTML já renderizado com todo o JS executado. Necessário para SPAs.

#### Como `use_browser` interage com Docling (novo)

```
use_browser = false + docling  →  Docling.convert(url) direto
                                   (Docling faz seu próprio fetch HTTP)

use_browser = true  + docling  →  Playwright.get(url) → HTML bytes
                                   → arquivo .html temporário
                                   → Docling.convert(arquivo.html)
                                   → arquivo temporário deletado
```

- `false + docling`: mais simples. O Docling faz o fetch e a conversão internamente. Recomendado para a maioria dos sites estáticos.
- `true + docling`: útil quando o site precisa de JS para montar o HTML (ex: tabelas carregadas via AJAX). O Playwright pré-renderiza, e o Docling converte o HTML resultante — preservando a estrutura semântica de tabelas e títulos mesmo em conteúdo dinâmico. **Qualidade pode variar dependendo da complexidade da SPA.**

#### Tabela resumo das 4 combinações

| `use_browser` | `metodo_extracao` | Quem faz o fetch | Quem converte | Ideal para |
|---|---|---|---|---|
| `false` | `html2text` | httpx | BeautifulSoup + html2text | Sites simples, texto corrido |
| `true` | `html2text` | Playwright | html2text | SPAs — conteúdo em texto |
| `false` | `docling` | Docling (interno) | Docling | HTML estático com tabelas/estrutura |
| `true` | `docling` | Playwright | Docling (via arquivo temp) | SPAs com tabelas/estrutura semântica |

> **Requisito de instalação:** `use_browser = true` exige `playwright` instalado e `playwright install chromium`. Sem isso, a execução falha com erro descritivo nos logs.

### 6.4. Fallback em Falha

- Se Docling lançar qualquer exceção, o comportamento é **idêntico ao atual**: `PaginaStatus.FALHOU`, log de erro registrado, execução continua nas URLs restantes.
- **Não há fallback automático** para html2text. Se o usuário quiser mudar de motor, deve editar a configuração.

### 6.5. Aviso de SPA no Frontend

- O aviso de limitação de SPA é informativo, **não bloqueia** a criação/edição da configuração com `metodo_extracao=DOCLING`.

---

## 7. Casos de Teste

### 7.1. Enum e Model

- ✅ `MetodoExtracao` possui valores `html2text` e `docling`
- ✅ `Configuracao` cria com `metodo_extracao=HTML2TEXT` por padrão
- ✅ `Configuracao` aceita `metodo_extracao=DOCLING`

### 7.2. Schema

- ✅ `ConfiguracaoCreate` deserializa `metodo_extracao` corretamente
- ✅ `ConfiguracaoCreate` sem `metodo_extracao` usa default `html2text`
- ✅ `ConfiguracaoResponse` serializa `metodo_extracao`
- ✅ `ConfiguracaoUpdate` aceita atualização de `metodo_extracao`

### 7.3. DoclingPageExtractor (unit tests)

- ✅ `extract()` retorna dict com `status="sucesso"`, `bytes > 0`, `title`, `path` ao mockar Docling
- ✅ `extract()` retorna `status="erro"` quando Docling lança exceção
- ✅ `extract_from_html()` cria arquivo temporário e chama `_converter.convert()`
- ✅ `_extract_title_from_markdown()` retorna string vazia se não houver `# h1`
- ✅ Frontmatter gerado contém `extrator: Toninho/Docling v1.0`

### 7.4. ExtractionOrchestrator

- ✅ `_extract_url()` instancia `PageExtractor` quando `metodo_extracao=HTML2TEXT`
- ✅ `_extract_url()` instancia `DoclingPageExtractor` quando `metodo_extracao=DOCLING`
- ✅ `_extract_url()` com `DOCLING + use_browser=True` chama `extract_from_html()`
- ✅ `_extract_url()` com `DOCLING + use_browser=False` chama `extract()` (URL direta)

### 7.5. Migration

- ✅ `upgrade()` adiciona coluna `metodo_extracao` com default `html2text`
- ✅ `downgrade()` remove coluna sem erros
- ✅ Registros existentes recebem `metodo_extracao = "html2text"` após upgrade

### 7.6. API / Integração

- ✅ `POST /api/v1/processos/{id}/configuracoes` com `metodo_extracao=docling` persiste corretamente
- ✅ `GET /api/v1/processos/{id}/configuracao` retorna `metodo_extracao` no response
- ✅ `PUT /api/v1/configuracoes/{id}` altera `metodo_extracao` de `html2text` para `docling`

---

## 8. Critérios de Aceite

- [ ] Usuário consegue criar/editar uma configuração de processo escolhendo `html2text` ou `docling`.
- [ ] Ao selecionar `docling` no formulário, o aviso de limitação de SPA é exibido.
- [ ] Execução com `metodo_extracao=docling` gera arquivo `.md` com Markdown semanticamente mais rico (tabelas formatadas, hierarquia de títulos preservada).
- [ ] Execução com `metodo_extracao=html2text` continua funcionando exatamente como antes.
- [ ] Falha do Docling em uma URL não interrompe a execução das demais URLs.
- [ ] Migration aplicada sem erros em banco existente; configurações antigas recebem `html2text`.
- [ ] Testes passam (`make test`).

---

## 9. Notas e Observações

### 9.1. Download de Modelos Docling

Na primeira execução, o Docling baixa modelos de deep learning (~300 MB no total) para `~/.cache/docling`. Este download ocorre **apenas uma vez**. Em ambientes Docker, garantir que o diretório de cache seja montado como volume persistente para evitar re-download a cada restart:

```yaml
# docker-compose.override.yml
services:
  worker:
    volumes:
      - docling_cache:/root/.cache/docling

volumes:
  docling_cache:
```

### 9.2. Performance

Docling é mais lento que html2text por URL (~2-10s vs ~0.1s), pois executa modelos de layout analysis. Para o volume atual (poucos documentos/dia, sem SLA de latência), isso é aceitável.

### 9.3. Docling e SPAs

Se no futuro for necessário suportar SPAs com Docling, o fluxo `use_browser=True + metodo_extracao=DOCLING` já está implementado: Playwright pré-renderiza o HTML, que é passado ao Docling via arquivo temporário.

### 9.4. Expansão Futura

Este PRD abre caminho para:
- Suporte a PDF/DOCX via Docling (novo `FormatoEntrada` na configuração).
- OCR de imagens embutidas em páginas.
- Comparação A/B automática de qualidade entre os dois motores.
