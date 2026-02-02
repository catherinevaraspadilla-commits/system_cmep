"""
API endpoints: empleados (lista para seleccion en formularios).
Ref: docs/claude/M4_5_incremental_improvements.md

GET /empleados?rol=GESTOR  → lista gestores activos con nombre
GET /empleados?rol=MEDICO  → lista medicos activos con nombre
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.user import User
from app.models.empleado import Empleado

router = APIRouter(prefix="/empleados", tags=["empleados"])


@router.get("")
async def listar_empleados(
    rol: str = Query(..., description="Filtrar por rol: GESTOR, MEDICO, OPERADOR"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista empleados activos por rol, con persona_id y nombre."""
    stmt = select(Empleado).where(
        Empleado.rol_empleado == rol,
        Empleado.estado_empleado == "ACTIVO",
    ).order_by(Empleado.empleado_id)

    result = await db.execute(stmt)
    empleados = result.scalars().all()

    items = []
    for emp in empleados:
        persona = emp.persona
        nombre = f"{persona.nombres} {persona.apellidos}" if persona else "?"
        items.append({
            "persona_id": emp.persona_id,
            "nombre": nombre,
            "rol": emp.rol_empleado,
        })

    return {"ok": True, "data": items}
