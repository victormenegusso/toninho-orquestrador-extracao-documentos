# Explicação do que foi feito e ganhos obtidos

> Documento que detalha cada arquivo criado na preparação de suporte a agentes de IA (GitHub Copilot, Copilot Workspace, Copilot Coding Agent), explicando **o que é**, **por que foi criado**, **o que contém** e **exemplos concretos de ganho prático** (antes vs depois).

---

## Sumário

1. [`.github/copilot-instructions.md`](#githubcopilot-instructionsmd)
2. [`.github/workflows/copilot-setup-steps.yml`](#githubworkflowscopilot-setup-stepsyml)
3. [`.github/instructions/python-tests.instructions.md`](#githubinstructionspython-testsinstructionsmd)
4. [`.github/instructions/api-routes.instructions.md`](#githubinstructionsapi-routesinstructionsmd)
5. [`.github/instructions/models-schemas.instructions.md`](#githubinstructionsmodels-schemasinstructionsmd)
6. [`.github/instructions/e2e-tests.instructions.md`](#githubinstructionse2e-testsinstructionsmd)
7. [`AGENTS.md`](#agentsmd)
8. [`CONTRIBUTING.md`](#contributingmd)
9. [`SECURITY.md`](#securitymd)
10. [`.github/CODEOWNERS`](#githubcodeowners)
11. [`.vscode/extensions.json`](#vscodeextensionsjson)
12. [`.vscode/settings.json`](#vscodesettingsjson)

---

## `.github/copilot-instructions.md`

**O que é:** Arquivo de instruções globais do GitHub Copilot para o repositório. É lido automaticamente pelo Copilot (Chat, Inline, Coding Agent) em todas as interações dentro deste projeto.

**Por que foi criado:** Sem esse arquivo, o Copilot não tem nenhum contexto sobre a arquitetura, stack tecnológica, convenções de código ou padrões do projeto. Ele gera código "genérico" que frequentemente não se encaixa no estilo e nas decisões arquiteturais do Toninho. A [documentação oficial do GitHub](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-instructions-for-github-copilot) recomenda este arquivo como ponto central de contexto.

**O que contém:**
- Visão geral do projeto (orquestrador de extração de documentos)
- Stack tecnológica completa (FastAPI, SQLAlchemy 2.x, Celery, Playwright, HTMX, Alpine.js, TailwindCSS)
- Tabela de arquitetura com todos os caminhos (Routes → Dependencies → Services → Repositories → Models → Schemas → Extraction → Workers → Monitoring → Core → Frontend → Tests → Migrations)
- Padrões de código (configuração do Ruff, regras de lint, mypy, bandit, conventional commits)
- Convenções de nomenclatura (nomes de domínio em português, termos técnicos em inglês)
- Padrões-chave do projeto (`Depends()`, Pydantic v2, exceções customizadas, pydantic-settings, Celery tasks, asyncio_mode auto)
- Tabela de comandos essenciais do Makefile
- Descrição do CI/CD

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** Ao pedir ao Copilot para criar um novo endpoint, ele gerava código usando formatação do Black (ao invés do Ruff), não sabia que os nomes de tabelas e campos são em português (criava `document_status` ao invés de `status_documento`), e não seguia o padrão de injeção de dependência com `Depends()`. Também não conhecia a estrutura de diretórios, colocando arquivos em locais errados.
- **Depois (com o arquivo):** O Copilot já sabe que o projeto usa Ruff para formatação, que nomes de domínio são em português, que deve usar `Depends()` para injeção de dependência, e conhece toda a estrutura de diretórios. Ao pedir "crie um endpoint para listar tipos de documento", ele gera código que já segue o padrão correto do projeto: rota em `toninho/api/routes/`, schema em `toninho/schemas/`, com nomenclatura em português.

---

## `.github/workflows/copilot-setup-steps.yml`

**O que é:** Workflow do GitHub Actions que define os passos de setup do ambiente para o Copilot Coding Agent. É executado automaticamente antes de qualquer tarefa do agente.

**Por que foi criado:** O Copilot Coding Agent (que trabalha em pull requests e issues) precisa de um ambiente funcional para executar código, rodar testes e validar mudanças. Sem este workflow, o agente gasta tempo tentando descobrir como instalar dependências por tentativa e erro, frequentemente falhando em projetos com setups não triviais como o nosso (Poetry + Playwright).

**O que contém:**
- Trigger `workflow_dispatch` para uso pelo agente
- Job `copilot-setup-steps` rodando em `ubuntu-latest`
- Steps: checkout do código, setup do Python 3.11, instalação do Poetry, configuração do virtualenv in-project, cache de dependências, `poetry install`, `playwright install chromium`

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** O Copilot Coding Agent recebia uma issue como "adicione testes E2E para a tela de login" e, na sua primeira tentativa, falhava ao rodar `pip install -r requirements.txt` (que não existe, usamos Poetry). Depois tentava `poetry install` mas sem o Python 3.11 configurado. Quando finalmente instalava as dependências Python, os testes E2E falhavam porque o Playwright/Chromium não estava instalado. Resultado: múltiplas iterações desperdiçadas antes mesmo de começar a tarefa real.
- **Depois (com o arquivo):** O ambiente já está pronto antes do agente começar a trabalhar. Python 3.11, Poetry, todas as dependências do projeto e o Chromium para testes E2E já estão instalados. O agente vai direto para a tarefa: escrever código, rodar `make test` e validar. Economia de tempo significativa e menos falhas.

---

## `.github/instructions/python-tests.instructions.md`

**O que é:** Instrução contextual do Copilot aplicada automaticamente quando o usuário está editando ou criando arquivos em `**/tests/**/*.py`. Funciona como um guia especializado para escrita de testes.

**Por que foi criado:** Testes têm convenções muito específicas neste projeto (markers customizados, asyncio_mode auto, fixtures compartilhadas, termos de domínio em português). Sem instruções específicas, o Copilot gera testes que não seguem os padrões do projeto e precisam de refatoração manual. O recurso de `applyTo` permite que essas instruções sejam carregadas apenas quando relevante, não poluindo o contexto em outros cenários.

**O que contém:**
- Escopo de aplicação: `**/tests/**/*.py`
- Convenções do pytest (asyncio_mode auto, sem necessidade de decorator `@pytest.mark.asyncio`)
- Markers disponíveis: `unit`, `integration`, `e2e`, `slow`, `requires_redis`, `requires_celery`
- Meta de cobertura: 75%
- Ferramentas de mock: `pytest-mock` + `respx` para HTTP
- Tabela de convenções de nomenclatura de testes
- Uso de fixtures de `tests/fixtures/`
- Termos de domínio em português nos nomes de teste

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** Ao pedir "crie testes para o serviço de extração", o Copilot gerava:
  ```python
  @pytest.mark.asyncio  # desnecessário, asyncio_mode=auto
  async def test_extract_document():
      mock_response = MagicMock()  # não usa pytest-mock
      # sem markers, sem fixtures do projeto
  ```
  Os testes não usavam os markers corretos, adicionavam decorators desnecessários (`@pytest.mark.asyncio` quando já temos `asyncio_mode = auto`), não referenciavam fixtures existentes e usavam `MagicMock` diretamente ao invés de `pytest-mock`.

- **Depois (com o arquivo):** O Copilot gera:
  ```python
  @pytest.mark.unit
  async def test_deve_extrair_documento_com_sucesso(mocker, documento_fixture):
      mock_extractor = mocker.patch("toninho.services.extracao.ExtratorService.extrair")
      # usa fixture do projeto, marker correto, nomenclatura em português
  ```
  Testes seguem todas as convenções do projeto desde a primeira geração.

---

## `.github/instructions/api-routes.instructions.md`

**O que é:** Instrução contextual do Copilot aplicada automaticamente ao editar arquivos em `**/api/routes/*.py` e `**/api/dependencies/*.py`.

**Por que foi criado:** As rotas da API seguem um padrão rígido de arquitetura em camadas, injeção de dependência e tratamento de erros que é muito específico do projeto. Sem essa instrução, o Copilot gera endpoints que violam a separação de responsabilidades (por exemplo, acessando o banco de dados diretamente na rota).

**O que contém:**
- Escopo: `**/api/routes/*.py,**/api/dependencies/*.py`
- Padrão de injeção de dependência com `Depends()`
- Uso de Pydantic schemas para request/response
- Formato padrão de resposta da API
- Exceções customizadas do projeto
- Convenções REST sob `/api/v1/`
- Códigos HTTP corretos para cada operação
- Regra: nunca acessar banco de dados diretamente nas rotas
- Metadata OpenAPI nos endpoints

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** O Copilot gerava rotas como:
  ```python
  @router.get("/documents")
  async def get_documents(db: Session = Depends(get_db)):
      documents = db.query(Documento).all()  # acesso direto ao DB na rota!
      return documents  # sem schema de resposta padronizado
  ```
  Violava a arquitetura em camadas, não usava o service layer, não seguia o formato de resposta padrão e não incluía metadata OpenAPI.

- **Depois (com o arquivo):** O Copilot gera:
  ```python
  @router.get("/documentos", response_model=DocumentoListResponse,
              summary="Lista documentos", tags=["documentos"])
  async def listar_documentos(
      service: DocumentoService = Depends(get_documento_service),
  ) -> DocumentoListResponse:
      return await service.listar_todos()
  ```
  Usa o service layer, schemas de resposta, metadata OpenAPI e nomenclatura correta.

---

## `.github/instructions/models-schemas.instructions.md`

**O que é:** Instrução contextual do Copilot para criação e edição de models SQLAlchemy e schemas Pydantic, aplicada automaticamente em `**/models/*.py` e `**/schemas/*.py`.

**Por que foi criado:** Models e schemas têm padrões muito específicos no projeto: SQLAlchemy 2.x com mapeamento declarativo, Pydantic v2 com `ConfigDict`, separação de schemas por operação (Create, Update, Response, List), enums centralizados, nomes em português. Esses padrões são difíceis de inferir sem contexto explícito.

**O que contém:**
- Escopo: `**/models/*.py,**/schemas/*.py`
- SQLAlchemy 2.x com `DeclarativeBase` e `Mapped[]`
- Tipos de coluna e relacionamentos
- Enums centralizados em `enums.py`
- Nomes de tabelas e colunas em português
- Exemplo de código de model
- Pydantic v2 com `ConfigDict(from_attributes=True)`
- Separação de schemas: Create, Update, Response, List
- Validators em `validators.py`
- Uso de `Field()` para validação
- Nomes de campos em português
- Exemplo de código de schema

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** O Copilot gerava models no estilo antigo do SQLAlchemy:
  ```python
  class Document(Base):  # nome em inglês
      __tablename__ = "documents"
      id = Column(Integer, primary_key=True)  # estilo SQLAlchemy 1.x
      status = Column(String)  # sem enum centralizado

  class DocumentSchema(BaseModel):  # Pydantic v1 style
      class Config:
          orm_mode = True  # deprecated no Pydantic v2
  ```

- **Depois (com o arquivo):** O Copilot gera:
  ```python
  class Documento(Base):
      __tablename__ = "documentos"
      id: Mapped[int] = mapped_column(primary_key=True)  # SQLAlchemy 2.x
      status: Mapped[StatusDocumento] = mapped_column(default=StatusDocumento.PENDENTE)

  class DocumentoResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)  # Pydantic v2
      id: int
      status: StatusDocumento
  ```
  Usa a sintaxe correta do SQLAlchemy 2.x, Pydantic v2, enums centralizados e nomenclatura em português.

---

## `.github/instructions/e2e-tests.instructions.md`

**O que é:** Instrução contextual do Copilot para testes end-to-end, aplicada automaticamente em `**/tests/e2e/**/*.py`.

**Por que foi criado:** Testes E2E com Playwright têm padrões específicos que diferem muito de testes unitários. O projeto usa HTMX + Alpine.js no frontend, o que exige uma abordagem diferente para localizar e interagir com elementos. Sem instruções específicas, o Copilot gera testes E2E frágeis com seletores CSS ruins e `time.sleep()`.

**O que contém:**
- Escopo: `**/tests/e2e/**/*.py`
- Uso do pytest-playwright
- Modos headless/headed
- Locators estáveis: `get_by_role`, `get_by_text`, `get_by_test_id`, `locator`
- Caminhos relativos com base URL
- Auto-wait (nunca usar `time.sleep()`)
- Assertions com `expect` API
- Tratamento de conteúdo dinâmico HTMX + Alpine.js
- Padrão de nomenclatura
- Isolamento e limpeza de testes

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** O Copilot gerava testes E2E como:
  ```python
  def test_login(page):
      page.goto("http://localhost:8000/login")  # URL hardcoded
      page.click("#login-btn")  # seletor CSS frágil
      time.sleep(3)  # espera fixa, anti-pattern
      assert page.query_selector(".success")  # assertion frágil
  ```
  Usava URLs hardcoded, seletores CSS frágeis, `time.sleep()` e assertions que não aproveitam o auto-wait do Playwright.

- **Depois (com o arquivo):** O Copilot gera:
  ```python
  @pytest.mark.e2e
  def test_deve_realizar_login_com_sucesso(page):
      page.goto("/login")  # caminho relativo com base URL
      page.get_by_role("button", name="Entrar").click()  # locator estável
      expect(page.get_by_text("Login realizado")).to_be_visible()  # auto-wait
  ```
  Usa caminhos relativos, locators semânticos, auto-wait do Playwright e assertions robustas.

---

## `AGENTS.md`

**O que é:** Arquivo de instruções para agentes de IA autônomos (Copilot Coding Agent, Claude Code, Cursor, etc.). É lido automaticamente por diversos agentes quando trabalham no repositório.

**Por que foi criado:** O `AGENTS.md` é o equivalente do `copilot-instructions.md` para agentes que operam de forma autônoma (sem interação com o desenvolvedor). Enquanto o `copilot-instructions.md` guia o Copilot Chat/Inline, o `AGENTS.md` guia agentes que recebem uma issue e precisam implementar a solução sozinhos. Ele precisa ser mais direto e conter anti-patterns explícitos para evitar erros comuns.

**O que contém:**
- Visão geral do projeto
- Lista da stack tecnológica
- Tabela de comandos essenciais (lint, test, format, etc.)
- Diagrama de arquitetura (Routes → Services → Repositories → Models) com todos os paths
- Convenções de código
- Anti-patterns a evitar (6 itens explícitos):
  1. Não acessar DB diretamente nas rotas
  2. Não importar de `api` nos services
  3. Não usar `time.sleep()` em testes
  4. Não fazer hardcode de configurações
  5. Não criar tasks Celery fora de `workers/tasks`
  6. Não alterar models sem criar migration
- Links para documentação

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** Um agente autônomo recebendo a issue "adicione campo 'prioridade' ao modelo de documento" poderia: alterar o model sem criar a migration Alembic, acessar o banco diretamente na rota para testar, usar `time.sleep()` em um teste de integração, e criar uma task Celery em um arquivo qualquer. Cada um desses erros geraria uma iteração extra de correção.

- **Depois (com o arquivo):** O agente lê o `AGENTS.md` e sabe que deve: alterar o model em `toninho/models/`, criar a migration com `make migration`, criar/atualizar o schema, implementar via service layer, e colocar qualquer task em `toninho/workers/tasks/`. A lista explícita de anti-patterns funciona como guardrails que previnem erros comuns antes que aconteçam.

---

## `CONTRIBUTING.md`

**O que é:** Guia de contribuição do projeto, escrito em português, que documenta o fluxo de trabalho para novos contribuidores (humanos e agentes de IA).

**Por que foi criado:** Além de ser uma boa prática para qualquer projeto open-source ou de equipe, o `CONTRIBUTING.md` é lido por agentes de IA como contexto adicional sobre o fluxo de trabalho esperado. Ele documenta o processo de setup, branch naming, commits convencionais e checklist de qualidade.

**O que contém:**
- Pré-requisitos do ambiente
- Setup do ambiente em 5 passos
- Fluxo de contribuição em 6 passos com convenção de nomes de branch
- Conventional commits (formato e exemplos)
- Checklist de qualidade (6 itens)
- Estrutura do projeto (camadas + testes)
- Práticas de code review

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** Um novo contribuidor (ou agente) não sabia que o projeto usa conventional commits, criava branches com nomes inconsistentes (ex: `fix-bug-123` ao invés de `fix/corrigir-bug-extracao`), e não rodava o checklist de qualidade antes de abrir o PR.

- **Depois (com o arquivo):** O fluxo está documentado. Commits seguem o padrão `feat:`, `fix:`, `docs:`, etc. Branches seguem a convenção `feat/`, `fix/`, `docs/`. E o checklist de qualidade (`make lint`, `make test`, `make format`) é aplicado antes de cada PR. Agentes autônomos também seguem esse fluxo ao criar PRs.

---

## `SECURITY.md`

**O que é:** Política de segurança do projeto que documenta como reportar vulnerabilidades, quais ferramentas de segurança são usadas e quais práticas de segurança são seguidas.

**Por que foi criado:** Além de ser uma boa prática de segurança, este arquivo informa agentes de IA sobre as ferramentas e práticas de segurança do projeto. Isso evita que agentes introduzam código inseguro ou ignorem verificações de segurança existentes.

**O que contém:**
- Processo de reporte de vulnerabilidades
- Tabela de ferramentas de segurança (Bandit, pip-audit, pre-commit hooks)
- Práticas de segurança: sem secrets no código, auditoria de dependências, análise estática, pre-commit, enforcement no CI
- Versões suportadas
- Nota sobre dependências

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** O Copilot podia gerar código que incluía strings de conexão hardcoded, não sabia que o projeto usa Bandit para análise estática de segurança, e não alertava sobre práticas inseguras.

- **Depois (com o arquivo):** O Copilot e agentes autônomos sabem que o projeto usa Bandit e pip-audit, que secrets nunca devem estar no código (usar variáveis de ambiente via pydantic-settings), e que há pre-commit hooks que vão rejeitar código inseguro. Isso influencia a geração de código a usar `settings.DATABASE_URL` ao invés de hardcodar a connection string.

---

## `.github/CODEOWNERS`

**O que é:** Arquivo que define os responsáveis (owners) por cada parte do código. O GitHub usa esse arquivo para automaticamente solicitar reviews dos owners corretos em pull requests.

**Por que foi criado:** Garante que todo PR tenha pelo menos um reviewer qualificado. Em projetos onde agentes de IA criam PRs automaticamente, o CODEOWNERS é essencial para garantir que um humano revise as mudanças antes do merge.

**O que contém:**
- Owner padrão: `@menegusso` para todo o repositório
- Paths específicos com owners para: backend core, extração, workers, frontend, testes, infraestrutura (Dockerfile, docker-compose), documentação

**Exemplo de ganho prático:**

- **Antes (sem o arquivo):** Quando o Copilot Coding Agent criava um PR, não havia atribuição automática de reviewer. O PR ficava sem review até alguém perceber manualmente. Em projetos de equipe, mudanças em áreas críticas (como extração ou workers) podiam ser mergeadas sem review do especialista.

- **Depois (com o arquivo):** Todo PR criado (por humano ou agente) automaticamente solicita review de `@menegusso`. Em equipes maiores, cada área pode ter seu especialista designado. Isso cria uma camada de governança humana sobre as mudanças feitas por agentes de IA.

---

## `.vscode/extensions.json`

**O que é:** Arquivo de recomendações de extensões do VS Code para o projeto.

**Por que foi criado:** Atualizado para refletir a migração do Black para Ruff como formatter e para recomendar as extensões do GitHub Copilot a todos os contribuidores.

**O que mudou:**
- Removido: `ms-python.black-formatter` (não usamos mais Black)
- Adicionado: `github.copilot` e `github.copilot-chat`

**Exemplo de ganho prático:**

- **Antes (sem a mudança):** Um novo contribuidor abria o projeto no VS Code e recebia a recomendação de instalar o Black formatter, que conflitava com o Ruff. Também não recebia recomendação para instalar o Copilot.

- **Depois (com a mudança):** O VS Code recomenda as extensões corretas: Ruff para formatação e Copilot para assistência de IA. Não há mais conflito entre formatadores, e novos contribuidores já começam com o Copilot instalado para aproveitar todas as instruções contextuais do projeto.

---

## `.vscode/settings.json`

**O que é:** Configurações do VS Code específicas do projeto, compartilhadas entre todos os contribuidores via repositório.

**Por que foi criado:** Atualizado para completar a migração do Black para Ruff como formatter Python, garantindo consistência entre as configurações do editor e as ferramentas de CI.

**O que mudou:**
- `python.formatting.provider`: de `"black"` para `"none"` (Ruff usa sua própria extensão)
- `[python].editor.defaultFormatter`: de `"ms-python.black-formatter"` para `"charliermarsh.ruff"`

**Exemplo de ganho prático:**

- **Antes (sem a mudança):** Ao salvar um arquivo Python, o VS Code formatava com Black, que tem regras diferentes do Ruff. Isso causava conflitos: o CI rodava Ruff e falhava, ou o desenvolvedor via diferenças de formatação no `git diff` que não eram mudanças reais de código.

- **Depois (com a mudança):** O VS Code formata com Ruff ao salvar, que é o mesmo formatter do CI. Zero conflitos de formatação, `git diff` limpo, e o código está sempre no formato correto antes mesmo do commit.

---

## Resumo dos ganhos

| Categoria | Arquivo(s) | Ganho principal |
|-----------|-----------|-----------------|
| **Contexto global** | `copilot-instructions.md`, `AGENTS.md` | Copilot e agentes entendem a arquitetura, stack e convenções do projeto |
| **Setup automatizado** | `copilot-setup-steps.yml` | Agente autônomo tem ambiente funcional sem tentativa e erro |
| **Instruções por contexto** | `python-tests`, `api-routes`, `models-schemas`, `e2e-tests` | Código gerado segue os padrões específicos de cada camada |
| **Governança** | `CODEOWNERS` | Todo PR de agente passa por review humano |
| **Onboarding** | `CONTRIBUTING.md`, `SECURITY.md` | Fluxo de contribuição e segurança documentados |
| **Tooling** | `extensions.json`, `settings.json` | Editor configurado corretamente para Ruff + Copilot |

Esses arquivos, em conjunto, transformam o repositório de um projeto "opaco" para agentes de IA em um projeto **auto-documentado e otimizado para assistência de IA**, onde cada interação com o Copilot gera código mais próximo do padrão desejado desde a primeira sugestão.
