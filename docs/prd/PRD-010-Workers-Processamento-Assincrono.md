# PRD-010: Workers e Processamento Assíncrono

**Status**: ✅ Concluído  
**Prioridade**: 🟡 Média - Backend Features Avançadas (Prioridade 3)  
**Categoria**: Backend - Features Avançadas  
**Estimativa**: 10-12 horas

---

## 1. Objetivo

Implementar sistema de processamento assíncrono utilizando Celery + Redis para executar extrações de dados em background. Inclui workers, task queue, agendamento via Celery Beat, retry automático, monitoramento com Flower e controle de concorrência.

## 2. Contexto e Justificativa

Extrações de dados são operações demoradas (minutos/horas). Executar de forma síncrona bloquearia a API. Workers Celery permitem:
- Execução em background (não bloqueia API)
- Processamento paralelo (múltiplos workers)
- Retry automático em falhas
- Agendamento via cron (Celery Beat)
- Monitoramento centralizado (Flower)
- Escalabilidade horizontal

**Arquitetura:**
```
FastAPI (enfileira task) → Redis (message broker) → Celery Workers (executam) → Database (resultados)
```

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
toninho/workers/
├── __init__.py
├── celery_app.py             # Configuração Celery
├── tasks/
│   ├── __init__.py
│   ├── execucao_task.py      # Task principal de execução
│   ├── agendamento_task.py   # Tasks de agendamento
│   └── limpeza_task.py       # Tasks de manutenção
├── config.py                  # Configurações específicas de workers
└── utils.py                   # Utilidades compartilhadas

scripts/
├── start_worker.sh            # Inicia worker
├── start_beat.sh              # Inicia scheduler
└── start_flower.sh            # Inicia monitoramento
```

### 3.2. Celery App (toninho/workers/celery_app.py)

**Configuração:**
```python
from celery import Celery
from toninho.core.config import settings

celery_app = Celery(
    "toninho",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "toninho.workers.tasks.execucao_task",
        "toninho.workers.tasks.agendamento_task",
        "toninho.workers.tasks.limpeza_task"
    ]
)

# Configurações
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Retry configurado
    task_acks_late=True,  # ACK após task completa (não ao receber)
    task_reject_on_worker_lost=True,
    
    # Limites
    task_time_limit=7200,  # 2 horas (hard limit)
    task_soft_time_limit=7000,  # 1h56min (soft limit)
    worker_prefetch_multiplier=1,  # Pega 1 task por vez
    worker_max_tasks_per_child=100,  # Recicla worker após 100 tasks
    
    # Beat schedule (agendamentos)
    beat_schedule={
        "verificar_agendamentos": {
            "task": "toninho.workers.tasks.agendamento_task.verificar_agendamentos",
            "schedule": 60.0,  # A cada 60 segundos
        },
        "limpar_logs_antigos": {
            "task": "toninho.workers.tasks.limpeza_task.limpar_logs_antigos",
            "schedule": 86400.0,  # Diariamente
        }
    },
    
    # Concorrência
    worker_concurrency=settings.WORKER_CONCURRENCY,  # Default: 2
)
```

**Settings adicionais** (toninho/core/config.py):
```python
CELERY_BROKER_URL: str = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
WORKER_CONCURRENCY: int = 2
MAX_CONCURRENT_PROCESSES: int = 5  # Máximo de processos simultâneos
```

### 3.3. Task Principal de Execução (toninho/workers/tasks/execucao_task.py)

**Task executar_processo:**
```python
@celery_app.task(
    bind=True,
    name="toninho.workers.executar_processo",
    max_retries=3,
    default_retry_delay=60,  # Retry após 60s
    autoretry_for=(Exception,),
    retry_backoff=True,  # Backoff exponencial
    retry_jitter=True
)
def executar_processo_task(self, execucao_id: str) -> dict:
    """
    Task principal para executar processo de extração.
    
    Fluxo:
    1. Atualizar status da execução para AGUARDANDO
    2. Buscar configuração do processo
    3. Para cada URL na configuração:
       a. Extrair conteúdo usando docling
       b. Salvar arquivo markdown
       c. Registrar página extraída
       d. Registrar logs
       e. Atualizar métricas da execução
    4. Marcar execução como CONCLUIDO ou FALHOU
    
    Args:
        execucao_id: UUID da execução
    
    Returns:
        dict com resultado da execução
    
    Raises:
        Exception: Em caso de erro não recuperável
    """
    from toninho.core.database import SessionLocal
    from toninho.services.execucao_service import ExecucaoService
    from toninho.services.log_service import LogService
    from toninho.workers.utils import ExtractionOrchestrator
    
    db = SessionLocal()
    
    try:
        # 1. Buscar execução
        execucao_service = ExecucaoService()
        execucao = execucao_service.get_execucao_model(db, UUID(execucao_id))
        
        # 2. Atualizar status
        execucao.status = ExecucaoStatus.EM_EXECUCAO
        execucao.iniciado_em = datetime.utcnow()
        db.commit()
        
        # 3. Buscar configuração
        configuracao = db.query(Configuracao).filter(
            Configuracao.processo_id == execucao.processo_id
        ).order_by(Configuracao.created_at.desc()).first()
        
        if not configuracao:
            raise ValueError("Processo não tem configuração")
        
        # 4. Log inicial
        log_service = LogService()
        log_service.create_log(db, LogCreate(
            execucao_id=execucao.id,
            nivel=LogNivel.INFO,
            mensagem=f"Iniciando extração de {len(configuracao.urls)} URLs"
        ))
        
        # 5. Orquestrar extração
        orchestrator = ExtractionOrchestrator(db, execucao, configuracao)
        resultado = orchestrator.executar()
        
        # 6. Finalizar
        execucao.finalizado_em = datetime.utcnow()
        execucao.status = resultado["status"]  # CONCLUIDO ou CONCLUIDO_COM_ERROS
        db.commit()
        
        log_service.create_log(db, LogCreate(
            execucao_id=execucao.id,
            nivel=LogNivel.INFO,
            mensagem=f"Extração finalizada: {resultado['paginas_sucesso']} sucesso, {resultado['paginas_falha']} falhas"
        ))
        
        return resultado
        
    except Exception as e:
        # Registrar erro
        log_service.create_log(db, LogCreate(
            execucao_id=UUID(execucao_id),
            nivel=LogNivel.ERROR,
            mensagem=f"Erro na extração: {str(e)}"
        ))
        
        # Atualizar status
        execucao = db.query(Execucao).get(UUID(execucao_id))
        if execucao:
            execucao.status = ExecucaoStatus.FALHOU
            execucao.finalizado_em = datetime.utcnow()
            db.commit()
        
        # Retry se possível
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        raise
        
    finally:
        db.close()
```

### 3.4. Orchestrator de Extração (toninho/workers/utils.py)

**ExtractionOrchestrator:**
Classe responsável por orquestrar a extração de múltiplas URLs:
```python
class ExtractionOrchestrator:
    def __init__(self, db: Session, execucao: Execucao, configuracao: Configuracao):
        self.db = db
        self.execucao = execucao
        self.configuracao = configuracao
        self.extractor = None  # Implementado no PRD-011
        
    def executar(self) -> dict:
        """Executa extração de todas as URLs"""
        total_urls = len(self.configuracao.urls)
        sucesso = 0
        falhas = 0
        
        for idx, url in enumerate(self.configuracao.urls, 1):
            try:
                # Log progresso
                self._log_info(f"Processando URL {idx}/{total_urls}: {url}")
                
                # Extrair página (ver PRD-011)
                resultado = self._extrair_pagina(url)
                
                # Registrar página extraída
                self._registrar_pagina(url, resultado)
                
                if resultado["status"] == "sucesso":
                    sucesso += 1
                else:
                    falhas += 1
                
                # Atualizar métricas
                self._atualizar_metricas(resultado["bytes"])
                
            except Exception as e:
                falhas += 1
                self._log_error(f"Erro ao processar {url}: {str(e)}")
                self._registrar_pagina_falha(url, str(e))
        
        # Determinar status final
        if falhas == 0:
            status = ExecucaoStatus.CONCLUIDO
        elif sucesso > 0:
            status = ExecucaoStatus.CONCLUIDO_COM_ERROS
        else:
            status = ExecucaoStatus.FALHOU
        
        return {
            "status": status,
            "paginas_sucesso": sucesso,
            "paginas_falha": falhas,
            "total": total_urls
        }
    
    def _extrair_pagina(self, url: str) -> dict:
        # Implementado no PRD-011 (Sistema de Extração)
        pass
    
    def _log_info(self, mensagem: str):
        # Criar log INFO
        pass
    
    def _log_error(self, mensagem: str):
        # Criar log ERROR
        pass
```

### 3.5. Tasks de Agendamento (toninho/workers/tasks/agendamento_task.py)

**Task verificar_agendamentos:**
```python
@celery_app.task(name="toninho.workers.verificar_agendamentos")
def verificar_agendamentos():
    """
    Task periódica que verifica configurações com agendamento
    e cria execuções se necessário.
    
    Executada a cada minuto pelo Celery Beat.
    """
    from toninho.core.database import SessionLocal
    from croniter import croniter
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    
    try:
        # Buscar configurações com agendamento RECORRENTE
        configuracoes = db.query(Configuracao).filter(
            Configuracao.agendamento_tipo == AgendamentoTipo.RECORRENTE,
            Configuracao.agendamento_cron.isnot(None)
        ).all()
        
        agora = datetime.utcnow()
        
        for config in configuracoes:
            # Verificar se deve executar
            cron = croniter(config.agendamento_cron, agora - timedelta(minutes=2))
            proxima = cron.get_next(datetime)
            
            # Se próxima execução é nos próximos 60 segundos, criar execução
            if proxima <= agora + timedelta(seconds=60):
                # Verificar se não há execução recente (evitar duplicatas)
                ultima_execucao = db.query(Execucao).filter(
                    Execucao.processo_id == config.processo_id,
                    Execucao.created_at >= agora - timedelta(minutes=5)
                ).first()
                
                if not ultima_execucao:
                    # Criar e enfileirar execução
                    execucao = Execucao(processo_id=config.processo_id)
                    db.add(execucao)
                    db.commit()
                    
                    # Enfileirar task
                    executar_processo_task.delay(str(execucao.id))
    
    finally:
        db.close()
```

### 3.6. Tasks de Limpeza (toninho/workers/tasks/limpeza_task.py)

**Task limpar_logs_antigos:**
```python
@celery_app.task(name="toninho.workers.limpar_logs_antigos")
def limpar_logs_antigos(dias_retencao: int = 30):
    """
    Task que remove logs antigos para economizar espaço.
    Executada diariamente.
    """
    from toninho.core.database import SessionLocal
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    
    try:
        data_limite = datetime.utcnow() - timedelta(days=dias_retencao)
        
        # Deletar logs antigos
        count = db.query(Log).filter(
            Log.timestamp < data_limite
        ).delete()
        
        db.commit()
        
        return {"logs_deletados": count}
    
    finally:
        db.close()
```

### 3.7. Scripts de Inicialização

**scripts/start_worker.sh:**
```bash
#!/bin/bash
celery -A toninho.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=100
```

**scripts/start_beat.sh:**
```bash
#!/bin/bash
celery -A toninho.workers.celery_app beat \
    --loglevel=info
```

**scripts/start_flower.sh:**
```bash
#!/bin/bash
celery -A toninho.workers.celery_app flower \
    --port=5555
```

## 4. Dependências

### 4.1. Dependências de Outros PRDs
- PRD-003: Models
- PRD-007: Módulo Execução
- PRD-011: Sistema de Extração (para extração de páginas) - pode ser stub inicialmente

### 4.2. Bibliotecas Python
- celery: ^5.3.6
- redis: ^5.0.1
- flower: ^2.0.1
- croniter: ^2.0.1 (para parsing de cron)

## 5. Regras de Negócio

### 5.1. Concorrência
- Máximo de 5 processos simultâneos (configurável)
- Implementar limite via Celery rate limiting ou semáforos
- Se limite atingido, tasks ficam em AGUARDANDO na fila

### 5.2. Retry
- Máximo de 3 retries (configurável em max_retries)
- Backoff exponencial: 1min, 2min, 4min
- Jitter para evitar thundering herd

### 5.3. Timeout
- Task timeout: 2 horas (hard limit)
- Soft timeout: 1h56min (aviso antes de kill)
- Configurável via settings.DEFAULT_TIMEOUT

### 5.4. Agendamento
- Verificação a cada minuto (Celery Beat)
- Cron expressions: 5 campos padrão Unix
- Evitar criar execuções duplicadas

### 5.5. Monitoramento
- Flower UI: http://localhost:5555
- Métricas: tasks succeeded, failed, retried, active
- Logs centralizados via Loguru

## 6. Casos de Teste

### 6.1. Celery App Tests
- ✅ Celery app inicializa corretamente
- ✅ Conecta ao Redis broker
- ✅ Configurações aplicadas

### 6.2. Task Tests
- ✅ executar_processo_task: executa com sucesso
- ✅ executar_processo_task: falha e retries
- ✅ executar_processo_task: atualiza status da execução
- ✅ executar_processo_task: registra logs
- ✅ verificar_agendamentos: cria execuções conforme cron
- ✅ limpar_logs_antigos: remove logs antigos

### 6.3. Orchestrator Tests
- ✅ ExtractionOrchestrator: processa múltiplas URLs
- ✅ Orchestrator: atualiza métricas
- ✅ Orchestrator: registra páginas extraídas
- ✅ Orchestrator: determina status final correto

### 6.4. Integration Tests
- ✅ Enfileirar task via API
- ✅ Worker processa task
- ✅ Resultado atualizado no banco
- ✅ Flower mostra tasks

## 7. Critérios de Aceitação

### ✅ Configuração
- [ ] Celery app configurado
- [ ] Redis conectado
- [ ] Beat scheduler configurado
- [ ] Flower configurado

### ✅ Tasks
- [ ] Task executar_processo implementada
- [ ] Task verificar_agendamentos implementada
- [ ] Task limpar_logs_antigos implementada
- [ ] Retry configurado e funcional

### ✅ Scripts
- [ ] Scripts de inicialização criados
- [ ] Workers startam sem erros
- [ ] Beat executa tasks agendadas

### ✅ Monitoramento
- [ ] Flower acessível em localhost:5555
- [ ] Tasks visíveis no Flower
- [ ] Logs aparecem corretamente

### ✅ Testes
- [ ] Testes com cobertura > 85%
- [ ] Tasks executam end-to-end

## 8. Notas de Implementação

### 8.1. Testar Task Localmente
```python
# Testar task sem Celery (síncr ono)
from toninho.workers.tasks.execucao_task import executar_processo_task

resultado = executar_processo_task.apply(args=[str(execucao.id)])
print(resultado.get())
```

### 8.2. Monitorar Tasks
```bash
# Status dos workers
celery -A toninho.workers.celery_app status

# Inspecionar tasks ativas
celery -A toninho.workers.celery_app inspect active

# Revogar task
celery -A toninho.workers.celery_app control revoke <task_id> --terminate
```

### 8.3. Pontos de Atenção
- Session SQLAlchemy: sempre criar nova session em cada task
- Conexões: não deixar conexões abertas
- Memory leaks: reciclar workers periodicamente
- Redis: configurar persistência (AOF)
- Celery Beat: apenas 1 instância rodando

## 9. Referências Técnicas

- **Celery**: https://docs.celeryproject.org/
- **Flower**: https://flower.readthedocs.io/
- **Croniter**: https://github.com/kiorky/croniter

## 10. Definição de Pronto

- ✅ Celery + Redis + Flower configurados
- ✅ Tasks principais implementadas
- ✅ Workers processam extrações em background
- ✅ Retry automático funciona
- ✅ Agendamento via cron funcional
- ✅ Flower acessível e mostra tasks
- ✅ Testes com cobertura > 85%
- ✅ Pode enfileirar e executar processos via Workers

---

**PRD Anterior**: PRD-009 - Módulo Página Extraída  
**Próximo PRD**: PRD-011 - Sistema de Extração
