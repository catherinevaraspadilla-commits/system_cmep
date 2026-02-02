# CMEP — Arquitectura Tecnica Final

## 1. Vista general

```
+-------------------+       +---------------------+       +----------------+
|                   |       |                     |       |                |
|  CloudFront/CDN   +------>+  S3 (frontend)      |       |  S3 (archivos) |
|  (HTTPS + SPA)    |       |  build estatico     |       |  bucket priv.  |
|                   |       |                     |       |                |
+-------------------+       +---------------------+       +-------+--------+
                                                                  ^
                                                                  |
+-------------------+       +---------------------+       +-------+--------+
|                   |       |                     |       |                |
|  Browser          +------>+  App Runner         +------>+  RDS MySQL 8   |
|  (React SPA)      | API   |  (FastAPI backend)  | SQL   |  (transaccional)|
|                   |       |                     |       |                |
+-------------------+       +----------+----------+       +----------------+
                                       |
                                       v
                            +---------------------+
                            | Secrets Manager     |
                            | CloudWatch (logs)   |
                            | EventBridge+Lambda  |
                            +---------------------+
```

## 2. Componentes principales

### 2.1 Frontend (React SPA)

- **Framework:** React con routing client-side
- **Estrategia:** mobile-first responsive, sin PWA en V1
- **Hosting:** S3 + CloudFront (prod), dev server local (dev)
- **Rutas publicas:** `/`, `/login`
- **Rutas privadas:** `/app/*` (requieren sesion valida via `GET /auth/me`)
- **Regla critica:** el frontend NO calcula permisos. Renderiza botones basandose exclusivamente en `acciones_permitidas` retornadas por el backend.

### 2.2 Backend (FastAPI)

- **Framework:** Python FastAPI
- **Responsabilidades:**
  - Autenticacion y gestion de sesiones
  - Calculo del estado operativo derivado
  - Evaluacion de POLICY (autorizacion)
  - Ejecucion transaccional de acciones de negocio
  - Auditoria obligatoria
  - Gestion de archivos (upload/download)
- **Sesiones:** server-side, almacenadas en MySQL, cookie segura httpOnly
- **Migraciones:** Alembic desde dia 1

### 2.3 Base de datos (MySQL 8)

- **Motor:** MySQL 8 (RDS en prod, Docker en dev)
- **Modelo:** 17+ tablas (personas, clientes, empleados, users, solicitudes, asignaciones, pagos, archivos, historial, etc.)
- **Convenciones:**
  - Auditoria en todas las tablas: `created_by`, `updated_by`, `created_at`, `updated_at`
  - FK con `ON UPDATE RESTRICT`, `ON DELETE RESTRICT`
  - ENUMs definidos en el glosario (doc 01)
  - Estado operativo NO almacenado en BD

### 2.4 Storage de archivos

- **Dev:** filesystem local o MinIO (emulacion S3)
- **Prod:** Amazon S3, bucket privado
- **Acceso:** URLs firmadas con vencimiento, generadas por backend
- **Metadata:** tabla `archivos` + tabla pivot `solicitud_archivo`

## 3. Modelo de seguridad

### 3.1 Autenticacion

```
POST /auth/login  -->  valida credenciales  -->  crea sesion en BD  -->  set-cookie httpOnly
GET  /auth/me     -->  valida cookie        -->  retorna user + roles + permisos
POST /auth/logout -->  invalida sesion      -->  elimina cookie
```

- Password almacenado como hash (bcrypt)
- Email normalizado: `lower(trim(email))`
- Usuario SUSPENDIDO: login rechazado, sesiones existentes invalidadas
- Token de reset: hash almacenado, con expiracion y uso unico

### 3.2 Autorizacion (POLICY)

La autorizacion se evalua con la formula:

```
POLICY[rol_usuario][estado_operativo_derivado] => lista de acciones_permitidas
```

- La POLICY es un diccionario estatico definido en el backend (doc 05)
- Se evalua en cada request de accion
- El frontend recibe `acciones_permitidas` en `GET /solicitudes/{id}` y solo renderiza botones correspondientes

### 3.3 Estado operativo derivado

Se calcula en runtime con orden de precedencia estricto:

```
1. CANCELADO    — estado_atencion = 'CANCELADO'
2. CERRADO      — estado_atencion = 'ATENDIDO'
3. ASIGNADO_MEDICO — estado_pago = 'PAGADO' AND asignacion vigente MEDICO
4. PAGADO       — estado_pago = 'PAGADO'
5. ASIGNADO_GESTOR — asignacion vigente GESTOR
6. REGISTRADO   — ninguna condicion anterior
```

El primer match gana. No se almacena en BD.

## 4. Estructura de repositorio

```
CMEP_APP/
  backend/
    app/
      main.py              # FastAPI app, CORS, lifespan
      config.py            # Settings via env vars
      database.py          # SQLAlchemy engine + session
      models/              # ORM models (1 archivo por tabla o grupo)
      schemas/             # Pydantic request/response DTOs
      api/
        auth.py            # /auth/login, /auth/logout, /auth/me
        solicitudes.py     # CRUD + acciones workflow
        archivos.py        # upload/download
        admin.py           # CRUD usuarios
      services/
        auth_service.py    # logica de autenticacion
        policy.py          # POLICY dict + assert_allowed()
        estado_operativo.py # derivar_estado_operativo()
        solicitud_service.py
        archivo_service.py
        admin_service.py
      middleware/
        session_middleware.py
      utils/
        hashing.py         # bcrypt helpers
        audit.py           # registrar historial
    migrations/            # Alembic
    tests/
      unit/
      integration/
    requirements.txt
    Dockerfile
  frontend/
    src/
      pages/
        Landing.tsx
        Login.tsx
        app/
          Inicio.tsx
          Solicitudes.tsx
          SolicitudNueva.tsx
          SolicitudDetalle.tsx
          Usuarios.tsx
      components/
      hooks/
      services/            # API client
      types/               # DTOs typescript
    public/
    package.json
    Dockerfile
  infra/
    docker-compose.yml
    docker-compose.test.yml
    init-db/               # scripts SQL iniciales
    seed_dev.py            # datos de prueba
  docs/
    source/                # 8 docs de especificacion (fuente de verdad)
    claude/                # documentacion operativa generada
  .env.example
  .gitignore
```

## 5. Flujo de datos principal

### Request autenticado tipico

```
Browser --> CloudFront --> App Runner (FastAPI)
                              |
                              +--> middleware: validar sesion (cookie -> sessions table)
                              |
                              +--> resolver usuario, roles, permisos
                              |
                              +--> ejecutar logica de negocio
                              |      +--> derivar estado_operativo
                              |      +--> evaluar POLICY
                              |      +--> ejecutar accion en transaccion
                              |      +--> registrar auditoria
                              |
                              +--> retornar JSON estandar {ok, data, meta}
```

### Formato de respuesta estandar

**Exito:**
```json
{ "ok": true, "data": { ... }, "meta": { ... } }
```

**Error:**
```json
{ "ok": false, "error": { "code": "FORBIDDEN|NOT_FOUND|CONFLICT|VALIDATION_ERROR", "message": "...", "details": { ... } } }
```

## 6. Configuracion por entorno

| Variable | Dev | Test | Prod |
|----------|-----|------|------|
| DB_HOST | localhost / docker | docker | RDS endpoint |
| DB_PORT | 3306 | 3306 | 3306 |
| DB_NAME | cmep_dev | cmep_test | cmep_prod |
| SESSION_SECRET | dev-secret | test-secret | Secrets Manager |
| CORS_ORIGINS | http://localhost:3000 | http://localhost:3000 | https://dominio.com |
| S3_BUCKET | (no usado) | (no usado) | cmep-archivos |
| FILE_STORAGE | local | local | s3 |
| APP_ENV | local | test | prod |

## 7. Decisiones de diseno

| Decision | Justificacion |
|----------|---------------|
| Sesiones server-side (no JWT) | Control total de invalidacion; usuario suspendido pierde acceso inmediato |
| Estado operativo derivado (no almacenado) | Evita inconsistencias; una sola fuente de verdad calculada |
| POLICY como diccionario estatico | Simple, auditable, testeable; no requiere BD para permisos |
| Alembic desde dia 1 | Migraciones reproducibles en dev, test y prod |
| FastAPI + Pydantic | Validacion automatica, docs OpenAPI, async-ready |
| React SPA | Una sola app, routing client-side, build estatico para S3 |
| Mobile-first sin PWA | Menor complejidad MVP; arquitectura preparada para PWA futuro |
| FK RESTRICT (no CASCADE) | Prevenir eliminaciones accidentales en MVP |
