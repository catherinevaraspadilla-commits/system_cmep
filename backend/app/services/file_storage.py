"""
Servicio de almacenamiento de archivos.
Ref: docs/source/05_api_y_policy.md (Modulo Archivos MVP)

Local: guarda en UPLOAD_DIR (default: uploads/).
Prod:  S3 via boto3 (FILE_STORAGE=s3).
"""

import uuid
from pathlib import Path

from app.config import settings


# ── Helpers ─────────────────────────────────────────────────────────────

def generate_storage_name(original_filename: str) -> str:
    """Genera nombre unico para storage usando UUID + extension original."""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


# ── Local storage ───────────────────────────────────────────────────────

def _ensure_upload_dir() -> Path:
    """Crea el directorio de uploads si no existe y retorna el Path."""
    base = Path(settings.UPLOAD_DIR)
    if not base.is_absolute():
        backend_dir = Path(__file__).resolve().parent.parent.parent
        base = backend_dir / base
    base.mkdir(parents=True, exist_ok=True)
    return base


async def _local_save(file_bytes: bytes, storage_name: str) -> str:
    upload_dir = _ensure_upload_dir()
    dest = upload_dir / storage_name
    dest.write_bytes(file_bytes)
    return str(dest)


async def _local_read(storage_path: str) -> bytes:
    p = Path(storage_path)
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {storage_path}")
    return p.read_bytes()


async def _local_delete(storage_path: str) -> None:
    p = Path(storage_path)
    if p.exists():
        p.unlink()


# ── S3 storage ──────────────────────────────────────────────────────────

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3")
    return _s3_client


async def _s3_save(file_bytes: bytes, storage_name: str) -> str:
    client = _get_s3_client()
    key = f"uploads/{storage_name}"
    client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=file_bytes)
    return key


async def _s3_read(storage_path: str) -> bytes:
    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=settings.S3_BUCKET, Key=storage_path)
        return response["Body"].read()
    except client.exceptions.NoSuchKey:
        raise FileNotFoundError(f"Archivo no encontrado en S3: {storage_path}")


async def _s3_delete(storage_path: str) -> None:
    client = _get_s3_client()
    client.delete_object(Bucket=settings.S3_BUCKET, Key=storage_path)


# ── Public API (routing por FILE_STORAGE) ───────────────────────────────

def _use_s3() -> bool:
    return settings.FILE_STORAGE == "s3"


async def save_file(file_bytes: bytes, storage_name: str) -> str:
    """Guarda bytes en storage (local o S3). Retorna path/key."""
    if _use_s3():
        return await _s3_save(file_bytes, storage_name)
    return await _local_save(file_bytes, storage_name)


async def read_file(storage_path: str) -> bytes:
    """Lee un archivo desde storage (local o S3)."""
    if _use_s3():
        return await _s3_read(storage_path)
    return await _local_read(storage_path)


async def delete_file(storage_path: str) -> None:
    """Elimina un archivo de storage (local o S3)."""
    if _use_s3():
        return await _s3_delete(storage_path)
    return await _local_delete(storage_path)
