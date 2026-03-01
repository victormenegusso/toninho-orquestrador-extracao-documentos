# PRD-011: Sistema de Extração

**Status**: 📋 Pronto para implementação  
**Prioridade**: 🟡 Média - Backend Features Avançadas (Prioridade 3)  
**Categoria**: Backend - Features Avançadas  
**Estimativa**: 8-10 horas

---

## 1. Objetivo

Implementar o sistema de extração de conteúdo web usando Docling e httpx. Responsável por buscar páginas, extrair conteúdo, converter para markdown e salvar em filesystem local. Inclui tratamento de erros, retry, cache HTTP e storage abstrato.

## 2. Contexto e Justificativa

Este é o coração funcional do Toninho: extrair conteúdo de URLs e converter para markdown. Utiliza:
- **httpx**: HTTP client async para requests
- **docling**: Extração e conversão para markdown
- **Storage Interface**: Abstração para salvar arquivos (local/S3/etc)

**Features:**
- Extração de conteúdo HTML
- Conversão para markdown estruturado
- Metadados (título, URL, data)
- Retry automático em falhas de rede
- Cache HTTP para evitar requests duplicados
- Timeout configurável
- Suporte a headless browser (via docling) para sites JS

## 3. Requisitos Técnicos

### 3.1. Estrutura de Arquivos

```
toninho/extraction/
├── __init__.py
├── extractor.py              # Classe principal PageExtractor
├── storage.py                # Storage interfaces e implementações
├── http_client.py            # Cliente HTTP com retry e cache
├── markdown_converter.py     # Conversão para markdown
└── utils.py                  # Utilidades (sanitize filename, etc)
```

### 3.2. Storage Interface (toninho/extraction/storage.py)

**Interface abstrata:**
```python
from abc import ABC, abstractmethod
from typing import BinaryIO, List
from pathlib import Path

class StorageInterface(ABC):
    """Interface abstrata para diferentes tipos de armazenamento"""
    
    @abstractmethod
    async def save_file(self, path: str, content: bytes) -> str:
        """Salva arquivo e retorna o caminho/URL"""
        pass
    
    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """Recupera arquivo do storage"""
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """Deleta arquivo do storage"""
        pass
    
    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """Lista arquivos em um diretório"""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Verifica se arquivo existe"""
        pass
```

**Implementação Local Filesystem:**
```python
class LocalFileSystemStorage(StorageInterface):
    """Implementação para filesystem local"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_file(self, path: str, content: bytes) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content)
        
        return str(full_path)
    
    async def get_file(self, path: str) -> bytes:
        full_path = self.base_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, path: str) -> bool:
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    async def list_files(self, directory: str) -> List[str]:
        dir_path = self.base_dir / directory
        if not dir_path.exists():
            return []
        return [str(f.relative_to(self.base_dir)) for f in dir_path.rglob("*") if f.is_file()]
    
    def exists(self, path: str) -> bool:
        return (self.base_dir / path).exists()
```

**Factory para criar storage:**
```python
def get_storage(storage_type: str = "local", **kwargs) -> StorageInterface:
    if storage_type == "local":
        return LocalFileSystemStorage(kwargs.get("base_dir", "./output"))
    elif storage_type == "s3":
        # Implementação futura
        raise NotImplementedError("S3 storage not implemented yet")
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
```

### 3.3. HTTP Client (toninho/extraction/http_client.py)

**HTTPClient com retry e timeout:**
```python
import httpx
from typing import Optional, Dict
from loguru import logger

class HTTPClient:
    """Cliente HTTP com retry, timeout e cache"""
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        cache_enabled: bool = True
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, bytes] = {}  # Simple in-memory cache (melhorar com Redis)
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers={"User-Agent": "Toninho/1.0"}
        )
    
    async def get(self, url: str) -> Dict[str, any]:
        """
        Faz GET request com retry e cache
        
        Returns:
            dict com keys: content, status_code, headers, from_cache
        """
        # Check cache
        if self.cache_enabled and url in self.cache:
            logger.debug(f"Cache hit for {url}")
            return {
                "content": self.cache[url],
                "status_code": 200,
                "from_cache": True
            }
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                
                content = response.content
                
                # Cache successful response
                if self.cache_enabled and response.status_code == 200:
                    self.cache[url] = content
                
                return {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "from_cache": False
                }
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [404, 403, 401]:
                    # Não fazer retry em erros de cliente
                    raise
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts")
    
    async def close(self):
        await self.client.aclose()
```

### 3.4. Page Extractor (toninho/extraction/extractor.py)

**Classe principal:**
```python
from typing import Dict, Optional
from docling import Docling  # Biblioteca para extração
from toninho.extraction.http_client import HTTPClient
from toninho.extraction.storage import StorageInterface
from loguru import logger

class PageExtractor:
    """Extrator de páginas web para markdown"""
    
    def __init__(
        self,
        storage: StorageInterface,
        timeout: int = 30,
        max_retries: int = 3,
        use_headless: bool = False
    ):
        self.storage = storage
        self.http_client = HTTPClient(timeout=timeout, max_retries=max_retries)
        self.use_headless = use_headless
    
    async def extract(self, url: str, output_path: str) -> Dict[str, any]:
        """
        Extrai conteúdo de URL e salva como markdown
        
        Args:
            url: URL para extrair
            output_path: Caminho relativo para salvar arquivo
        
        Returns:
            dict com informações da extração
        
        Raises:
            Exception: Em caso de erro
        """
        try:
            logger.info(f"Extracting: {url}")
            
            # 1. Fetch HTML
            response = await self.http_client.get(url)
            html_content = response["content"]
            
            # 2. Extract usando Docling
            extracted = await self._extract_with_docling(html_content, url)
            
            # 3. Convert to markdown
            markdown_content = self._convert_to_markdown(extracted)
            
            # 4. Add metadata
            markdown_with_metadata = self._add_metadata(
                markdown_content,
                url=url,
                title=extracted.get("title", ""),
                timestamp=datetime.utcnow()
            )
            
            # 5. Save file
            saved_path = await self.storage.save_file(
                output_path,
                markdown_with_metadata.encode("utf-8")
            )
            
            logger.info(f"Saved to: {saved_path}")
            
            return {
                "status": "success",
                "url": url,
                "path": saved_path,
                "bytes": len(markdown_with_metadata),
                "title": extracted.get("title", ""),
                "from_cache": response.get("from_cache", False)
            }
            
        except Exception as e:
            logger.error(f"Error extracting {url}: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    async def _extract_with_docling(self, html_content: bytes, url: str) -> Dict:
        """Extrai conteúdo estruturado usando Docling"""
        # Integração com Docling
        # Nota: Docling API pode variar, adaptar conforme documentação
        docling = Docling()
        
        if self.use_headless:
            # Usar headless browser para sites JS pesados
            result = await docling.extract_from_url(url, headless=True)
        else:
            # Parse HTML diretamente
            result = await docling.extract_from_html(html_content, base_url=url)
        
        return {
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "headings": result.get("headings", []),
            "links": result.get("links", []),
            "images": result.get("images", [])
        }
    
    def _convert_to_markdown(self, extracted: Dict) -> str:
        """Converte conteúdo extraído para markdown"""
        # Docling já retorna markdown, mas podemos processar
        markdown = extracted.get("content", "")
        
        # Processar: limpar, formatar, etc
        markdown = self._clean_markdown(markdown)
        
        return markdown
    
    def _clean_markdown(self, markdown: str) -> str:
        """Limpa e normaliza markdown"""
        # Remove múltiplas linhas vazias
        import re
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove espaços em branco no final das linhas
        lines = [line.rstrip() for line in markdown.split('\n')]
        
        return '\n'.join(lines)
    
    def _add_metadata(
        self,
        content: str,
        url: str,
        title: str,
        timestamp: datetime
    ) -> str:
        """Adiciona frontmatter com metadados"""
        metadata = [
            "---",
            f"url: {url}",
            f"title: {title}",
            f"extracted_at: {timestamp.isoformat()}",
            f"extractor: Toninho v1.0",
            "---",
            "",
            content
        ]
        
        return '\n'.join(metadata)
    
    def generate_filename(self, url: str) -> str:
        """Gera nome de arquivo seguro a partir da URL"""
        from urllib.parse import urlparse
        import re
        
        parsed = urlparse(url)
        path = parsed.path.strip('/').replace('/', '-')
        
        if not path:
            path = "index"
        
        # Remove caracteres inválidos
        path = re.sub(r'[^\w\-]', '_', path)
        
        # Limite de tamanho
        if len(path) > 100:
            path = path[:100]
        
        return f"{path}.md"
    
    async def close(self):
        await self.http_client.close()
```

## 4. Dependências

### 4.1. Bibliotecas
- httpx: ^0.26.0
- docling: (verificar versão disponível)
- loguru: ^0.7.2

### 4.2. Dependências de Outros PRDs
- PRD-010: Workers (integração com ExtractionOrchestrator)

## 5. Regras de Negócio

### 5.1. Extração
- Timeout padrão: 30 segundos (configurável)
- Retry automático: 3 tentativas
- Backoff exponencial: 1s, 2s, 4s

### 5.2. Formato de Saída
- Markdown com frontmatter YAML
- Metadados: URL, title, extracted_at, extractor
- Encoding: UTF-8

### 5.3. Nome de Arquivo
- Gerado a partir da URL path
- Caracteres seguros apenas
- Máximo 100 caracteres
- Extensão: .md

### 5.4. Storage
- MVP: Local filesystem em OUTPUT_DIR
- Interface preparada para S3/GCS (futuro)

### 5.5. Cache HTTP
- In-memory cache simples no MVP
- Futuro: Redis cache
- Cache apenas responses 200 OK

## 6. Casos de Teste

### 6.1. Storage Tests
- ✅ LocalFileSystemStorage: save_file cria arquivo
- ✅ LocalFileSystemStorage: get_file lê arquivo
- ✅ LocalFileSystemStorage: delete_file remove arquivo
- ✅ LocalFileSystemStorage: list_files lista arquivos
- ✅ LocalFileSystemStorage: exists verifica existência

### 6.2. HTTP Client Tests
- ✅ HTTPClient: fetch com sucesso
- ✅ HTTPClient: retry em timeout
- ✅ HTTPClient: não retry em 404
- ✅ HTTPClient: cache funciona
- ✅ HTTPClient: backoff exponencial

### 6.3. Extractor Tests
- ✅ PageExtractor: extrai página com sucesso
- ✅ PageExtractor: gera nome de arquivo válido
- ✅ PageExtractor: adiciona metadados
- ✅ PageExtractor: lida com erros de rede
- ✅ PageExtractor: salva arquivo no storage

### 6.4. Integration Tests
- ✅ Extração end-to-end de URL real
- ✅ Arquivo markdown gerado está válido
- ✅ Metadados presentes no arquivo

## 7. Critérios de Aceitação

### ✅ Storage
- [ ] Storage interface definida
- [ ] LocalFileSystemStorage implementado
- [ ] Factory de storage funcional

### ✅ HTTP Client
- [ ] HTTPClient com retry
- [ ] Cache HTTP funcional
- [ ] Timeout configurável

### ✅ Extractor
- [ ] PageExtractor extrai páginas
- [ ] Conversão para markdown
- [ ] Metadados adicionados
- [ ] Nome de arquivo gerado corretamente

### ✅ Integração
- [ ] Integração com Docling
- [ ] Salva arquivos no storage
- [ ] Pode ser usado por workers

### ✅ Testes
- [ ] Testes com cobertura > 85%
- [ ] Testes end-to-end

## 8. Notas de Implementação

### 8.1. Docling
Docling é uma biblioteca fictícia para este exemplo. Na prática, usar:
- BeautifulSoup4 + html2text
- Ou Trafilatura
- Ou Playwright para sites JS

### 8.2. Usage no Worker
```python
from toninho.extraction.extractor import PageExtractor
from toninho.extraction.storage import get_storage

storage = get_storage("local", base_dir="./output/processo-123")
extractor = PageExtractor(storage, timeout=60)

resultado = await extractor.extract(
    url="https://example.com/page",
    output_path="example-page.md"
)
```

### 8.3. Pontos de Atenção
- Docling pode não existir, adaptar para biblioteca real
- Cache HTTP em production usar Redis
- Headless browser pesado, usar apenas se necessário
- Tratamento de encoding (UTF-8, latin1, etc)
- Limites de tamanho de página (max 10MB)

## 9. Referências Técnicas

- **httpx**: https://www.python-httpx.org/
- **Trafilatura**: https://github.com/adbar/trafilatura
- **html2text**: https://github.com/Alir3z4/html2text/

## 10. Definição de Pronto

- ✅ Storage interface e implementação local
- ✅ HTTP client com retry e cache
- ✅ PageExtractor extrai e converte páginas
- ✅ Metadados adicionados aos arquivos
- ✅ Integração funcional com Workers
- ✅ Testes com cobertura > 85%
- ✅ Pode extrair páginas reais para markdown

---

**PRD Anterior**: PRD-010 - Workers e Processamento Assíncrono  
**Próximo PRD**: PRD-012 - Monitoramento e Métricas
