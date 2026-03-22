# PRD-ORG-007: Teste E2E Anti-Regressão de Formulários

**Status**: ✅ Implementado
**Prioridade**: 🔴 Alta
**Categoria**: Testes / Frontend
**Tipo**: Novo Teste

---

## 1. Objetivo

Criar teste E2E com Playwright que previna regressões em campos pré-preenchidos de formulários, especificamente o formulário de criação de processo que não carrega valores default na primeira navegação via HTMX.

## 2. Contexto e Justificativa

### Bug Reportado

Ao navegar para a página de criar processo pela primeira vez (via HTMX/sidebar), os campos do formulário não vêm pré-preenchidos com valores default. Após um reload manual da página (F5), os valores carregam corretamente.

**Causa provável**: O Alpine.js (`x-data`) depende de dados injetados pelo Jinja2. Quando o HTMX faz swap parcial de DOM, o Alpine pode não re-inicializar os bindings.

**Histórico**: Este bug já foi corrigido antes e **regrediu**, o que indica falta de cobertura de teste automatizado.

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: T1

---

## 3. Implementação

### 3.1. Arquivo a Criar

`tests/e2e/test_uc14_formulario_pre_preenchido.py`

(Seguindo a numeração dos UCs existentes: test_uc01 a test_uc13)

### 3.2. Cenários de Teste

#### Cenário 1: Navegação direta via URL
```python
async def test_criar_processo_campos_default_via_url(page):
    """Verifica que campos default estão presentes ao acessar via URL direta."""
    await page.goto("/processos/criar")  # ou path correto

    # Verificar que campos existem e têm valores default
    # (o agente deve verificar quais campos existem no template create.html)
```

#### Cenário 2: Navegação via HTMX (sidebar/link interno)
```python
async def test_criar_processo_campos_default_via_htmx(page):
    """Verifica que campos default estão presentes ao navegar via HTMX."""
    # Navegar primeiro para outra página (ex: lista de processos)
    await page.goto("/processos")

    # Clicar no botão/link de criar processo (via HTMX)
    await page.click("[data-testid='btn-criar-processo']")  # ou seletor correto

    # Aguardar HTMX completar o swap
    # Verificar que campos default estão preenchidos (mesmo resultado que URL direta)
```

#### Cenário 3: Campos mantêm valor após navegação ida-e-volta
```python
async def test_criar_processo_campos_persistem_navegacao(page):
    """Verifica que campos não perdem valores ao navegar ida e volta."""
    await page.goto("/processos/criar")
    # Verificar campos
    # Navegar para lista
    # Voltar para criar
    # Verificar campos novamente
```

### 3.3. Campos a Verificar

O agente deve ler `frontend/templates/pages/processos/create.html` para identificar:
1. Quais campos existem no formulário
2. Quais têm valores default (via `x-data`, `value=`, ou Jinja2)
3. Quais usam Alpine.js bindings (`x-model`, `x-bind`)

### 3.4. Padrão de Implementação

Seguir o padrão dos testes E2E existentes:
- Usar `async def test_...`
- Usar `expect()` do Playwright (auto-retry)
- Usar `page.wait_for_response()` para aguardar HTMX
- Usar markers: `@pytest.mark.e2e`
- Importar fixtures do `tests/e2e/conftest.py`

O agente deve ler `tests/e2e/conftest.py` e pelo menos 2 arquivos de teste E2E existentes (ex: `test_uc01_criar_processo.py`, `test_uc02_validacao_formulario.py`) para entender o padrão.

---

## 4. Critérios de Aceite

- [ ] Arquivo `tests/e2e/test_uc14_formulario_pre_preenchido.py` criado
- [ ] Cenário de navegação via URL direta passa
- [ ] Cenário de navegação via HTMX (sem reload) passa
- [ ] Teste usa padrão consistente com E2E existentes
- [ ] Teste marcado com `@pytest.mark.e2e`
- [ ] Teste roda com `make test-e2e` sem erros

---

## 5. Fontes de Informação

O agente deve ler:
- `frontend/templates/pages/processos/create.html` → campos do formulário
- `tests/e2e/conftest.py` → fixtures E2E
- `tests/e2e/test_uc01_criar_processo.py` → padrão de teste de criação
- `tests/e2e/test_uc02_validacao_formulario.py` → padrão de validação de formulário
- `toninho/api/routes/frontend.py` → rotas do frontend (paths corretos)
