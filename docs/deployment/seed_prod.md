# Seed de Produccion — Documentacion

---

## Que es

`infra/seed_prod.py` inserta los datos minimos para que CMEP funcione en produccion:

| Dato | Valor |
|------|-------|
| Servicio | Certificado Medico de Evaluacion Psicologica (PEN 200.00) |
| Admin | Hector Varas (hvarasg@hotmail.com) con rol ADMIN |

No inserta clientes, promotores, empleados ni datos de prueba. Esos se crean despues via la interfaz web.

---

## Diferencias con seed_dev.py

| | seed_dev.py | seed_prod.py |
|-|-------------|-------------|
| **Proposito** | Desarrollo y testing local | Produccion (RDS MySQL) |
| **Si ya hay datos** | BORRA todo y re-inserta | ABORTA sin cambios |
| **Usuarios** | 5 (admin, operador, gestor, medico, suspendido) | 1 (admin real) |
| **Passwords** | Hardcodeadas (admin123, etc.) | Parametro obligatorio `--password` |
| **Clientes** | 3 ficticios | Ninguno |
| **Promotores** | 2 ficticios | Ninguno |
| **Servicio** | "Evaluacion Profesional" | "Evaluacion Psicologica" |
| **SQLite** | Permitido | Bloqueado (solo MySQL) |
| **Confirmacion** | No pide | Pide "si/no" antes de ejecutar |

---

## Como ejecutar

### Prerequisitos

- RDS MySQL operativo con database `cmep_prod`
- Usuario `cmep_user` con permisos (SELECT, INSERT, UPDATE, DELETE)
- Acceso de red al RDS (tunel SSH, VPN, o IP autorizada en SG)
- Python 3.12+ con dependencias instaladas (`pip install -r backend/requirements.txt`)

### Comando

```bash
DB_URL="mysql+asyncmy://cmep_user:<PASSWORD>@cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306/cmep_prod" python infra/seed_prod.py --password varas123
```

### Que sucede

```
BD: cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306/cmep_prod
Admin: hvarasg@hotmail.com
Continuar? (si/no): si
Tablas creadas/verificadas.
Servicio: Certificado Medico de Evaluacion Psicologica (PEN 200.00)
Admin: hvarasg@hotmail.com (roles: ['ADMIN'])

Seed de produccion completado.
Proximo paso: login con el admin y crear usuarios reales via /app/usuarios
```

---

## Que se crea en la BD

### Tablas (19)

El script ejecuta `create_all` que crea las 19 tablas si no existen:

```
personas, users, user_role, user_permissions, sessions, password_resets,
clientes, cliente_apoderado, empleado, medico_extra, promotores, servicios,
solicitud_cmep, solicitud_asignacion, solicitud_estado_historial,
pago_solicitud, archivos, solicitud_archivo, resultado_medico
```

### Registros insertados

**Tabla `personas`** (1 registro):

| Campo | Valor |
|-------|-------|
| tipo_documento | DNI |
| numero_documento | 00000001 |
| nombres | Hector |
| apellidos | Varas |
| email | hvarasg@hotmail.com |

**Tabla `users`** (1 registro):

| Campo | Valor |
|-------|-------|
| persona_id | (FK a persona creada) |
| user_email | hvarasg@hotmail.com |
| password_hash | (bcrypt hash del --password) |
| estado | ACTIVO |

**Tabla `user_role`** (1 registro):

| Campo | Valor |
|-------|-------|
| user_id | (FK a user creado) |
| user_role | ADMIN |

**Tabla `servicios`** (1 registro):

| Campo | Valor |
|-------|-------|
| descripcion_servicio | Certificado Medico de Evaluacion Psicologica |
| tarifa_servicio | 200.00 |
| moneda_tarifa | PEN |

---

## Protecciones

1. **No borra datos**: Si ya hay usuarios, el script muestra mensaje y sale sin tocar nada
2. **Solo MySQL**: Si detecta SQLite en el URL, aborta
3. **Confirmacion**: Pide escribir "si" antes de ejecutar
4. **Password como parametro**: No hay passwords hardcodeadas en el codigo

---

## Despues del seed

1. Login: `https://cmep.<dominio>` con `hvarasg@hotmail.com` / la password que usaste
2. Ir a `/app/usuarios` y crear los usuarios reales:
   - Operadores (con rol OPERADOR + empleado)
   - Gestores (con rol GESTOR + empleado)
   - Medicos (con rol MEDICO + empleado + medico_extra)
3. Los clientes y promotores se crean automaticamente al registrar solicitudes
