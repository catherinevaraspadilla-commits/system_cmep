# Páginas Principales del Frontend CMEP

## 1. SolicitudDetalle (Detalle de Solicitud)
- Ubicación: `frontend/src/pages/app/solicitud/SolicitudDetalle.tsx`
- Orquesta la visualización y edición de una solicitud.
- Divide la UI en 3 bloques principales:
  - **BlockGestion**: Gestión administrativa (asignar/cambiar gestor, cancelar solicitud)
  - **BlockPago**: Registro y visualización de pagos
  - **BlockEvaluacion**: Evaluación médica, asignación/cambio de médico, resultados
- Usa helpers para determinar el estado visual y reglas de negocio (`detailHelpers.ts`).
- Consume endpoints REST `/solicitudes/{id}`, `/empleados`, `/archivos`, etc.
- Permite acciones según permisos y estado operativo.

## 2. SolicitudesLista (Listado de Solicitudes)
- Ubicación: `frontend/src/pages/app/SolicitudesLista.tsx`
- Muestra tabla paginada y filtrable de solicitudes.
- Permite navegación a detalle, creación y búsqueda.

## 3. SolicitudNueva (Nueva Solicitud)
- Ubicación: `frontend/src/pages/app/SolicitudNueva.tsx`
- Formulario para registrar una nueva solicitud.
- Valida datos y realiza POST a `/solicitudes`.

## 4. UsuariosLista, ReportesAdmin, Inicio
- Listados y dashboards para usuarios y reportes administrativos.

## 5. Componentes y helpers clave
- `WorkflowStepper`: Visualiza el flujo de estados de la solicitud.
- `detailHelpers.ts`: Lógica de estados visuales y reglas de UI.
- `detailStyles.ts`: Estilos compartidos para bloques.

---

Cada página principal está modularizada y consume servicios API, gestionando estado y permisos según el usuario y el estado de la solicitud.