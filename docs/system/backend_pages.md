# Endpoints y Páginas Principales del Backend CMEP

## 1. solicitudes.py (API de Solicitudes)
- Ubicación: `backend/app/api/solicitudes.py`
- Endpoints REST:
  - `POST /solicitudes`: Crear nueva solicitud
  - `GET /solicitudes`: Listar solicitudes (filtros, paginación)
  - `GET /solicitudes/{id}`: Detalle completo de solicitud
  - `PATCH /solicitudes/{id}`: Editar datos de solicitud
  - Acciones: asignar gestor/médico, registrar pago, cerrar/cancelar
- Orquesta lógica de negocio usando servicios y modelos.
- Controla permisos y estados operativos.

## 2. Otros módulos API
- `admin.py`: Gestión de usuarios (listar, crear, actualizar, resetear password)
- `archivos.py`: Subida, descarga y borrado de archivos asociados a solicitudes
- `empleados.py`: Listado de empleados por rol (GESTOR, MEDICO)
- `promotores.py`: Listado de promotores disponibles
- `reportes.py`: Generación de reportes administrativos (KPIs, series, rankings)
- `auth.py`: Autenticación, login, manejo de sesiones

## 3. Flujo típico de una solicitud
1. El usuario crea una solicitud vía frontend (POST /solicitudes)
2. Se asigna gestor, se registra pago, se asigna médico, se evalúa y cierra
3. Cada acción corresponde a endpoints y lógica específica en el backend

---

Cada endpoint valida permisos, estados y aplica reglas de negocio, registrando auditoría y devolviendo DTOs detallados para el frontend.