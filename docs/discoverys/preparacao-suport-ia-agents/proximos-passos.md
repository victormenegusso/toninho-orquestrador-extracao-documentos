# Próximos Passos — Preparação para Suporte a IA Agents

> Este documento descreve os próximos passos após a preparação do projeto para trabalhar com o GitHub Copilot coding agent e boas práticas de IA assistida.

## Contexto

Os seguintes arquivos foram adicionados ao projeto para habilitar e otimizar o uso do Copilot:

| Arquivo | Propósito |
|---------|-----------|
| `.github/copilot-instructions.md` | Instruções globais do Copilot para o repositório |
| `.github/workflows/copilot-setup-steps.yml` | Setup do ambiente para o Copilot agent |
| `.github/instructions/*.instructions.md` | Instruções específicas por tipo de arquivo (testes, API, models/schemas, E2E) |
| `AGENTS.md` | Instruções para agentes de IA |
| `CONTRIBUTING.md` | Guia de contribuição |
| `SECURITY.md` | Política de segurança |
| `.github/CODEOWNERS` | Ownership de código |
| `.vscode/` | Extensões do Copilot + formatador Ruff |

---

## 1. Testar o Workflow `copilot-setup-steps.yml`

O primeiro passo é validar que o ambiente automatizado do Copilot agent funciona corretamente.

**Como fazer:**

1. Ir ao GitHub → aba **Actions** → workflow **"Copilot Setup Steps"**
2. Clicar em **"Run workflow"** para disparar manualmente
3. Verificar que **todas as etapas completam sem erros**
4. Se houver falhas, editar o arquivo `.github/workflows/copilot-setup-steps.yml` e re-executar

> **Por que isso importa?** Este workflow garante que o Copilot agent consegue instalar dependências, configurar o banco de dados e preparar o ambiente automaticamente antes de fazer qualquer alteração no código.

---

## 2. Usar o Copilot para Identificar Technical Debt

Aproveitar o Copilot para mapear áreas do projeto que precisam de atenção.

**Como fazer:**

1. Abrir o **Copilot Chat** em [github.com/copilot](https://github.com/copilot)
2. Selecionar o modo **"Ask"** e apontar para este repositório
3. Usar o seguinte prompt:

```
What technical debt exists in this project? Give me a prioritized list
of up to 5 areas we need to focus on. For each, describe the problem
and its consequences.
```

4. Revisar as áreas identificadas pelo Copilot
5. Para cada área, criar uma issue usando:

```
/create-issue

Create a GitHub issue to address the first of the problem areas
that you identified. If the problem area requires substantial work,
create one main issue and then sub-issues.
```

6. Repetir para cada área prioritária identificada

---

## 3. Atribuir Issues ao Copilot Coding Agent

Com issues criadas, podemos delegar trabalho diretamente ao Copilot.

**Como fazer:**

1. Abrir uma issue que tenha **acceptance criteria claros** e bem definidos
2. Clicar em **"Assign to Copilot"** → **"Assign"**
3. Aguardar o Copilot criar um **draft PR** com as mudanças propostas
4. Revisar as mudanças no PR — verificar código, testes e aderência aos padrões
5. Usar **`@copilot`** nos comentários do PR para pedir ajustes específicos
6. Quando satisfeito com as mudanças, clicar em **"Ready for review"** e fazer merge

> **Dica:** Issues com critérios de aceitação objetivos e específicos geram PRs de maior qualidade.

---

## 4. Refinar as Instruções do Copilot

As instruções são um documento vivo — devem evoluir com o projeto.

**Quando atualizar:**

- Se o Copilot gerar código que **não segue os padrões do projeto** → atualizar `.github/copilot-instructions.md`
- Se padrões específicos por **tipo de arquivo** não estiverem sendo seguidos → atualizar os arquivos em `.github/instructions/`
- Se o `AGENTS.md` precisar de **mais anti-patterns** ou contexto → atualizá-lo
- Após cada ciclo de uso do Copilot, avaliar a qualidade e ajustar

**Exemplos de refinamento:**

- Adicionar exemplos de código que o Copilot deve seguir
- Listar padrões que o Copilot está errando consistentemente
- Incluir decisões arquiteturais recentes

> **Dica:** As instruções devem evoluir com o projeto. Cada PR do Copilot que precisou de ajustes manuais é uma oportunidade de melhorar as instruções.

---

## 5. Configurar Branch Rulesets de Segurança

Garantir que nenhum código — humano ou gerado por IA — vá para `main` sem revisão.

**Como fazer:**

1. No GitHub: **Settings** → **Rules** → **Rulesets**
2. Criar uma nova regra para a branch `main` que exija:
   - **Pull request antes de merge** (obrigatório)
   - **Pelo menos 1 aprovação** de um usuário com write access
3. Salvar a regra

> **Por que isso importa?** Isso garante que nenhum código do Copilot vai para a branch principal sem review humano, mantendo a qualidade e segurança do projeto.

---

## 6. Explorar MCP (Model Context Protocol)

O MCP permite que o Copilot acesse contexto externo além do repositório.

**O que já temos:**

- O Copilot já possui o **GitHub MCP server embutido**, com acesso completo ao contexto do repositório

**O que considerar adicionar:**

- **Ferramentas de planejamento** — Notion, Figma, Linear
- **Documentação atualizada** de bibliotecas utilizadas (FastAPI, SQLAlchemy, etc.)
- **APIs internas** que o projeto consome

**Como configurar:**

- No GitHub: **Settings** → **Copilot** → **MCP servers**
- Adicionar os servers relevantes para o contexto do projeto

---

## 7. Criar Custom Agents Especializados (Avançado)

Para necessidades mais específicas, criar agentes focados em áreas do projeto.

**Sugestões de agentes:**

| Agente | Foco | Benefício |
|--------|------|-----------|
| **Testing specialist** | Cobertura de testes | Garantir que novos PRs incluam testes adequados |
| **Documentation expert** | Manter docs atualizados | Documentação sempre sincronizada com o código |
| **Security reviewer** | Práticas de segurança | Identificar vulnerabilidades antes do merge |

**Onde configurar:**

- Documentar em `.github/copilot-agents/` ou via **Copilot Extensions**
- Cada agente pode ter suas próprias instruções e escopo de atuação

---

## 8. Iterar e Medir Resultados

O uso do Copilot deve ser continuamente avaliado e otimizado.

**Após cada ciclo de uso:**

- **Avaliar qualidade** dos PRs gerados — quantos precisaram de ajustes?
- **Medir tempo economizado** — comparar com o tempo que levaria manualmente
- **Identificar lacunas** — onde o Copilot precisa de mais contexto?
- **Atualizar instruções** conforme necessário com base nos aprendizados

**Métricas sugeridas:**

- Número de PRs aceitos vs. rejeitados
- Quantidade de iterações necessárias por PR
- Tempo médio entre abertura e merge de PRs do Copilot

---

## 9. Checklist de Manutenção Contínua

Para manter a eficácia do Copilot ao longo do tempo:

- [ ] Manter `copilot-instructions.md` atualizado quando a stack mudar
- [ ] Atualizar `copilot-setup-steps.yml` quando novas dependências forem adicionadas
- [ ] Revisar instruções path-specific quando novos padrões forem adotados
- [ ] Atualizar `AGENTS.md` com novos anti-patterns descobertos
- [ ] Manter `CODEOWNERS` atualizado com novos contribuidores
- [ ] Revisar `CONTRIBUTING.md` quando processos de contribuição mudarem
- [ ] Validar `SECURITY.md` quando novas políticas de segurança forem definidas

---

## Referências

- [GitHub Copilot coding agent — Documentação oficial](https://docs.github.com/en/copilot/using-github-copilot/using-the-copilot-coding-agent)
- [Customizing Copilot for your repository](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)
- [Model Context Protocol (MCP)](https://docs.github.com/en/copilot/customizing-copilot/extending-the-functionality-of-github-copilot-in-your-organization)
