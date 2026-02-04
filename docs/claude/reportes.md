# Reportes Admin (M7)

## Endpoint

`GET /admin/reportes?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&estado=ESTADO&agrupacion=mensual|semanal`

- Requiere rol ADMIN (dependency `require_admin`)
- Parametros opcionales: `desde` (default: 30 dias atras), `hasta` (default: hoy), `estado`, `agrupacion` (default: mensual)

## Estructura de la pagina (ReportesAdmin.tsx)

| Seccion | Descripcion |
|---------|-------------|
| Filtros | desde, hasta, estado, agrupacion, boton exportar CSV, boton reset |
| KPI cards | Solicitudes, Cerradas, Ingresos (PEN), Ticket promedio |
| Series temporales | 2 BarCharts (solicitudes y ingresos en el tiempo) |
| Distribucion | BarChart horizontal por estado_operativo (6 estados) |
| Ranking promotores | Tabla top 20 por clientes (nombre, clientes, solicitudes, %) |
| Ranking equipo | Tabs gestores/medicos/operadores, top 20 cada uno |

## Queries SQL (reportes_service.py)

### 1. KPIs

**Total solicitudes:**
```sql
SELECT COUNT(*) FROM solicitud_cmep WHERE created_at >= :desde AND created_at < :hasta
-- Si filtro por estado: usa subquery con CASE de estado_operativo
```

**Cerradas:**
```sql
SELECT COUNT(*) FROM solicitud_cmep
WHERE created_at >= :desde AND created_at < :hasta AND estado_atencion = 'ATENDIDO'
```

**Ingresos:**
```sql
SELECT COALESCE(SUM(monto), 0) FROM pago_solicitud
WHERE validated_at IS NOT NULL AND fecha_pago >= :desde AND fecha_pago < :hasta
```

**Ticket promedio:**
```
ingresos / COUNT(DISTINCT solicitud_id con pago validado)
-- Si no hay pagos: 0
```

### 2. Series temporales

**Agrupacion por periodo (dual DB):**
- SQLite: `strftime('%Y-%m', col)` / `strftime('%Y-W%W', col)`
- MySQL: `DATE_FORMAT(col, '%Y-%m')` / `CONCAT(DATE_FORMAT(col, '%Y'), '-W', LPAD(WEEK(col, 1), 2, '0'))`

Se detecta automaticamente via `settings.is_sqlite` (config.py).

**Solicitudes por periodo:**
```sql
SELECT periodo, COUNT(*) as solicitudes FROM solicitud_cmep
WHERE created_at >= :desde AND created_at < :hasta
GROUP BY periodo ORDER BY periodo
```

**Ingresos por periodo:**
```sql
SELECT periodo, COALESCE(SUM(monto), 0) as ingresos FROM pago_solicitud
WHERE validated_at IS NOT NULL AND fecha_pago >= :desde AND fecha_pago < :hasta
GROUP BY periodo ORDER BY periodo
```

Ambas series se merge: periodos que aparecen en una pero no en otra se completan con 0.

### 3. Distribucion por estado

```sql
-- Subquery con CASE para derivar estado_operativo
SELECT estado_operativo, COUNT(*) as cantidad
FROM (
    SELECT solicitud_id, CASE ... END as estado_operativo
    FROM solicitud_cmep WHERE created_at >= :desde AND created_at < :hasta
) sub
GROUP BY estado_operativo
```

Los 6 estados siempre se incluyen (con 0 si no hay datos):
REGISTRADO, ASIGNADO_GESTOR, PAGADO, ASIGNADO_MEDICO, CERRADO, CANCELADO

### 4. Ranking promotores

```sql
SELECT p.promotor_id,
    CASE
        WHEN p.tipo_promotor='PERSONA' THEN COALESCE(per.nombres || ' ' || per.apellidos, 'Persona')
        WHEN p.tipo_promotor='EMPRESA' THEN COALESCE(p.razon_social, 'Empresa')
        ELSE COALESCE(p.nombre_promotor_otros, 'Otro')
    END as nombre,
    COUNT(DISTINCT s.cliente_id) as clientes,
    COUNT(s.solicitud_id) as solicitudes
FROM promotores p
JOIN solicitud_cmep s ON s.promotor_id = p.promotor_id
LEFT JOIN personas per ON p.persona_id = per.persona_id
WHERE s.created_at >= :desde AND s.created_at < :hasta
GROUP BY p.promotor_id
ORDER BY clientes DESC LIMIT 20
```

Porcentaje = solicitudes / total_solicitudes * 100 (division por zero protegida).

### 5. Ranking equipo (por rol)

```sql
SELECT per.persona_id, per.nombres || ' ' || per.apellidos as nombre,
    COUNT(s.solicitud_id) as solicitudes,
    SUM(CASE WHEN s.estado_atencion='ATENDIDO' THEN 1 ELSE 0 END) as cerradas,
    MAX(s.updated_at) as ultima_actividad
FROM personas per
JOIN solicitud_asignacion sa ON sa.persona_id = per.persona_id
JOIN solicitud_cmep s ON s.solicitud_id = sa.solicitud_id
WHERE s.created_at >= :desde AND s.created_at < :hasta
    AND sa.rol = :rol AND sa.es_vigente = true
GROUP BY per.persona_id
ORDER BY solicitudes DESC LIMIT 20
```

Se ejecuta 3 veces: GESTOR, MEDICO, OPERADOR.

## Estado operativo (derivado, no almacenado)

Prioridad (primera coincidencia gana):

| # | Condicion | Estado |
|---|-----------|--------|
| 1 | estado_atencion = CANCELADO | CANCELADO |
| 2 | estado_atencion = ATENDIDO | CERRADO |
| 3 | estado_pago = PAGADO AND tiene asignacion MEDICO vigente | ASIGNADO_MEDICO |
| 4 | estado_pago = PAGADO | PAGADO |
| 5 | Tiene asignacion GESTOR vigente | ASIGNADO_GESTOR |
| 6 | Fallback | REGISTRADO |

Implementado como CASE SQL con subqueries correlacionadas en `_estado_operativo_sql()`.

## Tablas consultadas

- `solicitud_cmep` — datos principales de solicitudes
- `solicitud_asignacion` — asignaciones vigentes (gestor, medico, operador)
- `pago_solicitud` — pagos validados (validated_at IS NOT NULL)
- `promotores` — datos de promotor
- `personas` — nombres de personas (clientes, equipo, promotores persona)

## Edge cases

- **Sin datos en rango**: KPIs = 0, series/rankings = arrays vacios, frontend muestra "No hay datos..."
- **Division por zero**: ticket_promedio = 0 si no hay pagos; porcentaje promotor usa max(total, 1)
- **Periodos parciales**: merge de series garantiza que ambos graficos muestren todos los periodos
- **Compatibilidad DB**: `_format_periodo()` brancha entre SQLite (dev) y MySQL (prod) via `settings.is_sqlite`
- **403 si no es admin**: dependency `require_admin` bloquea acceso

## Base de datos en produccion

- MySQL 8 en RDS: `cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com:3306/cmep_prod`
- Usuario: `cmep_user` (SELECT, INSERT, UPDATE, DELETE)
- Conexion via App Runner con VPC Connector
- DB_URL inyectado desde Secrets Manager
