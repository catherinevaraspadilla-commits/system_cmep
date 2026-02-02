# 4. Acciones / Use Cases (Reglas de Negocio)

Esta sección define, para cada acción del sistema CMEP, una **ficha de acción**
que especifica de forma determinista:

- Precondiciones (rol + estado operativo)
- Cambios en base de datos
- Auditoría obligatoria
- Errores esperados

Estas fichas constituyen la **base directa para implementar el backend
(FastAPI)** y garantizan que el comportamiento del sistema sea coherente con la
**POLICY**.

---

## 4.1. Convenciones y Reglas Globales

- **Fuente de autorización:**  
  Toda acción se autoriza exclusivamente mediante la **POLICY**, evaluada
  contra la combinación `(rol_usuario, estado_operativo_derivado)`.

- **Auditoría obligatoria:**  
  Toda acción que modifique datos debe registrar eventos en
  `solicitud_estado_historial` con:
  - `solicitud_id`
  - `campo`
  - `valor_anterior`
  - `valor_nuevo`
  - `cambiado_por`
  - `cambiado_en`
  - `comentario` (opcional)

- **Transacciones:**  
  Acciones que impliquen múltiples escrituras (por ejemplo, reasignaciones)
  deben ejecutarse dentro de una **transacción atómica**.

- **Asignabilidad de personal:**  
  Para asignar una persona a un rol operativo (`OPERADOR`, `GESTOR`, `MEDICO`)
  se debe validar:
  - Existe un registro en `empleado`
  - `empleado.estado_empleado = 'ACTIVO'`
  - `empleado.rol_empleado = rol`  
  *(Regla R10)*

- **Pagos:**  
  Se permiten **múltiples pagos por solicitud**.

- **MVP:**  
  - `EDITAR_DATOS` permite editar cualquier dato.
  - `OVERRIDE` permite ejecutar cualquier acción, con auditoría reforzada.

---

## 4.2. Listado de Acciones

Las acciones soportadas por el sistema CMEP son:

- `EDITAR_DATOS`
- `ASIGNAR_GESTOR`
- `CAMBIAR_GESTOR`
- `REGISTRAR_PAGO`
- `ASIGNAR_MEDICO`
- `CAMBIAR_MEDICO`
- `CERRAR`
- `CANCELAR`
- `OVERRIDE`

---

## 4.3. Fichas de Acciones

A continuación se detalla cada acción de forma completa.

---

### 4.3.1. Acción: EDITAR_DATOS

#### Precondiciones
- Permitido por **POLICY** para el `(rol, estado_operativo)` actual.
- Usuario autenticado con `users.estado = 'ACTIVO'`.

#### Cambios en Base de Datos
- MVP: se permite editar cualquier campo de negocio relacionado a la solicitud,
  incluyendo (pero no limitado a):
  - `solicitud_cmep`
  - referencias a `cliente_id`, `apoderado_id`, `servicio_id`
  - fechas, descripciones y estados (cuando aplique)
- Toda actualización debe cumplir:
  - Integridad referencial (FK)
  - Constraints definidos en el modelo

#### Auditoría
- Insertar **una fila por cada campo modificado** en
  `solicitud_estado_historial`:
  - `campo` = nombre del campo
  - `valor_anterior`
  - `valor_nuevo`

- Si se modifican múltiples tablas, registrar igualmente los cambios relevantes
  a nivel de solicitud.

#### Errores Esperados
- `403 Forbidden`: no permitido por POLICY
- `404 Not Found`: solicitud no existe
- `422 Unprocessable Entity`: violación de constraint, FK inválida o valores inválidos

---

### 4.3.2. Acción: ASIGNAR_GESTOR

#### Precondiciones
- Permitido por POLICY.
- Persona asignada cumple R10:
  - Existe `empleado`
  - `estado_empleado = 'ACTIVO'`
  - `rol_empleado = 'GESTOR'`

#### Cambios en Base de Datos (transacción obligatoria)
1. Si existe una asignación vigente para `(solicitud_id, rol='GESTOR')`,
   actualizar esa fila a `es_vigente = 0`.
2. Insertar nueva fila en `solicitud_asignacion` con:
   - `rol = 'GESTOR'`
   - `persona_id = <gestor>`
   - `es_vigente = 1`
   - `asignado_por = <user_id>`
   - `fecha_asignacion = NOW()`

#### Auditoría
- `campo = 'asignacion_gestor'`
- `valor_anterior = <gestor anterior o NULL>`
- `valor_nuevo = <gestor nuevo>`

#### Errores Esperados
- `403 Forbidden`: no permitido
- `422 Unprocessable Entity`: persona no cumple R10
- `409 Conflict`: colisión con UNIQUE `(solicitud_id, rol, es_vigente)`

---

### 4.3.3. Acción: CAMBIAR_GESTOR

#### Precondiciones
- Permitido por POLICY.
- Persona asignada cumple R10 para rol `GESTOR`.

#### Cambios en Base de Datos
- Mismo impacto que `ASIGNAR_GESTOR`:
  - Cerrar asignación vigente
  - Insertar nueva asignación vigente
- Operación ejecutada en transacción.

#### Auditoría
- `campo = 'cambio_gestor'` (o `asignacion_gestor`)
- Registrar valor anterior y nuevo.

#### Errores Esperados
- `403`, `422`, `409` (idénticos a ASIGNAR_GESTOR)

---

### 4.3.4. Acción: REGISTRAR_PAGO

#### Precondiciones
- Permitido por POLICY.
- Validaciones mínimas:
  - `monto > 0`
  - `moneda` consistente con la solicitud *(R23)*

- Evidencia/documento: **opcional en MVP**.

#### Cambios en Base de Datos
1. Insertar fila en `pago_solicitud` con:
   - `solicitud_id`
   - `canal_pago`
   - `fecha_pago`
   - `monto`
   - `moneda`
   - `referencia_transaccion`
   - auditoría (`created_*`)
2. Validar el pago:
   - `validated_by = <user_id>`
   - `validated_at = NOW()`
3. Actualizar `solicitud_cmep.estado_pago = 'PAGADO'`
4. (Opcional) Si existe archivo de evidencia:
   - Insertar en `solicitud_archivo (solicitud_id, archivo_id, pago_id)`

#### Auditoría
- `campo = 'pago_registrado'` con `valor_nuevo = <pago_id>`
- `campo = 'estado_pago'`: valor anterior → `PAGADO` (si cambió)

#### Errores Esperados
- `403 Forbidden`
- `422 Unprocessable Entity`
- `404 Not Found`

---

### 4.3.5. Acción: ASIGNAR_MEDICO

#### Precondiciones
- Permitido por POLICY.
- Requisito de flujo:
  - `solicitud_cmep.estado_pago = 'PAGADO'`
- Persona asignada cumple R10 para rol `MEDICO`.

#### Cambios en Base de Datos (transacción obligatoria)
1. Cerrar asignación vigente con rol `MEDICO` (si existe).
2. Insertar nueva asignación vigente:
   - `rol = 'MEDICO'`
   - `es_vigente = 1`

#### Auditoría
- `campo = 'asignacion_medico'`
- Registrar valor anterior y nuevo.

#### Errores Esperados
- `403 Forbidden`
- `422 Unprocessable Entity` (no cumple R10 o no está PAGADO)
- `409 Conflict`

---

### 4.3.6. Acción: CAMBIAR_MEDICO

#### Precondiciones
- Permitido por POLICY.
- Persona asignada cumple R10 para rol `MEDICO`.

#### Cambios en Base de Datos
- Igual que `ASIGNAR_MEDICO`:
  - cerrar vigente
  - insertar nueva asignación vigente
- Ejecutado en transacción.

#### Auditoría
- `campo = 'cambio_medico'` (o `asignacion_medico`)

#### Errores Esperados
- `403`, `422`, `409` (idénticos a ASIGNAR_MEDICO)

---

### 4.3.7. Acción: CERRAR

#### Precondiciones
- Permitido por POLICY.
- Estado operativo actual: típicamente `ASIGNADO_MEDICO`.

#### Cambios en Base de Datos
1. Actualizar `solicitud_cmep.estado_atencion = 'ATENDIDO'`

#### Auditoría
- `campo = 'estado_atencion'`
- `valor_anterior → 'ATENDIDO'`

#### Errores Esperados
- `403 Forbidden`
- `409 Conflict` (ya ATENDIDO o CANCELADO)

---

### 4.3.8. Acción: CANCELAR

#### Precondiciones
- Permitido por POLICY.

#### Cambios en Base de Datos
1. Actualizar `solicitud_cmep.estado_atencion = 'CANCELADO'`

#### Auditoría
- `campo = 'estado_atencion'`
- `valor_anterior → 'CANCELADO'`

#### Errores Esperados
- `403 Forbidden`
- `409 Conflict` (ya CANCELADO)

---

### 4.3.9. Acción: OVERRIDE

#### Precondiciones
- Permitido por POLICY.
- Solo `ADMIN` cuando el estado operativo es `CERRADO` o `CANCELADO`.

#### Cambios en Base de Datos
- MVP: permite ejecutar cualquier modificación equivalente a las demás acciones:
  - editar datos
  - reasignar
  - registrar pagos
  - cerrar
  - cancelar

#### Auditoría (reforzada)
- Registrar evento explícito:
  - `campo = 'override'`
  - `valor_nuevo = 'true'`
  - `comentario` **obligatorio**
- Además, registrar los cambios específicos campo por campo
  (igual que en `EDITAR_DATOS`).

#### Errores Esperados
- `403 Forbidden`: no permitido
- `422 Unprocessable Entity`: violación de constraints o FK
