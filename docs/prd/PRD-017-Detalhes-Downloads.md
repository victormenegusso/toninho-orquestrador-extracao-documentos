# PRD-017: Detalhes e Downloads

**Status**: 📋 Pronto para implementação  
**Prioridade**: 🟢 Baixa - Frontend (Prioridade 4)  
**Categoria**: Frontend - Features  
**Estimativa**: 6-8 horas

---

## 1. Objetivo

Implementar interface para visualização detalhada de páginas extraídas e sistema de downloads. Inclui listagem de páginas por execução, preview de conteúdo markdown, download individual e em lote (ZIP), estatísticas de extração e navegação entre páginas.

## 2. Contexto e Justificativa

Após a extração, usuário precisa:
- **Visualizar** páginas extraídas
- **Baixar** arquivos markdown individualmente
- **Baixar em lote** todas páginas de uma execução (ZIP)
- **Filtrar** por status (sucesso/erro)
- **Buscar** páginas por URL ou título
- **Ver estatísticas** de extração (tamanho, tempo)

**Tecnologias:**
- HTMX para filtros e paginação
- Alpine.js para preview modal
- FastAPI FileResponse para downloads
- Streaming ZIP para downloads em lote

## 3. Requisitos Técnicos

### 3.1. Páginas e Rotas

**Frontend Routes:**
```python
@router.get("/execucoes/{id}/paginas", response_class=HTMLResponse)
async def execucao_paginas(request: Request, id: UUID):
    """Lista páginas extraídas de uma execução"""

@router.get("/paginas/{id}", response_class=HTMLResponse)
async def pagina_detail(request: Request, id: UUID):
    """Detalhes de uma página extraída"""

# Download endpoints (API)
@router.get("/api/v1/paginas/{id}/download")
async def download_pagina(id: UUID):
    """Download arquivo markdown individual"""

@router.get("/api/v1/execucoes/{id}/download-all")
async def download_all_paginas(id: UUID):
    """Download ZIP com todas as páginas"""

# Partials
@router.get("/paginas/search", response_class=HTMLResponse)
async def paginas_search(request: Request, q: str):
    """Busca páginas (partial)"""
```

### 3.2. Lista de Páginas (frontend/templates/pages/execucoes/paginas.html)

```html
{% extends "layouts/dashboard.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">Páginas Extraídas</h1>
            <p class="text-gray-600 mt-1">
                <a href="{{ url_for('execucoes_detail', id=execucao.id) }}" 
                   class="text-blue-600 hover:text-blue-800">
                    ← Voltar para execução
                </a>
            </p>
        </div>
        <div class="flex space-x-2">
            <!-- Download All -->
            <a 
                href="{{ url_for('api_download_all_paginas', id=execucao.id) }}"
                class="btn-primary flex items-center"
                {% if not paginas.items %}disabled{% endif %}>
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Baixar Todas (ZIP)
            </a>
        </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card">
            <p class="text-sm text-gray-600">Total de Páginas</p>
            <p class="text-2xl font-bold mt-1">{{ execucao.total_urls }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Extraídas com Sucesso</p>
            <p class="text-2xl font-bold text-green-600 mt-1">{{ execucao.urls_sucesso }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Erros</p>
            <p class="text-2xl font-bold text-red-600 mt-1">{{ execucao.urls_erro }}</p>
        </div>

        <div class="card">
            <p class="text-sm text-gray-600">Tamanho Total</p>
            <p class="text-2xl font-bold mt-1">{{ total_size_formatted }}</p>
        </div>
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
                    placeholder="URL ou título..."
                    hx-get="{{ url_for('paginas_search', execucao_id=execucao.id) }}"
                    hx-trigger="keyup changed delay:500ms"
                    hx-target="#paginas-grid"
                    hx-indicator="#search-indicator">
                <span id="search-indicator" class="htmx-indicator">⏳</span>
            </div>

            <!-- Status Filter -->
            <div>
                <label class="form-label">Status</label>
                <select 
                    name="status" 
                    class="form-input"
                    hx-get="{{ url_for('execucao_paginas', id=execucao.id) }}"
                    hx-target="#paginas-grid"
                    hx-include="[name='search']">
                    <option value="">Todos</option>
                    <option value="success">Sucesso</option>
                    <option value="error">Erro</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Grid de Páginas -->
    <div id="paginas-grid">
        {% include 'partials/paginas_grid.html' %}
    </div>
</div>
{% endblock %}
```

### 3.3. Páginas Grid Partial (frontend/templates/partials/paginas_grid.html)

```html
{% if paginas.items %}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {% for pagina in paginas.items %}
    <div class="card hover:shadow-lg transition-shadow">
        <!-- Header -->
        <div class="flex items-start justify-between mb-3">
            <div class="flex-1 min-w-0">
                <h3 class="text-sm font-medium text-gray-900 truncate">
                    {{ pagina.titulo or 'Sem título' }}
                </h3>
                <p class="text-xs text-gray-500 truncate mt-1">
                    {{ pagina.url }}
                </p>
            </div>
            <span class="badge-{{ 'success' if pagina.status_extracao == 'sucesso' else 'danger' }} ml-2">
                {{ pagina.status_extracao }}
            </span>
        </div>

        <!-- Metadata -->
        <div class="space-y-1 text-xs text-gray-600 mb-3">
            <div class="flex justify-between">
                <span>Tamanho:</span>
                <span class="font-medium">{{ pagina.tamanho_bytes|filesizeformat }}</span>
            </div>
            <div class="flex justify-between">
                <span>Extraída em:</span>
                <span class="font-medium">{{ pagina.created_at.strftime('%d/%m %H:%M') }}</span>
            </div>
            {% if pagina.tempo_extracao %}
            <div class="flex justify-between">
                <span>Tempo:</span>
                <span class="font-medium">{{ pagina.tempo_extracao }}s</span>
            </div>
            {% endif %}
        </div>

        <!-- Actions -->
        <div class="flex space-x-2 pt-3 border-t">
            <!-- Preview -->
            <button 
                @click="$dispatch('open-preview', { id: '{{ pagina.id }}' })"
                class="flex-1 text-sm text-blue-600 hover:text-blue-800 font-medium">
                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                Preview
            </button>

            <!-- Download -->
            <a 
                href="{{ url_for('api_download_pagina', id=pagina.id) }}"
                download
                class="flex-1 text-sm text-green-600 hover:text-green-800 font-medium text-center">
                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Baixar
            </a>
        </div>
    </div>
    {% endfor %}
</div>

<!-- Pagination -->
{% if paginas.pages > 1 %}
<div class="mt-6">
    {% include 'components/pagination.html' %}
</div>
{% endif %}

{% else %}
<div class="text-center py-12">
    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
    </svg>
    <h3 class="mt-2 text-sm font-medium text-gray-900">Nenhuma página encontrada</h3>
    <p class="mt-1 text-sm text-gray-500">
        Ajuste os filtros ou aguarde a extração terminar.
    </p>
</div>
{% endif %}
```

### 3.4. Preview Modal (frontend/templates/components/preview_modal.html)

```html
<!-- Incluir no base.html ou na página de paginas -->
<div 
    x-data="{ 
        open: false, 
        paginaId: null,
        loading: false,
        content: '',
        title: '',
        url: ''
    }"
    @open-preview.window="
        open = true;
        paginaId = $event.detail.id;
        loading = true;
        fetch(`/api/v1/paginas/${paginaId}`)
            .then(r => r.json())
            .then(data => {
                title = data.titulo;
                url = data.url;
                content = data.conteudo_markdown;
                loading = false;
            });
    "
    x-show="open"
    x-cloak
    class="fixed inset-0 z-50 overflow-y-auto"
    style="display: none;">
    
    <!-- Backdrop -->
    <div 
        class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        @click="open = false">
    </div>

    <!-- Modal -->
    <div class="flex items-center justify-center min-h-screen p-4">
        <div 
            class="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col"
            @click.away="open = false">
            
            <!-- Header -->
            <div class="flex items-start justify-between p-4 border-b">
                <div class="flex-1 min-w-0">
                    <h3 class="text-lg font-medium text-gray-900 truncate" x-text="title"></h3>
                    <p class="text-sm text-gray-500 truncate mt-1" x-text="url"></p>
                </div>
                <button 
                    @click="open = false"
                    class="ml-4 text-gray-400 hover:text-gray-500">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>

            <!-- Content -->
            <div class="flex-1 overflow-y-auto p-6">
                <div x-show="loading" class="text-center py-8">
                    <svg class="animate-spin h-8 w-8 mx-auto text-blue-600" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="mt-2 text-gray-600">Carregando...</p>
                </div>

                <div x-show="!loading" class="prose max-w-none">
                    <!-- Markdown renderizado -->
                    <pre class="whitespace-pre-wrap text-sm" x-text="content"></pre>
                </div>
            </div>

            <!-- Footer -->
            <div class="flex justify-end p-4 border-t space-x-2">
                <button 
                    @click="open = false"
                    class="btn-secondary">
                    Fechar
                </button>
                <a 
                    :href="`/api/v1/paginas/${paginaId}/download`"
                    download
                    class="btn-primary">
                    Baixar
                </a>
            </div>
        </div>
    </div>
</div>
```

### 3.5. API Download Endpoints (toninho/api/v1/paginas.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import zipfile
import io

from toninho.database import get_db
from toninho.repositories.pagina_repository import PaginaExtraidaRepository
from toninho.models import Execucao

router = APIRouter(prefix="/paginas", tags=["Páginas"])

@router.get("/{id}/download")
async def download_pagina(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download arquivo markdown de uma página
    """
    repo = PaginaExtraidaRepository(db)
    pagina = await repo.buscar_por_id(id)
    
    if not pagina:
        raise HTTPException(status_code=404, detail="Página não encontrada")
    
    file_path = Path(pagina.caminho_arquivo)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Generate safe filename
    from urllib.parse import urlparse
    parsed = urlparse(pagina.url)
    filename = f"{parsed.netloc}_{parsed.path.replace('/', '_')}.md"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/markdown"
    )

@router.get("/execucoes/{execucao_id}/download-all")
async def download_all_paginas(
    execucao_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download ZIP com todas páginas de uma execução
    """
    # Buscar execução
    result = await db.execute(
        select(Execucao).where(Execucao.id == execucao_id)
    )
    execucao = result.scalar_one_or_none()
    
    if not execucao:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    
    # Buscar páginas
    repo = PaginaExtraidaRepository(db)
    paginas = await repo.listar_por_execucao(execucao_id, filtros={"status": "sucesso"})
    
    if not paginas:
        raise HTTPException(status_code=404, detail="Nenhuma página para baixar")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for pagina in paginas:
            file_path = Path(pagina.caminho_arquivo)
            
            if file_path.exists():
                # Add to ZIP with safe filename
                arcname = f"{pagina.id}.md"
                zip_file.write(file_path, arcname=arcname)
    
    zip_buffer.seek(0)
    
    # Return as streaming response
    filename = f"execucao_{execucao_id}_paginas.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

### 3.6. Pagination Component (frontend/templates/components/pagination.html)

```html
<nav class="flex items-center justify-between">
    <!-- Info -->
    <div class="text-sm text-gray-700">
        Mostrando 
        <span class="font-medium">{{ (pagination.page - 1) * pagination.size + 1 }}</span>
        até
        <span class="font-medium">{{ min(pagination.page * pagination.size, pagination.total) }}</span>
        de
        <span class="font-medium">{{ pagination.total }}</span>
        resultados
    </div>

    <!-- Buttons -->
    <div class="flex space-x-2">
        <!-- Previous -->
        <button
            {% if pagination.page <= 1 %}disabled{% endif %}
            hx-get="{{ request.url.path }}?page={{ pagination.page - 1 }}&size={{ pagination.size }}"
            hx-target="#paginas-grid"
            class="px-3 py-1 border rounded text-sm {{ 'text-gray-400 cursor-not-allowed' if pagination.page <= 1 else 'text-gray-700 hover:bg-gray-50' }}">
            Anterior
        </button>

        <!-- Page numbers -->
        {% for page_num in range(1, pagination.pages + 1) %}
            {% if page_num == pagination.page or 
                   page_num == 1 or 
                   page_num == pagination.pages or
                   (page_num >= pagination.page - 2 and page_num <= pagination.page + 2) %}
            <button
                hx-get="{{ request.url.path }}?page={{ page_num }}&size={{ pagination.size }}"
                hx-target="#paginas-grid"
                class="px-3 py-1 border rounded text-sm {{ 'bg-blue-600 text-white' if page_num == pagination.page else 'text-gray-700 hover:bg-gray-50' }}">
                {{ page_num }}
            </button>
            {% elif page_num == pagination.page - 3 or page_num == pagination.page + 3 %}
            <span class="px-2 text-gray-400">...</span>
            {% endif %}
        {% endfor %}

        <!-- Next -->
        <button
            {% if pagination.page >= pagination.pages %}disabled{% endif %}
            hx-get="{{ request.url.path }}?page={{ pagination.page + 1 }}&size={{ pagination.size }}"
            hx-target="#paginas-grid"
            class="px-3 py-1 border rounded text-sm {{ 'text-gray-400 cursor-not-allowed' if pagination.page >= pagination.pages else 'text-gray-700 hover:bg-gray-50' }}">
            Próxima
        </button>
    </div>
</nav>
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-014: Setup Frontend
- PRD-009: Módulo Página Extraída (API)

## 5. Regras de Negócio

### 5.1. Downloads
- Individual: Arquivo markdown com nome seguro
- ZIP: streaming para não consumir memória
- Apenas páginas com sucesso no ZIP

### 5.2. Preview
- Modal com markdown raw (ou renderizado se parser instalado)
- Carregamento lazy via API

### 5.3. Filtros
- Busca: Por URL ou título
- Status: Sucesso/Erro
- Paginação: 12 itens por página (grid 3x4)

## 6. Casos de Teste

### 6.1. Lista
- ✅ Renderiza grid de páginas
- ✅ Busca filtra corretamente
- ✅ Status filter funciona
- ✅ Paginação funciona

### 6.2. Preview
- ✅ Modal abre ao clicar
- ✅ Conteúdo carrega via API
- ✅ Modal fecha corretamente

### 6.3. Downloads
- ✅ Download individual funciona
- ✅ Download ZIP com todas páginas
- ✅ Nomes de arquivo corretos

## 7. Critérios de Aceitação

### ✅ Lista
- [ ] Grid responsivo de páginas
- [ ] Stats cards
- [ ] Busca e filtros
- [ ] Paginação

### ✅ Preview
- [ ] Modal funcional
- [ ] Carregamento via API
- [ ] Exibe conteúdo markdown

### ✅ Downloads
- [ ] Download individual
- [ ] Download ZIP em lote
- [ ] Nomes de arquivo seguros

## 8. Notas de Implementação

### 8.1. ZIP Streaming

Para evitar consumir muita memória ao criar ZIP grande:

```python
async def generate_zip():
    with zipfile.ZipFile(..., mode='w') as zip:
        for pagina in paginas:
            zip.write(file_path, arcname)
            # Yield chunks periodicamente
```

### 8.2. Safe Filenames

```python
import re
from urllib.parse import urlparse

def safe_filename(url: str) -> str:
    parsed = urlparse(url)
    filename = f"{parsed.netloc}_{parsed.path}"
    filename = re.sub(r'[^\w\-]', '_', filename)
    return f"{filename[:100]}.md"  # Limit length
```

### 8.3. Markdown Preview

Para renderizar markdown no preview (opcional):

```bash
poetry add markdown
```

```python
import markdown

html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
```

## 9. Referências Técnicas

- **Python zipfile**: https://docs.python.org/3/library/zipfile.html
- **FastAPI FileResponse**: https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse

## 10. Definição de Pronto

- ✅ Lista de páginas com grid responsivo
- ✅ Busca e filtros funcionais
- ✅ Preview modal com Alpine.js
- ✅ Download individual de arquivos
- ✅ Download ZIP em lote
- ✅ Paginação
- ✅ Stats cards com métricas
- ✅ Responsivo (mobile-friendly)

---

**PRD Anterior**: PRD-016 - Interface de Monitoramento  
**Próximo PRD**: N/A (último PRD)

**STATUS DO PROJETO**: ✅ Todos os 17 PRDs foram criados com sucesso!
