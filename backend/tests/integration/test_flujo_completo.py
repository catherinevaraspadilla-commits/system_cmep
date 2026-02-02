"""
Test de integracion: flujo completo de una solicitud CMEP.
Ref: docs/claude/M4_5_incremental_improvements.md (PASO 2.8)

Recorre: login → crear → asignar gestor → registrar pago
         → asignar medico → cerrar.
Verifica transiciones de estado_operativo en cada paso.
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


@pytest.fixture(autouse=True)
async def setup_db():
    """Crea tablas y datos base antes de cada test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        # ADMIN user (persona_id=1)
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
        db.add(Session(
            session_id="sess-admin",
            user_id=user_admin.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        # OPERADOR user (persona_id=2)
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
        db.add(Empleado(
            persona_id=persona_op.persona_id,
            rol_empleado=RolEmpleado.OPERADOR.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        ))
        db.add(Session(
            session_id="sess-operador",
            user_id=user_op.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        # GESTOR user (persona_id=3)
        persona_gestor = Persona(
            tipo_documento="DNI", numero_documento="00000003",
            nombres="Carlos", apellidos="Gestor",
        )
        db.add(persona_gestor)
        await db.flush()
        user_gestor = User(
            persona_id=persona_gestor.persona_id,
            user_email="gestor@cmep.local",
            password_hash=hash_password("gestor123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user_gestor)
        await db.flush()
        db.add(UserRole(user_id=user_gestor.user_id, user_role=UserRoleEnum.GESTOR.value))
        db.add(Empleado(
            persona_id=persona_gestor.persona_id,
            rol_empleado=RolEmpleado.GESTOR.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        ))
        db.add(Session(
            session_id="sess-gestor",
            user_id=user_gestor.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        # MEDICO user (persona_id=4)
        persona_medico = Persona(
            tipo_documento="DNI", numero_documento="00000004",
            nombres="Maria", apellidos="Medico",
        )
        db.add(persona_medico)
        await db.flush()
        user_medico = User(
            persona_id=persona_medico.persona_id,
            user_email="medico@cmep.local",
            password_hash=hash_password("medico123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user_medico)
        await db.flush()
        db.add(UserRole(user_id=user_medico.user_id, user_role=UserRoleEnum.MEDICO.value))
        db.add(Empleado(
            persona_id=persona_medico.persona_id,
            rol_empleado=RolEmpleado.MEDICO.value,
            estado_empleado=EstadoEmpleado.ACTIVO.value,
        ))
        db.add(MedicoExtra(
            persona_id=persona_medico.persona_id,
            cmp="12345", especialidad="Medicina Ocupacional",
        ))
        db.add(Session(
            session_id="sess-medico",
            user_id=user_medico.user_id,
            expires_at=utcnow() + timedelta(hours=24),
        ))

        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def _cookies(session_id: str) -> dict:
    return {"cmep_session": session_id}


@pytest.mark.asyncio
async def test_flujo_completo_solicitud():
    """
    Flujo completo:
    REGISTRADO → ASIGNADO_GESTOR → PAGADO → ASIGNADO_MEDICO → CERRADO
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ── PASO 1: Login como operador ──
        resp = await client.post("/auth/login", json={
            "email": "operador@cmep.local",
            "password": "operador123",
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # ── PASO 2: Crear solicitud (como operador) ──
        resp = await client.post("/solicitudes", json={
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "99001122",
                "nombres": "Flujo",
                "apellidos": "Completo Test",
            },
        }, cookies=_cookies("sess-operador"))
        assert resp.status_code == 200
        sol_id = resp.json()["data"]["solicitud_id"]
        codigo = resp.json()["data"]["codigo"]
        assert codigo is not None

        # Verificar estado_operativo = REGISTRADO
        resp = await client.get(
            f"/solicitudes/{sol_id}",
            cookies=_cookies("sess-operador"),
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail["estado_operativo"] == "REGISTRADO"
        assert "ASIGNAR_GESTOR" in detail["acciones_permitidas"]

        # ── PASO 3: Asignar gestor (como admin) ──
        resp = await client.post(
            f"/solicitudes/{sol_id}/asignar-gestor",
            json={"persona_id_gestor": 3},  # Carlos Gestor
            cookies=_cookies("sess-admin"),
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail["estado_operativo"] == "ASIGNADO_GESTOR"
        assert detail["asignaciones_vigentes"]["GESTOR"] is not None
        assert detail["asignaciones_vigentes"]["GESTOR"]["nombre"] == "Carlos Gestor"

        # ── PASO 4: Registrar pago (como gestor) ──
        resp = await client.post(
            f"/solicitudes/{sol_id}/registrar-pago",
            json={
                "canal_pago": "YAPE",
                "fecha_pago": "2026-01-30",
                "monto": 150.00,
                "moneda": "PEN",
                "referencia_transaccion": "YP-123456",
            },
            cookies=_cookies("sess-gestor"),
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail["estado_operativo"] == "PAGADO"
        assert detail["estado_pago"] == "PAGADO"
        assert len(detail["pagos"]) == 1
        assert detail["pagos"][0]["canal_pago"] == "YAPE"

        # ── PASO 5: Asignar medico (como admin) ──
        resp = await client.post(
            f"/solicitudes/{sol_id}/asignar-medico",
            json={"persona_id_medico": 4},  # Maria Medico
            cookies=_cookies("sess-admin"),
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail["estado_operativo"] == "ASIGNADO_MEDICO"
        assert detail["asignaciones_vigentes"]["MEDICO"] is not None
        assert detail["asignaciones_vigentes"]["MEDICO"]["nombre"] == "Maria Medico"

        # ── PASO 6: Cerrar solicitud (como medico) ──
        resp = await client.post(
            f"/solicitudes/{sol_id}/cerrar",
            json={"comentario": "Evaluacion completada sin observaciones."},
            cookies=_cookies("sess-medico"),
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail["estado_operativo"] == "CERRADO"
        assert detail["estado_atencion"] == "ATENDIDO"

        # ── Verificar historial completo ──
        assert len(detail["historial"]) >= 5  # creacion + asig gestor + pago + asig medico + cierre

        # ── Verificar que no se pueden hacer mas acciones ──
        # Solo OVERRIDE deberia estar permitido (para ADMIN)
        resp = await client.get(
            f"/solicitudes/{sol_id}",
            cookies=_cookies("sess-operador"),
        )
        assert resp.status_code == 200
        operador_actions = resp.json()["data"]["acciones_permitidas"]
        assert "ASIGNAR_GESTOR" not in operador_actions
        assert "REGISTRAR_PAGO" not in operador_actions
        assert "CERRAR" not in operador_actions


@pytest.mark.asyncio
async def test_flujo_cancelar_solicitud():
    """
    Flujo de cancelacion:
    REGISTRADO → CANCELADO
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # Crear solicitud
        resp = await client.post("/solicitudes", json={
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "88776655",
                "nombres": "Cancelar",
                "apellidos": "Test",
            },
        }, cookies=_cookies("sess-operador"))
        assert resp.status_code == 200
        sol_id = resp.json()["data"]["solicitud_id"]

        # Verificar REGISTRADO
        resp = await client.get(
            f"/solicitudes/{sol_id}",
            cookies=_cookies("sess-operador"),
        )
        assert resp.json()["data"]["estado_operativo"] == "REGISTRADO"

        # Cancelar (como admin)
        resp = await client.post(
            f"/solicitudes/{sol_id}/cancelar",
            json={"comentario": "Cliente desistio."},
            cookies=_cookies("sess-admin"),
        )
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert detail["estado_operativo"] == "CANCELADO"
        assert detail["estado_atencion"] == "CANCELADO"
