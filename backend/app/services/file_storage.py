"""
Servicio de almacenamiento de archivos.
Ref: docs/source/05_api_y_policy.md (Modulo Archivos MVP)

Local: guarda en UPLOAD_DIR (default: uploads/).
Prod:  S3 (futuro M6).
"""

import os
import uuid
from pathlib import Path

from app.config import settings


def _ensure_upload_dir() -> Path:
    """Crea el directorio de uploads si no existe y retorna el Path."""
    base = Path(settings.UPLOAD_DIR)
    if not base.is_absolute():
        # Relativo al directorio backend/
        backend_dir = Path(__file__).resolve().parent.parent.parent
        base = backend_dir / base
    base.mkdir(parents=True, exist_ok=True)
    return base


def generate_storage_name(original_filename: str) -> str:
    """Genera nombre unico para storage usando UUID + extension original."""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


async def save_file(file_bytes: bytes, storage_name: str) -> str:
    """
    Guarda bytes en filesystem local.
    Retorna el path relativo dentro de UPLOAD_DIR.
    """
    upload_dir = _ensure_upload_dir()
    dest = upload_dir / storage_name
    dest.write_bytes(file_bytes)
    return str(dest)


async def read_file(storage_path: str) -> bytes:
    """Lee un archivo desde storage local."""
    p = Path(storage_path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {storage_path}")
    return p.read_bytes()


async def delete_file(storage_path: str) -> None:
    """Elimina un archivo de storage local."""
    p = Path(storage_path)
    if p.exists():
        p.unlink()
