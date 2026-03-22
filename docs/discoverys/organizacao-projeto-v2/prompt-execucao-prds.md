# Prompt: Execução dos PRDs de Organização do Projeto Toninho

## Contexto

Você é um agente de IA responsável por implementar melhorias de organização no projeto **Toninho** (sistema de extração de documentos web). O projeto está localizado no diretório atual.

Antes de começar qualquer implementação, leia obrigatoriamente:

1. **Discovery**: `docs/discoverys/organizacao-projeto-v2/discovery.md` — contexto completo dos problemas e motivação
2. **Os 8 PRDs** listados abaixo — especificação detalhada de cada tarefa

## PRDs a Executar

Execute na ordem abaixo. Os PRDs da Fase 1 são independentes e podem ser executados em qualquer ordem. Fase 2 depende da Fase 1. Fase 3 é a última.

### Fase 1 (independentes entre si):

| PRD | Arquivo | Resumo |
|-----|---------|--------|
| PRD-ORG-001 | `docs/prd/PRD-ORG-001-Atualizacao-README.md` | Corrigir README.md na raiz: trocar Black/isort/flake8 por Ruff, corrigir links quebrados para docs, atualizar seção de API e testes |
| PRD-ORG-002 | `docs/prd/PRD-ORG-002-Documento-Arquitetura.md` | Criar `docs/ARCHITECTURE.md` com visão completa: estrutura de pastas, camadas, entidades, ciclo de vida, fluxos, stack |
| PRD-ORG-003 | `docs/prd/PRD-ORG-003-Documento-API.md` | Criar `docs/API.md` com referência completa dos endpoints REST (extrair do código real) |
| PRD-ORG-004 | `docs/prd/PRD-ORG-004-Documento-Testes.md` | Criar `docs/TESTING.md` com guia de testes, mapeamento E2E, gaps de cobertura |
| PRD-ORG-006 | `docs/prd/PRD-ORG-006-Otimizacao-Docker.md` | Otimizar docker-compose.yml: imagem compartilhada (1 build, 4 reusam) + docling cache |
| PRD-ORG-007 | `docs/prd/PRD-ORG-007-Teste-E2E-Formularios.md` | Criar teste Playwright anti-regressão para campos pré-preenchidos em formulários |

### Fase 2 (depende da Fase 1):

| PRD | Arquivo | Resumo |
|-----|---------|--------|
| PRD-ORG-005 | `docs/prd/PRD-ORG-005-Index-Documentacao.md` | Criar `docs/README.md` como índice de navegação de toda a documentação |

### Fase 3 (verificação final):

| PRD | Arquivo | Resumo |
|-----|---------|--------|
| PRD-ORG-008 | `docs/prd/PRD-ORG-008-Atualizacao-Backlog.md` | Verificar cada item do backlog no código e atualizar status |

## Regras de Execução

1. **Leia o PRD completo** antes de implementar cada tarefa
2. **Extraia informações do código real** — cada PRD indica quais arquivos ler na seção "Fontes de Informação"
3. **Não invente dados** — endpoints, campos, versões devem vir do código fonte
4. **Documentação em PT-BR**, código/comentários em EN
5. **README.md permanece na raiz** do projeto (`./README.md`), não mover para docs/
6. **Não altere lógica de negócio** — estas são mudanças de documentação, configuração e testes apenas
7. **Valide suas alterações**:
   - Para Docker (PRD-ORG-006): rode `docker compose config` para validar YAML
   - Para testes (PRD-ORG-007): verifique que o teste segue o padrão dos existentes em `tests/e2e/`
   - Para documentação: verifique que links relativos apontam para arquivos que existem
8. **Marque cada PRD como ✅ Implementado** no header do arquivo após concluir

## Commits

Faça um commit por PRD concluído, usando Conventional Commits:

```
docs: atualizar README com informações corretas de stack e links (PRD-ORG-001)
docs: criar documento de arquitetura ARCHITECTURE.md (PRD-ORG-002)
docs: criar documento de referência da API (PRD-ORG-003)
docs: criar guia de testes TESTING.md (PRD-ORG-004)
docs: criar índice de navegação da documentação (PRD-ORG-005)
fix: otimizar Docker build com imagem compartilhada (PRD-ORG-006)
test: criar teste E2E anti-regressão de formulários (PRD-ORG-007)
docs: atualizar backlog com status verificado (PRD-ORG-008)
```

## Resultado Esperado

Ao final da execução:

- `README.md` atualizado (sem referências a Black/isort/flake8, links corretos)
- `docs/ARCHITECTURE.md` criado (visão completa do sistema)
- `docs/API.md` criado (todos os endpoints documentados)
- `docs/TESTING.md` criado (guia + mapeamento E2E)
- `docs/README.md` criado (índice de navegação)
- `docker-compose.yml` otimizado (1 build, 4 reusam)
- `tests/e2e/test_uc14_formulario_pre_preenchido.py` criado
- `docs/demandas/backlog.md` atualizado (status verificado)
- 8 PRDs com status ✅ Implementado
