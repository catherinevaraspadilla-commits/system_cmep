# Pagina: Detalle de Solicitud (SolicitudDetalle)

> Ruta: `/app/solicitudes/:id`
> Acceso: todos los roles (ADMIN, OPERADOR, GESTOR, MEDICO)
> Ultima actualizacion: 2026-02-03

---

## 1. Arquitectura de archivos

```
frontend/src/pages/app/
  SolicitudDetalle.tsx          # Orquestador principal (~530 lineas)
  solicitud/
    detailStyles.ts             # Constantes de estilo compartidas
    detailHelpers.ts            # Funciones puras de estado visual
    BlockGestion.tsx            # Bloque A: Gestion administrativa
    BlockPago.tsx               # Bloque B: Pago
    BlockEvaluacion.tsx         # Bloque C: Evaluacion medica
frontend/src/components/
  WorkflowStepper.tsx           # Stepper visual del flujo
frontend/src/types/
  solicitud.ts                  # Tipos TypeScript (DTOs, requests)
```

---

## 2. APIs consumidas

### GET `/solicitudes/{id}` — Carga detalle
- **Cuando**: al montar el componente y post-accion (recarga completa)
- **Respuesta**: `ApiResponse<SolicitudDetailDTO>`
- **Backend**: `solicitudes.py` > `get_solicitud_detail` > `solicitud_service.build_detail_dto`
- **Tablas leidas**: solicitud_cmep, personas (cliente, apoderado, medico, gestor), promotores, servicios, solicitud_asignacion, pago_solicitud, archivos, solicitud_archivo, resultado_medico, solicitud_estado_historial

### PATCH `/solicitudes/{id}` — Editar datos / estado certificado
- **Cuando**: guardar formulario "Editar datos" o cambiar select estado_certificado
- **Request**: `EditSolicitudRequest`
- **Campos editables**: tipo_atencion, lugar_atencion, comentario, servicio_id, estado_certificado, cliente_nombres, cliente_apellidos, cliente_celular, cliente_email
- **Tablas escritas**: solicitud_cmep (campos directos), personas (campos cliente_*), solicitud_estado_historial (auditoria)
- **Requiere accion**: EDITAR_DATOS en acciones_permitidas

### POST `/solicitudes/{id}/asignar-gestor`
- **Request**: `{ persona_id_gestor: int }`
- **Tablas escritas**: solicitud_asignacion (nueva fila, vigente=true), solicitud_estado_historial
- **Efecto**: estado operativo cambia de REGISTRADO a ASIGNADO_GESTOR

### POST `/solicitudes/{id}/cambiar-gestor`
- **Request**: `{ persona_id_gestor: int }`
- **Tablas escritas**: solicitud_asignacion (anterior vigente=false, nueva vigente=true), solicitud_estado_historial

### POST `/solicitudes/{id}/registrar-pago`
- **Request**: `{ canal_pago, fecha_pago, monto, moneda, referencia_transaccion? }`
- **Tablas escritas**: pago_solicitud (nueva fila), solicitud_cmep (estado_pago=PAGADO), solicitud_estado_historial
- **Efecto**: estado operativo cambia de ASIGNADO_GESTOR a PAGADO

### POST `/solicitudes/{id}/asignar-medico`
- **Request**: `{ persona_id_medico: int }`
- **Tablas escritas**: solicitud_asignacion, solicitud_estado_historial
- **Efecto**: estado operativo cambia de PAGADO a ASIGNADO_MEDICO

### POST `/solicitudes/{id}/cambiar-medico`
- **Request**: `{ persona_id_medico: int }`
- **Tablas escritas**: solicitud_asignacion, solicitud_estado_historial

### POST `/solicitudes/{id}/cerrar`
- **Request**: `{ comentario? }`
- **Tablas escritas**: solicitud_cmep (estado_atencion=ATENDIDO, fecha_cierre, cerrado_por), solicitud_estado_historial
- **Efecto**: estado operativo cambia a CERRADO

### POST `/solicitudes/{id}/cancelar`
- **Request**: `{ comentario? }`
- **Tablas escritas**: solicitud_cmep (estado_atencion=CANCELADO, motivo_cancelacion, fecha_cancelacion, cancelado_por), solicitud_estado_historial
- **Efecto**: estado operativo cambia a CANCELADO

### POST `/solicitudes/{id}/override` (solo ADMIN)
- **Request**: `{ motivo, accion, payload }`
- **Solo disponible en**: CERRADO y CANCELADO
- **Sub-acciones**: EDITAR_DATOS, CAMBIAR_GESTOR, CAMBIAR_MEDICO, REGISTRAR_PAGO, CERRAR, CANCELAR

### GET `/empleados?rol={GESTOR|MEDICO}` — Listas para dropdowns
- **Cuando**: al abrir modal de asignar/cambiar gestor o medico
- **Tablas leidas**: personas, empleado, user_role

### POST `/solicitudes/{id}/archivos` — Upload archivo
- **Request**: FormData (file + tipo_archivo)
- **Tablas escritas**: archivos, solicitud_archivo

### GET `/archivos/{id}` — Download archivo
### DELETE `/archivos/{id}` — Eliminar archivo
- **Tablas escritas**: archivos, solicitud_archivo (cascade)

---

## 3. Estado operativo derivado

El estado operativo NO se almacena en BD. Se calcula cada vez a partir de campos reales:

```
Precedencia (primera condicion verdadera gana):
  CANCELADO:       estado_atencion = 'CANCELADO'
  CERRADO:         estado_atencion = 'ATENDIDO'
  ASIGNADO_MEDICO: estado_pago = 'PAGADO' AND medico vigente
  PAGADO:          estado_pago = 'PAGADO'
  ASIGNADO_GESTOR: gestor vigente
  REGISTRADO:      fallback
```

**Backend**: `estado_operativo.py` > `derivar_estado_operativo()`
**Campos fuente**: solicitud_cmep.estado_atencion, solicitud_cmep.estado_pago, solicitud_asignacion (vigentes)

---

## 4. POLICY (acciones permitidas por rol y estado)

El frontend NO calcula permisos. Usa `detail.acciones_permitidas` que viene del backend.

```
ADMIN:
  REGISTRADO:      EDITAR_DATOS, ASIGNAR_GESTOR, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_GESTOR: EDITAR_DATOS, REGISTRAR_PAGO, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  PAGADO:          EDITAR_DATOS, ASIGNAR_MEDICO, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_MEDICO: EDITAR_DATOS, CERRAR, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  CERRADO:         OVERRIDE
  CANCELADO:       OVERRIDE

OPERADOR:
  REGISTRADO:      EDITAR_DATOS, ASIGNAR_GESTOR, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_GESTOR: EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  PAGADO:          EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_MEDICO: EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  CERRADO:         (ninguna)
  CANCELADO:       (ninguna)

GESTOR:
  REGISTRADO:      EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_GESTOR: EDITAR_DATOS, REGISTRAR_PAGO, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  PAGADO:          EDITAR_DATOS, ASIGNAR_MEDICO, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_MEDICO: EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  CERRADO:         (ninguna)
  CANCELADO:       (ninguna)

MEDICO:
  REGISTRADO:      EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_GESTOR: EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  PAGADO:          EDITAR_DATOS, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  ASIGNADO_MEDICO: EDITAR_DATOS, CERRAR, CANCELAR, CAMBIAR_GESTOR, CAMBIAR_MEDICO
  CERRADO:         (ninguna)
  CANCELADO:       (ninguna)
```

**Backend**: `policy.py` > `POLICY` dict > `get_acciones_permitidas(roles, estado_operativo)`
**Frontend**: `can(action)` = `detail.acciones_permitidas.includes(action)`

---

## 5. Tablas involucradas

| Tabla | Lectura | Escritura | Desde |
|-------|---------|-----------|-------|
| solicitud_cmep | GET detalle | PATCH editar, cerrar, cancelar | Todas las operaciones |
| personas | GET detalle (cliente, apoderado, gestor, medico) | PATCH editar (cliente_*) | Via FK |
| clientes | GET detalle | - | Via FK solicitud.cliente_id |
| promotores | GET detalle | - | Via FK solicitud.promotor_id |
| servicios | GET detalle | - | Via FK solicitud.servicio_id |
| solicitud_asignacion | GET detalle (vigentes) | Asignar/Cambiar gestor/medico | Workflow |
| solicitud_estado_historial | GET detalle (historial) | Todas las acciones (auditoria) | Auditoria |
| pago_solicitud | GET detalle (pagos) | Registrar pago | Pago |
| archivos | GET detalle, download | Upload, delete | Archivos M4 |
| solicitud_archivo | GET detalle | Upload, delete | Archivos M4 |
| resultado_medico | GET detalle | - (futuro) | Evaluacion |
| empleado + user_role | GET empleados dropdown | - | Asignaciones |

---

## 6. Enums relevantes

| Enum | Valores | Tabla/Campo |
|------|---------|-------------|
| EstadoPago | PENDIENTE, PAGADO, OBSERVADO | solicitud_cmep.estado_pago |
| EstadoAtencion | REGISTRADO, EN_PROCESO, ATENDIDO, OBSERVADO, CANCELADO | solicitud_cmep.estado_atencion |
| EstadoCertificado | APROBADO, OBSERVADO | solicitud_cmep.estado_certificado, resultado_medico.estado_certificado |
| TarifaMoneda | PEN, USD | solicitud_cmep.tarifa_moneda |
| RolAsignacion | OPERADOR, GESTOR, MEDICO | solicitud_asignacion.rol |
| TipoArchivo | EVIDENCIA_PAGO, DOCUMENTO, OTROS | archivos.tipo |
| EstadoOperativo (derivado) | REGISTRADO, ASIGNADO_GESTOR, PAGADO, ASIGNADO_MEDICO, CERRADO, CANCELADO | NO almacenado |

---

## 7. Estructura visual de la pagina

```
[Header compacto]
  Codigo | Badge estado | Cliente (doc) | Promotor | Fecha
  <- Volver a solicitudes

[WorkflowStepper]
  5 pasos: Registrado > Gestor asignado > Pagado > Medico asignado > Cerrado
  Colores: verde=completado, azul=actual, gris=pendiente
  Banner CANCELADA si aplica

[Alertas]
  Error (rojo) | Motivo cancelacion (amarillo)

[Datos del cliente] — fondo morado suave (#f3eef8)
  Tipo documento | Nro documento | Nombre | Celular
  Apoderado (si existe)
  Promotor (si existe)
  Info solicitud: tipo atencion, lugar, fecha creacion
  Boton "Editar datos" (en header del bloque)

[Edit form] — aparece al hacer clic en "Editar datos"
  Tipo atencion (select) | Lugar atencion (input)
  Comentario (textarea)
  Guardar | Cancelar

[Block A: Gestion administrativa] — colores segun estado visual
  Gestor asignado | Estado atencion
  Botones: Asignar/Cambiar gestor, Cancelar solicitud
  Modal inline: Asignar gestor (select empleados)

[Block B: Pago] — colores segun estado visual
  Estado pago | Tarifa | Pagos registrados
  Tabla de pagos (siempre visible)
  Boton: Registrar pago
  Modal inline: Registrar pago (canal, fecha, monto, moneda, ref)

[Block C: Evaluacion medica] — colores segun estado visual
  Medico asignado | Estado certificado (read) | Select estado certificado (funcional)
  Tabla resultados medicos (siempre visible)
  Observaciones del ultimo resultado
  Botones: Asignar/Cambiar medico, Cerrar solicitud
  Modales inline: Asignar medico, Cerrar solicitud

[Cancelar modal] — nivel orquestador (cross-cutting)
  Motivo (opcional) | Confirmar | Cancelar

[Archivos] — fondo blanco neutral
  Upload: file input + tipo archivo + boton subir
  Tabla: nombre, tipo, tamano, acciones (descargar, eliminar)

[Historial de cambios] — fondo blanco neutral
  Tabla: fecha, campo, anterior, nuevo, comentario
```

---

## 8. Colores de bloques por estado visual

Los bloques (Gestion, Pago, Evaluacion) cambian de color segun su estado derivado:

| Estado visual | Fondo | Borde | Dot | Condicion |
|---------------|-------|-------|-----|-----------|
| completed | #d1e7dd (verde claro) | #a3cfbb | #198754 | Bloque completado |
| in_progress | #cfe2ff (azul claro) | #9ec5fe | #0d6efd | Bloque en curso |
| pending | #f8f9fa (gris claro) | #dee2e6 | #adb5bd | Esperando paso anterior |
| blocked | #f8f9fa (gris claro) | #dee2e6 | #adb5bd | Bloqueado por dependencia |

### Logica de estado visual por bloque

**Gestion (BlockA)**:
- completed: gestor asignado
- in_progress: REGISTRADO (sin gestor)
- pending: CANCELADO sin gestor

**Pago (BlockB)**:
- completed: estado_pago === PAGADO
- in_progress: gestor asignado pero no pagado
- blocked: no hay gestor aun

**Evaluacion (BlockC)**:
- completed: CERRADO
- in_progress: medico asignado
- pending: pagado pero sin medico
- blocked: sin pago registrado

---

## 9. Patron de botones

Todos los botones siempre se renderizan. Si la accion no esta permitida, el boton aparece deshabilitado con texto explicativo:

```tsx
{can("ACCION") ? (
  <button onClick={handler} style={actionBtnStyle("#color")}>Label</button>
) : (
  <div>
    <button disabled style={disabledBtnStyle()}>Label</button>
    <div style={helperTextStyle}>{explicacion}</div>
  </div>
)}
```

---

## 10. Estado certificado (select funcional)

- **Ubicacion**: BlockEvaluacion.tsx
- **Valores**: APROBADO, OBSERVADO (enum EstadoCertificado)
- **Fuente de dato**: detail.estado_certificado (campo de solicitud_cmep)
- **Guardado**: onChange llama PATCH /solicitudes/{id} con { estado_certificado: value }
- **Deshabilitado cuando**: bloque bloqueado, solicitud terminal, o sin permiso EDITAR_DATOS
- **Backend**: estado_certificado esta en solicitud_fields del PATCH handler

---

## 11. Flujo tipico completo

1. REGISTRADO: Se crea solicitud. Block A en azul (in_progress), B y C en gris (blocked).
2. ASIGNAR_GESTOR: Admin/Operador asigna gestor. Block A pasa a verde, Block B a azul.
3. REGISTRAR_PAGO: Gestor/Admin registra pago. Block B pasa a verde, Block C a pending (gris, falta medico).
4. ASIGNAR_MEDICO: Se asigna medico. Block C pasa a azul (in_progress).
5. Se puede cambiar estado_certificado a APROBADO/OBSERVADO.
6. CERRAR: Medico/Admin cierra solicitud. Block C pasa a verde. Todos los bloques finales en verde.

---

## 12. Datos del DTO de detalle (SolicitudDetailDTO)

```typescript
interface SolicitudDetailDTO {
  solicitud_id: number;
  codigo: string | null;
  cliente: ClienteDTO;              // persona_id, doc, nombre, celular, tipo_documento, numero_documento
  apoderado: PersonaDTO | null;     // persona_id, tipo_documento, numero_documento, nombres, apellidos
  servicio: dict | null;
  estado_atencion: string;          // REGISTRADO | EN_PROCESO | ATENDIDO | OBSERVADO | CANCELADO
  estado_pago: string;              // PENDIENTE | PAGADO | OBSERVADO
  estado_certificado: string | null; // APROBADO | OBSERVADO
  tarifa_monto: number | null;
  tarifa_moneda: string | null;
  tipo_atencion: string | null;     // VIRTUAL | PRESENCIAL
  lugar_atencion: string | null;
  comentario: string | null;
  estado_operativo: string;         // DERIVADO: REGISTRADO|ASIGNADO_GESTOR|PAGADO|ASIGNADO_MEDICO|CERRADO|CANCELADO
  acciones_permitidas: string[];    // Array de acciones segun POLICY
  asignaciones_vigentes: {
    OPERADOR: { persona_id, nombre, rol } | null;
    GESTOR: { persona_id, nombre, rol } | null;
    MEDICO: { persona_id, nombre, rol } | null;
  };
  promotor: dict | null;            // tipo_promotor, nombre, ruc, email, celular, fuente_promotor
  pagos: PagoDTO[];                 // pago_id, canal_pago, fecha_pago, monto, moneda, referencia, validated_at
  archivos: dict[];                 // archivo_id, nombre, tipo, tamano_bytes
  historial: HistorialDTO[];        // historial_id, campo, valor_anterior, valor_nuevo, cambiado_por, cambiado_en
  resultados_medicos: ResultadoMedicoDTO[]; // resultado_id, medico_id, fecha, diagnostico, resultado, observaciones
  motivo_cancelacion: string | null;
  fecha_cierre: datetime | null;
  cerrado_por: number | null;
  fecha_cancelacion: datetime | null;
  cancelado_por: number | null;
  comentario_admin: string | null;
  created_at: datetime;
  updated_at: datetime | null;
}
```

---

## 13. Colores del badge de estado operativo

| Estado | Color | Hex |
|--------|-------|-----|
| REGISTRADO | Gris | #6c757d |
| ASIGNADO_GESTOR | Azul | #0d6efd |
| PAGADO | Verde | #198754 |
| ASIGNADO_MEDICO | Morado | #6f42c1 |
| CERRADO | Teal | #0d9488 |
| CANCELADO | Rojo | #dc3545 |

---

## 14. Secciones con colores especiales

| Seccion | Fondo | Borde |
|---------|-------|-------|
| Datos del cliente | #f3eef8 (morado suave) | #d1c4e9 |
| Cancelar modal | #fff5f5 (rojo suave) | #f5c6cb |
| Motivo cancelacion alert | #fff3cd (amarillo) | #ffc107 |
| Error alert | #f8d7da (rojo claro) | - |
| Archivos / Historial | #fff (blanco) | #dee2e6 |
| Edit form | #f8f9fa (gris) | #dee2e6 |
