# 3. Estado Operativo Derivado (Mapping y Ejemplos)

Esta sección define cómo el sistema CMEP deriva el **estado operativo**
(`estado_operativo`) de una solicitud a partir de los estados persistidos en
base de datos y las asignaciones vigentes.

El **estado operativo no se almacena en la base de datos**.  
Se calcula exclusivamente en el backend y se utiliza como:

- Fuente de verdad para **control de permisos (POLICY)**
- Base del **workflow operativo**
- Entrada para el **comportamiento de la UI**

---

## 3.1. Estados Base Utilizados

El estado operativo se deriva **exclusivamente** a partir de:

- `solicitud_cmep.estado_atencion`
- `solicitud_cmep.estado_pago`
- Asignaciones vigentes en `solicitud_asignacion`
  - condición: `es_vigente = 1`

No se utiliza ningún otro campo ni cálculo adicional.

---

## 3.2. Estados Operativos

El sistema CMEP utiliza los siguientes estados operativos derivados:

- `REGISTRADO`
- `ASIGNADO_GESTOR`
- `PAGADO`
- `ASIGNADO_MEDICO`
- `CERRADO`
- `CANCELADO`

Estos estados **no coinciden necesariamente** con los estados persistidos
en la base de datos, sino que representan una abstracción operativa del
proceso completo.

---

## 3.3. Orden de Precedencia

El cálculo del estado operativo sigue un **orden estricto de precedencia**.

El **primer estado cuya condición se cumpla** es el que se asigna como
estado operativo actual.

### Orden de evaluación (de mayor a menor prioridad):

1. `CANCELADO`
2. `CERRADO`
3. `ASIGNADO_MEDICO`
4. `PAGADO`
5. `ASIGNADO_GESTOR`
6. `REGISTRADO`

Este orden garantiza que:

- El estado operativo **avance correctamente** conforme progresa el flujo.
- Estados finales (CANCELADO, CERRADO) **siempre prevalezcan**, incluso si
  existen asignaciones previas o pagos registrados.

---

## 3.4. Reglas de Derivación

A continuación se definen las reglas formales para cada estado operativo.

---

### REGISTRADO

**Condición:**

- Ninguna de las reglas siguientes se cumple.

**Interpretación:**

- Solicitud recién creada.
- No existe asignación relevante.
- No se ha registrado ni validado un pago.

---

### ASIGNADO_GESTOR

**Condición:**

- Existe una asignación vigente (`es_vigente = 1`)
- Con `rol = 'GESTOR'`

**Interpretación:**

- La solicitud ya fue tomada por un gestor.
- Aún no se ha registrado un pago válido.

---

### PAGADO

**Condición:**

- `solicitud_cmep.estado_pago = 'PAGADO'`

**Interpretación:**

- El gestor registró y validó el pago del cliente.
- La existencia de una asignación a gestor **no impide**
  que el estado operativo avance a `PAGADO`.

---

### ASIGNADO_MEDICO

**Condición:**

- `solicitud_cmep.estado_pago = 'PAGADO'`
- Existe una asignación vigente con `rol = 'MEDICO'`

**Interpretación:**

- La solicitud está pagada.
- Fue asignada a un médico para su evaluación.

---

### CERRADO

**Condición:**

- `solicitud_cmep.estado_atencion = 'ATENDIDO'`

**Interpretación:**

- La atención médica fue completada.
- La solicitud se considera finalizada, independientemente
  de asignaciones previas.

---

### CANCELADO

**Condición:**

- `solicitud_cmep.estado_atencion = 'CANCELADO'`

**Interpretación:**

- La solicitud fue cancelada.
- No puede continuar el flujo normal bajo ninguna circunstancia.

---

## 3.5. Ejemplos de Derivación

A continuación se muestran ejemplos concretos de cómo se calcula el estado
operativo a partir de los estados base.

---

**Ejemplo 1**

- `estado_atencion = REGISTRADO`
- `estado_pago = PENDIENTE`
- Sin asignación de gestor

➡ **Estado operativo:** `REGISTRADO`

---

**Ejemplo 2**

- `estado_pago = PENDIENTE`
- Existe asignación vigente de `GESTOR`

➡ **Estado**
