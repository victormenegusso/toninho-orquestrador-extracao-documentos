# Casos de Uso — Testes E2E de Frontend
**Projeto Toninho — Sistema de Extração de Documentos**
*Versão 1.0 · Março 2026*

---

## Contexto

Este documento mapeia os **casos de uso (UC)** que os testes E2E com Playwright devem cobrir. Cada UC representa um fluxo completo que um usuário real executaria e que **depende de JavaScript rodando no browser** (Alpine.js, HTMX ou SSE). Fluxos puramente server-side já estão cobertos por testes de API/integração.

### Critérios de seleção

| Critério | Justificativa |
|---|---|
| Envolve HTMX com swap de fragmentos | Precisa de browser real para validar que o DOM foi atualizado |
| Envolve Alpine.js com estado reativo | `x-model`, `x-show`, `x-data` só executam em runtime JS |
| Envolve SSE (Server-Sent Events) | `EventSource` é API de browser |
| Envolve polling automático | `hx-trigger="every Xs"` precisa de tempo real |
| Envolve diálogos de confirmação | `hx-confirm` depende de interceptação do browser |
| É fluxo crítico para o negócio | Falha silenciosa aqui impacta diretamente o usuário |

---

## Legenda de prioridade

| Nível | Significado |
|---|---|
| 🔴 P0 — Crítico | Fluxo principal do sistema; sem ele o produto não funciona |
| 🟡 P1 — Importante | Funcionalidade relevante usada com frequência |
| 🟢 P2 — Desejável | Melhoria de UX ou cenário de borda |

---

## UC-01: Criar processo com configuração completa
**Prioridade:** 🔴 P0

### Descrição
O usuário acessa `/processos/novo`, preenche o formulário Alpine.js com dados do processo e da configuração, e submete via `fetch()`. O fluxo envolve o componente `processoForm()` com validação client-side, campos condicionais e submissão assíncrona em duas etapas (processo + configuração).

### Pré-condições
- Nenhum processo existente com o mesmo nome.

### Fluxo principal
1. Navegar para `/processos/novo`.
2. Preencher **nome** (`x-model="form.nome"`).
3. Preencher **descrição** (`x-model="form.descricao"`).
4. Selecionar **status** = `ativo`.
5. Expandir seção de configuração.
6. Preencher **URLs** (uma por linha no `<textarea x-model="config.urls">`).
7. Definir **timeout** (`x-model.number="config.timeout"`).
8. Definir **max_retries** (`x-model.number="config.max_retries"`).
9. Selecionar **formato_saida** = `multiplos_arquivos`.
10. Selecionar **metodo_extracao** = `html2text`.
11. Clicar em "Criar Processo" (`@click="submit(true)"`).
12. Verificar redirecionamento para a página de detalhe do processo criado.

### O que o teste valida
- Binding bidirecional Alpine.js (`x-model`) nos campos de texto, número, select e textarea.
- Submissão assíncrona via `fetch()` (POST `/api/v1/processos` + POST configuração).
- Redirecionamento após criação bem-sucedida.
- Dados persistidos corretamente (validar na página de detalhe).

### Variações a cobrir
| Variação | O que muda |
|---|---|
| **UC-01a** Agendamento recorrente | Selecionar `agendamento_tipo = recorrente` → campo cron aparece (`x-show`), preencher expressão cron |
| **UC-01b** Agendamento one_time | Selecionar `agendamento_tipo = one_time` → campo datetime aparece (`x-show`), preencher data/hora |
| **UC-01c** Método Docling | Selecionar `metodo_extracao = docling` → warning amarelo aparece (`x-show`) |
| **UC-01d** Usar browser | Marcar checkbox `use_browser` → validar que o valor é enviado |

---

## UC-02: Validação do formulário de processo
**Prioridade:** 🟡 P1

### Descrição
O usuário tenta submeter o formulário com dados inválidos. O Alpine.js exibe erros inline abaixo dos campos e/ou um `globalError` no topo, **sem recarregar a página**.

### Fluxo principal
1. Navegar para `/processos/novo`.
2. Deixar o campo **nome** vazio.
3. Clicar "Criar Processo".
4. Verificar que a mensagem de erro aparece abaixo do campo nome.
5. Verificar que nenhuma request HTTP foi disparada.

### Variações a cobrir
| Variação | Campo/Cenário |
|---|---|
| **UC-02a** Nome vazio | Erro inline no campo nome |
| **UC-02b** URLs vazias (com config) | Erro inline no campo URLs |
| **UC-02c** Timeout fora do range | Valor < 1 ou > 86400 → erro inline |
| **UC-02d** Cron inválido (recorrente) | Expressão cron malformada → erro inline |
| **UC-02e** Erro do servidor (409 conflito) | Nome duplicado → exibe `globalError` no topo do form |

### O que o teste valida
- Exibição de erros inline via Alpine.js (`errors` object).
- Exibição de `globalError` para erros de servidor.
- Que a página **não recarrega** durante validação client-side.
- Que o `fetch()` **não é chamado** quando há erros de validação.

---

## UC-03: Editar processo existente
**Prioridade:** 🟡 P1

### Descrição
O usuário acessa `/processos/{id}/editar`, onde o formulário Alpine.js é pré-populado com os dados existentes via `initialProcesso` e `initialConfig`. O fluxo é similar ao UC-01 mas usando PUT em vez de POST.

### Pré-condições
- Processo existente com configuração.

### Fluxo principal
1. Navegar para `/processos/{id}/editar`.
2. Verificar que todos os campos estão pré-populados (nome, descrição, status, URLs, timeout, etc.).
3. Alterar o **nome** do processo.
4. Alterar o **timeout** da configuração.
5. Clicar em "Salvar" (`@click="submit(true)"`).
6. Verificar redirecionamento para a página de detalhe com dados atualizados.

### O que o teste valida
- Pré-populaçao correta do Alpine.js via `x-init="init()"`.
- Binding bidirecional mantido após edição.
- Submissão via PUT (não POST).
- Dados atualizados refletidos na página de detalhe.

---

## UC-04: Buscar e filtrar processos (HTMX)
**Prioridade:** 🔴 P0

### Descrição
Na listagem de processos (`/processos`), o usuário digita no campo de busca ou altera o filtro de status. O HTMX faz uma request parcial com debounce de 500ms e substitui o conteúdo da tabela **sem recarregar a página**.

### Pré-condições
- Pelo menos 3 processos existentes com nomes e status distintos.

### Fluxo principal
1. Navegar para `/processos`.
2. Verificar que a tabela exibe todos os processos.
3. Digitar parte do nome de um processo no campo de busca.
4. Aguardar 500ms (debounce de `hx-trigger="keyup changed delay:500ms"`).
5. Verificar que a tabela foi atualizada via HTMX (`hx-target="#processos-table"`).
6. Verificar que apenas processos correspondentes aparecem.

### Variações a cobrir
| Variação | Interação |
|---|---|
| **UC-04a** Filtro por status | Selecionar status no dropdown → tabela atualiza via `hx-trigger="change"` |
| **UC-04b** Busca + filtro combinados | Digitar texto + selecionar status → `hx-include` envia ambos os parâmetros |
| **UC-04c** Busca sem resultados | Digitar termo inexistente → tabela exibe estado vazio |
| **UC-04d** Limpar busca | Apagar texto → tabela volta a exibir todos os processos |

### O que o teste valida
- Request HTMX parcial (GET `/processos/search`) disparada após debounce.
- Swap correto do conteúdo: `hx-swap="innerHTML"` no `#processos-table`.
- Parâmetros enviados corretamente (`search`, `status` via `hx-include`).
- Indicador de loading (`hx-indicator="#search-indicator"`).

---

## UC-05: Executar processo a partir da listagem
**Prioridade:** 🔴 P0

### Descrição
O usuário clica no botão de executar (ícone play) em uma linha da tabela de processos. O HTMX exibe um diálogo de confirmação nativo (`hx-confirm`) e, ao confirmar, faz POST para criar uma nova execução.

### Pré-condições
- Processo existente com configuração válida.

### Fluxo principal
1. Navegar para `/processos`.
2. Localizar o processo na tabela.
3. Clicar no botão "Executar agora" (ícone play).
4. Aceitar o diálogo de confirmação: *"Executar processo 'X' agora?"*.
5. Verificar que a request `POST /api/v1/processos/{id}/execucoes` foi enviada.
6. Verificar feedback visual (toast de sucesso ou atualização da UI).

### Variações a cobrir
| Variação | O que muda |
|---|---|
| **UC-05a** Cancelar confirmação | Clicar "Cancelar" no diálogo → nenhuma request enviada |
| **UC-05b** Executar da página de detalhe | Botão "Executar Agora" em `/processos/{id}` → mesmo fluxo |

### O que o teste valida
- `hx-confirm` exibe diálogo nativo do browser.
- POST é enviado somente após confirmação.
- `hx-swap="none"` — o DOM da tabela não é alterado pelo response direto.
- Feedback visual ao usuário (flash message ou toast).

---

## UC-06: Deletar processo
**Prioridade:** 🟡 P1

### Descrição
O usuário clica no botão de deletar (ícone lixeira) na tabela de processos. Após confirmação, o HTMX faz DELETE e remove a linha da tabela com animação.

### Fluxo principal
1. Navegar para `/processos`.
2. Clicar no botão deletar do processo alvo.
3. Aceitar o diálogo: *"Deletar o processo 'X'? Esta ação não pode ser desfeita."*
4. Verificar que a request `DELETE /api/v1/processos/{id}` foi enviada.
5. Verificar que a linha desaparece da tabela (`hx-swap="outerHTML swap:0.5s"`).

### O que o teste valida
- `hx-confirm` com mensagem de alerta irreversível.
- DELETE via HTMX.
- Remoção animada da row (`hx-target="#processo-row-{id}"` + `swap:0.5s`).
- A linha não reaparece após refresh.

---

## UC-07: Dashboard com polling automático
**Prioridade:** 🔴 P0

### Descrição
O dashboard (`/dashboard`) possui dois mecanismos de polling HTMX independentes: cards de estatísticas atualizando a cada 5s e execuções ativas atualizando a cada 3s. O teste valida que ambos funcionam e exibem dados atualizados.

### Fluxo principal
1. Navegar para `/dashboard`.
2. Verificar que os 4 cards de estatísticas estão visíveis (Total de Execuções, Execuções Ativas, Concluídas, Taxa de Sucesso).
3. Verificar que a seção de execuções ativas exibe cards ou mensagem de "nenhuma execução ativa".
4. Aguardar ~5s e interceptar a request `GET /dashboard/stats`.
5. Verificar que os cards de estatísticas foram atualizados (swap `outerHTML`).
6. Aguardar ~3s e interceptar a request `GET /execucoes/ativas`.
7. Verificar que a seção de execuções ativas foi atualizada (swap `innerHTML`).

### O que o teste valida
- Polling HTMX: `hx-trigger="every 5s"` no `#stats-cards`.
- Polling HTMX: `hx-trigger="every 3s"` no `#execucoes-ativas`.
- Dados numéricos atualizados nos cards sem recarregar a página.
- Quick actions (botões de atalho) levam às páginas corretas.

---

## UC-08: Acompanhar execução com logs em tempo real (SSE)
**Prioridade:** 🔴 P0

### Descrição
O usuário abre o detalhe de uma execução em andamento (`/execucoes/{id}`). A página conecta via **Server-Sent Events** ao endpoint de logs e exibe mensagens em tempo real no terminal estilizado. A barra de progresso atualiza via polling HTMX a cada 2s.

### Pré-condições
- Execução com status `em_execucao`.

### Fluxo principal
1. Navegar para `/execucoes/{id}` (execução em andamento).
2. Verificar que o container de logs exibe "Conectando ao stream de logs...".
3. Verificar que a conexão SSE é estabelecida (`EventSource` para `/api/v1/execucoes/{id}/logs/stream`).
4. Verificar que mensagens de log aparecem no terminal com cores corretas:
   - `INFO` → azul (`text-blue-400`)
   - `WARNING` → amarelo (`text-yellow-400`)
   - `ERROR` → vermelho (`text-red-400`)
   - `DEBUG` → cinza (`text-gray-400`)
5. Verificar que a barra de progresso atualiza automaticamente (`hx-trigger="every 2s"`).
6. Verificar que o número de páginas processadas incrementa.

### Variações a cobrir
| Variação | O que muda |
|---|---|
| **UC-08a** Filtro de nível | Selecionar "ERROR" no dropdown → apenas logs de erro são exibidos |
| **UC-08b** Auto-scroll | Desmarcar checkbox "Auto-scroll" → container para de rolar automaticamente |
| **UC-08c** Buffer overflow | Mais de 1000 logs → logs antigos são removidos (FIFO) |
| **UC-08d** Desconexão SSE | Stream encerra → mensagem de desconexão ou reconexão graceful |

### O que o teste valida
- Conexão SSE estabelecida e recebendo dados.
- Parsing JSON dos eventos e renderização com cores por nível.
- Auto-scroll funcional e seu toggle.
- Filtro de nível operando corretamente.
- Polling da barra de progresso (`GET /execucoes/{id}/progress`) a cada 2s.
- Limite de 1000 linhas no buffer.

---

## UC-09: Pausar, retomar e cancelar execução
**Prioridade:** 🔴 P0

### Descrição
O usuário gerencia o ciclo de vida de uma execução através dos botões condicionais na página de detalhe. Os botões aparecem/desaparecem conforme o status da execução, usando renderização condicional do Jinja2.

### Pré-condições
- Execução com status `em_execucao`.

### Fluxo principal — Pausar
1. Navegar para `/execucoes/{id}` (execução em andamento).
2. Verificar que o botão **"Pausar"** está visível (amarelo).
3. Verificar que o botão **"Cancelar"** está visível (vermelho).
4. Verificar que o botão **"Retomar"** **não** está visível.
5. Clicar "Pausar" → aceitar confirmação *"Pausar esta execução?"*.
6. Verificar request `POST /api/v1/execucoes/{id}/pausar`.
7. Recarregar a página e verificar que o status mudou para `pausado`.

### Fluxo principal — Retomar
8. Verificar que agora o botão **"Retomar"** está visível (verde).
9. Verificar que o botão **"Pausar"** **não** está visível.
10. Clicar "Retomar".
11. Verificar request `POST /api/v1/execucoes/{id}/retomar`.
12. Recarregar e verificar status `em_execucao`.

### Fluxo principal — Cancelar
13. Clicar "Cancelar" → aceitar confirmação *"Tem certeza que deseja cancelar esta execução?"*.
14. Verificar request `POST /api/v1/execucoes/{id}/cancelar`.
15. Recarregar e verificar status `cancelado`.
16. Verificar que **nenhum** botão de controle está visível (nem Pausar, nem Retomar, nem Cancelar).

### O que o teste valida
- Renderização condicional dos botões baseada no status Jinja2.
- `hx-confirm` com mensagens distintas para cada ação.
- `hx-swap="none"` — nenhuma alteração direta no DOM pela response.
- Transições de estado: `em_execucao → pausado → em_execucao → cancelado`.
- Botões desaparecem corretamente em estados terminais (`concluido`, `falhou`, `cancelado`).

---

## UC-10: Listar e filtrar execuções
**Prioridade:** 🟡 P1

### Descrição
Na listagem de execuções (`/execucoes`), o usuário filtra por status usando os links de filtro (não é HTMX — é navegação com query param). O teste valida que os filtros funcionam e que os badges de status têm as cores corretas.

### Fluxo principal
1. Navegar para `/execucoes`.
2. Verificar que a tabela exibe execuções com colunas: ID, Status, Páginas, Taxa de Erro, Início, Duração.
3. Clicar no filtro "em_execucao".
4. Verificar que a URL muda para `/execucoes?status=em_execucao`.
5. Verificar que apenas execuções com status `em_execucao` aparecem.
6. Clicar em "Todos" para limpar o filtro.

### O que o teste valida
- Filtros por query param funcionam.
- Badges de status com cores corretas: verde (concluido), azul (em_execucao), vermelho (falhou), amarelo (pausado), cinza (cancelado).
- Paginação funcional.
- Link "Ver detalhes" leva à página correta.

---

## UC-11: Navegar pelas páginas extraídas
**Prioridade:** 🟡 P1

### Descrição
O usuário acessa a lista de páginas extraídas de uma execução (`/execucoes/{id}/paginas`), busca por URL e filtra por status usando HTMX com debounce.

### Pré-condições
- Execução concluída com páginas extraídas (sucesso, falhou, ignorado).

### Fluxo principal
1. Navegar para `/execucoes/{id}/paginas`.
2. Verificar que o grid exibe cards de páginas com URL, status e tamanho.
3. Digitar parte de uma URL no campo de busca.
4. Aguardar debounce (500ms) do `hx-trigger="keyup changed delay:500ms"`.
5. Verificar que o grid foi atualizado via HTMX (`hx-target="#paginas-grid"`).
6. Verificar que apenas páginas com URL correspondente aparecem.

### Variações a cobrir
| Variação | O que muda |
|---|---|
| **UC-11a** Filtro por status | Selecionar "Sucesso" → apenas cards verdes |
| **UC-11b** Busca + filtro | Combinar texto + status → `hx-include` envia ambos |
| **UC-11c** Preview de página | Clicar "Preview" em um card → `openPreview(id)` abre modal com conteúdo |
| **UC-11d** Download de página | Clicar "Baixar" → arquivo é baixado |

### O que o teste valida
- Request HTMX parcial: `GET /paginas/search?execucao_id={id}&search=...&status=...`.
- Swap do grid sem recarregar a página.
- Cards com badges de status coloridos (verde/vermelho/cinza).
- Modal de preview funcional.
- Link de download aponta para `/api/v1/paginas/{id}/download`.

---

## UC-12: Sistema de notificações (toasts e flash messages)
**Prioridade:** 🟢 P2

### Descrição
O sistema exibe feedback visual em duas formas: **flash messages** server-side (renderizadas pelo Jinja2 com Alpine.js transitions) e **toasts** client-side (disparados por eventos HTMX `htmx:responseError` e `htmx:timeout`). O teste valida ambos.

### Fluxo principal — Flash Messages
1. Realizar uma ação que gere flash message (ex: criar processo com sucesso).
2. Verificar que o alert aparece no topo com cor correta (verde para sucesso).
3. Verificar animação de entrada (`x-transition`).
4. Clicar no botão de fechar (`@click="show = false"`).
5. Verificar que o alert desaparece com animação de saída.

### Fluxo principal — Toasts de Erro HTMX
6. Simular uma falha de rede (interceptar request e retornar erro).
7. Verificar que o toast de erro aparece (evento `htmx:responseError`).
8. Verificar cor vermelha e mensagem de erro.

### O que o teste valida
- Alpine.js `x-show` + `x-transition` nas flash messages.
- Botão de fechar (`@click="show = false"`).
- Toasts disparados por eventos HTMX globais.
- Cores corretas por tipo: success (verde), error (vermelho), warning (amarelo), info (azul).

---

## UC-13: Navegação geral e sidebar
**Prioridade:** 🟢 P2

### Descrição
A sidebar fixa oferece navegação entre as 3 seções principais. O `hx-boost="true"` no `<body>` transforma links normais em requests HTMX parciais, proporcionando navegação sem recarregar a página inteira.

### Fluxo principal
1. Acessar `/dashboard`.
2. Clicar em "Processos" na sidebar → verificar que navega para `/processos`.
3. Clicar em "Execuções" na sidebar → verificar que navega para `/execucoes`.
4. Clicar em "Dashboard" na sidebar → verificar que volta para `/dashboard`.
5. Verificar que o link ativo está destacado visualmente.

### O que o teste valida
- `hx-boost="true"` intercepta a navegação corretamente.
- Sidebar mantém estado visual do link ativo.
- Conteúdo principal é atualizado sem full page reload.

---

## UC-14: Tratamento de erros de rede (HTMX)
**Prioridade:** 🟢 P2

### Descrição
Quando uma request HTMX falha (timeout, 500, etc.), o sistema deve exibir feedback visual e não deixar a UI em estado inconsistente.

### Fluxo principal
1. Navegar para `/processos`.
2. Interceptar requests HTMX e simular erro 500.
3. Digitar no campo de busca para disparar request HTMX.
4. Verificar que o toast de erro aparece (listener `htmx:responseError` no `base.html`).
5. Verificar que a tabela mantém o conteúdo anterior (não fica vazia).

### Variações a cobrir
| Variação | Cenário |
|---|---|
| **UC-14a** Timeout HTMX | Request demora além do timeout configurado → evento `htmx:timeout` |
| **UC-14b** Erro no formulário Alpine | Servidor retorna 422 → Alpine exibe `globalError` |
| **UC-14c** Dashboard polling com erro | Polling falha → não quebra os polls seguintes |

### O que o teste valida
- Resiliência da UI a falhas de rede.
- Toast/notificação exibido sem intervenção do usuário.
- UI não fica em estado "travado" ou vazio após erro.
- Polling continua funcionando após erro pontual.

---

## Resumo — Matriz de Cobertura

| UC | Nome | Prioridade | Tecnologias Testadas |
|---|---|---|---|
| UC-01 | Criar processo com configuração | 🔴 P0 | Alpine.js (x-model, x-show, fetch), Jinja2 |
| UC-02 | Validação do formulário | 🟡 P1 | Alpine.js (errors, globalError) |
| UC-03 | Editar processo existente | 🟡 P1 | Alpine.js (init, x-model, fetch PUT) |
| UC-04 | Buscar e filtrar processos | 🔴 P0 | HTMX (hx-get, hx-trigger debounce, hx-include) |
| UC-05 | Executar processo | 🔴 P0 | HTMX (hx-post, hx-confirm) |
| UC-06 | Deletar processo | 🟡 P1 | HTMX (hx-delete, hx-confirm, hx-swap animation) |
| UC-07 | Dashboard com polling | 🔴 P0 | HTMX (hx-trigger every, polling duplo) |
| UC-08 | Logs em tempo real (SSE) | 🔴 P0 | SSE (EventSource), Alpine.js, HTMX polling |
| UC-09 | Pausar/Retomar/Cancelar execução | 🔴 P0 | HTMX (hx-post, hx-confirm), Jinja2 condicional |
| UC-10 | Listar e filtrar execuções | 🟡 P1 | Jinja2 (query params), navegação |
| UC-11 | Páginas extraídas | 🟡 P1 | HTMX (hx-get debounce, hx-include), modal JS |
| UC-12 | Notificações (toasts/flash) | 🟢 P2 | Alpine.js (x-show, x-transition), HTMX events |
| UC-13 | Navegação e sidebar | 🟢 P2 | HTMX (hx-boost) |
| UC-14 | Erros de rede | 🟢 P2 | HTMX (responseError, timeout), Alpine.js |

### Distribuição

- **P0 (Crítico):** 5 UCs — cobrem os fluxos primários do sistema
- **P1 (Importante):** 5 UCs — cobrem CRUD completo e listagens
- **P2 (Desejável):** 4 UCs — cobrem edge cases e polimento de UX

---

## Mapeamento para arquivos de teste

```
tests/e2e/
├── conftest.py                         # fixtures: live_server, page, authenticated_page
├── test_uc01_criar_processo.py         # UC-01 + UC-01a/b/c/d
├── test_uc02_validacao_formulario.py   # UC-02 + UC-02a/b/c/d/e
├── test_uc03_editar_processo.py        # UC-03
├── test_uc04_busca_processos.py        # UC-04 + UC-04a/b/c/d
├── test_uc05_executar_processo.py      # UC-05 + UC-05a/b
├── test_uc06_deletar_processo.py       # UC-06
├── test_uc07_dashboard_polling.py      # UC-07
├── test_uc08_logs_sse.py              # UC-08 + UC-08a/b/c/d
├── test_uc09_ciclo_vida_execucao.py   # UC-09
├── test_uc10_listagem_execucoes.py    # UC-10
├── test_uc11_paginas_extraidas.py     # UC-11 + UC-11a/b/c/d
├── test_uc12_notificacoes.py          # UC-12
├── test_uc13_navegacao.py             # UC-13
└── test_uc14_erros_rede.py            # UC-14 + UC-14a/b/c
```

---

## Ordem de implementação recomendada

| Fase | UCs | Justificativa |
|---|---|---|
| **Fase 0** | Infra (`conftest.py`, fixtures, `pyproject.toml`) | Base para todos os testes |
| **Fase 1** | UC-07, UC-04 | Validam HTMX polling e busca — são os mais independentes e rápidos de implementar |
| **Fase 2** | UC-01, UC-02, UC-03 | Formulário Alpine.js — o componente mais complexo do frontend |
| **Fase 3** | UC-05, UC-06, UC-09 | Ações destrutivas com confirmação + ciclo de vida |
| **Fase 4** | UC-08 | SSE — requer setup mais elaborado |
| **Fase 5** | UC-10, UC-11, UC-12, UC-13, UC-14 | Complementares — P1/P2 |
