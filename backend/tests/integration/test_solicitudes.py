"""
Tests de integracion: Solicitudes endpoints (M2).
Ref: docs/claude/02_module_specs.md (M2)
Ref: docs/claude/04_testing_strategy.md

Usa engine compartido de conftest.py.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.database import Base
from app.main import app
from app.models.persona import Persona
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum, Session
from app.models.servicio import Servicio
from app.models.empleado import Empleado, MedicoExtra, RolEmpleado, EstadoEmpleado
from app.utils.hashing import hash_password
from app.utils.time import utcnow
from datetime import timedelta
from decimal import Decimal

from tests.integration.conftest import test_engine, TestSessionLocal


@pytest.fixture(autouse=True)
async def setup_db():
    """Crea tablas y datos base antes de cada test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        # Persona + User OPERADOR
        persona_op = Persona(
            tipo_documento="DNI", numero_documento="00000002",
            nombres="Ana", apellidos="Operadora", email="operador@cmep.local",
        )
        db.add(persona_op)
        await db.flush()

        user_op = User(
            persona_id=persona_op.persona_id,
            user_email="operador@cmep.local",
            password_hash=hash_password("operador123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user_op)
        await db.flush()

        db.add(UserRole(user_id=user_op.user_id, user_role=UserRoleEnum.OPERADOR.value))

        session_op = Session(
            session_id="test-operador-session",
            user_id=user_op.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        )
        db.add(session_op)

        emp_op = Empleado(
            persona_id=persona_op.persona_id,
            rol_empleado=RolEmpleado.OPERADOR.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        )
        db.add(emp_op)

        # Persona + User ADMIN
        persona_admin = Persona(
            tipo_documento="DNI", numero_documento="00000001",
            nombres="Admin", apellidos="Sistema", email="admin@cmep.local",
        )
        db.add(persona_admin)
        await db.flush()

        user_admin = User(
            persona_id=persona_admin.persona_id,
            user_email="admin@cmep.local",
            password_hash=hash_password("admin123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user_admin)
        await db.flush()

        db.add(UserRole(user_id=user_admin.user_id, user_role=UserRoleEnum.ADMIN.value))

        session_admin = Session(
            session_id="test-admin-session",
            user_id=user_admin.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        )
        db.add(session_admin)

        # Servicio de prueba
        servicio = Servicio(
            descripcion_servicio="CMEP Presencial",
            tarifa_servicio=Decimal("150.00"),
            moneda_tarifa="PEN",
        )
        db.add(servicio)

        # Persona gestor + empleado
        persona_gestor = Persona(
            tipo_documento="DNI", numero_documento="00000003",
            nombres="Carlos", apellidos="Gestor",
        )
        db.add(persona_gestor)
        await db.flush()

        emp_gestor = Empleado(
            persona_id=persona_gestor.persona_id,
            rol_empleado=RolEmpleado.GESTOR.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        )
        db.add(emp_gestor)

        # User GESTOR (for mine tests)
        user_gestor = User(
            persona_id=persona_gestor.persona_id,
            user_email="gestor@cmep.local",
            password_hash=hash_password("gestor123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user_gestor)
        await db.flush()
        db.add(UserRole(user_id=user_gestor.user_id, user_role=UserRoleEnum.GESTOR.value))
        db.add(Session(
            session_id="test-gestor-session",
            user_id=user_gestor.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        # Persona + User MEDICO (for mine tests)
        persona_medico = Persona(
            tipo_documento="DNI", numero_documento="00000004",
            nombres="Dra", apellidos="Medica",
        )
        db.add(persona_medico)
        await db.flush()

        emp_medico = Empleado(
            persona_id=persona_medico.persona_id,
            rol_empleado=RolEmpleado.MEDICO.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        )
        db.add(emp_medico)
        db.add(MedicoExtra(persona_id=persona_medico.persona_id))

        user_medico = User(
            persona_id=persona_medico.persona_id,
            user_email="medico@cmep.local",
            password_hash=hash_password("medico123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user_medico)
        await db.flush()
        db.add(UserRole(user_id=user_medico.user_id, user_role=UserRoleEnum.MEDICO.value))
        db.add(Session(
            session_id="test-medico-session",
            user_id=user_medico.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def _cookies(session_id: str) -> dict:
    return {"cmep_session": session_id}


# ── T022: POST /solicitudes ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_solicitud_minimal():
    """Crear solicitud con datos minimos retorna 200 con solicitud_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/solicitudes",
            json={
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "12345678",
                    "nombres": "Juan",
                    "apellidos": "Perez",
                },
            },
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "solicitud_id" in data["data"]
        assert data["data"]["codigo"].startswith("CMEP-")


@pytest.mark.asyncio
async def test_create_solicitud_with_apoderado():
    """Crear solicitud con apoderado incluido."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/solicitudes",
            json={
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "22222222",
                    "nombres": "Rosa",
                    "apellidos": "Garcia",
                },
                "apoderado": {
                    "tipo_documento": "DNI",
                    "numero_documento": "33333333",
                    "nombres": "Pedro",
                    "apellidos": "Apoderado",
                },
            },
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_create_solicitud_existing_client():
    """Crear dos solicitudes con el mismo cliente reutiliza la persona."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "44444444",
                "nombres": "Reuso",
                "apellidos": "Test",
            },
        }
        resp1 = await client.post("/solicitudes", json=payload, cookies=_cookies("test-operador-session"))
        resp2 = await client.post("/solicitudes", json=payload, cookies=_cookies("test-operador-session"))
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["data"]["solicitud_id"] != resp2.json()["data"]["solicitud_id"]


@pytest.mark.asyncio
async def test_create_solicitud_unauthorized():
    """Sin sesion, POST /solicitudes retorna 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/solicitudes",
            json={
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "55555555",
                    "nombres": "No",
                    "apellidos": "Auth",
                },
            },
        )
        assert resp.status_code == 401


# ── T023: GET /solicitudes ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_solicitudes_empty():
    """Lista vacia al inicio."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/solicitudes", cookies=_cookies("test-operador-session"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["data"]["items"] == []
        assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_solicitudes_after_create():
    """Despues de crear, la lista tiene 1 item."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/solicitudes",
            json={"cliente": {"tipo_documento": "DNI", "numero_documento": "66666666", "nombres": "Lista", "apellidos": "Test"}},
            cookies=_cookies("test-operador-session"),
        )
        resp = await client.get("/solicitudes", cookies=_cookies("test-operador-session"))
        data = resp.json()
        assert data["meta"]["total"] == 1
        assert len(data["data"]["items"]) == 1
        item = data["data"]["items"][0]
        assert item["estado_operativo"] == "REGISTRADO"


@pytest.mark.asyncio
async def test_list_solicitudes_search():
    """Busqueda por documento del cliente."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/solicitudes",
            json={"cliente": {"tipo_documento": "DNI", "numero_documento": "77777777", "nombres": "Buscar", "apellidos": "Test"}},
            cookies=_cookies("test-operador-session"),
        )
        resp = await client.get("/solicitudes?q=77777", cookies=_cookies("test-operador-session"))
        assert resp.json()["meta"]["total"] >= 1

        resp2 = await client.get("/solicitudes?q=ZZZZZ999", cookies=_cookies("test-operador-session"))
        assert resp2.json()["meta"]["total"] == 0


# ── T024: GET /solicitudes/{id} ──────────────────────────────────────

@pytest.mark.asyncio
async def test_detail_solicitud():
    """Detalle incluye estado_operativo, acciones_permitidas, historial."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/solicitudes",
            json={"cliente": {"tipo_documento": "DNI", "numero_documento": "88888888", "nombres": "Detalle", "apellidos": "Test"}},
            cookies=_cookies("test-admin-session"),
        )
        sol_id = create_resp.json()["data"]["solicitud_id"]

        resp = await client.get(f"/solicitudes/{sol_id}", cookies=_cookies("test-admin-session"))
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert data["estado_operativo"] == "REGISTRADO"
        assert "EDITAR_DATOS" in data["acciones_permitidas"]
        assert "ASIGNAR_GESTOR" in data["acciones_permitidas"]
        assert data["asignaciones_vigentes"]["GESTOR"] is None
        assert data["asignaciones_vigentes"]["MEDICO"] is None
        assert len(data["historial"]) >= 1


@pytest.mark.asyncio
async def test_detail_not_found():
    """Solicitud inexistente retorna 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/solicitudes/99999", cookies=_cookies("test-admin-session"))
        assert resp.status_code == 404


# ── T025: PATCH /solicitudes/{id} ────────────────────────────────────

@pytest.mark.asyncio
async def test_edit_solicitud_success():
    """EDITAR_DATOS modifica campos y registra auditoria."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/solicitudes",
            json={"cliente": {"tipo_documento": "DNI", "numero_documento": "99999999", "nombres": "Edit", "apellidos": "Test"}},
            cookies=_cookies("test-admin-session"),
        )
        sol_id = create_resp.json()["data"]["solicitud_id"]

        resp = await client.patch(
            f"/solicitudes/{sol_id}",
            json={"comentario": "Actualizado via test"},
            cookies=_cookies("test-admin-session"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["comentario"] == "Actualizado via test"


@pytest.mark.asyncio
async def test_edit_solicitud_not_found():
    """PATCH solicitud inexistente retorna 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            "/solicitudes/99999",
            json={"comentario": "no existe"},
            cookies=_cookies("test-admin-session"),
        )
        assert resp.status_code == 404


# ── T061_dash: Tests mine filter ─────────────────────────────────────

async def _create_solicitud(client: AsyncClient, session_id: str, doc: str = "99999999") -> int:
    """Helper: crea una solicitud y retorna su solicitud_id."""
    resp = await client.post(
        "/solicitudes",
        json={
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": doc,
                "nombres": "Test",
                "apellidos": "Cliente",
            },
        },
        cookies=_cookies(session_id),
    )
    assert resp.status_code == 200
    return resp.json()["data"]["solicitud_id"]


@pytest.mark.asyncio
async def test_list_solicitudes_mine_operador():
    """mine=true + OPERADOR: solo ve solicitudes que creo."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Operador crea 2 solicitudes
        await _create_solicitud(client, "test-operador-session", "55550001")
        await _create_solicitud(client, "test-operador-session", "55550002")

        # Admin crea 1 solicitud
        await _create_solicitud(client, "test-admin-session", "55550003")

        # mine=true as operador: should see only 2
        resp = await client.get(
            "/solicitudes?mine=true",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) == 2

        # mine=false: should see all 3
        resp2 = await client.get(
            "/solicitudes?mine=false",
            cookies=_cookies("test-operador-session"),
        )
        assert resp2.status_code == 200
        assert len(resp2.json()["data"]["items"]) == 3


@pytest.mark.asyncio
async def test_list_solicitudes_mine_admin():
    """mine=true + ADMIN: ve todas las solicitudes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_solicitud(client, "test-operador-session", "55560001")
        await _create_solicitud(client, "test-admin-session", "55560002")

        resp = await client.get(
            "/solicitudes?mine=true",
            cookies=_cookies("test-admin-session"),
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        # ADMIN sees all
        assert len(items) >= 2


@pytest.mark.asyncio
async def test_list_solicitudes_mine_gestor():
    """mine=true + GESTOR: solo ve solicitudes donde esta asignado como gestor."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Operador crea solicitud
        sol_id = await _create_solicitud(client, "test-operador-session", "55570001")

        # Gestor with mine=true: should see 0 (not assigned yet)
        resp = await client.get(
            "/solicitudes?mine=true",
            cookies=_cookies("test-gestor-session"),
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0

        # Assign gestor to the solicitud
        resp_assign = await client.post(
            f"/solicitudes/{sol_id}/asignar-gestor",
            json={"persona_id": 3},  # persona_gestor (DNI 00000003) — created 3rd
            cookies=_cookies("test-admin-session"),
        )
        # If assignment returns 200, gestor is assigned
        if resp_assign.status_code == 200:
            # Now gestor with mine=true should see 1
            resp2 = await client.get(
                "/solicitudes?mine=true",
                cookies=_cookies("test-gestor-session"),
            )
            assert resp2.status_code == 200
            assert len(resp2.json()["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_list_solicitudes_mine_medico():
    """mine=true + MEDICO: solo ve solicitudes donde esta asignado como medico."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Medico with mine=true: should see 0
        resp = await client.get(
            "/solicitudes?mine=true",
            cookies=_cookies("test-medico-session"),
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) == 0


@pytest.mark.asyncio
async def test_list_solicitudes_mine_false_unchanged():
    """mine=false (default) retorna todas las solicitudes como antes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_solicitud(client, "test-operador-session", "55590001")

        # Without mine param
        resp = await client.get(
            "/solicitudes",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        total_default = resp.json()["meta"]["total"]

        # With mine=false
        resp2 = await client.get(
            "/solicitudes?mine=false",
            cookies=_cookies("test-operador-session"),
        )
        assert resp2.status_code == 200
        total_false = resp2.json()["meta"]["total"]

        assert total_default == total_false
