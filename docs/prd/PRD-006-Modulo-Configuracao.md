# PRD-006: Módulo Configuração

**Status**: ✅ Concluído  
**Prioridade**: 🟠 Alta - Backend Entidades Core (Prioridade 2)  
**Categoria**: Backend - Entidades Core  
**Estimativa**: 5-6 horas

---

## 1. Objetivo

Implementar o módulo completo de Configuração (Repository, Service, API), responsável por gerenciar as configurações de extração de cada processo (URLs, timeout, retry, agendamento, formato de saída).

## 2. Contexto e Justificativa

Configuração define **como** um processo será executado. Cada processo tem uma ou mais configurações (historicamente), mas apenas a mais recente é utilizada para novas execuções. Este módulo implementa CRUD completo, validação de URLs e expressões cron.

**Particularidades:**
- Validação de lista de URLs (formato, quantidade)
- Validação de expressão cron se agendamento recorrente
- Relacionamento N:1 com Processo (chave estrangeira)
- Valores default para timeout, max_retries, formato_saída

## 3. Requisitos Técnicos

### 3.1. Repository (toninho/repositories/configuracao_repository.py)

**Métodos obrigatórios:**
```python
create(db, configuracao) -> Configuracao
get_by_id(db, config_id) -> Optional[Configuracao]
get_by_processo_id(db, processo_id) -> Optional[Configuracao]
    # Retorna configuração mais recente do processo
get_all_by_processo_id(db, processo_id) -> List[Configuracao]
    # Retorna histórico de configurações (ordenado por created_at desc)
update(db, configuracao) -> Configuracao
delete(db, config_id) -> bool
```

### 3.2. Service (toninho/services/configuracao_service.py)

**Métodos obrigatórios:**
```python
create_configuracao(db, processo_id, config_create) -> ConfiguracaoResponse
    # 1. Validar processo existe
    # 2. Validar URLs (formato, não vazias, max 100)
    # 3. Validar cron expression se agendamento_tipo=RECORRENTE
    # 4. Validar output_dir (path válido)
    # 5. Criar configuração
    # 6. Associar ao processo via processo_id

get_configuracao(db, config_id) -> ConfiguracaoResponse
    # Buscar por ID

get_configuracao_by_processo(db, processo_id) -> ConfiguracaoResponse
    # Retorna configuração mais recente do processo
    # Exceção se processo não tem configuração

list_configuracoes_by_processo(db, processo_id) -> List[ConfiguracaoResponse]
    # Lista histórico de configurações do processo

update_configuracao(db, config_id, config_update) -> ConfiguracaoResponse
    # 1. Buscar configuração existente
    # 2. Validar mudanças (URLs, cron, etc)
    # 3. Atualizar
    # Nota: Idealmente, criar nova configuração (histórico), mas MVP pode atualizar

delete_configuracao(db, config_id) -> bool
    # Deletar configuração
    # Nota: Considerar se processo precisa ter ao menos 1 configuração
```

**Validações específicas de negócio:**
- Se agendamento_tipo=RECORRENTE, agendamento_cron obrigatório
- Se agendamento_tipo!=RECORRENTE, agendamento_cron deve ser None
- URLs: no mínimo 1, máximo 100
- Timeout: entre 1 e 86400 segundos (24 horas)
- Max_retries: entre 0 e 10
- Expressão cron: validar sintaxe (5 campos)

**Validators:**
- Usar validators do PRD-004 (url_validator, cron_validator, path_validator)
- Validator de lista de URLs:
  - Cada URL deve ser http/https
  - Não permitir duplicatas na lista
  - Não permitir URLs excessivamente longas (> 2048 chars)

### 3.3. API Routes (toninho/api/routes/configuracoes.py)

**Router**: prefix="/api/v1", tags=["Configurações"]

**Endpoints:**
```python
POST /api/v1/processos/{processo_id}/configuracoes
    # Criar configuração para processo
    # Request: ConfiguracaoCreate
    # Response: SuccessResponse[ConfiguracaoResponse]
    # Status: 201

GET /api/v1/processos/{processo_id}/configuracoes
    # Listar todas as configurações do processo (histórico)
    # Response: SuccessResponse[List[ConfiguracaoResponse]]
    # Status: 200

GET /api/v1/processos/{processo_id}/configuracao
    # Obter configuração atual (mais recente) do processo
    # Response: SuccessResponse[ConfiguracaoResponse]
    # Status: 200
    # Status: 404 se processo não tem configuração

GET /api/v1/configuracoes/{config_id}
    # Obter configuração específica por ID
    # Response: SuccessResponse[ConfiguracaoResponse]
    # Status: 200
    # Status: 404

PUT /api/v1/configuracoes/{config_id}
    # Atualizar configuração
    # Request: ConfiguracaoUpdate
    # Response: SuccessResponse[ConfiguracaoResponse]
    # Status: 200

DELETE /api/v1/configuracoes/{config_id}
    # Deletar configuração
    # Response: 204 No Content
    # Status: 404

GET /api/v1/configuracoes/{config_id}/validar-agendamento
    # Validar expressão cron e retornar próximas execuções
    # Response: SuccessResponse[AgendamentoInfo]
    # Status: 200
```

**AgendamentoInfo** (novo schema):
```python
class AgendamentoInfo(BaseModel):
    expressao_cron: str
    valida: bool
    proximas_execucoes: List[datetime]  # próximas 5 execuções
    descricao_legivel: str  # "Diariamente às 02:00"
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-003: Models
- PRD-004: Schemas (ConfiguracaoCreate, ConfiguracaoUpdate, ConfiguracaoResponse)
- PRD-005: Módulo Processo (validar processo existe)

## 5. Regras de Negócio

### 5.1. Relação com Processo
- Configuração pertence a um Processo (FK não null)
- Processo pode ter múltiplas Configurações (histórico)
- Apenas a mais recente é usada para novas execuções

### 5.2. URLs
- Mínimo 1 URL, máximo 100
- Formato: http:// ou https://
- Sem duplicatas na lista
- Comprimento máximo por URL: 2048 caracteres

### 5.3. Agendamento
- Tipos: MANUAL, ONE_TIME, RECORRENTE
- Se RECORRENTE: cron obrigatório
- Se não RECORRENTE: cron deve ser None
- Cron: 5 campos (minuto hora dia mês dia_semana)

### 5.4. Timeout e Retries
- Timeout: 1 a 86400 segundos
- Max_retries: 0 a 10
- Defaults: timeout=3600, max_retries=3

### 5.5. Output Directory
- Path relativo ou absoluto
- Validar caracteres válidos
- Criar diretório se não existe (na execução, não na criação da config)

## 6. Casos de Teste

### 6.1. Repository Tests
- ✅ create(): insere configuração
- ✅ get_by_processo_id(): retorna última configuração
- ✅ get_all_by_processo_id(): retorna histórico ordenado
- ✅ update(): atualiza configuração
- ✅ delete(): remove configuração

### 6.2. Service Tests
- ✅ create_configuracao(): cria com dados válidos
- ✅ create_configuracao(): valida processo existe
- ✅ create_configuracao(): valida URLs formato correto
- ✅ create_configuracao(): valida cron obrigatório se RECORRENTE
- ✅ create_configuracao(): valida timeout e max_retries ranges
- ✅ create_configuracao(): rejeita URLs duplicadas
- ✅ create_configuracao(): rejeita lista vazia de URLs
- ✅ create_configuracao(): rejeita mais de 100 URLs
- ✅ update_configuracao(): atualiza campos
- ✅ get_configuracao_by_processo(): retorna última

### 6.3. API Tests
- ✅ POST /processos/{id}/configuracoes: cria (201)
- ✅ POST: retorna 404 se processo não existe
- ✅ POST: retorna 400 se URLs inválidas
- ✅ POST: retorna 400 se cron inválido
- ✅ GET /processos/{id}/configuracoes: lista histórico
- ✅ GET /processos/{id}/configuracao: retorna última
- ✅ GET /configuracoes/{id}: retorna específica
- ✅ PUT /configuracoes/{id}: atualiza
- ✅ DELETE /configuracoes/{id}: deleta (204)
- ✅ GET /configuracoes/{id}/validar-agendamento: valida cron

### 6.4. Validação de Cron
- ✅ "0 2 * * *" válido (diariamente às 2h)
- ✅ "*/15 * * * *" válido (a cada 15 min)
- ✅ "0 0 1 * *" válido (primeiro dia do mês)
- ✅ "0 2 * * 1-5" válido (seg-sex às 2h)
- ✅ "invalid" inválido
- ✅ "0 2 * *" inválido (4 campos, precisa 5)

## 7. Critérios de Aceitação

### ✅ Implementação
- [x] Repository com todos os métodos
- [x] Service com validações de negócio
- [x] API Routes implementadas
- [x] Validação de URLs funcional
- [x] Validação de cron funcional

### ✅ Testes
- [x] Testes unitários > 90% cobertura
- [x] Testes de integração end-to-end
- [x] Validações testadas (URLs, cron, ranges)

### ✅ Funcionalidades
- [x] Pode criar configuração via API
- [x] Validações bloqueiam dados inválidos
- [x] Histórico de configurações funcional
- [x] Endpoint de validação de agendamento funciona

## 8. Notas de Implementação

### 8.1. Validação de Cron
Usar biblioteca `croniter` para validar e calcular próximas execuções:
```python
from croniter import croniter
from datetime import datetime

def validar_cron(expressao: str) -> bool:
    try:
        croniter(expressao, datetime.now())
        return True
    except:
        return False

def proximas_execucoes(expressao: str, num: int = 5) -> List[datetime]:
    cron = croniter(expressao, datetime.now())
    return [cron.get_next(datetime) for _ in range(num)]
```

### 8.2. Validação de URLs
```python
from urllib.parse import urlparse

def validar_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False
```

### 8.3. Pontos de Atenção
- Adicionar croniter nas dependências do Poetry
- Validação de cron pode ser custosa, cachear se necessário
- URLs podem ter caracteres especiais, validar encoding
- Output_dir: não criar diretório na validação, apenas na execução

## 9. Referências Técnicas

- **Croniter**: https://github.com/kiorky/croniter
- **Cron Syntax**: https://crontab.guru/
- **URL Parsing**: https://docs.python.org/3/library/urllib.parse.html

## 10. Definição de Pronto

- ✅ CRUD completo de Configuração
- ✅ Validação de URLs funcionando
- ✅ Validação de cron expressions
- ✅ Endpoint de validação de agendamento
- ✅ Histórico de configurações acessível
- ✅ Testes com cobertura > 90%
- ✅ Pode criar e gerenciar configurações via API

---

**PRD Anterior**: PRD-005 - Módulo Processo  
**Próximo PRD**: PRD-007 - Módulo Execução
