# Guia de Testing Manual — CMEP (localhost:3000)

## Requisitos previos

1. Backend corriendo en `localhost:8000`
2. Frontend corriendo en `localhost:3000`
3. Seed de datos ejecutado (`python infra/seed_dev.py`)

---

cd infra && docker-compose up (o backend local: cd backend && uvicorn app.main:app --reload)
Ejecutar seed: cd infra && python seed_dev.py
Abrir http://localhost:3000/login
En una terminal dentro de frontend/:
npm install
npm run dev
---

## Usuarios disponibles

| Email | Password | Rol | Nombre |
|-------|----------|-----|--------|
| `admin@cmep.local` | `admin123` | ADMIN | Admin Sistema |
| `operador@cmep.local` | `operador123` | OPERADOR | Ana Operadora |
| `gestor@cmep.local` | `gestor123` | GESTOR | Carlos Gestor |
| `medico@cmep.local` | `medico123` | MEDICO | Maria Medico |
| `suspendido@cmep.local` | `suspendido123` | OPERADOR (suspendido) | Suspendido Test |

---

## Test 1: Login y sesion

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1.1 | Abrir `localhost:3000` | Redirige a `/login` |
| 1.2 | Login con `admin@cmep.local` / `admin123` | Entra a `/app`, ve header con "Admin Sistema" |
| 1.3 | Ver navegacion | Ve links: Inicio, Solicitudes, Usuarios |
| 1.4 | Hacer logout (boton en header) | Vuelve a `/login` |
| 1.5 | Login con `operador@cmep.local` / `operador123` | Entra a `/app`, NO ve link "Usuarios" |
| 1.6 | Login con `suspendido@cmep.local` / `suspendido123` | Mensaje de error, no puede entrar |

---

## Test 2: Crear solicitud

Login como: **operador** o **admin**

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 2.1 | Click "Solicitudes" en nav | Ve lista de solicitudes |
| 2.2 | Click "+ Registrar Solicitud" | Abre formulario nueva solicitud |
| 2.3 | Llenar datos cliente: DNI, 99999999, "Test", "Cliente" | Campos aceptados |
| 2.4 | Seleccionar un servicio del dropdown | Se muestra tarifa |
| 2.5 | Opcionalmente seleccionar promotor | Dropdown con promotores del seed |
| 2.6 | Click "Crear" | Redirige a detalle, estado = REGISTRADO |

---

## Test 3: Flujo completo de solicitud

Login como: **admin** u **operador** (ambos pueden completar el flujo entero)

### Fase 1: REGISTRADO -> ASIGNADO_GESTOR
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 3.1 | Desde detalle de solicitud en REGISTRADO | Stepper muestra fase 1 activa (azul) |
| 3.2 | Click "Asignar gestor" | Abre modal con dropdown de gestores |
| 3.3 | Seleccionar "Carlos Gestor" del dropdown | Nombre visible |
| 3.4 | Confirmar | Estado cambia a ASIGNADO_GESTOR, stepper avanza |

### Fase 2: ASIGNADO_GESTOR -> PAGADO
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 3.5 | Click "Registrar pago" | Abre modal de pago |
| 3.6 | Llenar: canal=YAPE, fecha=hoy, monto=150, moneda=PEN | Campos aceptados |
| 3.7 | Confirmar | Estado cambia a PAGADO, stepper avanza |

### Fase 3: PAGADO -> ASIGNADO_MEDICO
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 3.8 | Click "Asignar medico" | Abre modal con dropdown de medicos |
| 3.9 | Seleccionar "Maria Medico" del dropdown | Nombre visible |
| 3.10 | Confirmar | Estado cambia a ASIGNADO_MEDICO, stepper avanza |

### Fase 4: ASIGNADO_MEDICO -> CERRADO
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 3.11 | Click "Cerrar" | Abre modal (comentario opcional) |
| 3.12 | Confirmar | Estado cambia a CERRADO, stepper completo (todo verde) |

---

## Test 4: Cancelar solicitud

Login como: cualquier rol

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 4.1 | Crear nueva solicitud (Test 2) | Solicitud en REGISTRADO |
| 4.2 | Click "Cancelar" | Abre modal (comentario opcional) |
| 4.3 | Confirmar | Estado = CANCELADO, stepper todo gris + banner rojo |

---

## Test 5: Flujo con diferentes roles

### Como GESTOR (login: gestor@cmep.local)
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 5.1 | Abrir solicitud en ASIGNADO_GESTOR | Ve botones: Registrar pago, Cancelar, Editar |
| 5.2 | NO ve boton "Asignar gestor" | GESTOR no puede asignar gestor en REGISTRADO |
| 5.3 | Registrar pago | Avanza a PAGADO |
| 5.4 | Asignar medico | Avanza a ASIGNADO_MEDICO |
| 5.5 | Cerrar | Avanza a CERRADO |

### Como MEDICO (login: medico@cmep.local)
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 5.6 | Abrir solicitud en ASIGNADO_MEDICO | Ve botones: Cerrar, Cancelar, Editar |
| 5.7 | NO ve Asignar gestor ni Registrar pago | MEDICO no tiene esas acciones |
| 5.8 | Cerrar | Avanza a CERRADO |

---

## Test 6: Editar datos de solicitud

Login como: cualquier rol

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 6.1 | Abrir detalle de solicitud (no cerrada/cancelada) | Ve boton "Editar datos" |
| 6.2 | Click "Editar datos" | Abre modal con campos editables |
| 6.3 | Cambiar nombre del cliente, comentario | Campos aceptan input |
| 6.4 | Guardar | Datos actualizados, historial muestra cambio |

---

## Test 7: Cambiar gestor/medico

Login como: cualquier rol

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 7.1 | Solicitud con gestor asignado | Ve boton "Cambiar gestor" |
| 7.2 | Click "Cambiar gestor" | Modal con dropdown de gestores |
| 7.3 | Seleccionar otro gestor (si hay mas de uno) | Gestor cambiado |

---

## Test 8: Subir archivos

Login como: cualquier rol

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 8.1 | Abrir detalle de solicitud | Ve seccion "Archivos" |
| 8.2 | Subir un archivo (PDF, imagen) | Archivo aparece en la lista |
| 8.3 | Click para descargar | Archivo se descarga |
| 8.4 | Click eliminar | Archivo se elimina de la lista |

---

## Test 9: Administracion de usuarios (solo ADMIN)

Login como: **admin@cmep.local**

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 9.1 | Click "Usuarios" en nav | Ve tabla con 5 usuarios del seed |
| 9.2 | Verificar tabla | Ve email, nombre, documento, roles (badges color), estado |
| 9.3 | Click "+ Nuevo Usuario" | Abre modal de creacion |
| 9.4 | Llenar: email=test@cmep.local, pass=test12345, nombres=Test, apellidos=Nuevo, DNI, 88888888, rol=OPERADOR | Campos aceptados |
| 9.5 | Click "Crear" | Usuario aparece en tabla, mensaje verde |
| 9.6 | Click "Editar" en el nuevo usuario | Modal con datos precargados |
| 9.7 | Cambiar nombre a "Editado" | Nombre actualizado en tabla |
| 9.8 | Click "Editar" > cambiar roles a GESTOR+MEDICO | Badges cambian en tabla |
| 9.9 | Click "Suspender" en un usuario | Confirm > estado cambia a "SUSPENDIDO" (rojo) |
| 9.10 | Click "Reactivar" en usuario suspendido | Estado cambia a "ACTIVO" (verde) |
| 9.11 | Click "Reset Pass" en un usuario | Modal pide nueva password |
| 9.12 | Ingresar nueva password (min 8 chars) | Mensaje de exito |
| 9.13 | Intentar suspenderse a si mismo (admin) | Error: "No puedes suspenderte a ti mismo" |

### Verificar permisos
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 9.14 | Logout, login como operador | NO ve link "Usuarios" en nav |
| 9.15 | Ir manualmente a `/app/usuarios` | Pagina carga pero API retorna error 403 |

---

## Test 10: Stepper visual

Login como: cualquier rol

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 10.1 | Abrir solicitud REGISTRADO | Fase 1 azul (con glow), fases 2-5 grises |
| 10.2 | Abrir solicitud ASIGNADO_GESTOR | Fase 1 verde (checkmark), fase 2 azul, fases 3-5 grises |
| 10.3 | Abrir solicitud PAGADO | Fases 1-2 verdes, fase 3 azul, fases 4-5 grises |
| 10.4 | Abrir solicitud ASIGNADO_MEDICO | Fases 1-3 verdes, fase 4 azul, fase 5 gris |
| 10.5 | Abrir solicitud CERRADO | Fases 1-5 todas verdes con checkmarks |
| 10.6 | Abrir solicitud CANCELADO | Todas grises + banner rojo "CANCELADA" |
| 10.7 | Verificar descripciones | Cada fase muestra mini-explicacion de que falta |

---

## Test 11: Busqueda y filtros

Login como: cualquier rol

| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 11.1 | En lista de solicitudes, escribir numero de documento | Filtra por documento |
| 11.2 | Buscar por nombre del cliente | Filtra por nombre |
| 11.3 | Seleccionar filtro de estado "PAGADO" | Solo muestra solicitudes en estado PAGADO |
| 11.4 | Limpiar filtros | Muestra todas las solicitudes |

---

## Datos de prueba del seed

### Clientes pre-creados
- Juan Perez Lopez — DNI 12345678
- Rosa Garcia Torres — DNI 87654321
- Pedro Ramirez Silva — CE CE001234

### Servicios disponibles
| Servicio | Tarifa |
|----------|--------|
| Certificado Medico de Evaluacion Profesional - Presencial | S/ 150.00 |
| Certificado Medico de Evaluacion Profesional - Virtual | S/ 120.00 |
| Certificado Medico de Salud Mental | S/ 200.00 |

### Promotores
- Luis Promotor Reyes (Persona) — DNI 11111111
- Notaria Gonzales & Asociados (Empresa) — RUC 20123456789
