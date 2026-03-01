# PRD-DT-001: Correção de Warnings Deprecados

**Status**: 📋 Pronto para implementação
**Prioridade**: 🟡 Média - Débito técnico
**Categoria**: Qualidade de Código / Futuro-Proof
**Estimativa**: 30 minutos - 1 hora
**Tipo**: Débito Técnico

---

## 1. Objetivo

Eliminar warnings deprecados no código-fonte que causam ruído nos testes (9.573 warnings totais, dos quais 8 podem ser corrigidos) e garantir que o projeto seja preparado para versões futuras do Python, evitando quebras futuras.

## 2. Contexto e Justificativa

### 2.1. Análise de Warnings Atuais

Ao executar `make test`, obtemos **9.573 warnings**:

```
Conforme pytest output:
====================== 146 passed, 9573 warnings in 1.74s ======================
```

### 2.2. Breakdown dos Warnings

| Fonte | Quantidade | Tipo | Removível? |
|-------|-----------|------|-----------|
| pytest-asyncio/plugin.py:169 | ~9.297 | `asyncio.iscoroutinefunction()` deprecated | ❌ Não (dependência) |
| pytest-asyncio/plugin.py:433 | ~146 | `asyncio.iscoroutinefunction()` deprecated | ❌ Não (dependência) |
| FastAPI/routing.py:211 | ~18 | `asyncio.iscoroutinefunction()` deprecated | ❌ Não (dependência) |
| Starlette/_utils.py (42 e 43) | ~113 | `asyncio.iscoroutinefunction()` deprecated | ❌ Não (dependência) |
| pytest-asyncio/plugin.py:1005 | ~20-50 | `asyncio.get_event_loop_policy()` deprecated | ❌ Não (dependência) |
| **toninho/models/base.py:77** | **4** | `datetime.utcnow()` deprecated | ✅ **SIM** |
| **tests/unit/test_models.py:216-217** | **2** | `datetime.utcnow()` deprecated | ✅ **SIM** |
| **tests/unit/test_schemas.py:210-211** | **2** | `datetime.utcnow()` deprecated | ✅ **SIM** |
| **TOTAL CORRIGÍVEL** | **8** | | **✅ 0.08%** |

### 2.3. O Problema

**99.92% dos warnings** vêm de dependências (pytest-asyncio, FastAPI, Starlette) que usam APIs deprecadas do Python. Estas serão removidas no **Python 3.16** (lançado em ~2025).

**0.08% dos warnings** (8 warnings) estão no **código próprio** e podem ser corrigidos **AGORA**.

---

## 3. Problemas Identificados

### 3.1. Problema 1: `datetime.utcnow()` em [toninho/models/base.py](../../toninho/models/base.py#L77)

**Localização:** `toninho/models/base.py`, linha 77

**Código atual:**
```python
@event.listens_for(TimestampMixin, "before_update", propagate=True)
def receive_before_update(mapper: Any, connection: Any, target: TimestampMixin) -> None:
    """Event listener que garante updated_at seja sempre atualizado."""
    target.updated_at = datetime.utcnow()  # ⚠️ DEPRECATED
```

**Descrição:**
- `datetime.utcnow()` foi deprecado no Python 3.12
- Será removido no Python 3.16
- **Gera 4 warnings** durante os testes (uma por test-run)

**Estado do aviso (DeprecationWarning):**
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal
in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
```

---

### 3.2. Problema 2: `datetime.utcnow()` em [tests/unit/test_models.py](../../tests/unit/test_models.py#L216-L217)

**Localização:** `tests/unit/test_models.py`, linhas 216-217

**Código atual:**
```python
def test_execucao_property_duracao(self):
    """Testa o cálculo de duração de Execução."""
    execucao = Execucao(
        processo_id=1,
        status="em_progresso",
        esperado_inicio=datetime.utcnow(),      # ⚠️ DEPRECATED (linha 216)
        esperado_fim=datetime.utcnow() + timedelta(hours=2)  # ⚠️ DEPRECATED (linha 217)
    )
```

**Descrição:**
- Mesmo problema que acima
- **Gera 2 warnings** (nos testes unitários)

---

### 3.3. Problema 3: `datetime.utcnow()` em [tests/unit/test_schemas.py](../../tests/unit/test_schemas.py#L210-L211)

**Localização:** `tests/unit/test_schemas.py`, linhas 210-211

**Código atual:**
```python
def test_execucao_response_computed_duracao(self):
    """Testa resposta com duração computada."""
    duracao = datetime.utcnow() - datetime.utcnow() - timedelta(hours=3)  # ⚠️ DEPRECATED
```

**Descrição:**
- Mesmo problema
- **Gera 2 warnings** (nos testes de schemas)

---

## 4. Solução

### 4.1. Migração: `datetime.utcnow()` → `datetime.now(datetime.UTC)`

**Antes (Deprecado):**
```python
from datetime import datetime

target.updated_at = datetime.utcnow()
```

**Depois (Correto - Python 3.11+):**
```python
from datetime import datetime, UTC

target.updated_at = datetime.now(UTC)
```

**Compatibilidade:**
- ✅ Python 3.11+ (nativo)
- ✅ Python 3.10 (via `datetime.timezone.utc`)
- ✅ Fortemente tipado (timezone-aware)

### 4.2. Plano de Correção

#### 4.2.1. Arquivo: `toninho/models/base.py`

**Mudança necessária:**
1. Importar `UTC` ou `timezone`:
   ```python
   from datetime import UTC  # Python 3.11+
   # OU
   from datetime import timezone
   UTC = timezone.utc
   ```

2. Substituir chamada na linha 77:
   ```python
   # Antes:
   target.updated_at = datetime.utcnow()

   # Depois:
   target.updated_at = datetime.now(UTC)
   ```

**Impacto:** 4 warnings eliminados

---

#### 4.2.2. Arquivo: `tests/unit/test_models.py`

**Mudanças necessárias:**

Linhas 216-217, dentro do método `test_execucao_property_duracao()`:
```python
# Antes:
esperado_inicio=datetime.utcnow(),
esperado_fim=datetime.utcnow() + timedelta(hours=2)

# Depois:
esperado_inicio=datetime.now(UTC),
esperado_fim=datetime.now(UTC) + timedelta(hours=2)
```

**Impacto:** 2 warnings eliminados

---

#### 4.2.3. Arquivo: `tests/unit/test_schemas.py`

**Mudanças necessárias:**

Linhas 210-211, dentro do método `test_execucao_response_computed_duracao()`:
```python
# Antes:
duracao = datetime.utcnow() - datetime.utcnow() - timedelta(hours=3)

# Depois:
duracao = datetime.now(UTC) - datetime.now(UTC) - timedelta(hours=3)
```

**Impacto:** 2 warnings eliminados

---

## 5. Resultado Esperado

### Antes:
```
====================== 146 passed, 9573 warnings in 1.74s ======================
```

### Depois:
```
====================== 146 passed, 9565 warnings in 1.74s ======================
```

**Redução:** 8 warnings (0.08%)
**Novos warnings:** 0
**Warnings residuais:** 9.565 (de dependências - requer atualização das libraries)

---

## 6. Recomendações para PRDs Futuros

### 🔴 **CRÍTICO - Adicionar ao Checklist de Código**

Para **todos os PRDs que implementem funcionalidades**, adicionar os seguintes checklist items:

#### 6.1. Verificação de DateTime

- [ ] **Usar apenas `datetime.now(datetime.UTC)` e `datetime.now(timezone.utc)` para UTC**
  - ❌ **NUNCA** usar `datetime.utcnow()` (deprecado)
  - ❌ **NUNCA** usar `time.time()` (não timezone-aware)
  - ✅ **SEMPRE** usar `datetime.now(UTC)` ou `datetime.now(timezone.utc)`

**Exemplo correto:**
```python
from datetime import datetime, UTC, timedelta

class MinhaEntidade(Base):
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: datetime = Column(DateTime, onupdate=lambda: datetime.now(UTC))

    def refresh(self):
        self.last_refresh = datetime.now(UTC)
```

**Exemplo incorreto (REMOVER):**
```python
import datetime
default=datetime.datetime.utcnow()  # ❌ DEPRECATED
```

#### 6.2. Verificação de Warnings

- [ ] **Executar testes com `-W error` para falhar em deprecations:**
  ```bash
  poetry run pytest -W error::DeprecationWarning
  ```
  - Detecta novos warnings antes de mergear
  - Impede acúmulo de débito técnico

#### 6.3. Compatibilidade com Python Futuro

- [ ] **Revisar PRDs que mencionem Python 3.12+**
  - Deprecations significativas nessa versão
  - Validar se código é compatível

---

## 7. Impacto na Arquitetura

### 7.1. Segurança Temporal

A mudança para **timezone-aware datetimes** é mais segura:

| Aspecto | `utcnow()` | `now(UTC)` |
|--------|-----------|-----------|
| Timezone-aware | ❌ Não | ✅ Sim |
| Comparação segura | ⚠️ Manual | ✅ Nativa |
| Serialização JSON | ⚠️ Ambígua | ✅ Clara |
| Futura-proof | ❌ Deprecated | ✅ Recomendado |

### 7.2. Atualizar Documentação

Adicionar à [docs/base/inicio-projeto.md](../base/inicio-projeto.md):

```markdown
## Padrões de Data/Hora

Sempre use timezone-aware datetimes UTC:

✅ **Correto:**
from datetime import datetime, UTC
now = datetime.now(UTC)

❌ **Incorreto:**
import datetime
now = datetime.datetime.utcnow()  # Deprecated
```

---

## 8. Próximos Passos para Dependências

### ⏳ Ações Futuras (quando houver atualização das libs)

Quando as dependências forem atualizadas:

1. **pytest-asyncio >= 0.24.0** (usar `inspect.iscoroutinefunction`)
2. **FastAPI >= 0.110.0** (usar `inspect.iscoroutinefunction`)
3. **Starlette >= 0.37.0** (usar `inspect.iscoroutinefunction`)

Atualizar `pyproject.toml`:
```toml
pytest-asyncio = "^0.24.0"
fastapi = "^0.110.0"
starlette = "^0.37.0"
```

Resultado final: **0 warnings** (meta)

---

## 9. Checklist de Implementação

- [ ] Adicionar import `UTC` em `toninho/models/base.py`
- [ ] Substituir `datetime.utcnow()` → `datetime.now(UTC)` em `base.py`
- [ ] Adicionar import `UTC` em `tests/unit/test_models.py`
- [ ] Substituir `datetime.utcnow()` em `test_models.py` (linhas 216-217)
- [ ] Adicionar import `UTC` em `tests/unit/test_schemas.py`
- [ ] Substituir `datetime.utcnow()` em `test_schemas.py` (linhas 210-211)
- [ ] Executar `make test` e confirmar redução de warnings
- [ ] Adicionar guia de DateTime na documentação
- [ ] Adicionar checklist de warnings aos PRDs futuros
- [ ] Commit: "chore: Corrigir 8 warnings de datetime.utcnow() deprecado"

---

## 10. Referências

- [Python 3.12 datetime deprecation warnings](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow)
- [PEP 654 - Timezone-aware datetimes](https://www.python.org/dev/peps/pep-0495/)
- [Python 3.11 - UTC constant](https://docs.python.org/3.11/library/datetime.html#datetime.UTC)

---

**Autor**: Análise Automática de Warnings
**Data**: Março 2026
**Status**: Pronto para implementação
