# Discovery: Testes de Frontend com Playwright
**Projeto Toninho — Sistema de Extração de Documentos**
*Versão 1.0 · Março 2026*

---

## 1. Resumo do Projeto

O Toninho é um sistema que orquestra a extração de dados de sites. Ele recebe configurações de extração, dispara workers assíncronos via Celery e entrega os dados extraídos de forma estruturada. O frontend server-side (renderizado por Jinja2 / FastAPI) oferece a interface de controle para toda essa orquestração.

| Camada | Tecnologia | Função |
|---|---|---|
| Backend API | FastAPI + Pydantic | Endpoints REST, validação, lógica de negócio |
| Workers | Celery + Redis | Extração assíncrona e paralela de sites |
| Banco de dados | SQLite (dev) / PostgreSQL | Persistência de jobs e resultados |
| Frontend | HTMX + Alpine.js + Tailwind | UI reativa renderizada server-side (Jinja2) |
| Monitoramento | Flower | Acompanhamento das tasks Celery em tempo real |

---

## 2. Objetivo dos Testes de Frontend

O backend já possui cobertura de 90%+ com pytest. O gap atual está no frontend: alterações em templates Jinja2, atributos HTMX ou estado Alpine.js podem gerar comportamentos incorretos sem nenhum alarme automático.

Os testes de frontend têm três objetivos diretos:

- **Detectar regressões em templates** — quando uma mudança no Jinja2 quebra a renderização de um fragmento ou remove um atributo `hx-*` crítico.
- **Validar comportamento reativo** — garantir que Alpine.js e HTMX se comportam corretamente em resposta a interações do usuário (cliques, submissões, erros de rede).
- **Fechar o ciclo de qualidade** — hoje o pipeline bloqueia commits com falhas de lint, tipagem e cobertura de backend. Os testes de frontend estendem essa barreira para a camada de UI.

---

## 3. O que é o Playwright

Playwright é uma biblioteca open-source da Microsoft para automação de browsers. Ela controla Chromium, Firefox e WebKit de forma programática, executando ações reais num browser real (ou headless) e fazendo assertivas sobre o resultado.

> **Importante:** O Playwright não simula um browser — ele controla um browser de verdade. Isso significa que HTMX faz requests HTTP reais, Alpine.js executa com o motor V8 real e o Tailwind renderiza CSS real. Não há mocks de DOM como em jsdom.

### 3.1 Conceitos fundamentais

**Page**
Representa uma aba do browser. É o objeto central: você navega, interage e faz assertivas a partir dele.

**Locator**
A forma moderna de referenciar elementos. É lazy (não busca o elemento imediatamente), resiliente a mudanças de DOM e funciona bem com elementos que aparecem após requests HTMX.

```python
# aguarda o elemento aparecer após request HTMX
await expect(page.locator('.job-card')).to_have_count(3)
```

**expect() assíncrono**
Todas as assertivas do Playwright são auto-retry: se o elemento ainda não está lá, o Playwright aguarda (até o timeout configurado) antes de falhar. Isso elimina sleeps manuais e flakiness típicos de testes de UI.

**Network interception**
O Playwright pode interceptar, aguardar e inspecionar requests HTTP — essencial para validar que o HTMX está fazendo as chamadas corretas e recebendo as respostas esperadas.

---

## 4. Por que o Playwright se Encaixa no Projeto

| Característica do Toninho | Como o Playwright cobre |
|---|---|
| HTMX faz requests parciais e troca fragmentos de DOM | `waitForResponse()` aguarda a request completar; locators detectam o novo fragmento automaticamente |
| Alpine.js gerencia estado client-side | O Playwright roda no browser real — `x-data`, `x-show`, `x-bind` executam normalmente sem nenhum mock |
| Templates Jinja2 renderizados server-side | Testa o HTML final entregue ao browser, capturando erros de template que testes de backend não veem |
| pytest já é o runner do projeto | `pytest-playwright` é um plugin nativo — os testes E2E convivem na mesma estrutura `tests/` e no mesmo CI |
| `asyncio_mode = auto` já configurado | Testes `async def test_...` funcionam sem nenhuma configuração adicional |
| Workers Celery com jobs assíncronos | O Playwright pode aguardar atualizações de status em polling (ex: job card mudando de "Processando" para "Concluído") |

A alternativa mais citada, Cypress, teria a mesma capacidade técnica mas introduz uma segunda linguagem (JavaScript obrigatório) e um segundo ecossistema de dependências num projeto 100% Python. O Playwright mantém tudo em Python.

---

## 5. Estratégia de Testes

A estratégia é organizada em duas camadas complementares. A divisão é por velocidade e por tipo de feedback — não por ferramenta.

### 5.1 Camada 2 — E2E com Playwright (com browser)

Testes organizados por **caso de uso**, não por página ou componente. Cada teste representa um fluxo completo que um usuário real executaria.

> **Critério para ir para E2E:** se o comportamento depende de JavaScript executando no browser (Alpine.js ou HTMX), ou se envolve múltiplas requests encadeadas, vai para E2E. Se é só HTML + dados, vai para Integration.

#### Casos de uso mapeados para o Toninho

[CONSTRUIR]

#### Estrutura de arquivos proposta

```
tests/
├── unit/                    # existente — sem alterações
├── integration/
│   ├── test_api.py          # existente
│   └── test_templates.py    # novo — validação de HTML/HTMX
└── e2e/
    ├── conftest.py          # fixture: live_server, page, context
    ├── test_uc01_criar_job.py
    ├── test_uc02_formulario.py
    ├── test_uc03_filtro.py
    ├── test_uc04_cancelar_job.py
    └── test_uc05_erro_rede.py
```

---

## 6. Integração no Pipeline Existente

Nenhuma decisão do ADR-007 precisa ser alterada. O Playwright se encaixa como extensão, não como substituição.

| Onde | O que muda |
|---|---|
| `pyproject.toml` | Adicionar `pytest-playwright` e `playwright` como dev deps; excluir `tests/e2e/` do `--cov-fail-under` |
| pytest markers | Marcar testes E2E com `@pytest.mark.e2e` para rodar separado do `make test` |
| Makefile | Adicionar `make test-e2e` sem alterar o `make test` ou `make quality` existentes |
| GitHub Actions | Adicionar job `test-e2e` paralelo ao job `test`; não bloqueia a cobertura de 90% |
| Pre-commit hooks | Sem alterações — E2E não roda no pre-commit (seria lento demais) |

```toml
# pyproject.toml — adições
[tool.pytest.ini_options]
markers = ["e2e: testes que requerem browser Playwright"]

[tool.coverage.run]
omit = ["tests/e2e/*"]  # E2E não entra no cov-fail-under=90
```

```makefile
# Makefile — novo target
test-e2e:
    poetry run pytest tests/e2e/ -m e2e --browser chromium

# DEVEMOS ter o Modo visivel tambem
```

---

## 7. Workflow com IA na Geração de Testes

O Playwright foi projetado pensando em geração automatizada, o que o torna a escolha ideal quando a IA vai ajudar a escrever os testes.

### 7.1 playwright codegen — ponto de partida

O comando `codegen` abre o browser e grava cada ação do usuário, gerando o código de teste automaticamente:

```bash
playwright codegen http://localhost:8000
# abre o browser + editor side-by-side
# cada clique/digitação vira código pytest em tempo real
```

O código gerado serve como rascunho. A IA então refina: adiciona assertivas de negócio, trata timing de HTMX e organiza por caso de uso.

### 7.2 Fluxo recomendado

1. Gravar o fluxo com `playwright codegen` (5 min por UC)
2. Passar o código gravado + template Jinja2 para a IA refinar
3. IA adiciona: assertivas de negócio, `waitForResponse` para HTMX, casos de borda
4. Revisão humana: validar seletores e comportamento esperado
5. Commit — CI roda os testes no job `test-e2e`

---

## 8. Dependências a Adicionar

| Pacote | Grupo | Motivo |
|---|---|---|
| `playwright` | dev | Biblioteca principal — controla o browser |
| `pytest-playwright` | dev | Plugin pytest — fixtures `page`, `browser`, `context` |
| Chromium (binário) | CI/dev | `playwright install chromium --with-deps` |

> Nenhuma dependência de produção é adicionada. Playwright é 100% dev/test.

---

## 9. Próximos Passos

Com base neste discovery, os próximos artefatos a produzir são:

- **PRD-FE-01** — Setup de infraestrutura Playwright (`conftest.py`, fixture `live_server`, `pyproject.toml`)
- **PRD-FE-02** — Implementação UC-01: Criar e acompanhar job de extração
- **PRD-FE-03** — Implementação UC-02 a UC-05 (formulários, filtros, cancelamento, erros)
- **PRD-FE-04** — Testes de Integration para templates Jinja2 e fragmentos HTMX
- **PRD-FE-05** — Integração CI/CD: job `test-e2e` no GitHub Actions

> **Recomendação de ordem:** começar pelo PRD-FE-01 (infra) antes de qualquer UC. Um `conftest.py` bem estruturado evita retrabalho em todos os testes seguintes.
