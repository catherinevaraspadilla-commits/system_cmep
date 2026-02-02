"""
API endpoint: reportes administrativos (M7).
Ref: docs/claude/M7_reportes_admin.md
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.admin_service import require_admin
from app.services.reportes_service import generar_reporte

router = APIRouter(prefix="/admin", tags=["admin-reportes"])


@router.get("/reportes")
async def obtener_reportes(
    desde: date | None = Query(None, description="Inicio del rango (YYYY-MM-DD)"),
    hasta: date | None = Query(None, description="Fin del rango (YYYY-MM-DD)"),
    estado: str | None = Query(None, description="Filtro estado operativo"),
    agrupacion: str = Query("mensual", description="semanal o mensual"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Genera reporte completo: KPIs, series, distribucion, rankings. Solo ADMIN."""
    data = await generar_reporte(db, desde, hasta, estado, agrupacion)
    return {"ok": True, "data": data}
