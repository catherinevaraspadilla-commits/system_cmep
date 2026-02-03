# M8 — Tracking de Despliegue AWS

> Ultima actualizacion: 2026-02-03
> Region: us-east-1 (N. Virginia)
> Arquitectura: Subdomain (cmep.dominio.com + api.cmep.dominio.com)

---

## Resumen de Arquitectura

```
[Usuario] → https://cmep.dominio.com → [CloudFront] → [S3 Frontend]
[Usuario] → https://api.cmep.dominio.com → [App Runner] → [FastAPI]
                                                  |
                                    [RDS MySQL 8] + [S3 Archivos]
                                    [Secrets Manager] + [CloudWatch]
```

---

## FASE 1: Preparacion del Codigo (Claude)

| # | Tarea | Archivo | Estado |
|---|-------|---------|--------|
| 1.1 | Agregar boto3 a dependencias | `backend/requirements.txt` | [x] Completado |
| 1.2 | Agregar COOKIE_DOMAIN a config | `backend/app/config.py` | [x] Completado |
| 1.3 | S3Storage + routing local/s3 | `backend/app/services/file_storage.py` | [x] Completado |
| 1.4 | Cookie condicional prod/local | `backend/app/api/auth.py` | [x] Completado |
| 1.5 | Quitar --reload del Dockerfile | `backend/Dockerfile` | [x] Completado |
| 1.6 | Lambda limpieza sesiones | `infra/lambda_cleanup.py` | [x] Completado |
| 1.7 | Documentar variables de entorno | `backend/.env.example` | [x] Completado |
| 1.8 | Crear este tracking | `docs/deployment/M8_tracking_deploy.md` | [x] Completado |
| 1.9 | Verificar tests (117 pasan) | - | [ ] Pendiente |

### Que cambio en el codigo (resumen)

**file_storage.py**: Ahora soporta `FILE_STORAGE=local` (default, igual que antes) y `FILE_STORAGE=s3` (usa boto3). Import de boto3 es lazy — solo se carga si se usa S3. La API publica (`save_file`, `read_file`, `delete_file`) no cambio.

**auth.py**: Cookie ahora es condicional:
- `APP_ENV=local` → `secure=False, samesite=lax` (igual que antes)
- `APP_ENV=prod` → `secure=True, samesite=none, domain=COOKIE_DOMAIN`

**config.py**: Nuevos settings `COOKIE_DOMAIN` (str, default vacio) y propiedad `is_prod`.

**Dockerfile**: Removido `--reload` (flag de desarrollo).

---

## FASE 2: Infraestructura AWS

### 2.0 Prerequisitos y cuenta
- [x] Cuenta AWS activa
- [x] Billing alerts configurados
- [x] Region: us-east-1

### 2.1 Red (VPC)
- [x] VPC: default-vpc-094b487cd8aee9831
- [x] Subnets privadas en us-east-1a y us-east-1b

### 2.2 Security Groups
- [x] SG-RDS-CMEP: inbound 3306 desde SG-AppRunner-CMEP
- [x] SG-AppRunner-CMEP: outbound 3306 hacia SG-RDS-CMEP

### 2.3 RDS MySQL 8
- [x] Instancia: db.t3.micro, 20GB gp2/gp3, MySQL 8.x
- [x] Database: `cmep_prod`
- [x] Single-AZ, sin acceso publico
- [x] Backups automaticos: 7 dias
- [x] Cifrado: AWS managed KMS
- [x] Master user: `admin` (self-managed, no Secrets Manager)
- [ ] **Crear usuario limitado `cmep_user`** con permisos minimos
  ```sql
  CREATE USER 'cmep_user'@'%' IDENTIFIED BY '<password-seguro>';
  GRANT SELECT, INSERT, UPDATE, DELETE ON cmep_prod.* TO 'cmep_user'@'%';
  FLUSH PRIVILEGES;
  ```

### 2.4 S3 Buckets
- [x] `cmep-archivos-prod` (privado, SSE-S3, sin versioning)
- [x] `cmep-frontend-prod` (privado, SSE-S3, sin versioning)

### 2.5 Secrets Manager
- [x] Secret: `cmep-prod-secrets`
- [ ] **Configurar valores del secreto**:
  ```json
  {
    "DB_URL": "mysql+asyncmy://cmep_user:<password>@<rds-endpoint>:3306/cmep_prod",
    "SESSION_SECRET": "<generar: python -c 'import secrets; print(secrets.token_hex(32))'>",
    "S3_BUCKET": "cmep-archivos-prod"
  }
  ```

### 2.6 IAM
- [ ] Crear rol `cmep-apprunner-role`:
  - S3: read/write en `cmep-archivos-prod`
  - Secrets Manager: read en `cmep-prod-secrets`
  - VPC: network access para conectar a RDS

### 2.7 ECR + Docker
- [ ] Crear repositorio ECR: `cmep-backend`
- [ ] Build y push imagen:
  ```bash
  cd backend
  docker build -t cmep-backend .
  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
  docker tag cmep-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
  docker push <account>.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
  ```

### 2.8 App Runner
- [ ] Crear servicio desde ECR
- [ ] Config: 0.25 vCPU, 0.5GB RAM, port 8000
- [ ] Health check: HTTP GET /health
- [ ] Variables de entorno:
  ```
  APP_ENV=prod
  FILE_STORAGE=s3
  CORS_ORIGINS=https://cmep.<dominio>
  COOKIE_DOMAIN=.<dominio>
  ```
- [ ] Secrets desde Secrets Manager: DB_URL, SESSION_SECRET, S3_BUCKET
- [ ] VPC connector: para acceder a RDS via SG-AppRunner-CMEP
- [ ] Anotar URL: ________________

### 2.9 Seed de produccion
- [ ] Conectar a RDS (bastion, Cloud9, o SSH tunnel)
- [ ] Crear tablas + seed:
  ```bash
  DB_URL="mysql+asyncmy://cmep_user:<pass>@<rds-endpoint>:3306/cmep_prod" python infra/seed_dev.py --mysql
  ```
- [ ] Verificar: GET /health retorna `{"ok": true}`

---

## FASE 3: Deploy Frontend

### 3.0 Dominio (Prerequisito)
- [ ] Registrar dominio (Route 53 ~$12/anio, o proveedor externo)
- [ ] Dominio elegido: ________________

### 3.1 Build
- [ ] Build frontend:
  ```bash
  cd frontend
  VITE_API_URL=https://api.cmep.<dominio> npm run build
  ```
- [ ] Verificar que `dist/` se genera correctamente

### 3.2 Upload a S3
- [ ] Subir build:
  ```bash
  aws s3 sync dist/ s3://cmep-frontend-prod/ --delete
  ```

### 3.3 CloudFront
- [ ] Crear distribucion:
  - Origin: S3 `cmep-frontend-prod` (OAC)
  - Default root object: `index.html`
  - Error pages: 403 → `/index.html` (200), 404 → `/index.html` (200)
- [ ] Cache: assets con cache largo, index.html sin cache

### 3.4 SSL + DNS
- [ ] Solicitar certificado ACM (us-east-1) para:
  - `cmep.<dominio>`
  - `api.cmep.<dominio>`
- [ ] DNS records:
  - `cmep.<dominio>` → CloudFront distribution
  - `api.cmep.<dominio>` → App Runner URL (CNAME)
- [ ] Esperar validacion SSL (puede tomar minutos)

### 3.5 Invalidar cache
- [ ] Primer deploy:
  ```bash
  aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
  ```

---

## FASE 4: CORS y Cookies

### 4.1 Configuracion (ya preparada en Fase 1)
- [ ] Verificar env vars en App Runner:
  - `CORS_ORIGINS=https://cmep.<dominio>`
  - `COOKIE_DOMAIN=.<dominio>`
  - `APP_ENV=prod`

### 4.2 Test de login
- [ ] Abrir `https://cmep.<dominio>`
- [ ] Login con `admin@cmep.local / admin123`
- [ ] DevTools > Application > Cookies:
  - `cmep_session` debe existir
  - `Secure`: true
  - `SameSite`: None
  - `Domain`: `.<dominio>`
- [ ] Si falla: revisar CORS_ORIGINS y COOKIE_DOMAIN

---

## FASE 5: Monitoreo

- [ ] CloudWatch: verificar logs de App Runner aparecen
- [ ] Crear alarma: 5xx errors > 5 en 5 minutos
- [ ] Lambda `cmep-session-cleanup`:
  - Codigo: `infra/lambda_cleanup.py`
  - Runtime: Python 3.12
  - VPC: misma que RDS, SG con acceso a 3306
  - Env vars: DB_HOST, DB_USER, DB_PASS, DB_NAME
- [ ] EventBridge rule: cada 6 horas → trigger Lambda
- [ ] Verificar backups RDS activos (7 dias)

---

## FASE 6: Smoke Test Produccion

### Login y roles
- [ ] Login como admin (admin@cmep.local / admin123)
- [ ] Login como operador (operador@cmep.local / operador123)
- [ ] Login como gestor (gestor@cmep.local / gestor123)
- [ ] Login como medico (medico@cmep.local / medico123)

### Flujo completo de solicitud
- [ ] Crear solicitud nueva
- [ ] Asignar gestor → estado: ASIGNADO_GESTOR
- [ ] Registrar pago → estado: PAGADO
- [ ] Asignar medico → estado: ASIGNADO_MEDICO
- [ ] Cerrar solicitud → estado: CERRADO

### Funcionalidades
- [ ] Upload de archivo (evidencia de pago)
- [ ] Download del archivo subido
- [ ] Reportes admin cargan correctamente (graficos, KPIs)
- [ ] Cancelar una solicitud de prueba
- [ ] Override como admin en solicitud cerrada
- [ ] Verificar responsive en movil

---

## Costos Estimados (Mensual)

| Servicio | Config | Costo |
|----------|--------|-------|
| RDS MySQL | db.t3.micro (free tier 12m) | $0-$15 |
| App Runner | 0.25 vCPU, 0.5GB | $5-$15 |
| S3 (archivos + frontend) | < 1 GB total | < $1 |
| CloudFront | < 10 GB transfer | $0-$2 |
| Secrets Manager | 1 secreto | $0.40 |
| CloudWatch | Logs basicos | $0-$5 |
| Lambda | < 1000 invocaciones/mes | $0 |
| **Total** | | **$7-$40/mes** |

---

## Notas y Decisiones

- RDS master credentials son self-managed (no Secrets Manager)
- Solo `cmep_user` (app) va en Secrets Manager
- Routing por subdomain: `cmep.dominio` (frontend), `api.cmep.dominio` (backend)
- Cookie: `SameSite=None, Secure=true` para cross-subdomain
- S3 archivos: key prefix `uploads/` para organizacion
- App Runner sin --reload (produccion)
