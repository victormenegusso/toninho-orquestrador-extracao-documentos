// JavaScript principal do Toninho
console.log('Toninho carregado!');

// Funções utilitárias
const Toninho = {
    // Fazer requisição à API
    async api(endpoint, options = {}) {
        const response = await fetch(`/api/v1${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        return response.json();
    },

    // Mostrar notificação
    notify(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // TODO: Implementar sistema de notificações visuais
    }
};

// Exportar para uso global
window.Toninho = Toninho;
