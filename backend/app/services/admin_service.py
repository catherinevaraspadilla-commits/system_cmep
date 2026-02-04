"""
Servicio de administracion de usuarios (M5).
Ref: docs/claude/02_module_specs.md (M5)
"""

from fastapi import HTTPException, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.persona import Persona
from app.models.user import User, UserRole, UserRoleEnum, EstadoUser, Session
from app.models.empleado import Empleado, MedicoExtra, RolEmpleado, EstadoEmpleado
from app.schemas.admin import CreateUserRequest, UpdateUserRequest, ResetPasswordRequest, AdminUserDTO
from app.utils.hashing import hash_password


# ── Roles validos para operaciones ─────────────────────────────────────

VALID_ROLES = {r.value for r in UserRoleEnum}
OPERATIONAL_ROLES = {"OPERADOR", "GESTOR", "MEDICO"}


# ── Dependency: require_admin ──────────────────────────────────────────

async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency que lanza 403 si el usuario no es ADMIN."""
    user_roles = {r.user_role for r in current_user.roles}
    if "ADMIN" not in user_roles:
        raise HTTPException(status_code=403, detail="Solo ADMIN puede acceder a esta funcion")
    return current_user


# ── Helpers ────────────────────────────────────────────────────────────

def _build_user_dto(user: User, persona: Persona) -> dict:
    """Construye AdminUserDTO como dict."""
    return {
        "user_id": user.user_id,
        "user_email": user.user_email,
        "is_active": user.estado == EstadoUser.ACTIVO.value,
        "persona_id": persona.persona_id,
        "nombres": persona.nombres,
        "apellidos": persona.apellidos,
        "tipo_documento": persona.tipo_documento,
        "numero_documento": persona.numero_documento,
        "telefono": persona.celular_1,
        "email": persona.email,
        "celular_2": persona.celular_2,
        "telefono_fijo": persona.telefono_fijo,
        "fecha_nacimiento": persona.fecha_nacimiento,
        "direccion": persona.direccion,
        "comentario": persona.comentario,
        "roles": [r.user_role for r in user.roles],
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


async def _load_user_with_persona(db: AsyncSession, user_id: int) -> tuple[User, Persona]:
    """Carga User + Persona o lanza 404."""
    stmt = select(User).where(User.user_id == user_id).options(selectinload(User.roles))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    p_stmt = select(Persona).where(Persona.persona_id == user.persona_id)
    p_result = await db.execute(p_stmt)
    persona = p_result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    return user, persona


def _validate_roles(roles: list[str]) -> None:
    """Valida que todos los roles sean validos."""
    invalid = set(roles) - VALID_ROLES
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Roles invalidos: {', '.join(invalid)}. Validos: {', '.join(sorted(VALID_ROLES))}",
        )


# ── list_users ─────────────────────────────────────────────────────────

async def list_users(db: AsyncSession) -> list[dict]:
    """Lista todos los usuarios con persona y roles."""
    stmt = select(User).options(selectinload(User.roles)).order_by(User.user_id)
    result = await db.execute(stmt)
    users = result.scalars().all()

    items = []
    for user in users:
        p_stmt = select(Persona).where(Persona.persona_id == user.persona_id)
        p_result = await db.execute(p_stmt)
        persona = p_result.scalar_one_or_none()
        if persona:
            items.append(_build_user_dto(user, persona))

    return items


# ── create_user ────────────────────────────────────────────────────────

async def create_user(db: AsyncSession, data: CreateUserRequest, admin_user_id: int) -> dict:
    """Crea usuario nuevo con persona, roles, empleado y medico_extra si aplica."""
    _validate_roles(data.roles)

    # Verificar email unico
    normalized_email = data.user_email.strip().lower()
    existing = await db.execute(select(User).where(User.user_email == normalized_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    # Buscar persona existente por (tipo_documento, numero_documento)
    p_stmt = select(Persona).where(
        Persona.tipo_documento == data.tipo_documento,
        Persona.numero_documento == data.numero_documento,
    )
    p_result = await db.execute(p_stmt)
    persona = p_result.scalar_one_or_none()

    if persona:
        # R5: copiar email a persona si no tenia
        if not persona.email:
            persona.email = normalized_email
        # Actualizar nombres si proporcionados
        persona.nombres = data.nombres
        persona.apellidos = data.apellidos
        if data.telefono:
            persona.celular_1 = data.telefono
        if data.direccion is not None:
            persona.direccion = data.direccion
        if data.fecha_nacimiento is not None:
            persona.fecha_nacimiento = data.fecha_nacimiento
    else:
        persona = Persona(
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            nombres=data.nombres,
            apellidos=data.apellidos,
            email=normalized_email,
            celular_1=data.telefono,
            direccion=data.direccion,
            fecha_nacimiento=data.fecha_nacimiento,
            created_by=admin_user_id,
        )
        db.add(persona)
        await db.flush()

    # Verificar que persona_id no esta ya asignado a otro user
    existing_user = await db.execute(select(User).where(User.persona_id == persona.persona_id))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Esta persona ya tiene un usuario asociado")

    # Crear User
    user = User(
        persona_id=persona.persona_id,
        user_email=normalized_email,
        password_hash=hash_password(data.password),
        estado=EstadoUser.ACTIVO.value,
        created_by=admin_user_id,
    )
    db.add(user)
    await db.flush()

    # Crear UserRoles
    for rol in data.roles:
        db.add(UserRole(
            user_id=user.user_id,
            user_role=rol,
            created_by=admin_user_id,
        ))

    # Crear Empleado para roles operativos
    for rol in data.roles:
        if rol in OPERATIONAL_ROLES:
            # Verificar que no exista ya empleado con esa persona+rol
            emp_exists = await db.execute(
                select(Empleado).where(
                    Empleado.persona_id == persona.persona_id,
                    Empleado.rol_empleado == rol,
                )
            )
            if not emp_exists.scalar_one_or_none():
                db.add(Empleado(
                    persona_id=persona.persona_id,
                    rol_empleado=rol,
                    estado_empleado=EstadoEmpleado.ACTIVO.value,
                    created_by=admin_user_id,
                ))

    # R11: Crear MedicoExtra si rol MEDICO
    if "MEDICO" in data.roles:
        me_exists = await db.execute(
            select(MedicoExtra).where(MedicoExtra.persona_id == persona.persona_id)
        )
        if not me_exists.scalar_one_or_none():
            db.add(MedicoExtra(
                persona_id=persona.persona_id,
                created_by=admin_user_id,
            ))

    await db.flush()

    # Reload user with roles
    user, persona = await _load_user_with_persona(db, user.user_id)
    return _build_user_dto(user, persona)


# ── update_user ────────────────────────────────────────────────────────

async def update_user(
    db: AsyncSession, user_id: int, data: UpdateUserRequest, admin_user_id: int
) -> dict:
    """Actualiza datos del usuario: persona, roles, estado."""
    user, persona = await _load_user_with_persona(db, user_id)

    # Prevenir auto-suspension
    if data.is_active is False and user_id == admin_user_id:
        raise HTTPException(status_code=400, detail="No puedes suspenderte a ti mismo")

    # Actualizar campos de persona
    if data.nombres is not None:
        persona.nombres = data.nombres
    if data.apellidos is not None:
        persona.apellidos = data.apellidos
    if data.telefono is not None:
        persona.celular_1 = data.telefono
    if data.email is not None:
        persona.email = data.email
    if data.celular_2 is not None:
        persona.celular_2 = data.celular_2
    if data.telefono_fijo is not None:
        persona.telefono_fijo = data.telefono_fijo
    if data.fecha_nacimiento is not None:
        persona.fecha_nacimiento = data.fecha_nacimiento
    if data.direccion is not None:
        persona.direccion = data.direccion
    if data.tipo_documento is not None:
        persona.tipo_documento = data.tipo_documento
    if data.numero_documento is not None:
        persona.numero_documento = data.numero_documento
    if data.comentario is not None:
        persona.comentario = data.comentario
    persona.updated_by = admin_user_id

    # Actualizar roles (delete + recreate)
    if data.roles is not None:
        _validate_roles(data.roles)
        # Eliminar roles existentes
        await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        await db.flush()
        # Crear nuevos
        for rol in data.roles:
            db.add(UserRole(
                user_id=user_id,
                user_role=rol,
                created_by=admin_user_id,
            ))
        # Crear Empleado para nuevos roles operativos
        for rol in data.roles:
            if rol in OPERATIONAL_ROLES:
                emp_exists = await db.execute(
                    select(Empleado).where(
                        Empleado.persona_id == persona.persona_id,
                        Empleado.rol_empleado == rol,
                    )
                )
                if not emp_exists.scalar_one_or_none():
                    db.add(Empleado(
                        persona_id=persona.persona_id,
                        rol_empleado=rol,
                        estado_empleado=EstadoEmpleado.ACTIVO.value,
                        created_by=admin_user_id,
                    ))
        # R11: MedicoExtra si se agrega MEDICO
        if "MEDICO" in data.roles:
            me_exists = await db.execute(
                select(MedicoExtra).where(MedicoExtra.persona_id == persona.persona_id)
            )
            if not me_exists.scalar_one_or_none():
                db.add(MedicoExtra(
                    persona_id=persona.persona_id,
                    created_by=admin_user_id,
                ))

    # Actualizar estado (suspender / reactivar)
    if data.is_active is not None:
        new_estado = EstadoUser.ACTIVO.value if data.is_active else EstadoUser.SUSPENDIDO.value
        user.estado = new_estado
        user.updated_by = admin_user_id

        # R13: invalidar sesiones al suspender
        if not data.is_active:
            await db.execute(delete(Session).where(Session.user_id == user_id))

    await db.flush()

    # Expire stale cached relationships before reload
    db.expire_all()

    # Reload
    user, persona = await _load_user_with_persona(db, user_id)
    return _build_user_dto(user, persona)


# ── reset_user_password ────────────────────────────────────────────────

async def reset_user_password(
    db: AsyncSession, user_id: int, data: ResetPasswordRequest, admin_user_id: int
) -> None:
    """Resetea password del usuario e invalida sus sesiones."""
    user, _persona = await _load_user_with_persona(db, user_id)

    user.password_hash = hash_password(data.new_password)
    user.updated_by = admin_user_id

    # R13: invalidar sesiones al cambiar password
    await db.execute(delete(Session).where(Session.user_id == user_id))
    await db.flush()
