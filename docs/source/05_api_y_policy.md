# Contrato de API (MVP) y Autorización por POLICY (CMEP)

## Objetivo

Esta sección define el **contrato mínimo pero completo** de endpoints para implementar el sistema CMEP sin ambigüedades: autenticación por sesión, gestión de solicitudes, acciones del workflow, administración de usuarios y carga/validación de archivos.

El backend **NO** persiste un campo único de `estado_operativo`; este estado se **deriva** estrictamente desde la BD con un orden de precedencia determinista.

## Fuente de verdad: estado operativo derivado (OBLIGATORIO)

El sistema opera sobre los estados:
`REGISTRADO`, `ASIGNADO_GESTOR`, `PAGADO`, `ASIGNADO_MEDICO`, `CERRADO`, `CANCELADO`

### Orden de precedencia

El primer estado cuya condición se cumpla es el asignado:
`CANCELADO` → `CERRADO` → `ASIGNADO_MEDICO` → `PAGADO` → `ASIGNADO_GESTOR` → `REGISTRADO`

### Reglas de derivación (resumen)

- **CANCELADO**: `solicitud_cmep.estado_atencion = 'CANCELADO'`
- **CERRADO**: `solicitud_cmep.estado_atencion = 'ATENDIDO'`
- **ASIGNADO_MEDICO**: `estado_pago='PAGADO'` y existe asignación vigente con rol `MEDICO`
- **PAGADO**: `estado_pago='PAGADO'` (aunque exista gestor vigente)
- **ASIGNADO_GESTOR**: existe asignación vigente con rol `GESTOR`
- **REGISTRADO**: ninguna regla anterior se cumple

## Modelo de autorización

### Regla principal

La autorización se determina por la **POLICY** usando la combinación:
```
(rol_usuario, estado_operativo_derivado) ⇒ acciones_permitidas
```

La POLICY es la **fuente de autorización** global.

### POLICY (fuente de verdad del backend)
```json
{
  "ADMIN": {
    "REGISTRADO": ["EDITAR_DATOS", "ASIGNAR_GESTOR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_GESTOR": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "PAGADO": ["EDITAR_DATOS", "ASIGNAR_MEDICO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_MEDICO": ["EDITAR_DATOS", "CERRAR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "CERRADO": ["OVERRIDE"],
    "CANCELADO": ["OVERRIDE"]
  },

  "OPERADOR": {
    "REGISTRADO": ["EDITAR_DATOS", "ASIGNAR_GESTOR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_GESTOR": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "PAGADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_MEDICO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "CERRADO": [],
    "CANCELADO": []
  },

  "GESTOR": {
    "REGISTRADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_GESTOR": ["EDITAR_DATOS", "REGISTRAR_PAGO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "PAGADO": ["EDITAR_DATOS", "ASIGNAR_MEDICO", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_MEDICO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "CERRADO": [],
    "CANCELADO": []
  },

  "MEDICO": {
    "REGISTRADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_GESTOR": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "PAGADO": ["EDITAR_DATOS", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "ASIGNADO_MEDICO": ["EDITAR_DATOS", "CERRAR", "CANCELAR", "CAMBIAR_GESTOR", "CAMBIAR_MEDICO"],
    "CERRADO": [],
    "CANCELADO": []
  }
}
```

### Convención: errores HTTP esperados (estándar CMEP)

Las fichas de acciones definen los códigos estándar:

- **403 Forbidden**: no permitido por POLICY
- **404 Not Found**: solicitud no existe
- **409 Conflict**: colisiones por condiciones de carrera o estado incompatible (ej. unique vigente, ya atendido/cancelado)
- **422 Unprocessable Entity**: violación de constraints, FK inválida, valores inválidos (monto/moneda, etc.)

## Convenciones generales de API

### Formato de respuesta estándar

#### Éxito
```json
{
  "ok": true,
  "data": { ... },
  "meta": { ... opcional ... }
}
```

#### Error
```json
{
  "ok": false,
  "error": {
    "code": "FORBIDDEN|NOT_FOUND|CONFLICT|VALIDATION_ERROR",
    "message": "mensaje humano",
    "details": { ... opcional ... }
  }
}
```

### Auditoría (mínimo)

Toda acción que cambie estado/relaciones de solicitud debe registrar evento en `solicitud_estado_historial` (campo anterior/nuevo), tal como se define en las fichas de acciones (p.ej. asignación/cambio/override/pago).

## Módulo Auth (sesiones)

### POST /auth/login

**Descripción**: Autentica por correo y contraseña. El correo es el identificador único de login.

**Request**:
```json
{
  "email": "user@dominio.com",
  "password": "********"
}
```

**Respuesta 200**:
```json
{
  "ok": true,
  "data": {
    "user": {
      "user_id": 123,
      "user_email": "user@dominio.com",
      "estado": "ACTIVO",
      "roles": ["ADMIN|OPERADOR|GESTOR|MEDICO"],
      "permissions_extra": ["..."],
      "display_name": "Nombre Apellido"
    }
  }
}
```

**Notas**:
- Si `users.estado = SUSPENDIDO` ⇒ rechazar login (403 o 422 según criterio del backend)
- Al login exitoso, la UI redirige a `/app`

### POST /auth/logout

**Descripción**: Invalida la sesión actual (elimina o marca expirada en BD).

**Respuesta 200**: `{"ok": true}`

### GET /auth/me

**Descripción**: Retorna usuario actual, roles y permisos efectivos.

**Respuesta 200**: Igual estructura `user` de login.

## Módulo Solicitudes (recurso central)

### GET /solicitudes

**Descripción**: Lista solicitudes. Es la página central para consultar y gestionar.

**Filtros**:
- Por defecto: solicitudes relacionadas al usuario según su rol
- Búsqueda por documento o nombres/apellidos
- Estado operativo derivado (opcional) para filtrar: `estado_operativo`

**Respuesta 200 (ejemplo)**:
```json
{
  "ok": true,
  "data": {
    "items": [
      {
        "solicitud_id": 999,
        "codigo": "CMEP-2026-0001",
        "cliente": { "doc": "DNI 12345678", "nombre": "..." },
        "apoderado": { "nombre": "...", "doc": "..." },
        "estado_operativo": "ASIGNADO_GESTOR",
        "operador": "Nombre Operador",
        "gestor": "Nombre Gestor",
        "medico": null,
        "promotor": "..."
      }
    ]
  },
  "meta": { "page": 1, "page_size": 20, "total": 1 }
}
```

### POST /solicitudes

**Descripción**: Registra una nueva solicitud (pantalla "Solicitudes -- Registrar").

**Request (campos del formulario)**:
```json
{
  "cliente": {
    "tipo_documento": "DNI|CE|PAS",
    "numero_documento": "12345678",
    "nombres": "....",
    "apellidos": "....",
    "celular": "...."
  },
  "apoderado": {
    "tipo_documento": "DNI|CE|PAS",
    "numero_documento": "...",
    "nombres": "...",
    "apellidos": "...",
    "celular": "..."
  },
  "promotor": {
    "tipo_promotor": "PERSONA|EMPRESA",
    "nombre_promotor": "..."
  },
  "atencion": {
    "tipo_atencion": "VIRTUAL|PRESENCIAL",
    "lugar_atencion": "..."
  }
}
```

**Notas**:
- Campos opcionales pueden quedar pendientes al registrar y completarse luego en detalle

**Respuesta 201**:
```json
{
  "ok": true,
  "data": { "solicitud_id": 999 }
}
```

### GET /solicitudes/{id}

**Descripción**: Devuelve detalle completo de solicitud, incluyendo:
- Estado operativo derivado (calculado server-side)
- Acciones permitidas (según POLICY) para pintar botones en UI
- Asignaciones vigentes (gestor/médico) y trazabilidad relevante
- Pagos registrados
- Archivos asociados

**Respuesta 200 (estructura mínima)**:
```json
{
  "ok": true,
  "data": {
    "solicitud": { ... },
    "estado_operativo": "PAGADO",
    "acciones_permitidas": ["ASIGNAR_MEDICO", "EDITAR_DATOS", ...],
    "asignaciones_vigentes": {
      "GESTOR": { "persona_id": 10, "nombre": "..." },
      "MEDICO": null
    },
    "pagos": [ ... ],
    "archivos": [ ... ],
    "historial": [ ... ]
  }
}
```

### PATCH /solicitudes/{id}

**Acción**: EDITAR_DATOS

**Descripción**: Edita campos de solicitud y/o datos pendientes. Debe registrar historial de cambios relevantes a nivel solicitud.

**Errores esperados**: 403/404/422 según estándar.

## Módulo Acciones del workflow (endpoints transaccionales)

Estas rutas representan las fichas de acciones del documento, con precondiciones, cambios en BD, auditoría y errores esperados.

### POST /solicitudes/{id}/asignar-gestor

**Acción**: ASIGNAR_GESTOR

**Precondiciones**:
- Permitido por POLICY
- La persona asignada cumple condición de "asignable" (empleado ACTIVO y rol GESTOR, equivalente a R10)

**Request**:
```json
{ "persona_id_gestor": 10 }
```

**Cambios en BD (transacción obligatoria)**:
Cerrar vigente e insertar nueva asignación vigente; registrar historial.

**Errores**: 403, 422, 409

### POST /solicitudes/{id}/cambiar-gestor

**Acción**: CAMBIAR_GESTOR

Mismo impacto que ASIGNAR_GESTOR (transacción: cerrar vigente e insertar nueva).

### POST /solicitudes/{id}/registrar-pago

**Acción**: REGISTRAR_PAGO

**Precondiciones**:
- Permitido por POLICY
- Validaciones mínimas: monto > 0 y moneda consistente con solicitud
- Evidencia/documento: opcional en MVP

**Request**:
```json
{
  "canal_pago": "YAPE|PLIN|TRANSFERENCIA|EFECTIVO",
  "fecha_pago": "2026-01-29",
  "monto": 100.00,
  "moneda": "PEN",
  "referencia_transaccion": "..."
}
```

**Cambios en BD**:
Insertar pago, validar (validated_by/validated_at), actualizar `estado_pago='PAGADO'`.

**Errores**: 403, 422, 404

### POST /solicitudes/{id}/asignar-medico

**Acción**: ASIGNAR_MEDICO

**Precondiciones**:
- Permitido por POLICY
- Requisito de flujo: `estado_pago='PAGADO'`

**Request**:
```json
{ "persona_id_medico": 55 }
```

**Cambios en BD (transacción obligatoria)**:
Cerrar vigente (si existe) e insertar nueva asignación vigente rol MEDICO.

**Errores**: 403, 422, 409

### POST /solicitudes/{id}/cambiar-medico

**Acción**: CAMBIAR_MEDICO

Análogo a ASIGNAR_MEDICO (transacción).

### POST /solicitudes/{id}/cerrar

**Acción**: CERRAR

Actualiza `solicitud_cmep.estado_atencion='ATENDIDO'`.

**Errores**: 403, 409 (ya atendido o cancelado)

### POST /solicitudes/{id}/cancelar

**Acción**: CANCELAR

Actualiza `solicitud_cmep.estado_atencion='CANCELADO'`.

**Errores**: 403, 409 (ya cancelado)

### POST /solicitudes/{id}/override

**Acción**: OVERRIDE (solo ADMIN en CERRADO o CANCELADO)

**Precondiciones**: Permitido por POLICY (ADMIN en CERRADO/CANCELADO).

**Descripción**: Permite ejecutar modificaciones equivalentes a otras acciones aunque el estado operativo normalmente bloquearía.

**Request**:
```json
{
  "motivo": "texto obligatorio",
  "accion": "EDITAR_DATOS|CAMBIAR_GESTOR|CAMBIAR_MEDICO|REGISTRAR_PAGO|...",
  "payload": { ... datos de la accion ... }
}
```

**Auditoría reforzada**:
Registrar evento explícito `override=true` con comentario obligatorio y registrar además cambios específicos como en EDITAR_DATOS.

**Errores**: 403, 422

## Módulo Archivos (MVP)

### POST /solicitudes/{id}/archivos

**Descripción**: Sube un archivo y lo asocia a la solicitud (y opcionalmente a un pago). En el flujo de pago, la evidencia es opcional.

**Request (multipart/form-data)**:
```
file=<binary>
tipo_archivo=EVIDENCIA_PAGO|DNI|OTRO
pago_id=<opcional>
```

**Respuesta 201**:
```json
{ "ok": true, "data": { "archivo_id": 777 } }
```

**Errores**: 403/404/422 estándar.

### GET /archivos/{archivo_id}

**Descripción**: Descarga/obtiene URL del archivo (según implementación S3 o storage).

**Respuesta 200**:
```json
{ "ok": true, "data": { "download_url": "..." } }
```

## Módulo Administración (Usuarios)

El menú principal V1 incluye `Usuarios` como opción en la app privada.

### GET /admin/users

Lista usuarios, roles, estado y permisos extra.

### POST /admin/users

Crea usuario (y si aplica, empleado/persona) respetando reglas:
- Normalizar email de login (lowercase + trim)
- Un usuario por persona; email único
- Si se crea empleado con usuario: copiar email a `persona.email` solo si es NULL

### PATCH /admin/users/{id}

Actualiza estado/roles/permisos extra (si estado pasa a no operativo, suspender y cerrar sesiones según implementación).

### POST /admin/users/{id}/reset-password

Inicia/ejecuta reset seguro (token con expiración, uso único, etc. según reglas de negocio internas del sistema).