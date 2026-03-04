# PRD-016: Interface de Monitoramento

**Status**: ✅ Concluído
**Prioridade**: 🟢 Baixa - Frontend (Prioridade 4)
**Categoria**: Frontend - Features
**Estimativa**: 8-10 horas

---

## 1. Objetivo

Implementar dashboard de monitoramento em tempo real com visualização de execuções ativas, logs streaming via SSE, status de workers, métricas operacionais e controles de execução (pausar, cancelar, retomar).

## 2. Contexto e Justificativa

Dashboard é o coração operacional do Toninho. Permite:
- **Visão geral**: Status de todas execuções
- **Real-time**: Atualizações ao vivo via SSE/WebSocket
- **Controle**: Pausar, cancelar, retomar execuções
- **Logs**: Stream de logs em tempo real
- **Métricas**: Gráficos e indicadores de performance

**Tecnologias:**
- Server-Sent Events (SSE) para logs streaming
- WebSocket para status updates
- HTMX para polling e partials
- Alpine.js para UI interativa (charts, progress bars)

## 3. Requisitos Técnicos

### 3.1. Páginas e Rotas

**Frontend Routes:**
```python
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal com métricas"""

@router.get("/execucoes", response_class=HTMLResponse)
async def execucoes_list(request: Request):
    """Lista de todas execuções"""

@router.get("/execucoes/{id}", response_class=HTMLResponse)
async def execucoes_detail(request: Request, id: UUID):
    """Detalhes de execução com logs streaming"""

# Partials
@router.get("/dashboard/stats", response_class=HTMLResponse)
async def dashboard_stats(request: Request):
    """Stats cards (para polling)"""

@router.get("/execucoes/{id}/progress", response_class=HTMLResponse)
async def execucao_progress(request: Request, id: UUID):
    """Progress bar partial (para polling)"""
```

### 3.2. Dashboard Principal (frontend/templates/pages/dashboard/index.html)

```html
{% extends "layouts/dashboard.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p class="text-gray-600 mt-1">Visão geral do sistema</p>
    </div>

    <!-- Stats Cards -->
    <div
        id="stats-cards"
        hx-get="{{ url_for('dashboard_stats') }}"
        hx-trigger="every 5s"
        hx-swap="outerHTML">
        {% include 'partials/dashboard_stats.html' %}
    </div>

    <!-- System Status -->
    <div class="card">
        <h2 class="text-lg font-semibold mb-4">Status do Sistema</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- API Status -->
            <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                <div class="flex-shrink-0">
                    <div class="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <div>
                    <p class="text-sm font-medium">API</p>
                    <p class="text-xs text-gray-600">Operacional</p>
                </div>
            </div>

            <!-- Workers Status -->
            <div
                hx-get="{{ url_for('health_workers') }}"
                hx-trigger="every 10s"
                class="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                <div class="flex-shrink-0">
                    <div class="w-3 h-3 rounded-full"
                         :class="workers_online ? 'bg-green-500' : 'bg-red-500'">
                    </div>
                </div>
                <div>
                    <p class="text-sm font-medium">Workers</p>
                    <p class="text-xs text-gray-600">
                        <span id="worker-count">{{ worker_count }}</span> ativos
                    </p>
                </div>
            </div>

            <!-- Redis Status -->
            <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                <div class="flex-shrink-0">
                    <div class="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <div>
                    <p class="text-sm font-medium">Redis</p>
                    <p class="text-xs text-gray-600">Conectado</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Execuções Ativas -->
    <div class="card">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">Execuções Ativas</h2>
            <a href="{{ url_for('execucoes_list') }}" class="text-sm text-blue-600 hover:text-blue-800">
                Ver todas →
            </a>
        </div>

        <div
            id="execucoes-ativas"
            hx-get="{{ url_for('execucoes_ativas_partial') }}"
            hx-trigger="every 3s"
            hx-swap="innerHTML">
            {% include 'partials/execucoes_ativas.html' %}
        </div>
    </div>

    <!-- Atividade Recente -->
    <div class="card">
        <h2 class="text-lg font-semibold mb-4">Atividade Recente</h2>
        <div class="space-y-3">
            {% for activity in recent_activities %}
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div class="flex items-center space-x-3">
                    <div class="flex-shrink-0">
                        {% if activity.type == 'execution_completed' %}
                        <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                        {% elif activity.type == 'execution_failed' %}
                        <svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
                        {% endif %}
                    </div>
                    <div>
                        <p class="text-sm font-medium">{{ activity.message }}</p>
                        <p class="text-xs text-gray-600">{{ activity.timestamp }}</p>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

### 3.3. Dashboard Stats Partial (frontend/templates/partials/dashboard_stats.html)

```html
<div id="stats-cards" class="grid grid-cols-1 md:grid-cols-4 gap-4">
    <!-- Total Execuções -->
    <div class="card border-l-4 border-blue-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-600">Total de Execuções</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ metrics.executions.total }}</p>
            </div>
            <div class="p-3 bg-blue-100 rounded-full">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
            </div>
        </div>
    </div>

    <!-- Ativas -->
    <div class="card border-l-4 border-yellow-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-600">Execuções Ativas</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ metrics.executions.active }}</p>
            </div>
            <div class="p-3 bg-yellow-100 rounded-full">
                <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
        </div>
    </div>

    <!-- Concluídas -->
    <div class="card border-l-4 border-green-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-600">Concluídas</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ metrics.executions.completed }}</p>
            </div>
            <div class="p-3 bg-green-100 rounded-full">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
        </div>
    </div>

    <!-- Taxa de Sucesso -->
    <div class="card border-l-4 border-purple-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm text-gray-600">Taxa de Sucesso</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ metrics.success_rate }}%</p>
            </div>
            <div class="p-3 bg-purple-100 rounded-full">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
            </div>
        </div>
    </div>
</div>
```

### 3.4. Execuções Ativas Partial (frontend/templates/partials/execucoes_ativas.html)

```html
{% if execucoes %}
<div class="space-y-3">
    {% for exec in execucoes %}
    <div class="border border-gray-200 rounded-lg p-4">
        <div class="flex items-center justify-between mb-3">
            <div>
                <p class="font-medium">{{ exec.processo.nome }}</p>
                <p class="text-sm text-gray-600">Iniciada {{ exec.started_at_relative }}</p>
            </div>
            <span class="badge-{{ 'info' if exec.status == 'EM_EXECUCAO' else 'warning' }}">
                {{ exec.status }}
            </span>
        </div>

        <!-- Progress Bar -->
        <div
            hx-get="{{ url_for('execucao_progress', id=exec.id) }}"
            hx-trigger="every 2s"
            hx-swap="innerHTML">
            {% include 'partials/progress_bar.html' %}
        </div>

        <!-- Actions -->
        <div class="flex space-x-2 mt-3">
            <a href="{{ url_for('execucoes_detail', id=exec.id) }}"
               class="text-sm text-blue-600 hover:text-blue-800">
                Ver detalhes
            </a>

            {% if exec.status == 'EM_EXECUCAO' %}
            <button
                hx-post="{{ url_for('api_pausar_execucao', id=exec.id) }}"
                hx-swap="none"
                class="text-sm text-yellow-600 hover:text-yellow-800">
                Pausar
            </button>
            {% elif exec.status == 'PAUSADO' %}
            <button
                hx-post="{{ url_for('api_retomar_execucao', id=exec.id) }}"
                hx-swap="none"
                class="text-sm text-green-600 hover:text-green-800">
                Retomar
            </button>
            {% endif %}

            <button
                hx-post="{{ url_for('api_cancelar_execucao', id=exec.id) }}"
                hx-confirm="Tem certeza que deseja cancelar?"
                hx-swap="none"
                class="text-sm text-red-600 hover:text-red-800">
                Cancelar
            </button>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<p class="text-center text-gray-500 py-8">Nenhuma execução ativa no momento</p>
{% endif %}
```

### 3.5. Progress Bar Partial (frontend/templates/partials/progress_bar.html)

```html
<div>
    <div class="flex justify-between text-sm text-gray-600 mb-1">
        <span>Progresso</span>
        <span>{{ execucao.urls_processadas }} / {{ execucao.total_urls }} URLs</span>
    </div>
    <div class="w-full bg-gray-200 rounded-full h-2">
        <div
            class="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style="width: {{ execucao.progress_percentage }}%">
        </div>
    </div>
    <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>{{ execucao.urls_sucesso }} sucesso</span>
        <span>{{ execucao.urls_erro }} erros</span>
    </div>
</div>
```

### 3.6. Execution Detail with Logs (frontend/templates/pages/execucoes/detail.html)

```html
{% extends "layouts/dashboard.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">
                Execução: {{ execucao.processo.nome }}
            </h1>
            <p class="text-gray-600 mt-1">
                Iniciada em {{ execucao.created_at.strftime('%d/%m/%Y %H:%M:%S') }}
            </p>
        </div>
        <div class="flex space-x-2">
            {% if execucao.status == 'EM_EXECUCAO' %}
            <button
                hx-post="{{ url_for('api_pausar_execucao', id=execucao.id) }}"
                hx-swap="none"
                class="btn-secondary">
                Pausar
            </button>
            {% elif execucao.status == 'PAUSADO' %}
            <button
                hx-post="{{ url_for('api_retomar_execucao', id=execucao.id) }}"
                hx-swap="none"
                class="btn-success">
                Retomar
            </button>
            {% endif %}

            <button
                hx-post="{{ url_for('api_cancelar_execucao', id=execucao.id) }}"
                hx-confirm="Tem certeza?"
                hx-swap="none"
                class="btn-danger">
                Cancelar
            </button>
        </div>
    </div>

    <!-- Status & Progress -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card">
            <p class="text-sm text-gray-600">Status</p>
            <p class="text-lg font-bold mt-1">
                <span class="badge-{{ 'success' if execucao.status == 'CONCLUIDO' else 'info' if execucao.status == 'EM_EXECUCAO' else 'danger' }}">
                    {{ execucao.status }}
                </span>
            </p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">URLs Processadas</p>
            <p class="text-2xl font-bold mt-1">{{ execucao.urls_processadas }} / {{ execucao.total_urls }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Sucesso</p>
            <p class="text-2xl font-bold text-green-600 mt-1">{{ execucao.urls_sucesso }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Erros</p>
            <p class="text-2xl font-bold text-red-600 mt-1">{{ execucao.urls_erro }}</p>
        </div>
    </div>

    <!-- Progress Bar -->
    <div
        class="card"
        hx-get="{{ url_for('execucao_progress', id=execucao.id) }}"
        hx-trigger="every 2s"
        hx-swap="innerHTML">
        {% include 'partials/progress_bar.html' %}
    </div>

    <!-- Logs Streaming -->
    <div class="card">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">Logs</h2>
            <div class="flex items-center space-x-2">
                <!-- Auto-scroll toggle -->
                <label class="flex items-center text-sm">
                    <input
                        type="checkbox"
                        id="auto-scroll"
                        checked
                        class="mr-2">
                    Auto-scroll
                </label>

                <!-- Level filter -->
                <select id="log-level-filter" class="text-sm border rounded px-2 py-1">
                    <option value="">Todos</option>
                    <option value="INFO">Info</option>
                    <option value="WARNING">Warning</option>
                    <option value="ERROR">Error</option>
                </select>
            </div>
        </div>

        <!-- Log Container -->
        <div
            id="logs-container"
            class="bg-gray-900 text-gray-100 rounded p-4 font-mono text-sm h-96 overflow-y-auto">
            <div id="logs-content"></div>
        </div>
    </div>

    <!-- Páginas Extraídas -->
    <div class="card">
        <h2 class="text-lg font-semibold mb-4">Páginas Extraídas</h2>
        <a href="{{ url_for('execucao_paginas', id=execucao.id) }}" class="text-blue-600 hover:text-blue-800">
            Ver todas as páginas extraídas ({{ execucao.paginas_extraidas|length }}) →
        </a>
    </div>
</div>

<script>
// SSE for log streaming
const logsContent = document.getElementById('logs-content');
const logsContainer = document.getElementById('logs-container');
const autoScrollCheckbox = document.getElementById('auto-scroll');

const eventSource = new EventSource("{{ url_for('api_logs_stream', execucao_id=execucao.id) }}");

eventSource.onmessage = function(event) {
    const log = JSON.parse(event.data);

    // Filter by level
    const levelFilter = document.getElementById('log-level-filter').value;
    if (levelFilter && log.nivel !== levelFilter) {
        return;
    }

    // Create log line
    const logLine = document.createElement('div');
    logLine.className = 'mb-1';

    const timestamp = new Date(log.timestamp).toLocaleTimeString();
    const levelColor = {
        'INFO': 'text-blue-400',
        'WARNING': 'text-yellow-400',
        'ERROR': 'text-red-400',
        'DEBUG': 'text-gray-400'
    }[log.nivel] || 'text-gray-400';

    logLine.innerHTML = `
        <span class="text-gray-500">${timestamp}</span>
        <span class="${levelColor}">[${log.nivel}]</span>
        <span>${log.mensagem}</span>
    `;

    logsContent.appendChild(logLine);

    // Auto-scroll
    if (autoScrollCheckbox.checked) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }
};

eventSource.onerror = function() {
    console.error('SSE connection error');
    // Reconectar após 5s
    setTimeout(() => {
        location.reload();
    }, 5000);
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    eventSource.close();
});

// Level filter change
document.getElementById('log-level-filter').addEventListener('change', () => {
    logsContent.innerHTML = '';  // Clear and reload
});
</script>
{% endblock %}
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-014: Setup Frontend
- PRD-007: Módulo Execução (API)
- PRD-008: Módulo Log (SSE streaming)
- PRD-012: Monitoramento e Métricas

## 5. Regras de Negócio

### 5.1. Real-time Updates
- Dashboard stats: Polling a cada 5s
- Execuções ativas: Polling a cada 3s
- Progress bars: Polling a cada 2s
- Logs: SSE (real-time push)

### 5.2. Controles
- Pausar: Apenas execuções EM_EXECUCAO
- Retomar: Apenas execuções PAUSADO
- Cancelar: Qualquer execução não terminal

### 5.3. Logs
- Auto-scroll habilitado por padrão
- Filtro por nível (INFO, WARNING, ERROR)
- Limit de 1000 linhas em memória (performance)

## 6. Casos de Teste

### 6.1. Dashboard
- ✅ Stats cards atualizam via polling
- ✅ System status mostra workers
- ✅ Execuções ativas listadas

### 6.2. Execution Detail
- ✅ Progress bar atualiza
- ✅ Logs streamam via SSE
- ✅ Auto-scroll funciona
- ✅ Level filter funciona

### 6.3. Controls
- ✅ Pausar execução funciona
- ✅ Retomar execução funciona
- ✅ Cancelar execução funciona

## 7. Critérios de Aceitação

### ✅ Dashboard
- [ ] Stats cards com métricas
- [ ] System status (API, workers, Redis)
- [ ] Execuções ativas com progress
- [ ] Atividade recente

### ✅ Execution Detail
- [ ] Status e progresso
- [ ] Logs streaming via SSE
- [ ] Auto-scroll e filtros
- [ ] Controles (pausar, retomar, cancelar)

### ✅ Real-time
- [ ] Polling funciona
- [ ] SSE conecta e recebe logs
- [ ] Reconecta automaticamente em caso de erro

## 8. Notas de Implementação

### 8.1. SSE Client Pattern

```javascript
const eventSource = new EventSource("/api/v1/logs/stream?execucao_id=123");

eventSource.onmessage = (event) => {
    const log = JSON.parse(event.data);
    // Append to DOM
};

eventSource.onerror = () => {
    eventSource.close();
    // Reconnect logic
};

window.addEventListener('beforeunload', () => {
    eventSource.close();
});
```

### 8.2. HTMX Polling Pattern

```html
<div
    hx-get="/api/stats"
    hx-trigger="every 5s"
    hx-swap="innerHTML">
    <!-- Content -->
</div>
```

### 8.3. Performance
- Limitar logs em memória (últimas 1000 linhas)
- Virtualização para grandes listas (futuro)
- Debounce em filtros

## 9. Referências Técnicas

- **SSE**: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- **HTMX Polling**: https://htmx.org/docs/#polling

## 10. Definição de Pronto

- ✅ Dashboard com métricas e polling
- ✅ System status indicators
- ✅ Execuções ativas com progress bars
- ✅ Execution detail page
- ✅ Logs streaming via SSE
- ✅ Auto-scroll e filtros de logs
- ✅ Controles de execução (pausar, retomar, cancelar)
- ✅ Responsivo

---

**PRD Anterior**: PRD-015 - Interface CRUD Processos
**Próximo PRD**: PRD-017 - Detalhes e Downloads
