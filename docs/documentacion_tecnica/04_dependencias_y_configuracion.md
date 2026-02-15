# Dependencias y Configuración — CMEP

## Requisitos del Sistema

| Herramienta | Versión mínima | Verificar con |
|-------------|---------------|---------------|
| Python | 3.12+ (probado en 3.13.1) | `python --version` |
| pip | 25+ | `pip --version` |
| Node.js | 18+ (probado en 20) | `node --version` |
| npm | 8+ | `npm --version` |
| Git | cualquier versión reciente | `git --version` |

> Para producción con Docker: **Docker Desktop** o **Docker Engine + docker-compose**.

---

## Dependencias del Backend

Archivo: [backend/requirements.txt](../../../backend/requirements.txt)

### Dependencias de Producción

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `fastapi` | 0.115.6 | Framework web async |
| `uvicorn[standard]` | 0.34.0 | Servidor ASGI (incluye websockets, watchfiles) |
| `pydantic-settings` | 2.7.1 | Carga y validación de variables de entorno |
| `sqlalchemy[asyncio]` | 2.0.46 | ORM async + core SQL |
| `asyncmy` | 0.2.9 | Driver async para MySQL |
| `pymysql` | 1.1.1 | Driver sync MySQL (usado por Alembic) |
| `alembic` | 1.14.1 | Migraciones de esquema de base de datos |
| `bcrypt` | 4.2.1 | Hash de contraseñas |
| `python-multipart` | 0.0.20 | Soporte para subida de archivos (multipart/form-data) |
| `boto3` | >=1.35.0 | SDK AWS (S3 para almacenamiento de archivos) |

### Dependencias de Testing

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `pytest` | 8.3.4 | Framework de tests |
| `pytest-asyncio` | 0.25.2 | Tests async con asyncio |
| `httpx` | 0.28.1 | Cliente HTTP para tests de integración |
| `aiosqlite` | 0.20.0 | SQLite async (BD en memoria para tests) |
| `anyio` | 4.8.0 | Backend async para tests |

### Instalación

```bash
cd backend
pip install -r requirements.txt
```

---

## Dependencias del Frontend

Archivo: [frontend/package.json](../../../frontend/package.json)

### Dependencias de Producción

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `react` | 18.3.1 | Librería de UI |
| `react-dom` | 18.3.1 | Renderizado en navegador |
| `react-router-dom` | 6.28.0 | Navegación y routing SPA |
| `@mui/material` | 7.3.7 | Componentes Material-UI |
| `@mui/icons-material` | 7.3.7 | Iconos MUI |
| `@mui/x-date-pickers` | 8.5.2 | Selector de fechas MUI |
| `recharts` | 3.7.0 | Gráficos y visualizaciones |
| `dayjs` | 1.11.19 | Manipulación de fechas |
| `react-datepicker` | 7.6.0 | Selector de fechas alternativo |

### Dependencias de Desarrollo

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `vite` | 6.0.5 | Bundler y dev server |
| `@vitejs/plugin-react` | 4.3.4 | Plugin Vite para React |
| `typescript` | 5.6.3 | Tipado estático |
| `@types/react` | 18.3.17 | Tipos TypeScript para React |
| `@types/react-dom` | 18.3.5 | Tipos TypeScript para React DOM |

### Instalación

```bash
cd frontend
npm install
```

---

## Variables de Entorno

### Variables del Backend

Archivo de referencia: [backend/.env.example](../../../backend/.env.example)

Crear el archivo `.env` en la carpeta `backend/` (o en la raíz si se usa el `.env.example` raíz):

| Variable | Valor por defecto | Descripción |
|----------|------------------|-------------|
| `APP_ENV` | `local` | Entorno: `local` o `prod` |
| `APP_VERSION` | `0.1.0` | Versión de la aplicación |
| `DB_URL` | _(vacío)_ | URL completa de BD. Si está vacío, usa las variables individuales o SQLite |
| `DB_HOST` | `localhost` | Host de MySQL |
| `DB_PORT` | `3306` | Puerto de MySQL |
| `DB_NAME` | `cmep_dev` | Nombre de la BD |
| `DB_USER` | `cmep_user` | Usuario de BD |
| `DB_PASS` | `cmep_pass` | Contraseña de BD |
| `SESSION_SECRET` | `dev-secret-change-in-production` | Clave para firma de sesiones. **Cambiar en producción** |
| `SESSION_EXPIRE_HOURS` | `24` | Duración de la sesión en horas |
| `CORS_ORIGINS` | `http://localhost:3000` | Orígenes permitidos (separados por coma) |
| `FILE_STORAGE` | `local` | Backend de archivos: `local` o `s3` |
| `UPLOAD_DIR` | `uploads` | Carpeta local para archivos (solo si `FILE_STORAGE=local`) |
| `S3_BUCKET` | _(vacío)_ | Nombre del bucket S3 (solo producción) |
| `S3_REGION` | `us-east-1` | Región AWS del bucket |
| `COOKIE_DOMAIN` | _(vacío)_ | Dominio de la cookie. Vacío para local; `.dominio.com` para prod |

**Comportamiento de la base de datos:**
```
DB_URL especificado        → usa esa URL directamente (MySQL/PostgreSQL)
DB_HOST/PORT/NAME/USER/PASS → construye URL MySQL
(ninguno)                  → usa SQLite en {raíz}/cmep_dev.db
```

### Variables del Frontend

Archivo de referencia: [frontend/.env.example](../../../frontend/frontend.env.example) (o el `.env.example` raíz)

Crear el archivo `.env` en la carpeta `frontend/`:

| Variable | Valor por defecto | Descripción |
|----------|------------------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | URL base del backend. **Debe comenzar con `VITE_`** para ser accesible en el código |

> Vite expone al navegador solo las variables con prefijo `VITE_`.

---

## Configuración por Entorno

### Local (sin Docker)

**Backend** — crear `backend/.env`:
```env
APP_ENV=local
SESSION_SECRET=cualquier-secreto-local
CORS_ORIGINS=http://localhost:3000
FILE_STORAGE=local
```
> Con esto, el backend usará **SQLite automáticamente**.

**Frontend** — crear `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

### Local con Docker (MySQL)

Crear `.env` en la raíz del proyecto:
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cmep_dev
DB_USER=cmep_user
DB_PASS=cmep_pass
DB_ROOT_PASS=rootpass
APP_ENV=local
SESSION_SECRET=dev-secret-local
CORS_ORIGINS=http://localhost:3000
VITE_API_URL=http://localhost:8000
FILE_STORAGE=local
```

### Producción (AWS)

```env
APP_ENV=prod
DB_URL=mysql+asyncmy://usuario:pass@rds-host:3306/cmep_prod
SESSION_SECRET=secreto-largo-y-aleatorio-generado
CORS_ORIGINS=https://tu-dominio.com
FILE_STORAGE=s3
S3_BUCKET=cmep-archivos-prod
S3_REGION=us-east-1
COOKIE_DOMAIN=.tu-dominio.com
```

---

## Configuración Adicional

### Alembic (Migraciones)

Archivo: [backend/alembic.ini](../../../backend/alembic.ini)

Solo necesario si se usa MySQL en desarrollo o producción. Para SQLite local, el seed crea las tablas automáticamente.

```bash
cd backend
alembic upgrade head    # aplica todas las migraciones
alembic revision --autogenerate -m "descripcion"  # genera nueva migración
```

### pytest (Tests)

Archivo: [backend/pytest.ini](../../../backend/pytest.ini)

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

Los tests usan SQLite en memoria — no necesitan configuración de BD externa.

```bash
cd backend
pytest              # todos los tests
pytest tests/unit/  # solo unitarios
pytest -v           # con detalle
```
