# 1. Glosario y Enumeraciones del Sistema (Nivel BD)

Esta sección define los conceptos clave del negocio y las enumeraciones (ENUM)
utilizadas en la base de datos del sistema CMEP. Su objetivo es evitar
ambigüedades durante la implementación del backend, las reglas de negocio y la
generación automática de código.

## 1.1. Glosario de Conceptos

**Pago:** Monto que el cliente abona por el servicio solicitado. El pago es un
requisito previo para la asignación médica y puede incluir evidencias asociadas
(comprobantes).

**Atención:** Estado del trámite operativo de una solicitud. Representa el avance
del proceso administrativo, el cual incluye el paso de pago dentro de su flujo.

**Certificado:** Resultado posterior a la evaluación médica. Solo ocurre después
de que el pago ha sido realizado y validado.

**Estado operativo:** Estado derivado utilizado por el sistema para control de
permisos y workflow (**REGISTRADO, ASIGNADO_GESTOR, PAGADO,
ASIGNADO_MEDICO, CERRADO, CANCELADO**). No se almacena directamente en BD,
se calcula a partir de otros estados y asignaciones vigentes.

**Apoderado:** Persona asociada a un cliente que actúa en su representación para
una o más solicitudes.

**Override:** Acción excepcional autorizada que permite modificar datos o tarifas
fuera del flujo normal del sistema.

## 1.2. Enumeraciones de Base de Datos

### 1.2.1. Identidad

**persona.tipo_documento:**
- DNI
- CE
- PASAPORTE
- RUC

### 1.2.2. Clientes y Relaciones

**clientes.estado:**
- ACTIVO
- SUSPENDIDO

**cliente_apoderado.estado:**
- ACTIVO
- INACTIVO

### 1.2.3. Promotores

**promotores.tipo_promotor:**
- PERSONA
- EMPRESA
- OTROS

### 1.2.4. Empleados y Usuarios

**empleado.rol_empleado:**
- OPERADOR
- GESTOR
- MEDICO

**empleado.estado_empleado:**
- ACTIVO
- SUSPENDIDO
- VACACIONES
- PERMISO

**users.estado:**
- ACTIVO
- SUSPENDIDO

**user_role.user_role:**
- ADMIN
- OPERADOR
- GESTOR
- MEDICO

### 1.2.5. Solicitudes

**solicitud_cmep.estado_pago:**
- PENDIENTE: Pago aún no realizado o no validado.
- PAGADO: Pago aceptado como válido para avanzar en el flujo.
- OBSERVADO: Pago con observación que requiere revisión o corrección.

**solicitud_cmep.estado_atencion:**
- REGISTRADO
- EN_PROCESO
- ATENDIDO
- OBSERVADO
- CANCELADO

**solicitud_cmep.estado_certificado:**
- APROBADO
- OBSERVADO

**solicitud_asignacion.rol:**
- OPERADOR
- GESTOR
- MEDICO

### 1.2.6. Tarifas

**solicitud_cmep.tarifa_moneda:**
- PEN
- USD

**solicitud_cmep.tarifa_fuente:**
- SERVICIO
- OVERRIDE

### 1.2.7. Archivos

**archivos.tipo:**
- EVIDENCIA_PAGO
- DOCUMENTO
- OTROS
