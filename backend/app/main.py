"""
Punto de entrada FastAPI para el sistema CMEP.
Ref: docs/claude/01_architecture_summary.md (seccion 2.2)
Ref: docs/claude/02_module_specs.md (M0)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.auth import router as auth_router
from app.api.solicitudes import router as solicitudes_router
from app.api.archivos import router as archivos_router
from app.api.promotores import router as promotores_router
from app.api.empleados import router as empleados_router
from app.api.admin import router as admin_router
from app.api.reportes import router as reportes_router
from app.api.servicios import router as servicios_router

logger = logging.getLogger("cmep")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CMEP backend starting — env=%s", settings.APP_ENV)
    # SQLite local: crear tablas automaticamente si no existen
    if settings.is_sqlite:
        from app.database import Base, _get_engine
        import app.models  # noqa: F401 — registrar modelos en metadata
        engine = _get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite: tablas creadas/verificadas en %s", settings.DATABASE_URL)
    yield
    logger.info("CMEP backend shutting down")


app = FastAPI(
    title="CMEP API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# --- CORS (Ref: risk R-001) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# --- Routers (M1+) ---
app.include_router(auth_router)
app.include_router(solicitudes_router)  # M2
app.include_router(archivos_router)  # M4
app.include_router(promotores_router)  # M4.5
app.include_router(empleados_router)  # M4.5
app.include_router(admin_router)  # M5
app.include_router(reportes_router)  # M7
app.include_router(servicios_router)  # Catalogo servicios


# --- Public endpoints (M0) ---
@app.get("/health")
async def health():
    return {"ok": True, "status": "healthy"}


@app.get("/version")
async def version():
    return {"ok": True, "version": settings.APP_VERSION}
