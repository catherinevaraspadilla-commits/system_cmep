# Tablas del Sistema CMEP

El sistema cuenta con **19 tablas** organizadas en 5 dominios: identidad y acceso (6), personas y roles (5), catalogo (1), solicitudes y workflow (5), y archivos (2).

Base de datos: MySQL (produccion) / SQLite (desarrollo y tests).
ORM: SQLAlchemy 2.0 async.

---

## Identidad y Acceso

| # | Tabla | PK | Descripcion |
|---|-------|----|-------------|
| 1 | `personas` | persona_id | Registro unico por individuo (tipo_documento + numero_documento) |
| 2 | `users` | user_id | Cuenta de usuario del sistema (FK persona_id) |
| 3 | `user_role` | (user_id, user_role) | Roles asignados: ADMIN, OPERADOR, GESTOR, MEDICO |
| 4 | `user_permissions` | id | Permisos granulares por usuario (reservado) |
| 5 | `sessions` | session_id | Sesiones activas (cookie-based auth) |
| 6 | `password_resets` | reset_id | Tokens de reset de password |

## Personas y Roles de Negocio

| # | Tabla | PK | Descripcion |
|---|-------|----|-------------|
| 7 | `clientes` | persona_id | Persona registrada como cliente CMEP |
| 8 | `cliente_apoderado` | id | Relacion cliente-apoderado |
| 9 | `empleado` | empleado_id | Empleado con rol_empleado (GESTOR, MEDICO, OPERADOR) |
| 10 | `medico_extra` | persona_id | Datos adicionales de medicos (CMP, especialidad) |
| 11 | `promotores` | promotor_id | Promotor: PERSONA, EMPRESA u OTROS |

## Catalogo

| # | Tabla | PK | Descripcion |
|---|-------|----|-------------|
| 12 | `servicios` | servicio_id | Servicios CMEP con tarifa y moneda |

## Solicitudes y Workflow

| # | Tabla | PK | Descripcion |
|---|-------|----|-------------|
| 13 | `solicitud_cmep` | solicitud_id | Solicitud principal con estados, tarifa y campos de cierre/cancelacion |
| 14 | `solicitud_asignacion` | asignacion_id | Asignaciones de gestor/medico (vigente o historica) |
| 15 | `solicitud_estado_historial` | historial_id | Auditoria de cada cambio de campo o accion |
| 16 | `pago_solicitud` | pago_id | Pagos registrados por solicitud |
| 17 | `resultado_medico` | resultado_id | Resultados de evaluacion medica por solicitud |

## Archivos

| # | Tabla | PK | Descripcion |
|---|-------|----|-------------|
| 18 | `archivos` | archivo_id | Metadatos de archivos subidos (nombre, path, tipo) |
| 19 | `solicitud_archivo` | id | Relacion solicitud-archivo (opcionalmente ligada a un pago) |

---

## Estado operativo (derivado, no almacenado)

La solicitud no guarda un campo `estado_operativo`. Se calcula en tiempo real con esta precedencia:

```
CANCELADO > CERRADO > ASIGNADO_MEDICO > PAGADO > ASIGNADO_GESTOR > REGISTRADO
```

## Enums principales

| Enum | Valores | Usado en |
|------|---------|----------|
| EstadoAtencion | REGISTRADO, EN_PROCESO, ATENDIDO, OBSERVADO, CANCELADO | solicitud_cmep.estado_atencion |
| EstadoPago | PENDIENTE, PAGADO, OBSERVADO | solicitud_cmep.estado_pago |
| EstadoCertificado | APROBADO, OBSERVADO | resultado_medico.estado_certificado |
| RolAsignacion | OPERADOR, GESTOR, MEDICO | solicitud_asignacion.rol |
| TipoArchivo | EVIDENCIA_PAGO, DOCUMENTO, OTROS | archivos.tipo |
