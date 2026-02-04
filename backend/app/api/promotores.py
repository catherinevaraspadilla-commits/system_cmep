"""
API endpoints: promotores CRUD.
Accesible a cualquier usuario autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.user import User
from app.models.promotor import Promotor
from app.models.persona import Persona
from app.models.solicitud import SolicitudCmep
from app.schemas.promotor import CreatePromotorRequest, UpdatePromotorRequest
from app.services.solicitud_service import create_promotor

router = APIRouter(prefix="/promotores", tags=["promotores"])


def _build_promotor_item(p: Promotor, persona: Persona | None = None) -> dict:
    """Construye dict de respuesta para un promotor."""
    if p.tipo_promotor == "PERSONA" and persona:
        nombre = f"{persona.nombres} {persona.apellidos}"
    elif p.tipo_promotor == "EMPRESA":
        nombre = p.razon_social or "?"
    else:
        nombre = p.nombre_promotor_otros or p.fuente_promotor or "?"

    return {
        "promotor_id": p.promotor_id,
        "tipo_promotor": p.tipo_promotor,
        "nombre": nombre,
        "razon_social": p.razon_social,
        "nombre_promotor_otros": p.nombre_promotor_otros,
        "ruc": p.ruc,
        "email": p.email,
        "celular_1": p.celular_1,
        "fuente_promotor": p.fuente_promotor,
        "comentario": p.comentario,
        "persona_id": p.persona_id,
        "persona_nombres": persona.nombres if persona else None,
        "persona_apellidos": persona.apellidos if persona else None,
        "persona_tipo_documento": persona.tipo_documento if persona else None,
        "persona_numero_documento": persona.numero_documento if persona else None,
    }


async def _load_persona(db: AsyncSession, promotor: Promotor) -> Persona | None:
    """Carga persona vinculada si tipo=PERSONA."""
    if promotor.tipo_promotor == "PERSONA" and promotor.persona_id:
        result = await db.execute(
            select(Persona).where(Persona.persona_id == promotor.persona_id)
        )
        return result.scalar_one_or_none()
    return None


# ── GET /promotores ──────────────────────────────────────────────────

@router.get("")
async def listar_promotores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista promotores disponibles."""
    stmt = select(Promotor).order_by(Promotor.promotor_id)
    result = await db.execute(stmt)
    promotores = result.scalars().all()

    items = []
    for p in promotores:
        persona = await _load_persona(db, p)
        items.append(_build_promotor_item(p, persona))

    return {"ok": True, "data": items}


# ── GET /promotores/{id} ─────────────────────────────────────────────

@router.get("/{promotor_id}")
async def detalle_promotor(
    promotor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalle completo de un promotor."""
    result = await db.execute(
        select(Promotor).where(Promotor.promotor_id == promotor_id)
    )
    promotor = result.scalar_one_or_none()
    if not promotor:
        raise HTTPException(status_code=404, detail={
            "ok": False, "error": {"code": "NOT_FOUND", "message": "Promotor no encontrado"},
        })

    persona = await _load_persona(db, promotor)
    return {"ok": True, "data": _build_promotor_item(promotor, persona)}


# ── POST /promotores ─────────────────────────────────────────────────

@router.post("")
async def crear_promotor(
    body: CreatePromotorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear promotor nuevo."""
    promotor = await create_promotor(db, body, created_by=current_user.user_id)
    persona = await _load_persona(db, promotor)
    return {"ok": True, "data": _build_promotor_item(promotor, persona)}


# ── PATCH /promotores/{id} ───────────────────────────────────────────

@router.patch("/{promotor_id}")
async def editar_promotor(
    promotor_id: int,
    body: UpdatePromotorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Editar promotor existente."""
    result = await db.execute(
        select(Promotor).where(Promotor.promotor_id == promotor_id)
    )
    promotor = result.scalar_one_or_none()
    if not promotor:
        raise HTTPException(status_code=404, detail={
            "ok": False, "error": {"code": "NOT_FOUND", "message": "Promotor no encontrado"},
        })

    changes = body.model_dump(exclude_unset=True)

    # Campos directos del promotor
    promotor_fields = {"razon_social", "nombre_promotor_otros", "ruc", "email", "celular_1", "fuente_promotor", "comentario"}
    for field in promotor_fields:
        if field in changes:
            setattr(promotor, field, changes[field])

    # Para tipo PERSONA: actualizar persona vinculada
    if promotor.tipo_promotor == "PERSONA" and promotor.persona_id:
        persona = await _load_persona(db, promotor)
        if persona:
            for field in ("nombres", "apellidos"):
                if field in changes and changes[field]:
                    setattr(persona, field, changes[field])

    promotor.updated_by = current_user.user_id
    await db.flush()

    persona = await _load_persona(db, promotor)
    return {"ok": True, "data": _build_promotor_item(promotor, persona)}


# ── DELETE /promotores/{id} ──────────────────────────────────────────

@router.delete("/{promotor_id}")
async def eliminar_promotor(
    promotor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Eliminar promotor (solo si no tiene solicitudes vinculadas)."""
    result = await db.execute(
        select(Promotor).where(Promotor.promotor_id == promotor_id)
    )
    promotor = result.scalar_one_or_none()
    if not promotor:
        raise HTTPException(status_code=404, detail={
            "ok": False, "error": {"code": "NOT_FOUND", "message": "Promotor no encontrado"},
        })

    # Verificar que no tenga solicitudes vinculadas
    count = (await db.execute(
        select(func.count()).select_from(SolicitudCmep)
        .where(SolicitudCmep.promotor_id == promotor_id)
    )).scalar() or 0

    if count > 0:
        raise HTTPException(status_code=409, detail={
            "ok": False,
            "error": {
                "code": "CONFLICT",
                "message": f"No se puede eliminar: el promotor tiene {count} solicitud(es) vinculada(s)",
            },
        })

    await db.delete(promotor)
    await db.flush()
    return {"ok": True}
