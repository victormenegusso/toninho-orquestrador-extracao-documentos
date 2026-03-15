# descrição

Hoje a extração de dados no toninho é feita da maneira descrita abaixo:

## Resumo da Extração

Orquestração: PageExtractor.extract() — busca HTML → converte → adiciona frontmatter → salva. Veja extractor.py:1-200.
Busca de HTML: HTTPClient para requisições async com retry/caching/rate-limit (http_client.py:1-200); BrowserClient (Playwright) para páginas com JS (browser_client.py:1-200).
Conversão HTML → Markdown: extract_from_html() usa BeautifulSoup para título e html2text para converter; depois clean_markdown() e build_markdown_with_metadata() adiciona YAML frontmatter. Código em markdown_converter.py:1-200.
Armazenamento: abstração StorageInterface e implementação local LocalFileSystemStorage grava em output via save_file() — storage.py:1-200.
Integração / persistência: o service grava metadados no banco (model PaginaExtraida) e fornece download/remoção — pagina_extraida_service.py:1-200.

## Observações rápidas

O modo headless (Playwright) é opcional e requer instalação (pip install playwright + playwright install chromium).
Conversão e limpeza ficam em markdown_converter.py — ajustar configurações do html2text altera saída Markdown.
HTTPClient aplica retries, backoff exponencial e cache in-memory; useful para reduzir requisições duplicadas.


## Uma nova prospota

Gostaria de de uma nova forma de extrair os dados, Onde na configuração do processo, o usuário possa escolher entre 2 formas de extração:

- atual: usando o PageExtractor
- nova: usando o Docling, uma ferramenta de extração de dados estruturados a partir de documentos, que pode ser mais eficiente para certos tipos de conteúdo.

### Docling

O **Docling** (desenvolvido pela IBM Research) é uma ferramenta excelente para essa tarefa. Ele foi projetado justamente para converter documentos complexos — incluindo **HTML, PDFs, DOCX e imagens** — em formatos prontos para modelos de linguagem (LLMs), sendo o **Markdown** o principal deles.

Aqui está como ele lida com o HTML e por que ele se destaca:

#### Por que usar o Docling para HTML?

Diferente de bibliotecas de "scraping" puro que apenas limpam as tags, o Docling foca na **preservação da estrutura semântica**.

* **Hierarquia de Títulos:** Ele identifica corretamente o que é um `# h1`, `## h2`, etc.
* **Tabelas Complexas:** Um dos maiores pontos fortes do Docling é a capacidade de converter tabelas HTML em tabelas Markdown bem formatadas, mantendo a relação entre os dados.
* **Listas e Links:** Converte listas ordenadas/não ordenadas e preserva os links de forma limpa.
* **Metadados:** Ele consegue extrair metadados da página enquanto limpa o "ruído" (como scripts de anúncios ou menus de navegação).

---

#### Exemplo Rápido de Uso (Python)

Se você já tem o Docling instalado (`pip install docling`), o código para converter uma URL ou arquivo local é muito direto:

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

source = "https://www.exemplo.com"  # Pode ser uma URL ou caminho de arquivo .html
converter = DocumentConverter()
result = converter.convert(source)

# Exportando para Markdown
print(result.document.export_to_markdown())

```

---

#### O Diferencial: Docling vs. Outras Ferramentas

| Recurso | Beautiful Soup | Docling |
| --- | --- | --- |
| **Objetivo** | Parsing genérico de tags | Conversão estruturada para IA |
| **Esforço** | Exige código manual para cada site | Automático e "out-of-the-box" |
| **Tabelas** | Difícil de converter para MD | Excelente suporte nativo |
| **Output** | Texto bruto ou árvore HTML | Markdown, JSON ou Document Object |

#### Quando ele brilha?

O Docling é ideal se o seu objetivo final for alimentar um sistema de **RAG (Retrieval-Augmented Generation)**. Como o Markdown resultante é limpo e estruturado, o seu LLM terá muito mais facilidade para entender o contexto do que se você enviasse o HTML "sujo".

#### Como ele mantém a semântica?

O Docling utiliza uma abordagem chamada **Document Layout Analysis (DLA)**. Em vez de apenas ler o código fonte de cima para baixo, ele tenta "enxergar" o documento como um todo.

1. **Reconhecimento de Estrutura:** Ele identifica o papel de cada bloco (se é um parágrafo, um cabeçalho, uma nota de rodapé ou uma célula de tabela).
2. **Agrupamento Lógico:** Ele entende que uma imagem e a legenda logo abaixo dela pertencem ao mesmo contexto.
3. **Conversão de Tabelas:** Ele reconstrói a lógica de linhas e colunas, mesmo que o HTML original use estruturas complexas ou aninhadas.

### Ele usa IA?

**Sim, mas de forma híbrida.**

O Docling não é apenas um "prompt" enviado para o ChatGPT. Ele utiliza modelos de **Deep Learning** leves e especializados (como redes neurais convolucionais e transformadores de visão) para:

* **Segmentação de Layout:** Detectar onde termina um bloco e começa outro.
* **Table Structure Recognition:** O Docling utiliza modelos de visão computacional especificamente treinados para entender tabelas.
* **OCR (Opcional):** Se o seu HTML contiver imagens com texto ou se você estiver convertendo um PDF, ele utiliza IA para "ler" essas imagens.

O uso desses modelos locais garante que ele seja muito mais preciso que um conversor baseado em regras (Regex), mas ainda assim muito rápido.

---

#### Existe um limite para o uso?

Aqui estão as boas notícias sobre "limites":

* **Licença (Open Source):** O Docling é distribuído sob a **Licença Apache 2.0**. Isso significa que ele é gratuito para uso pessoal e comercial, sem taxas de licenciamento.
* **Sem Limite de Requisições:** Como ele roda **localmente na sua máquina** (via Python), não há uma API externa te cobrando por página ou por caractere. Você pode processar milhões de documentos se tiver hardware para isso.
* **Hardware:** O limite é o seu computador. Para documentos muito grandes ou uso intenso de OCR, ter uma GPU ajuda, mas ele roda perfeitamente em CPUs modernas.
* **Complexidade do Site:** O limite técnico principal aparece em sites que dependem excessivamente de JavaScript pesado para renderizar o conteúdo (Single Page Applications - SPAs). Nesses casos, você pode precisar "pré-renderizar" o HTML antes de passá-lo ao Docling.

---

#### Comparativo de Processamento

| Tipo de Processamento | Método | Dependência de Nuvem | Custo |
| --- | --- | --- | --- |
| **Padrão (HTML/Docx)** | Heurística + Modelos Leves | Zero (Local) | Grátis |
| **Complexo (PDF/Imagens)** | IA de Visão (Layout Analysis) | Zero (Local) | Grátis |
| **OCR** | Tesseract / EasyOCR | Zero (Local) | Grátis |

> **Nota:** Se você comparar com o **LlamaParse** (da LlamaIndex), por exemplo, o Docling leva vantagem por ser totalmente local e gratuito, enquanto o LlamaParse tem limites de páginas gratuitas por dia.

**Você pretende rodar o Docling em um servidor próprio ou quer testar a conversão de um site específico agora para ver o resultado?**
