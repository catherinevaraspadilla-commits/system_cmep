# Seed de Produccion — Analisis Detallado y Riesgos

> Archivo analizado: `infra/seed_dev.py`
> Fecha: 2026-02-03

---

## 1. Que hace el seed actual

### Flujo de ejecucion

```
seed_dev.py --mysql
    |
    ├─ 1. Conecta a BD (MySQL via _get_engine si --mysql, SQLite si no)
    ├─ 2. CREATE_ALL: crea las 19 tablas si no existen (metadata.create_all)
    ├─ 3. Verifica si ya hay datos (SELECT COUNT(*) FROM users)
    │     └─ Si hay datos → DELETE de todas las tablas en orden FK
    ├─ 4. Inserta Personas + Users + Empleados + MedicoExtra
    ├─ 5. Inserta Promotores (con persona si tipo PERSONA)
    ├─ 6. Inserta Clientes (con persona)
    ├─ 7. Inserta Servicios
    └─ 8. COMMIT
```

### Datos que inserta

| Entidad | Cantidad | Detalle |
|---------|----------|---------|
| **Personas** | 10 | 5 usuarios + 3 clientes + 1 promotor persona + 1 implícita |
| **Users** | 5 | admin, operador, gestor, medico, suspendido |
| **UserRole** | 5 | 1 rol por usuario |
| **Empleados** | 3 | operador, gestor, medico |
| **MedicoExtra** | 1 | CMP 12345, Medicina Ocupacional |
| **Clientes** | 3 | Juan Perez, Rosa Garcia, Pedro Ramirez |
| **Promotores** | 2 | 1 persona (Luis Reyes), 1 empresa (Notaria Gonzales) |
| **Servicios** | 1 | "Certificado Medico de Evaluacion Profesional" PEN 200.00 |

### Credenciales insertadas

| Email | Password | Rol | Estado |
|-------|----------|-----|--------|
| admin@cmep.local | admin123 | ADMIN | ACTIVO |
| operador@cmep.local | operador123 | OPERADOR | ACTIVO |
| gestor@cmep.local | gestor123 | GESTOR | ACTIVO |
| medico@cmep.local | medico123 | MEDICO | ACTIVO |
| suspendido@cmep.local | suspendido123 | OPERADOR | SUSPENDIDO |

### Tablas que el seed NO toca (quedan vacias)

- `solicitud_cmep`, `solicitud_asignacion`, `solicitud_estado_historial`
- `pago_solicitud`, `archivos`, `solicitud_archivo`, `resultado_medico`
- `cliente_apoderado`
- `sessions`, `password_resets`, `user_permissions`

---

## 2. Riesgos Detectados

### RIESGO CRITICO: Re-seed borra TODO

**Lineas 165-178**: Si ya existen usuarios, el seed ejecuta `DELETE FROM` en TODAS las 18 tablas en orden FK inverso. Esto borra solicitudes, pagos, archivos, historial — todo.

```python
if count and count > 0:
    for table in ["solicitud_archivo", "archivos", ..., "personas"]:
        await db.execute(text(f"DELETE FROM {table}"))
```

**Impacto en produccion**: Si alguien ejecuta el seed por error despues de que el sistema ya tiene datos reales, se pierde TODA la informacion.

**Severidad**: CRITICA
**Probabilidad**: Media (error humano, script ejecutado por accidente)

---

### RIESGO ALTO: Passwords en texto plano en el codigo

Las passwords estan hardcodeadas: `admin123`, `operador123`, etc. Si este script se ejecuta en produccion, los usuarios quedan con passwords triviales y conocidas publicamente (estan en el repo).

**Severidad**: ALTA
**Probabilidad**: Alta (es el comportamiento actual)

---

### RIESGO MEDIO: create_all en produccion

**Linea 157-158**: El seed ejecuta `Base.metadata.create_all` que crea tablas. En produccion con RDS esto:
- Funciona la primera vez (tablas nuevas)
- Es idempotente (no falla si ya existen)
- Pero NO migra esquemas — si el modelo cambio, no aplica ALTER TABLE

Esto no es un bug, pero depender de `create_all` en produccion en lugar de Alembic es fragil.

**Severidad**: MEDIA
**Probabilidad**: Baja (solo relevante si cambian modelos)

---

### RIESGO MEDIO: Auto-increment no se resetea en MySQL

Cuando se borran datos con DELETE, MySQL NO resetea los contadores auto-increment. Si se re-seedea:
- persona_id empezaria desde 11 (no desde 1)
- user_id empezaria desde 6

Esto no es un bug funcional, pero puede confundir si se esperan IDs especificos.

**Severidad**: BAJA
**Probabilidad**: Alta (ocurre siempre en re-seed MySQL)

---

### RIESGO BAJO: Datos de prueba mezclados con produccion

Clientes ficticios (Juan Perez DNI 12345678), promotores ficticios, y el usuario "Suspendido Test" no son datos de produccion. Si se usa el mismo seed, quedan en la BD real.

**Severidad**: BAJA
**Probabilidad**: Alta (el seed actual solo tiene datos de prueba)

---

### RIESGO BAJO: No hay flag --prod ni confirmacion

El seed no distingue entre dev y produccion. No hay confirmacion "estas seguro?" ni flag de proteccion. Un `python seed_dev.py --mysql` borra todo sin preguntar.

**Severidad**: MEDIA (combinada con el riesgo de re-seed)
**Probabilidad**: Media

---

## 3. Que NECESITA produccion vs que es solo dev

| Dato | Necesario en PROD | Necesario en DEV |
|------|-------------------|------------------|
| **Servicio** (CMEP, PEN 200) | SI — el sistema necesita al menos 1 servicio | SI |
| **User ADMIN** | SI — necesitas al menos 1 admin para gestionar | SI |
| **Users operador/gestor/medico** | DEPENDE — los reales se crean via /admin/usuarios | SI (testing) |
| **User suspendido** | NO — solo para testing | SI |
| **Clientes ficticios** | NO — los reales se crean via solicitudes | SI (testing) |
| **Promotores ficticios** | NO — los reales se crean via solicitudes | SI (testing) |
| **Empleados** | DEPENDE — los reales se crean al crear usuario con rol | SI |

---

## 4. Recomendacion

### Opcion A: Separar en dos scripts (RECOMENDADO)

1. **`seed_dev.py`** (actual, sin cambios) — para desarrollo y testing local
2. **`seed_prod.py`** (nuevo) — para produccion, solo lo minimo:
   - 1 servicio
   - 1 usuario admin con password segura (parametro obligatorio)
   - Sin datos ficticios
   - Sin DELETE destructivo
   - Con confirmacion interactiva

### Opcion B: Agregar flag --prod al seed actual

Agregar modo `--prod` que:
- Solo inserta servicio + admin
- Requiere password como parametro
- No borra datos existentes
- Muestra confirmacion

### Opcion C: Mantener como esta

Usar el seed actual tal cual para produccion y despues:
- Cambiar passwords manualmente via `/admin/usuarios/{id}/reset-password`
- Eliminar usuario suspendido manualmente
- Aceptar que hay datos ficticios en la BD

---

## 5. Resumen de decision necesaria

| Pregunta | Impacto |
|----------|---------|
| Quieres datos ficticios en produccion? | Si NO → necesitas seed_prod.py |
| El admin de produccion puede tener password `admin123` inicialmente? | Si NO → password como parametro |
| Necesitas proteccion contra re-seed accidental? | Si SI → agregar confirmacion o flag |
| Los otros usuarios (operador, gestor, medico) existen en la vida real? | Si SI → incluirlos con datos reales |
