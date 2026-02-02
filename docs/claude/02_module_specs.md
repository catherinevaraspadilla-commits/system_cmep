# CMEP — Especificacion por Modulos

> Todos los modulos M0-M7 estan implementados. 117 tests pasando, 0 errores TypeScript.

---

## M0 — Bootstrap Proyecto

### Objetivo
Estructura de repositorio funcional. Backend + Frontend + BD levantan con un solo comando. Healthcheck end-to-end.

### Endpoints backend
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/health` | Retorna `{"ok": true, "status": "healthy"}` |
| GET | `/version` | Retorna version de la app |

### Cambios de BD
- SQLite (dev) / MySQL (prod)
- BD creada con todas las tablas via `create_all`

### Tests
- **Integracion:** `GET /health` retorna 200, `GET /version` retorna 200

### Criterios de aceptacion
- [x] Backend levanta sin errores
- [x] `GET /health` retorna 200 con JSON valido
- [x] Frontend muestra indicador de conexion exitosa

---

## M1 — Auth y Sesiones

### Objetivo
Login por email/password, sesiones server-side, middleware de autenticacion, logout. Todo endpoint requiere sesion valida.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| POST | `/auth/login` | Autentica y crea sesion | Publico |
| POST | `/auth/logout` | Invalida sesion actual | Privado |
| GET | `/auth/me` | Retorna usuario actual + roles | Privado |

### Tablas
- `personas`, `users`, `user_role`, `user_permissions`, `sessions`, `password_resets`

### Tests
- **Unit:** Hash/verificacion de password, normalizacion de email
- **Integracion:** Login exitoso, credenciales invalidas, usuario suspendido, me con/sin sesion, logout, email case-insensitive

### Criterios de aceptacion
- [x] Login exitoso retorna datos del usuario y setea cookie httpOnly
- [x] `GET /auth/me` funciona con cookie valida
- [x] Sesion se invalida correctamente al hacer logout
- [x] Usuario SUSPENDIDO no puede hacer login
- [x] Todos los endpoints privados rechazan requests sin sesion (401)
- [x] Email se normaliza a lowercase/trim
- [x] Seed: usuarios ADMIN, OPERADOR, GESTOR, MEDICO con credenciales conocidas

### Paginas frontend
- Login (`/login`), Redirect a `/app` post-login

---

## M2 — CRUD Solicitudes

### Objetivo
Crear, listar (con filtros y paginacion), ver detalle y editar solicitudes. Modelo completo de personas, clientes, promotores, servicios, empleados.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| POST | `/solicitudes` | Crear solicitud | Privado |
| GET | `/solicitudes` | Listar con filtros y paginacion | Privado |
| GET | `/solicitudes/{id}` | Detalle completo | Privado |
| PATCH | `/solicitudes/{id}` | Editar datos (EDITAR_DATOS) | Privado |

### Tablas
- `clientes`, `cliente_apoderado`, `promotores`, `empleado`, `medico_extra`, `servicios`
- `solicitud_cmep`, `solicitud_asignacion`, `solicitud_estado_historial`, `pago_solicitud`
- `archivos`, `solicitud_archivo`

### Tests
- **Integracion:** Crear solicitud minimal, con apoderado, con cliente existente, sin auth; listar vacio, con data, con busqueda, mine por rol; detalle, editar

### Criterios de aceptacion
- [x] POST /solicitudes crea solicitud con estado_atencion=REGISTRADO, estado_pago=PENDIENTE
- [x] GET /solicitudes retorna lista paginada con filtros funcionales
- [x] GET /solicitudes/{id} retorna estado_operativo derivado y acciones_permitidas
- [x] PATCH /solicitudes/{id} modifica datos y registra historial
- [x] Todas las tablas del modelo relacional creadas

### Paginas frontend
- Solicitudes lista (`/app/solicitudes`), Solicitud nueva (`/app/solicitudes/nueva`), Solicitud detalle (`/app/solicitudes/{id}`)

---

## M3 — Workflow + POLICY + Acciones

### Objetivo
Implementar estado operativo derivado, POLICY de autorizacion y endpoints de acciones. Workflow completo REGISTRADO -> CERRADO funciona end-to-end.

### Endpoints backend
| Metodo | Ruta | Accion | Auth |
|--------|------|--------|------|
| POST | `/solicitudes/{id}/asignar-gestor` | ASIGNAR_GESTOR | Privado |
| POST | `/solicitudes/{id}/cambiar-gestor` | CAMBIAR_GESTOR | Privado |
| POST | `/solicitudes/{id}/registrar-pago` | REGISTRAR_PAGO | Privado |
| POST | `/solicitudes/{id}/asignar-medico` | ASIGNAR_MEDICO | Privado |
| POST | `/solicitudes/{id}/cambiar-medico` | CAMBIAR_MEDICO | Privado |
| POST | `/solicitudes/{id}/cerrar` | CERRAR | Privado |
| POST | `/solicitudes/{id}/cancelar` | CANCELAR | Privado |
| POST | `/solicitudes/{id}/override` | OVERRIDE | Privado (ADMIN) |

### Componentes backend
1. `derivar_estado_operativo()` — funcion pura, estado derivado
2. `POLICY` dict — `{rol: {estado: [acciones]}}`
3. `assert_allowed()` — lanza 403 si no permitido

### Estado operativo derivado (precedencia)
```
CANCELADO > CERRADO > ASIGNADO_MEDICO > PAGADO > ASIGNADO_GESTOR > REGISTRADO
```

### Tests
- **Unit:** derivar_estado_operativo (9 casos), POLICY matrix (19 tests), assert_allowed
- **Integracion:** Flujo completo happy path, cancelar, override, permisos 403, R10 validation

### Criterios de aceptacion
- [x] derivar_estado_operativo() produce los 6 estados correctamente
- [x] POLICY coincide con la matriz del doc 05 (alineada en M6)
- [x] Flujo happy path completo funciona end-to-end
- [x] Acciones no permitidas retornan 403
- [x] ASIGNAR_MEDICO requiere estado_pago=PAGADO
- [x] OVERRIDE solo funciona para ADMIN en CERRADO/CANCELADO
- [x] Toda accion registra historial en solicitud_estado_historial

---

## M4 — Archivos

### Objetivo
Subida, descarga y eliminacion de archivos asociados a solicitudes y/o pagos. Storage local en dev.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| POST | `/solicitudes/{id}/archivos` | Subir archivo (multipart) | Privado |
| GET | `/archivos/{archivo_id}` | Descargar archivo | Privado |
| DELETE | `/archivos/{archivo_id}` | Eliminar archivo | Privado |

### Tests
- **Integracion:** Upload success, evidencia pago, tipo invalido, solicitud not found, unauthorized, download success/not found, delete success/not found, archivos en detalle

### Criterios de aceptacion
- [x] Upload almacena archivo y registra metadata en BD
- [x] Download retorna el archivo correcto
- [x] Delete elimina archivo y registro
- [x] Archivos se asocian a solicitud y opcionalmente a pago
- [x] Tipos permitidos: EVIDENCIA_PAGO, DOCUMENTO, OTROS

---

## M4.5 — Mejoras Incrementales

### Objetivo
UX mejorada: stepper visual del flujo, dropdowns con nombres, login fix, endpoints auxiliares.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| GET | `/promotores` | Lista promotores con nombre y tipo | Privado |
| GET | `/empleados?rol=X` | Lista empleados activos por rol | Privado |

### Componentes frontend
- `WorkflowStepper.tsx` — stepper horizontal de 5 fases
- Dropdowns de empleados por nombre en modales de asignacion
- Dropdown de promotores en creacion de solicitud
- `useAuth.ts` refactorizado a React Context + Provider

### Criterios de aceptacion
- [x] Stepper visual muestra fase actual con descripcion
- [x] Asignacion de gestor/medico muestra dropdown con nombres
- [x] Login redirige correctamente sin refresh manual

> **Nota**: M4.5 expandio permisos de OPERADOR/GESTOR. Esto fue corregido en M6 para alinear con docs/source/05_api_y_policy.md.

---

## M5 — Administracion

### Objetivo
CRUD de usuarios para ADMIN: listar, crear, editar, suspender/reactivar, resetear password. Auto-crea persona, empleado y medico_extra segun roles.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| GET | `/admin/usuarios` | Listar todos los usuarios con persona y roles | ADMIN |
| POST | `/admin/usuarios` | Crear usuario completo | ADMIN |
| PATCH | `/admin/usuarios/{user_id}` | Editar datos, cambiar roles, suspender/reactivar | ADMIN |
| POST | `/admin/usuarios/{user_id}/reset-password` | Resetear password e invalidar sesiones | ADMIN |

### Reglas de negocio
- **R5**: Copiar user_email a persona.email si persona.email es null
- **R11**: Crear MedicoExtra automaticamente con rol MEDICO
- **R13**: Invalidar sesiones al suspender usuario o resetear password
- Persona reutilizable por (tipo_documento, numero_documento)
- Admin no puede suspenderse a si mismo

### Tests (21 integracion)
- list_users, create_user (8 variantes), update_user (7 variantes), reset_password (4 variantes)

### Paginas frontend
- **Usuarios** (`/app/usuarios`) — tabla con modales CRUD, solo ADMIN

### Criterios de aceptacion
- [x] Solo ADMIN puede acceder a endpoints `/admin/*`
- [x] Crear usuario crea persona + user + roles + empleado + medico_extra en transaccion
- [x] Suspender usuario invalida sesiones existentes
- [x] Reset password cambia hash e invalida sesiones
- [x] Reutilizar persona existente por documento

---

## M5.5 — Mejoras Incrementales (Post-M5)

### Objetivo
4 mejoras funcionales: registro inline de promotor, promotor en detalle, separacion tipo/numero documento, tabla de permisos por rol.

### Cambios implementados

| ID | Cambio | Tipo |
|----|--------|------|
| 5.5.1 | Registro de promotor inline durante creacion de solicitud | Feature |
| 5.5.2 | Mostrar promotor en detalle de solicitud | Feature |
| 5.5.3 | Separar tipo_documento y numero_documento en detalle | Fix visual |
| 5.5.4 | Seccion de permisos por rol en pagina de usuarios | Feature |

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| POST | `/solicitudes` | Extendido: acepta `promotor` inline (tipo PERSONA/EMPRESA/OTROS) | Privado |

### Reglas de promotor
- 3 tipos: PERSONA (con persona FK), EMPRESA (razon_social), OTROS (nombre_promotor_otros)
- Promotor siempre opcional en solicitud
- Si tipo PERSONA con documento, reutiliza persona existente

### Archivos clave
- `backend/app/services/solicitud_service.py` — `create_promotor()`
- `frontend/src/pages/app/SolicitudNueva.tsx` — formulario con seccion promotor
- `frontend/src/pages/app/SolicitudDetalle.tsx` — muestra promotor asignado
- `frontend/src/pages/app/UsuariosLista.tsx` — tabla de permisos por rol

### Criterios de aceptacion
- [x] Crear solicitud con promotor inline (3 tipos) funciona
- [x] Promotor aparece en detalle de solicitud
- [x] Tipo y numero de documento se muestran por separado
- [x] Pagina de usuarios muestra tabla de permisos por rol

---

## M5.6 — Dashboard / Pagina de Inicio

### Objetivo
Convertir la pagina de inicio en un dashboard ligero: bienvenida personalizada, accesos rapidos por rol, solicitudes recientes.

### Componentes
1. **Bloque de bienvenida** — saludo con nombre + descripcion de rol
2. **Accesos rapidos** — botones de accion segun roles del usuario
3. **Solicitudes recientes** — tabla con ultimas 10 solicitudes relevantes al usuario

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| GET | `/solicitudes?mine=true` | Filtra solicitudes segun rol del usuario | Privado |

### Filtro `mine` por rol
- **ADMIN**: ve todas
- **OPERADOR**: ve solo las que creo (created_by)
- **GESTOR**: ve asignaciones vigentes como GESTOR
- **MEDICO**: ve asignaciones vigentes como MEDICO

### Archivos clave
- `frontend/src/pages/app/Inicio.tsx` — dashboard completo
- `backend/app/services/solicitud_service.py` — `list_solicitudes()` con parametro mine

### Criterios de aceptacion
- [x] Dashboard muestra bienvenida personalizada con nombre y descripcion de rol
- [x] Accesos rapidos correctos segun rol
- [x] Tabla de solicitudes recientes filtra por rol
- [x] mine=true funciona correctamente para los 4 roles

---

## M6 — Override, Auditoria y Modelo de Datos

### Objetivo
Override para ADMIN en estados terminales, campos de tracking en solicitud_cmep, tabla resultado_medico, correccion de POLICY alineada con docs/source.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| POST | `/solicitudes/{id}/override` | Override en CERRADO/CANCELADO | ADMIN |

### Override — sub-acciones
| Sub-accion | Descripcion | Payload |
|------------|-------------|---------|
| EDITAR_DATOS | Modificar tipo_atencion, lugar_atencion, comentario, servicio_id | `{campo: valor}` |
| CAMBIAR_GESTOR | Reasignar gestor vigente | `{persona_id_gestor: int}` |
| CAMBIAR_MEDICO | Reasignar medico vigente | `{persona_id_medico: int}` |
| REGISTRAR_PAGO | Registrar pago adicional | `{canal_pago, fecha_pago, monto, moneda}` |
| CERRAR | Establecer estado_atencion = ATENDIDO | `{}` |
| CANCELAR | Establecer estado_atencion = CANCELADO | `{}` |

Todo Override requiere `motivo` (string, no vacio). Genera auditoria doble en solicitud_estado_historial.

### Nuevos campos en solicitud_cmep
| Campo | Tipo | Cuando se establece |
|-------|------|---------------------|
| motivo_cancelacion | TEXT | Al cancelar |
| fecha_cierre | DATETIME | Al cerrar |
| cerrado_por | INT FK users | Al cerrar |
| fecha_cancelacion | DATETIME | Al cancelar |
| cancelado_por | INT FK users | Al cancelar |
| comentario_admin | TEXT | Notas admin (libre) |

### Nueva tabla: resultado_medico
Datos de evaluacion medica: diagnostico, resultado, observaciones, recomendaciones, estado_certificado (APROBADO/OBSERVADO).

### Correccion de POLICY
Se alinea POLICY con docs/source/05_api_y_policy.md:
- OPERADOR: -REGISTRAR_PAGO, -ASIGNAR_MEDICO, -CERRAR (solo registra y asigna gestor)
- GESTOR: -CERRAR en ASIGNADO_MEDICO (solo paga y asigna medico)
- Tests invertidos para reflejar permisos correctos

### Tests
- **Unit (7):** Tabla de verdad de derivar_estado_operativo
- **Integracion (12):** Happy path, override con sub-acciones, forbidden para no-ADMIN, cambiar gestor, historial, doble cancelar/cerrar

### Criterios de aceptacion
- [x] Override funciona solo para ADMIN en CERRADO/CANCELADO
- [x] 6 sub-acciones implementadas con auditoria doble
- [x] Motivo obligatorio (422 si vacio)
- [x] 6 nuevos campos de tracking en solicitud_cmep
- [x] Tabla resultado_medico creada
- [x] POLICY corregida: alineada con docs/source
- [x] 117 tests pasando

---

## M7 — Reportes Admin

### Objetivo
Pagina de reportes con KPIs, graficos temporales, distribucion por estado, rankings de promotores y equipo. Acceso exclusivo ADMIN.

### Endpoints backend
| Metodo | Ruta | Descripcion | Auth |
|--------|------|-------------|------|
| GET | `/admin/reportes` | Reporte agregado con filtros | ADMIN |

### Parametros query
| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| desde | date | hace 30 dias | Inicio del rango |
| hasta | date | hoy | Fin del rango |
| estado | string | null | Filtro de estado operativo |
| agrupacion | string | "mensual" | "semanal" o "mensual" |

### Respuesta: secciones
- **kpis**: solicitudes, cerradas, ingresos, ticket_promedio
- **series**: periodos con solicitudes e ingresos
- **distribucion**: cantidad por estado operativo
- **ranking_promotores**: promotor, clientes, solicitudes, porcentaje
- **ranking_equipo**: gestores, medicos, operadores con solicitudes y cerradas

### Notas tecnicas
- Estado operativo replicado como SQL CASE expression (no carga todos los registros)
- Ingresos: solo pagos con `validated_at IS NOT NULL`
- CSV export client-side desde data ya cargada
- Graficos con recharts (v3.7.0)

### Archivos clave
| Archivo | Descripcion |
|---------|-------------|
| `backend/app/services/reportes_service.py` | Logica SQL de agregacion |
| `backend/app/api/reportes.py` | Router GET /admin/reportes |
| `frontend/src/types/reportes.ts` | TypeScript interfaces |
| `frontend/src/pages/app/ReportesAdmin.tsx` | Pagina completa con filtros, KPIs, charts, rankings |

### Tests
- **Unit (7):** Tabla de verdad estado operativo
- **Integracion (8):** Sin auth 401, operador 403, admin 200, KPIs con datos, distribucion, filtro estado, ranking promotores, agrupacion semanal

### Paginas frontend
- **Reportes** (`/app/reportes-admin`) — solo visible para ADMIN en nav

### Criterios de aceptacion
- [x] Solo ADMIN puede acceder al endpoint y ver la pagina
- [x] KPIs, series, distribucion, rankings retornan datos correctos
- [x] Filtros de fecha, estado y agrupacion funcionan
- [x] Graficos renderizan correctamente con recharts
- [x] Export CSV funcional
- [x] 117 tests pasando, 0 errores TypeScript

---

## M8 — Despliegue Cloud (Pendiente)

### Objetivo
Desplegar CMEP a AWS: base de datos RDS MySQL, backend en App Runner, frontend en S3 + CloudFront, archivos en S3, secretos en Secrets Manager, monitoreo con CloudWatch.

### Plan detallado
Ver `M8_despliegue_cloud.md` para el plan completo con:
- Arquitectura AWS (8 componentes)
- 6 fases de ejecucion con checklists
- Separacion de tareas Claude (codigo) vs usuario (consola AWS)
- Estimacion de costos ($7-40/mes)
- Registro de riesgos y mitigaciones

### Fases
1. **Preparacion de codigo** (Claude) — Alembic, S3Storage, config prod, Dockerfile, healthcheck
2. **Infraestructura AWS** (Usuario) — RDS, Secrets Manager, App Runner, S3
3. **Deploy frontend** (Usuario) — Build, S3, CloudFront
4. **CORS y cookies** (Ambos) — Dominios, HTTPS, cross-origin
5. **Monitoreo** (Usuario) — CloudWatch, alarmas, EventBridge
6. **Smoke test** (Usuario) — Validacion end-to-end

### Criterios de aceptacion
- [ ] Backend corriendo en App Runner con RDS MySQL
- [ ] Frontend servido desde CloudFront con HTTPS
- [ ] Archivos almacenados en S3
- [ ] Login/sesiones funcionan cross-origin
- [ ] Seed ejecutado contra RDS
- [ ] Monitoreo y alarmas configurados
