# CMEP — Checkpoints de Validacion UI

Este documento define los puntos donde se requiere validacion del owner antes de continuar al siguiente modulo. Cada checkpoint especifica que se muestra, que se espera validar y que se necesita para dar el OK.

---

## Checkpoint 1 — Post M0 (Bootstrap)

### Que se muestra
- Repositorio con estructura de carpetas
- docker-compose funcional (3 servicios levantan)
- Backend responde `GET /health`
- Frontend carga y muestra estado "Conectado"

### Que validar
- [ ] La estructura de carpetas es correcta
- [ ] docker-compose levanta sin errores
- [ ] Frontend se ve en el navegador

### Como validar
```bash
docker-compose up
# Abrir http://localhost:3000
# Verificar indicador de conexion
```

### Para dar OK
- Estructura correcta
- Servicios levantan
- Frontend conecta al backend

---

## Checkpoint 2 — Post M1 (Auth y Sesiones)

### Que se muestra
- Pagina de login funcional
- Login/logout/me funcionando
- Middleware de autenticacion activo
- Tests de auth pasando

### Que validar
- [ ] Login con usuario seed funciona
- [ ] Logout limpia la sesion
- [ ] `/app` sin sesion redirige a `/login`
- [ ] Usuario SUSPENDIDO no puede entrar
- [ ] Tests: `pytest tests/ -v` todos pasan

### Endpoints creados
| Metodo | Ruta | Estado |
|--------|------|--------|
| POST | `/auth/login` | Nuevo |
| POST | `/auth/logout` | Nuevo |
| GET | `/auth/me` | Nuevo |

### Pantallas involucradas
- `/login` — formulario de autenticacion
- Redirect logic a `/app` y `/login`

### Pasos manuales (smoke)
1. Abrir `http://localhost:3000/login`
2. Ingresar email y password del admin seed
3. Verificar redirect a `/app` y datos del usuario
4. Hacer logout
5. Intentar acceder a `/app` — debe redirigir a `/login`
6. Intentar login con usuario SUSPENDIDO — debe fallar

---

## Checkpoint 3 — Post M2 (CRUD Solicitudes)

### Que se muestra
- Formulario de registro de solicitud
- Lista de solicitudes con filtros y paginacion
- Vista de detalle con estado operativo
- Edicion de datos con auditoria
- Tests CRUD pasando

### Que validar
- [ ] Se puede crear una solicitud con datos minimos
- [ ] La lista muestra solicitudes con filtros funcionales
- [ ] El detalle muestra estado_operativo = REGISTRADO
- [ ] Editar un campo actualiza y registra historial
- [ ] Tests: todos pasan

### Endpoints creados
| Metodo | Ruta | Estado |
|--------|------|--------|
| POST | `/solicitudes` | Nuevo |
| GET | `/solicitudes` | Nuevo |
| GET | `/solicitudes/{id}` | Nuevo |
| PATCH | `/solicitudes/{id}` | Nuevo |

### Pantallas involucradas
- `/app/solicitudes` — lista con filtros
- `/app/solicitudes/nueva` — formulario de registro
- `/app/solicitudes/{id}` — vista detalle (sin botones de workflow aun)

### Pasos manuales (smoke)
1. Login como OPERADOR
2. Ir a "Solicitudes" > "Nueva"
3. Llenar datos del cliente (DNI, nombre, apellido, celular)
4. Enviar — verificar redirect a lista
5. Click en la solicitud — verificar detalle con estado REGISTRADO
6. Editar un campo (ej: celular) — verificar actualizacion

---

## Checkpoint 4 — Post M3 (Workflow + POLICY)

### Que se muestra
- Flujo completo: REGISTRADO -> ASIGNADO_GESTOR -> PAGADO -> ASIGNADO_MEDICO -> CERRADO
- Botones condicionados por acciones_permitidas
- Bloqueo de acciones no permitidas (403)
- Override para ADMIN en estados terminales
- Tests de derivacion, POLICY y workflow pasando

### Que validar
- [ ] Asignar gestor cambia estado a ASIGNADO_GESTOR
- [ ] Registrar pago cambia estado a PAGADO
- [ ] Asignar medico (requiere PAGADO) cambia a ASIGNADO_MEDICO
- [ ] Cerrar cambia a CERRADO
- [ ] Cancelar funciona desde estados no terminales
- [ ] Override funciona solo para ADMIN en CERRADO/CANCELADO
- [ ] Botones aparecen/desaparecen segun POLICY
- [ ] Accion no permitida retorna 403
- [ ] Pagina de inicio muestra trabajo por rol
- [ ] Tests: todos pasan

### Endpoints creados
| Metodo | Ruta | Estado |
|--------|------|--------|
| POST | `/solicitudes/{id}/asignar-gestor` | Nuevo |
| POST | `/solicitudes/{id}/cambiar-gestor` | Nuevo |
| POST | `/solicitudes/{id}/registrar-pago` | Nuevo |
| POST | `/solicitudes/{id}/asignar-medico` | Nuevo |
| POST | `/solicitudes/{id}/cambiar-medico` | Nuevo |
| POST | `/solicitudes/{id}/cerrar` | Nuevo |
| POST | `/solicitudes/{id}/cancelar` | Nuevo |
| POST | `/solicitudes/{id}/override` | Nuevo |

### Pantallas involucradas
- `/app/solicitudes/{id}` — botones de accion condicionales
- `/app/inicio` — dashboard de trabajo por rol

### Pasos manuales (smoke completo)
1. Login como ADMIN
2. Crear solicitud — estado REGISTRADO
3. En detalle: verificar botones visibles (EDITAR_DATOS, ASIGNAR_GESTOR, CANCELAR)
4. Asignar gestor — verificar estado ASIGNADO_GESTOR
5. Verificar que botones cambiaron (ahora incluye REGISTRAR_PAGO)
6. Registrar pago — verificar estado PAGADO
7. Asignar medico — verificar estado ASIGNADO_MEDICO
8. Login como MEDICO
9. Verificar que en Inicio aparece la solicitud asignada
10. Abrir detalle — verificar botones (CERRAR, EDITAR_DATOS)
11. Cerrar — verificar estado CERRADO, sin botones de accion (excepto OVERRIDE para ADMIN)
12. Login como ADMIN — verificar OVERRIDE disponible
13. Crear otra solicitud, intentar asignar medico sin pagar — verificar error 422

---

## Checkpoint 5 — Post M4 (Archivos)

### Que se muestra
- Subida de archivos desde detalle de solicitud
- Listado de archivos asociados
- Descarga funcional
- Tests de archivos pasando

### Que validar
- [ ] Se puede subir un archivo a una solicitud
- [ ] El archivo aparece en la lista del detalle
- [ ] Se puede descargar correctamente
- [ ] Tipo de archivo se registra (EVIDENCIA_PAGO, DOCUMENTO, OTROS)

### Endpoints creados
| Metodo | Ruta | Estado |
|--------|------|--------|
| POST | `/solicitudes/{id}/archivos` | Nuevo |
| GET | `/archivos/{archivo_id}` | Nuevo |

### Pantallas involucradas
- `/app/solicitudes/{id}` — seccion de archivos

### Pasos manuales (smoke)
1. Abrir detalle de solicitud
2. Click en "Subir archivo"
3. Seleccionar archivo, elegir tipo
4. Verificar que aparece en la lista
5. Click en "Descargar" — verificar contenido

---

## Checkpoint 6 — Post M5 (Administracion)

### Que se muestra
- Pagina de usuarios (solo ADMIN)
- CRUD completo de usuarios
- Suspension invalida sesiones
- Reset password
- Tests de admin pasando

### Que validar
- [ ] Solo ADMIN ve el menu "Usuarios"
- [ ] Se puede crear un usuario nuevo
- [ ] El nuevo usuario puede hacer login
- [ ] Suspender usuario impide login
- [ ] Reset password funciona

### Endpoints creados
| Metodo | Ruta | Estado |
|--------|------|--------|
| GET | `/admin/users` | Nuevo |
| POST | `/admin/users` | Nuevo |
| PATCH | `/admin/users/{id}` | Nuevo |
| POST | `/admin/users/{id}/reset-password` | Nuevo |

### Pantallas involucradas
- `/app/usuarios` — tabla + formularios CRUD

### Pasos manuales (smoke)
1. Login como ADMIN
2. Ir a "Usuarios"
3. Crear usuario OPERADOR con email y password
4. Logout, login como nuevo usuario — verificar acceso
5. Login como ADMIN, suspender el usuario
6. Intentar login como suspendido — debe fallar

---

## Checkpoint 6.5 — Post M5.5 (Mejoras Incrementales)

### Que se muestra
- Registro de promotor nuevo durante creacion de solicitud
- Promotor visible en detalle de solicitud
- Tipo/numero documento separados en detalle
- Tabla de permisos por rol en pagina de usuarios

### Que validar
- [ ] Crear solicitud con promotor existente (dropdown) sigue funcionando
- [ ] Crear solicitud con promotor nuevo tipo PERSONA (nombres+apellidos)
- [ ] Crear solicitud con promotor nuevo tipo EMPRESA (razon_social)
- [ ] Crear solicitud con promotor nuevo tipo OTROS (nombre_promotor_otros)
- [ ] Crear solicitud sin promotor sigue funcionando
- [ ] Detalle muestra seccion "Promotor" con datos correctos segun tipo
- [ ] Detalle sin promotor muestra "Sin promotor"
- [ ] Tipo documento y numero documento aparecen como campos separados
- [ ] Pagina de usuarios (ADMIN) muestra seccion "Permisos por rol"
- [ ] Tabla de permisos refleja POLICY del backend
- [ ] Tests: `pytest tests/ -v` todos pasan
- [ ] TypeScript: `npx tsc --noEmit` 0 errores

### Endpoints creados/modificados
| Metodo | Ruta | Estado |
|--------|------|--------|
| POST | `/solicitudes` | Modificado (acepta promotor inline) |
| GET | `/solicitudes/{id}` | Modificado (incluye promotor) |
| GET | `/admin/permisos` | Nuevo |

### Pantallas involucradas
- `/app/solicitudes/nueva` — sub-formulario promotor nuevo
- `/app/solicitudes/{id}` — seccion promotor + doc separados
- `/app/usuarios` — seccion permisos por rol

### Pasos manuales (smoke)
1. Login como OPERADOR
2. Ir a "Solicitudes" > "Registrar Solicitud"
3. Seleccionar "Registrar nuevo promotor" en dropdown
4. Seleccionar tipo PERSONA → verificar campos: nombres*, apellidos*, tipo_doc, numero_doc
5. Llenar datos y crear solicitud → verificar redirect a detalle
6. En detalle: verificar seccion "Promotor" muestra datos correctos
7. En detalle: verificar "Tipo documento" y "Numero documento" separados
8. Crear otra solicitud con promotor tipo EMPRESA → verificar razon_social
9. Crear solicitud sin promotor → verificar "Sin promotor" en detalle
10. Login como ADMIN, ir a "Usuarios"
11. Verificar seccion "Permisos por rol" (colapsable)
12. Expandir → verificar tabla con roles y estados

---

## Checkpoint 6.6 — Post M5.6 (Dashboard / Pagina de Inicio)

### Que se muestra
- Pagina de inicio funcional con bienvenida personalizada
- Accesos rapidos segun rol
- Tabla de solicitudes recientes del usuario

### Que validar
- [ ] Login como OPERADOR → bienvenida con nombre + texto de operador
- [ ] Accesos rapidos visibles: "Registrar solicitud", "Ver solicitudes"
- [ ] Tabla muestra solicitudes creadas por el operador
- [ ] Login como GESTOR → texto gestor + solicitudes asignadas como gestor
- [ ] Login como MEDICO → texto medico + solicitudes asignadas como medico
- [ ] Login como ADMIN → texto admin + boton "Administrar usuarios" + todas las solicitudes
- [ ] Usuario multi-rol ve descripciones combinadas
- [ ] Usuario sin solicitudes ve mensaje "No tienes solicitudes activas"
- [ ] Link "Ver todas las solicitudes" navega a /app/solicitudes
- [ ] Botones de accion rapida navegan a rutas correctas
- [ ] Lenguaje simple, sin tecnicismos
- [ ] Tests: `pytest tests/ -v` todos pasan
- [ ] TypeScript: `npx tsc --noEmit` 0 errores

### Endpoints modificados
| Metodo | Ruta | Estado |
|--------|------|--------|
| GET | `/solicitudes` | Modificado (parametro `mine`) |

### Pantallas involucradas
- `/app` — Inicio.tsx (reescritura completa)

### Pasos manuales (smoke)
1. Login como OPERADOR
2. Verificar bienvenida: "Bienvenido, {nombre}" + texto operador
3. Verificar botones: "Registrar solicitud", "Ver solicitudes"
4. Click "Registrar solicitud" → navega a /app/solicitudes/nueva
5. Volver a inicio, verificar tabla con solicitudes propias
6. Login como GESTOR → verificar texto gestor + solicitudes asignadas
7. Login como MEDICO → verificar texto medico + solicitudes asignadas
8. Login como ADMIN → verificar texto admin + boton usuarios + todas las solicitudes
9. Verificar responsive (reducir ventana)

---

## Checkpoint 7 — Post M6 (Despliegue Cloud)

### Que se muestra
- Sistema funcional en AWS
- URL publica HTTPS
- Mismo comportamiento que en local

### Que validar
- [ ] Frontend carga desde URL publica
- [ ] Login funciona con cookies cross-origin
- [ ] Flujo completo funciona (smoke M3 en cloud)
- [ ] Archivos se suben/descargan desde S3
- [ ] Logs visibles en CloudWatch
- [ ] No hay secretos expuestos

### Pasos manuales
1. Abrir URL publica en navegador (desktop)
2. Abrir URL publica en navegador movil
3. Ejecutar smoke M3 completo
4. Subir y descargar archivo
5. Verificar logs en CloudWatch

---

## Reglas de interaccion

1. **Despues de cada checkpoint** se muestra:
   - Endpoints creados
   - Tests ejecutados (resultado)
   - Pantallas involucradas
   - Pasos manuales para validar

2. **Se espera validacion** antes de continuar al siguiente modulo.

3. **Si hay observaciones:**
   - Se corrigen en el mismo modulo
   - Se re-ejecutan tests
   - Se re-valida el checkpoint

4. **Formato de respuesta esperado del owner:**
   - `OK` — continuar al siguiente modulo
   - `Observacion: [detalle]` — corregir y re-validar
