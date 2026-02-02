# CMEP — Registro de Riesgos Tecnicos

## Formato

| Campo | Descripcion |
|-------|-------------|
| ID | Identificador unico |
| Modulo | Modulo afectado |
| Riesgo | Descripcion del riesgo |
| Probabilidad | Alta / Media / Baja |
| Impacto | Alto / Medio / Bajo |
| Mitigacion | Accion preventiva o correctiva |
| Estado | Abierto / Mitigado / Cerrado |

---

## Riesgos identificados

### R-001 — CORS y cookies cross-origin

| Campo | Valor |
|-------|-------|
| ID | R-001 |
| Modulo | M1, M6 |
| Riesgo | Las cookies httpOnly no se envian correctamente entre frontend (localhost:3000 o CloudFront) y backend (localhost:8000 o App Runner) por configuracion CORS incorrecta |
| Probabilidad | Alta |
| Impacto | Alto — sin cookies, no hay sesion; toda la app queda inaccesible |
| Mitigacion | Configurar CORS desde M0 con `credentials: true` y `Access-Control-Allow-Credentials`. Testear cookies en dev con dominios separados antes de M6. En produccion: asegurar que frontend y backend compartan dominio o subdominios con cookie domain correcto |
| Estado | Abierto |

---

### R-002 — Transcripcion incorrecta de la POLICY

| Campo | Valor |
|-------|-------|
| ID | R-002 |
| Modulo | M3 |
| Riesgo | La POLICY (4 roles x 6 estados = 24 combinaciones) se transcribe manualmente al codigo. Un error permite o bloquea acciones incorrectamente |
| Probabilidad | Media |
| Impacto | Alto — acciones no autorizadas o flujo bloqueado |
| Mitigacion | Test unitario exhaustivo que verifica la matriz completa contra el doc 05. La POLICY se define como diccionario literal en el codigo, no se genera dinamicamente. Code review antes de merge |
| Estado | Abierto |

---

### R-003 — Orden de precedencia del estado operativo

| Campo | Valor |
|-------|-------|
| ID | R-003 |
| Modulo | M3 |
| Riesgo | El orden de evaluacion de las 6 reglas de derivacion no coincide con el doc 03, causando estados incorrectos |
| Probabilidad | Media |
| Impacto | Alto — estados incorrectos rompen todo el workflow y la autorizacion |
| Mitigacion | Test unitario con los 7+ casos de la tabla del doc 03. Verificar especialmente que CANCELADO y CERRADO siempre prevalecen. Funcion pura sin side effects, facil de testear |
| Estado | Abierto |

---

### R-004 — Condiciones de carrera en asignaciones

| Campo | Valor |
|-------|-------|
| ID | R-004 |
| Modulo | M3 |
| Riesgo | Dos usuarios intentan asignar gestor/medico simultaneamente, causando doble asignacion vigente |
| Probabilidad | Baja |
| Impacto | Medio — inconsistencia de datos, pero detectable |
| Mitigacion | Transaccion atomica con SELECT FOR UPDATE. UNIQUE constraint en `(solicitud_id, rol, es_vigente)` cuando `es_vigente = 1` (o logica equivalente). Retornar 409 Conflict si se detecta colision |
| Estado | Abierto |

---

### R-005 — Migraciones Alembic en produccion

| Campo | Valor |
|-------|-------|
| ID | R-005 |
| Modulo | M6 |
| Riesgo | Una migracion falla en RDS y deja la BD en estado inconsistente |
| Probabilidad | Baja |
| Impacto | Alto — backend no funciona, datos potencialmente corruptos |
| Mitigacion | Probar migraciones en BD de test antes de produccion. Backup automatico de RDS antes de migrar. Migraciones atomicas (cada una autocontenida). Tener scripts de rollback (alembic downgrade) |
| Estado | Abierto |

---

### R-006 — Archivos grandes saturan App Runner

| Campo | Valor |
|-------|-------|
| ID | R-006 |
| Modulo | M4, M6 |
| Riesgo | Subida de archivos grandes consume toda la memoria/CPU de la instancia App Runner |
| Probabilidad | Media |
| Impacto | Medio — servicio degradado o caido temporalmente |
| Mitigacion | Limitar tamano maximo de archivo (ej: 10MB). Streaming upload en lugar de cargar en memoria. En produccion: considerar presigned URL para upload directo a S3 |
| Estado | Abierto |

---

### R-007 — Modelo relacional complejo y migraciones incrementales

| Campo | Valor |
|-------|-------|
| ID | R-007 |
| Modulo | M2 |
| Riesgo | El modelo tiene 17+ tablas con FK cruzadas. Migraciones incrementales pueden generar errores de orden (FK a tabla que aun no existe) |
| Probabilidad | Media |
| Impacto | Medio — migraciones fallan, requieren correccion manual |
| Mitigacion | Crear tablas en orden de dependencia (personas primero, luego clientes, empleados, users, servicios, solicitudes). Una migracion grande para el modelo core en M2 en lugar de multiples migraciones pequenas |
| Estado | Abierto |

---

### R-008 — Seed de desarrollo desactualizado

| Campo | Valor |
|-------|-------|
| ID | R-008 |
| Modulo | M1-M5 |
| Riesgo | Los datos seed no se actualizan al agregar nuevas tablas/campos, causando errores al levantar el entorno |
| Probabilidad | Media |
| Impacto | Bajo — solo afecta desarrollo, no produccion |
| Mitigacion | Seed como script Python (no SQL) que valida constraints. Ejecutar seed como parte del setup automatico en docker-compose. Actualizar seed al agregar cada modulo |
| Estado | Abierto |

---

### R-009 — Performance de queries con joins multiples

| Campo | Valor |
|-------|-------|
| ID | R-009 |
| Modulo | M2, M3 |
| Riesgo | GET /solicitudes con filtros, paginacion y joins a personas, clientes, asignaciones, pagos puede ser lento con muchos registros |
| Probabilidad | Baja (MVP tiene pocos registros) |
| Impacto | Bajo en MVP — alto en escalamiento |
| Mitigacion | Indices en campos de filtro y FK. Queries optimizadas con joins selectivos. Paginacion obligatoria (page_size maximo). Monitorear queries lentas con CloudWatch |
| Estado | Abierto |

---

### R-010 — Reset password sin canal de email

| Campo | Valor |
|-------|-------|
| ID | R-010 |
| Modulo | M5 |
| Riesgo | En MVP no hay envio de email. El token de reset debe comunicarse manualmente del ADMIN al usuario, lo cual es inseguro y no escalable |
| Probabilidad | Alta (certeza en MVP) |
| Impacto | Bajo — solo afecta UX, no seguridad del token en si |
| Mitigacion | Aceptado para MVP. Token con expiracion corta (1 hora). Log de auditoria del reset. Fase post-MVP: integrar SES o similar para envio de email |
| Estado | Abierto (aceptado) |

---

### R-011 — Frontend calcula permisos por error

| Campo | Valor |
|-------|-------|
| ID | R-011 |
| Modulo | M2-M5 |
| Riesgo | Un desarrollador frontend agrega logica condicional basada en rol del usuario en lugar de usar acciones_permitidas del backend |
| Probabilidad | Media |
| Impacto | Alto — permisos inconsistentes entre frontend y backend |
| Mitigacion | Documentar regla clave en este repo y en comentarios del codigo. Code review enfocado en esta regla. Typescript types que refuercen el patron: los botones reciben `acciones_permitidas: string[]` y renderizan condicionalmente |
| Estado | Abierto |

---

### R-012 — Docker no disponible en maquina de desarrollo

| Campo | Valor |
|-------|-------|
| ID | R-012 |
| Modulo | M0 |
| Riesgo | El desarrollador no tiene Docker instalado o configurado |
| Probabilidad | Baja |
| Impacto | Medio — no puede levantar el entorno completo |
| Mitigacion | Documentar alternativas: MySQL instalado localmente, backend con `uvicorn` directo, frontend con `npm start`. docker-compose es ideal pero no obligatorio para desarrollo |
| Estado | Abierto |

---

### R-013 — MySQL ENUMs y compatibilidad SQLAlchemy

| Campo | Valor |
|-------|-------|
| ID | R-013 |
| Modulo | M1, M2 |
| Riesgo | Los ENUMs de MySQL tienen comportamiento particular (ej: case sensitivity, validacion estricta). SQLAlchemy puede manejarlos de forma diferente |
| Probabilidad | Media |
| Impacto | Medio — errores de insercion o validacion inesperados |
| Mitigacion | Usar `sqlalchemy.Enum` con los valores exactos del doc 01. Probar inserciones con todos los valores ENUM en tests de integracion. Considerar usar VARCHAR + CHECK constraint como alternativa si los ENUMs causan problemas |
| Estado | Abierto |

---

### R-014 — PromotorInput validator rompe solicitudes sin promotor

| Campo | Valor |
|-------|-------|
| ID | R-014 |
| Modulo | M5.5 |
| Riesgo | La validacion cruzada de campos en PromotorInput (model_validator) se ejecuta incluso cuando no se envia promotor, bloqueando creacion de solicitudes |
| Probabilidad | Baja |
| Impacto | Alto — no se pueden crear solicitudes |
| Mitigacion | El campo `promotor` en CreateSolicitudRequest es `Optional[PromotorInput]`. El validator solo se ejecuta si se instancia PromotorInput. Tests de regresion: crear solicitud sin promotor debe seguir funcionando |
| Estado | Abierto |

---

### R-015 — Relationship promotor en SolicitudCmep genera queries N+1

| Campo | Valor |
|-------|-------|
| ID | R-015 |
| Modulo | M5.5 |
| Riesgo | Agregar relationship `promotor` con lazy="selectin" puede degradar performance de list_solicitudes si hay muchos promotores tipo PERSONA (carga adicional de Persona) |
| Probabilidad | Baja (pocos promotores en MVP) |
| Impacto | Bajo en MVP, medio en escalamiento |
| Mitigacion | lazy="selectin" agrupa queries. Para PERSONA, el promotor ya tiene persona_id FK — la carga es eficiente. Monitorear en produccion |
| Estado | Abierto |

---

### R-016 — Exponer POLICY via endpoint revela configuracion interna

| Campo | Valor |
|-------|-------|
| ID | R-016 |
| Modulo | M5.5 |
| Riesgo | El endpoint GET /admin/permisos expone la matriz completa de permisos del sistema |
| Probabilidad | Baja |
| Impacto | Bajo — es informacion de configuracion, no secreta. Solo accesible por ADMIN |
| Mitigacion | Proteger con require_admin. La POLICY ya es efectivamente publica (el frontend recibe acciones_permitidas por solicitud). El endpoint solo centraliza la visualizacion |
| Estado | Abierto (aceptado) |

---

### R-017 — Filtro mine requiere joins adicionales en list_solicitudes

| Campo | Valor |
|-------|-------|
| ID | R-017 |
| Modulo | M5.6 |
| Riesgo | Para GESTOR y MEDICO, el filtro `mine=true` requiere JOIN con SolicitudAsignacion y comparar con persona_id del usuario. Puede degradar performance en listas grandes |
| Probabilidad | Baja |
| Impacto | Bajo — dashboard solo pide 10 registros (page_size=10). Indices existentes en asignaciones |
| Mitigacion | Limitar page_size en dashboard. Indices en solicitud_asignacion(empleado_persona_id, es_vigente). Monitorear en produccion |
| Estado | Abierto |

---

### R-018 — Textos de bienvenida estaticos pueden desactualizarse

| Campo | Valor |
|-------|-------|
| ID | R-018 |
| Modulo | M5.6 |
| Riesgo | Los textos descriptivos por rol estan hardcodeados en el frontend. Si cambian las funciones de un rol (ej: se agregan acciones), los textos no se actualizan automaticamente |
| Probabilidad | Baja (roles estables en MVP) |
| Impacto | Bajo — es texto informativo, no afecta funcionalidad |
| Mitigacion | Textos son genericos ("gestionar solicitudes", "dar seguimiento") y no mencionan acciones especificas de POLICY. Actualizar manualmente si cambian roles |
| Estado | Abierto (aceptado) |

---

## Resumen de riesgos por criticidad

| Criticidad | Riesgos |
|------------|---------|
| Alta (prob alta + impacto alto) | R-001 (CORS) |
| Alta (prob media + impacto alto) | R-002 (POLICY), R-003 (estado operativo), R-011 (frontend permisos) |
| Media | R-004 (race conditions), R-005 (migraciones prod), R-006 (archivos grandes), R-007 (modelo complejo), R-008 (seed), R-013 (ENUMs) |
| Baja | R-009 (performance), R-010 (reset password), R-012 (Docker), R-014 (PromotorInput), R-015 (N+1 promotor), R-016 (POLICY expuesta), R-017 (mine joins), R-018 (textos estaticos) |
