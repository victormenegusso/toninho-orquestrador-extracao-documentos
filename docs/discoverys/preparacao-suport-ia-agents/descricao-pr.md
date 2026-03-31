# Pull Request — Preparação do Repositório para Suporte a IA/Copilot Agents

> **Branch:** `feature/agent-use` → `main`
> **Arquivos alterados:** 12 (541 adições, 4 remoções)

---

## 📋 Descrição

Este PR adiciona toda a infraestrutura de documentação e configuração necessária para que o GitHub Copilot (Chat, Agent e Coding Agent) compreenda e interaja de forma inteligente com o repositório **Toninho — Orquestrador de Extração de Documentos**.

Nenhum arquivo de código-fonte foi alterado. Todas as mudanças são de documentação, instruções e configuração do ambiente de desenvolvimento.

## 🎯 Motivação

Com a evolução do GitHub Copilot — especialmente o **Copilot Coding Agent** e o **Copilot Chat com contexto de repositório** — é fundamental que os repositórios forneçam instruções claras para que a IA entenda:

- A arquitetura e stack do projeto
- As convenções de código e padrões adotados
- Como executar testes e validar mudanças
- Quem é responsável por cada parte do código

Seguindo as **best practices oficiais do GitHub Copilot**, este PR implementa todas as recomendações documentadas para melhorar a qualidade das sugestões e permitir que o Copilot Coding Agent opere de forma autônoma no repositório.

## 🔄 Mudanças

### Instruções do Copilot

| Arquivo | Descrição |
|---|---|
| `.github/copilot-instructions.md` | Instruções gerais do repositório — descreve a stack (FastAPI, SQLAlchemy, HTMX, Tailwind), a arquitetura do projeto, convenções de nomenclatura e padrões de código. Limitado a ~2 páginas conforme recomendado. |
| `.github/instructions/python-tests.instructions.md` | Instruções path-specific para testes Python — define padrões de escrita de testes unitários com `pytest`, fixtures, mocks e convenções de nomenclatura. |
| `.github/instructions/api-routes.instructions.md` | Instruções path-specific para rotas FastAPI — define padrões de endpoints, injeção de dependências, tratamento de erros e schemas de resposta. |
| `.github/instructions/models-schemas.instructions.md` | Instruções path-specific para models e schemas — define padrões de modelos SQLAlchemy, schemas Pydantic e convenções de relacionamento. |
| `.github/instructions/e2e-tests.instructions.md` | Instruções path-specific para testes E2E — define padrões de testes end-to-end com Playwright, Page Objects e boas práticas de seletores. |

### Ambiente do Copilot Agent

| Arquivo | Descrição |
|---|---|
| `.github/workflows/copilot-setup-steps.yml` | Workflow do GitHub Actions que configura o ambiente para o Copilot Coding Agent. Define o job `copilot-setup-steps` com instalação de dependências via Poetry, configuração do banco de dados de teste e execução de migrações Alembic. Garante que o agent consiga executar testes e validar mudanças automaticamente. |

### Documentação do Projeto

| Arquivo | Descrição |
|---|---|
| `AGENTS.md` | Instruções de alto nível para agentes de IA — explica a estrutura do projeto, como executar testes, como validar mudanças e quais são as regras de contribuição que o agent deve seguir. |
| `CONTRIBUTING.md` | Guia de contribuição para desenvolvedores humanos e agentes — descreve o fluxo de trabalho com branches, commits convencionais, processo de code review e padrões de qualidade. |
| `SECURITY.md` | Política de segurança do projeto — define como reportar vulnerabilidades e quais são as práticas de segurança adotadas. |

### Configuração do Repositório

| Arquivo | Descrição |
|---|---|
| `.github/CODEOWNERS` | Define a propriedade de código por diretório/arquivo — garante que PRs sejam automaticamente atribuídos aos revisores corretos e que o Copilot saiba quem consultar para cada área do projeto. |
| `.vscode/extensions.json` | Atualizado para recomendar a extensão do GitHub Copilot e remover a extensão do Black (substituído pelo Ruff). |
| `.vscode/settings.json` | Atualizado para configurar o Ruff como formatter padrão do Python, substituindo o Black. |

## ✅ Checklist

- [x] Arquivos criados seguem as best practices do GitHub Copilot
- [x] `copilot-instructions.md` não excede 2 páginas (~8KB)
- [x] `copilot-setup-steps.yml` tem job chamado `copilot-setup-steps`
- [x] Instruções path-specific usam glob patterns corretos (`applyTo`)
- [x] `AGENTS.md` está na raiz do repositório
- [x] `CONTRIBUTING.md` está na raiz do repositório
- [x] `SECURITY.md` está na raiz do repositório
- [x] `.github/CODEOWNERS` segue a sintaxe correta
- [x] Pre-commit hooks passam em todos os arquivos
- [x] Nenhum arquivo de código foi alterado
- [x] Nenhum teste existente foi modificado ou quebrado

## 📚 Referências

Toda a preparação foi baseada na documentação oficial do GitHub Copilot, armazenada como discovery neste repositório:

- [Improve a project for GitHub Copilot](./coding-agent/improve-a-project.md) — Guia principal de como preparar um repositório para o Copilot
- [Add repository instructions](./coding-agent/add-repository-instructions.md) — Como criar `copilot-instructions.md` e instruções path-specific
- [Get the best results from Copilot](./coding-agent/get-the-best-results.md) — Boas práticas para maximizar a qualidade das sugestões
- [Add organization instructions](./coding-agent/add-organization-instructions.md) — Instruções a nível de organização
- [Add personal instructions](./coding-agent/add-personal-instructions.md) — Instruções pessoais do desenvolvedor
- [Pilot the coding agent](./coding-agent/pilot-coding-agent.md) — Como pilotar e operar o Copilot Coding Agent
- [Plano de execução (prompt-plan)](./prompt-plan.md) — Plano usado para guiar a implementação deste PR

## 🧪 Como Testar

1. **Workflow do Copilot Agent** — Verificar que o workflow `copilot-setup-steps.yml` executa com sucesso no GitHub Actions (será acionado automaticamente pelo Copilot Coding Agent)
2. **Instruções path-specific** — Abrir um arquivo de teste (ex: `tests/test_*.py`) no VS Code e verificar que o Copilot recebe as instruções de `python-tests.instructions.md` ao gerar sugestões
3. **Instruções do repositório** — Usar o Copilot Chat no GitHub (na aba do repositório) e verificar que as instruções de `copilot-instructions.md` são consideradas nas respostas
4. **CODEOWNERS** — Criar um PR de teste e verificar que os revisores são atribuídos automaticamente conforme o `.github/CODEOWNERS`
5. **Extensões VS Code** — Abrir o projeto no VS Code e verificar que a extensão do Copilot é recomendada e o Ruff é o formatter padrão

## 📊 Impacto

- **Nenhuma mudança de código** — apenas adição de documentação e configuração
- **Zero risco de regressão** — nenhum teste ou funcionalidade existente é afetado
- **Ganho imediato** — Copilot passa a entender o projeto desde o primeiro uso
- **Habilitação do Coding Agent** — O repositório está pronto para receber issues e ter PRs gerados automaticamente pelo Copilot
- **Padronização** — Contribuidores (humanos e IA) têm um guia claro de como contribuir

---

> **Nota:** Este PR é a implementação do discovery documentado em `docs/discoverys/preparacao-suport-ia-agents/`. Consulte os arquivos de referência para entender o racional completo por trás de cada decisão.
