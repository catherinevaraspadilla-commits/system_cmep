# 07 — Catalogo Completo de Tablas del Sistema CMEP

Generado desde los modelos SQLAlchemy en `backend/app/models/`.

---

## 1. personas

**Archivo**: `backend/app/models/persona.py`
**Descripcion**: Entidad base de identidad. Toda persona fisica del sistema (clientes, empleados, apoderados, promotores persona) tiene un registro aqui.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| persona_id | INTEGER | No | autoincrement | PK |
| tipo_documento | ENUM(DNI,CE,PASAPORTE,RUC) | Si | - | native_enum=True |
| numero_documento | VARCHAR(30) | Si | - | |
| nombres | VARCHAR(150) | No | - | |
| apellidos | VARCHAR(150) | No | - | |
| fecha_nacimiento | DATE | Si | - | |
| email | VARCHAR(255) | Si | - | |
| celular_1 | VARCHAR(20) | Si | - | |
| celular_2 | VARCHAR(20) | Si | - | |
| telefono_fijo | VARCHAR(20) | Si | - | |
| direccion | VARCHAR(500) | Si | - | |
| comentario | TEXT | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Constraints**: UNIQUE(tipo_documento, numero_documento) — `uq_persona_documento`

---

## 2. users

**Archivo**: `backend/app/models/user.py`
**Descripcion**: Cuentas de usuario del sistema. Cada usuario esta vinculado a una persona.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| user_id | INTEGER | No | autoincrement | PK |
| persona_id | INTEGER | No | - | FK -> personas.persona_id, UNIQUE |
| password_hash | VARCHAR(255) | No | - | |
| user_email | VARCHAR(255) | No | - | UNIQUE |
| estado | ENUM(ACTIVO,SUSPENDIDO) | No | ACTIVO | native_enum=True |
| last_login_at | DATETIME | Si | - | |
| comentario | TEXT | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Relationships**: roles (-> user_role), permissions (-> user_permissions)

---

## 3. user_role

**Archivo**: `backend/app/models/user.py`
**Descripcion**: Roles asignados a cada usuario. PK compuesta.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| user_id | INTEGER | No | - | PK, FK -> users.user_id |
| user_role | ENUM(ADMIN,OPERADOR,GESTOR,MEDICO) | No | - | PK, native_enum=True |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Constraints**: UNIQUE(user_id, user_role) — `uq_user_role`

---

## 4. user_permissions

**Archivo**: `backend/app/models/user.py`
**Descripcion**: Permisos extra asignados individualmente a usuarios.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | INTEGER | No | autoincrement | PK |
| user_id | INTEGER | No | - | FK -> users.user_id |
| permission_code | VARCHAR(100) | No | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Constraints**: UNIQUE(user_id, permission_code) — `uq_user_permission`

---

## 5. sessions

**Archivo**: `backend/app/models/user.py`
**Descripcion**: Sesiones activas de usuario (server-side).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| session_id | VARCHAR(64) | No | uuid4().hex | PK |
| user_id | INTEGER | No | - | FK -> users.user_id |
| created_at | DATETIME | No | utcnow | |
| expires_at | DATETIME | No | - | |
| last_seen_at | DATETIME | Si | - | |

---

## 6. password_resets

**Archivo**: `backend/app/models/user.py`
**Descripcion**: Tokens de reseteo de contrasena.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| reset_id | INTEGER | No | autoincrement | PK |
| user_id | INTEGER | No | - | FK -> users.user_id |
| token_hash | VARCHAR(255) | No | - | |
| expires_at | DATETIME | No | - | |
| used_at | DATETIME | Si | - | |
| created_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |

---

## 7. clientes

**Archivo**: `backend/app/models/cliente.py`
**Descripcion**: Clientes del sistema. PK es FK a personas (patron 1:1).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| persona_id | INTEGER | No | - | PK, FK -> personas.persona_id |
| estado | ENUM(ACTIVO,SUSPENDIDO) | No | ACTIVO | |
| promotor_id | INTEGER | Si | - | FK -> promotores.promotor_id |
| comentario | TEXT | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Relationships**: persona (-> personas)

---

## 8. cliente_apoderado

**Archivo**: `backend/app/models/cliente.py`
**Descripcion**: Relacion M:N entre clientes y sus apoderados (representantes legales).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | INTEGER | No | autoincrement | PK |
| cliente_id | INTEGER | No | - | FK -> clientes.persona_id |
| apoderado_id | INTEGER | No | - | FK -> personas.persona_id |
| estado | ENUM(ACTIVO,INACTIVO) | No | ACTIVO | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Constraints**: UNIQUE(cliente_id, apoderado_id) — `uq_cliente_apoderado`

---

## 9. empleado

**Archivo**: `backend/app/models/empleado.py`
**Descripcion**: Empleados operativos del sistema (operadores, gestores, medicos).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| empleado_id | INTEGER | No | autoincrement | PK |
| persona_id | INTEGER | No | - | FK -> personas.persona_id |
| rol_empleado | ENUM(OPERADOR,GESTOR,MEDICO) | No | - | |
| estado_empleado | ENUM(ACTIVO,SUSPENDIDO,VACACIONES,PERMISO) | No | ACTIVO | |
| tipo_empleado | VARCHAR(100) | Si | - | |
| tarifa_empleado | DECIMAL(12,2) | Si | - | |
| comentario | TEXT | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Constraints**: UNIQUE(persona_id, rol_empleado) — `uq_empleado_persona_rol`
**Relationships**: persona (-> personas)

---

## 10. medico_extra

**Archivo**: `backend/app/models/empleado.py`
**Descripcion**: Datos adicionales para empleados con rol MEDICO. PK es FK a personas.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| persona_id | INTEGER | No | - | PK, FK -> personas.persona_id |
| tipo_medico | VARCHAR(100) | Si | - | |
| cmp | VARCHAR(20) | Si | - | Colegio Medico del Peru |
| especialidad | VARCHAR(150) | Si | - | |
| comentario | TEXT | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

---

## 11. promotores

**Archivo**: `backend/app/models/promotor.py`
**Descripcion**: Promotores/referentes que traen clientes. Pueden ser persona, empresa u otros.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| promotor_id | INTEGER | No | autoincrement | PK |
| tipo_promotor | ENUM(PERSONA,EMPRESA,OTROS) | No | - | |
| fuente_promotor | VARCHAR(255) | Si | - | | notarias, abogados, clientes referentes, etc.
| persona_id | INTEGER | Si | - | FK -> personas.persona_id (solo si PERSONA) |
| razon_social | VARCHAR(255) | Si | - | Solo si EMPRESA |
| nombre_promotor_otros | VARCHAR(255) | Si | - | Solo si OTROS |
| ruc | VARCHAR(20) | Si | - | |
| email | VARCHAR(255) | Si | - | |
| celular_1 | VARCHAR(20) | Si | - | |
| comentario | TEXT | Si | - | |
| tarifa | DECIMAL(12,2) | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Relationships**: persona (-> personas, nullable)

---

## 12. servicios

**Archivo**: `backend/app/models/servicio.py`
**Descripcion**: Catalogo de servicios con tarifa.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| servicio_id | INTEGER | No | autoincrement | PK |
| descripcion_servicio | VARCHAR(255) | No | - | |
| caracteristicas_servicio | TEXT | Si | - | |
| tarifa_servicio | DECIMAL(12,2) | No | - | |
| moneda_tarifa | VARCHAR(3) | No | PEN | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

---

## 13. solicitud_cmep

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Tabla central de solicitudes de certificado medico.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| solicitud_id | INTEGER | No | autoincrement | PK |
| codigo | VARCHAR(20) | Si | - | UNIQUE. Formato CMEP-YYYY-NNNN |
| cliente_id | INTEGER | No | - | FK -> clientes.persona_id |
| apoderado_id | INTEGER | Si | - | FK -> personas.persona_id |
| servicio_id | INTEGER | Si | - | FK -> servicios.servicio_id |
| promotor_id | INTEGER | Si | - | FK -> promotores.promotor_id |
| estado_atencion | ENUM(REGISTRADO,EN_PROCESO,ATENDIDO,OBSERVADO,CANCELADO) | No | REGISTRADO | |
| estado_pago | ENUM(PENDIENTE,PAGADO,OBSERVADO) | No | PENDIENTE | |
| estado_certificado | ENUM(APROBADO,OBSERVADO) | Si | - | |
| tarifa_monto | DECIMAL(12,2) | Si | - | Snapshot de tarifa al momento |
| tarifa_moneda | ENUM(PEN,USD) | Si | - | |
| tarifa_fuente | ENUM(SERVICIO,OVERRIDE) | Si | - | |
| tipo_atencion | VARCHAR(20) | Si | - | VIRTUAL, PRESENCIAL |
| lugar_atencion | VARCHAR(255) | Si | - | |
| comentario | TEXT | Si | - | Comentario general |
| motivo_cancelacion | TEXT | Si | - | **NUEVO M6** |
| fecha_cierre | DATETIME | Si | - | **NUEVO M6** |
| cerrado_por | INTEGER | Si | - | **NUEVO M6** FK -> users.user_id |
| fecha_cancelacion | DATETIME | Si | - | **NUEVO M6** |
| cancelado_por | INTEGER | Si | - | **NUEVO M6** FK -> users.user_id |
| comentario_admin | TEXT | Si | - | **NUEVO M6** |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Nota**: `estado_operativo` NO es columna — se deriva en runtime desde estado_atencion + estado_pago + asignaciones vigentes.

**Relationships**: cliente, apoderado, servicio, promotor, asignaciones, historial, pagos, archivos_rel, resultados_medicos

---

## 14. solicitud_asignacion

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Asignaciones de personal (gestor, medico) a solicitudes.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| asignacion_id | INTEGER | No | autoincrement | PK |
| solicitud_id | INTEGER | No | - | FK -> solicitud_cmep.solicitud_id |
| persona_id | INTEGER | No | - | FK -> personas.persona_id |
| rol | ENUM(OPERADOR,GESTOR,MEDICO) | No | - | |
| es_vigente | BOOLEAN | No | True | Solo 1 vigente por (solicitud, rol) |
| asignado_por | INTEGER | Si | - | FK -> users.user_id |
| fecha_asignacion | DATETIME | No | utcnow | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Relationships**: solicitud (-> solicitud_cmep), persona (-> personas)

---

## 15. solicitud_estado_historial

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Registro de auditoria de todos los cambios en solicitudes.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| historial_id | INTEGER | No | autoincrement | PK |
| solicitud_id | INTEGER | No | - | FK -> solicitud_cmep.solicitud_id |
| campo | VARCHAR(100) | No | - | Nombre del campo modificado |
| valor_anterior | TEXT | Si | - | |
| valor_nuevo | TEXT | Si | - | |
| cambiado_por | INTEGER | Si | - | FK -> users.user_id |
| cambiado_en | DATETIME | No | utcnow | |
| comentario | TEXT | Si | - | Contexto adicional (motivo override, etc.) |

**Relationships**: solicitud (-> solicitud_cmep)

---

## 16. pago_solicitud

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Pagos registrados para solicitudes.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| pago_id | INTEGER | No | autoincrement | PK |
| solicitud_id | INTEGER | No | - | FK -> solicitud_cmep.solicitud_id |
| canal_pago | VARCHAR(50) | Si | - | Ej: YAPE, BCP, EFECTIVO |
| fecha_pago | DATE | Si | - | |
| monto | DECIMAL(12,2) | No | - | |
| moneda | VARCHAR(3) | No | PEN | |
| referencia_transaccion | VARCHAR(255) | Si | - | |
| validated_by | INTEGER | Si | - | FK -> users.user_id |
| validated_at | DATETIME | Si | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Relationships**: solicitud (-> solicitud_cmep)

---

## 17. archivos

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Registro de archivos subidos al sistema.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| archivo_id | INTEGER | No | autoincrement | PK |
| nombre_original | VARCHAR(255) | No | - | Nombre del archivo subido |
| nombre_storage | VARCHAR(255) | No | - | Nombre en storage |
| tipo | ENUM(EVIDENCIA_PAGO,DOCUMENTO,OTROS) | No | - | |
| mime_type | VARCHAR(100) | Si | - | |
| tamano_bytes | INTEGER | Si | - | |
| storage_path | VARCHAR(500) | No | - | |
| created_by | INTEGER | Si | - | |
| updated_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

---

## 18. solicitud_archivo

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Tabla puente: asocia archivos a solicitudes (y opcionalmente a pagos).

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | INTEGER | No | autoincrement | PK |
| solicitud_id | INTEGER | No | - | FK -> solicitud_cmep.solicitud_id |
| archivo_id | INTEGER | No | - | FK -> archivos.archivo_id |
| pago_id | INTEGER | Si | - | FK -> pago_solicitud.pago_id |
| created_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |

**Relationships**: solicitud (-> solicitud_cmep), archivo (-> archivos)

---

## 19. resultado_medico (NUEVA — M6)

**Archivo**: `backend/app/models/solicitud.py`
**Descripcion**: Resultados de evaluaciones medicas realizadas por los medicos asignados.

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| resultado_id | INTEGER | No | autoincrement | PK |
| solicitud_id | INTEGER | No | - | FK -> solicitud_cmep.solicitud_id |
| medico_id | INTEGER | No | - | FK -> personas.persona_id |
| fecha_evaluacion | DATE | Si | - | |
| diagnostico | TEXT | Si | - | |
| resultado | VARCHAR(50) | Si | - | APTO, NO_APTO, OBSERVADO |
| observaciones | TEXT | Si | - | |
| recomendaciones | TEXT | Si | - | |
| estado_certificado | ENUM(APROBADO,OBSERVADO) | Si | - | |
| created_by | INTEGER | Si | - | |
| created_at | DATETIME | No | utcnow | |
| updated_at | DATETIME | Si | utcnow (onupdate) | |

**Relationships**: solicitud (-> solicitud_cmep), medico (-> personas)

---

## Resumen de enums utilizados

| Enum | Valores | Usado en |
|------|---------|----------|
| TipoDocumento | DNI, CE, PASAPORTE, RUC | personas.tipo_documento |
| EstadoCliente | ACTIVO, SUSPENDIDO | clientes.estado |
| EstadoApoderado | ACTIVO, INACTIVO | cliente_apoderado.estado |
| TipoPromotor | PERSONA, EMPRESA, OTROS | promotores.tipo_promotor |
| RolEmpleado | OPERADOR, GESTOR, MEDICO | empleado.rol_empleado |
| EstadoEmpleado | ACTIVO, SUSPENDIDO, VACACIONES, PERMISO | empleado.estado_empleado |
| EstadoUser | ACTIVO, SUSPENDIDO | users.estado |
| UserRoleEnum | ADMIN, OPERADOR, GESTOR, MEDICO | user_role.user_role |
| EstadoPago | PENDIENTE, PAGADO, OBSERVADO* | solicitud_cmep.estado_pago |
| EstadoAtencion | REGISTRADO, EN_PROCESO*, ATENDIDO, OBSERVADO*, CANCELADO | solicitud_cmep.estado_atencion |
| EstadoCertificado | APROBADO, OBSERVADO | solicitud_cmep.estado_certificado, resultado_medico.estado_certificado |
| TarifaMoneda | PEN, USD | solicitud_cmep.tarifa_moneda |
| TarifaFuente | SERVICIO, OVERRIDE | solicitud_cmep.tarifa_fuente |
| RolAsignacion | OPERADOR, GESTOR, MEDICO | solicitud_asignacion.rol |
| TipoArchivo | EVIDENCIA_PAGO, DOCUMENTO, OTROS | archivos.tipo |

(*) Valores reservados — definidos en enum pero no asignados por ninguna accion en la implementacion actual.
