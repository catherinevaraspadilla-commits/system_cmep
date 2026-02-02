"""
Tests de integracion: GET /admin/reportes (M7).
Ref: docs/claude/M7_reportes_admin.md

Verifica: auth, permisos, estructura de respuesta, filtros.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import timedelta
from decimal import Decimal

from app.database import Base
from app.main import app
from app.models.persona import Persona
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum, Session
from app.models.cliente import Cliente
from app.models.servicio import Servicio
from app.models.solicitud import SolicitudCmep, SolicitudAsignacion, PagoSolicitud
from app.models.promotor import Promotor
from app.utils.hashing import hash_password
from app.utils.time import utcnow

from tests.integration.conftest import test_engine, TestSessionLocal


def _cookies(session_id: str) -> dict:
    return {"cmep_session": session_id}


@pytest.fixture(autouse=True)
async def setup_db():
    """Crea tablas y datos de prueba para reportes."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    now = utcnow()
    expires = now + timedelta(hours=24)

    async with TestSessionLocal() as db:
        # ── ADMIN ──
        p_admin = Persona(
            tipo_documento="DNI", numero_documento="99000001",
            nombres="Admin", apellidos="Reportes",
        )
        db.add(p_admin)
        await db.flush()

        u_admin = User(
            persona_id=p_admin.persona_id,
            user_email="admin-rep@cmep.local",
            password_hash=hash_password("admin123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(u_admin)
        await db.flush()
        db.add(UserRole(user_id=u_admin.user_id, user_role=UserRoleEnum.ADMIN.value))
        db.add(Session(
            session_id="test-admin-rep",
            user_id=u_admin.user_id, created_at=now, expires_at=expires,
        ))

        # ── OPERADOR ──
        p_op = Persona(
            tipo_documento="DNI", numero_documento="99000002",
            nombres="Operador", apellidos="Test",
        )
        db.add(p_op)
        await db.flush()

        u_op = User(
            persona_id=p_op.persona_id,
            user_email="op-rep@cmep.local",
            password_hash=hash_password("op123"),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(u_op)
        await db.flush()
        db.add(UserRole(user_id=u_op.user_id, user_role=UserRoleEnum.OPERADOR.value))
        db.add(Session(
            session_id="test-op-rep",
            user_id=u_op.user_id, created_at=now, expires_at=expires,
        ))

        # ── Promotor ──
        promotor = Promotor(
            tipo_promotor="EMPRESA",
            razon_social="Empresa Test SA",
        )
        db.add(promotor)
        await db.flush()

        # ── Cliente ──
        p_cliente = Persona(
            tipo_documento="DNI", numero_documento="99000003",
            nombres="Cliente", apellidos="Prueba",
        )
        db.add(p_cliente)
        await db.flush()

        cliente = Cliente(persona_id=p_cliente.persona_id, promotor_id=promotor.promotor_id)
        db.add(cliente)
        await db.flush()

        # ── Servicio ──
        servicio = Servicio(
            descripcion_servicio="CMEP Basico",
            tarifa_servicio=Decimal("350.00"),
            moneda_tarifa="PEN",
        )
        db.add(servicio)
        await db.flush()

        # ── Gestor persona ──
        p_gestor = Persona(
            tipo_documento="DNI", numero_documento="99000004",
            nombres="Gestor", apellidos="Test",
        )
        db.add(p_gestor)
        await db.flush()

        # ── Solicitud 1: CERRADA ──
        sol1 = SolicitudCmep(
            cliente_id=p_cliente.persona_id,
            servicio_id=servicio.servicio_id,
            promotor_id=promotor.promotor_id,
            estado_atencion="ATENDIDO",
            estado_pago="PAGADO",
            tarifa_monto=Decimal("350.00"),
            tarifa_moneda="PEN",
            created_by=u_admin.user_id,
        )
        db.add(sol1)
        await db.flush()

        # Asignar gestor vigente
        db.add(SolicitudAsignacion(
            solicitud_id=sol1.solicitud_id,
            persona_id=p_gestor.persona_id,
            rol="GESTOR",
            es_vigente=True,
            asignado_por=u_admin.user_id,
        ))

        # Pago validado
        db.add(PagoSolicitud(
            solicitud_id=sol1.solicitud_id,
            canal_pago="YAPE",
            fecha_pago=now.date(),
            monto=Decimal("350.00"),
            moneda="PEN",
            validated_by=u_admin.user_id,
            validated_at=now,
        ))

        # ── Solicitud 2: REGISTRADA ──
        sol2 = SolicitudCmep(
            cliente_id=p_cliente.persona_id,
            estado_atencion="REGISTRADO",
            estado_pago="PENDIENTE",
            created_by=u_admin.user_id,
        )
        db.add(sol2)

        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Tests ────────────────────────────────────────────────────────────


async def test_reportes_sin_auth_retorna_401():
    """Sin cookie de sesion → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/reportes")
    assert resp.status_code == 401


async def test_reportes_operador_retorna_403():
    """OPERADOR no puede acceder → 403."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes",
            cookies=_cookies("test-op-rep"),
        )
    assert resp.status_code == 403


async def test_reportes_admin_retorna_200():
    """ADMIN obtiene reporte con estructura correcta."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes",
            cookies=_cookies("test-admin-rep"),
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True

    data = body["data"]

    # KPIs structure
    assert "kpis" in data
    kpis = data["kpis"]
    assert "solicitudes" in kpis
    assert "cerradas" in kpis
    assert "ingresos" in kpis
    assert "ticket_promedio" in kpis

    # Series
    assert "series" in data
    assert isinstance(data["series"], list)

    # Distribucion
    assert "distribucion" in data
    assert isinstance(data["distribucion"], list)
    assert len(data["distribucion"]) == 6  # 6 estados

    # Rankings
    assert "ranking_promotores" in data
    assert isinstance(data["ranking_promotores"], list)
    assert "ranking_equipo" in data
    assert "gestores" in data["ranking_equipo"]
    assert "medicos" in data["ranking_equipo"]
    assert "operadores" in data["ranking_equipo"]


async def test_reportes_kpis_con_datos():
    """Verifica que KPIs reflejan los datos de prueba."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes",
            cookies=_cookies("test-admin-rep"),
        )
    assert resp.status_code == 200
    kpis = resp.json()["data"]["kpis"]

    # Tenemos 2 solicitudes, 1 cerrada, ingresos de 350
    assert kpis["cerradas"] == 1
    assert kpis["ingresos"] == 350.0
    assert kpis["ticket_promedio"] == 350.0


async def test_reportes_distribucion_estados():
    """Distribucion muestra al menos las solicitudes de prueba."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes",
            cookies=_cookies("test-admin-rep"),
        )
    assert resp.status_code == 200
    dist = resp.json()["data"]["distribucion"]

    dist_map = {d["estado"]: d["cantidad"] for d in dist}
    assert dist_map["CERRADO"] == 1
    assert dist_map["REGISTRADO"] == 1


async def test_reportes_filtro_estado():
    """Filtro por estado limita KPIs a ese estado."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes?estado=CERRADO",
            cookies=_cookies("test-admin-rep"),
        )
    assert resp.status_code == 200
    kpis = resp.json()["data"]["kpis"]
    assert kpis["solicitudes"] == 1  # Solo la cerrada


async def test_reportes_ranking_promotores():
    """Ranking promotores incluye datos del promotor de prueba."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes",
            cookies=_cookies("test-admin-rep"),
        )
    assert resp.status_code == 200
    ranking = resp.json()["data"]["ranking_promotores"]

    # Al menos un promotor (Empresa Test SA tiene 1 solicitud con promotor_id)
    assert len(ranking) >= 1
    first = ranking[0]
    assert "nombre" in first
    assert "clientes" in first
    assert "solicitudes" in first


async def test_reportes_agrupacion_semanal():
    """Agrupacion semanal no produce error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/reportes?agrupacion=semanal",
            cookies=_cookies("test-admin-rep"),
        )
    assert resp.status_code == 200
    series = resp.json()["data"]["series"]
    assert isinstance(series, list)
