# Documentación Técnica — CMEP

Sistema de gestión de certificados médicos profesionales.
Documentación técnica completa del proyecto `system_cmep`.

---

## Índice de Documentos

| Documento | Contenido |
|-----------|-----------|
| [01_arquitectura_del_sistema.md](01_arquitectura_del_sistema.md) | Diagrama de capas, stack tecnológico, principios de diseño, roles del sistema |
| [02_flujo_de_funcionamiento.md](02_flujo_de_funcionamiento.md) | Ciclo de vida de solicitudes, estados operativos, matriz de autorización, flujos detallados |
| [03_modulos_principales.md](03_modulos_principales.md) | Descripción de cada módulo backend y frontend, responsabilidades y API interna |
| [04_dependencias_y_configuracion.md](04_dependencias_y_configuracion.md) | Requisitos del sistema, dependencias, variables de entorno por entorno |
| [05_despliegue_y_ejecucion.md](05_despliegue_y_ejecucion.md) | Guía paso a paso para local (sin Docker), Docker, y producción AWS |

---

## Inicio Rápido (Local sin Docker)

```bash
# 1. Instalar dependencias
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. Configurar variables de entorno
echo "APP_ENV=local
SESSION_SECRET=dev-secret-local
CORS_ORIGINS=http://localhost:3000
FILE_STORAGE=local" > backend/.env

echo "VITE_API_URL=http://localhost:8000" > frontend/.env

# 3. Crear BD SQLite y datos de prueba
cd infra && python seed_dev.py

# 4. Iniciar backend (terminal 1)
cd backend && uvicorn app.main:app --reload --port 8000

# 5. Iniciar frontend (terminal 2)
cd frontend && npm run dev
```

Acceder en: **http://localhost:3000**

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin@cmep.local` | `admin123` | ADMIN |
| `operador@cmep.local` | `operador123` | OPERADOR |
| `gestor@cmep.local` | `gestor123` | GESTOR |
| `medico@cmep.local` | `medico123` | MEDICO |

---

## Resumen del Sistema

**CMEP** es una plataforma web para gestionar el ciclo completo de certificados médicos profesionales.

### ¿Qué hace el sistema?

1. Un **OPERADOR** registra una solicitud de certificado médico para un cliente
2. Asigna un **GESTOR** que coordina el proceso
3. El gestor registra el pago y asigna un **MÉDICO**
4. El médico evalúa al paciente y cierra la solicitud
5. Todo el proceso queda trazado y auditado

### Estado operativo de una solicitud

```
REGISTRADO → ASIGNADO_GESTOR → PAGADO → ASIGNADO_MEDICO → CERRADO
                                                         ↘ CANCELADO (en cualquier paso)
```

### Tecnologías principales

- **Backend:** FastAPI (Python) + SQLAlchemy async
- **Frontend:** React 18 + TypeScript + Vite
- **BD desarrollo:** SQLite (automático, sin configuración)
- **BD producción:** MySQL 8 en AWS RDS
- **Archivos producción:** AWS S3

---

## Estructura del Proyecto

```
system_cmep/
├── backend/               → API REST (FastAPI)
│   ├── app/
│   │   ├── api/           → Endpoints por dominio
│   │   ├── models/        → Modelos ORM (SQLAlchemy)
│   │   ├── schemas/       → DTOs de validación (Pydantic)
│   │   ├── services/      → Lógica de negocio
│   │   ├── middleware/    → Sesiones y autenticación
│   │   └── main.py        → Punto de entrada
│   ├── tests/             → 117 tests unitarios e integración
│   └── requirements.txt
│
├── frontend/              → SPA React
│   └── src/
│       ├── pages/         → Páginas de la aplicación
│       ├── components/    → Componentes reutilizables
│       ├── services/      → Cliente HTTP
│       └── types/         → Interfaces TypeScript
│
├── infra/                 → Docker, seeds, Lambda
├── docs/
│   └── documentacion_tecnica/  ← estás aquí
└── scripts/               → Herramientas de diagnóstico
```

---

## Estado de Dependencias

| Herramienta | Requerida | Estado |
|-------------|-----------|--------|
| Python 3.12+ | ✅ Sí | Verificar con `python --version` |
| pip | ✅ Sí | Verificar con `pip --version` |
| Node.js 18+ | ✅ Sí | Verificar con `node --version` |
| npm | ✅ Sí | Incluido con Node.js |
| Docker | ⚙️ Opcional | Solo para opción con MySQL local |
| AWS CLI | ⚙️ Opcional | Solo para despliegue en producción |
