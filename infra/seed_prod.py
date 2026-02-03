"""
Seed de produccion: inserta SOLO los datos minimos para que CMEP funcione.
  - 1 servicio
  - 1 usuario admin

NO borra datos existentes. Si ya hay datos, aborta sin cambios.

Ejecutar:
  DB_URL="mysql+asyncmy://cmep_user:PASS@RDS_ENDPOINT:3306/cmep_prod" python infra/seed_prod.py
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import asyncio
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base
import app.models  # noqa: F401
from app.models.persona import Persona, TipoDocumento
from app.models.user import User, UserRole, EstadoUser, UserRoleEnum
from app.models.servicio import Servicio
from app.utils.hashing import hash_password


# ── Datos de produccion ─────────────────────────────────────────────────

ADMIN_USER = {
    "nombres": "Hector",
    "apellidos": "Varas",
    "tipo_doc": TipoDocumento.DNI,
    "numero_doc": "00000001",
    "email": "hvarasg@hotmail.com",
    "roles": [UserRoleEnum.ADMIN],
}

SERVICIO = {
    "descripcion_servicio": "Certificado Medico de Evaluacion Psicologica",
    "tarifa_servicio": Decimal("200.00"),
    "moneda_tarifa": "PEN",
}


async def seed(db_url: str, admin_password: str):
    engine = create_async_engine(db_url, echo=False)

    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablas creadas/verificadas.")

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        # ── Verificar que NO hay datos ──────────────────────────────
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print(f"ABORTADO: ya existen {count} usuarios en la BD.")
            print("Este script solo se ejecuta en una BD vacia.")
            print("Si necesitas re-seedear, usa seed_dev.py (solo para desarrollo).")
            await engine.dispose()
            return

        # ── 1. Servicio ─────────────────────────────────────────────
        servicio = Servicio(
            descripcion_servicio=SERVICIO["descripcion_servicio"],
            tarifa_servicio=SERVICIO["tarifa_servicio"],
            moneda_tarifa=SERVICIO["moneda_tarifa"],
        )
        db.add(servicio)
        await db.flush()
        print(f"Servicio: {SERVICIO['descripcion_servicio']} ({SERVICIO['moneda_tarifa']} {SERVICIO['tarifa_servicio']})")

        # ── 2. Admin ────────────────────────────────────────────────
        persona = Persona(
            tipo_documento=ADMIN_USER["tipo_doc"].value,
            numero_documento=ADMIN_USER["numero_doc"],
            nombres=ADMIN_USER["nombres"],
            apellidos=ADMIN_USER["apellidos"],
            email=ADMIN_USER["email"],
        )
        db.add(persona)
        await db.flush()

        user = User(
            persona_id=persona.persona_id,
            user_email=ADMIN_USER["email"].strip().lower(),
            password_hash=hash_password(admin_password),
            estado=EstadoUser.ACTIVO.value,
        )
        db.add(user)
        await db.flush()

        for role in ADMIN_USER["roles"]:
            db.add(UserRole(user_id=user.user_id, user_role=role.value))

        print(f"Admin: {ADMIN_USER['email']} (roles: {[r.value for r in ADMIN_USER['roles']]})")

        await db.commit()
        print("\nSeed de produccion completado.")
        print("Proximo paso: login con el admin y crear usuarios reales via /app/usuarios")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de produccion CMEP")
    parser.add_argument("--password", required=True, help="Password para el usuario admin")
    args = parser.parse_args()

    db_url = os.environ.get("DB_URL")
    if not db_url:
        print("ERROR: variable DB_URL no definida.")
        print('Uso: DB_URL="mysql+asyncmy://user:pass@host:3306/db" python infra/seed_prod.py --password <pass>')
        sys.exit(1)

    if "sqlite" in db_url:
        print("ERROR: seed_prod.py es solo para MySQL (produccion).")
        print("Para desarrollo local usa: python infra/seed_dev.py")
        sys.exit(1)

    print(f"BD: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print(f"Admin: {ADMIN_USER['email']}")
    confirm = input("Continuar? (si/no): ").strip().lower()
    if confirm != "si":
        print("Cancelado.")
        sys.exit(0)

    asyncio.run(seed(db_url, args.password))
