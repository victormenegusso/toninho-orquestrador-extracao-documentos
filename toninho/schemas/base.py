"""
Base schema e configurações compartilhadas para todos os schemas Pydantic.

Define o BaseSchema com ConfigDict padrão e convenções de nomenclatura.
"""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Schema base para todos os schemas Pydantic do Toninho.

    Define configuração padrão compartilhada por todos os schemas,
    incluindo serialização, validação e conversão de ORM models.
    """

    model_config = ConfigDict(
        # Permite conversão de ORM models para schemas
        from_attributes=True,
        # Serializa enums como valores (não nomes)
        use_enum_values=True,
        # Aceita aliases de campos
        populate_by_name=True,
        # Remove whitespace de strings automaticamente
        str_strip_whitespace=True,
        # Valida valores durante atribuições (não apenas na criação)
        validate_assignment=True,
        # Serialização JSON otimizada
        json_schema_serialization_defaults_required=True,
    )
