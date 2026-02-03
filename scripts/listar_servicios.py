

# Ajustar sys.path para importar modulos del backend

import sys
import os
# Agregar 'backend' al sys.path para que 'app' sea importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

import asyncio
from sqlalchemy import select
from app.models.servicio import Servicio
from app.database import _get_session_factory

async def main():
    session_factory = _get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(Servicio))
        servicios = result.scalars().all()
        if not servicios:
            print("No hay servicios registrados.")
        for s in servicios:
            print(f"ID: {s.servicio_id} | Descripcion: {s.descripcion_servicio} | Tarifa: {s.tarifa_servicio} {s.moneda_tarifa}")

if __name__ == "__main__":
    asyncio.run(main())
