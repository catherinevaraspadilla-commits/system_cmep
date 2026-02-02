"""
API endpoints: promotores (lista para seleccion en formularios).
Ref: docs/claude/M4_5_incremental_improvements.md (PASO 2.2)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.user import User
from app.models.promotor import Promotor
from app.models.persona import Persona

router = APIRouter(prefix="/promotores", tags=["promotores"])


@router.get("")
async def listar_promotores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista promotores disponibles para seleccion."""
    stmt = select(Promotor).order_by(Promotor.promotor_id)
    result = await db.execute(stmt)
    promotores = result.scalars().all()

    items = []
    for p in promotores:
        # Build display name based on type
        if p.tipo_promotor == "PERSONA" and p.persona_id:
            persona_result = await db.execute(
                select(Persona).where(Persona.persona_id == p.persona_id)
            )
            persona = persona_result.scalar_one_or_none()
            nombre = f"{persona.nombres} {persona.apellidos}" if persona else "?"
        elif p.tipo_promotor == "EMPRESA":
            nombre = p.razon_social or "?"
        else:
            nombre = p.nombre_promotor_otros or p.fuente_promotor or "?"

        items.append({
            "promotor_id": p.promotor_id,
            "tipo_promotor": p.tipo_promotor,
            "nombre": nombre,
            "fuente_promotor": p.fuente_promotor,
        })

    return {"ok": True, "data": items}
