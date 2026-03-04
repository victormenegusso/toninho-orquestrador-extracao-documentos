# ADR-006: Frontend HTMX + Alpine.js vs SPA Framework

**Status**: Aceito
**Data**: 2025
**Contexto**: Interface de monitoramento e CRUD para uso interno, single-user, sem requisito de UX complexo.

---

## Decisão

Usar **HTMX + Alpine.js + TailwindCSS** renderizado server-side via **Jinja2** (FastAPI).

## Alternativas Rejeitadas

| Alternativa | Motivo rejeição |
|---|---|
| React / Next.js | Overhead de build, complexidade desnecessária para uso interno |
| Vue.js / Nuxt | Idem — separação de repos ou monorepo mais complexo |
| Django Admin | Stack Python diferente, menos flexibilidade de customização |

## Razões

- **HTMX**: requisições parciais sem JavaScript customizado; formulários e atualizações dinâmicas com HTML puro.
- **Alpine.js**: reatividade local (dropdowns, modais) sem bundle step.
- **TailwindCSS**: utilitário CSS, sem CSS custom; build via `package.json`.
- **Jinja2 server-side**: templates no mesmo processo FastAPI, sem API separada para o frontend.

## Consequências

- Sem Node.js em runtime (apenas build do Tailwind).
- Frontend fortemente acoplado ao backend → mudanças de schema afetam templates.
- Não adequado se o frontend precisar ser consumido por apps mobile ou APIs externas.
