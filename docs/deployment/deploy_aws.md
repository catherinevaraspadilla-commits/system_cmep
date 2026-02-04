# CMEP - Despliegue AWS (Documentacion Completa)

> Region: **us-east-1 (N. Virginia)**
> Dominio: **cmepdoc.com** (registrado en Porkbun, DNS en Cloudflare)
> Cuenta AWS: `114082792962`
> Ultima actualizacion: 2026-02-04

---

## Arquitectura

```
[Usuario]
    |
    ├── https://cmepdoc.com ──→ [CloudFront] ──→ [S3: cmep-archivos-frontend]
    |                                               (React SPA, Vite build)
    |
    └── https://api.cmepdoc.com ──→ [App Runner: cmep-backend-prod]
                                        |          (FastAPI, Python 3.12)
                                        |
                            ┌───────────┼───────────┐
                            |           |           |
                    [RDS MySQL 8]  [S3: cmep-   [Secrets
                     cmep_prod     archivos-    Manager]
                                   prod]
                            |
                    [Lambda: session-cleanup]
                    (EventBridge: cada 6h)
```

### Subdominios
| URL | Destino | Servicio AWS |
|-----|---------|--------------|
| `cmepdoc.com` | Frontend React SPA | CloudFront → S3 |
| `api.cmepdoc.com` | Backend FastAPI | App Runner (custom domain) |

### Stack Tecnico
- **Backend**: FastAPI + SQLAlchemy 2.0 async + Pydantic v2
- **Frontend**: React 18 + TypeScript + Vite
- **BD**: MySQL 8 (RDS) con asyncmy driver
- **Auth**: Sesiones server-side con cookie httpOnly (bcrypt)
- **Almacenamiento**: S3 via boto3 (FILE_STORAGE=s3)
- **DNS**: Cloudflare (nameservers: guss.ns.cloudflare.com, meiling.ns.cloudflare.com)

---

## Cambios de Codigo para Cloud (Fase 1)

Cambios realizados al codebase para soportar produccion AWS. Todos son condicionales — el sistema sigue funcionando en local sin cambios.

| Archivo | Cambio | Condicion |
|---------|--------|-----------|
| `backend/requirements.txt` | Agregado `boto3>=1.35.0` | Solo se importa si FILE_STORAGE=s3 |
| `backend/app/config.py` | Agregado `COOKIE_DOMAIN` (str), propiedad `is_prod` | Default vacio (sin efecto local) |
| `backend/app/services/file_storage.py` | S3Storage + routing local/s3 | FILE_STORAGE=local (default) mantiene comportamiento original |
| `backend/app/api/auth.py` | Cookie condicional: prod (secure, samesite=none) / local (lax) | Condicionado por APP_ENV |
| `backend/Dockerfile` | Removido `--reload` del CMD | Solo afecta build de produccion |
| `infra/lambda_cleanup.py` | Nuevo: limpia sesiones expiradas via pymysql | Archivo aislado, no interactua con el sistema |
| `backend/.env.example` | Nuevo: documenta todas las variables de entorno | Solo referencia |

### Detalle de file_storage.py
```python
# API publica (sin cambios):
save_file(file_bytes, storage_name) -> path
read_file(storage_path) -> bytes
delete_file(storage_path) -> None

# Routing interno:
FILE_STORAGE=local → _local_save/_local_read/_local_delete (filesystem)
FILE_STORAGE=s3    → _s3_save/_s3_read/_s3_delete (boto3, lazy import)
```

### Detalle de auth.py (cookies)
```
APP_ENV=local → secure=False, samesite=lax          (desarrollo)
APP_ENV=prod  → secure=True,  samesite=none, domain=COOKIE_DOMAIN (produccion)
```

---

## Infraestructura AWS (Completada)

### 1. Red (VPC)

| Recurso | Nombre/Valor |
|---------|-------------|
| VPC | `vpc-cmep-prod` (CIDR: 10.0.0.0/16, DNS Resolution + Hostnames: Enabled) |
| Internet Gateway | `igw-cmep-prod` |
| Subnet publica 1 | `subnet-cmep-public-1` (us-east-1a, 10.0.10.0/24, auto-assign public IP) |
| Subnet publica 2 | `subnet-cmep-public-2` (us-east-1b, 10.0.11.0/24, auto-assign public IP) |

### 2. Security Groups

**SG-RDS-CMEP** (Base de datos):
- Inbound: MySQL 3306 desde IPs admin autorizadas + SG-AppRunner-CMEP
- Outbound: All traffic

**SG-AppRunner-CMEP** (Backend):
- Inbound: Ninguno (App Runner maneja HTTP externo)
- Outbound: MySQL 3306 hacia SG-RDS-CMEP

### 3. RDS MySQL 8

| Config | Valor |
|--------|-------|
| Instancia | `db.t3.micro` |
| Storage | 20 GiB (gp3) |
| Engine | MySQL 8.0 |
| Deployment | Single-AZ |
| Public Access | Enabled (temporal, controlado por SG) |
| Encryption | AWS KMS |
| Backups automaticos | 7 dias |
| Actualizaciones menores | Automaticas |
| Database | `cmep_prod` (utf8mb4 / utf8mb4_unicode_ci) |
| Endpoint | `cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306` |

**Usuarios de base de datos:**

| Usuario | Uso | Permisos |
|---------|-----|----------|
| `admin` | Administracion, migraciones, seed, debug | Full (self-managed, acceso via MySQL Workbench/CLI con SSL) |
| `cmep_user` | Backend FastAPI (App Runner) | SELECT, INSERT, UPDATE, DELETE en `cmep_prod.*` |

**Seed de produccion ejecutado:**
- Script: `infra/seed_prod.py --password varas123`
- Admin: hvarasg@hotmail.com (Hector Varas, DNI 00000001, rol ADMIN)
- Servicio: Certificado Medico de Evaluacion Psicologica (PEN 200.00)
- Documentacion: `docs/deployment/seed_prod.md`

### 4. Storage (S3)

| Bucket | Uso | Acceso | Cifrado |
|--------|-----|--------|---------|
| `cmep-archivos-prod` | Documentos y adjuntos del backend | Privado (via IAM role) | SSE-S3 |
| `cmep-archivos-frontend` | Hosting frontend React SPA | Privado (via CloudFront OAC) | SSE-S3 |

### 5. Secrets Manager

Patron: 1 secret = 1 variable sensible (formato Plaintext)

| Secret | ARN | Variable |
|--------|-----|----------|
| `cmep-prod-DB_URL` | `arn:aws:secretsmanager:us-east-1:114082792962:secret:cmep-prod-DB_URL-ffJJOy` | DB_URL |
| `cmep-prod-SESSION_SECRET` | `arn:aws:secretsmanager:us-east-1:114082792962:secret:cmep-prod-SESSION_SECRET-QTBWAZ` | SESSION_SECRET |
| `cmep-prod-S3_BUCKET` | `arn:aws:secretsmanager:us-east-1:114082792962:secret:cmep-prod-S3_BUCKET-N9YRme` | S3_BUCKET |

Valores configurados:
```
DB_URL          = mysql+asyncmy://cmep_user:sistemaprado%23%232026@cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306/cmep_prod
SESSION_SECRET  = ddacb2405f8f8e9b46f8e7d642c83d16ef1f160cef6f3af0fe5d9d7a7e812509
S3_BUCKET       = cmep-archivos-prod
```

> Nota: La password del RDS contiene `##` — en URLs se codifica como `%23%23`.

### 6. IAM

**Rol: `cmep-apprunner-role`**
ARN: `arn:aws:iam::114082792962:role/cmep-apprunner-role`

| Policy | Permisos | Recurso |
|--------|----------|---------|
| S3 Access | GetObject, PutObject, DeleteObject | `arn:aws:s3:::cmep-archivos-prod/*` |
| Secrets Manager | GetSecretValue, DescribeSecret | `arn:aws:secretsmanager:us-east-1:114082792962:secret:cmep-prod-*` |
| KMS | Decrypt | `*` (para desencriptar secrets) |

Trust relationship: `tasks.apprunner.amazonaws.com`

> Importante: Este rol debe asignarse como **Instance Role** (no solo Access Role) en App Runner para que los secrets se inyecten al container en runtime.

### 7. ECR (Container Registry)

| Config | Valor |
|--------|-------|
| Repositorio | `cmep-backend` |
| URI | `114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend` |
| CLI User | `cmep-dev-cli` |

**Comandos de deploy:**
```bash
# Login ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 114082792962.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t cmep-backend ./backend

# Tag + Push
docker tag cmep-backend:latest 114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
docker push 114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
```

### 8. App Runner (Backend)

| Config | Valor |
|--------|-------|
| Servicio | `cmep-backend-prod` |
| Source | ECR `cmep-backend:latest` |
| CPU / RAM | 0.25 vCPU / 0.5 GB |
| Port | 8000 |
| Health Check | HTTP GET /health |
| VPC Connector | vpc-cmep-prod (subnet-public-1, subnet-public-2, SG-AppRunner-CMEP) |
| Instance Role | `cmep-apprunner-role` |
| URL interna AWS | `https://yt3mrtj2sd.us-east-1.awsapprunner.com` |
| Custom domain | `api.cmepdoc.com` |

**Variables de entorno (no sensibles):**

| Variable | Valor |
|----------|-------|
| APP_ENV | `prod` |
| APP_VERSION | `0.1.0` |
| FILE_STORAGE | `s3` |
| CORS_ORIGINS | `https://cmepdoc.com` |
| COOKIE_DOMAIN | `.cmepdoc.com` |

**Variables de entorno (secrets mapeados via ARN):**

| Variable | Secret ARN |
|----------|------------|
| DB_URL | `cmep-prod-DB_URL-ffJJOy` |
| SESSION_SECRET | `cmep-prod-SESSION_SECRET-QTBWAZ` |
| S3_BUCKET | `cmep-prod-S3_BUCKET-N9YRme` |

### 9. SSL Certificate (ACM)

| Config | Valor |
|--------|-------|
| Dominios | `cmepdoc.com`, `*.cmepdoc.com` (wildcard) |
| Validacion | DNS (CNAME en Cloudflare) |
| Estado | **Issued** |
| ARN | `arn:aws:acm:us-east-1:114082792962:certificate/04d15a6e-f6fb-40cf-98a3-e71718d06b64` |

> El wildcard `*.cmepdoc.com` cubre api.cmepdoc.com y cualquier subdominio futuro.

### 10. CloudFront (Frontend)

| Config | Valor |
|--------|-------|
| Origin | S3 `cmep-archivos-frontend` (OAC - Origin Access Control) |
| Default root object | `index.html` |
| Error pages | 403 → `/index.html` (200), 404 → `/index.html` (200) |
| SSL | ACM cert wildcard (seccion 9) |
| Alternate domain | `cmepdoc.com` |
| Domain CloudFront | `ds4yoqq6e4436.cloudfront.net` |
| Cache | CachingOptimized (assets), CachingDisabled (index.html) |

### 11. DNS (Cloudflare)

Nameservers: `guss.ns.cloudflare.com`, `meiling.ns.cloudflare.com`

| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | `@` (cmepdoc.com) | `ds4yoqq6e4436.cloudfront.net` | DNS only |
| CNAME | `www` | `cmepdoc.com` | Proxied |
| CNAME | `api` | `yt3mrtj2sd.us-east-1.awsapprunner.com` | DNS only |
| CNAME | `_c9bee95ec6624dcd01ca3cf7e5fa3acd` | `_f046bf3b06b1158154091b1fd6880d92.jkddzzz.acm-validations.aws` | DNS only |
| CNAME | `_155a147b83a81e9a0f6afa1c64060c8f.api` | `_dcb3dbe26fc4374eec4887d3f3568891.jkddzztszm.acm-validations.aws` | DNS only |
| CNAME | `_28ee1c5339711b6f553fc64d147db244.70i813jnk4pjjazccb4zqam3wlj3u00.api` | `_6533e44838801319b1e41a16680d4015.jkddzztszm.acm-validations.aws` | DNS only |

> Regla critica Cloudflare: Todos los registros de validacion (`_xxx`) deben estar en **DNS only** (nube gris), nunca proxied.
> Los nombres en Cloudflare se ingresan SIN `.cmepdoc.com` — Cloudflare lo agrega automaticamente.

### 12. Frontend Deploy

**Build:**
```bash
cd frontend
$env:VITE_API_URL="https://api.cmepdoc.com"
npm run build
```

**Upload a S3:**
```bash
aws s3 sync dist/ s3://cmep-archivos-frontend/ --delete
```

**Invalidar cache CloudFront (despues de cada deploy):**
```bash
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```

---

## Pendientes

### Verificar CORS y Cookies
- [X] Variables App Runner: CORS_ORIGINS=https://cmepdoc.com, COOKIE_DOMAIN=.cmepdoc.com
- [ ] Test login desde `https://cmepdoc.com`:
  - DevTools > Application > Cookies
  - Cookie `cmep_session`: Secure=true, SameSite=None, Domain=`.cmepdoc.com`
- [ ] Si falla login: revisar CORS_ORIGINS y COOKIE_DOMAIN en App Runner

### Smoke Test Completo
- [ ] Login con admin (hvarasg@hotmail.com / varas123)
- [ ] Crear usuarios reales via `/app/usuarios` (operador, gestor, medico)
- [ ] Crear solicitud nueva
- [ ] Flujo: REGISTRADO → ASIGNAR_GESTOR → REGISTRAR_PAGO → ASIGNAR_MEDICO → CERRAR
- [ ] Upload y download de archivo
- [ ] Reportes admin (graficos cargan)
- [ ] Cancelar solicitud de prueba
- [ ] Override como admin
- [ ] Test responsive (movil)

### CloudWatch Alarmas
- [ ] Alarma: RDS CPU > 80% por 5 minutos
- [ ] Alarma: App Runner 5xx > 5 en 5 minutos
- [ ] Alarma: RDS storage libre < 2 GB
- [ ] Configurar notificacion SNS (email de alerta)

### Lambda Session Cleanup
- [ ] Crear funcion Lambda:
  - Nombre: `cmep-session-cleanup`
  - Runtime: Python 3.12
  - Codigo: subir `infra/lambda_cleanup.py`
  - VPC: `vpc-cmep-prod` (mismas subnets y SG con acceso a 3306)
  - Env vars: DB_HOST, DB_USER, DB_PASS, DB_NAME
  - Timeout: 30 seg
- [ ] Crear EventBridge rule:
  - Schedule: `rate(6 hours)`
  - Target: Lambda `cmep-session-cleanup`
- [ ] Test manual: invocar Lambda desde consola AWS y verificar log

---

## Problemas Resueltos

### P1: DB_URL no llegaba al container (RESUELTO)
- **Sintoma**: Logs mostraban `SQLite: tablas creadas en sqlite+aiosqlite:////cmep_dev.db`
- Invoke-RestMethod -Uri "https://yt3mrtj2sd.us-east-1.awsapprunner.com/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"hvarasg@hotmail.com","password":"varas123"}' con esto se valido que si funciona


### P2: Custom domain api.cmepdoc.com sin SSL (RESUELTO)
- **Sintoma**: `NET::ERR_CERT_COMMON_NAME_INVALID` al acceder a `https://api.cmepdoc.com`
- **Causa**: Faltaban los 2 CNAMEs de validacion de App Runner custom domain en Cloudflare
- **Solucion**: Agregar ambos CNAMEs de validacion (ver seccion DNS) en modo DNS only
- **Diagnostico usado**: nslookup contra 8.8.8.8 para verificar propagacion publica
- **Verificacion**: App Runner custom domain status → Active, `https://api.cmepdoc.com/health` responde OK

---

## Costos Estimados (Mensual)

| Servicio | Config | Costo estimado |
|----------|--------|----------------|
| RDS MySQL | db.t3.micro (free tier 12 meses) | $0 - $15 |
| App Runner | 0.25 vCPU, 0.5 GB | $5 - $15 |
| S3 (archivos + frontend) | < 1 GB total | < $1 |
| CloudFront | < 10 GB transfer | $0 - $2 |
| Secrets Manager | 3 secrets | ~$1.20 |
| CloudWatch | Logs basicos | $0 - $5 |
| Lambda | < 1000 invocaciones/mes | $0 |
| Dominio | cmepdoc.com (Porkbun) | ~$1/mes ($11/anio) |
| **Total estimado** | | **$8 - $40/mes** |

---

## Operaciones Recurrentes

### Redesplegar backend (cambios de codigo)
```bash
# 1. Build y push imagen
docker build -t cmep-backend ./backend
docker tag cmep-backend:latest 114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
docker push 114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest

# 2. App Runner detecta nueva imagen y redespliega automaticamente (si auto-deploy esta ON)
#    Si no, ir a App Runner > Deploy
```

### Redesplegar frontend (cambios de UI)
```bash
# 1. Build
cd frontend
$env:VITE_API_URL="https://api.cmepdoc.com"
npm run build

# 2. Upload
aws s3 sync dist/ s3://cmep-archivos-frontend/ --delete

# 3. Invalidar cache
aws cloudfront create-invalidation --distribution-id E2QYC21NF9GJUY --paths "/*"

aws cloudfront create-invalidation --distribution-id E2QYC21NF9GJUY --paths "/index.html" "/assets/*"

```

### Verificar estado del sistema
```bash
# Health check
curl https://api.cmepdoc.com/health
# Esperado: {"ok":true,"status":"healthy"}

# Version
curl https://api.cmepdoc.com/version
# Esperado: {"ok":true,"version":"0.1.0"}
```

### Ver logs del backend
AWS Console > App Runner > cmep-backend-prod > Logs > Application logs

### Diagnosticar DNS
```powershell
nslookup -type=CNAME api.cmepdoc.com 8.8.8.8
nslookup -type=CNAME cmepdoc.com 8.8.8.8
```
