# Perguntas para Enriquecimento do Projeto Toninho

## 1. Arquitetura e Design

### 1.1 Arquitetura Geral
- **P1.1.1**: Qual será a arquitetura do sistema? Monolítico, microsserviços, ou algo híbrido? 
  - Resposta: Monolito, separar so back e front.

- **P1.1.2**: Como será a comunicação entre backend e frontend? REST puro, WebSockets para atualizações em tempo real, Server-Sent Events (SSE)? 
    - Resposta: REST para a maioria das operações, WebSockets ou SSE para atualizações em tempo real do progresso dos processos.

- **P1.1.3**: O sistema terá camadas bem definidas (controller, service, repository)? Qual padrão arquitetural pretende seguir?
    - Resposta: Sim, mas eu nunca trabalhei com python, então não sei qual é o padrão mais utilizado. Pode me sugerir algo? algo mais proximo de uma arquitetura hexagonal talvez? ou algo mais simples mesmo, tipo MVC?

### 1.2 Componentes do Sistema
- **P1.2.1**: Haverá um componente separado para processar as extrações (worker) ou será tudo no mesmo processo?
    - Resposta: Sim, havera um componete separado para processar as extrações, para garantir que a interface do usuário permaneça responsiva mesmo durante extrações longas. Esse componente pode ser implementado usando uma fila de tarefas (como Celery / rabbitMQ / REDIS) oque vc me recomenda?
- **P1.2.2**: Como será feito o gerenciamento de filas de tarefas? Terá fila de prioridade?
    - Resposta: Inicialmente nao teremos filas de prioridade.
- **P1.2.3**: Quantos processos de extração simultâneos o sistema deve suportar?
    - Resposta: Inicialmente, o sistema deve suportar pelo menos 5 processos de extração simultâneos por usuário, com a possibilidade de escalar para mais conforme necessário. ( podemos deixar como variavel de ambiente, default 5, e o usuario pode configurar conforme a necessidade )

## 2. Fluxo de Dados e Estados

### 2.1 Ciclo de Vida de um Processo
- **P2.1.1**: Quais são todos os estados possíveis de um processo? (Ex: Criado, Aguardando, Em Execução, Pausado, Concluído, Falhou, Cancelado)
    - Resposta: Criado, Aguardando, Em Execução, Pausado, Concluído, Falhou, Cancelado.
- **P2.1.2**: Um processo pode ser pausado e retomado? Se sim, como salvar o estado intermediário?
    - Resposta: Sim, mas se pausado de inicio ao retornar ele vai iniciar do zero, nao vamos salvar o estado intermediário, para simplificar a implementação inicial. Mas podemos considerar isso para uma versão futura.
- **P2.1.3**: É possível cancelar um processo em execução? Como garantir que recursos sejam liberados corretamente?
    - Resposta: Sim, o usuário pode cancelar um processo em execução. Para garantir que os recursos sejam liberados corretamente, o sistema deve implementar um mecanismo de interrupção para os processos de extração, como sinalização de cancelamento e limpeza de recursos alocados (threads, conexões, arquivos temporários).

### 2.2 Dados Extraídos
- **P2.2.1**: Onde os dados extraídos serão armazenados? Sistema de arquivos local, S3, banco de dados?
    - Resposta: A ideia é usar uma interface para no futuro ir plugando diferentes tipos de armazenamento, mas inicialmente vamos salvar os arquivos markdown gerados no sistema de arquivos local, em uma pasta configurável (por exemplo, "output/"). O caminho para essa pasta pode ser definido nas configurações do processo de extração. Para dados estruturados ou logs, podemos usar o banco de dados SQLite para armazenar metadados e informações sobre as extrações.
- **P2.2.2**: Haverá versionamento dos dados extraídos? Se extrair o mesmo site duas vezes, mantém histórico?
    - Resposta: Inicialmente, não teremos versionamento dos dados extraídos. Se o usuário extrair o mesmo site duas vezes, o sistema pode sobrescrever os arquivos existentes ou criar uma nova versão com um sufixo de timestamp para evitar perda de dados. Podemos considerar a implementação de um sistema de versionamento mais robusto para uma versão futura, onde cada extração gera uma nova versão dos dados e mantém um histórico completo.
   
- **P2.2.3**: Qual o tamanho máximo esperado de dados por extração? GB? TB?
    - Resposta: O tamanho pode ser setado via variavel de ambiente, mas inicialmente podemos definir um limite de 1GB por extração para evitar sobrecarga do sistema. Esse limite pode ser ajustado conforme a necessidade e a capacidade do ambiente de execução.
- **P2.2.4**: Os arquivos markdown gerados terão alguma estrutura padrão? Metadados no cabeçalho?
    - Resposta: A lib docling gera arquivos markdown com uma estrutura padrão, incluindo metadados no cabeçalho (como título, URL de origem, data de extração). Somo mais uma ferramenta de orquestração, então vamos seguir a estrutura gerada pela docling, mas podemos adicionar metadados adicionais conforme necessário, como tags ou categorias definidas pelo usuário.

## 3. Configuração de Processos de Extração

### 3.1 Regras de Extração
- **P3.1.1**: Como o usuário definirá as "regras" de extração? Interface visual, JSON, YAML, Python scripts? 
    - Resposta: nao entendi muito bem a pergunta, pois a extracao em si vai ser feita pela lib docling, entao as regras de extracao vao ser definidas seguindo a estrutura de configuracao da docling.
- **P3.1.2**: Quais regras são necessárias? Profundidade máxima, padrões de URL a incluir/excluir, tipos de conteúdo (imagens, texto, código)?
    - Resposta: Nao entendi bem a pergunta poderia me dar um exemplo?
- **P3.1.3**: É possível definir seletores CSS/XPath personalizados para extrair apenas partes específicas de uma página?
    - Resposta: Neste momento nao teremos essa funcionalidade, vamos extrair o conteudo seguindo a estrutura padrao da docling, mas podemos considerar isso para uma versao futura, onde o usuario pode definir seletores CSS/XPath personalizados para extrair apenas partes específicas de uma página.
- **P3.1.4**: Como lidar com JavaScript dinâmico? Vai precisar de headless browser?
    - Resposta: A lib docling tem suporte para lidar com JavaScript dinâmico usando um headless browser.
### 3.2 Transformações
- **P3.2.1**: Que tipos de transformações são necessárias? Limpeza de HTML, formatação de código, tradução, resumos?
    - Resposta: A padrao do docling.
- **P3.2.2**: O usuário poderá criar transformações customizadas? Como? (plugins, scripts Python)
    - Resposta: Inicialmente nào.
- **P3.2.3**: As transformações serão aplicadas em tempo real ou em batch após a extração?
    - Respsota: A lib que cuida disso.

### 3.3 Fontes de Dados
- **P3.3.1**: Além de sites web (HTTP/HTTPS), quais outras fontes são previstas? APIs REST, GraphQL, bancos de dados, arquivos locais, PDFs?
    - Resposta: Inicialmente, vamos focar apenas em sites web (HTTP/HTTPS) para a funcionalidade de exploração de sites.
- **P3.3.2**: Como lidar com sites que requerem autenticação? Login, cookies, tokens API?
    - Resposta: Inicialmente não teremos suporte para autenticação em sites.
- **P3.3.3**: Como lidar com rate limiting de APIs/sites? Sistema de backoff?
    - Resposta: Para lidar com rate limiting, o sistema pode implementar um mecanismo de backoff exponencial, onde o tempo entre as tentativas de requisição aumenta progressivamente após cada falha devido a rate limiting. Além disso, o sistema pode monitorar os cabeçalhos de resposta para detectar quando o limite de requisições foi atingido e ajustar automaticamente a frequência das requisições para evitar bloqueios. Podemos considerar a implementação de uma fila de requisições para gerenciar melhor o ritmo das requisições e evitar sobrecarregar os sites.

## 4. Agendamento e Execução

### 4.1 Agendamento
- **P4.1.1**: Que tipos de agendamento serão suportados? Cron expressions, intervalos fixos, one-time?
    - Resposta: Cron expressions para agendamento recorrente, e opção de one-time para agendamento único. O usuário poderá escolher entre essas opções ao configurar o processo de extração.
- **P4.1.2**: Haverá limite de processos agendados por usuário?
    - Resposta: não.
- **P4.1.3**: Como lidar com sobreposição? Se um processo ainda está rodando quando chega a hora do próximo agendamento?
    - resposta: Coloca na fila de execução.

### 4.2 Execução
- **P4.2.1**: Haverá timeout para processos? Quanto tempo máximo uma extração pode rodar?
    - Resposta: Sim, haverá um timeout configurável para os processos de extração. O tempo máximo que uma extração pode rodar pode ser definido pelo usuário ao configurar o processo, com um valor padrão de 1 hora. Se o processo atingir esse limite de tempo, ele será automaticamente interrompido e marcado como falhado, com uma notificação enviada ao usuário sobre o timeout.
- **P4.2.2**: Como será o tratamento de retry? Quantas tentativas em caso de falha?
    - Resposta: O sistema pode implementar um mecanismo de retry configurável, onde o usuário pode definir o número máximo de tentativas em caso de falha (por exemplo, 3 tentativas). Entre cada tentativa, o sistema pode aplicar um backoff exponencial para evitar sobrecarregar os recursos ou os sites-alvo. Se todas as tentativas falharem, o processo será marcado como falhado e uma notificação será enviada ao usuário.
- **P4.2.3**: O sistema terá um limite de recursos (CPU, memória, disco) por processo?
    - Resposta: não.

## 5. Exploração de Sites

- resposta: A Exploracao de sites vamos deixar para um segundo momento. Pois tem muitos detalhes a serem definidos, e queremos focar primeiro na funcionalidade de extracao a partir de uma url, sem a parte de exploracao. Mas vou deixar aqui algumas perguntas para guiar o desenvolvimento dessa funcionalidade no futuro. "A definir"
### 5.1 Descoberta de Páginas
- **P5.1.1**: Como determinar quais links são "páginas filhas"? Mesmo domínio? Padrão de URL?
- **P5.1.2**: Como evitar loops infinitos (páginas que se referenciam ciclicamente)?
- **P5.1.3**: Como lidar com sitemaps XML? Será utilizado para descobrir páginas?
- **P5.1.4**: Haverá cache de páginas já visitadas para evitar re-extração desnecessária?

### 5.2 Navegação
- **P5.2.1**: O sistema respeitará robots.txt dos sites?
- **P5.2.2**: Como será o controle de velocidade de requisições para não sobrecarregar os sites?
- **P5.2.3**: Haverá User-Agent customizável?

## 6. Monitoramento e Logs

### 6.1 Logs
- **P6.1.1**: Que nível de detalhe nos logs? Debug, Info, Warning, Error?
   - Resposta: podemos ter todos, mas por padráo so vai para stdout os logs de info, warning e error, e os logs de debug so vao ser exibidos se o usuario configurar para isso.
- **P6.1.2**: Os logs serão armazenados onde? Arquivo, banco de dados, serviço externo?
    - Inicialmente, vamos apenas enviar para o console (stdout) os logs de info, warning e error.
- **P6.1.3**: Por quanto tempo os logs serão mantidos?
    - Resposta: Como os logs não serão armazenados em um arquivo ou banco de dados, eles não serão mantidos por um período específico.

### 6.2 Métricas
- **P6.2.1**: Quais métricas devem ser coletadas? Tempo de execução, páginas processadas, taxa de erro, tamanho dos dados?
    - todas essas.
- **P6.2.2**: Haverá dashboard de métricas? Gráficos de execução ao longo do tempo?
    - Resposta: A ideia seria usar o grafana, mas de inicio nao vamos configurar isso, vamos deixar as metricas disponiveis via API, e o usuario pode usar a ferramenta que preferir para criar dashboards personalizados.
- **P6.2.3**: Alertas automáticos em caso de falhas recorrentes?
    - Resposta: no futuro.

### 6.3 Progresso em Tempo Real
- **P6.3.1**: Como será exibido o progresso? Percentual, páginas processadas de total estimado?
    - Resposta: Temos que pesquisar como a lib docling disponibiliza o progresso da extração, e a partir disso definir como será exibido o progresso para o usuário. A ideia é mostrar um percentual de conclusão, baseado no número de páginas processadas em relação ao total estimado de páginas a serem extraídas. Se a docling fornecer informações mais detalhadas, como o número total de páginas ou o tempo estimado restante, podemos usar esses dados para melhorar a exibição do progresso.
- **P6.3.2**: O frontend atualizará automaticamente ou precisa fazer polling?
    - Resposta: A ideia é usar WebSockets ou Server-Sent Events (SSE) para que o frontend possa receber atualizações em tempo real sobre o progresso dos processos de extração, evitando a necessidade de polling constante. Isso permitirá uma experiência mais fluida e responsiva para o usuário.

## 7. Notificações
"A definir"
### 7.1 Canais
    - resposta: Vamos deixar isso para o futuro.
- **P7.1.1**: Quais canais de notificação? Email, webhooks, Slack, Discord, Telegram?
- **P7.1.2**: O usuário pode configurar preferências de notificação por processo?

### 7.2 Eventos
    - resposta: Vamos deixar isso para o futuro. "A definir"
- **P7.2.1**: Quais eventos disparam notificações? Início, conclusão, falha, pausas, alertas de recursos?
- **P7.2.2**: Haverá limite de notificações para evitar spam?

## 8. Interface do Usuário

### 8.1 Funcionalidades
- **P8.1.1**: Quais são as telas principais? Dashboard, Lista de Processos, Criar/Editar Processo, Detalhes do Processo, Configurações? 
    - Resposta: sim.
- **P8.1.2**: Haverá busca e filtros na lista de processos? Por status, data, tags?
    - Resposta: por enquanto nao
- **P8.1.3**: Como será a experiência de criar um processo? Wizard passo-a-passo, formulário único, template?
    - Resposta: Formulário único, com campos organizados de forma clara e intuitiva. Podemos considerar a implementação de templates pré-configurados para facilitar a criação de processos comuns, mas inicialmente o usuário terá que configurar cada processo manualmente.

### 8.2 Visualização de Resultados
- **P8.2.1**: O usuário poderá visualizar os dados extraídos diretamente na interface ou só fazer download?
    - resposta: Inicialmente, o usuário poderá apenas fazer download dos arquivos markdown gerados. 
- **P8.2.2**: Haverá preview dos arquivos markdown gerados?
    - Resposta: No início, não teremos um preview integrado para os arquivos markdown gerados. 
- **P8.2.3**: Como será exibida a estrutura de páginas exploradas? Árvore hierárquica, lista, grafo?
    - Resposta: "A definir"

## 9. Usuários e Autenticação

### 9.1 Multi-usuário
- **P9.1.1**: O sistema será multi-usuário ou single-user (uso local)? 
    - resposta: uso local, single-user.
- **P9.1.2**: Se multi-usuário, haverá diferentes níveis de permissão? Admin, usuário comum?
- **P9.1.3**: Cada usuário terá suas próprias configurações e processos isolados?

### 9.2 Autenticação e Segurança
- **P9.2.1**: Como será a autenticação? Usuário/senha, OAuth, JWT?
    - resposta: Não teremos autenticação, pois o sistema é single-user e voltado para uso local
- **P9.2.2**: Haverá necessidade de HTTPS obrigatório?
    - resposta: Não, como o sistema é voltado para uso local, não será necessário implementar HTTPS obrigatório.
- **P9.2.3**: Como serão armazenadas credenciais sensíveis (senhas de sites, tokens de API)? Criptografia?
    - resposta: Como o sistema é voltado para uso local e não terá autenticação, não haverá armazenamento de credenciais sensíveis. 
## 10. Persistência e Banco de Dados

### 10.1 Modelo de Dados
- **P10.1.1**: Quais as principais entidades? Usuário, Processo, Execução, Log, Configuração, Página Extraída?
    - Resposta: Processo, Execução, Log, Configuração, Página Extraída.
- **P10.1.2**: Relacionamentos entre entidades? Um Processo tem várias Execuções?
    - Resposta: Sim, um Processo pode ter várias Execuções, e cada Execução pode ter vários Logs e Páginas Extraídas associadas a ela. A Configuração pode estar relacionada ao Processo, definindo as regras e parâmetros para as extrações.
- **P10.1.3**: Haverá soft-delete ou deleção física?
    - Resposta: Inicialmente, teremos deleção física para simplificar a implementação.
### 10.2 Escolha do Banco
- **P10.2.1**: SQLite será suficiente ou pretende escalar para PostgreSQL/MySQL no futuro?
    - Resposta: SQLite deve ser suficiente para a versão inicial do projeto.
- **P10.2.2**: Haverá necessidade de transações complexas?
    - Resposta: Não, as operações de banco de dados serão relativamente simples, então não haverá necessidade de transações complexas.
- **P10.2.3**: Considera-se usar ORM (SQLAlchemy, Peewee) ou queries SQL diretas?
    - Resposta: Sim, podemos usar um ORM, qual você me recomenda para python? 

## 11. Performance e Escalabilidade

### 11.1 Limites
- **P11.1.1**: Quantos usuários simultâneos o sistema deve suportar? 
    - Resposta: Como o sistema é voltado para uso local e single-user, não há necessidade de suportar múltiplos usuários simultâneos. O foco será garantir que o sistema funcione de forma eficiente para um único usuário, com a possibilidade de escalar para mais processos de extração simultâneos conforme necessário.
- **P11.1.2**: Quantos processos simultâneos por usuário?
    - Resposta: O sistema deve suportar pelo menos 5 processos de extração simultâneos por usuário, com a possibilidade de escalar para mais conforme necessário. ( podemos deixar como variavel de ambiente, default 5, e o usuario pode configurar conforme a necessidade )
- **P11.1.3**: Qual o tempo de resposta aceitável para a interface (ms)?
    - Resposta: O tempo de resposta para a interface deve ser inferior a 500ms para operações comuns, como navegação entre telas e visualização de processos. Para operações mais complexas, como criação ou edição de processos, um tempo de resposta de até 1 segundo pode ser aceitável. O objetivo é garantir uma experiência fluida e responsiva para o usuário.

### 11.2 Otimizações
- **P11.2.1**: Haverá cache de requisições HTTP?
    - Resposta: Sim, podemos implementar um cache simples para as requisições HTTP durante a extração, para evitar reprocessar páginas que já foram visitadas. O cache pode ser armazenado em memória ou em um arquivo temporário, e pode ter um tempo de expiração configurável para garantir que os dados sejam atualizados periodicamente.
- **P11.2.2**: Processamento paralelo de páginas? Quantas threads/processos?
    - Resposta: Sim, podemos implementar processamento paralelo de páginas para acelerar a extração. O número de threads ou processos pode ser configurável, com um valor padrão de 4 threads para processar as páginas simultaneamente. No entanto, é importante monitorar o uso de recursos do sistema e ajustar esse número conforme necessário para evitar sobrecarga.
- **P11.2.3**: Como evitar esgotar recursos em extrações muito grandes?
    - Resposta: "A definir"

## 12. Tratamento de Erros

### 12.1 Tipos de Erro
- **P12.1.1**: Quais erros são esperados? Timeout, 404, 403, falha de rede, conteúdo inválido?
    - Resposta: Timeout, 404, 403, falha de rede, conteúdo inválido, erros de parsing, erros de transformação.
- **P12.1.2**: Como diferenciar erros recuperáveis de irrecuperáveis?
    - Resposta: Erros recuperáveis são aqueles que podem ser resolvidos com uma nova tentativa, como falhas de rede ou timeouts. Erros irrecuperáveis são aqueles que indicam um problema fundamental, como conteúdo inválido ou erros de parsing que não podem ser corrigidos sem intervenção manual. O sistema pode categorizar os erros com base em seus códigos de status HTTP e mensagens de erro para determinar se são recuperáveis ou irrecuperáveis.

### 12.2 Recuperação
- **P12.2.1**: Em caso de falha parcial (algumas páginas falharam), o que fazer? Salvar parcial, tentar novamente, alertar usuário?
    - Resposta: Em caso de falha parcial, o sistema pode salvar os dados extraídos até o ponto da falha e marcar o processo como "Concluído com Erros". 
- **P12.2.2**: Haverá checkpoint/savepoint durante extração longa?
    - Resposta: Não, inicialmente não teremos checkpoint/savepoint durante extrações longas para simplificar a implementação. 
- **P12.2.3**: Como lidar com mudanças na estrutura do site entre tentativas?
    - Resposta: "A definir"

## 13. Deploy e Ambiente

### 13.1 Ambiente de Execução
- **P13.1.1**: O sistema será executado onde? Localmente, servidor próprio, cloud?
    - Resposta: O sistema será executado localmente, voltado para uso em máquinas pessoais ou ambientes de desenvolvimento. A ideia é ser simples, mas seria legal ter uma imagem docker, para colocar na vps.
- **P13.1.2**: Haverá containerização (Docker)? Docker Compose para orquestração local? 
    - Resposta: Sim, podemos criar uma imagem Docker para facilitar a execução do sistema em diferentes ambientes. O Docker Compose pode ser usado para orquestrar os serviços necessários, como o backend, frontend e o worker de extração, tornando mais fácil para os usuários configurarem e executarem o sistema localmente.
- **P13.1.3**: Como será o processo de instalação? Pip install, clone + setup.py, imagem Docker?
    - Resposta: Oque voce me recomenda?

### 13.2 Configuração
- **P13.2.1**: Configurações do sistema (porta, DB path, etc) serão via variáveis de ambiente, arquivo config, ou banco?
    - Resposta: As configurações do sistema, como porta de execução, caminho do banco de dados e outros parâmetros, serão definidas via variáveis de ambiente para facilitar a configuração e a flexibilidade. Podemos usar uma biblioteca como `python-dotenv` para carregar as variáveis de ambiente a partir de um arquivo `.env`, permitindo que os usuários personalizem as configurações sem precisar modificar o código-fonte.
- **P13.2.2**: Haverá migrations de banco de dados gerenciadas (Alembic)?
    - Resposta: Sim, podemos usar uma ferramenta de migração de banco de dados como Alembic para gerenciar as mudanças no esquema do banco de dados ao longo do desenvolvimento. Isso facilitará a evolução do modelo de dados e garantirá que as alterações sejam aplicadas de forma consistente em diferentes ambientes.

## 14. Documentação e Testes

### 14.1 Documentação
- **P14.1.1**: Haverá documentação da API (Swagger/OpenAPI)?
    - Resposta: Sim, podemos usar uma ferramenta como Swagger ou OpenAPI para documentar a API do backend, facilitando a compreensão e o uso dos endpoints disponíveis para os desenvolvedores e para a integração com o frontend.
- **P14.1.2**: Documentação de usuário? Como usar, tutoriais, exemplos?
    - Resposta: Podemos criar uma documentação de usuário detalhada, incluindo tutoriais, exemplos de uso e guias passo a passo para ajudar os usuários a entenderem e utilizarem o sistema de forma eficaz.
### 14.2 Testes
- **P14.2.1**: Que nível de cobertura de testes é esperado? Unit tests, integration tests, e2e?
    - Resposta: O objetivo é alcançar uma cobertura de testes de pelo menos 90%, incluindo unit tests para as funções e métodos individuais, integration tests para verificar a interação entre os componentes do sistema (test containers)
- **P14.2.2**: Como testar extração de sites? Mocks, fixtures, sites de teste?
    - Resposta: Para testar a extração de sites como vamos usar o test contairse podemos subir um mock server. Podemos criar endpoints específicos para retornar respostas pré-definidas, simulando diferentes cenários, como páginas com conteúdo estático, páginas com JavaScript dinâmico, páginas que retornam erros (404, 500), etc. Isso permitirá testar a funcionalidade de extração de forma controlada e garantir que o sistema lide corretamente com diferentes tipos de conteúdo e situações.

## 15. Casos de Uso Específicos

### 15.1 Cenários Reais
- **P15.1.1**: Além de documentações técnicas, que outros casos de uso você imagina? Blogs, artigos científicos, e-commerce?
    - Resposta: Qualquer site que possa ser intetressante para uma IA ler.
- **P15.1.2**: Haverá templates pré-configurados para sites comuns? (GitHub docs, ReadTheDocs, etc)
    - Resposta: Não inicialmente.
- **P15.1.3**: Como o sistema lidará com sites com estrutura muito diferente uns dos outros?
    - Resposta: A lib docling tem uma estrutura de configuração flexível que pode ser adaptada para lidar com diferentes estruturas de sites. 

### 15.2 Integração
- **P15.2.1**: Os dados extraídos serão usados para quê depois? Análise, busca, processamento com IA?
    - Resposta: A ideia é que os dados extraídos possam ser usados para análise, busca e processamento com IA. O formato markdown é bastante versátil e pode ser facilmente integrado com outras ferramentas de análise de texto ou processamento de linguagem natural. Os usuários podem usar os dados extraídos para criar resumos, gerar insights, alimentar modelos de IA ou simplesmente organizar o conteúdo de forma mais acessível.
- **P15.2.2**: Haverá integração com outras ferramentas? (Obsidian, Notion, Confluence)
    - Resposta: A definir.
- **P15.2.3**: API para integração externa? Webhooks para eventos?
    - Resposta: A definir.

---

## Instruções para Resposta

Você pode responder às perguntas de forma livre, não precisa seguir uma estrutura rígida. Priorize as perguntas que você acha mais relevantes para o projeto. Se alguma pergunta não se aplicar ou você ainda não tiver pensado sobre, pode indicar "A definir" ou "Não aplicável".

Suas respostas ajudarão a amadurecer o documento do projeto e guiar as decisões técnicas.
