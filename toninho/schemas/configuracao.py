"""
Schemas para a entidade Configuracao.

Define schemas de entrada, saída e variações para operações com Configurações.
"""

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from toninho.models.enums import AgendamentoTipo, FormatoSaida
from toninho.schemas.base import BaseSchema
from toninho.schemas.validators import (
    validate_cron_expression,
    validate_path,
    validate_timeout,
    validate_urls_list,
)


class ConfiguracaoCreate(BaseSchema):
    """
    Schema para criação de configuração.

    Attributes:
        processo_id: ID do processo (opcional, pode ser setado na rota)
        urls: Lista de URLs para extração (1-100 URLs)
        timeout: Timeout em segundos (1-86400)
        max_retries: Número máximo de retentativas (0-10)
        formato_saida: Formato de saída dos arquivos
        output_dir: Diretório de saída
        agendamento_cron: Expressão cron (obrigatória se tipo=RECORRENTE)
        agendamento_tipo: Tipo de agendamento
    """

    processo_id: uuid.UUID | None = Field(
        None,
        description="ID do processo (setado automaticamente pela rota)",
    )
    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de URLs para extração",
        examples=[["https://exemplo.com", "https://exemplo.com/pagina2"]],
    )
    timeout: int = Field(
        default=3600,
        ge=1,
        le=86400,
        description="Timeout em segundos (máximo 24 horas)",
        examples=[3600, 7200],
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Número máximo de retentativas",
        examples=[3, 5],
    )
    formato_saida: FormatoSaida = Field(
        default=FormatoSaida.MULTIPLOS_ARQUIVOS,
        description="Formato de saída dos arquivos extraídos",
    )
    output_dir: str = Field(
        ...,
        description=(
            "Diretório de saída dos arquivos extraídos. "
            "Caminhos relativos com `./` são normalizados automaticamente "
            "(ex: `./output` → `output`). "
            "Os arquivos gerados seguem a estrutura: "
            "`{output_dir}/{processo_id}/{execucao_id}/{slug}.md`."
        ),
        examples=["/tmp/output", "./output", "output"],  # nosec B108
    )
    agendamento_cron: str | None = Field(
        None,
        description="Expressão cron para agendamento recorrente",
        examples=["0 */6 * * *", "0 0 * * *"],
    )
    agendamento_tipo: AgendamentoTipo = Field(
        default=AgendamentoTipo.MANUAL,
        description="Tipo de agendamento",
    )
    use_browser: bool = Field(
        default=False,
        description=(
            "Se True, usa Playwright (navegador headless) para renderizar páginas JavaScript (SPAs). "
            "Requer instalação de `playwright` e `playwright install chromium` no ambiente. "
            "Se False (padrão), usa httpx para extração HTTP simples."
        ),
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        """Valida lista de URLs."""
        return validate_urls_list(v)

    @field_validator("timeout")
    @classmethod
    def validate_timeout_range(cls, v: int) -> int:
        """Valida timeout."""
        return validate_timeout(v)

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str) -> str:
        """Valida e normaliza output_dir (remove ./ inicial se presente)."""
        return validate_path(v)

    @field_validator("agendamento_cron")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        """Valida expressão cron se fornecida."""
        if v is not None:
            return validate_cron_expression(v)
        return v

    def model_post_init(self, __context) -> None:
        """Valida consistência entre agendamento_tipo e agendamento_cron."""
        if self.agendamento_tipo == AgendamentoTipo.RECORRENTE:
            if not self.agendamento_cron:
                raise ValueError(
                    "agendamento_cron é obrigatório quando agendamento_tipo=RECORRENTE"
                )
        elif self.agendamento_cron:
            # Se não é recorrente mas tem cron, emite warning via log
            # (não bloqueia, mas pode ser melhorado)
            pass


class ConfiguracaoUpdate(BaseSchema):
    """
    Schema para atualização de configuração.

    Todos os campos são opcionais para permitir atualização parcial.
    """

    urls: list[str] | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Nova lista de URLs",
    )
    timeout: int | None = Field(
        None,
        ge=1,
        le=86400,
        description="Novo timeout",
    )
    max_retries: int | None = Field(
        None,
        ge=0,
        le=10,
        description="Novo max_retries",
    )
    formato_saida: FormatoSaida | None = Field(
        None,
        description="Novo formato de saída",
    )
    output_dir: str | None = Field(
        None,
        description="Novo diretório de saída",
    )
    agendamento_cron: str | None = Field(
        None,
        description="Nova expressão cron",
    )
    agendamento_tipo: AgendamentoTipo | None = Field(
        None,
        description="Novo tipo de agendamento",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str] | None) -> list[str] | None:
        """Valida lista de URLs se fornecida."""
        if v is not None:
            return validate_urls_list(v)
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout_range(cls, v: int | None) -> int | None:
        """Valida timeout se fornecido."""
        if v is not None:
            return validate_timeout(v)
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str | None) -> str | None:
        """Valida output_dir se fornecido."""
        if v is not None:
            return validate_path(v)
        return v

    @field_validator("agendamento_cron")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        """Valida expressão cron se fornecida."""
        if v is not None:
            return validate_cron_expression(v)
        return v


class ConfiguracaoResponse(BaseSchema):
    """
    Schema de resposta para configuração.

    Attributes:
        id: Identificador único
        processo_id: ID do processo
        urls: Lista de URLs
        timeout: Timeout em segundos
        max_retries: Número máximo de retentativas
        formato_saida: Formato de saída
        output_dir: Diretório de saída
        agendamento_cron: Expressão cron
        agendamento_tipo: Tipo de agendamento
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
    """

    id: uuid.UUID = Field(..., description="Identificador único")
    processo_id: uuid.UUID = Field(..., description="ID do processo")
    urls: list[str] = Field(..., description="Lista de URLs para extração")
    timeout: int = Field(..., description="Timeout em segundos")
    max_retries: int = Field(..., description="Número máximo de retentativas")
    formato_saida: FormatoSaida = Field(..., description="Formato de saída")
    output_dir: str = Field(
        ...,
        description=(
            "Diretório de saída (normalizado). "
            "Os arquivos extraídos são salvos em: "
            "`{output_dir}/{processo_id}/{execucao_id}/{slug}.md`."
        ),
    )
    agendamento_cron: str | None = Field(None, description="Expressão cron")
    agendamento_tipo: AgendamentoTipo = Field(..., description="Tipo de agendamento")
    use_browser: bool = Field(..., description="Se usa Playwright para renderizar JS")
    created_at: datetime = Field(..., description="Data/hora de criação")
    updated_at: datetime = Field(..., description="Data/hora da última atualização")


class AgendamentoInfo(BaseSchema):
    """
    Informações de agendamento retornadas pelo endpoint de validação.

    Attributes:
        expressao_cron: Expressão cron avaliada
        valida: Se a expressão é válida
        proximas_execucoes: Próximas 5 execuções calculadas
        descricao_legivel: Descrição em linguagem natural
    """

    expressao_cron: str = Field(..., description="Expressão cron avaliada")
    valida: bool = Field(..., description="Se a expressão é válida")
    proximas_execucoes: list[datetime] = Field(
        default_factory=list,
        description="Próximas 5 execuções",
    )
    descricao_legivel: str = Field(..., description="Descrição em linguagem natural")


# Aliases
ConfiguracaoInCreate = ConfiguracaoCreate
ConfiguracaoInUpdate = ConfiguracaoUpdate
ConfiguracaoOut = ConfiguracaoResponse
