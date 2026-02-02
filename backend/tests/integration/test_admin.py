"""
Tests de integracion: Administracion de usuarios (M5).
Ref: docs/claude/02_module_specs.md (M5)

CRUD de usuarios: listar, crear, editar, suspender, reactivar, resetear password.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.database import Base
from app.main import app
from app.models.persona import Persona
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum, Session
from app.models.empleado import Empleado, MedicoExtra, RolEmpleado, EstadoEmpleado
from app.utils.hashing import hash_password
from app.utils.time import utcnow
from datetime import timedelta

from tests.integration.conftest import test_engine, TestSessionLocal


def _cookies(session_id: str) -> dict:
    return {"cmep_session": session_id}


@pytest.fixture(autouse=True)
async def setup_db():
    """Crea tablas y datos para admin tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        # ── ADMIN user ──
        p_admin = Persona(
            tipo_documento="DNI", numero_documento="90000001",
            nombres="Admin", apellidos="Principal", email="admin@cmep.local",
        )
        db.add(p_admin)
        await db.flush()

        u_admin = User(
            persona_id=p_admin.persona_id,
            user_email="admin@cmep.local",
            password_hash=hash_password("admin123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(u_admin)
        await db.flush()
        db.add(UserRole(user_id=u_admin.user_id, user_role=UserRoleEnum.ADMIN.value))
        db.add(Session(
            session_id="test-admin-session",
            user_id=u_admin.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        # ── OPERADOR user (non-admin) ──
        p_op = Persona(
            tipo_documento="DNI", numero_documento="90000002",
            nombres="Ana", apellidos="Operadora", email="operador@cmep.local",
        )
        db.add(p_op)
        await db.flush()

        u_op = User(
            persona_id=p_op.persona_id,
            user_email="operador@cmep.local",
            password_hash=hash_password("operador123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(u_op)
        await db.flush()
        db.add(UserRole(user_id=u_op.user_id, user_role=UserRoleEnum.OPERADOR.value))
        db.add(Session(
            session_id="test-operador-session",
            user_id=u_op.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))
        db.add(Empleado(
            persona_id=p_op.persona_id,
            rol_empleado=RolEmpleado.OPERADOR.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        ))

        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Helper ────────────────────────────────────────────────────────────

def _new_user_payload(**overrides) -> dict:
    base = {
        "user_email": "nuevo@cmep.local",
        "password": "password123",
        "nombres": "Juan",
        "apellidos": "Perez",
        "tipo_documento": "DNI",
        "numero_documento": "12345678",
        "telefono": "999888777",
        "roles": ["OPERADOR"],
    }
    base.update(overrides)
    return base


# ── GET /admin/usuarios ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_users_as_admin(client: AsyncClient):
    """ADMIN puede listar usuarios."""
    resp = await client.get("/admin/usuarios", cookies=_cookies("test-admin-session"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert len(body["data"]) >= 2  # admin + operador


@pytest.mark.anyio
async def test_list_users_as_non_admin(client: AsyncClient):
    """Non-ADMIN recibe 403."""
    resp = await client.get("/admin/usuarios", cookies=_cookies("test-operador-session"))
    assert resp.status_code == 403


# ── POST /admin/usuarios ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_user_ok(client: AsyncClient):
    """ADMIN puede crear un usuario nuevo."""
    payload = _new_user_payload()
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["user_email"] == "nuevo@cmep.local"
    assert data["nombres"] == "Juan"
    assert data["apellidos"] == "Perez"
    assert "OPERADOR" in data["roles"]
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_create_user_duplicate_email(client: AsyncClient):
    """Email duplicado retorna 409."""
    payload = _new_user_payload(user_email="admin@cmep.local")
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_create_user_short_password(client: AsyncClient):
    """Password < 8 chars retorna 422."""
    payload = _new_user_payload(password="short")
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_user_missing_fields(client: AsyncClient):
    """Campos faltantes retornan 422."""
    resp = await client.post(
        "/admin/usuarios",
        json={"user_email": "test@test.com"},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_user_with_medico_role(client: AsyncClient):
    """Crear usuario con rol MEDICO crea MedicoExtra."""
    payload = _new_user_payload(
        user_email="medico.nuevo@cmep.local",
        numero_documento="11111111",
        roles=["MEDICO"],
    )
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "MEDICO" in data["roles"]

    # Verificar que MedicoExtra fue creado
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        me = await db.execute(
            select(MedicoExtra).where(MedicoExtra.persona_id == data["persona_id"])
        )
        assert me.scalar_one_or_none() is not None


@pytest.mark.anyio
async def test_create_user_reuses_existing_persona(client: AsyncClient):
    """Si ya existe persona con mismo documento, la reutiliza."""
    # Crear persona previa
    async with TestSessionLocal() as db:
        p = Persona(
            tipo_documento="DNI", numero_documento="55555555",
            nombres="Existente", apellidos="Persona", email="existente@test.com",
        )
        db.add(p)
        await db.commit()

    payload = _new_user_payload(
        user_email="nuevo.reuse@cmep.local",
        numero_documento="55555555",
        nombres="Actualizado",
        apellidos="Persona",
    )
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    assert resp.status_code == 201
    data = resp.json()["data"]
    # El nombre se actualiza
    assert data["nombres"] == "Actualizado"


@pytest.mark.anyio
async def test_create_user_non_admin(client: AsyncClient):
    """Non-ADMIN no puede crear usuarios."""
    payload = _new_user_payload(user_email="x@cmep.local", numero_documento="99999999")
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-operador-session"))
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_create_user_invalid_role(client: AsyncClient):
    """Rol invalido retorna 422."""
    payload = _new_user_payload(roles=["INVALID_ROLE"])
    resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    assert resp.status_code == 422


# ── PATCH /admin/usuarios/{user_id} ───────────────────────────────────

@pytest.mark.anyio
async def test_update_user_nombre(client: AsyncClient):
    """ADMIN puede actualizar nombre del usuario."""
    # Primero crear un usuario
    payload = _new_user_payload()
    create_resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    user_id = create_resp.json()["data"]["user_id"]

    # Actualizar
    resp = await client.patch(
        f"/admin/usuarios/{user_id}",
        json={"nombres": "Pedro", "apellidos": "Garcia"},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["nombres"] == "Pedro"
    assert data["apellidos"] == "Garcia"


@pytest.mark.anyio
async def test_update_user_roles(client: AsyncClient):
    """ADMIN puede cambiar roles del usuario."""
    payload = _new_user_payload()
    create_resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    user_id = create_resp.json()["data"]["user_id"]

    resp = await client.patch(
        f"/admin/usuarios/{user_id}",
        json={"roles": ["GESTOR", "MEDICO"]},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data["roles"]) == {"GESTOR", "MEDICO"}


@pytest.mark.anyio
async def test_update_user_suspend(client: AsyncClient):
    """Suspender usuario invalida sesiones."""
    # Crear usuario con sesion
    payload = _new_user_payload()
    create_resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    user_id = create_resp.json()["data"]["user_id"]

    # Crear sesion para el nuevo usuario
    async with TestSessionLocal() as db:
        db.add(Session(
            session_id="test-nuevo-session",
            user_id=user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))
        await db.commit()

    # Suspender
    resp = await client.patch(
        f"/admin/usuarios/{user_id}",
        json={"is_active": False},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_active"] is False

    # Verificar que sesiones fueron eliminadas
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        sessions = await db.execute(
            select(Session).where(Session.user_id == user_id)
        )
        assert sessions.scalars().all() == []


@pytest.mark.anyio
async def test_update_user_reactivate(client: AsyncClient):
    """Reactivar usuario suspendido."""
    payload = _new_user_payload()
    create_resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    user_id = create_resp.json()["data"]["user_id"]

    # Suspender
    await client.patch(
        f"/admin/usuarios/{user_id}",
        json={"is_active": False},
        cookies=_cookies("test-admin-session"),
    )

    # Reactivar
    resp = await client.patch(
        f"/admin/usuarios/{user_id}",
        json={"is_active": True},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True


@pytest.mark.anyio
async def test_update_user_self_suspend_blocked(client: AsyncClient):
    """ADMIN no puede suspenderse a si mismo."""
    # Obtener user_id del admin
    list_resp = await client.get("/admin/usuarios", cookies=_cookies("test-admin-session"))
    admin_user = next(u for u in list_resp.json()["data"] if u["user_email"] == "admin@cmep.local")

    resp = await client.patch(
        f"/admin/usuarios/{admin_user['user_id']}",
        json={"is_active": False},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_update_nonexistent_user(client: AsyncClient):
    """Editar usuario inexistente retorna 404."""
    resp = await client.patch(
        "/admin/usuarios/99999",
        json={"nombres": "Test"},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_user_as_non_admin(client: AsyncClient):
    """Non-ADMIN no puede editar usuarios."""
    resp = await client.patch(
        "/admin/usuarios/1",
        json={"nombres": "Test"},
        cookies=_cookies("test-operador-session"),
    )
    assert resp.status_code == 403


# ── POST /admin/usuarios/{user_id}/reset-password ─────────────────────

@pytest.mark.anyio
async def test_reset_password_ok(client: AsyncClient):
    """ADMIN puede resetear password."""
    payload = _new_user_payload()
    create_resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    user_id = create_resp.json()["data"]["user_id"]

    resp = await client.post(
        f"/admin/usuarios/{user_id}/reset-password",
        json={"new_password": "newpassword123"},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.anyio
async def test_reset_password_short(client: AsyncClient):
    """Password < 8 chars retorna 422."""
    payload = _new_user_payload()
    create_resp = await client.post("/admin/usuarios", json=payload, cookies=_cookies("test-admin-session"))
    user_id = create_resp.json()["data"]["user_id"]

    resp = await client.post(
        f"/admin/usuarios/{user_id}/reset-password",
        json={"new_password": "short"},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_reset_password_non_admin(client: AsyncClient):
    """Non-ADMIN no puede resetear password."""
    resp = await client.post(
        "/admin/usuarios/1/reset-password",
        json={"new_password": "newpassword123"},
        cookies=_cookies("test-operador-session"),
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_reset_password_nonexistent(client: AsyncClient):
    """Reset password de usuario inexistente retorna 404."""
    resp = await client.post(
        "/admin/usuarios/99999/reset-password",
        json={"new_password": "newpassword123"},
        cookies=_cookies("test-admin-session"),
    )
    assert resp.status_code == 404
