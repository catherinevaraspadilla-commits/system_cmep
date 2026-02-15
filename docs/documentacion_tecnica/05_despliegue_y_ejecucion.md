# Cómo Desplegar y Ejecutar el Proyecto — CMEP

## Opción A: Ejecución Local sin Docker (Recomendada para Desarrollo)

Esta es la opción más rápida. Usa SQLite como base de datos, sin necesidad de instalar MySQL ni Docker.

### Paso 1 — Verificar Requisitos

```bash
python --version    # debe ser 3.12+
node --version      # debe ser 18+
npm --version       # incluido con Node.js
```

**Si falta Node.js:**
- Descargar desde https://nodejs.org/ (versión LTS recomendada)
- Instalar y reiniciar la terminal

**Si falta Python:**
- Descargar desde https://python.org/downloads/
- Asegurarse de marcar "Add to PATH" durante la instalación

---

### Paso 2 — Instalar Dependencias del Backend

```bash
cd backend
pip install -r requirements.txt
```

> Si hay conflictos de versión, usar un entorno virtual:
> ```bash
> python -m venv venv
> venv\Scripts\activate    # Windows
> source venv/bin/activate  # macOS/Linux
> pip install -r requirements.txt
> ```

---

### Paso 3 — Instalar Dependencias del Frontend

```bash
cd frontend
npm install
```

---

### Paso 4 — Configurar Variables de Entorno

**Backend** — crear `backend/.env`:
```env
APP_ENV=local
SESSION_SECRET=dev-secret-local-cmep
CORS_ORIGINS=http://localhost:3000
FILE_STORAGE=local
```

**Frontend** — crear `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

> Sin estas variables, el backend igualmente funciona con valores por defecto (SQLite automático).

---

### Paso 5 — Crear Base de Datos y Datos de Prueba

```bash
cd infra
python seed_dev.py
```

Este script:
- Crea el archivo `cmep_dev.db` (SQLite) en la raíz del proyecto
- Genera todas las tablas del esquema
- Inserta usuarios, empleados, clientes, promotores y servicios de prueba

**Usuarios de prueba creados:**

| Email | Contraseña | Rol |
|-------|-----------|-----|
| `admin@cmep.local` | `admin123` | ADMIN |
| `operador@cmep.local` | `operador123` | OPERADOR |
| `gestor@cmep.local` | `gestor123` | GESTOR |
| `medico@cmep.local` | `medico123` | MEDICO |
| `suspendido@cmep.local` | `suspendido123` | OPERADOR (suspendido) |

---

### Paso 6 — Iniciar el Backend

Abrir una terminal en la carpeta `backend/`:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verificar que esté activo:
```
http://localhost:8000/health
```

---

### Paso 7 — Iniciar el Frontend

Abrir **otra terminal** en la carpeta `frontend/`:

```bash
cd frontend
npm run dev
```

Acceder en el navegador:
```
http://localhost:3000
```

---

### Verificación Rápida

```
✅ http://localhost:8000/health    → {"status": "ok"}
✅ http://localhost:8000/version   → {"version": "..."}
✅ http://localhost:3000           → Pantalla de login
```

---

## Opción B: Ejecución Local con Docker (MySQL)

Requiere **Docker Desktop** instalado y corriendo.

### Paso 1 — Crear archivo `.env` en la raíz

```env
DB_HOST=mysql
DB_PORT=3306
DB_NAME=cmep_dev
DB_USER=cmep_user
DB_PASS=cmep_pass
DB_ROOT_PASS=rootpass
APP_ENV=local
SESSION_SECRET=dev-secret-docker
CORS_ORIGINS=http://localhost:3000
VITE_API_URL=http://localhost:8000
FILE_STORAGE=local
BACKEND_PORT=8000
```

### Paso 2 — Levantar servicios

```bash
docker-compose -f infra/docker-compose.yml up --build
```

### Paso 3 — Ejecutar seed con MySQL

```bash
cd infra
python seed_dev.py --mysql
```

### Paso 4 — Acceder

```
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

---

## Opción C: Despliegue en Producción (AWS)

### Arquitectura de Producción

```
CloudFront → S3 (frontend estático)
Navegador → App Runner (FastAPI) → RDS MySQL 8
                                 → S3 (archivos médicos)
Secrets Manager → variables de entorno del backend
Lambda + EventBridge → limpieza de sesiones expiradas
```

### Pasos de Despliegue

#### 1. Preparar la Base de Datos

```bash
# Conectar a RDS MySQL
mysql -h <rds-endpoint> -u admin -p

CREATE DATABASE cmep_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cmep_user'@'%' IDENTIFIED BY '<password-segura>';
GRANT ALL PRIVILEGES ON cmep_prod.* TO 'cmep_user'@'%';
FLUSH PRIVILEGES;
```

Ejecutar migraciones:
```bash
cd backend
DB_URL=mysql+asyncmy://cmep_user:<pass>@<rds-endpoint>:3306/cmep_prod alembic upgrade head
```

Poblar datos iniciales (producción):
```bash
cd infra
DB_URL=mysql+asyncmy://cmep_user:<pass>@<rds-endpoint>:3306/cmep_prod python seed_prod.py
```

#### 2. Configurar Secrets Manager

Crear secreto con las variables de entorno del backend:
```json
{
  "APP_ENV": "prod",
  "DB_URL": "mysql+asyncmy://cmep_user:<pass>@<rds-endpoint>:3306/cmep_prod",
  "SESSION_SECRET": "<secreto-largo-aleatorio>",
  "CORS_ORIGINS": "https://tu-dominio.com",
  "FILE_STORAGE": "s3",
  "S3_BUCKET": "cmep-archivos-prod",
  "S3_REGION": "us-east-1",
  "COOKIE_DOMAIN": ".tu-dominio.com"
}
```

#### 3. Deploy del Backend en App Runner

```bash
# Construir imagen Docker
cd backend
docker build -t cmep-backend .

# Push a ECR
aws ecr create-repository --repository-name cmep-backend
docker tag cmep-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/cmep-backend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/cmep-backend:latest

# Crear servicio App Runner (desde consola AWS o CLI)
```

Configuración de App Runner:
- Puerto: `8000`
- Healthcheck: `GET /health`
- Variables de entorno: desde Secrets Manager

#### 4. Deploy del Frontend en S3 + CloudFront

```bash
cd frontend
# Crear .env.production
echo "VITE_API_URL=https://api.tu-dominio.com" > .env.production

# Build de producción
npm run build

# Subir a S3
aws s3 sync dist/ s3://cmep-frontend-prod --delete

# Invalidar caché CloudFront
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

#### 5. Configurar CloudFront

- Origin: bucket S3 con acceso OAI
- Comportamiento por defecto: redirigir a `index.html` para SPA routing
- HTTPS obligatorio
- Certificado SSL: ACM (us-east-1 para CloudFront)

---

## Comandos de Utilidad

### Tests

```bash
cd backend
pytest                    # todos los tests
pytest tests/unit/        # solo tests unitarios
pytest tests/integration/ # solo tests de integración
pytest -v                 # con salida detallada
pytest -k "test_auth"     # filtrar por nombre
```

### Diagnóstico de Base de Datos

```bash
cd scripts
python check_db.py        # verifica conexión y tablas
python diagnose.py        # diagnóstico general del sistema
python fix_db.py          # reparaciones comunes
python listar_servicios.py # lista servicios disponibles
```

### Migraciones Alembic

```bash
cd backend
alembic upgrade head              # aplica todas las migraciones pendientes
alembic downgrade -1              # revierte la última migración
alembic history                   # historial de migraciones
alembic revision --autogenerate -m "descripcion"  # crea nueva migración
```

### Build de Producción (Frontend)

```bash
cd frontend
npm run build   # genera /dist listo para producción
npm run preview # sirve el build localmente para verificar
```

---

## Resolución de Problemas Comunes

### Error: `ModuleNotFoundError: No module named 'fastapi'`

El entorno Python no tiene las dependencias instaladas.

```bash
pip install -r backend/requirements.txt
```

### Error: `CORS policy blocked`

El frontend está corriendo en un puerto diferente al configurado.
Verificar `CORS_ORIGINS` en `backend/.env` o variables de entorno.

### Error: `Database locked` (SQLite)

SQLite no soporta múltiples escrituras concurrentes. Solo ocurre en desarrollo.
Reiniciar el backend o eliminar el archivo `.db` y volver a ejecutar el seed.

### Error: `aiosqlite` o `asyncmy` not found

```bash
pip install aiosqlite    # para SQLite async
pip install asyncmy      # para MySQL async
```

### El frontend no conecta al backend

1. Verificar que el backend está corriendo: `http://localhost:8000/health`
2. Verificar `frontend/.env`: `VITE_API_URL=http://localhost:8000`
3. Reiniciar el servidor de Vite (`npm run dev`) después de cambiar `.env`

### Error de bcrypt en Windows

```bash
pip install bcrypt --upgrade
```
Si persiste: `pip install bcrypt==4.2.1 --no-binary bcrypt`

### `node` no encontrado en terminal bash de Windows

Node.js está instalado en Windows pero no está en el PATH de bash.
Usar **PowerShell** o **Símbolo del sistema (cmd)** para ejecutar comandos `node` y `npm`:

```powershell
cd frontend
npm install
npm run dev
```
