"""
Servicio de autenticacion y gestion de sesiones.
Ref: docs/source/05_api_y_policy.md seccion Auth
Ref: docs/source/02_modelo_de_datos.md secciones 2.2.7, 2.2.10 (R7, R12, R13)
"""

from datetime import timedelta

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, Session, EstadoUser
from app.utils.hashing import verify_password
from app.utils.time import utcnow


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User | None:
    """
    Autentica usuario por email + password.
    Email se normaliza a lower(trim()) segun R3/R5.
    Retorna User si credenciales validas, None si no.
    """
    normalized_email = email.strip().lower()
    stmt = select(User).where(User.user_email == normalized_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_session(db: AsyncSession, user_id: int) -> Session:
    """Crea sesion server-side. Ref: doc 02, seccion 2.2.10."""
    session = Session(
        user_id=user_id,
        created_at=utcnow(),
        expires_at=utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS),
        last_seen_at=utcnow(),
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_with_user(
    db: AsyncSession, session_id: str
) -> tuple[Session, User] | None:
    """
    Recupera sesion valida con su usuario.
    Invalida si expirada o usuario SUSPENDIDO (R7, R13).
    """
    stmt = select(Session).where(Session.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        return None

    # Sesion expirada
    if session.expires_at < utcnow():
        await db.delete(session)
        await db.flush()
        return None

    # Cargar usuario
    user_stmt = select(User).where(User.user_id == session.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user is None:
        return None

    # R7/R13: usuario suspendido invalida sesion
    if user.estado == EstadoUser.SUSPENDIDO.value:
        await invalidate_user_sessions(db, user.user_id)
        return None

    # Actualizar last_seen_at
    session.last_seen_at = utcnow()
    await db.flush()

    return session, user


async def invalidate_session(db: AsyncSession, session_id: str) -> None:
    """Elimina una sesion especifica (logout)."""
    stmt = delete(Session).where(Session.session_id == session_id)
    await db.execute(stmt)
    await db.flush()


async def invalidate_user_sessions(db: AsyncSession, user_id: int) -> None:
    """Invalida todas las sesiones de un usuario (R13: suspension)."""
    stmt = delete(Session).where(Session.user_id == user_id)
    await db.execute(stmt)
    await db.flush()


def build_user_dto(user: User) -> dict:
    """
    Construye UserDTO para respuestas de auth.
    Ref: docs/source/06_ui_paginas_y_contratos.md — UserDTO
    """
    # Cargar persona para display_name (relacion eager via select)
    return {
        "user_id": user.user_id,
        "user_email": user.user_email,
        "estado": user.estado,
        "roles": [r.user_role for r in user.roles],
        "permissions_extra": [p.permission_code for p in user.permissions],
        "display_name": user.user_email,  # Se actualizara cuando carguemos persona
    }
