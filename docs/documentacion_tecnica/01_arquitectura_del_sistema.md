# Arquitectura del Sistema — CMEP

## Descripción General

CMEP (Medical Certificate Management Platform) es una aplicación web full-stack diseñada para gestionar el ciclo de vida completo de certificados médicos profesionales. El sistema es cloud-native, orientado a producción en AWS, y soporta múltiples roles de usuario en un flujo de trabajo colaborativo.

---

## Diagrama de Capas

```
┌────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Navegador)                     │
│              React 18 SPA — TypeScript — Vite                  │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTP/HTTPS (JSON REST API)
                             │ Cookies httpOnly (sesión)
┌────────────────────────────▼───────────────────────────────────┐
│                       BACKEND (API)                            │
│           FastAPI — Python 3.12+ — Uvicorn (ASGI)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │   Auth   │ │Solicitudes│ │ Archivos │ │ Admin / Reportes │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │     Servicios de Negocio (policy, workflow, storage)      │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │     SQLAlchemy 2.0 (async ORM) — Pydantic (validación)    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────┬──────────────────────┬───────────────────┘
                      │                      │
        ┌─────────────▼──────────┐  ┌────────▼────────────┐
        │     Base de Datos      │  │  Almacén de Archivos │
        │  SQLite (dev)          │  │  Local /uploads (dev)│
        │  MySQL 8 — RDS (prod)  │  │  AWS S3 (prod)       │
        └────────────────────────┘  └─────────────────────┘
```

---

## Arquitectura en Producción (AWS)

```
Internet
    │
    ▼
┌──────────────┐     ┌──────────────────┐
│  CloudFront  │────▶│  S3 (frontend)   │  ← React SPA (estático)
│  CDN + HTTPS │     │  static hosting  │
└──────────────┘     └──────────────────┘

┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Navegador  │────▶│   App Runner     │────▶│  RDS MySQL 8 │
│   (React)    │ API │   (FastAPI)      │ SQL │  (prod DB)   │
└──────────────┘     └────────┬─────────┘     └──────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   S3 (archivos)   │  ← Documentos médicos
                    │   (bucket privado)│
                    └───────────────────┘

Servicios de soporte:
├── AWS Secrets Manager   → credenciales y variables de entorno
├── CloudWatch Logs       → monitoreo y trazas de la app
└── Lambda + EventBridge  → tareas programadas (limpieza de sesiones)
```

---

## Principios de Diseño

| Principio | Implementación |
|-----------|---------------|
| **Separación de responsabilidades** | API, servicios de negocio, modelos y esquemas son capas independientes |
| **Operaciones asíncronas** | SQLAlchemy async + FastAPI async para alta concurrencia |
| **Autorización basada en matriz** | `policy.py` define qué rol puede hacer qué acción en cada estado |
| **Estado derivado (no almacenado)** | `estado_operativo` se calcula en tiempo real desde los datos |
| **Trazabilidad total** | Todas las entidades tienen `created_by`, `updated_by`, `created_at`, `updated_at` |
| **Almacenamiento abstracto** | `file_storage.py` es agnóstico de backend (local o S3) |
| **Configuración por entorno** | Pydantic Settings carga `.env` y permite override por variable de entorno |

---

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React | 18.3.1 |
| Frontend | TypeScript | 5.6.3 |
| Frontend | Vite (bundler) | 6.0.5 |
| Frontend | React Router | 6.28.0 |
| Frontend | Material-UI | 7.3.7 |
| Frontend | Recharts | 3.7.0 |
| Backend | Python | 3.12+ (3.13 recomendado) |
| Backend | FastAPI | 0.115.6 |
| Backend | Uvicorn (ASGI) | 0.34.0 |
| Backend | SQLAlchemy (async) | 2.0.46 |
| Backend | Pydantic Settings | 2.7.1 |
| Backend | Alembic (migraciones) | 1.14.1 |
| Backend | bcrypt | 4.2.1 |
| Base de Datos | SQLite | desarrollo local |
| Base de Datos | MySQL 8 | producción (RDS) |
| Almacenamiento | Sistema de archivos local | desarrollo |
| Almacenamiento | AWS S3 | producción |
| Contenedores | Docker + docker-compose | local y prod |
| Tests | pytest + pytest-asyncio | 8.3.4 / 0.25.2 |

---

## Roles del Sistema

| Rol | Descripción |
|-----|-------------|
| `ADMIN` | Gestión de usuarios, reportes globales, acceso total |
| `OPERADOR` | Creación y edición de solicitudes, registro de pagos |
| `GESTOR` | Gestión de solicitudes asignadas, coordinación de pagos |
| `MEDICO` | Evaluación médica y cierre de solicitudes asignadas |

---

## Seguridad

- **Autenticación:** sesiones del servidor, cookie `httpOnly` con `SESSION_SECRET`
- **Contraseñas:** bcrypt con salt automático
- **Autorización:** matriz de políticas `POLICY[rol][estado] → acciones_permitidas`
- **CORS:** origen(s) configurados explícitamente, no wildcard en producción
- **Archivos:** acceso mediante URLs firmadas de S3 (producción) o validación de permisos local

---

## Estructura de Carpetas (raíz)

```
system_cmep/
├── backend/          → API FastAPI, modelos, servicios, tests
├── frontend/         → React SPA con TypeScript
├── infra/            → docker-compose, scripts de seed, Lambda
├── docs/             → documentación técnica y funcional
├── scripts/          → herramientas de diagnóstico y utilidades
├── .env.example      → plantilla de variables de entorno
└── README.md         → guía de inicio rápido
```
