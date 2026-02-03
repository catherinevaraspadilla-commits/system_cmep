"""
Endpoint: GET /servicios — lista de servicios disponibles.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.user import User
from app.models.servicio import Servicio

router = APIRouter(prefix="/servicios", tags=["servicios"])


@router.get("")
async def listar_servicios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos los servicios disponibles."""
    result = await db.execute(
        select(Servicio).order_by(Servicio.servicio_id)
    )
    servicios = result.scalars().all()

    return {
        "ok": True,
        "data": [
            {
                "servicio_id": s.servicio_id,
                "descripcion_servicio": s.descripcion_servicio,
                "tarifa_servicio": str(s.tarifa_servicio),
                "moneda_tarifa": s.moneda_tarifa,
            }
            for s in servicios
        ],
    }
