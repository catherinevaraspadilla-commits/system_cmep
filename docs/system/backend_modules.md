# Módulos Técnicos del Backend CMEP

## 1. Estructura de Carpetas

```
backend/app/
  api/         # Endpoints REST
  middleware/  # Middlewares personalizados
  models/      # Modelos ORM (SQLAlchemy)
  schemas/     # Esquemas Pydantic (DTOs)
  services/    # Lógica de negocio
  utils/       # Utilidades y helpers
```

## 2. Descripción de Módulos
- **api/**: Define rutas y controladores REST.
- **middleware/**: Middlewares para sesiones, autenticación, etc.
- **models/**: Modelos de base de datos (ORM).
- **schemas/**: Validación y serialización de datos (Pydantic).
- **services/**: Lógica de negocio y acceso a datos.
- **utils/**: Funciones auxiliares.

## 3. Flujo de una petición típica
1. Llega petición HTTP a un endpoint en `api/`.
2. Se valida y deserializa con un esquema de `schemas/`.
3. Se ejecuta lógica en `services/` y se accede a modelos en `models/`.
4. Se retorna respuesta serializada.

## 4. Referencias
- [architecture.md](architecture.md)
- [tablas_del_sistema.md](tablas_del_sistema.md)
