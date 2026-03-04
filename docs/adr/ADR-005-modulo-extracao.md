# ADR-005: Módulo de Extração (httpx + BeautifulSoup + html2text)

**Status**: Aceito
**Data**: 2025
**Contexto**: Extração de conteúdo web para markdown requer HTTP client, parser HTML e conversor.

---

## Decisão

Pipeline de extração:

```
URL → HTTPClient (httpx) → HTML → BeautifulSoup (título/meta) → html2text → Markdown limpo → Storage
```

| Componente | Tecnologia | Papel |
|---|---|---|
| HTTP client | `httpx` (async) | Fetch com retry, cache, timeout |
| HTML parser | `BeautifulSoup4` | Extração de título, limpeza de DOM |
| MD converter | `html2text` | Conversão HTML → Markdown |
| Cache | `hishel` (httpx cache) | Evita re-downloads, TTL configurável |
| Storage | `StorageInterface` (Strategy) | Abstração local/S3 |

## Razões

- **httpx**: suporte async nativo, interface mais moderna que `requests`, compatível com `hishel`.
- **BeautifulSoup4**: maturidade, suporte amplo a parsers (`lxml`, `html.parser`).
- **html2text**: output markdown limpo, sem dependências pesadas.
- **StorageInterface (Strategy Pattern)**: troca de backend de storage sem alterar lógica de extração.

## Consequências

- Output: arquivos `.md` com YAML frontmatter (URL, título, data, tamanho).
- Cache HTTP armazenado em disco, TTL padrão 3600s (configurável).
- Extração de sites com JS pesado (SPAs) não suportada (sem headless browser).
