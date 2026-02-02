"""
Motor de base de datos y gestion de sesiones SQLAlchemy (async).
Ref: docs/claude/01_architecture_summary.md (seccion 2.3)

Engine se crea de forma lazy para permitir que los tests
sobreescriban la dependencia get_db sin importar asyncmy.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Engine y session factory se crean lazy (no al importar el modulo)
_engine = None
_async_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        from app.config import settings
        url = settings.DATABASE_URL
        if settings.is_sqlite:
            # SQLite no soporta pool_size/max_overflow/pool_pre_ping
            _engine = create_async_engine(url, echo=(settings.APP_ENV == "local"))
        else:
            _engine = create_async_engine(
                url,
                echo=(settings.APP_ENV == "local"),
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


# Propiedades de acceso para codigo que necesite el engine directamente
@property
def engine():
    return _get_engine()


async def get_db() -> AsyncSession:  # type: ignore[misc]
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
