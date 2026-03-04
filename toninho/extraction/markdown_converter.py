"""
Conversão de HTML para Markdown.

Utiliza html2text + BeautifulSoup para extrair e converter
conteúdo de páginas HTML em markdown estruturado.
"""

import re
from typing import Dict

import html2text
from bs4 import BeautifulSoup


def extract_title(html_content: bytes, base_url: str = "") -> str:
    """
    Extrai o título da página a partir do HTML.

    Tenta <title>, depois <h1>, e retorna string vazia se não encontrar.
    """
    try:
        soup = BeautifulSoup(html_content, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
    except Exception:
        pass
    return ""


def html_to_markdown(html_content: bytes, base_url: str = "") -> str:
    """
    Converte HTML em markdown usando html2text.

    Args:
        html_content: Conteúdo HTML em bytes
        base_url: URL base para resolver links relativos

    Returns:
        String com conteúdo em markdown
    """
    converter = html2text.HTML2Text()
    converter.IGNORE_LINKS = False
    converter.IGNORE_IMAGES = False
    converter.IGNORE_EMPHASIS = False
    converter.BODY_WIDTH = 0          # Sem quebra de linha forçada
    converter.UNICODE_SNOB = True
    converter.BYPASS_TABLES = False
    converter.PROTECT_LINKS = False

    if base_url:
        converter.baseurl = base_url

    try:
        text = html_content.decode("utf-8", errors="replace")
    except Exception:
        text = str(html_content)

    return converter.handle(text)


def clean_markdown(markdown: str) -> str:
    """
    Limpa e normaliza conteúdo markdown.

    - Remove múltiplas linhas em branco consecutivas
    - Remove espaços no final das linhas
    - Garante newline no final
    """
    # Normalizar quebras de linha
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    # Remover espaços em branco no final das linhas
    lines = [line.rstrip() for line in markdown.split("\n")]
    # Colapsar mais de 2 linhas em branco consecutivas
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Garantir newline no final
    return text.strip() + "\n"


def build_markdown_with_metadata(
    content: str,
    url: str,
    title: str,
    extracted_at: str,
) -> str:
    """
    Adiciona frontmatter YAML ao conteúdo markdown.

    Args:
        content: Conteúdo markdown
        url: URL de origem
        title: Título da página
        extracted_at: Timestamp ISO 8601

    Returns:
        Markdown com frontmatter YAML
    """
    frontmatter_lines = [
        "---",
        f"url: {url}",
        f'titulo: "{title}"',
        f"extraido_em: {extracted_at}",
        "extrator: Toninho v1.0",
        "---",
        "",
    ]
    return "\n".join(frontmatter_lines) + content


def extract_from_html(html_content: bytes, base_url: str = "") -> Dict:
    """
    Pipeline completo de extração: HTML → estrutura com título e markdown.

    Returns:
        Dict com keys: title (str), markdown (str)
    """
    title = extract_title(html_content, base_url)
    raw_md = html_to_markdown(html_content, base_url)
    cleaned_md = clean_markdown(raw_md)
    return {"title": title, "markdown": cleaned_md}
