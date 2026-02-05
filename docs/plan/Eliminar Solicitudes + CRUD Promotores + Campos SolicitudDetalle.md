Resumen
3 tareas: (1) eliminar solicitudes con cascade (admin only), (2) CRUD promotores accesible a todos, (3) agregar todos los campos de cliente/apoderado a SolicitudDetalle.

TAREA 1: Eliminar solicitudes (solo ADMIN)
Detalle de lo que se ELIMINA al borrar una solicitud
Orden de eliminacion (todas las FK usan RESTRICT, se debe borrar manualmente en orden):

#	Tabla	Que se borra
1	resultado_medico	Todos los resultados medicos de la solicitud
2	solicitud_archivo	Registros junction archivo-solicitud
3	archivos	Registros de archivo + archivos fisicos (local o S3 via delete_file())
4	pago_solicitud	Todos los pagos registrados
5	solicitud_estado_historial	Todo el historial de cambios
6	solicitud_asignacion	Todas las asignaciones (gestor, medico, operador)
7	solicitud_cmep	La solicitud misma
Limpieza condicional post-eliminacion:

#	Tabla	Condicion para eliminar
8	cliente_apoderado	Si el cliente se va a eliminar, borrar sus registros de apoderado
9	clientes	Solo si NO tiene otras solicitudes (COUNT solicitud_cmep WHERE cliente_id)
10	personas (del cliente)	Solo si se elimino el cliente Y la persona no es empleado ni user
11	personas (apoderado)	Solo si NO es apoderado en otras solicitudes Y no es empleado ni user
Lo que NO se elimina
Promotor: se preserva siempre (puede estar vinculado a otras solicitudes/clientes)
Servicio: catalogo, nunca se toca
Personas que son empleados o users: aunque sean cliente/apoderado, si tienen registro en empleados o users, la persona se preserva
1a. Backend service — backend/app/services/solicitud_service.py
Nueva funcion eliminar_solicitud(db, solicitud, user_id):

Recibe solicitud ya cargada con relaciones
Ejecuta eliminacion en el orden de la tabla anterior
Para archivos: itera solicitud.archivos_rel, obtiene Archivo, llama delete_file(archivo.storage_path), elimina junction y archivo
Para limpieza condicional: queries COUNT para verificar antes de borrar
1b. Backend API — backend/app/api/solicitudes.py

DELETE /solicitudes/{solicitud_id}
Dependency: require_admin (de admin_service.py)
Carga solicitud, llama eliminar_solicitud(), retorna {"ok": True}
1c. Frontend — SolicitudDetalle.tsx
Boton rojo "Eliminar solicitud" visible solo para ADMIN (via useAuth())
Dialog de confirmacion con confirm()
api.delete(/solicitudes/${id}) -> navigate("/app/solicitudes")
TAREA 2: CRUD Promotores
2a. Backend schemas — backend/app/schemas/promotor.py (archivo NUEVO)
CreatePromotorRequest: tipo_promotor + campos segun tipo + shared (ruc, email, celular_1, fuente_promotor, comentario)
UpdatePromotorRequest: todos opcionales, incluyendo nombres/apellidos para tipo PERSONA
2b. Backend API — backend/app/api/promotores.py
Ampliar el archivo existente (ya tiene GET lista). Agregar:

Endpoint	Descripcion
POST /promotores	Crear promotor. Reutiliza create_promotor() de solicitud_service
GET /promotores/{id}	Detalle completo (todos los campos + persona si tipo=PERSONA)
PATCH /promotores/{id}	Editar campos directos + persona vinculada
DELETE /promotores/{id}	Eliminar si no tiene solicitudes vinculadas (409 si tiene)
Todos requieren get_current_user (cualquier rol autenticado), NO requieren admin.

2c. Frontend — frontend/src/pages/app/PromotoresLista.tsx (archivo NUEVO)
Pagina CRUD completa:

Tabla con columnas: Tipo, Nombre, RUC, Email, Celular, Fuente, Acciones
Boton "Nuevo promotor" -> formulario inline (expandible)
Formulario adaptativo: PERSONA muestra nombres/apellidos/documento, EMPRESA muestra razon_social, OTROS muestra nombre libre
Boton editar/eliminar por fila
Eliminar con confirmacion
2d. Routing — frontend/src/App.tsx
Agregar: <Route path="promotores" element={<PromotoresLista />} />

2e. Menu — frontend/src/components/AppLayout.tsx
Agregar link "Promotores" despues de "Solicitudes" y antes del bloque {isAdmin && ...}.
Accesible a todos los roles.

TAREA 3: Campos cliente/apoderado en SolicitudDetalle
3a. Backend DTO — backend/app/services/solicitud_service.py
En build_detail_dto() (linea 454):

Cliente: agregar al dict:

email (de cliente_persona.email)
fecha_nacimiento (con .isoformat())
direccion (de cliente_persona.direccion)
Apoderado (linea 462): agregar:

fecha_nacimiento (con .isoformat())
direccion
3b. Frontend types — frontend/src/types/solicitud.ts
ClienteDTO: agregar email: string | null, fecha_nacimiento: string | null, direccion: string | null

PersonaDTO: agregar fecha_nacimiento: string | null, direccion: string | null

EditSolicitudRequest: agregar:

cliente_fecha_nacimiento?: string, cliente_direccion?: string
apoderado_nombres?: string, apoderado_apellidos?: string, apoderado_celular?: string, apoderado_email?: string, apoderado_fecha_nacimiento?: string, apoderado_direccion?: string
3c. Backend schema — backend/app/schemas/solicitud.py
EditSolicitudRequest: agregar los mismos campos correspondientes en Python (con date | None para fechas).

3d. Backend API — backend/app/api/solicitudes.py
En editar_solicitud() (PATCH handler):

Ampliar cliente_field_map: agregar "cliente_fecha_nacimiento": "fecha_nacimiento", "cliente_direccion": "direccion"

Nuevo apoderado_field_map (bloque nuevo similar al de cliente):


if solicitud.apoderado:
    for req_field, persona_field in apoderado_field_map.items():
        # misma logica de comparar old/new + historial
3e. Frontend display — SolicitudDetalle.tsx
Seccion cliente (grid 4 columnas, linea 441): agregar Email, Fecha nacimiento, Direccion

Seccion apoderado (linea 447): agregar Celular, Email, Fecha nacimiento, Direccion

Edit form (linea 494): agregar inputs para:

Cliente: fecha_nacimiento (date), direccion (text)
Apoderado (seccion nueva): nombres, apellidos, celular, email, fecha_nacimiento, direccion
Archivos a modificar (10 total)
#	Archivo	Tarea	Cambio
1	backend/app/services/solicitud_service.py	T1+T3	eliminar_solicitud() + campos en build_detail_dto()
2	backend/app/api/solicitudes.py	T1+T3	DELETE endpoint + ampliar PATCH con apoderado
3	backend/app/schemas/solicitud.py	T3	Campos apoderado en EditSolicitudRequest
4	backend/app/api/promotores.py	T2	POST, GET detail, PATCH, DELETE
5	backend/app/schemas/promotor.py	T2	NUEVO: CreatePromotorRequest, UpdatePromotorRequest
6	frontend/src/pages/app/SolicitudDetalle.tsx	T1+T3	Boton eliminar + campos display/edit
7	frontend/src/types/solicitud.ts	T3	Campos en ClienteDTO, PersonaDTO, EditRequest
8	frontend/src/pages/app/PromotoresLista.tsx	T2	NUEVO: pagina CRUD promotores
9	frontend/src/App.tsx	T2	Ruta /app/promotores
10	frontend/src/components/AppLayout.tsx	T2	Link menu "Promotores"
Verificacion
cd frontend && npm run build — sin errores TS
Probar: eliminar solicitud como admin -> cascade completa
Probar: eliminar solicitud como no-admin -> 403
Probar: CRUD promotores (crear, editar, listar, eliminar sin solicitudes, intentar eliminar con solicitudes -> 409)
Probar: ver detalle solicitud -> todos los campos visibles
Probar: editar cliente/apoderado desde detalle -> cambios guardados con historial
User approved the plan
Plan approved. Let me set up the task list and start implementing.

Update Todos

T1: Backend - eliminar_solicitud() en solicitud_service.py

T1: Backend - DELETE /solicitudes/{id} endpoint

T1: Frontend - Boton eliminar en SolicitudDetalle

T2: Backend - schemas/promotor.py (nuevo)

T2: Backend - CRUD endpoints en promotores.py

T2: Frontend - PromotoresLista.tsx (nuevo)

T2: Frontend - Ruta y menu promotores

T3: Backend - Campos en build_detail_dto()

T3: Backend - EditSolicitudRequest + PATCH apoderado

T3: Frontend types - ClienteDTO, PersonaDTO, EditRequest

T3: Frontend - Display y edit en SolicitudDetalle

Build frontend y verificar