# Módulos Técnicos del Frontend CMEP

## 1. Estructura de Carpetas

```
frontend/src/
  components/  # Componentes reutilizables
  hooks/       # Custom React hooks
  pages/       # Páginas principales
  services/    # Llamadas a APIs
  types/       # Tipos y DTOs
```

## 2. Descripción de Módulos
- **components/**: Elementos UI reutilizables.
- **hooks/**: Lógica reutilizable con hooks.
- **pages/**: Vistas principales de la app.
- **services/**: Funciones para consumir APIs.
- **types/**: Definiciones TypeScript para datos y APIs.

## 3. Flujo de una interacción típica
1. El usuario navega a una página en `pages/`.
2. Se renderizan componentes y se usan hooks.
3. Se llaman servicios para obtener datos.
4. Se renderiza la UI con los datos recibidos.

## 4. Referencias
- [architecture.md](architecture.md)
