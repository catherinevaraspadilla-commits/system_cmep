# Arquitectura Técnica del Sistema CMEP

## 1. Descripción General
El sistema CMEP es una aplicación web compuesta por un frontend en React (Vite) y un backend en Python (FastAPI), con una base de datos MySQL/SQLite y despliegue mediante Docker.

## 2. Componentes Principales
- **Frontend:** React + TypeScript, Vite, estructura modular por páginas y componentes.
- **Backend:** FastAPI, SQLAlchemy (ORM), estructura modular por dominios (api, models, schemas, services, utils).
- **Base de Datos:** MySQL (producción), SQLite (desarrollo/tests).
- **Infraestructura:** Docker, docker-compose, migraciones con Alembic.

## 3. Diagrama de Arquitectura

```
[Usuario]
   |
[Frontend (React)] <-> [Backend (FastAPI)] <-> [Base de Datos]
```

## 4. Flujo de Datos
1. El usuario interactúa con la SPA React.
2. El frontend consume APIs REST del backend.
3. El backend procesa, valida y accede a la base de datos.
4. Las respuestas se devuelven al frontend para renderizado.

## 5. Seguridad
- Autenticación basada en sesiones (cookie-based).
- Roles y permisos gestionados en backend.
- Validación de datos en backend y frontend.

## 6. Despliegue
- Contenedores Docker para frontend, backend y base de datos.
- Orquestación con docker-compose.

---

## Referencias
- [tablas_del_sistema.md](tablas_del_sistema.md)
- [solicitud_detalle.md](solicitud_detalle.md)
