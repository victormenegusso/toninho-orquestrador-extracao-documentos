# PRD-015: Interface CRUD Processos

**Status**: ✅ Concluído  
**Prioridade**: 🟢 Baixa - Frontend (Prioridade 4)  
**Categoria**: Frontend - Features  
**Estimativa**: 8-10 horas

---

## 1. Objetivo

Implementar interface completa de CRUD (Create, Read, Update, Delete) para Processos. Inclui listagem com filtros e paginação, formulário de criação/edição com validação, detalhes do processo, gerenciamento de configurações e ações de controle (executar, agendar).

## 2. Contexto e Justificativa

A interface de Processos é o ponto central do Toninho. Usuário deve poder:
- **Listar** processos existentes com busca/filtros
- **Criar** novo processo com configurações
- **Editar** processo e suas configurações
- **Deletar** processo (com confirmação)
- **Executar** processo manualmente
- **Ver detalhes** incluindo histórico de execuções

**Tecnologias:**
- HTMX para interações (search, pagination, delete)
- Alpine.js para modals e confirmações
- Tailwind para estilização

## 3. Requisitos Técnicos

### 3.1. Páginas e Rotas

**Frontend Routes (toninho/api/frontend.py):**
```python
@router.get("/processos", response_class=HTMLResponse)
async def processos_list(request: Request):
    """Lista de processos"""

@router.get("/processos/novo", response_class=HTMLResponse)
async def processos_create(request: Request):
    """Formulário de criação"""

@router.get("/processos/{id}", response_class=HTMLResponse)
async def processos_detail(request: Request, id: UUID):
    """Detalhes do processo"""

@router.get("/processos/{id}/editar", response_class=HTMLResponse)
async def processos_edit(request: Request, id: UUID):
    """Formulário de edição"""

# Partials para HTMX
@router.get("/processos/search", response_class=HTMLResponse)
async def processos_search(request: Request, q: str):
    """Busca processos (partial)"""
```

### 3.2. Lista de Processos (frontend/templates/pages/processos/list.html)

```html
{% extends "layouts/dashboard.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">Processos</h1>
            <p class="text-gray-600 mt-1">Gerencie seus processos de extração</p>
        </div>
        <a href="{{ url_for('processos_create') }}" class="btn-primary">
            <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Novo Processo
        </a>
    </div>

    <!-- Filters & Search -->
    <div class="card">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Search -->
            <div class="md:col-span-2">
                <label class="form-label">Buscar</label>
                <input 
                    type="text" 
                    name="search"
                    class="form-input"
                    placeholder="Nome ou descrição..."
                    hx-get="{{ url_for('processos_search') }}"
                    hx-trigger="keyup changed delay:500ms"
                    hx-target="#processos-table"
                    hx-indicator="#search-indicator">
                <span id="search-indicator" class="htmx-indicator">
                    <svg class="animate-spin h-4 w-4 inline ml-2" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </span>
            </div>

            <!-- Status Filter -->
            <div>
                <label class="form-label">Status</label>
                <select 
                    name="status" 
                    class="form-input"
                    hx-get="{{ url_for('processos_list') }}"
                    hx-target="#processos-table"
                    hx-include="[name='search']">
                    <option value="">Todos</option>
                    <option value="ATIVO">Ativo</option>
                    <option value="INATIVO">Inativo</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden p-0">
        <div id="processos-table">
            {% include 'partials/processos_table.html' %}
        </div>
    </div>
</div>
{% endblock %}
```

### 3.3. Table Partial (frontend/templates/partials/processos_table.html)

```html
<table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
        <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Nome
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agendamento
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Última Execução
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
            </th>
        </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
        {% for processo in processos.items %}
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4">
                <div>
                    <a href="{{ url_for('processos_detail', id=processo.id) }}" 
                       class="text-blue-600 hover:text-blue-800 font-medium">
                        {{ processo.nome }}
                    </a>
                    <p class="text-sm text-gray-500">{{ processo.descricao[:60] }}...</p>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                {% if processo.status == 'ATIVO' %}
                <span class="badge-success">Ativo</span>
                {% else %}
                <span class="badge-danger">Inativo</span>
                {% endif %}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {% if processo.agendamento %}
                <span class="badge-info">{{ processo.agendamento }}</span>
                {% else %}
                <span class="text-gray-400">-</span>
                {% endif %}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {% if processo.ultima_execucao %}
                {{ processo.ultima_execucao.strftime('%d/%m/%Y %H:%M') }}
                {% else %}
                <span class="text-gray-400">Nunca executado</span>
                {% endif %}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <!-- Executar -->
                <button 
                    hx-post="{{ url_for('api_executar_processo', id=processo.id) }}"
                    hx-confirm="Executar processo agora?"
                    class="text-green-600 hover:text-green-900"
                    title="Executar">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </button>

                <!-- Editar -->
                <a href="{{ url_for('processos_edit', id=processo.id) }}" 
                   class="text-blue-600 hover:text-blue-900"
                   title="Editar">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                </a>

                <!-- Deletar -->
                <button
                    hx-delete="{{ url_for('api_deletar_processo', id=processo.id) }}"
                    hx-confirm="Tem certeza que deseja deletar este processo? Esta ação não pode ser desfeita."
                    hx-target="closest tr"
                    hx-swap="outerHTML swap:1s"
                    class="text-red-600 hover:text-red-900"
                    title="Deletar">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </button>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Pagination -->
{% if processos.pages > 1 %}
<div class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
    {% include 'components/pagination.html' %}
</div>
{% endif %}
```

### 3.4. Form Create/Edit (frontend/templates/pages/processos/create.html)

```html
{% extends "layouts/dashboard.html" %}

{% block content %}
<div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-2xl font-bold text-gray-900">
            {% if processo %}Editar Processo{% else %}Novo Processo{% endif %}
        </h1>
        <p class="text-gray-600 mt-1">Preencha as informações abaixo</p>
    </div>

    <!-- Form -->
    <form 
        class="space-y-6"
        hx-post="{% if processo %}{{ url_for('api_update_processo', id=processo.id) }}{% else %}{{ url_for('api_create_processo') }}{% endif %}"
        hx-target="#form-container"
        hx-swap="outerHTML">
        
        <div id="form-container">
            <!-- Informações Básicas -->
            <div class="card space-y-4">
                <h2 class="text-lg font-semibold">Informações Básicas</h2>

                <!-- Nome -->
                <div>
                    <label for="nome" class="form-label">Nome *</label>
                    <input 
                        type="text" 
                        id="nome" 
                        name="nome" 
                        class="form-input"
                        value="{{ processo.nome if processo else '' }}"
                        required>
                    {% if errors.nome %}
                    <p class="form-error">{{ errors.nome }}</p>
                    {% endif %}
                </div>

                <!-- Descrição -->
                <div>
                    <label for="descricao" class="form-label">Descrição</label>
                    <textarea 
                        id="descricao" 
                        name="descricao" 
                        rows="3"
                        class="form-input">{{ processo.descricao if processo else '' }}</textarea>
                </div>

                <!-- Status -->
                <div>
                    <label for="status" class="form-label">Status *</label>
                    <select id="status" name="status" class="form-input" required>
                        <option value="ATIVO" {% if processo and processo.status == 'ATIVO' %}selected{% endif %}>
                            Ativo
                        </option>
                        <option value="INATIVO" {% if processo and processo.status == 'INATIVO' %}selected{% endif %}>
                            Inativo
                        </option>
                    </select>
                </div>
            </div>

            <!-- Configuração de Extração -->
            <div class="card space-y-4">
                <h2 class="text-lg font-semibold">Configuração de Extração</h2>

                <!-- URLs -->
                <div>
                    <label for="urls" class="form-label">URLs *</label>
                    <p class="text-sm text-gray-600 mb-2">Uma URL por linha (mínimo 1, máximo 100)</p>
                    <textarea 
                        id="urls" 
                        name="urls" 
                        rows="6"
                        class="form-input font-mono text-sm"
                        placeholder="https://example.com/page1&#10;https://example.com/page2"
                        required>{% if processo and processo.configuracao %}{{ processo.configuracao.urls|join('\n') }}{% endif %}</textarea>
                    <p class="text-sm text-gray-500 mt-1">
                        <span id="url-count">0</span> URLs
                    </p>
                    {% if errors.urls %}
                    <p class="form-error">{{ errors.urls }}</p>
                    {% endif %}
                </div>

                <!-- Tipo de Extração -->
                <div>
                    <label for="tipo_extracao" class="form-label">Tipo de Extração</label>
                    <select id="tipo_extracao" name="tipo_extracao" class="form-input">
                        <option value="SIMPLES">Simples (HTML parsing)</option>
                        <option value="HEADLESS">Headless Browser (sites JS)</option>
                    </select>
                </div>

                <!-- Timeout -->
                <div>
                    <label for="timeout" class="form-label">Timeout (segundos)</label>
                    <input 
                        type="number" 
                        id="timeout" 
                        name="timeout" 
                        class="form-input"
                        value="{{ processo.configuracao.timeout if processo and processo.configuracao else 30 }}"
                        min="10"
                        max="300">
                </div>
            </div>

            <!-- Agendamento -->
            <div class="card space-y-4" x-data="{ hasSchedule: {{ 'true' if processo and processo.agendamento else 'false' }} }">
                <div class="flex items-center justify-between">
                    <h2 class="text-lg font-semibold">Agendamento</h2>
                    <label class="flex items-center cursor-pointer">
                        <input 
                            type="checkbox" 
                            x-model="hasSchedule"
                            class="mr-2">
                        <span class="text-sm">Habilitar agendamento</span>
                    </label>
                </div>

                <div x-show="hasSchedule" x-transition>
                    <label for="agendamento" class="form-label">Expressão Cron</label>
                    <input 
                        type="text" 
                        id="agendamento" 
                        name="agendamento" 
                        class="form-input font-mono"
                        value="{{ processo.agendamento if processo else '' }}"
                        placeholder="0 9 * * 1-5"
                        x-bind:required="hasSchedule">
                    <p class="text-sm text-gray-600 mt-2">
                        Exemplos:<br>
                        • <code>0 9 * * *</code> - Todos os dias às 9h<br>
                        • <code>0 9 * * 1-5</code> - Dias úteis às 9h<br>
                        • <code>0 */4 * * *</code> - A cada 4 horas
                    </p>
                    {% if errors.agendamento %}
                    <p class="form-error">{{ errors.agendamento }}</p>
                    {% endif %}
                </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-end space-x-4">
                <a href="{{ url_for('processos_list') }}" class="btn-secondary">
                    Cancelar
                </a>
                <button type="submit" class="btn-primary">
                    {% if processo %}Salvar Alterações{% else %}Criar Processo{% endif %}
                </button>
            </div>
        </div>
    </form>
</div>

<script>
// Contador de URLs
document.getElementById('urls').addEventListener('input', function(e) {
    const lines = e.target.value.split('\n').filter(line => line.trim().length > 0);
    document.getElementById('url-count').textContent = lines.length;
});

// Trigger inicial
document.getElementById('urls').dispatchEvent(new Event('input'));
</script>
{% endblock %}
```

### 3.5. Process Detail (frontend/templates/pages/processos/detail.html)

```html
{% extends "layouts/dashboard.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ processo.nome }}</h1>
            <p class="text-gray-600 mt-1">{{ processo.descricao }}</p>
        </div>
        <div class="flex space-x-2">
            <button 
                hx-post="{{ url_for('api_executar_processo', id=processo.id) }}"
                hx-confirm="Executar processo agora?"
                class="btn-success">
                Executar Agora
            </button>
            <a href="{{ url_for('processos_edit', id=processo.id) }}" class="btn-secondary">
                Editar
            </a>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card">
            <p class="text-sm text-gray-600">Status</p>
            <p class="text-2xl font-bold mt-1">
                {% if processo.status == 'ATIVO' %}
                <span class="text-green-600">Ativo</span>
                {% else %}
                <span class="text-red-600">Inativo</span>
                {% endif %}
            </p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Total de URLs</p>
            <p class="text-2xl font-bold mt-1">{{ processo.configuracao.urls|length if processo.configuracao else 0 }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Execuções</p>
            <p class="text-2xl font-bold mt-1">{{ processo.total_execucoes or 0 }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Taxa de Sucesso</p>
            <p class="text-2xl font-bold mt-1">{{ processo.taxa_sucesso or 0 }}%</p>
        </div>
    </div>

    <!-- Configuração -->
    <div class="card">
        <h2 class="text-lg font-semibold mb-4">Configuração</h2>
        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <dt class="text-sm text-gray-600">Tipo de Extração</dt>
                <dd class="mt-1 font-medium">
                    {% if processo.configuracao %}
                    {{ processo.configuracao.tipo_extracao }}
                    {% else %}
                    -
                    {% endif %}
                </dd>
            </div>

            <div>
                <dt class="text-sm text-gray-600">Timeout</dt>
                <dd class="mt-1 font-medium">
                    {% if processo.configuracao %}
                    {{ processo.configuracao.timeout }}s
                    {% else %}
                    -
                    {% endif %}
                </dd>
            </div>

            <div>
                <dt class="text-sm text-gray-600">Agendamento</dt>
                <dd class="mt-1 font-medium">
                    {% if processo.agendamento %}
                    <code class="bg-gray-100 px-2 py-1 rounded">{{ processo.agendamento }}</code>
                    {% else %}
                    -
                    {% endif %}
                </dd>
            </div>

            <div>
                <dt class="text-sm text-gray-600">Última Execução</dt>
                <dd class="mt-1 font-medium">
                    {% if processo.ultima_execucao %}
                    {{ processo.ultima_execucao.strftime('%d/%m/%Y %H:%M') }}
                    {% else %}
                    Nunca executado
                    {% endif %}
                </dd>
            </div>
        </dl>
    </div>

    <!-- URLs -->
    <div class="card">
        <h2 class="text-lg font-semibold mb-4">URLs Configuradas</h2>
        {% if processo.configuracao and processo.configuracao.urls %}
        <ul class="space-y-2">
            {% for url in processo.configuracao.urls %}
            <li class="flex items-center text-sm">
                <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                </svg>
                <a href="{{ url }}" target="_blank" class="text-blue-600 hover:text-blue-800">
                    {{ url }}
                </a>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="text-gray-500">Nenhuma URL configurada</p>
        {% endif %}
    </div>

    <!-- Execuções Recentes -->
    <div class="card">
        <h2 class="text-lg font-semibold mb-4">Execuções Recentes</h2>
        {% if processo.execucoes %}
        <div class="space-y-3">
            {% for execucao in processo.execucoes[:5] %}
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                    <p class="font-medium">{{ execucao.created_at.strftime('%d/%m/%Y %H:%M') }}</p>
                    <p class="text-sm text-gray-600">
                        {{ execucao.urls_processadas }}/{{ execucao.total_urls }} URLs processadas
                    </p>
                </div>
                <div class="flex items-center space-x-3">
                    <span class="badge-{{ 'success' if execucao.status == 'CONCLUIDO' else 'danger' if execucao.status == 'ERRO' else 'info' }}">
                        {{ execucao.status }}
                    </span>
                    <a href="{{ url_for('execucoes_detail', id=execucao.id) }}" class="text-blue-600 hover:text-blue-800">
                        Ver detalhes →
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p class="text-gray-500">Nenhuma execução ainda</p>
        {% endif %}
    </div>
</div>
{% endblock %}
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-014: Setup Frontend (templates, Tailwind, HTMX)
- PRD-005: Módulo Processo (API endpoints)
- PRD-006: Módulo Configuração (validação)

## 5. Regras de Negócio

### 5.1. Validações
- Nome: obrigatório, único
- URLs: 1-100 URLs, formato válido
- Agendamento: expressão cron válida (se preenchido)
- Timeout: 10-300 segundos

### 5.2. HTMX Behaviors
- Busca com debounce de 500ms
- Delete com confirmação
- Executar com confirmação
- Formulário com validação server-side

### 5.3. Permissões (Futuro)
- MVP: sem autenticação
- Futuro: apenas admin pode deletar

## 6. Casos de Teste

### 6.1. Lista
- ✅ Renderiza lista de processos
- ✅ Busca filtra corretamente
- ✅ Paginação funciona
- ✅ Status filter funciona

### 6.2. Create/Edit
- ✅ Form renderiza corretamente
- ✅ Validações client-side
- ✅ Validações server-side com erros
- ✅ Criação bem-sucedida
- ✅ Edição bem-sucedida

### 6.3. Detail
- ✅ Renderiza detalhes
- ✅ Mostra estatísticas
- ✅ Lista execuções recentes

### 6.4. Delete
- ✅ Confirmação antes de deletar
- ✅ Remoção da linha após delete
- ✅ Erro se processo tem execuções ativas

## 7. Critérios de Aceitação

### ✅ Lista
- [ ] Renderiza processos com paginação
- [ ] Busca em tempo real
- [ ] Filtro por status
- [ ] Ações: executar, editar, deletar

### ✅ Create/Edit
- [ ] Form com todos os campos
- [ ] Validação client + server-side
- [ ] Contador de URLs
- [ ] Agendamento opcional

### ✅ Detail
- [ ] Informações completas
- [ ] Stats cards
- [ ] Lista de URLs
- [ ] Execuções recentes

### ✅ HTMX
- [ ] Busca sem reload
- [ ] Delete remove linha
- [ ] Form submit via HTMX

## 8. Notas de Implementação

### 8.1. HTMX Patterns

**Search with debounce:**
```html
<input 
    hx-get="/processos/search"
    hx-trigger="keyup changed delay:500ms"
    hx-target="#table"
    hx-indicator="#spinner">
```

**Delete with confirm:**
```html
<button 
    hx-delete="/api/v1/processos/{id}"
    hx-confirm="Tem certeza?"
    hx-target="closest tr"
    hx-swap="outerHTML swap:1s">
```

### 8.2. Alpine.js for Modals

```html
<div x-data="{ open: false }">
    <button @click="open = true">Open Modal</button>
    <div x-show="open" @click.away="open = false">
        <!-- Modal content -->
    </div>
</div>
```

## 9. Referências Técnicas

- **HTMX Docs**: https://htmx.org/docs/
- **Alpine.js**: https://alpinejs.dev/
- **Tailwind Forms**: https://tailwindcss.com/docs/plugins#forms

## 10. Definição de Pronto

- ✅ Lista de processos com busca e filtros
- ✅ Form de criação/edição
- ✅ Página de detalhes
- ✅ Delete com confirmação
- ✅ Executar processo via HTMX
- ✅ Validações client e server-side
- ✅ Responsivo (mobile-friendly)

---

**PRD Anterior**: PRD-014 - Setup Frontend  
**Próximo PRD**: PRD-016 - Interface de Monitoramento
