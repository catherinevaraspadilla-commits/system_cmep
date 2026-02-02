# 2. Modelo de Datos

> Fuente de verdad: codigo SQLAlchemy en `backend/app/models/`.
> Enums definidos en `01_glosario_y_enums.md`.
> Ultima actualizacion: M6 (cierre/cancelacion, resultado_medico).

---

## 2.1 Resumen de tablas

| # | Tabla | Modelo (archivo) | PK | Dominio |
|---|-------|-------------------|----|---------|
| 1 | personas | persona.py | persona_id | Identidad |
| 2 | clientes | cliente.py | persona_id | Clientes |
| 3 | cliente_apoderado | cliente.py | id | Clientes |
| 4 | promotores | promotor.py | promotor_id | Promotores |
| 5 | empleado | empleado.py | empleado_id | Empleados |
| 6 | medico_extra | empleado.py | persona_id | Empleados |
| 7 | users | user.py | user_id | Autenticacion |
| 8 | user_role | user.py | (user_id, user_role) | Autenticacion |
| 9 | user_permissions | user.py | id | Autenticacion |
| 10 | sessions | user.py | session_id | Autenticacion |
| 11 | password_resets | user.py | reset_id | Autenticacion |
| 12 | servicios | servicio.py | servicio_id | Catalogo |
| 13 | solicitud_cmep | solicitud.py | solicitud_id | Solicitudes |
| 14 | solicitud_asignacion | solicitud.py | asignacion_id | Solicitudes |
| 15 | solicitud_estado_historial | solicitud.py | historial_id | Solicitudes |
| 16 | pago_solicitud | solicitud.py | pago_id | Solicitudes |
| 17 | archivos | solicitud.py | archivo_id | Solicitudes |
| 18 | solicitud_archivo | solicitud.py | id | Solicitudes |
| 19 | resultado_medico | solicitud.py | resultado_id | Solicitudes (M6) |

---

## 2.2 Definicion de tablas

### 2.2.1 personas

Entidad base de identidad. Toda persona fisica del sistema hereda de aqui.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| persona_id | INTEGER | NO | autoincrement | PK |
| tipo_documento | ENUM(TipoDocumento) | SI | — | DNI, CE, PASAPORTE, RUC |
| numero_documento | VARCHAR(30) | SI | — | |
| nombres | VARCHAR(150) | NO | — | |
| apellidos | VARCHAR(150) | NO | — | |
| fecha_nacimiento | DATE | SI | — | |
| email | VARCHAR(255) | SI | — | |
| celular_1 | VARCHAR(20) | SI | — | |
| celular_2 | VARCHAR(20) | SI | — | |
| telefono_fijo | VARCHAR(20) | SI | — | |
| direccion | VARCHAR(500) | SI | — | |
| comentario | TEXT | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(tipo_documento, numero_documento) — `uq_persona_documento`

---

### 2.2.2 clientes

Extiende persona como cliente. Relacion 1:1 con personas via PK compartido.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| persona_id | INTEGER | NO | — | PK, FK -> personas.persona_id |
| estado | ENUM(EstadoCliente) | NO | ACTIVO | ACTIVO, SUSPENDIDO |
| promotor_id | INTEGER | SI | — | FK -> promotores.promotor_id |
| comentario | TEXT | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Relationships:** persona (-> Persona, selectin)

---

### 2.2.3 cliente_apoderado

Relacion N:M entre clientes y sus apoderados (personas).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | INTEGER | NO | autoincrement | PK |
| cliente_id | INTEGER | NO | — | FK -> clientes.persona_id |
| apoderado_id | INTEGER | NO | — | FK -> personas.persona_id |
| estado | ENUM(EstadoApoderado) | NO | ACTIVO | ACTIVO, INACTIVO |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(cliente_id, apoderado_id) — `uq_cliente_apoderado`

---

### 2.2.4 promotores

Fuente/origen del cliente. Puede ser persona, empresa u otros.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| promotor_id | INTEGER | NO | autoincrement | PK |
| tipo_promotor | ENUM(TipoPromotor) | NO | — | PERSONA, EMPRESA, OTROS |
| fuente_promotor | VARCHAR(255) | SI | — | |
| persona_id | INTEGER | SI | — | FK -> personas.persona_id (solo si PERSONA) |
| razon_social | VARCHAR(255) | SI | — | Solo si EMPRESA |
| nombre_promotor_otros | VARCHAR(255) | SI | — | Solo si OTROS |
| ruc | VARCHAR(20) | SI | — | |
| email | VARCHAR(255) | SI | — | |
| celular_1 | VARCHAR(20) | SI | — | |
| comentario | TEXT | SI | — | |
| tarifa | NUMERIC(12,2) | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Relationships:** persona (-> Persona, selectin, solo tipo PERSONA)

---

### 2.2.5 empleado

Empleado del sistema. Una persona puede tener multiples registros de empleado con distintos roles.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| empleado_id | INTEGER | NO | autoincrement | PK |
| persona_id | INTEGER | NO | — | FK -> personas.persona_id |
| rol_empleado | ENUM(RolEmpleado) | NO | — | OPERADOR, GESTOR, MEDICO |
| estado_empleado | ENUM(EstadoEmpleado) | NO | ACTIVO | ACTIVO, SUSPENDIDO, VACACIONES, PERMISO |
| tipo_empleado | VARCHAR(100) | SI | — | |
| tarifa_empleado | NUMERIC(12,2) | SI | — | |
| comentario | TEXT | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(persona_id, rol_empleado) — `uq_empleado_persona_rol`
**Relationships:** persona (-> Persona, selectin)

---

### 2.2.6 medico_extra

Datos adicionales para personas con rol MEDICO. Relacion 1:1 con personas.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| persona_id | INTEGER | NO | — | PK, FK -> personas.persona_id |
| tipo_medico | VARCHAR(100) | SI | — | |
| cmp | VARCHAR(20) | SI | — | Colegio Medico del Peru |
| especialidad | VARCHAR(150) | SI | — | |
| comentario | TEXT | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

---

### 2.2.7 users

Cuenta de usuario del sistema. Relacion 1:1 con personas.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| user_id | INTEGER | NO | autoincrement | PK |
| persona_id | INTEGER | NO | — | FK -> personas.persona_id, UNIQUE |
| password_hash | VARCHAR(255) | NO | — | |
| user_email | VARCHAR(255) | NO | — | UNIQUE |
| estado | ENUM(EstadoUser) | NO | ACTIVO | ACTIVO, SUSPENDIDO |
| last_login_at | DATETIME | SI | — | |
| comentario | TEXT | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(persona_id), UNIQUE(user_email)
**Relationships:** roles (-> UserRole[], selectin), permissions (-> UserPermission[], selectin)

---

### 2.2.8 user_role

Roles asignados a un usuario. PK compuesta.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| user_id | INTEGER | NO | — | PK, FK -> users.user_id |
| user_role | ENUM(UserRoleEnum) | NO | — | PK. ADMIN, OPERADOR, GESTOR, MEDICO |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(user_id, user_role) — `uq_user_role`

---

### 2.2.9 user_permissions

Permisos granulares por usuario.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | INTEGER | NO | autoincrement | PK |
| user_id | INTEGER | NO | — | FK -> users.user_id |
| permission_code | VARCHAR(100) | NO | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(user_id, permission_code) — `uq_user_permission`

---

### 2.2.10 sessions

Sesiones activas de usuario.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| session_id | VARCHAR(64) | NO | uuid4().hex | PK |
| user_id | INTEGER | NO | — | FK -> users.user_id |
| created_at | DATETIME | NO | utcnow | |
| expires_at | DATETIME | NO | — | |
| last_seen_at | DATETIME | SI | — | |

---

### 2.2.11 password_resets

Tokens de restablecimiento de contrasena.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| reset_id | INTEGER | NO | autoincrement | PK |
| user_id | INTEGER | NO | — | FK -> users.user_id |
| token_hash | VARCHAR(255) | NO | — | |
| expires_at | DATETIME | NO | — | |
| used_at | DATETIME | SI | — | |
| created_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |

---

### 2.2.12 servicios

Catalogo de servicios con tarifa.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| servicio_id | INTEGER | NO | autoincrement | PK |
| descripcion_servicio | VARCHAR(255) | NO | — | |
| caracteristicas_servicio | TEXT | SI | — | |
| tarifa_servicio | NUMERIC(12,2) | NO | — | |
| moneda_tarifa | VARCHAR(3) | NO | PEN | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

---

### 2.2.13 solicitud_cmep

Tabla principal de solicitudes de certificado medico.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| solicitud_id | INTEGER | NO | autoincrement | PK |
| codigo | VARCHAR(20) | SI | — | UNIQUE. Formato CMEP-YYYY-NNNN |
| cliente_id | INTEGER | NO | — | FK -> clientes.persona_id |
| apoderado_id | INTEGER | SI | — | FK -> personas.persona_id |
| servicio_id | INTEGER | SI | — | FK -> servicios.servicio_id |
| promotor_id | INTEGER | SI | — | FK -> promotores.promotor_id |
| estado_atencion | ENUM(EstadoAtencion) | NO | REGISTRADO | REGISTRADO, EN_PROCESO, ATENDIDO, OBSERVADO, CANCELADO |
| estado_pago | ENUM(EstadoPago) | NO | PENDIENTE | PENDIENTE, PAGADO, OBSERVADO |
| estado_certificado | ENUM(EstadoCertificado) | SI | — | APROBADO, OBSERVADO |
| tarifa_monto | NUMERIC(12,2) | SI | — | Snapshot al crear |
| tarifa_moneda | ENUM(TarifaMoneda) | SI | — | PEN, USD |
| tarifa_fuente | ENUM(TarifaFuente) | SI | — | SERVICIO, OVERRIDE |
| tipo_atencion | VARCHAR(20) | SI | — | |
| lugar_atencion | VARCHAR(255) | SI | — | |
| comentario | TEXT | SI | — | |
| motivo_cancelacion | TEXT | SI | — | **(M6)** Motivo al cancelar |
| fecha_cierre | DATETIME | SI | — | **(M6)** Timestamp de cierre |
| cerrado_por | INTEGER | SI | — | **(M6)** FK -> users.user_id |
| fecha_cancelacion | DATETIME | SI | — | **(M6)** Timestamp de cancelacion |
| cancelado_por | INTEGER | SI | — | **(M6)** FK -> users.user_id |
| comentario_admin | TEXT | SI | — | **(M6)** Comentario de override admin |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Constraints:** UNIQUE(codigo)
**FKs M6:** cerrado_por -> users.user_id, cancelado_por -> users.user_id
**Relationships:** cliente, apoderado, servicio, promotor, asignaciones[], historial[], pagos[], archivos_rel[], resultados_medicos[]

---

### 2.2.14 solicitud_asignacion

Asignaciones de personal a solicitudes (gestor, medico, operador).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| asignacion_id | INTEGER | NO | autoincrement | PK |
| solicitud_id | INTEGER | NO | — | FK -> solicitud_cmep.solicitud_id |
| persona_id | INTEGER | NO | — | FK -> personas.persona_id |
| rol | ENUM(RolAsignacion) | NO | — | OPERADOR, GESTOR, MEDICO |
| es_vigente | BOOLEAN | NO | true | |
| asignado_por | INTEGER | SI | — | FK -> users.user_id |
| fecha_asignacion | DATETIME | NO | utcnow | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

---

### 2.2.15 solicitud_estado_historial

Auditoria de cambios de estado/campos en solicitudes.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| historial_id | INTEGER | NO | autoincrement | PK |
| solicitud_id | INTEGER | NO | — | FK -> solicitud_cmep.solicitud_id |
| campo | VARCHAR(100) | NO | — | Nombre del campo modificado |
| valor_anterior | TEXT | SI | — | |
| valor_nuevo | TEXT | SI | — | |
| cambiado_por | INTEGER | SI | — | FK -> users.user_id |
| cambiado_en | DATETIME | NO | utcnow | |
| comentario | TEXT | SI | — | |

---

### 2.2.16 pago_solicitud

Pagos registrados contra solicitudes.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| pago_id | INTEGER | NO | autoincrement | PK |
| solicitud_id | INTEGER | NO | — | FK -> solicitud_cmep.solicitud_id |
| canal_pago | VARCHAR(50) | SI | — | |
| fecha_pago | DATE | SI | — | |
| monto | NUMERIC(12,2) | NO | — | |
| moneda | VARCHAR(3) | NO | PEN | |
| referencia_transaccion | VARCHAR(255) | SI | — | |
| validated_by | INTEGER | SI | — | FK -> users.user_id |
| validated_at | DATETIME | SI | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

---

### 2.2.17 archivos

Registro de archivos almacenados en storage.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| archivo_id | INTEGER | NO | autoincrement | PK |
| nombre_original | VARCHAR(255) | NO | — | |
| nombre_storage | VARCHAR(255) | NO | — | |
| tipo | ENUM(TipoArchivo) | NO | — | EVIDENCIA_PAGO, DOCUMENTO, OTROS |
| mime_type | VARCHAR(100) | SI | — | |
| tamano_bytes | INTEGER | SI | — | |
| storage_path | VARCHAR(500) | NO | — | |
| created_by | INTEGER | SI | — | |
| updated_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

---

### 2.2.18 solicitud_archivo

Tabla puente entre solicitudes, archivos y opcionalmente pagos.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | INTEGER | NO | autoincrement | PK |
| solicitud_id | INTEGER | NO | — | FK -> solicitud_cmep.solicitud_id |
| archivo_id | INTEGER | NO | — | FK -> archivos.archivo_id |
| pago_id | INTEGER | SI | — | FK -> pago_solicitud.pago_id |
| created_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |

---

### 2.2.19 resultado_medico (M6)

Resultados de evaluacion medica asociados a una solicitud.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| resultado_id | INTEGER | NO | autoincrement | PK |
| solicitud_id | INTEGER | NO | — | FK -> solicitud_cmep.solicitud_id |
| medico_id | INTEGER | NO | — | FK -> personas.persona_id |
| fecha_evaluacion | DATE | SI | — | |
| diagnostico | TEXT | SI | — | |
| resultado | VARCHAR(50) | SI | — | Ej: APTO, NO_APTO, OBSERVADO |
| observaciones | TEXT | SI | — | |
| recomendaciones | TEXT | SI | — | |
| estado_certificado | ENUM(EstadoCertificado) | SI | — | APROBADO, OBSERVADO |
| created_by | INTEGER | SI | — | |
| created_at | DATETIME | NO | utcnow | |
| updated_at | DATETIME | SI | utcnow/onupdate | |

**Relationships:** solicitud (-> SolicitudCmep), medico (-> Persona, selectin)

---

## 2.3 Relaciones principales

```
personas 1──1 clientes
personas 1──N cliente_apoderado (como apoderado)
clientes 1──N cliente_apoderado (como cliente)
personas 1──1 users
personas 1──N empleado
personas 1──1 medico_extra
personas 1──N promotores (nullable, solo tipo PERSONA)

users 1──N user_role
users 1──N user_permissions
users 1──N sessions
users 1──N password_resets

clientes    1──N solicitud_cmep
promotores  1──N solicitud_cmep
servicios   1──N solicitud_cmep

solicitud_cmep 1──N solicitud_asignacion
solicitud_cmep 1──N solicitud_estado_historial
solicitud_cmep 1──N pago_solicitud
solicitud_cmep 1──N solicitud_archivo
solicitud_cmep 1──N resultado_medico          (M6)

archivos 1──N solicitud_archivo
pago_solicitud 1──N solicitud_archivo

users -> solicitud_cmep.cerrado_por             (M6)
users -> solicitud_cmep.cancelado_por           (M6)
```

---

## 2.4 Notas

1. **estado_operativo** es derivado en runtime (no almacenado). Se calcula con prioridad:
   CANCELADO > CERRADO > ASIGNADO_MEDICO > PAGADO > ASIGNADO_GESTOR > REGISTRADO.

2. **Campos de auditoria** (`created_by`, `updated_by`, `created_at`, `updated_at`) estan presentes en casi todas las tablas. `sessions` y `solicitud_estado_historial` son excepciones parciales.

3. **Enums reservados** (definidos pero no asignados actualmente por ninguna accion):
   - `EstadoAtencion.EN_PROCESO`, `EstadoAtencion.OBSERVADO`
   - `EstadoPago.OBSERVADO`
   - `EstadoCertificado.APROBADO`, `EstadoCertificado.OBSERVADO` (columna existe en solicitud_cmep, nunca se establece)

4. **Todas las FK** usan `onupdate=RESTRICT, ondelete=RESTRICT`.

5. **Lazy loading**: Todas las relationships usan `lazy="selectin"`.
