"""
Utilidad de tiempo para el backend CMEP.
Usa naive UTC datetime para compatibilidad SQLAlchemy (MySQL + SQLite test).
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Retorna naive UTC datetime (sin tzinfo) compatible con MySQL y SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
