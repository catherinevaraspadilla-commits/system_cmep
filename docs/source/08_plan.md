# CMEP — Plan de Desarrollo por Módulos (con Tasks + Tests + Setup)

Este es un **approach para que Claude Code** pueda avanzar “por módulos”, con **tests locales**, y con un **orden de setup** que evita bloqueos (DB / sesiones / CORS / deploy).

---

## 0) Principios del Approach (para no romperte después)
1. **Primero “esqueleto” ejecutable end-to-end**: backend levanta + frontend levanta + DB levanta + healthcheck.
2. **Luego módulos** en orden que desbloquean a otros: Auth/Sesión → Solicitudes → Workflow (POLICY) → Archivos → Admin.
3. **Cada módulo debe traer**:
   - contrato (endpoints / inputs / outputs)
   - modelo BD (tablas/índices mínimos)
   - tests (unit + integración)
   - “smoke flow” manual (pasos rápidos para probar)
4. **Siempre con seeds + fixtures**: sin data de prueba, el desarrollo se frena.

---

## 1) Setup mínimo (orden recomendado)
### 1.1 Repo / estructura
- `/backend` (FastAPI)
- `/frontend` (React PWA)
- `/docs` (tus 7 docs)
- `/infra` (docker-compose, scripts)
- `/tests` (si prefieres separado, o dentro de backend)

### 1.2 Variables de entorno
- `.env.local` (dev)
- `.env.test` (test)
- `.env.prod` (aws)
Variables mínimas:
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
- SESSION_SECRET
- CORS_ORIGINS (frontend local)
- S3_BUCKET (cuando toque archivos)
- APP_ENV (local/test/prod)

### 1.3 Base de datos (ANTES del backend funcional)
**Sí: DB primero**, pero solo lo mínimo para que Auth y Solicitudes existan.

Recomendación práctica:
- usar **migraciones** (Alembic) desde el día 1
- tener un script `seed_dev.sql` o `seed_dev.py`

### 1.4 Docker compose (para que sea “1 comando y corre”)
Servicios:
- mysql
- backend
- frontend (opcional en compose, pero ideal)
- (más adelante) minio (si quieres simular S3 local)

### 1.5 Checks mínimos
- `GET /health`
- `GET /version`
- frontend muestra “OK conectado” leyendo `/health`

---

## 2) Plan por Módulos (orden que desbloquea)
### M0 — Bootstrap End-to-End (día 1)
**Objetivo:** correr todo local.
- Backend: FastAPI con `/health`
- Frontend: pantalla simple + fetch `/health`
- DB: MySQL arriba (aunque aún sin tablas finales)

**Salida esperada:** “levanta y responde”.

---

### M1 — Auth + Sesión (bloque base)
**Por qué primero:** sin sesión, todo lo privado se rompe.

Incluye:
- Login (email+password)
- Sesión persistida (cookie o header; según tu doc de sesiones)
- Middleware: “cada request privado valida session y permisos básicos”
- Logout

Tests:
- unit: hash/verify password
- integración: login crea sesión; endpoint privado rechaza sin sesión

Smoke flow:
1) login
2) llamar `/me`
3) logout
4) volver a llamar `/me` debe fallar

---

### M2 — Modelo core “Solicitud” + CRUD mínimo
**Objetivo:** crear/listar/ver solicitudes.

Incluye:
- Tabla `solicitud_cmep` (+ lo mínimo de persona/cliente si aplica)
- Endpoints:
  - POST /solicitudes
  - GET /solicitudes (filtros básicos)
  - GET /solicitudes/{id}
  - PUT/PATCH /solicitudes/{id} (editar “todo” como dijiste MVP)

Tests:
- integración: crear y leer
- integración: permisos por rol (aunque sea “ADMIN todo” y otros limitado)

Smoke flow:
- crear solicitud → aparece en listado → detalle

---

### M3 — Estado Operativo Derivado + POLICY (workflow real)
**Objetivo:** “estado_operativo” derivado + acciones permitidas.

Incluye:
- función derivadora de estado (determinista, con precedencia)
- enforcement: `assert_allowed(role, estado_operativo, action)`
- endpoints de acciones (ej: asignar gestor, registrar pago, asignar médico, cerrar, cancelar)

Tests:
- unit: derivación de estado (casos)
- unit: policy matrix (tabla de permitidos)
- integración: acción cambia BD y cambia estado derivado

Smoke flow:
- REGISTRADO → ASIGNADO_GESTOR → PAGADO → ASIGNADO_MEDICO → CERRADO

---

### M4 — Archivos (subida + validación + storage)
**Objetivo:** subir documentos de solicitud con reglas claras.

Incluye:
- endpoints upload
- metadata en DB
- (local) guardar en filesystem o minio
- (prod) S3

Tests:
- integración: upload y listar archivos
- integración: rechazo por formato/tamaño (si aplica)

---

### M5 — Admin (usuarios/roles)
**Objetivo:** gestión básica de usuarios y roles.

Incluye:
- crear usuario
- asignar roles (tu tabla user_role si aplica)
- reset password (si lo vas a incluir)

Tests:
- integración: admin crea usuario, usuario loguea

---

### M6 — Deploy AWS (cuando M1–M3 estén estables)
**Objetivo:** mismo comportamiento en cloud.

Incluye:
- App Runner backend + RDS MySQL + S3
- CORS/cookies correctos (ojo aquí siempre duele)
- migraciones en deploy
- variables prod

---

## 3) Spec de Tasks (formato que Claude Code puede seguir)
Cada task debería tener esto:

**TASK ID:** Txxx  
**Módulo:** Mx  
**Objetivo:** qué desbloquea  
**Entradas:** doc(s) de referencia (01..07)  
**Cambios:** archivos/carpetas esperadas  
**Criterios de aceptación:** checks verificables  
**Tests:** qué tests se agregan y cómo correrlos  
**Riesgos:** (si aplica)

---

## 4) Backlog inicial sugerido (lista de tasks)
### M0 — Bootstrap
- T001 Crear estructura repo (backend/frontend/infra/docs)
- T002 Docker compose mysql + backend + envs
- T003 Backend `/health` + logging básico
- T004 Frontend “Status” + fetch `/health`

### M1 — Auth + Sesión
- T010 Tablas mínimas: users, sessions (según tu diseño)
- T011 Endpoint POST /auth/login
- T012 Endpoint POST /auth/logout
- T013 Middleware auth para rutas privadas
- T014 Tests integración login/sesión

### M2 — Solicitudes
- T020 Tablas mínimas: solicitud_cmep (+ fk necesarias)
- T021 POST /solicitudes
- T022 GET /solicitudes + filtros
- T023 GET /solicitudes/{id}
- T024 PATCH /solicitudes/{id} (editar todo)
- T025 Tests CRUD solicitud

### M3 — Estado derivado + POLICY
- T030 Implementar función derivar_estado_operativo()
- T031 Implementar policy enforcement (assert_allowed)
- T032 Endpoint acción: asignar gestor
- T033 Endpoint acción: registrar pago
- T034 Endpoint acción: asignar médico
- T035 Endpoint acción: cerrar/cancelar
- T036 Tests: derivación + policy + flujos

### M4 — Archivos
- T040 Tabla relacionadas a archivo aun no creadas
- T041 Upload endpoint + storage local
- T042 List/download endpoint
- T043 Tests upload

### M5 — Admin
- T050 Crear usuario (admin)
- T051 Asignar roles
- T052 Reset password (si entra en MVP)

### M6 — Deploy
- T060 Infra AWS (App Runner + RDS + S3)
- T061 Migraciones en prod
- T062 Smoke tests en cloud

---

## 5) Testing local: cómo lo haría “sí o sí”
- Unit: pytest
- Integración: levantar DB test (docker) + migrar + correr tests
- Un “smoke script” que haga:
  1) login admin
  2) crear solicitud
  3) asignar gestor
  4) registrar pago
  5) asignar médico
  6) cerrar

---

## 6) Qué debes “crear primero” para que todo funcione bien
Orden mínimo realista:
1) **Docker + DB** (aunque sea vacío)
2) **Migraciones** (aunque sea 2 tablas)
3) **Auth+Sesión**
4) **Solicitud CRUD**
5) **Estado derivado + POLICY**
Después ya todo lo demás es “sumar”.

---

## 7) Próximo paso (para que Claude Code arranque sin perderse)
Dile a Claude Code:
- “Empieza por M0 y M1 (T001–T014).”
- “No avances a M2 hasta que los tests de auth pasen y el smoke flow funcione.”
- “Usa mis docs en /docs como fuente única y mantén el contrato de API.”

Si quieres, en tu próximo mensaje me pegas el contenido de:
- `docs/02_modelo_de_datos.md`
- `docs/05_api_y_policy.md`
y yo te devuelvo **las tasks T010–T036 ya escritas con criterios de aceptación + lista exacta de endpoints + tablas mínimas** (en Markdown puro, listo para copiar).


