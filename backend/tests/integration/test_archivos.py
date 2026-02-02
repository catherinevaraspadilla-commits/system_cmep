"""
Tests de integracion: Archivos endpoints (M4).
Ref: docs/source/05_api_y_policy.md (Modulo Archivos MVP)

Usa engine compartido de conftest.py.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.database import Base
from app.main import app
from app.models.persona import Persona
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum, Session
from app.models.empleado import Empleado, RolEmpleado, EstadoEmpleado
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

        # Persona GESTOR + empleado
        persona_gestor = Persona(
            tipo_documento="DNI", numero_documento="00000003",
            nombres="Carlos", apellidos="Gestor",
        )
        db.add(persona_gestor)
        await db.flush()

        db.add(Empleado(
            persona_id=persona_gestor.persona_id,
            rol_empleado=RolEmpleado.GESTOR.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        ))

        # Gestor user + session (needed for registrar-pago)
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

        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def _cookies(session_id: str) -> dict:
    return {"cmep_session": session_id}


async def _create_solicitud(client: AsyncClient) -> int:
    """Helper: crea una solicitud y retorna solicitud_id."""
    resp = await client.post(
        "/solicitudes",
        json={
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "99887766",
                "nombres": "Test",
                "apellidos": "Archivos",
            },
        },
        cookies=_cookies("test-operador-session"),
    )
    assert resp.status_code == 200
    return resp.json()["data"]["solicitud_id"]


# ── T041: Upload archivo ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_archivo_success():
    """Subir un archivo a una solicitud retorna 200 con archivo_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sol_id = await _create_solicitud(client)

        resp = await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("test.pdf", b"PDF-CONTENT-HERE", "application/pdf")},
            data={"tipo_archivo": "DOCUMENTO"},
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "archivo_id" in data["data"]
        assert data["data"]["nombre"] == "test.pdf"
        assert data["data"]["tipo"] == "DOCUMENTO"
        assert data["data"]["tamano_bytes"] == len(b"PDF-CONTENT-HERE")


@pytest.mark.asyncio
async def test_upload_archivo_evidencia_pago():
    """Subir evidencia de pago asociada a un pago_id."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sol_id = await _create_solicitud(client)

        # Asignar gestor (persona_id=3 = Carlos Gestor)
        resp = await client.post(
            f"/solicitudes/{sol_id}/asignar-gestor",
            json={"persona_id_gestor": 3},
            cookies=_cookies("test-admin-session"),
        )
        assert resp.status_code == 200

        # Registrar pago (como gestor)
        resp = await client.post(
            f"/solicitudes/{sol_id}/registrar-pago",
            json={
                "canal_pago": "EFECTIVO",
                "fecha_pago": "2026-01-30",
                "monto": 100.00,
                "moneda": "PEN",
            },
            cookies=_cookies("test-gestor-session"),
        )
        assert resp.status_code == 200

        pago_id = resp.json()["data"]["pagos"][0]["pago_id"]

        # Upload con pago_id
        resp = await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("recibo.jpg", b"JPEG-DATA", "image/jpeg")},
            data={"tipo_archivo": "EVIDENCIA_PAGO", "pago_id": str(pago_id)},
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["tipo"] == "EVIDENCIA_PAGO"


@pytest.mark.asyncio
async def test_upload_archivo_invalid_tipo():
    """Tipo de archivo invalido retorna 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sol_id = await _create_solicitud(client)

        resp = await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("test.pdf", b"DATA", "application/pdf")},
            data={"tipo_archivo": "INVALIDO"},
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_archivo_solicitud_not_found():
    """Solicitud inexistente retorna 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/solicitudes/99999/archivos",
            files={"file": ("test.pdf", b"DATA", "application/pdf")},
            data={"tipo_archivo": "DOCUMENTO"},
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_archivo_unauthorized():
    """Sin sesion retorna 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/solicitudes/1/archivos",
            files={"file": ("test.pdf", b"DATA", "application/pdf")},
            data={"tipo_archivo": "DOCUMENTO"},
        )
        assert resp.status_code == 401


# ── T042: Download archivo ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_download_archivo_success():
    """Descargar un archivo existente retorna el contenido."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sol_id = await _create_solicitud(client)

        # Upload
        upload_resp = await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("doc.txt", b"HELLO-WORLD", "text/plain")},
            data={"tipo_archivo": "OTROS"},
            cookies=_cookies("test-operador-session"),
        )
        archivo_id = upload_resp.json()["data"]["archivo_id"]

        # Download
        resp = await client.get(
            f"/archivos/{archivo_id}",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        assert resp.content == b"HELLO-WORLD"
        assert "doc.txt" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_download_archivo_not_found():
    """Archivo inexistente retorna 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/archivos/99999",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 404


# ── DELETE archivo ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_archivo_success():
    """Eliminar un archivo existente retorna ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sol_id = await _create_solicitud(client)

        # Upload
        upload_resp = await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("todelete.txt", b"DELETE-ME", "text/plain")},
            data={"tipo_archivo": "OTROS"},
            cookies=_cookies("test-operador-session"),
        )
        archivo_id = upload_resp.json()["data"]["archivo_id"]

        # Delete
        resp = await client.delete(
            f"/archivos/{archivo_id}",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Verify gone
        resp2 = await client.get(
            f"/archivos/{archivo_id}",
            cookies=_cookies("test-operador-session"),
        )
        assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_archivo_not_found():
    """Eliminar archivo inexistente retorna 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(
            "/archivos/99999",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 404


# ── Archivos in detail DTO ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_archivos_appear_in_detail():
    """Archivos subidos aparecen en la seccion archivos del detalle."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sol_id = await _create_solicitud(client)

        # Upload 2 archivos
        await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("file1.pdf", b"PDF1", "application/pdf")},
            data={"tipo_archivo": "DOCUMENTO"},
            cookies=_cookies("test-operador-session"),
        )
        await client.post(
            f"/solicitudes/{sol_id}/archivos",
            files={"file": ("file2.jpg", b"JPG2", "image/jpeg")},
            data={"tipo_archivo": "OTROS"},
            cookies=_cookies("test-operador-session"),
        )

        # Get detail
        resp = await client.get(
            f"/solicitudes/{sol_id}",
            cookies=_cookies("test-operador-session"),
        )
        assert resp.status_code == 200
        archivos = resp.json()["data"]["archivos"]
        assert len(archivos) == 2
        nombres = {a["nombre"] for a in archivos}
        assert "file1.pdf" in nombres
        assert "file2.jpg" in nombres
        # Verify new fields present
        assert archivos[0]["mime_type"] is not None
        assert archivos[0]["tamano_bytes"] is not None
