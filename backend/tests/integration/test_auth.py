"""
Tests de integracion: Auth endpoints (M1).
Ref: docs/claude/02_module_specs.md (M1 — criterios de aceptacion)
Ref: docs/claude/04_testing_strategy.md — M1 integracion

Usa engine compartido de conftest.py.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.database import Base
from app.main import app
from app.models.persona import Persona
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum
from app.utils.hashing import hash_password

from tests.integration.conftest import test_engine, TestSessionLocal


@pytest.fixture(autouse=True)
async def setup_db():
    """Crea tablas antes de cada test, las destruye despues."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed: crear usuario de prueba
    async with TestSessionLocal() as db:
        persona = Persona(
            nombres="Admin", apellidos="Test", email="admin@cmep.local"
        )
        db.add(persona)
        await db.flush()

        user = User(
            persona_id=persona.persona_id,
            user_email="admin@cmep.local",
            password_hash=hash_password("admin123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user)
        await db.flush()
        db.add(UserRole(user_id=user.user_id, user_role=UserRoleEnum.ADMIN.value))

        # Usuario suspendido
        persona2 = Persona(
            nombres="Suspendido", apellidos="Test", email="suspended@cmep.local"
        )
        db.add(persona2)
        await db.flush()
        user2 = User(
            persona_id=persona2.persona_id,
            user_email="suspended@cmep.local",
            password_hash=hash_password("pass123"),
            estado=EstadoUser.SUSPENDIDO.value,
        )
        db.add(user2)
        await db.flush()
        db.add(UserRole(user_id=user2.user_id, user_role=UserRoleEnum.OPERADOR.value))

        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Tests ---

@pytest.mark.anyio
async def test_login_success(client: AsyncClient):
    """Login exitoso retorna user data y setea cookie."""
    resp = await client.post("/auth/login", json={
        "email": "admin@cmep.local",
        "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["user"]["user_email"] == "admin@cmep.local"
    assert "ADMIN" in data["data"]["user"]["roles"]
    assert "cmep_session" in resp.cookies


@pytest.mark.anyio
async def test_login_invalid_password(client: AsyncClient):
    """Password incorrecto retorna 401."""
    resp = await client.post("/auth/login", json={
        "email": "admin@cmep.local",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_user_not_found(client: AsyncClient):
    """Email inexistente retorna 401."""
    resp = await client.post("/auth/login", json={
        "email": "noexiste@cmep.local",
        "password": "anything",
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_user_suspended(client: AsyncClient):
    """Usuario SUSPENDIDO retorna 403."""
    resp = await client.post("/auth/login", json={
        "email": "suspended@cmep.local",
        "password": "pass123",
    })
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_login_email_case_insensitive(client: AsyncClient):
    """Login funciona con email en mayusculas/espacios."""
    resp = await client.post("/auth/login", json={
        "email": "  ADMIN@CMEP.LOCAL  ",
        "password": "admin123",
    })
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_me_with_valid_session(client: AsyncClient):
    """/auth/me retorna datos con sesion valida."""
    # Login primero
    login_resp = await client.post("/auth/login", json={
        "email": "admin@cmep.local",
        "password": "admin123",
    })
    cookies = login_resp.cookies

    # Me
    resp = await client.get("/auth/me", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["user"]["user_email"] == "admin@cmep.local"


@pytest.mark.anyio
async def test_me_without_session(client: AsyncClient):
    """/auth/me sin cookie retorna 401."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_logout_invalidates_session(client: AsyncClient):
    """Logout elimina sesion; /me posterior falla."""
    # Login
    login_resp = await client.post("/auth/login", json={
        "email": "admin@cmep.local",
        "password": "admin123",
    })
    cookies = login_resp.cookies

    # Logout
    logout_resp = await client.post("/auth/logout", cookies=cookies)
    assert logout_resp.status_code == 200

    # Me deberia fallar
    me_resp = await client.get("/auth/me", cookies=cookies)
    assert me_resp.status_code == 401
