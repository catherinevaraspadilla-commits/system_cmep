# CMEP — Task Backlog Ejecutable

> **Estado**: Todos los modulos M0-M7 estan implementados y verificados (117 tests, 0 errores TS).
> Las tareas T001-T063 corresponden al plan original (M0-M5 + Cloud). Los modulos M5.5, M5.6, M6 (override/audit) y M7 (reportes) se implementaron fuera de este backlog.
> Ver `02_module_specs.md` para la especificacion completa de cada modulo y su estado.

Cada task sigue el formato:
- **TASK ID** — identificador unico
- **Modulo** — a que modulo pertenece
- **Objetivo** — que desbloquea
- **Entradas** — documentos de referencia
- **Cambios** — archivos/carpetas esperadas
- **Criterios de aceptacion** — checks verificables
- **Tests** — que tests se agregan
- **Riesgos** — si aplica

---

## M0 — Bootstrap Proyecto

### T001 — Crear estructura de repositorio

**Modulo:** M0
**Objetivo:** Estructura de carpetas lista para desarrollo
**Entradas:** doc 07 (arquitectura), doc 08 (plan)
**Cambios:**
```
backend/
  app/
    __init__.py
    main.py
    config.py
  requirements.txt
  Dockerfile
frontend/
  package.json
  src/
    App.tsx
    index.tsx
  Dockerfile
infra/
  docker-compose.yml
docs/
  source/    (ya existente)
  claude/    (ya existente)
.env.example
.gitignore
```
**Criterios de aceptacion:**
- [ ] Estructura de carpetas creada
- [ ] `.gitignore` ignora `.env`, `node_modules`, `__pycache__`, `.venv`
- [ ] `.env.example` con todas las variables documentadas

**Tests:** Ninguno
**Riesgos:** Ninguno

---

### T002 — Docker compose: MySQL + Backend + Frontend

**Modulo:** M0
**Objetivo:** `docker-compose up` levanta los 3 servicios
**Entradas:** doc 07 (arquitectura)
**Cambios:**
- `infra/docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `.env.example` actualizado

**Criterios de aceptacion:**
- [ ] `docker-compose up` levanta MySQL, backend y frontend sin errores
- [ ] MySQL accesible en puerto 3306
- [ ] Backend accesible en puerto 8000
- [ ] Frontend accesible en puerto 3000
- [ ] Variables de entorno cargadas correctamente

**Tests:** Verificacion manual de puertos
**Riesgos:** Conflictos de puertos; Docker no instalado

---

### T003 — Backend: /health + /version + logging

**Modulo:** M0
**Objetivo:** Backend responde con healthcheck
**Entradas:** doc 08 (plan)
**Cambios:**
- `backend/app/main.py` — FastAPI app con CORS + endpoints
- `backend/app/config.py` — Settings desde env vars

**Criterios de aceptacion:**
- [ ] `GET /health` retorna `{"ok": true, "status": "healthy"}`
- [ ] `GET /version` retorna `{"version": "0.1.0"}`
- [ ] CORS configurado para frontend local
- [ ] Logging basico configurado

**Tests:**
- test_health.py: GET /health retorna 200

**Riesgos:** Ninguno

---

### T004 — Frontend: pantalla status + fetch /health

**Modulo:** M0
**Objetivo:** Frontend muestra estado de conexion al backend
**Entradas:** doc 06 (UI)
**Cambios:**
- `frontend/src/App.tsx`
- `frontend/src/pages/Status.tsx`

**Criterios de aceptacion:**
- [ ] Frontend carga en navegador
- [ ] Muestra indicador "Conectado" / "Desconectado" segun respuesta de `/health`

**Tests:** Verificacion visual manual
**Riesgos:** CORS bloqueando fetch

---

### T005 — Alembic: inicializacion + primera migracion

**Modulo:** M0
**Objetivo:** Migraciones configuradas y funcionales
**Entradas:** doc 02 (modelo de datos)
**Cambios:**
- `backend/alembic.ini`
- `backend/migrations/` (estructura Alembic)
- `backend/app/database.py` — SQLAlchemy engine + session

**Criterios de aceptacion:**
- [ ] `alembic upgrade head` ejecuta sin errores
- [ ] Conexion a MySQL funcional
- [ ] Primera migracion (aunque sea vacia) aplicada

**Tests:** Ejecucion de migracion sin errores
**Riesgos:** Conexion a MySQL falla por credenciales o red

---

## M1 — Auth y Sesiones

### T010 — Migracion: tablas personas, users, user_role, user_permissions, sessions, password_resets

**Modulo:** M1
**Objetivo:** Tablas de auth creadas en BD
**Entradas:** doc 02 (modelo de datos, secciones 2.2.1, 2.2.7-2.2.11)
**Cambios:**
- Nueva migracion Alembic
- `backend/app/models/persona.py`
- `backend/app/models/user.py`
- `backend/app/models/session.py`

**Criterios de aceptacion:**
- [ ] Tablas creadas con todos los campos, tipos y constraints del doc 02
- [ ] ENUM values coinciden con doc 01
- [ ] Auditoria (created_by, updated_by, created_at, updated_at) en cada tabla
- [ ] FK con ON UPDATE RESTRICT, ON DELETE RESTRICT
- [ ] UNIQUE constraints: (tipo_documento, numero_documento), user_email, (user_id, user_role)

**Tests:** Migracion up/down sin errores
**Riesgos:** Tipos ENUM de MySQL vs SQLAlchemy

---

### T011 — Seed de desarrollo: usuario ADMIN

**Modulo:** M1
**Objetivo:** Datos iniciales para probar login
**Entradas:** doc 02, doc 01
**Cambios:**
- `infra/seed_dev.py` (o SQL)

**Criterios de aceptacion:**
- [ ] Al menos 1 usuario ADMIN con password conocido
- [ ] Al menos 1 usuario por cada rol (OPERADOR, GESTOR, MEDICO)
- [ ] Cada usuario tiene persona asociada
- [ ] Passwords hasheados con bcrypt

**Tests:** Seed ejecuta sin errores
**Riesgos:** Ninguno

---

### T012 — Endpoint POST /auth/login

**Modulo:** M1
**Objetivo:** Autenticacion funcional
**Entradas:** doc 05 (API, seccion Auth)
**Cambios:**
- `backend/app/api/auth.py`
- `backend/app/services/auth_service.py`
- `backend/app/utils/hashing.py`
- `backend/app/schemas/auth.py`

**Criterios de aceptacion:**
- [ ] Email normalizado a lower(trim)
- [ ] Password verificado contra hash bcrypt
- [ ] Sesion creada en tabla `sessions`
- [ ] Cookie httpOnly seteada en respuesta
- [ ] Retorna UserDTO: user_id, user_email, estado, roles, permissions_extra, display_name
- [ ] Usuario SUSPENDIDO: retorna 403
- [ ] Credenciales invalidas: retorna 401 o 422
- [ ] `last_login_at` actualizado en tabla users

**Tests:**
- test_login_success
- test_login_invalid_password
- test_login_user_not_found
- test_login_user_suspended
- test_login_email_case_insensitive

**Riesgos:** Cookie no se envia correctamente al frontend por CORS

---

### T013 — Endpoint POST /auth/logout

**Modulo:** M1
**Objetivo:** Invalidacion de sesion
**Entradas:** doc 05 (API)
**Cambios:**
- `backend/app/api/auth.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Sesion eliminada o marcada como expirada en BD
- [ ] Cookie eliminada de la respuesta
- [ ] Retorna `{"ok": true}`
- [ ] Sin sesion valida retorna 401

**Tests:**
- test_logout_success
- test_logout_without_session

**Riesgos:** Ninguno

---

### T014 — Endpoint GET /auth/me

**Modulo:** M1
**Objetivo:** Consulta de sesion actual
**Entradas:** doc 05 (API)
**Cambios:**
- `backend/app/api/auth.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Retorna UserDTO con roles y permisos
- [ ] Sin sesion: retorna 401
- [ ] Sesion expirada: retorna 401
- [ ] Usuario suspendido post-login: retorna 403 e invalida sesion

**Tests:**
- test_me_with_valid_session
- test_me_without_session
- test_me_expired_session

**Riesgos:** Ninguno

---

### T015 — Middleware de autenticacion para rutas privadas

**Modulo:** M1
**Objetivo:** Todo endpoint privado requiere sesion valida
**Entradas:** doc 05, doc 06 (regla de acceso)
**Cambios:**
- `backend/app/middleware/session_middleware.py`
- Aplicar a todas las rutas excepto `/health`, `/version`, `/auth/login`

**Criterios de aceptacion:**
- [ ] Requests sin cookie -> 401
- [ ] Requests con sesion invalida/expirada -> 401
- [ ] Requests con sesion valida -> pasan al handler con usuario en context
- [ ] `GET /health` y `GET /version` no requieren autenticacion

**Tests:**
- test_private_endpoint_without_auth
- test_private_endpoint_with_auth
- test_public_endpoint_without_auth

**Riesgos:** Performance: consulta a BD en cada request (mitigacion: cache en memoria con TTL corto)

---

### T016 — Frontend: pagina Login + integracion /auth/login

**Modulo:** M1
**Objetivo:** Login funcional desde el navegador
**Entradas:** doc 06 (pagina Login)
**Cambios:**
- `frontend/src/pages/Login.tsx`
- `frontend/src/services/api.ts` (API client)
- `frontend/src/hooks/useAuth.ts`

**Criterios de aceptacion:**
- [ ] Formulario con email y password
- [ ] Login exitoso redirige a `/app`
- [ ] Error de credenciales muestra mensaje
- [ ] Usuario suspendido muestra mensaje apropiado

**Tests:** Verificacion manual
**Riesgos:** Cookies cross-origin

---

## M2 — CRUD Solicitudes

### T020 — Migracion: tablas de dominio (clientes, promotores, empleados, servicios, solicitudes)

**Modulo:** M2
**Objetivo:** Modelo relacional completo creado en BD
**Entradas:** doc 02 (modelo de datos, secciones 2.2.2-2.2.6, 2.2.12-2.2.17)
**Cambios:**
- Nueva migracion Alembic
- `backend/app/models/cliente.py`
- `backend/app/models/promotor.py`
- `backend/app/models/empleado.py`
- `backend/app/models/servicio.py`
- `backend/app/models/solicitud.py`

**Criterios de aceptacion:**
- [ ] Todas las tablas del doc 02 creadas
- [ ] ENUMs correctos segun doc 01
- [ ] Constraints y FK segun doc 02
- [ ] Auditoria en cada tabla

**Tests:** Migracion up/down sin errores
**Riesgos:** Complejidad del modelo relacional

---

### T021 — Seed: datos de dominio (clientes, promotores, empleados, servicios)

**Modulo:** M2
**Objetivo:** Datos de prueba para desarrollo
**Entradas:** doc 01, doc 02
**Cambios:**
- Actualizar `infra/seed_dev.py`

**Criterios de aceptacion:**
- [ ] Al menos 3 clientes con personas asociadas
- [ ] Al menos 2 promotores (1 PERSONA, 1 EMPRESA)
- [ ] Empleados para cada usuario seed (con rol_empleado correcto)
- [ ] Al menos 1 medico con medico_extra
- [ ] Al menos 2 servicios con tarifa

**Tests:** Seed ejecuta sin errores
**Riesgos:** Ninguno

---

### T022 — Endpoint POST /solicitudes

**Modulo:** M2
**Objetivo:** Registro de nueva solicitud
**Entradas:** doc 05 (API, seccion Solicitudes)
**Cambios:**
- `backend/app/api/solicitudes.py`
- `backend/app/services/solicitud_service.py`
- `backend/app/schemas/solicitud.py`

**Criterios de aceptacion:**
- [ ] Crea solicitud con estado_atencion=REGISTRADO, estado_pago=PENDIENTE
- [ ] Crea o reutiliza persona/cliente por (tipo_documento, numero_documento)
- [ ] Asocia apoderado si se proporciona
- [ ] Asocia promotor si se proporciona
- [ ] Retorna 201 con solicitud_id
- [ ] Registra created_by con user_id de la sesion

**Tests:**
- test_create_solicitud_minimal
- test_create_solicitud_full
- test_create_solicitud_existing_client
- test_create_solicitud_unauthorized

**Riesgos:** Logica de "reutilizar persona existente"

---

### T023 — Endpoint GET /solicitudes (lista + filtros)

**Modulo:** M2
**Objetivo:** Listado paginado con filtros
**Entradas:** doc 05 (API), doc 06 (UI lista)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Paginacion: page, page_size, total
- [ ] Filtro por q (busqueda documento/nombre)
- [ ] Filtro por estado_operativo
- [ ] Filtro mine (solicitudes del usuario segun rol)
- [ ] Retorna SolicitudListItemDTO

**Tests:**
- test_list_solicitudes_paginated
- test_list_solicitudes_filter_estado
- test_list_solicitudes_search
- test_list_solicitudes_mine

**Riesgos:** Performance en queries con joins multiples

---

### T024 — Endpoint GET /solicitudes/{id} (detalle)

**Modulo:** M2
**Objetivo:** Detalle completo con estado operativo y acciones permitidas
**Entradas:** doc 05 (API), doc 03 (estado operativo), doc 06 (UI detalle)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar ruta)
- `backend/app/services/estado_operativo.py` (version basica)

**Criterios de aceptacion:**
- [ ] Retorna SolicitudDetailDTO
- [ ] Incluye estado_operativo derivado
- [ ] Incluye acciones_permitidas segun POLICY
- [ ] Incluye asignaciones_vigentes (gestor, medico)
- [ ] Incluye pagos y archivos (arrays vacios inicialmente)
- [ ] Incluye historial

**Tests:**
- test_detail_solicitud_exists
- test_detail_solicitud_not_found
- test_detail_includes_estado_operativo
- test_detail_includes_acciones_permitidas

**Riesgos:** La derivacion de estado y POLICY se necesitan aqui; puede adelantar trabajo de M3

---

### T025 — Endpoint PATCH /solicitudes/{id} (editar)

**Modulo:** M2
**Objetivo:** Edicion de datos con auditoria
**Entradas:** doc 04 (accion EDITAR_DATOS), doc 05 (API)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar ruta)
- `backend/app/utils/audit.py`

**Criterios de aceptacion:**
- [ ] Edita campos permitidos
- [ ] Registra cambios en solicitud_estado_historial (campo, valor_anterior, valor_nuevo)
- [ ] Valida POLICY: EDITAR_DATOS permitido para rol/estado
- [ ] Retorna solicitud actualizada
- [ ] 403 si no permitido, 404 si no existe, 422 si datos invalidos

**Tests:**
- test_edit_solicitud_success
- test_edit_solicitud_audit_trail
- test_edit_solicitud_forbidden

**Riesgos:** MVP permite editar "cualquier campo" — definir que campos especificamente

---

### T026 — Frontend: paginas solicitudes (lista, nueva, detalle)

**Modulo:** M2
**Objetivo:** Interfaz funcional para CRUD de solicitudes
**Entradas:** doc 06 (UI)
**Cambios:**
- `frontend/src/pages/app/Solicitudes.tsx`
- `frontend/src/pages/app/SolicitudNueva.tsx`
- `frontend/src/pages/app/SolicitudDetalle.tsx`
- `frontend/src/components/` (tablas, formularios)
- `frontend/src/types/solicitud.ts`

**Criterios de aceptacion:**
- [ ] Lista con filtros y paginacion
- [ ] Formulario de registro con validaciones frontend
- [ ] Vista detalle con datos completos
- [ ] Botones de accion basados en acciones_permitidas (renderizados, no funcionales aun)
- [ ] Manejo de errores 403/404/422

**Tests:** Verificacion manual
**Riesgos:** Complejidad del formulario de registro

---

## M3 — Workflow + POLICY + Acciones

### T030 — Implementar derivar_estado_operativo()

**Modulo:** M3
**Objetivo:** Funcion pura que calcula estado operativo derivado
**Entradas:** doc 03 (estado operativo derivado)
**Cambios:**
- `backend/app/services/estado_operativo.py`

**Criterios de aceptacion:**
- [ ] Implementa las 6 reglas de precedencia del doc 03
- [ ] Primer match gana
- [ ] Funcion pura (sin side effects, sin acceso a BD directo)
- [ ] Todos los 7+ casos de la tabla de derivacion pasan

**Tests:**
- test_estado_registrado
- test_estado_asignado_gestor
- test_estado_pagado
- test_estado_asignado_medico
- test_estado_cerrado
- test_estado_cancelado
- test_cancelado_overrides_all

**Riesgos:** Orden de precedencia incorrecto

---

### T031 — Implementar POLICY dict + assert_allowed()

**Modulo:** M3
**Objetivo:** Autorizacion basada en matriz rol x estado
**Entradas:** doc 05 (POLICY JSON)
**Cambios:**
- `backend/app/services/policy.py`

**Criterios de aceptacion:**
- [ ] POLICY dict coincide exactamente con doc 05
- [ ] assert_allowed(rol, estado, accion) retorna True o lanza HTTPException 403
- [ ] get_acciones_permitidas(roles, estado) retorna lista de acciones (union de roles)
- [ ] Todos los 4 roles x 6 estados verificados

**Tests:**
- test_policy_admin_registrado (y todas las combinaciones)
- test_policy_forbidden_operador_cerrado
- test_get_acciones_admin
- test_assert_allowed_raises_403

**Riesgos:** Transcripcion incorrecta de la POLICY

---

### T032 — Endpoint POST /solicitudes/{id}/asignar-gestor

**Modulo:** M3
**Objetivo:** Asignacion de gestor funcional
**Entradas:** doc 04 (ASIGNAR_GESTOR), doc 05 (API)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Valida POLICY
- [ ] Valida R10 (empleado ACTIVO, rol GESTOR)
- [ ] Cierra asignacion vigente anterior (es_vigente=0)
- [ ] Crea nueva asignacion (es_vigente=1)
- [ ] Transaccion atomica
- [ ] Registra auditoria
- [ ] 403/422/409 segun corresponda

**Tests:**
- test_asignar_gestor_success
- test_asignar_gestor_forbidden
- test_asignar_gestor_invalid_employee
- test_asignar_gestor_replaces_previous

**Riesgos:** Condicion de carrera en asignacion concurrente

---

### T033 — Endpoint POST /solicitudes/{id}/cambiar-gestor

**Modulo:** M3
**Objetivo:** Cambio de gestor
**Entradas:** doc 04 (CAMBIAR_GESTOR)
**Cambios:** Mismos archivos que T032

**Criterios de aceptacion:**
- [ ] Misma logica que ASIGNAR_GESTOR
- [ ] Auditoria con campo 'cambio_gestor'

**Tests:**
- test_cambiar_gestor_success
- test_cambiar_gestor_forbidden

**Riesgos:** Ninguno adicional

---

### T034 — Endpoint POST /solicitudes/{id}/registrar-pago

**Modulo:** M3
**Objetivo:** Registro de pago funcional
**Entradas:** doc 04 (REGISTRAR_PAGO), doc 05 (API)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Valida POLICY
- [ ] Valida monto > 0, moneda consistente
- [ ] Inserta pago en pago_solicitud
- [ ] Marca pago como validado (validated_by, validated_at)
- [ ] Actualiza solicitud_cmep.estado_pago = 'PAGADO'
- [ ] Registra auditoria (pago_registrado, estado_pago)
- [ ] 403/422/404 segun corresponda

**Tests:**
- test_registrar_pago_success
- test_registrar_pago_forbidden
- test_registrar_pago_invalid_monto
- test_registrar_pago_updates_estado

**Riesgos:** Multiples pagos por solicitud — confirmar que es valido

---

### T035 — Endpoints asignar-medico, cambiar-medico

**Modulo:** M3
**Objetivo:** Asignacion y cambio de medico
**Entradas:** doc 04 (ASIGNAR_MEDICO, CAMBIAR_MEDICO)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar rutas)

**Criterios de aceptacion:**
- [ ] Valida POLICY
- [ ] Requiere estado_pago = PAGADO
- [ ] Valida R10 (empleado ACTIVO, rol MEDICO)
- [ ] Transaccion atomica (cerrar vigente, crear nueva)
- [ ] Auditoria registrada
- [ ] 403/422/409 segun corresponda

**Tests:**
- test_asignar_medico_success
- test_asignar_medico_requires_pagado
- test_asignar_medico_invalid_employee
- test_cambiar_medico_success

**Riesgos:** Ninguno adicional

---

### T036 — Endpoints cerrar y cancelar

**Modulo:** M3
**Objetivo:** Cierre y cancelacion de solicitudes
**Entradas:** doc 04 (CERRAR, CANCELAR)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar rutas)

**Criterios de aceptacion:**
- [ ] CERRAR: actualiza estado_atencion = 'ATENDIDO', valida POLICY
- [ ] CANCELAR: actualiza estado_atencion = 'CANCELADO', valida POLICY
- [ ] No se puede cerrar/cancelar si ya esta en ese estado (409)
- [ ] Auditoria registrada

**Tests:**
- test_cerrar_success
- test_cerrar_already_closed
- test_cancelar_success
- test_cancelar_already_cancelled

**Riesgos:** Ninguno

---

### T037 — Endpoint POST /solicitudes/{id}/override

**Modulo:** M3
**Objetivo:** Override para ADMIN en estados terminales
**Entradas:** doc 04 (OVERRIDE), doc 05 (API)
**Cambios:**
- `backend/app/api/solicitudes.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Solo ADMIN puede ejecutar
- [ ] Solo en estados CERRADO o CANCELADO
- [ ] Comentario obligatorio
- [ ] Registra auditoria reforzada (override=true + cambios especificos)
- [ ] Ejecuta sub-accion segun payload

**Tests:**
- test_override_success
- test_override_not_admin
- test_override_not_terminal_state
- test_override_requires_comment

**Riesgos:** Complejidad de ejecutar sub-acciones dentro de override

---

### T038 — Frontend: botones de accion + flujo completo en detalle

**Modulo:** M3
**Objetivo:** Acciones del workflow funcionales desde la UI
**Entradas:** doc 06 (UI detalle)
**Cambios:**
- `frontend/src/pages/app/SolicitudDetalle.tsx` (actualizar)
- `frontend/src/components/` (modales, formularios de accion)

**Criterios de aceptacion:**
- [ ] Botones se muestran SOLO si estan en acciones_permitidas
- [ ] Cada boton abre modal/formulario con campos requeridos
- [ ] Post-accion: reconsultar GET /solicitudes/{id}
- [ ] Errores 403 -> modal "No autorizado"
- [ ] Errores 409 -> "La solicitud cambio, refresca"
- [ ] Errores 422 -> validaciones por campo

**Tests:** Verificacion manual
**Riesgos:** UX de multiples modales/formularios

---

### T039 — ~~Frontend: pagina Inicio (mi trabajo de hoy)~~ (MOVIDO a M5.6 — T059/T060/T061)

> Tarea original reemplazada por M5.6 con requisitos detallados.
> Ver: `docs/claude/M5.6_dashboard_inicio.md`

---

## M4 — Archivos / Promotores

### T040 — Backend: upload de archivos

**Modulo:** M4
**Objetivo:** Subida de archivos asociados a solicitudes
**Entradas:** doc 05 (API archivos)
**Cambios:**
- `backend/app/api/archivos.py`
- `backend/app/services/archivo_service.py`

**Criterios de aceptacion:**
- [ ] POST multipart/form-data acepta archivo
- [ ] Almacena en filesystem (dev) o S3 (prod)
- [ ] Registra metadata en tabla archivos
- [ ] Asocia a solicitud en solicitud_archivo
- [ ] Opcionalmente asocia a pago_id
- [ ] Tipos: EVIDENCIA_PAGO, DOCUMENTO, OTROS
- [ ] Limite de tamano configurado

**Tests:**
- test_upload_success
- test_upload_unauthorized
- test_upload_solicitud_not_found

**Riesgos:** Archivos grandes; configuracion S3

---

### T041 — Backend: descarga de archivos

**Modulo:** M4
**Objetivo:** Descarga o URL firmada de archivos
**Entradas:** doc 05 (API)
**Cambios:**
- `backend/app/api/archivos.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] GET /archivos/{id} retorna URL de descarga (S3) o contenido (local)
- [ ] Solo usuarios autenticados pueden descargar
- [ ] Archivo no encontrado: 404

**Tests:**
- test_download_success
- test_download_not_found

**Riesgos:** URL firmada expira antes de descarga

---

### T042 — Frontend: componente de archivos en detalle

**Modulo:** M4
**Objetivo:** Subida y listado de archivos en vista de solicitud
**Entradas:** doc 06
**Cambios:**
- `frontend/src/components/Archivos.tsx`
- Actualizar SolicitudDetalle.tsx

**Criterios de aceptacion:**
- [ ] Boton de subir archivo
- [ ] Lista de archivos con nombre, tipo, fecha
- [ ] Link de descarga funcional

**Tests:** Verificacion manual
**Riesgos:** UX de drag-and-drop vs input file

---

## M5 — Administracion

### T050 — Backend: GET /admin/users (listar usuarios)

**Modulo:** M5
**Objetivo:** Listado de usuarios para administracion
**Entradas:** doc 05 (API admin)
**Cambios:**
- `backend/app/api/admin.py`
- `backend/app/services/admin_service.py`

**Criterios de aceptacion:**
- [ ] Solo ADMIN puede acceder
- [ ] Lista usuarios con roles, estado, permisos extra
- [ ] Non-admin: 403

**Tests:**
- test_list_users_admin
- test_list_users_non_admin

**Riesgos:** Ninguno

---

### T051 — Backend: POST /admin/users (crear usuario)

**Modulo:** M5
**Objetivo:** Creacion de usuarios desde panel admin
**Entradas:** doc 05 (API), doc 02 (modelo), doc 04 (reglas)
**Cambios:**
- `backend/app/api/admin.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Crea persona + user + user_role en transaccion
- [ ] Email normalizado: lower(trim)
- [ ] Email duplicado: 422
- [ ] Si persona.email es NULL, copiar user_email (R5)
- [ ] Password hasheado con bcrypt
- [ ] Si rol incluye MEDICO, crear/validar medico_extra (R11)

**Tests:**
- test_create_user_success
- test_create_user_duplicate_email
- test_create_user_copies_email

**Riesgos:** Complejidad de crear persona + empleado + user en un solo request

---

### T052 — Backend: PATCH /admin/users/{id} (actualizar usuario)

**Modulo:** M5
**Objetivo:** Actualizacion de estado, roles, permisos
**Entradas:** doc 05, doc 02
**Cambios:**
- `backend/app/api/admin.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Actualiza estado, roles, permisos extra
- [ ] Si estado -> SUSPENDIDO: invalidar sesiones existentes (R13)
- [ ] Solo ADMIN

**Tests:**
- test_update_user_success
- test_suspend_user_invalidates_sessions
- test_update_user_non_admin

**Riesgos:** Invalidacion de sesiones en tiempo real

---

### T053 — Backend: POST /admin/users/{id}/reset-password

**Modulo:** M5
**Objetivo:** Reset seguro de password
**Entradas:** doc 02 (password_resets, R14)
**Cambios:**
- `backend/app/api/admin.py` (agregar ruta)

**Criterios de aceptacion:**
- [ ] Genera token con hash, expiracion y uso unico
- [ ] Token valido: used_at IS NULL y now() < expires_at (R14)
- [ ] En MVP: retorna token al admin (no hay email)

**Tests:**
- test_reset_password_generates_token
- test_reset_password_token_expires
- test_reset_password_token_single_use

**Riesgos:** Sin canal de email, el admin debe comunicar token manualmente

---

### T054 — Frontend: pagina Usuarios (CRUD admin)

**Modulo:** M5
**Objetivo:** Interfaz de administracion de usuarios
**Entradas:** doc 06 (pagina Usuarios)
**Cambios:**
- `frontend/src/pages/app/Usuarios.tsx`
- `frontend/src/components/` (formularios)

**Criterios de aceptacion:**
- [ ] Tabla de usuarios con estado, roles
- [ ] Formulario de creacion
- [ ] Edicion de estado y roles
- [ ] Boton de reset password
- [ ] Solo visible si rol incluye ADMIN

**Tests:** Verificacion manual
**Riesgos:** Ninguno

---

## M5.5 — Mejoras Incrementales

### T055 — Separar tipo_documento y numero_documento en detalle de solicitud

**Modulo:** M5.5
**Objetivo:** Mostrar tipo y numero de documento como campos separados en el detalle
**Entradas:** M5.5_mejoras_incrementales.md (5.5.3)
**Cambios:**
- `backend/app/services/solicitud_service.py` (build_detail_dto + list_solicitudes)
- `frontend/src/types/solicitud.ts` (ClienteDTO)
- `frontend/src/pages/app/SolicitudDetalle.tsx`

**Criterios de aceptacion:**
- [ ] ClienteDTO retorna tipo_documento y numero_documento separados
- [ ] Campo `doc` se mantiene por retrocompatibilidad
- [ ] Detalle muestra dos campos separados

**Tests:**
- test_detail_cliente_separate_doc_fields

**Riesgos:** Bajo

---

### T056 — Registro de promotor nuevo durante creacion de solicitud

**Modulo:** M5.5
**Objetivo:** Permitir registrar promotor nuevo inline al crear solicitud
**Entradas:** M5.5_mejoras_incrementales.md (5.5.1), docs/source/02_modelo_de_datos.md (2.2.4)
**Cambios:**
- `backend/app/schemas/solicitud.py` (expandir PromotorInput)
- `backend/app/api/solicitudes.py` (logica crear promotor)
- `backend/app/services/solicitud_service.py` (create_promotor)
- `backend/app/models/solicitud.py` (relationship promotor)
- `frontend/src/types/solicitud.ts` (PromotorInput)
- `frontend/src/pages/app/SolicitudNueva.tsx` (sub-formulario)

**Criterios de aceptacion:**
- [ ] PromotorInput expandido con campos por tipo (PERSONA/EMPRESA/OTROS)
- [ ] Validacion backend: PERSONA requiere nombres+apellidos, EMPRESA requiere razon_social, OTROS requiere nombre_promotor_otros
- [ ] No se puede enviar promotor + promotor_id simultanamente (422)
- [ ] Promotor existente via dropdown sigue funcionando
- [ ] Frontend muestra campos dinamicos segun tipo seleccionado

**Tests:**
- test_create_solicitud_with_new_promotor_persona
- test_create_solicitud_with_new_promotor_empresa
- test_create_solicitud_with_new_promotor_otros
- test_create_solicitud_promotor_and_promotor_id_error
- test_create_solicitud_promotor_empresa_sin_razon_social

**Riesgos:** Medio — validacion cruzada de campos segun tipo

---

### T057 — Mostrar promotor en detalle de solicitud

**Modulo:** M5.5
**Objetivo:** Seccion de promotor visible en detalle de solicitud
**Entradas:** M5.5_mejoras_incrementales.md (5.5.2)
**Cambios:**
- `backend/app/services/solicitud_service.py` (build_detail_dto + list_solicitudes)
- `frontend/src/types/solicitud.ts` (PromotorDetailDTO)
- `frontend/src/pages/app/SolicitudDetalle.tsx` (seccion Promotor)

**Criterios de aceptacion:**
- [ ] Detalle incluye promotor con tipo, nombre, ruc, email, celular, fuente
- [ ] Nombre se construye segun tipo (PERSONA: persona, EMPRESA: razon_social, OTROS: nombre_promotor_otros)
- [ ] Solicitudes sin promotor muestran "Sin promotor"
- [ ] Lista de solicitudes tambien muestra nombre del promotor

**Tests:**
- test_detail_includes_promotor
- test_detail_without_promotor

**Riesgos:** Bajo — relationship selectin evita N+1

---

### T058 — Seccion de permisos por rol en pagina de usuarios

**Modulo:** M5.5
**Objetivo:** Tabla de permisos (POLICY) visible para ADMIN
**Entradas:** M5.5_mejoras_incrementales.md (5.5.4)
**Cambios:**
- `backend/app/api/admin.py` (endpoint GET /admin/permisos)
- `frontend/src/pages/app/UsuariosLista.tsx` (seccion permisos)

**Criterios de aceptacion:**
- [ ] Endpoint GET /admin/permisos retorna POLICY como JSON
- [ ] Solo ADMIN puede acceder (403 para otros)
- [ ] Frontend muestra tabla: filas=estados, columnas=roles, celdas=acciones
- [ ] Seccion colapsable (inicialmente cerrada)
- [ ] Nota informativa sobre reglas de edicion por rol

**Tests:**
- test_get_permisos_as_admin
- test_get_permisos_as_non_admin

**Riesgos:** Bajo — seccion informativa, no modifica logica

---

## M5.6 — Dashboard / Pagina de Inicio

### T059 — Backend: parametro `mine` en GET /solicitudes

**Modulo:** M5.6
**Objetivo:** Filtrar solicitudes por usuario logueado segun su rol
**Entradas:** M5.6_dashboard_inicio.md (seccion 2)
**Cambios:**
- `backend/app/services/solicitud_service.py` (agregar filtro user_id/roles en list_solicitudes)
- `backend/app/api/solicitudes.py` (agregar query param `mine: bool`)

**Criterios de aceptacion:**
- [ ] `mine=true` + OPERADOR → solo solicitudes donde `created_by = user_id`
- [ ] `mine=true` + GESTOR → solo solicitudes con asignacion vigente de ese gestor
- [ ] `mine=true` + MEDICO → solo solicitudes con asignacion vigente de ese medico
- [ ] `mine=true` + ADMIN → todas (sin filtro)
- [ ] `mine=true` + multi-rol → union de conjuntos sin duplicados
- [ ] `mine=false` o ausente → comportamiento actual (todas)
- [ ] Paginacion y demas filtros (q, estado_operativo) siguen funcionando con mine

**Tests:**
- test_list_solicitudes_mine_operador
- test_list_solicitudes_mine_gestor
- test_list_solicitudes_mine_medico
- test_list_solicitudes_mine_admin
- test_list_solicitudes_mine_multi_rol
- test_list_solicitudes_mine_false_unchanged

**Riesgos:** Joins adicionales para asignaciones — mitigado con page_size pequeno

---

### T060_dash — Frontend: reescribir Inicio.tsx como dashboard

**Modulo:** M5.6
**Objetivo:** Pagina de inicio funcional con bienvenida, accesos rapidos y solicitudes relevantes
**Entradas:** M5.6_dashboard_inicio.md (secciones 1, 3, 4)
**Cambios:**
- `frontend/src/pages/app/Inicio.tsx` (reescritura completa)

**Criterios de aceptacion:**
- [ ] Bloque de bienvenida con nombre del usuario y descripcion del sistema
- [ ] Texto adaptado por rol (OPERADOR, GESTOR, MEDICO, ADMIN)
- [ ] Usuarios multi-rol ven descripciones combinadas
- [ ] Botones de accion rapida segun rol (navegan a rutas correspondientes)
- [ ] Tabla compacta con ultimas 10 solicitudes del usuario (mine=true)
- [ ] Link "Ver todas las solicitudes" al final
- [ ] Texto amigable cuando no hay solicitudes
- [ ] Lenguaje simple, sin tecnicismos
- [ ] Responsive (cards colapsan en pantallas angostas)
- [ ] Estilo consistente con el resto del sistema (PRIMARY=#1a3d5c)

**Tests:** Verificacion manual (smoke test en checkpoint)
**Riesgos:** Bajo

---

### T061_dash — Tests backend para filtro mine

**Modulo:** M5.6
**Objetivo:** Cobertura de tests para el nuevo parametro
**Entradas:** M5.6_dashboard_inicio.md (seccion 7)
**Cambios:**
- `backend/tests/integration/test_solicitudes.py` (agregar tests)

**Criterios de aceptacion:**
- [ ] 6 tests nuevos cubriendo todos los escenarios de mine
- [ ] Tests existentes no se rompen

**Tests:**
- test_list_solicitudes_mine_operador
- test_list_solicitudes_mine_gestor
- test_list_solicitudes_mine_medico
- test_list_solicitudes_mine_admin
- test_list_solicitudes_mine_multi_rol
- test_list_solicitudes_mine_false_unchanged

**Riesgos:** Ninguno

---

## M6 — Modelo de Datos, POLICY y Detalle de Solicitud

### T062_m6 — Documentacion M6

**Modulo:** M6
**Objetivo:** Documentar override, catalogo de tablas, tablas faltantes, enums, discrepancias POLICY
**Entradas:** docs/source/05_api_y_policy.md (POLICY), modelos existentes
**Cambios:**
- `docs/claude/M6_override_y_auditoria.md` (nuevo)
- `docs/claude/07_tablas_del_sistema.md` (nuevo)
- `docs/claude/tablas_faltantes.md` (poblar)
- `docs/claude/M6_modelo_datos_y_workflow.md` (nuevo)

**Criterios de aceptacion:**
- [ ] Override documentado: reglas, sub-acciones, auditoria doble
- [ ] Catalogo de 19 tablas con columnas, tipos, PKs, FKs
- [ ] Tablas faltantes analizado (ninguna faltante del diseno original)
- [ ] Enums no utilizados documentados (EN_PROCESO, OBSERVADO, EstadoCertificado)
- [ ] 4 discrepancias POLICY identificadas y documentadas

**Tests:** Ninguno (solo documentacion)
**Riesgos:** Ninguno

---

### T063_m6 — Nuevas columnas en solicitud_cmep + tabla resultado_medico

**Modulo:** M6
**Objetivo:** Extender modelo de datos para tracking de cierre/cancelacion y resultados medicos
**Entradas:** M6_modelo_datos_y_workflow.md
**Cambios:**
- `backend/app/models/solicitud.py` (+6 columnas, +clase ResultadoMedico, +relationship)
- `backend/app/models/__init__.py` (+import ResultadoMedico)

**Criterios de aceptacion:**
- [ ] motivo_cancelacion, fecha_cierre, cerrado_por, fecha_cancelacion, cancelado_por, comentario_admin en SolicitudCmep
- [ ] Tabla resultado_medico con: resultado_id, solicitud_id, medico_id, fecha_evaluacion, diagnostico, resultado, observaciones, recomendaciones, estado_certificado
- [ ] Todas columnas nullable (sin impacto en filas existentes)
- [ ] Tests existentes siguen pasando (create_all recrea tablas)

**Tests:** Tests existentes verifican compatibilidad
**Riesgos:** Bajo — todo nullable

---

### T064_m6 — Correccion POLICY (OPERADOR y GESTOR)

**Modulo:** M6
**Objetivo:** Alinear POLICY con fuente de verdad (docs/source/05_api_y_policy.md)
**Entradas:** docs/source/05_api_y_policy.md lineas 51-67
**Cambios:**
- `backend/app/services/policy.py` (OPERADOR -3 acciones, GESTOR -1 accion)
- `backend/tests/unit/test_policy.py` (invertir 4 tests)
- `backend/tests/integration/test_workflow.py` (invertir 1 test)

**Criterios de aceptacion:**
- [ ] OPERADOR sin REGISTRAR_PAGO en ASIGNADO_GESTOR
- [ ] OPERADOR sin ASIGNAR_MEDICO en PAGADO
- [ ] OPERADOR sin CERRAR en ASIGNADO_MEDICO
- [ ] GESTOR sin CERRAR en ASIGNADO_MEDICO
- [ ] 4 tests unit invertidos (assert not in)
- [ ] 1 test integracion invertido (expect 403)
- [ ] Happy path (test_full_happy_path) sigue pasando

**Tests:**
- test_operador_asignado_gestor_cannot_registrar_pago
- test_operador_pagado_cannot_asignar_medico
- test_operador_asignado_medico_cannot_cerrar
- test_gestor_asignado_medico_cannot_cerrar
- test_registrar_pago_operador_forbidden

**Riesgos:** Medio — cambia comportamiento de OPERADOR y GESTOR

---

### T065_m6 — Backend: exponer nuevos campos en detalle

**Modulo:** M6
**Objetivo:** Nuevos campos disponibles en SolicitudDetailDTO
**Entradas:** T063_m6
**Cambios:**
- `backend/app/services/solicitud_service.py` (cerrar, cancelar, build_detail_dto)
- `backend/app/api/solicitudes.py` (override handler)
- `backend/app/schemas/solicitud.py` (SolicitudDetailDTO)

**Criterios de aceptacion:**
- [ ] cerrar_solicitud establece fecha_cierre y cerrado_por
- [ ] cancelar_solicitud establece fecha_cancelacion, cancelado_por, motivo_cancelacion
- [ ] Override CERRAR/CANCELAR tambien establece los campos
- [ ] build_detail_dto retorna todos los campos nuevos
- [ ] Campos default null/[] — no rompe API existente

**Tests:** Tests existentes de cerrar/cancelar siguen pasando
**Riesgos:** Bajo — campos aditivos con default null

---

### T066_m6 — Frontend: tipos y detalle para nuevos campos

**Modulo:** M6
**Objetivo:** Mostrar nuevos campos en la vista de detalle de solicitud
**Entradas:** T065_m6
**Cambios:**
- `frontend/src/types/solicitud.ts` (+ResultadoMedicoDTO, +campos en SolicitudDetailDTO)
- `frontend/src/pages/app/SolicitudDetalle.tsx` (+secciones UI)

**Criterios de aceptacion:**
- [ ] ResultadoMedicoDTO definido
- [ ] SolicitudDetailDTO extendido con 7 campos nuevos
- [ ] Alerta de cancelacion visible si motivo_cancelacion existe
- [ ] Fecha de cierre visible en solicitudes cerradas
- [ ] Seccion de resultados medicos (solo si hay datos)
- [ ] Comentario admin visible (solo si no es null)
- [ ] 0 errores TypeScript

**Tests:** Verificacion manual + tsc --noEmit
**Riesgos:** Bajo — cambios aditivos

---

## M7 — Despliegue Cloud

### T060 — Infraestructura AWS (RDS + App Runner + S3)

**Modulo:** M7
**Objetivo:** Infraestructura cloud creada
**Entradas:** doc 07 (arquitectura)
**Cambios:**
- Scripts/configuracion de infra AWS

**Criterios de aceptacion:**
- [ ] RDS MySQL 8 accesible desde App Runner
- [ ] App Runner desplegado con backend
- [ ] S3 bucket de archivos creado (privado)
- [ ] S3 bucket de frontend creado
- [ ] Secrets Manager con credenciales

**Tests:** Verificacion de conectividad
**Riesgos:** Configuracion IAM; costos AWS

---

### T061 — CloudFront + despliegue frontend

**Modulo:** M7
**Objetivo:** Frontend accesible via HTTPS con CDN
**Entradas:** doc 07
**Cambios:**
- Configuracion CloudFront
- Build y deploy de frontend a S3

**Criterios de aceptacion:**
- [ ] Frontend carga desde URL publica HTTPS
- [ ] SPA fallback a index.html funciona
- [ ] CORS correcto entre frontend y backend

**Tests:** Smoke manual en navegador
**Riesgos:** CORS/cookies cross-origin

---

### T062 — Migraciones + seed en produccion

**Modulo:** M7
**Objetivo:** BD de produccion inicializada
**Entradas:** doc 02
**Cambios:**
- Ejecucion de Alembic contra RDS
- Seed de usuario ADMIN

**Criterios de aceptacion:**
- [ ] Todas las migraciones aplicadas sin errores
- [ ] Usuario ADMIN creado con password seguro
- [ ] Sin datos de desarrollo en produccion

**Tests:** Login funcional en prod
**Riesgos:** Migraciones fallidas; rollback necesario

---

### T063 — Smoke test completo en cloud

**Modulo:** M7
**Objetivo:** Validar flujo completo en produccion
**Entradas:** Todos los docs

**Criterios de aceptacion:**
- [ ] Login desde navegador (desktop y movil)
- [ ] Crear solicitud
- [ ] Flujo completo: REGISTRADO -> CERRADO
- [ ] Upload y download de archivo
- [ ] CRUD de usuarios
- [ ] Logs visibles en CloudWatch

**Tests:** Smoke manual end-to-end
**Riesgos:** Problemas de red/latencia no vistos en dev
