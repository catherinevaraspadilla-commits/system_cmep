# Flujo de Funcionamiento — CMEP

## Visión General

El sistema gestiona el ciclo de vida de una **solicitud de certificado médico** (SolicitudCmep), desde su registro inicial hasta su cierre o cancelación. El flujo está controlado por un motor de estados que determina qué acciones son posibles según el rol del usuario y el estado actual de la solicitud.

---

## 1. Flujo de Autenticación

```
Usuario ingresa credenciales
        │
        ▼
POST /auth/login
        │
        ├─ Verifica email y contraseña (bcrypt)
        ├─ Valida estado del usuario (ACTIVO / SUSPENDIDO)
        ├─ Crea registro en tabla `sessions`
        └─ Devuelve cookie httpOnly (session_id)
                │
                ▼
GET /auth/me → retorna usuario + roles + permisos
        │
        ▼
React guarda contexto de auth en AuthProvider
        │
        ▼
Ruta protegida habilitada → /app/*
```

---

## 2. Ciclo de Vida de una Solicitud

### Estados Operativos

El `estado_operativo` no se almacena en la base de datos; se **deriva en tiempo real** a partir de los datos de la solicitud:

```
                    ┌─────────────────────────────┐
                    │        REGISTRADO            │  ← Estado inicial
                    │  (sin gestor, sin pago)      │
                    └──────────────┬──────────────┘
                                   │ ASIGNAR_GESTOR (OPERADOR/ADMIN)
                    ┌──────────────▼──────────────┐
                    │      ASIGNADO_GESTOR         │
                    │  (tiene gestor activo)       │
                    └──────────────┬──────────────┘
                                   │ REGISTRAR_PAGO (GESTOR/OPERADOR/ADMIN)
                    ┌──────────────▼──────────────┐
                    │           PAGADO             │
                    │  (estado_pago = PAGADO)      │
                    └──────────────┬──────────────┘
                                   │ ASIGNAR_MEDICO (GESTOR/ADMIN)
                    ┌──────────────▼──────────────┐
                    │      ASIGNADO_MEDICO         │
                    │  (tiene médico activo)       │
                    └──────────────┬──────────────┘
                                   │ CERRAR (MEDICO/ADMIN)
                    ┌──────────────▼──────────────┐
                    │           CERRADO            │
                    │  (estado_atencion = ATENDIDO)│
                    └─────────────────────────────┘

En cualquier estado anterior a CERRADO:
                    ┌─────────────────────────────┐
                    │          CANCELADO           │
                    │  (estado_atencion = CANCELADO│
                    └─────────────────────────────┘
```

### Lógica de Derivación del Estado Operativo

```python
# Prioridad de evaluación (de mayor a menor):
1. estado_atencion == 'CANCELADO'    → CANCELADO
2. estado_atencion == 'ATENDIDO'     → CERRADO
3. estado_pago == 'PAGADO'
   AND asignacion MEDICO activa      → ASIGNADO_MEDICO
4. estado_pago == 'PAGADO'           → PAGADO
5. asignacion GESTOR activa          → ASIGNADO_GESTOR
6. (ninguna condición anterior)      → REGISTRADO
```

---

## 3. Matriz de Autorización (Policy)

La tabla completa de qué rol puede hacer qué acción en cada estado:

| Estado Operativo | ADMIN | OPERADOR | GESTOR | MEDICO |
|-----------------|-------|----------|--------|--------|
| REGISTRADO | EDITAR, ASIGNAR_GESTOR, CANCELAR | EDITAR, ASIGNAR_GESTOR, CANCELAR | — | — |
| ASIGNADO_GESTOR | EDITAR, REGISTRAR_PAGO, CANCELAR | EDITAR, REGISTRAR_PAGO, CANCELAR | EDITAR, REGISTRAR_PAGO, CANCELAR | — |
| PAGADO | ASIGNAR_MEDICO, CANCELAR | — | ASIGNAR_MEDICO, CANCELAR | — |
| ASIGNADO_MEDICO | CERRAR, CANCELAR | — | CERRAR, CANCELAR | CERRAR |
| CERRADO | — | — | — | — |
| CANCELADO | — | — | — | — |

> **Nota:** `EDITAR` siempre incluye la capacidad de subir y gestionar archivos adjuntos.

---

## 4. Flujo Detallado: Crear una Solicitud

```
OPERADOR inicia formulario → /app/solicitudes/nueva
        │
        ▼
Completa datos del cliente (DNI, nombre, celular)
Selecciona servicio
Agrega promotor (opcional)
Adjunta archivos (opcional)
        │
        ▼
POST /solicitudes
        │
        ├─ Valida datos con Pydantic schema
        ├─ Crea/reutiliza registro de Persona + Cliente
        ├─ Crea SolicitudCmep
        │    ├── estado_atencion = REGISTRADO
        │    ├── estado_pago = PENDIENTE
        │    └── created_by = user_id actual
        ├─ Sube archivos a S3/local (si hay)
        └─ Registra en solicitud_estado_historial
                │
                ▼
        Estado: REGISTRADO
```

---

## 5. Flujo Detallado: Asignar Gestor

```
OPERADOR/ADMIN en detalle de solicitud
        │
        ▼
Lista empleados con rol GESTOR (GET /empleados?rol=GESTOR)
Selecciona gestor
        │
        ▼
POST /solicitudes/{id}/asignar-gestor
        │
        ├─ Verifica policy: rol usuario + estado_operativo actual
        ├─ Desactiva asignación GESTOR previa (es_vigente = false)
        ├─ Crea nueva SolicitudAsignacion
        │    ├── rol_asignacion = GESTOR
        │    ├── empleado_id = seleccionado
        │    └── es_vigente = true
        └─ Registra en historial
                │
                ▼
        Estado: ASIGNADO_GESTOR
```

---

## 6. Flujo Detallado: Registrar Pago

```
GESTOR/OPERADOR/ADMIN
        │
        ▼
POST /solicitudes/{id}/registrar-pago
body: { monto, moneda, metodo_pago, fecha_pago, comprobante_numero }
        │
        ├─ Verifica policy
        ├─ Crea registro PagoSolicitud
        ├─ Actualiza solicitud.estado_pago = PAGADO
        └─ Registra en historial
                │
                ▼
        Estado: PAGADO
```

---

## 7. Flujo Detallado: Asignar Médico y Cerrar

```
GESTOR/ADMIN
        │
        ▼
POST /solicitudes/{id}/asignar-medico
        │ (igual que asignar gestor, pero rol MEDICO)
        ▼
Estado: ASIGNADO_MEDICO

        │
MEDICO/GESTOR/ADMIN evalúa
        ▼
POST /solicitudes/{id}/cerrar
body: { resultado_evaluacion, observaciones, fecha_evaluacion }
        │
        ├─ Crea ResultadoMedico
        ├─ Actualiza solicitud.estado_atencion = ATENDIDO
        └─ Registra en historial
                │
                ▼
        Estado: CERRADO (terminal)
```

---

## 8. Flujo de Archivos

```
Cliente/operador sube archivo
        │
        ▼
POST /archivos/upload (multipart/form-data)
        │
        ├─ FILE_STORAGE=local  → guarda en /uploads/{uuid}.{ext}
        │   FILE_STORAGE=s3    → sube a S3 con ruta {bucket}/{key}
        ├─ Crea registro Archivo en DB
        └─ Vincula a solicitud via SolicitudArchivo
                │
                ▼
GET /solicitudes/{id}/descargar/{archivo_id}
        │
        ├─ Verifica permisos del usuario
        ├─ local → devuelve FileResponse
        └─ s3    → genera URL prefirmada y redirige
```

---

## 9. Ciclo Petición-Respuesta HTTP

```
Navegador
    │  1. Request HTTP con cookie de sesión
    ▼
SessionMiddleware (middleware/session_middleware.py)
    │  2. Lee cookie → busca Session en DB → obtiene user_id
    │  3. Adjunta current_user al request state
    ▼
Router FastAPI (api/*.py)
    │  4. Extrae parámetros, body (Pydantic validation)
    ▼
Service Layer (services/*.py)
    │  5. Lógica de negocio + verificación de policy
    ▼
SQLAlchemy async session (database.py)
    │  6. Query async a DB
    ▼
MySQL / SQLite
    │  7. Resultado
    ▼
Pydantic schema → JSON response
    │  8. Serialización y respuesta
    ▼
Navegador / React
```

---

## 10. Trazabilidad y Auditoría

Cada acción relevante genera una entrada en `solicitud_estado_historial`:

```
solicitud_id  | estado_anterior | estado_nuevo | accion       | user_id | timestamp
─────────────────────────────────────────────────────────────────────────────────────
uuid-solicitud | REGISTRADO      | ASIGNADO_GESTOR | asignar_gestor | user-1 | 2025-01-15 10:30
uuid-solicitud | ASIGNADO_GESTOR | PAGADO          | registrar_pago | user-2 | 2025-01-16 09:00
uuid-solicitud | PAGADO          | ASIGNADO_MEDICO | asignar_medico | user-2 | 2025-01-16 09:05
uuid-solicitud | ASIGNADO_MEDICO | CERRADO         | cerrar         | user-3 | 2025-01-17 14:00
```
