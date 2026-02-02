"""
Endpoints de autenticacion (M1).
Ref: docs/source/05_api_y_policy.md seccion Auth
Ref: docs/claude/02_module_specs.md (M1 — endpoints)
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, EstadoUser
from app.models.persona import Persona
from app.schemas.auth import LoginRequest
from app.services.auth_service import (
    authenticate_user,
    create_session,
    invalidate_session,
    build_user_dto,
)
from app.middleware.session_middleware import get_current_user, SESSION_COOKIE_NAME
from app.utils.time import utcnow

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /auth/login
    Autentica por email+password, crea sesion, setea cookie.
    Ref: docs/source/05_api_y_policy.md
    """
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    # R7: usuario SUSPENDIDO no puede hacer login
    if user.estado == EstadoUser.SUSPENDIDO.value:
        raise HTTPException(status_code=403, detail="Usuario suspendido")

    # Crear sesion
    session = await create_session(db, user.user_id)

    # Actualizar last_login_at
    user.last_login_at = utcnow()
    await db.flush()

    # Cargar persona para display_name
    persona_stmt = select(Persona).where(Persona.persona_id == user.persona_id)
    persona_result = await db.execute(persona_stmt)
    persona = persona_result.scalar_one_or_none()

    user_dto = build_user_dto(user)
    if persona:
        user_dto["display_name"] = f"{persona.nombres} {persona.apellidos}"

    # Cookie httpOnly (R-001: CORS seguro)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_id,
        httponly=True,
        samesite="lax",
        secure=False,  # True en produccion
        max_age=86400,
        path="/",
    )

    return {"ok": True, "data": {"user": user_dto}}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    POST /auth/logout
    Invalida sesion actual, elimina cookie.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        await invalidate_session(db, session_id)

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /auth/me
    Retorna usuario actual + roles + permisos.
    Ref: docs/source/06_ui_paginas_y_contratos.md — UserDTO
    """
    # Cargar persona para display_name
    persona_stmt = select(Persona).where(Persona.persona_id == current_user.persona_id)
    persona_result = await db.execute(persona_stmt)
    persona = persona_result.scalar_one_or_none()

    user_dto = build_user_dto(current_user)
    if persona:
        user_dto["display_name"] = f"{persona.nombres} {persona.apellidos}"

    return {"ok": True, "data": {"user": user_dto}}
