# PRD-ORG-006: Otimização Docker Build

**Status**: ✅ Implementado
**Prioridade**: 🔴 Alta
**Categoria**: DevOps / Docker
**Tipo**: Melhoria

---

## 1. Objetivo

Otimizar o `docker-compose.yml` para que a imagem Docker seja construída **uma única vez** e compartilhada entre os 4 serviços (api, worker, beat, flower), reduzindo o tempo de build. Também adicionar o volume de cache do Docling ao compose principal.

## 2. Contexto e Justificativa

### 2.1. Problema: Build Redundante

O `docker-compose.yml` atual define 4 serviços que fazem `build:` do **mesmo Dockerfile**:

```yaml
# Cada um destes faz build independente:
api:    build: { context: ., dockerfile: Dockerfile }
worker: build: { context: ., dockerfile: Dockerfile }
beat:   build: { context: ., dockerfile: Dockerfile }
flower: build: { context: ., dockerfile: Dockerfile }
```

**Impacto**: O Docker Compose pode construir a imagem até 4 vezes. Mesmo com cache, cada serviço verifica layers independentemente, desperdiçando tempo.

### 2.2. Problema: Docling Cache

O volume `docling_cache` está definido **apenas** no `docker-compose.override.yml` (dev). Em produção, o cache é perdido a cada restart do container.

### Referência: Discovery

- Discovery: `docs/discoverys/organizacao-projeto-v2/discovery.md`
- Items cobertos: K1, K2

---

## 3. Alterações no `docker-compose.yml`

### 3.1. Imagem Compartilhada

**Antes** (4 builds):
```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    # ...

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    # ...

  beat:
    build:
      context: .
      dockerfile: Dockerfile
    # ...

  flower:
    build:
      context: .
      dockerfile: Dockerfile
    # ...
```

**Depois** (1 build, 4 reusam):
```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: toninho:latest          # ← Nomeia a imagem construída
    # ... (restante igual)

  worker:
    image: toninho:latest          # ← Reusa a imagem (sem build:)
    depends_on:
      redis:
        condition: service_healthy
      api:
        condition: service_healthy # ← Garante que api (e a imagem) existe
    # ... (restante igual, remover build:)

  beat:
    image: toninho:latest          # ← Reusa (sem build:)
    depends_on:
      - redis
      - worker
    # ... (restante igual, remover build:)

  flower:
    image: toninho:latest          # ← Reusa (sem build:)
    depends_on:
      - redis
      - worker
    # ... (restante igual, remover build:)
```

**Regras:**
- Apenas o serviço `api` mantém `build:` + `image:`
- Os demais serviços usam apenas `image: toninho:latest`
- O `depends_on` do worker já referencia `api` com `condition: service_healthy`, garantindo que a imagem é construída antes
- **Não alterar**: volumes, environment, command, ports, networks, healthcheck

### 3.2. Volume Docling Cache

Adicionar ao `docker-compose.yml` principal:

**No serviço worker:**
```yaml
  worker:
    volumes:
      - ./output:/app/output
      - db_data:/app
      - docling_cache:/home/toninho/.cache/docling  # ← Adicionar
```

**Na seção volumes:**
```yaml
volumes:
  redis_data:
    driver: local
  db_data:
    driver: local
  docling_cache:              # ← Adicionar
    driver: local
```

### 3.3. Atualizar `docker-compose.override.yml`

O override já define `docling_cache`. Verificar que o path do mount é consistente:
- `docker-compose.yml`: `/home/toninho/.cache/docling` (user toninho no Dockerfile)
- `docker-compose.override.yml` atual: `/root/.cache/docling`

**Corrigir** o override para usar o mesmo path: `/home/toninho/.cache/docling`

---

## 4. Critérios de Aceite

- [ ] Apenas o serviço `api` tem `build:` no `docker-compose.yml`
- [ ] Serviços `worker`, `beat`, `flower` usam `image: toninho:latest` sem `build:`
- [ ] `docker compose up --build` constrói a imagem **uma vez**
- [ ] Todos os 5 serviços sobem corretamente após a mudança
- [ ] Volume `docling_cache` presente no `docker-compose.yml` principal
- [ ] Path do mount de docling_cache consistente entre compose e override
- [ ] Nenhuma funcionalidade quebrada (API responde, worker processa, beat agenda, flower monitora)

---

## 5. Verificação

Após implementar, rodar:

```bash
# Build e start
docker compose up --build -d

# Verificar que todos os serviços estão rodando
docker compose ps

# Verificar que a imagem foi construída uma vez
docker images | grep toninho

# Health check da API
curl http://localhost:8000/api/v1/health

# Parar
docker compose down
```

---

## 6. Riscos

- **Baixo risco**: Apenas altera **como** a imagem é referenciada, não o conteúdo
- **Rollback**: Reverter as 4 linhas `build:` é trivial
- **Compatibilidade**: `docker compose` (v2) suporta `image:` sem `build:` nativamente
