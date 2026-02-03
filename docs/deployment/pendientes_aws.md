# CMEP — Pendientes AWS

> Basado en infraestructura ya creada en `info.md`
> Actualizado: 2026-02-03

---

## Infraestructura YA completada

| Recurso | Detalle | Estado |
|---------|---------|--------|
| VPC | `vpc-cmep-prod` (10.0.0.0/16) | Listo |
| Internet Gateway | `igw-cmep-prod` | Listo |
| Subnets publicas | us-east-1a (10.0.10.0/24), us-east-1b (10.0.11.0/24) | Listo |
| SG-RDS-CMEP | Inbound 3306 desde SG-AppRunner + IPs admin | Listo |
| SG-AppRunner-CMEP | Outbound 3306 hacia SG-RDS | Listo |
| RDS MySQL 8 | db.t3.micro, 20GB, `cmep_prod`, cifrado KMS | Listo |
| Endpoint RDS | `cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306` | Listo |
| Usuario `cmep_user` | SELECT, INSERT, UPDATE, DELETE en cmep_prod.* | Listo |
| S3 archivos | `cmep-archivos-prod` (privado, SSE-S3) | Listo |
| S3 frontend | `cmep-frontend-prod` (publico, SSE-S3) | Listo |
| Secrets Manager | `cmep-prod-secrets` (DB_URL, DB_USER, DB_PASSWORD, SESSION_SECRET, S3_BUCKET) | Listo |

---

## Pendientes

### 1. IAM Role para App Runner

Crear rol `cmep-apprunner-role` con estas policies:

**S3 Access** (inline policy):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::cmep-archivos-prod/*"
    }
  ]
}
```

**Secrets Manager Access** (inline policy):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:cmep-prod-secrets*"
    }
  ]
}
```

**Trust relationship** (para App Runner):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "tasks.apprunner.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

- [ ] Crear rol en IAM
- [ ] Adjuntar policies
- [ ] Anotar ARN del rol: ________________

---

### 2. ECR + Docker Image

- [ ] Crear repositorio ECR: `cmep-backend`

```bash
aws ecr create-repository --repository-name cmep-backend --region us-east-1
```

- [ ] Build de la imagen (desde raiz del proyecto):

```bash
docker build -t cmep-backend ./backend
```

- [ ] Login, tag y push:

```bash
# Reemplazar <ACCOUNT_ID> con tu AWS Account ID
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker tag cmep-backend:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest

docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
```

- [ ] Verificar imagen en consola ECR

---

### 3. VPC Connector para App Runner

App Runner necesita un VPC connector para llegar a RDS (que esta en la VPC).

- [ ] Crear VPC Connector en App Runner:
  - VPC: `vpc-cmep-prod`
  - Subnets: `subnet-cmep-public-1`, `subnet-cmep-public-2`
  - Security Group: `SG-AppRunner-CMEP`
- [ ] Anotar nombre: ________________

---

### 4. App Runner Service

- [ ] Crear servicio App Runner:
  - **Source**: ECR (`cmep-backend:latest`)
  - **Port**: 8000
  - **CPU**: 0.25 vCPU
  - **Memory**: 0.5 GB
  - **Instance role**: `cmep-apprunner-role`
  - **VPC Connector**: el creado en paso 3
  - **Health check**: HTTP GET `/health`

- [ ] Variables de entorno (plaintext):
  ```
  APP_ENV=prod
  APP_VERSION=0.1.0
  FILE_STORAGE=s3
  CORS_ORIGINS=https://cmep.<dominio>
  COOKIE_DOMAIN=.<dominio>
  ```

- [ ] Variables de entorno (desde Secrets Manager):
  - Mapear `cmep-prod-secrets` → DB_URL, SESSION_SECRET, S3_BUCKET

  **Nota**: App Runner puede leer secrets si el instance role tiene permiso.
  Alternativa: pasar como env vars en la config del servicio.

- [ ] Esperar que el servicio este `Running`
- [ ] Verificar: `curl https://<apprunner-url>/health` → `{"ok": true}`
- [ ] Anotar URL de App Runner: ________________

---

### 5. Seed de Base de Datos Produccion

Antes de probar el backend, necesitas datos iniciales.

- [ ] Conectar a RDS (MySQL Workbench, CLI, o tunnel SSH):
  ```
  Host: cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com
  Port: 3306
  User: admin
  ```

- [ ] Ejecutar seed (desde una maquina con acceso a RDS):
  ```bash
  DB_URL="mysql+asyncmy://cmep_user:<password>@cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306/cmep_prod" python infra/seed_dev.py --mysql
  ```

- [ ] Verificar: `GET /health` y `GET /version` responden

---

### 6. Dominio

- [ ] Registrar dominio (opciones):
  - Route 53 (~$12/anio, integrado con AWS)
  - Externo (Namecheap, Cloudflare, GoDaddy)
- [ ] Dominio elegido: ________________
- [ ] Subdomains planeados:
  - `cmep.<dominio>` → frontend (CloudFront)
  - `api.cmep.<dominio>` → backend (App Runner)

---

### 7. SSL Certificate (ACM)

- [ ] Solicitar certificado en ACM (**region us-east-1**, requerido por CloudFront):
  - Domain: `cmep.<dominio>`
  - Additional names: `api.cmep.<dominio>`
- [ ] Validar via DNS (agregar CNAME que ACM indica)
- [ ] Esperar status: `Issued`
- [ ] Anotar ARN del certificado: ________________

---

### 8. Frontend Build + Upload

- [ ] Build frontend:
  ```bash
  cd frontend
  VITE_API_URL=https://api.cmep.<dominio> npm run build
  ```

- [ ] Upload a S3:
  ```bash
  aws s3 sync dist/ s3://cmep-frontend-prod/ --delete
  ```

- [ ] Verificar archivos en S3 (index.html, assets/)

---

### 9. CloudFront Distribution

- [ ] Crear distribucion:
  - **Origin**: S3 `cmep-frontend-prod`
  - **Origin Access**: OAC (Origin Access Control)
  - **Default root object**: `index.html`
  - **Error pages**: 403→`/index.html` (200), 404→`/index.html` (200)
  - **SSL certificate**: el creado en paso 7
  - **Alternate domain**: `cmep.<dominio>`
  - **Cache policy**: `CachingOptimized` (assets), `CachingDisabled` (index.html)

- [ ] Actualizar bucket policy de S3 para permitir acceso desde CloudFront OAC
- [ ] Anotar domain de CloudFront: ________________

---

### 10. DNS Records

- [ ] `cmep.<dominio>` → CloudFront distribution (CNAME o Alias si Route 53)
- [ ] `api.cmep.<dominio>` → App Runner URL (CNAME)
- [ ] Esperar propagacion DNS
- [ ] Verificar: `https://cmep.<dominio>` carga el frontend
- [ ] Verificar: `https://api.cmep.<dominio>/health` responde

---

### 11. Verificar CORS y Cookies

- [ ] Actualizar App Runner env vars si falta:
  - `CORS_ORIGINS=https://cmep.<dominio>`
  - `COOKIE_DOMAIN=.<dominio>`
- [ ] Test login desde `https://cmep.<dominio>`:
  - DevTools > Application > Cookies
  - Cookie `cmep_session`: Secure=true, SameSite=None, Domain=`.<dominio>`
- [ ] Si falla login: revisar CORS y COOKIE_DOMAIN

---

### 12. CloudWatch Alarmas

- [ ] Alarma: RDS CPU > 80% por 5 minutos
- [ ] Alarma: App Runner 5xx > 5 en 5 minutos
- [ ] Alarma: RDS storage libre < 2 GB
- [ ] Configurar notificacion SNS (email)

---

### 13. Lambda Session Cleanup

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

- [ ] Test manual: invocar Lambda desde consola y verificar log

---

### 14. Smoke Test Completo

- [ ] Login con admin (admin@cmep.local / admin123)
- [ ] Login con operador, gestor, medico
- [ ] Crear solicitud nueva
- [ ] Flujo: REGISTRADO → ASIGNAR_GESTOR → REGISTRAR_PAGO → ASIGNAR_MEDICO → CERRAR
- [ ] Upload y download de archivo
- [ ] Reportes admin (graficos cargan)
- [ ] Cancelar solicitud de prueba
- [ ] Override como admin
- [ ] Test responsive (movil)

---

## Orden sugerido de ejecucion

```
1. IAM Role            ← no depende de nada
2. ECR + Docker        ← no depende de nada
3. VPC Connector       ← necesita VPC + subnets (ya listo)
4. App Runner          ← necesita ECR + IAM + VPC Connector
5. Seed BD             ← necesita App Runner corriendo (o acceso directo a RDS)
6. Dominio             ← independiente, hacerlo en paralelo
7. SSL (ACM)           ← necesita dominio
8. Frontend build      ← necesita URL del API (App Runner)
9. CloudFront          ← necesita S3 + SSL
10. DNS                ← necesita CloudFront + App Runner URLs
11. CORS/Cookies       ← necesita todo lo anterior
12. CloudWatch         ← post-deploy
13. Lambda cleanup     ← post-deploy
14. Smoke test         ← al final
```
