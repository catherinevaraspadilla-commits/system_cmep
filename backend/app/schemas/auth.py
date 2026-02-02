"""
Schemas Pydantic para el modulo Auth.
Ref: docs/source/05_api_y_policy.md seccion Auth
Ref: docs/source/06_ui_paginas_y_contratos.md — UserDTO
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class UserDTO(BaseModel):
    user_id: int
    user_email: str
    estado: str
    roles: list[str]
    permissions_extra: list[str]
    display_name: str


class LoginResponse(BaseModel):
    ok: bool = True
    data: dict  # {"user": UserDTO}


class MeResponse(BaseModel):
    ok: bool = True
    data: dict  # {"user": UserDTO}
