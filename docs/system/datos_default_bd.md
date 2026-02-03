# Datos Default de la Base de Datos

> Valores iniciales cargados por `infra/seed_dev.py`

---

## 1. Servicio

Un unico servicio en el catalogo:

| Campo | Valor |
|-------|-------|
| servicio_id | 1 |
| descripcion_servicio | Certificado Medico de Evaluacion Profesional |
| tarifa_servicio | 200.00 |
| moneda_tarifa | PEN |

**Impacto en Solicitud Detalle:**
- Al crear solicitud, se selecciona este servicio
- `tarifa_monto` y `tarifa_moneda` de la solicitud se copian de la tarifa del servicio
- Se muestra como "Tarifa regular" en el bloque de Pago

---

## 2. Usuarios Seed

| # | Nombres | Apellidos | Email | Password | Roles | Estado |
|---|---------|-----------|-------|----------|-------|--------|
| 1 | Admin | Sistema | admin@cmep.local | admin123 | ADMIN | ACTIVO |
| 2 | Ana | Operadora | operador@cmep.local | operador123 | OPERADOR | ACTIVO |
| 3 | Carlos | Gestor | gestor@cmep.local | gestor123 | GESTOR | ACTIVO |
| 4 | Maria | Medico | medico@cmep.local | medico123 | MEDICO | ACTIVO |
| 5 | Suspendido | Test | suspendido@cmep.local | suspendido123 | OPERADOR | SUSPENDIDO |

Los usuarios 2, 3 y 4 tambien tienen registro en la tabla `empleado` con su rol correspondiente.
El usuario 4 (Medico) ademas tiene registro en `medico_extra` con CMP=12345, especialidad="Medicina Ocupacional".

---

## 3. Clientes Seed

| Nombres | Apellidos | Tipo Doc | Numero Doc | Celular |
|---------|-----------|----------|------------|---------|
| Juan | Perez Lopez | DNI | 12345678 | 987654321 |
| Rosa | Garcia Torres | DNI | 87654321 | 912345678 |
| Pedro | Ramirez Silva | CE | CE001234 | 999888777 |

---

## 4. Promotores Seed

| Tipo | Nombre | Fuente | Detalle |
|------|--------|--------|---------|
| PERSONA | Luis Promotor Reyes | Cliente referente | DNI 11111111 |
| EMPRESA | Notaria Gonzales & Asociados | Notaria | RUC 20123456789 |

---

## 5. Roles del Sistema

| Rol | Descripcion |
|-----|-------------|
| ADMIN | Acceso total, override, reportes, gestion de usuarios |
| OPERADOR | Registro y seguimiento de solicitudes |
| GESTOR | Gestion administrativa de solicitudes asignadas |
| MEDICO | Evaluacion medica, cierre de solicitudes |

---

## 6. Enums y Valores Default

### EstadoAtencion (solicitud_cmep.estado_atencion)
| Valor | Uso |
|-------|-----|
| REGISTRADO | Default al crear solicitud |
| EN_PROCESO | Reservado (no usado actualmente) |
| ATENDIDO | Al cerrar solicitud |
| OBSERVADO | Reservado |
| CANCELADO | Al cancelar solicitud |

### EstadoPago (solicitud_cmep.estado_pago)
| Valor | Uso |
|-------|-----|
| PENDIENTE | Default al crear solicitud |
| PAGADO | Al registrar pago |
| OBSERVADO | Reservado |

### EstadoCertificado (solicitud_cmep.estado_certificado)
| Valor | Uso |
|-------|-----|
| APROBADO | Gestor/Admin marca resultado aprobado |
| OBSERVADO | Gestor/Admin marca resultado con observaciones |

### TarifaMoneda
| Valor |
|-------|
| PEN |
| USD |

### TipoDocumento (personas)
| Valor |
|-------|
| DNI |
| CE |
| PASAPORTE |
| RUC |

### TipoPromotor
| Valor |
|-------|
| PERSONA |
| EMPRESA |
| OTROS |

---

## 7. Valores Default al Crear Solicitud

Cuando se crea una nueva solicitud via POST /solicitudes:

| Campo | Valor Default | Origen |
|-------|---------------|--------|
| estado_atencion | REGISTRADO | Hardcoded en modelo |
| estado_pago | PENDIENTE | Hardcoded en modelo |
| estado_certificado | NULL | Sin evaluacion aun |
| tarifa_monto | 200.00 (si servicio_id=1) | Copiado del servicio |
| tarifa_moneda | PEN (si servicio_id=1) | Copiado del servicio |
| tipo_atencion | NULL | Lo ingresa el gestor |
| lugar_atencion | NULL | Lo ingresa el gestor |
| codigo | NULL | Se puede generar despues |

### Campos que siempre estan vacios al inicio
- **tipo_atencion**: Lo define el gestor en el bloque de Gestion administrativa
- **lugar_atencion**: Lo define el gestor en el bloque de Gestion administrativa
- **estado_certificado**: Se define durante la evaluacion medica
- **fecha_cierre**: Se llena al cerrar (accion CERRAR)
- **fecha_cancelacion**: Se llena al cancelar (accion CANCELAR)
- **motivo_cancelacion**: Se ingresa al cancelar

---

## 8. Estado Operativo (derivado, no almacenado)

El estado operativo se calcula a partir de las tablas, en este orden de prioridad:

| Prioridad | Condicion | Estado |
|-----------|-----------|--------|
| 1 | estado_atencion = CANCELADO | CANCELADO |
| 2 | estado_atencion = ATENDIDO | CERRADO |
| 3 | Tiene asignacion vigente MEDICO | ASIGNADO_MEDICO |
| 4 | estado_pago = PAGADO | PAGADO |
| 5 | Tiene asignacion vigente GESTOR | ASIGNADO_GESTOR |
| 6 | Default | REGISTRADO |

Este estado determina las acciones permitidas segun la POLICY.
