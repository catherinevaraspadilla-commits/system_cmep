Plan: Campos SolicitudNueva + Colores + Fix Reportes
Resumen
3 tareas: (1) agregar campos opcionales al form, (2) colores por seccion, (3) fix queries reportes para MySQL + documentacion.

TAREA 1: Fix Reportes (bug critico en produccion)
Problema: func.strftime() es funcion SQLite. En produccion (MySQL 8 RDS) falla → error de carga en la pagina de reportes.

Archivo: backend/app/services/reportes_service.py

Cambios:

Agregar from app.config import settings (import)
Crear helper _format_periodo(col, agrupacion) que usa settings.is_sqlite para branchar:
SQLite: func.strftime("%Y-%m", col) / func.strftime("%Y-W%W", col)
MySQL: func.date_format(col, "%Y-%m") / func.concat(func.date_format(col, "%Y"), literal("-W"), func.lpad(func.week(col, 1), 2, "0"))
Reemplazar 3 usos de func.strftime:
Linea 72-74: _periodo_expr()
Linea 187-190: periodo en subquery con estado
Linea 201-204: periodo de pagos
Riesgo: Bajo. SQLite path queda identico (tests pasan). MySQL path es nuevo pero usa funciones estandar.

TAREA 2: Agregar campos al formulario SolicitudNueva
2a. Backend schema — backend/app/schemas/solicitud.py
ClienteInput: agregar direccion: str | None = None (ya tiene fecha_nacimiento y email)
ApoderadoInput: agregar fecha_nacimiento: date | None = None, direccion: str | None = None, email: str | None = None
2b. Backend service — backend/app/services/solicitud_service.py
find_or_create_persona(): agregar parametro direccion: str | None = None
En update block: if direccion and persona.direccion != direccion: persona.direccion = direccion
En create block: agregar direccion=direccion al constructor Persona
2c. Backend API — backend/app/api/solicitudes.py
Llamada cliente (linea 58-68): agregar direccion=body.cliente.direccion
Llamada apoderado (linea 73-80): agregar email=body.apoderado.email, fecha_nacimiento=body.apoderado.fecha_nacimiento, direccion=body.apoderado.direccion
2d. Frontend types — frontend/src/types/solicitud.ts
ClienteInput: agregar direccion?: string
ApoderadoInput: agregar fecha_nacimiento?: string, direccion?: string, email?: string
2e. Frontend form — frontend/src/pages/app/SolicitudNueva.tsx
Agregar 5 estados: cliFechaNacimiento, cliDireccion, apoFechaNacimiento, apoDireccion, apoEmail
Agregar campos al payload de envio
Agregar inputs al JSX:
Cliente: fila con Fecha nacimiento + Direccion (grid 1fr 1fr)
Apoderado: fila con Email + Fecha nacimiento (grid 1fr 1fr), luego Direccion
TAREA 3: Colores por seccion
Archivo: frontend/src/pages/app/SolicitudNueva.tsx

Agregar background a los 3 fieldsets:

Cliente: #e8f0fe (azul suave)
Apoderado: #fff8e1 (ambar suave)
Promotor: #e8f5e9 (verde suave)
TAREA 4: Documentacion reportes
Archivo nuevo: docs/claude/reportes.md

Contenido: estructura de la pagina, queries SQL usadas, logica de estado_operativo, edge cases, compatibilidad DB.

Archivos a modificar (7 total)
Archivo	Tarea	Cambio
backend/app/services/reportes_service.py	T1	Fix strftime → dual compatible
backend/app/schemas/solicitud.py	T2	Agregar campos opcionales
backend/app/services/solicitud_service.py	T2	Agregar param direccion
backend/app/api/solicitudes.py	T2	Pasar nuevos campos
frontend/src/types/solicitud.ts	T2	Agregar tipos
frontend/src/pages/app/SolicitudNueva.tsx	T2+T3	Campos + colores
docs/claude/reportes.md	T4	Nuevo doc
Verificacion
Build frontend: npm run build sin errores
Backend: los tests existentes usan SQLite → deben pasar sin cambios
Reportes en prod: deberia cargar sin error despues del fix MySQL