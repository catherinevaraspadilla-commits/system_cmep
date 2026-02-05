"""
Servicio de almacenamiento de archivos.
Ref: docs/source/05_api_y_policy.md (Modulo Archivos MVP)

Local: guarda en UPLOAD_DIR (default: uploads/).
Prod:  S3 via boto3 (FILE_STORAGE=s3).
"""

import uuid
from pathlib import Path

from app.config import settings
import os
import boto3
import logging
from botocore.config import Config
from botocore.exceptions import ConnectTimeoutError, ReadTimeoutError, EndpointConnectionError
from starlette.concurrency import run_in_threadpool
from app.config import settings
logger = logging.getLogger(__name__)

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


async def _local_save(file_bytes: bytes, key: str) -> str:
    path = os.path.join(settings.LOCAL_UPLOADS_PATH, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


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
    cfg = Config(
        connect_timeout=5,   # conecta rápido o falla
        read_timeout=60,     # tiempo razonable para subir/leer
        retries={"max_attempts": 2, "mode": "standard"},
    )
    return boto3.client(
        "s3",
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=cfg,
    )

class StorageUploadError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)
        
async def _s3_save(file_bytes: bytes, key: str) -> str:
    client = _get_s3_client()

    try:
        # boto3 es BLOQUEANTE: lo sacamos del worker async
        await run_in_threadpool(
            client.put_object,
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=file_bytes,
        )
    except (ConnectTimeoutError, EndpointConnectionError) as e:
        logger.exception("S3 connect error uploading key=%s", key)
        raise StorageUploadError(
            code="S3_CONNECT_TIMEOUT",
            message="No se pudo conectar a S3 (timeout/red). Intenta nuevamente."
        ) from e
    except ReadTimeoutError as e:
        logger.exception("S3 read timeout uploading key=%s", key)
        raise StorageUploadError(
            code="S3_READ_TIMEOUT",
            message="La subida a S3 tardó demasiado (timeout). Intenta nuevamente."
        ) from e
    except Exception as e:
        logger.exception("Unexpected S3 error uploading key=%s", key)
        raise StorageUploadError(
            code="S3_UPLOAD_FAILED",
            message="Error inesperado subiendo el archivo."
        ) from e

    url = f"https://{settings.S3_BUCKET}.s3.amazonaws.com/{key}"
    return url


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


async def save_file(file_bytes: bytes, key: str) -> str:
    if _use_s3():
        return await _s3_save(file_bytes, key)
    return await _local_save(file_bytes, key)


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
