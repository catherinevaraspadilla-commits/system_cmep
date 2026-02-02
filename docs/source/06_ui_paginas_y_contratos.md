# Definición de Páginas del Sistema CMEP (Especificación UI + Contrato API)

## Convenciones Técnicas (Frontend)

### Ruteo
- Páginas públicas: `/` (Landing), `/login`
- App privada:
  - `/app`
  - `/app/inicio`
  - `/app/solicitudes`
  - `/app/solicitudes/nueva`
  - `/app/solicitudes/{id}`
  - `/app/reportes`
  - `/app/usuarios`

### Regla de acceso
- Toda ruta `/app/*` requiere sesión válida
- Si `GET /auth/me` falla (401/403) → redirigir a `/login`
- Usuario `SUSPENDIDO` → forzar logout y bloquear app

### Contrato UI para permisos
- El frontend NO calcula permisos
- Renderiza acciones desde `acciones_permitidas`
- Botones solo visibles si la acción existe
- Respuestas backend:
  - 403 → modal "No autorizado"
  - 409 → "La solicitud cambió, refresca"
  - 422 → validaciones por campo

## DTOs mínimos esperados (UI Contracts)

### UserDTO
Objeto esperado desde `/auth/me`

{
  user_id: number,
  user_email: string,
  estado: "ACTIVO" | "SUSPENDIDO",
  roles: ["ADMIN", "OPERADOR", "GESTOR", "MEDICO"],
  permissions_extra: string[],
  display_name: string
}

### SolicitudListItemDTO
Elemento retornado por `GET /solicitudes`

{
  solicitud_id: number,
  codigo: string,
  cliente_doc: string,
  cliente_nombre: string,
  apoderado_nombre: string | null,
  estado_operativo: "REGISTRADO" | "ASIGNADO_GESTOR" | "PAGADO" | "ASIGNADO_MEDICO" | "CERRADO" | "CANCELADO",
  operador: string | null,
  gestor: string | null,
  medico: string | null,
  promotor: string | null
}

### SolicitudDetailDTO (extracto)

{
  solicitud: object,
  estado_operativo: string,
  acciones_permitidas: string[],
  asignaciones_vigentes: {
    GESTOR: object | null,
    MEDICO: object | null
  },
  pagos: array,
  archivos: array,
  historial: array
}

## Páginas Públicas

### Landing
Propósito:
- Página informativa del servicio CMEP

Contenido:
- Descripción del servicio
- Beneficios
- Contacto
- Botón Login

Acciones:
- Redirigir a `/login`

### Login
Campos:
- Email
- Contraseña

Contrato API:
- POST /auth/login
- GET /auth/me

Estados UI:
- 401 / 422 → Credenciales inválidas
- 403 → Usuario suspendido

Acciones:
- Login
- Redirigir a `/app`

## Páginas Privadas (App)

### Menú Principal
Opciones:
- Inicio
- Solicitudes
- Reportes
- Usuarios

Reglas:
- Usuarios solo ADMIN
- Reportes solo ADMIN (MVP)

### Inicio (Mi trabajo de hoy)
Implementación:
- Usa GET /solicitudes
- Sin endpoint propio

Bloques por rol:
- OPERADOR → registradas / pendientes
- GESTOR → asignadas / pendientes de pago
- MEDICO → asignadas
- ADMIN → vista global

### Solicitudes – Lista
Fuente:
- GET /solicitudes

Filtros:
- q
- estado
- mine
- page / page_size

Acciones:
- Registrar Solicitud
- Ver detalle

### Solicitudes – Registrar
Endpoint:
- POST /solicitudes

Payload esperado:
{
  cliente: { ... },
  apoderado: null | { ... },
  promotor: null | { ... },
  atencion: null | { ... }
}

Validaciones:
- Cliente obligatorio
- Apoderado consistente

Resultado:
- 201 → volver a lista
- 422 → errores por campo

### Solicitudes – Detalle
Fuente:
- GET /solicitudes/{id}

Regla UI:
- Mostrar botones SOLO si están en acciones_permitidas

Acciones:
- EDITAR_DATOS
- ASIGNAR_GESTOR / CAMBIAR_GESTOR
- REGISTRAR_PAGO
- ASIGNAR_MEDICO / CAMBIAR_MEDICO
- CERRAR
- CANCELAR
- OVERRIDE

Endpoints:
- POST /solicitudes/{id}/registrar-pago
- POST /solicitudes/{id}/asignar-gestor
- POST /solicitudes/{id}/cambiar-gestor
- POST /solicitudes/{id}/asignar-medico
- POST /solicitudes/{id}/cambiar-medico
- POST /solicitudes/{id}/cerrar
- POST /solicitudes/{id}/cancelar
- POST /solicitudes/{id}/override

Post-acción:
- Siempre reconsultar GET /solicitudes/{id}

## Administración

### Usuarios
Fuente:
- GET /admin/users

Acciones:
- POST /admin/users
- PATCH /admin/users/{id}
- POST /admin/users/{id}/reset-password

Visible solo para ADMIN

## Plan de Implementación
1. Usuarios
2. Autenticación
3. Solicitudes + POLICY
4. Inicio
5. Reportes (opcional)
