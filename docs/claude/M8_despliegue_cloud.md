# M8 — Despliegue en AWS (Plan Detallado)

> Este modulo corresponde al M6 original en `docs/source/07_arquitectura_y_despliegue.md` y `08_plan.md`.
> Renombrado a M8 porque M6 y M7 se usaron para override/audit y reportes respectivamente.

---

## Resumen

Desplegar el sistema CMEP completo en AWS. El objetivo es que funcione identicamente a local pero con infraestructura productiva: MySQL en vez de SQLite, S3 en vez de filesystem, HTTPS, dominio propio.

---

## Arquitectura Target

```
                    [CloudFront CDN]
                    (HTTPS + SPA fallback)
                          |
                    [S3 - Frontend]
                    (React build estatico)

[Usuario] --HTTPS--> [CloudFront] ---> [App Runner]
                                        (FastAPI backend)
                                            |
                          +-----------------+------------------+
                          |                 |                  |
                    [RDS MySQL 8]    [S3 Archivos]    [Secrets Manager]
                    (BD transaccional) (uploads)       (credenciales)
                          |
                    [CloudWatch]     [EventBridge + Lambda]
                    (logs/metricas)  (limpieza sesiones)
```

---

## Componentes AWS

### 1. Amazon RDS (MySQL 8)

**Proposito**: BD transaccional (reemplaza SQLite local).

**Configuracion**:
- Instancia: `db.t3.micro` (free tier) o `db.t3.small`
- Motor: MySQL 8.0
- Almacenamiento: 20 GB gp3
- Backups automaticos: 7 dias
- Multi-AZ: No (MVP)
- Acceso: Solo desde la VPC (no publico)
- Security group: permite ingress puerto 3306 solo desde App Runner

**Migracion de datos**:
- El schema se crea con `Base.metadata.create_all()` (como en dev)
- Seed inicial con `python infra/seed_dev.py --mysql`
- Para produccion real: usar Alembic migrations

**Cambios necesarios en codigo**: Ninguno. `config.py` ya soporta `DB_URL` como variable de entorno con driver `mysql+asyncmy`.

### 2. AWS App Runner

**Proposito**: Ejecutar el backend FastAPI como servicio managed.

**Configuracion**:
- Fuente: Imagen Docker desde ECR (o directamente del repo)
- CPU: 0.25 vCPU
- Memoria: 0.5 GB
- Puerto: 8000
- Auto-scaling: 1-3 instancias
- Health check: `GET /health`
- Variables de entorno: desde Secrets Manager

**Dockerfile** (ya existe en `backend/Dockerfile`, puede requerir ajustes):
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Variables de entorno necesarias**:
```
DB_URL=mysql+asyncmy://user:pass@rds-endpoint:3306/cmep_prod
APP_ENV=prod
SESSION_SECRET=<secreto-aleatorio-64-chars>
CORS_ORIGINS=https://cmep.tudominio.com
FILE_STORAGE=s3
S3_BUCKET=cmep-archivos-prod
```

### 3. Amazon S3 — Archivos de negocio

**Proposito**: Storage de archivos subidos (evidencias de pago, documentos).

**Configuracion**:
- Bucket: `cmep-archivos-prod` (privado)
- Cifrado: AES-256 (SSE-S3)
- Versionado: Deshabilitado (MVP)
- Acceso: Solo desde App Runner via IAM role
- CORS: No necesario (backend sube/baja, no el browser)

**Cambios necesarios en codigo**:
- `backend/app/services/file_storage.py` ya tiene la logica. Solo necesita:
  1. Instalar `boto3` (agregar a requirements.txt)
  2. Implementar `S3Storage` class con `upload()` y `download()` usando URLs firmadas
  3. El config `FILE_STORAGE=s3` ya existe, solo falta la implementacion S3

**Implementacion S3Storage** (lo que Claude debe crear):
```python
# backend/app/services/file_storage.py — agregar clase S3Storage
import boto3
from botocore.exceptions import ClientError

class S3Storage:
    def __init__(self, bucket: str):
        self.s3 = boto3.client("s3")
        self.bucket = bucket

    async def save(self, filename: str, content: bytes) -> str:
        self.s3.put_object(Bucket=self.bucket, Key=filename, Body=content)
        return filename

    async def get(self, filename: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=filename)
        return response["Body"].read()

    async def delete(self, filename: str):
        self.s3.delete_object(Bucket=self.bucket, Key=filename)

    def get_presigned_url(self, filename: str, expires_in: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": filename},
            ExpiresIn=expires_in,
        )
```

### 4. Amazon S3 — Frontend estatico

**Proposito**: Alojar el build de React.

**Configuracion**:
- Bucket: `cmep-frontend-prod` (privado, acceso via CloudFront OAC)
- Build: `cd frontend && npm run build` genera `dist/`
- Deploy: `aws s3 sync dist/ s3://cmep-frontend-prod/`

### 5. Amazon CloudFront

**Proposito**: CDN, HTTPS, SPA routing.

**Configuracion**:
- Origin 1: S3 frontend (default behavior)
- Origin 2: App Runner backend (behavior para `/api/*` o subdomain)
- Certificado SSL: ACM (gratis) con dominio propio
- Default root object: `index.html`
- Error pages: 403/404 -> `/index.html` (SPA fallback)
- Cache: Static assets con cache largo, API sin cache

**Opciones de routing API**:

**Opcion A — Subdomain** (recomendada):
- `cmep.tudominio.com` -> CloudFront -> S3 frontend
- `api.cmep.tudominio.com` -> App Runner directamente
- Frontend: `VITE_API_URL=https://api.cmep.tudominio.com`

**Opcion B — Path-based**:
- `cmep.tudominio.com/*` -> S3 frontend
- `cmep.tudominio.com/api/*` -> App Runner (via CloudFront behavior)
- Requiere configurar behaviors en CloudFront y prefijo `/api` en backend

### 6. AWS Secrets Manager

**Proposito**: Almacenar secretos fuera del codigo.

**Secretos necesarios**:
```json
{
  "DB_URL": "mysql+asyncmy://cmep_user:PASSWORD@rds-endpoint:3306/cmep_prod",
  "SESSION_SECRET": "random-64-char-string",
  "S3_BUCKET": "cmep-archivos-prod"
}
```

**Acceso**: App Runner instance role con permiso `secretsmanager:GetSecretValue`.

### 7. CloudWatch

**Proposito**: Logs y monitoreo.

**Configuracion**:
- App Runner envia logs automaticamente a CloudWatch
- Alarmas: error rate > 5%, latencia p99 > 2s, 5xx count > 10/min
- Dashboard: requests/min, errores, latencia

### 8. EventBridge + Lambda

**Proposito**: Tarea programada para limpiar sesiones expiradas.

**Implementacion**:
```python
# lambda_cleanup.py
import pymysql

def handler(event, context):
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sessions WHERE expires_at < NOW()")
        deleted = cur.rowcount
    conn.commit()
    conn.close()
    return {"deleted_sessions": deleted}
```

**Schedule**: Cada 6 horas via EventBridge rule.

### 9. IAM

**Roles necesarios**:

| Rol | Permisos |
|-----|----------|
| AppRunnerRole | RDS connect, S3 read/write (bucket archivos), Secrets Manager read |
| LambdaCleanupRole | RDS connect, CloudWatch logs |
| DeployRole (CI/CD) | ECR push, App Runner deploy, S3 sync frontend |

---

## Plan de Ejecucion — Paso a Paso

### Fase 1: Preparacion del codigo (Claude)

- [ ] **1.1** Agregar `boto3` a `backend/requirements.txt`
- [ ] **1.2** Implementar `S3Storage` en `file_storage.py` (clase que use boto3)
- [ ] **1.3** Modificar `file_storage.py` para seleccionar LocalStorage o S3Storage segun `FILE_STORAGE` config
- [ ] **1.4** Verificar que `backend/Dockerfile` funciona (build y run local)
- [ ] **1.5** Ajustar `backend/app/database.py` para soportar MySQL async driver (`asyncmy`)
- [ ] **1.6** Agregar `asyncmy` y `pymysql` a `backend/requirements.txt`
- [ ] **1.7** Verificar que `CORS_ORIGINS` soporta multiples origenes (ya lo hace via `.split(",")`)
- [ ] **1.8** Crear `lambda_cleanup.py` en `infra/` para limpieza de sesiones
- [ ] **1.9** Actualizar `.env.example` con variables de produccion comentadas
- [ ] **1.10** Verificar que 117 tests siguen pasando tras cambios

### Fase 2: Infraestructura AWS (Usuario — via consola o CLI)

- [ ] **2.1** Crear cuenta AWS (si no existe) y configurar billing alerts
- [ ] **2.2** Crear VPC con 2 subnets (publica + privada) o usar la default VPC
- [ ] **2.3** Crear RDS MySQL 8 instance
  - Engine: MySQL 8.0
  - Clase: db.t3.micro
  - Storage: 20 GB gp3
  - Subnet: privada
  - Security group: ingress 3306 desde App Runner SG
  - Crear DB `cmep_prod` y usuario `cmep_user`
- [ ] **2.4** Crear S3 bucket para archivos: `cmep-archivos-prod`
  - Block all public access
  - Encryption: SSE-S3
- [ ] **2.5** Crear S3 bucket para frontend: `cmep-frontend-prod`
  - Block all public access (acceso via CloudFront OAC)
- [ ] **2.6** Crear secreto en Secrets Manager con DB_URL, SESSION_SECRET, S3_BUCKET
- [ ] **2.7** Crear IAM role para App Runner con permisos:
  - `AmazonRDSDataFullAccess` (o politica custom mas restrictiva)
  - `AmazonS3FullAccess` limitada al bucket de archivos
  - `SecretsManagerReadWrite` limitada al secreto CMEP
- [ ] **2.8** Crear ECR repository para la imagen Docker del backend
- [ ] **2.9** Build y push Docker image:
  ```bash
  cd backend
  docker build -t cmep-backend .
  aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
  docker tag cmep-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/cmep-backend:latest
  docker push <account>.dkr.ecr.<region>.amazonaws.com/cmep-backend:latest
  ```
- [ ] **2.10** Crear App Runner service
  - Source: ECR image
  - Port: 8000
  - Health check: HTTP GET /health
  - Environment: Variables desde Secrets Manager
  - Instance role: el IAM role creado en 2.7
- [ ] **2.11** Ejecutar seed en produccion:
  - Conectarse a la instancia RDS (via bastion o Cloud9)
  - Ejecutar `python infra/seed_dev.py --mysql` con las credenciales de prod
  - O alternativamente: crear un endpoint temporal `/admin/seed` protegido

### Fase 3: Frontend deploy (Usuario)

- [ ] **3.1** Build del frontend:
  ```bash
  cd frontend
  VITE_API_URL=https://api.cmep.tudominio.com npm run build
  ```
- [ ] **3.2** Subir a S3:
  ```bash
  aws s3 sync dist/ s3://cmep-frontend-prod/ --delete
  ```
- [ ] **3.3** Crear distribucion CloudFront:
  - Origin: S3 bucket frontend
  - OAC (Origin Access Control) para acceso privado
  - Default root object: `index.html`
  - Error pages: 403 -> `/index.html` (status 200), 404 -> `/index.html` (status 200)
  - Certificado SSL: solicitar en ACM para tu dominio
- [ ] **3.4** Configurar dominio DNS (Route 53 o tu proveedor):
  - `cmep.tudominio.com` -> CloudFront distribution
  - `api.cmep.tudominio.com` -> App Runner URL (CNAME)
- [ ] **3.5** Invalidar cache CloudFront:
  ```bash
  aws cloudfront create-invalidation --distribution-id XXXXX --paths "/*"
  ```

### Fase 4: CORS y cookies (Claude + Usuario)

- [ ] **4.1** Configurar CORS en backend:
  ```
  CORS_ORIGINS=https://cmep.tudominio.com
  ```
- [ ] **4.2** Ajustar cookie settings para produccion en `auth_service.py`:
  ```python
  response.set_cookie(
      key="cmep_session",
      value=session.session_id,
      httponly=True,
      secure=True,          # HTTPS obligatorio
      samesite="none",      # Cross-origin (si API en subdomain diferente)
      domain=".tudominio.com",  # Compartir cookie entre subdomains
      max_age=86400,
  )
  ```
- [ ] **4.3** Test manual: login desde el frontend desplegado, verificar cookie se setea

### Fase 5: Monitoreo y mantenimiento (Usuario)

- [ ] **5.1** Verificar logs en CloudWatch (App Runner los envia automaticamente)
- [ ] **5.2** Crear alarma CloudWatch: 5xx errors > 5 en 5 minutos
- [ ] **5.3** Crear Lambda para limpieza de sesiones:
  - Usar `infra/lambda_cleanup.py`
  - Runtime: Python 3.12
  - EventBridge rule: cada 6 horas
  - VPC: misma que RDS
  - Security group: permite egress a RDS
- [ ] **5.4** Configurar backups RDS (automaticos, 7 dias minimo)

### Fase 6: Smoke test en produccion (Usuario)

- [ ] **6.1** Abrir `https://cmep.tudominio.com` — carga login
- [ ] **6.2** Login con admin@cmep.local / admin123
- [ ] **6.3** Crear una solicitud de prueba
- [ ] **6.4** Ejecutar flujo completo: asignar gestor, pagar, asignar medico, cerrar
- [ ] **6.5** Subir y descargar un archivo
- [ ] **6.6** Verificar reportes admin
- [ ] **6.7** Probar desde movil (responsive)

---

## Variables de entorno — Produccion

```bash
# Backend (App Runner)
DB_URL=mysql+asyncmy://cmep_user:PASS@rds-endpoint.us-east-1.rds.amazonaws.com:3306/cmep_prod
APP_ENV=prod
SESSION_SECRET=<generar-con: python -c "import secrets; print(secrets.token_hex(32))">
CORS_ORIGINS=https://cmep.tudominio.com
FILE_STORAGE=s3
S3_BUCKET=cmep-archivos-prod
UPLOAD_DIR=uploads

# Frontend (build time)
VITE_API_URL=https://api.cmep.tudominio.com
```

---

## Estimacion de costos AWS (minima)

| Servicio | Config | Costo mensual aprox |
|----------|--------|---------------------|
| RDS MySQL | db.t3.micro (free tier 12 meses) | $0 - $15 |
| App Runner | 0.25 vCPU, 0.5 GB | $5 - $15 |
| S3 (archivos) | < 1 GB | < $1 |
| S3 (frontend) | < 50 MB | < $1 |
| CloudFront | < 10 GB transfer | $0 - $2 |
| Secrets Manager | 1 secreto | $0.40 |
| CloudWatch | Logs basicos | $0 - $5 |
| Lambda | < 1000 invocaciones/mes | $0 |
| **Total estimado** | | **$7 - $40/mes** |

---

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| CORS/cookies cross-origin | Alta | Alto | Probar config SameSite=None, Secure=true, domain correcto |
| Cold start App Runner | Media | Bajo | Primer request tarda ~5s, configurar min instances=1 si es critico |
| Migracion SQLite -> MySQL | Baja | Medio | SQLAlchemy abstrae, pero verificar tipos de datos (DATETIME, ENUM) |
| Costos inesperados | Baja | Medio | Billing alerts, usar free tier, apagar recursos no usados |
| Permisos IAM insuficientes | Media | Medio | Probar cada servicio individualmente antes de integrar |

---

## Resumen de quien hace que

### Claude hace:
- Fase 1 completa (preparar codigo para produccion)
- Fase 4.1-4.2 (configurar CORS y cookies)

### El usuario hace:
- Fase 2 completa (crear infraestructura AWS via consola/CLI)
- Fase 3 completa (build y deploy frontend)
- Fase 5 completa (monitoreo)
- Fase 6 completa (smoke tests)

### Ambos:
- Fase 4.3 (test manual de cookies — usuario prueba, Claude ajusta si falla)
