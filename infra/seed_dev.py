"""
Seed de desarrollo: crea usuarios, empleados, clientes, promotores y servicios.
Ref: docs/claude/03_task_backlog.md (T011, T021)

Ejecutar desde /infra:
  python seed_dev.py            (usa SQLite local por defecto)
  python seed_dev.py --mysql    (usa MySQL via docker-compose)
"""

import sys
import os
import argparse

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import asyncio
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
import app.models  # noqa: F401 — registrar todos los modelos en metadata
from app.models.persona import Persona, TipoDocumento
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum
from app.models.cliente import Cliente
from app.models.promotor import Promotor, TipoPromotor
from app.models.empleado import Empleado, MedicoExtra, RolEmpleado, EstadoEmpleado
from app.models.servicio import Servicio
from app.utils.hashing import hash_password


# --- Base de datos SQLite local para desarrollo sin Docker ---
SQLITE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cmep_dev.db"))
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_PATH}"


# ── Datos de seed ──────────────────────────────────────────────────────

SEED_USERS = [
    {
        "nombres": "Admin",
        "apellidos": "Sistema",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "00000001",
        "email": "admin@cmep.local",
        "password": "admin123",
        "roles": [UserRoleEnum.ADMIN],
    },
    {
        "nombres": "Ana",
        "apellidos": "Operadora",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "00000002",
        "email": "operador@cmep.local",
        "password": "operador123",
        "roles": [UserRoleEnum.OPERADOR],
        "empleado_rol": RolEmpleado.OPERADOR,
    },
    {
        "nombres": "Carlos",
        "apellidos": "Gestor",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "00000003",
        "email": "gestor@cmep.local",
        "password": "gestor123",
        "roles": [UserRoleEnum.GESTOR],
        "empleado_rol": RolEmpleado.GESTOR,
    },
    {
        "nombres": "Maria",
        "apellidos": "Medico",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "00000004",
        "email": "medico@cmep.local",
        "password": "medico123",
        "roles": [UserRoleEnum.MEDICO],
        "empleado_rol": RolEmpleado.MEDICO,
        "medico_extra": {"cmp": "12345", "especialidad": "Medicina Ocupacional"},
    },
    {
        "nombres": "Suspendido",
        "apellidos": "Test",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "00000005",
        "email": "suspendido@cmep.local",
        "password": "suspendido123",
        "roles": [UserRoleEnum.OPERADOR],
        "estado": EstadoUser.SUSPENDIDO,
    },
]

SEED_CLIENTES = [
    {
        "nombres": "Juan",
        "apellidos": "Perez Lopez",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "12345678",
        "celular_1": "987654321",
    },
    {
        "nombres": "Rosa",
        "apellidos": "Garcia Torres",
        "tipo_doc": TipoDocumento.DNI,
        "numero_doc": "87654321",
        "celular_1": "912345678",
    },
    {
        "nombres": "Pedro",
        "apellidos": "Ramirez Silva",
        "tipo_doc": TipoDocumento.CE,
        "numero_doc": "CE001234",
        "celular_1": "999888777",
    },
]

SEED_PROMOTORES = [
    {
        "tipo_promotor": TipoPromotor.PERSONA,
        "fuente_promotor": "Cliente referente",
        "persona_nombres": "Luis",
        "persona_apellidos": "Promotor Reyes",
        "persona_tipo_doc": TipoDocumento.DNI,
        "persona_numero_doc": "11111111",
    },
    {
        "tipo_promotor": TipoPromotor.EMPRESA,
        "fuente_promotor": "Notaria",
        "razon_social": "Notaria Gonzales & Asociados",
        "ruc": "20123456789",
        "email": "contacto@notariagonzales.com",
    },
]

SEED_SERVICIOS = [
    {
        "descripcion_servicio": "Certificado Medico de Evaluacion Profesional - Presencial",
        "tarifa_servicio": Decimal("150.00"),
        "moneda_tarifa": "PEN",
    },
    {
        "descripcion_servicio": "Certificado Medico de Evaluacion Profesional - Virtual",
        "tarifa_servicio": Decimal("120.00"),
        "moneda_tarifa": "PEN",
    },
    {
        "descripcion_servicio": "Certificado Medico de Salud Mental",
        "tarifa_servicio": Decimal("200.00"),
        "moneda_tarifa": "PEN",
    },
]


def get_engine(use_mysql: bool):
    if use_mysql:
        from app.database import _get_engine
        return _get_engine()

    print(f"Usando SQLite local: {SQLITE_PATH}")
    return create_async_engine(SQLITE_URL, echo=False)


async def seed(use_mysql: bool):
    engine = get_engine(use_mysql)

    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        # Verificar si ya hay datos
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print(f"Seed: ya existen {count} usuarios. Borrando datos para re-seed...")
            # Borrar en orden por dependencias FK
            for table in [
                "solicitud_archivo", "archivos", "pago_solicitud",
                "solicitud_estado_historial", "solicitud_asignacion",
                "solicitud_cmep", "cliente_apoderado", "clientes",
                "medico_extra", "empleado", "promotores", "servicios",
                "sessions", "password_resets", "user_permissions",
                "user_role", "users", "personas",
            ]:
                await db.execute(text(f"DELETE FROM {table}"))
            await db.commit()
            print("  Datos anteriores eliminados.")

        # ── 1. Usuarios + Personas + Empleados ──────────────────
        print("\n=== Usuarios ===")
        persona_map = {}  # email -> persona_id
        user_map = {}     # email -> user_id

        for u in SEED_USERS:
            persona = Persona(
                tipo_documento=u["tipo_doc"].value,
                numero_documento=u["numero_doc"],
                nombres=u["nombres"],
                apellidos=u["apellidos"],
                email=u["email"],
            )
            db.add(persona)
            await db.flush()
            persona_map[u["email"]] = persona.persona_id

            user = User(
                persona_id=persona.persona_id,
                user_email=u["email"].strip().lower(),
                password_hash=hash_password(u["password"]),
                estado=u.get("estado", EstadoUser.ACTIVO).value,
            )
            db.add(user)
            await db.flush()
            user_map[u["email"]] = user.user_id

            for role in u["roles"]:
                db.add(UserRole(user_id=user.user_id, user_role=role.value))

            # Crear empleado si tiene rol operativo
            if "empleado_rol" in u:
                empleado = Empleado(
                    persona_id=persona.persona_id,
                    rol_empleado=u["empleado_rol"].value,
                    estado_empleado=EstadoEmpleado.ACTIVO.value,
                )
                db.add(empleado)
                await db.flush()

                # Crear medico_extra si es MEDICO (R11)
                if u["empleado_rol"] == RolEmpleado.MEDICO and "medico_extra" in u:
                    me = MedicoExtra(
                        persona_id=persona.persona_id,
                        cmp=u["medico_extra"]["cmp"],
                        especialidad=u["medico_extra"]["especialidad"],
                    )
                    db.add(me)

            print(f"  {u['email']} (roles: {[r.value for r in u['roles']]})")

        await db.flush()

        # ── 2. Promotores ────────────────────────────────────────
        print("\n=== Promotores ===")
        for p in SEED_PROMOTORES:
            persona_id = None
            if p["tipo_promotor"] == TipoPromotor.PERSONA:
                persona = Persona(
                    tipo_documento=p["persona_tipo_doc"].value,
                    numero_documento=p["persona_numero_doc"],
                    nombres=p["persona_nombres"],
                    apellidos=p["persona_apellidos"],
                )
                db.add(persona)
                await db.flush()
                persona_id = persona.persona_id

            promotor = Promotor(
                tipo_promotor=p["tipo_promotor"].value,
                fuente_promotor=p.get("fuente_promotor"),
                persona_id=persona_id,
                razon_social=p.get("razon_social"),
                ruc=p.get("ruc"),
                email=p.get("email"),
            )
            db.add(promotor)
            await db.flush()
            display = p.get("razon_social") or f"{p.get('persona_nombres', '')} {p.get('persona_apellidos', '')}"
            print(f"  {p['tipo_promotor'].value}: {display.strip()}")

        # ── 3. Clientes ──────────────────────────────────────────
        print("\n=== Clientes ===")
        for c in SEED_CLIENTES:
            persona = Persona(
                tipo_documento=c["tipo_doc"].value,
                numero_documento=c["numero_doc"],
                nombres=c["nombres"],
                apellidos=c["apellidos"],
                celular_1=c.get("celular_1"),
            )
            db.add(persona)
            await db.flush()

            cliente = Cliente(
                persona_id=persona.persona_id,
                estado="ACTIVO",
            )
            db.add(cliente)
            print(f"  {c['tipo_doc'].value} {c['numero_doc']}: {c['nombres']} {c['apellidos']}")

        # ── 4. Servicios ──────────────────────────────────────────
        print("\n=== Servicios ===")
        for s in SEED_SERVICIOS:
            servicio = Servicio(
                descripcion_servicio=s["descripcion_servicio"],
                tarifa_servicio=s["tarifa_servicio"],
                moneda_tarifa=s["moneda_tarifa"],
            )
            db.add(servicio)
            print(f"  {s['descripcion_servicio']} ({s['moneda_tarifa']} {s['tarifa_servicio']})")

        await db.commit()
        print("\nSeed completado exitosamente.")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de desarrollo CMEP")
    parser.add_argument("--mysql", action="store_true", help="Usar MySQL (requiere docker-compose up)")
    args = parser.parse_args()
    asyncio.run(seed(use_mysql=args.mysql))
