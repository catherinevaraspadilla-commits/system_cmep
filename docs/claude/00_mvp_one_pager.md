# CMEP — MVP One Pager

## Producto

**CMEP** (Certificado Medico de Evaluacion Profesional) es un sistema web interno para gestionar el ciclo de vida completo de solicitudes de certificados medicos: desde el registro del cliente hasta el cierre de la evaluacion medica, incluyendo pagos, asignaciones de personal y archivos asociados.

## Usuarios objetivo

| Rol | Funcion principal |
|-----|-------------------|
| ADMIN | Gestion global, usuarios, override en estados finales |
| OPERADOR | Registro de solicitudes, asignacion inicial de gestor |
| GESTOR | Gestion de pagos, asignacion de medico |
| MEDICO | Evaluacion medica, cierre de solicitud |

## Alcance MVP

### Incluido

1. **Autenticacion y sesiones** — login por email/password, sesiones server-side con cookie, middleware de autorizacion
2. **CRUD de solicitudes** — crear, listar (con filtros y paginacion), ver detalle, editar datos
3. **Workflow completo con POLICY** — estado operativo derivado (no almacenado), 9 acciones de negocio (EDITAR_DATOS, ASIGNAR_GESTOR, CAMBIAR_GESTOR, REGISTRAR_PAGO, ASIGNAR_MEDICO, CAMBIAR_MEDICO, CERRAR, CANCELAR, OVERRIDE), auditoria obligatoria en `solicitud_estado_historial`
4. **Gestion de archivos** — subida, asociacion a solicitud/pago, descarga via URL firmada (S3 en prod, filesystem en dev)
5. **Administracion de usuarios** — CRUD usuarios, asignacion de roles, reset de password (solo ADMIN)
6. **Frontend responsive** — React mobile-first, una sola app web, sin PWA en V1
7. **Despliegue cloud AWS** — App Runner + RDS MySQL + S3 + CloudFront

### Excluido del MVP

- PWA / modo offline
- Notificaciones push o email
- Modulo de reportes avanzados
- Integraciones externas (RENIEC, pasarelas de pago automaticas)
- Multi-idioma
- Dashboard analitico

## Flujo principal (happy path)

```
REGISTRADO --> ASIGNADO_GESTOR --> PAGADO --> ASIGNADO_MEDICO --> CERRADO
```

1. Operador registra solicitud (estado: REGISTRADO)
2. Operador/Admin asigna gestor (estado: ASIGNADO_GESTOR)
3. Gestor registra pago (estado: PAGADO)
4. Gestor/Admin asigna medico (estado: ASIGNADO_MEDICO)
5. Medico completa evaluacion y cierra (estado: CERRADO)

Flujo alternativo: CANCELAR puede ejecutarse desde cualquier estado no terminal.
OVERRIDE solo disponible para ADMIN en estados CERRADO/CANCELADO.

## Restricciones clave

| Restriccion | Detalle |
|-------------|---------|
| Estado operativo | Se calcula en backend, NO se almacena en BD |
| Permisos frontend | El frontend NO calcula permisos; usa `acciones_permitidas` del backend |
| POLICY unica | Toda autorizacion pasa por la matriz `(rol, estado_operativo) => acciones` |
| Auditoria | Toda accion que modifique estado/asignacion registra historial campo por campo |
| Transacciones | Asignaciones y reasignaciones son atomicas |
| Email unico | `users.user_email` se normaliza a `lower(trim(email))` |

## Stack tecnologico

| Capa | Tecnologia |
|------|------------|
| Backend | Python + FastAPI |
| Frontend | React (responsive, mobile-first) |
| BD | MySQL 8 (RDS en prod) |
| Migraciones | Alembic |
| Auth | Sesiones server-side + cookie segura |
| Storage | S3 (prod) / filesystem (dev) |
| Infra | AWS: App Runner, RDS, S3, CloudFront, Secrets Manager |
| Contenedores | Docker + docker-compose (dev) |

## Modulos de desarrollo (orden obligatorio)

| Modulo | Nombre | Dependencia |
|--------|--------|-------------|
| M0 | Bootstrap proyecto | - |
| M1 | Auth y sesiones | M0 |
| M2 | CRUD solicitudes | M1 |
| M3 | Workflow + POLICY + acciones | M2 |
| M4 | Archivos | M3 |
| M5 | Administracion | M1 |
| M6 | Despliegue cloud | M1-M5 |

**Regla:** no se avanza a un modulo nuevo si el anterior no pasa tests.

## Criterio de exito MVP

- Un usuario ADMIN puede crear solicitudes, asignar personal, registrar pagos y cerrar el flujo completo
- La POLICY bloquea acciones no permitidas segun rol/estado
- Toda accion queda registrada en historial de auditoria
- El sistema funciona desde navegador movil y escritorio
- Despliegue funcional en AWS con datos persistentes
