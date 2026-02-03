# CMEP — Status del Proyecto

> Ultima actualizacion: 2026-02-03

---

## Resumen

Sistema de gestion de certificados medicos (CMEP). FastAPI + React 18 + SQLAlchemy 2.0 async + SQLite (dev).

- **Backend**: Python 3.13, FastAPI, sesiones server-side, RBAC con 4 roles
- **Frontend**: React 18, Vite, TypeScript, inline CSS, recharts para graficos
- **Tests**: 117 pasando (unit + integracion), 0 errores TypeScript
- **Roles**: ADMIN, OPERADOR, GESTOR, MEDICO

---

## Modulos implementados

| Modulo | Descripcion | Estado |
|--------|-------------|--------|
| M0 | Bootstrap proyecto (health, version) | Completo |
| M1 | Auth y sesiones (login, logout, me) | Completo |
| M2 | CRUD solicitudes (crear, listar, detalle, editar) | Completo |
| M3 | Workflow + POLICY + acciones (9 acciones, override) | Completo |
| M4 | Archivos (upload, download, delete) | Completo |
| M4.5 | Mejoras UX (stepper, dropdowns, login fix) | Completo |
| M5 | Administracion (CRUD usuarios, ADMIN only) | Completo |
| M5.5 | Mejoras post-M5 (promotor inline, permisos por rol) | Completo |
| M5.6 | Dashboard inicio (bienvenida, accesos rapidos, recientes) | Completo |
| M6 | Override + auditoria + modelo datos + correccion POLICY | Completo |
| M7 | Reportes admin (KPIs, graficos, rankings) | Completo |
| M8 | Despliegue Cloud (AWS: RDS, App Runner, S3, CloudFront) | Pendiente |

---

## Paginas frontend

| Ruta | Pagina | Acceso |
|------|--------|--------|
| `/login` | Login | Publico |
| `/app` | Dashboard inicio | Todos los roles |
| `/app/solicitudes` | Lista de solicitudes | Todos los roles |
| `/app/solicitudes/nueva` | Nueva solicitud | Todos los roles |
| `/app/solicitudes/:id` | Detalle de solicitud | Todos los roles |
| `/app/usuarios` | Gestion de usuarios | ADMIN |
| `/app/reportes-admin` | Reportes y metricas | ADMIN |

---

## Endpoints backend

### Auth
- `POST /auth/login` — login publico
- `POST /auth/logout` — invalidar sesion
- `GET /auth/me` — usuario actual + roles

### Solicitudes
- `POST /solicitudes` — crear (con promotor inline)
- `GET /solicitudes` — listar (filtros, paginacion, mine)
- `GET /solicitudes/{id}` — detalle
- `PATCH /solicitudes/{id}` — editar

### Acciones workflow
- `POST /solicitudes/{id}/asignar-gestor`
- `POST /solicitudes/{id}/cambiar-gestor`
- `POST /solicitudes/{id}/registrar-pago`
- `POST /solicitudes/{id}/asignar-medico`
- `POST /solicitudes/{id}/cambiar-medico`
- `POST /solicitudes/{id}/cerrar`
- `POST /solicitudes/{id}/cancelar`
- `POST /solicitudes/{id}/override` (ADMIN)

### Archivos
- `POST /solicitudes/{id}/archivos` — upload
- `GET /archivos/{id}` — download
- `DELETE /archivos/{id}` — delete

### Admin
- `GET /admin/usuarios` — listar usuarios
- `POST /admin/usuarios` — crear usuario
- `PATCH /admin/usuarios/{id}` — editar usuario
- `POST /admin/usuarios/{id}/reset-password`
- `GET /admin/reportes` — reportes agregados

### Auxiliares
- `GET /promotores` — lista promotores
- `GET /empleados?rol=X` — empleados por rol
- `GET /health` — healthcheck
- `GET /version` — version

---

## Tablas (19)

personas, users, user_role, user_permissions, sessions, password_resets, clientes, cliente_apoderado, empleado, medico_extra, promotores, servicios, solicitud_cmep, solicitud_asignacion, solicitud_estado_historial, pago_solicitud, archivos, solicitud_archivo, resultado_medico

Ver `07_tablas_del_sistema.md` para esquema completo.

---

## Pendiente

### M8 — Despliegue Cloud
- Plan detallado en `M8_despliegue_cloud.md`
- AWS: RDS MySQL, App Runner, S3, CloudFront, Secrets Manager, CloudWatch
- 6 fases: preparacion codigo, infra AWS, deploy frontend, CORS/cookies, monitoreo, smoke test
- Incluye tareas Claude (codigo) y tareas usuario (consola AWS)

### UX Redesign (completado)
- SolicitudDetalle reescrito como orquestador con 3 bloques de proceso (Gestion, Pago, Evaluacion)
- Bloques siempre visibles para todos los roles, botones deshabilitados con texto explicativo
- Colores como lenguaje de estado: verde=completado, azul=en curso, gris=pendiente
- Select funcional de estado_certificado (APROBADO/OBSERVADO) via PATCH
- Archivos nuevos: `solicitud/detailStyles.ts`, `detailHelpers.ts`, `BlockGestion.tsx`, `BlockPago.tsx`, `BlockEvaluacion.tsx`
- Backend: estado_certificado agregado a PATCH /solicitudes/{id}

### Fixes logicos y funcionales (completado)
- Historial de cambios: muestra nombre del usuario (no solo ID) via join users->personas
- Pago: campo `comentario` agregado a pago_solicitud (modelo, schema, API, frontend)
- Pago: "Tarifa" renombrado a "Tarifa regular" en BlockPago
- POLICY: ASIGNAR_MEDICO permitido en estado ASIGNADO_GESTOR (ADMIN, GESTOR)
- CERRAR: requiere al menos 1 pago registrado y medico asignado vigente
- Tipo atencion / lugar atencion movidos a BlockGestion (campos del gestor, con edicion inline)
- Servicio unico: seed actualizado a 1 registro ("Certificado Medico de Evaluacion Profesional", PEN 200)
- GET /servicios: nuevo endpoint para listar servicios disponibles
- SolicitudNueva: selector de servicio agregado (auto-selecciona si solo hay uno)
- Documentacion: `docs/system/datos_default_bd.md` con valores default de BD

### Mejoras funcionales posibles
- Flujo de resultado medico (usar tabla resultado_medico)
- Notificaciones por email
- Exportacion masiva de solicitudes
- Audit log de acciones de usuario
- Filtros avanzados en lista de solicitudes (rango de fechas, promotor)

### Deuda tecnica
- Migrar de SQLite a MySQL para desarrollo local (mas cercano a produccion)
- Alembic para migraciones incrementales (actualmente usa create_all)
- Enums reservados (EN_PROCESO, OBSERVADO en EstadoAtencion/EstadoPago) sin uso

---

## Documentacion (docs/claude/)

| Archivo | Contenido |
|---------|-----------|
| `claude.md` | Este archivo — status y pendientes |
| `00_mvp_one_pager.md` | Vision general del MVP |
| `01_architecture_summary.md` | Arquitectura tecnica, decisiones, seguridad |
| `02_module_specs.md` | Especificacion de todos los modulos M0-M7 |
| `03_task_backlog.md` | Backlog ejecutable de tareas (plan original M0-M5) |
| `04_testing_strategy.md` | Estrategia de testing (unit, integracion, smoke) |
| `05_ui_review_checkpoints.md` | Checkpoints de validacion UI por modulo |
| `06_risk_register.md` | Registro de 18 riesgos tecnicos identificados |
| `07_tablas_del_sistema.md` | Catalogo completo de 19 tablas con columnas y tipos |
| `M8_despliegue_cloud.md` | Plan detallado de despliegue AWS (6 fases, costos, riesgos) |
