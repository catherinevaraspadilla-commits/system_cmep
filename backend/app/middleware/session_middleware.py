"""
Middleware y dependencias de autenticacion por sesion.
Ref: docs/claude/02_module_specs.md (M1/T015)
Ref: docs/source/05_api_y_policy.md — regla de acceso: toda ruta /app/* requiere sesion
"""

from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_session_with_user

SESSION_COOKIE_NAME = "cmep_session"


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependencia FastAPI que extrae el usuario de la sesion.
    Lanza 401 si no hay sesion valida.
    Lanza 403 si el usuario esta SUSPENDIDO.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="No autenticado")

    result = await get_session_with_user(db, session_id)
    if result is None:
        raise HTTPException(status_code=401, detail="Sesion invalida o expirada")

    _session, user = result
    return user
