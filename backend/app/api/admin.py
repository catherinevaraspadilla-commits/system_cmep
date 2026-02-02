"""
API endpoints: administracion de usuarios (M5).
Ref: docs/claude/02_module_specs.md (M5)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.admin import CreateUserRequest, UpdateUserRequest, ResetPasswordRequest
from app.services.admin_service import (
    require_admin,
    list_users,
    create_user,
    update_user,
    reset_user_password,
)
from app.services.policy import POLICY

router = APIRouter(prefix="/admin", tags=["admin"])


# ── GET /admin/usuarios ───────────────────────────────────────────────

@router.get("/usuarios")
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lista todos los usuarios (solo ADMIN)."""
    items = await list_users(db)
    return {"ok": True, "data": items}


# ── POST /admin/usuarios ──────────────────────────────────────────────

@router.post("/usuarios", status_code=201)
async def crear_usuario(
    body: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Crear usuario nuevo (solo ADMIN)."""
    dto = await create_user(db, body, admin.user_id)
    return {"ok": True, "data": dto}


# ── PATCH /admin/usuarios/{user_id} ───────────────────────────────────

@router.patch("/usuarios/{user_id}")
async def editar_usuario(
    user_id: int,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Editar usuario: datos, roles, suspender/reactivar (solo ADMIN)."""
    dto = await update_user(db, user_id, body, admin.user_id)
    return {"ok": True, "data": dto}


# ── POST /admin/usuarios/{user_id}/reset-password ─────────────────────

@router.post("/usuarios/{user_id}/reset-password")
async def resetear_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Resetear password de un usuario (solo ADMIN)."""
    await reset_user_password(db, user_id, body, admin.user_id)
    return {"ok": True, "message": "Password reseteado exitosamente"}


# ── GET /admin/permisos ──────────────────────────────────────────────

@router.get("/permisos")
async def obtener_permisos(
    admin: User = Depends(require_admin),
):
    """Retorna la POLICY de permisos por rol (solo ADMIN)."""
    return {"ok": True, "data": POLICY}
