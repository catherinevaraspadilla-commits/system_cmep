"""
Schemas Pydantic para administracion de usuarios (M5).
Ref: docs/claude/02_module_specs.md (M5)
"""

from datetime import datetime, date
from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    user_email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    nombres: str = Field(..., min_length=1, max_length=150)
    apellidos: str = Field(..., min_length=1, max_length=150)
    tipo_documento: str = Field(..., pattern="^(DNI|CE|PASAPORTE)$")
    numero_documento: str = Field(..., min_length=1, max_length=30)
    telefono: str | None = None
    direccion: str | None = None
    fecha_nacimiento: date | None = None
    roles: list[str] = Field(..., min_length=1)


class UpdateUserRequest(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None
    email: str | None = None
    celular_2: str | None = None
    telefono_fijo: str | None = None
    fecha_nacimiento: date | None = None
    direccion: str | None = None
    tipo_documento: str | None = None
    numero_documento: str | None = None
    comentario: str | None = None
    roles: list[str] | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Response schemas ──────────────────────────────────────────────────

class AdminUserDTO(BaseModel):
    user_id: int
    user_email: str
    is_active: bool
    persona_id: int
    nombres: str
    apellidos: str
    tipo_documento: str | None = None
    numero_documento: str | None = None
    telefono: str | None = None
    email: str | None = None
    celular_2: str | None = None
    telefono_fijo: str | None = None
    fecha_nacimiento: date | None = None
    direccion: str | None = None
    comentario: str | None = None
    roles: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
