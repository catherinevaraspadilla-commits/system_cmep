"""
API endpoints para archivos (M4).
Ref: docs/source/05_api_y_policy.md (Modulo Archivos MVP)

POST /solicitudes/{id}/archivos  — upload
GET  /archivos/{archivo_id}      — download
DELETE /archivos/{archivo_id}    — delete
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.session_middleware import get_current_user
from app.models.user import User
from app.models.solicitud import (
    SolicitudCmep,
    Archivo,
    SolicitudArchivo,
    PagoSolicitud,
)
from app.services.file_storage import (
    generate_storage_name,
    save_file,
    read_file,
    delete_file,
)

router = APIRouter(tags=["archivos"])

# Tipos permitidos
ALLOWED_TIPO_ARCHIVO = {"EVIDENCIA_PAGO", "DOCUMENTO", "OTROS"}

# Tamano maximo: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


# ── POST /solicitudes/{id}/archivos ──────────────────────────────────

@router.post("/solicitudes/{solicitud_id}/archivos")
async def upload_archivo(
    solicitud_id: int,
    file: UploadFile = File(...),
    tipo_archivo: str = Form("OTROS"),
    pago_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sube un archivo y lo asocia a la solicitud."""
    # Validar tipo_archivo
    if tipo_archivo not in ALLOWED_TIPO_ARCHIVO:
        raise HTTPException(status_code=422, detail={
            "ok": False,
            "error": {"code": "VALIDATION_ERROR",
                      "message": f"tipo_archivo debe ser uno de: {', '.join(sorted(ALLOWED_TIPO_ARCHIVO))}"},
        })

    # Validar solicitud existe
    result = await db.execute(
        select(SolicitudCmep).where(SolicitudCmep.solicitud_id == solicitud_id)
    )
    solicitud = result.scalar_one_or_none()
    if not solicitud:
        raise HTTPException(status_code=404, detail={
            "ok": False,
            "error": {"code": "NOT_FOUND", "message": "Solicitud no encontrada"},
        })

    # Validar pago_id si se proporciona
    if pago_id is not None:
        pago_result = await db.execute(
            select(PagoSolicitud).where(
                PagoSolicitud.pago_id == pago_id,
                PagoSolicitud.solicitud_id == solicitud_id,
            )
        )
        if not pago_result.scalar_one_or_none():
            raise HTTPException(status_code=422, detail={
                "ok": False,
                "error": {"code": "VALIDATION_ERROR",
                          "message": "pago_id no pertenece a esta solicitud"},
            })

    # Leer contenido del archivo
    file_bytes = await file.read()

    # Validar tamano
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=422, detail={
            "ok": False,
            "error": {"code": "VALIDATION_ERROR",
                      "message": f"Archivo excede el tamano maximo ({MAX_FILE_SIZE // (1024*1024)} MB)"},
        })

    # Guardar en storage
    original_name = file.filename or "archivo"
    storage_name = generate_storage_name(original_name)
    storage_path = await save_file(file_bytes, storage_name)

    # Crear registro Archivo
    archivo = Archivo(
        nombre_original=original_name,
        nombre_storage=storage_name,
        tipo=tipo_archivo,
        mime_type=file.content_type,
        tamano_bytes=len(file_bytes),
        storage_path=storage_path,
        created_by=current_user.user_id,
    )
    db.add(archivo)
    await db.flush()

    # Crear junction SolicitudArchivo
    sol_archivo = SolicitudArchivo(
        solicitud_id=solicitud_id,
        archivo_id=archivo.archivo_id,
        pago_id=pago_id,
        created_by=current_user.user_id,
    )
    db.add(sol_archivo)
    await db.flush()

    return {
        "ok": True,
        "data": {
            "archivo_id": archivo.archivo_id,
            "nombre": archivo.nombre_original,
            "tipo": archivo.tipo,
            "tamano_bytes": archivo.tamano_bytes,
            "mime_type": archivo.mime_type,
        },
    }


# ── GET /archivos/{archivo_id} ───────────────────────────────────────

@router.get("/archivos/{archivo_id}")
async def download_archivo(
    archivo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Descarga un archivo por su ID."""
    result = await db.execute(
        select(Archivo).where(Archivo.archivo_id == archivo_id)
    )
    archivo = result.scalar_one_or_none()
    if not archivo:
        raise HTTPException(status_code=404, detail={
            "ok": False,
            "error": {"code": "NOT_FOUND", "message": "Archivo no encontrado"},
        })

    try:
        file_bytes = await read_file(archivo.storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail={
            "ok": False,
            "error": {"code": "NOT_FOUND", "message": "Archivo fisico no encontrado en storage"},
        })

    return Response(
        content=file_bytes,
        media_type=archivo.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{archivo.nombre_original}"',
        },
    )


# ── DELETE /archivos/{archivo_id} ────────────────────────────────────

@router.delete("/archivos/{archivo_id}")
async def delete_archivo(
    archivo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elimina un archivo (registro + fichero fisico)."""
    result = await db.execute(
        select(Archivo).where(Archivo.archivo_id == archivo_id)
    )
    archivo = result.scalar_one_or_none()
    if not archivo:
        raise HTTPException(status_code=404, detail={
            "ok": False,
            "error": {"code": "NOT_FOUND", "message": "Archivo no encontrado"},
        })

    # Eliminar junction records
    junctions = await db.execute(
        select(SolicitudArchivo).where(SolicitudArchivo.archivo_id == archivo_id)
    )
    for junction in junctions.scalars().all():
        await db.delete(junction)

    # Eliminar archivo fisico
    try:
        await delete_file(archivo.storage_path)
    except Exception:
        pass  # Si falla borrado fisico, seguimos con borrado logico

    # Eliminar registro
    await db.delete(archivo)
    await db.flush()

    return {"ok": True}
