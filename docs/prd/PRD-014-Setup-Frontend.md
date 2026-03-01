# PRD-014: Setup Frontend

**Status**: ✅ Concluído
**Prioridade**: 🟢 Baixa - Frontend (Prioridade 4)
**Categoria**: Frontend - Setup
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Configurar stack frontend com HTMX, Alpine.js, Tailwind CSS e Jinja2 templates. Estabelecer estrutura base de arquivos, sistema de templates, componentes reutilizáveis, build process e integração com FastAPI.

## 2. Contexto e Justificativa

Frontend será server-side rendering (SSR) com progressive enhancement:
- **Jinja2**: Templates server-side
- **HTMX**: Interatividade sem JS complexo (AJAX, partials)
- **Alpine.js**: JS leve para interações (dropdowns, modals)
- **Tailwind CSS**: Utility-first CSS framework

**Vantagens:**
- ✅ Simples de desenvolver e manter
- ✅ SEO-friendly (HTML renderizado no server)
- ✅ Performance (menos JS para carregar)
- ✅ Progressive enhancement (funciona sem JS)

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
frontend/
├── static/                      # Arquivos estáticos
│   ├── css/
│   │   ├── tailwind.css        # Source Tailwind
│   │   └── output.css          # Tailwind compilado
│   ├── js/
│   │   ├── alpine.js           # Alpine.js customizado
│   │   └── app.js              # JS global
│   └── img/
│       └── logo.svg
│
└── templates/                   # Jinja2 templates
    ├── base.html               # Template base
    ├── components/             # Componentes reutilizáveis
    │   ├── navbar.html
    │   ├── sidebar.html
    │   ├── alert.html
    │   ├── modal.html
    │   ├── table.html
    │   └── pagination.html
    ├── layouts/
    │   └── dashboard.html      # Layout do dashboard
    ├── pages/                  # Páginas completas
    │   ├── home.html
    │   ├── processos/
    │   │   ├── list.html
    │   │   ├── create.html
    │   │   ├── edit.html
    │   │   └── detail.html
    │   ├── execucoes/
    │   │   ├── list.html
    │   │   └── detail.html
    │   └── dashboard/
    │       └── index.html
    └── partials/               # Partials para HTMX
        ├── processo_row.html
        ├── execucao_card.html
        └── log_entry.html
```

### 3.2. Configuração Tailwind (frontend/static/css/tailwind.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom styles */
@layer components {
  /* Buttons */
  .btn {
    @apply px-4 py-2 rounded font-medium transition-colors;
  }

  .btn-primary {
    @apply btn bg-blue-600 text-white hover:bg-blue-700;
  }

  .btn-secondary {
    @apply btn bg-gray-600 text-white hover:bg-gray-700;
  }

  .btn-danger {
    @apply btn bg-red-600 text-white hover:bg-red-700;
  }

  .btn-success {
    @apply btn bg-green-600 text-white hover:bg-green-700;
  }

  /* Cards */
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }

  /* Forms */
  .form-input {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500;
  }

  .form-label {
    @apply block text-sm font-medium text-gray-700 mb-2;
  }

  .form-error {
    @apply text-sm text-red-600 mt-1;
  }

  /* Status badges */
  .badge {
    @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
  }

  .badge-success {
    @apply badge bg-green-100 text-green-800;
  }

  .badge-danger {
    @apply badge bg-red-100 text-red-800;
  }

  .badge-warning {
    @apply badge bg-yellow-100 text-yellow-800;
  }

  .badge-info {
    @apply badge bg-blue-100 text-blue-800;
  }
}
```

### 3.3. Tailwind Config (tailwind.config.js)

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/templates/**/*.html",
    "./frontend/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### 3.4. Template Base (frontend/templates/base.html)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Toninho{% endblock %}</title>

    <!-- Tailwind CSS -->
    <link rel="stylesheet" href="{{ url_for('static', path='/css/output.css') }}">

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>

    <!-- Custom JS -->
    <script src="{{ url_for('static', path='/js/app.js') }}" defer></script>

    {% block head %}{% endblock %}
</head>
<body class="bg-gray-50">
    <!-- Flash Messages -->
    {% if messages %}
    <div id="flash-messages" class="fixed top-4 right-4 z-50 space-y-2">
        {% for message in messages %}
        {% include 'components/alert.html' %}
        {% endfor %}
    </div>
    {% endif %}

    <!-- Main Content -->
    {% block body %}{% endblock %}

    <!-- HTMX Config -->
    <script>
        // HTMX event listeners
        document.body.addEventListener('htmx:afterSwap', function(evt) {
            // Re-initialize Alpine components if needed
            console.log('HTMX swap completed');
        });

        // Error handling
        document.body.addEventListener('htmx:responseError', function(evt) {
            console.error('HTMX error:', evt.detail);
            alert('Erro ao processar requisição. Tente novamente.');
        });
    </script>

    {% block scripts %}{% endblock %}
</body>
</html>
```

### 3.5. Layout Dashboard (frontend/templates/layouts/dashboard.html)

```html
{% extends "base.html" %}

{% block body %}
<div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 text-white">
        {% include 'components/sidebar.html' %}
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col">
        <!-- Navbar -->
        <header class="bg-white shadow-sm">
            {% include 'components/navbar.html' %}
        </header>

        <!-- Page Content -->
        <main class="flex-1 p-6">
            {% block content %}{% endblock %}
        </main>
    </div>
</div>
{% endblock %}
```

### 3.6. Component: Sidebar (frontend/templates/components/sidebar.html)

```html
<div class="p-4 h-full flex flex-col">
    <!-- Logo -->
    <div class="mb-8">
        <h1 class="text-2xl font-bold">Toninho</h1>
        <p class="text-xs text-gray-400">Extração de Processos</p>
    </div>

    <!-- Navigation -->
    <nav class="flex-1">
        <ul class="space-y-2">
            <li>
                <a href="{{ url_for('dashboard') }}"
                   class="flex items-center px-4 py-2 rounded hover:bg-gray-700 transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    Dashboard
                </a>
            </li>

            <li>
                <a href="{{ url_for('processos_list') }}"
                   class="flex items-center px-4 py-2 rounded hover:bg-gray-700 transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Processos
                </a>
            </li>

            <li>
                <a href="{{ url_for('execucoes_list') }}"
                   class="flex items-center px-4 py-2 rounded hover:bg-gray-700 transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Execuções
                </a>
            </li>
        </ul>
    </nav>

    <!-- Footer -->
    <div class="border-t border-gray-700 pt-4">
        <p class="text-xs text-gray-400">v1.0.0</p>
    </div>
</div>
```

### 3.7. Component: Alert (frontend/templates/components/alert.html)

```html
<div x-data="{ show: true }"
     x-show="show"
     x-transition
     class="rounded-md p-4 {{ 'bg-green-50 text-green-800' if message.type == 'success'
                              else 'bg-red-50 text-red-800' if message.type == 'error'
                              else 'bg-blue-50 text-blue-800' }}">
    <div class="flex">
        <div class="flex-shrink-0">
            {% if message.type == 'success' %}
            <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            {% elif message.type == 'error' %}
            <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            {% endif %}
        </div>
        <div class="ml-3 flex-1">
            <p class="text-sm font-medium">{{ message.text }}</p>
        </div>
        <div class="ml-auto pl-3">
            <button @click="show = false" class="inline-flex rounded-md p-1.5 hover:bg-gray-100">
                <span class="sr-only">Fechar</span>
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        </div>
    </div>
</div>
```

### 3.8. FastAPI Integration (toninho/api/frontend.py)

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Frontend"])

# Templates
templates = Jinja2Templates(directory="frontend/templates")

# Helper para adicionar contexto global
def get_template_context(request: Request, **kwargs):
    """Adiciona contexto global a todos os templates"""
    return {
        "request": request,
        "app_name": "Toninho",
        "version": "1.0.0",
        **kwargs
    }

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial"""
    context = get_template_context(request, title="Home")
    return templates.TemplateResponse("pages/home.html", context)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    context = get_template_context(request, title="Dashboard")
    return templates.TemplateResponse("pages/dashboard/index.html", context)
```

### 3.9. Static Files Config (toninho/main.py)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Toninho")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include routers
from toninho.api.frontend import router as frontend_router
app.include_router(frontend_router)
```

### 3.10. Build Process (package.json)

```json
{
  "name": "toninho-frontend",
  "version": "1.0.0",
  "scripts": {
    "build:css": "tailwindcss -i ./frontend/static/css/tailwind.css -o ./frontend/static/css/output.css",
    "watch:css": "tailwindcss -i ./frontend/static/css/tailwind.css -o ./frontend/static/css/output.css --watch",
    "build": "npm run build:css"
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.7",
    "@tailwindcss/typography": "^0.5.10",
    "tailwindcss": "^3.4.1"
  }
}
```

## 4. Dependências

### 4.1. Python
- fastapi: ^0.109.0
- jinja2: ^3.1.2

### 4.2. Node.js
- tailwindcss: ^3.4.1
- @tailwindcss/forms: ^0.5.7
- @tailwindcss/typography: ^0.5.10

### 4.3. CDN
- HTMX: 1.9.10
- Alpine.js: 3.13.3

## 5. Regras de Negócio

### 5.1. Templates
- Base template: Contém HTML base, imports de CSS/JS
- Layout templates: Definem estruturas de página (dashboard, auth)
- Page templates: Páginas completas
- Components: Reutilizáveis (alert, modal, table)
- Partials: Fragmentos para HTMX

### 5.2. CSS
- Tailwind utility-first approach
- Custom components em @layer components
- Responsive design (mobile-first)

### 5.3. JavaScript
- Minimal JS (Alpine.js para dropdowns, modals)
- HTMX para interatividade AJAX
- Progressive enhancement

## 6. Casos de Teste

### 6.1. Templates
- ✅ Base template renderiza corretamente
- ✅ Layout dashboard inclui sidebar e navbar
- ✅ Components são reutilizáveis
- ✅ Jinja2 variables funcionam

### 6.2. Static Files
- ✅ CSS compilado corretamente
- ✅ Static files são servidos
- ✅ Hot reload funciona em dev

### 6.3. Routes
- ✅ GET / retorna HTML
- ✅ GET /dashboard retorna HTML
- ✅ Templates recebem contexto correto

## 7. Critérios de Aceitação

### ✅ Setup
- [ ] Estrutura de pastas criada
- [ ] Tailwind configurado
- [ ] HTMX e Alpine.js incluídos
- [ ] Static files montados no FastAPI

### ✅ Templates
- [ ] Base template criado
- [ ] Layout dashboard criado
- [ ] Sidebar e navbar components
- [ ] Alert component

### ✅ Build
- [ ] Tailwind compila CSS
- [ ] Watch mode funciona
- [ ] CSS minificado em produção

### ✅ Integração
- [ ] FastAPI serve templates
- [ ] FastAPI serve static files
- [ ] Contexto global funciona

## 8. Notas de Implementação

### 8.1. Development Mode

```bash
# Terminal 1: Watch Tailwind
npm run watch:css

# Terminal 2: Run FastAPI
poetry run uvicorn toninho.main:app --reload
```

### 8.2. Production Build

```bash
# Build CSS
npm run build:css -- --minify

# Run FastAPI
poetry run uvicorn toninho.main:app --host 0.0.0.0 --port 8000
```

### 8.3. Makefile Helpers

```makefile
.PHONY: frontend-dev frontend-build

frontend-dev:
	npm run watch:css

frontend-build:
	npm run build:css -- --minify
```

## 9. Referências Técnicas

- **HTMX**: https://htmx.org/
- **Alpine.js**: https://alpinejs.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **Jinja2**: https://jinja.palletsprojects.com/

## 10. Definição de Pronto

- ✅ Estrutura de pastas criada
- ✅ Tailwind configurado e compilando
- ✅ HTMX e Alpine.js incluídos
- ✅ Base template e layout dashboard
- ✅ Components básicos (sidebar, navbar, alert)
- ✅ FastAPI servindo templates e static files
- ✅ Watch mode funcionando
- ✅ Página inicial e dashboard renderizam

---

**PRD Anterior**: PRD-013 - Testes e Qualidade
**Próximo PRD**: PRD-015 - Interface CRUD Processos
