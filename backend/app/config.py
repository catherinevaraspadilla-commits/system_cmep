"""
Configuracion central del backend CMEP.
Lee variables de entorno y expone settings tipados.
Ref: docs/claude/01_architecture_summary.md (seccion 6)
"""

import os
from pydantic_settings import BaseSettings

# Ruta al SQLite local de desarrollo (project_root/cmep_dev.db)
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))       # backend/app/
_BACKEND_DIR = os.path.dirname(_CONFIG_DIR)                    # backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)                  # project root
_SQLITE_PATH = os.path.abspath(os.path.join(_PROJECT_ROOT, "cmep_dev.db"))
_DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{_SQLITE_PATH}"


class Settings(BaseSettings):
    # Base de datos
    # DB_URL tiene prioridad. Si no se define, usa SQLite local.
    # Docker/produccion definen DB_URL=mysql+asyncmy://...
    DB_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "cmep_dev"
    DB_USER: str = "cmep_user"
    DB_PASS: str = "cmep_pass"

    # Aplicacion
    APP_ENV: str = "local"
    APP_VERSION: str = "0.1.0"

    # Sesiones
    SESSION_SECRET: str = "dev-secret-change-in-production"
    SESSION_EXPIRE_HOURS: int = 24

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Storage
    FILE_STORAGE: str = "local"
    UPLOAD_DIR: str = "uploads"
    S3_BUCKET: str = ""

    # Cookies (produccion)
    COOKIE_DOMAIN: str = ""  # vacio = no domain attr; prod: ".tudominio.com"

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_URL:
            return self.DB_URL
        # Default: SQLite local para desarrollo sin Docker
        return _DEFAULT_SQLITE_URL

    @property
    def DATABASE_URL_SYNC(self) -> str:
        if self.DB_URL:
            return self.DB_URL.replace("+asyncmy", "+pymysql").replace("+aiosqlite", "")
        return _DEFAULT_SQLITE_URL.replace("+aiosqlite", "")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "prod"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
