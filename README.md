# CMEP — Sistema de Gestion de Certificados Medicos

Sistema web para gestionar solicitudes de certificados medicos de evaluacion profesional. Roles: ADMIN, OPERADOR, GESTOR, MEDICO.

## Requisitos

- **Python 3.12+** (probado con 3.13)
- **Node.js 18+** (probado con 20)
- **npm** (incluido con Node.js)

## Setup rapido (despues de clonar)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. Crear base de datos y datos de prueba

```bash
cd infra
python seed_dev.py
```

Esto crea `cmep_dev.db` (SQLite) en la raiz del proyecto con:
- 5 usuarios: admin, operador, gestor, medico, suspendido
- 2 promotores, 3 clientes, 3 servicios

### 4. Ejecutar

Abrir dos terminales:

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Acceder

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

### Usuarios de prueba

| Email | Password | Rol |
|-------|----------|-----|
| admin@cmep.local | admin123 | ADMIN |
| operador@cmep.local | operador123 | OPERADOR |
| gestor@cmep.local | gestor123 | GESTOR |
| medico@cmep.local | medico123 | MEDICO |

## Tests

```bash
cd backend
pytest
```

117 tests (unit + integracion). Los tests usan una BD en memoria independiente.

## Estructura del proyecto

```
backend/           Python/FastAPI backend
  app/
    api/           Endpoints (auth, solicitudes, admin, reportes, archivos)
    models/        SQLAlchemy ORM (persona, user, cliente, solicitud, etc.)
    schemas/       Pydantic request/response
    services/      Logica de negocio (policy, workflow, reportes)
    middleware/    Session middleware
    utils/         Hashing, time
  tests/           Unit + integration tests
frontend/          React 18 / TypeScript / Vite
  src/
    pages/app/     Paginas: Inicio, Solicitudes, Usuarios, Reportes
    components/    Layout, Stepper
    services/      API client
    types/         TypeScript interfaces
docs/
  source/          Documentacion original del sistema (8 docs)
  claude/          Especificaciones tecnicas y planes (claude.md para indice)
infra/             Docker compose, seed script
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0 (async), Pydantic
- **Frontend**: React 18, React Router, TypeScript, Vite, Recharts
- **BD**: SQLite (dev) / MySQL (prod)
- **Auth**: Sesiones server-side con cookie httpOnly

## Documentacion

Ver [docs/claude/claude.md](docs/claude/claude.md) para el estado completo del proyecto, modulos implementados, endpoints, y tareas pendientes.
