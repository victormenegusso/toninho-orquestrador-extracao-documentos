/**
 * Toninho Frontend - JavaScript Global
 *
 * Configurações globais de HTMX e utilitários.
 */

// ==================== HTMX Configuration ====================

document.addEventListener('htmx:configRequest', function (evt) {
    // Adicionar headers globais se necessário
});

document.addEventListener('htmx:responseError', function (evt) {
    const status = evt.detail.xhr.status;
    showToast(getErrorMessage(status), 'error');
});

document.addEventListener('htmx:timeout', function (evt) {
    showToast('Tempo limite excedido. Tente novamente.', 'warning');
});

// ==================== Toast Notifications ====================

function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.id = 'flash-messages';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm';
        document.body.appendChild(container);
    }

    const colors = {
        success: 'bg-green-50 text-green-800',
        error: 'bg-red-50 text-red-800',
        warning: 'bg-yellow-50 text-yellow-800',
        info: 'bg-blue-50 text-blue-800',
    };

    const toast = document.createElement('div');
    toast.className = `rounded-md p-4 shadow-lg ${colors[type] || colors.info} transition-opacity duration-300`;
    toast.innerHTML = `<p class="text-sm font-medium">${escapeHtml(message)}</p>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function getErrorMessage(status) {
    const messages = {
        400: 'Dados inválidos.',
        401: 'Não autorizado.',
        403: 'Acesso negado.',
        404: 'Recurso não encontrado.',
        409: 'Conflito: recurso já existe.',
        500: 'Erro interno do servidor.',
    };
    return messages[status] || `Erro na requisição (${status}).`;
}

// ==================== URL Counter ====================

document.addEventListener('DOMContentLoaded', function () {
    const urlTextareas = document.querySelectorAll('[data-url-counter]');
    urlTextareas.forEach(textarea => {
        const counterId = textarea.dataset.urlCounter;
        const counter = document.getElementById(counterId);
        if (counter) {
            const updateCount = () => {
                const lines = textarea.value.split('\n').filter(l => l.trim().length > 0);
                counter.textContent = lines.length;
            };
            textarea.addEventListener('input', updateCount);
            updateCount();
        }
    });
});

// ==================== API Utilities ====================

const Toninho = {
    async api(endpoint, options = {}) {
        const response = await fetch(`/api/v1${endpoint}`, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        return response.json();
    },
    showToast,
};

window.Toninho = Toninho;
