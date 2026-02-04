"""
Schemas Pydantic para CRUD de promotores.
"""

from pydantic import BaseModel, Field, model_validator


class CreatePromotorRequest(BaseModel):
    tipo_promotor: str = Field(..., pattern="^(PERSONA|EMPRESA|OTROS)$")
    # PERSONA
    tipo_documento: str | None = None
    numero_documento: str | None = None
    nombres: str | None = None
    apellidos: str | None = None
    # EMPRESA
    razon_social: str | None = None
    # OTROS
    nombre_promotor_otros: str | None = None
    # Shared
    ruc: str | None = None
    email: str | None = None
    celular_1: str | None = None
    fuente_promotor: str | None = None
    comentario: str | None = None

    @model_validator(mode="after")
    def validate_by_type(self) -> "CreatePromotorRequest":
        if self.tipo_promotor == "PERSONA":
            if not self.nombres or not self.apellidos:
                raise ValueError("PERSONA requiere nombres y apellidos")
        elif self.tipo_promotor == "EMPRESA":
            if not self.razon_social:
                raise ValueError("EMPRESA requiere razon_social")
        elif self.tipo_promotor == "OTROS":
            if not self.nombre_promotor_otros:
                raise ValueError("OTROS requiere nombre_promotor_otros")
        return self


class UpdatePromotorRequest(BaseModel):
    # Campos directos del promotor
    razon_social: str | None = None
    nombre_promotor_otros: str | None = None
    ruc: str | None = None
    email: str | None = None
    celular_1: str | None = None
    fuente_promotor: str | None = None
    comentario: str | None = None
    # Para tipo PERSONA: actualizar persona vinculada
    nombres: str | None = None
    apellidos: str | None = None
