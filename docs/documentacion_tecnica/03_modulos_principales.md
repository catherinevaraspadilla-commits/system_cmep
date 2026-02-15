# Módulos Principales — CMEP

## Backend

### Estructura de Carpetas

```
backend/app/
├── main.py              → Punto de entrada FastAPI
├── config.py            → Configuración centralizada (Pydantic Settings)
├── database.py          → Motor async SQLAlchemy, fábrica de sesiones
├── api/                 → Endpoints REST
├── models/              → Modelos ORM (SQLAlchemy)
├── schemas/             → DTOs de entrada/salida (Pydantic)
├── services/            → Lógica de negocio
├── middleware/          → Procesamiento de peticiones
└── utils/               → Utilidades compartidas
```

---

### `main.py` — Punto de Entrada

**Responsabilidad:** Inicializa la app FastAPI, registra todos los routers y configura middleware.

```python
# Routers registrados:
app.include_router(auth_router,        prefix="/auth")
app.include_router(solicitudes_router, prefix="/solicitudes")
app.include_router(archivos_router,    prefix="/archivos")
app.include_router(promotores_router,  prefix="/promotores")
app.include_router(empleados_router,   prefix="/empleados")
app.include_router(servicios_router,   prefix="/servicios")
app.include_router(admin_router,       prefix="/admin")
app.include_router(reportes_router,    prefix="/reportes")
```

**Endpoints de sistema:**
- `GET /health` → estado del servidor
- `GET /version` → versión de la app

---

### `config.py` — Configuración

**Responsabilidad:** Carga variables de entorno y expone propiedades calculadas.

```python
class Settings(BaseSettings):
    APP_ENV: str = "local"         # local | prod
    DB_URL: str = ""               # mysql+asyncmy://... (opcional)
    DB_HOST, DB_PORT, DB_NAME...   # alternativa a DB_URL
    SESSION_SECRET: str            # clave para firmar sesiones
    FILE_STORAGE: str = "local"    # local | s3
    CORS_ORIGINS: str              # URLs permitidas

    @property
    def is_prod(self): ...
    @property
    def is_sqlite(self): ...
    @property
    def effective_db_url(self): ...  # prioriza DB_URL, luego construye desde partes
```

Si no hay `DB_URL` ni variables MySQL, usa **SQLite** en `{raíz}/cmep_dev.db`.

---

### `database.py` — Base de Datos

**Responsabilidad:** Crea el motor async y la fábrica de sesiones.

```python
engine = create_async_engine(settings.effective_db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session  # inyectado por FastAPI Depends
```

---

### Módulo `api/` — Endpoints REST

| Archivo | Prefijo | Endpoints principales |
|---------|---------|----------------------|
| `auth.py` | `/auth` | POST /login, GET /me, POST /logout |
| `solicitudes.py` | `/solicitudes` | GET /, POST /, GET /{id}, PATCH /{id}, POST /{id}/asignar-gestor, POST /{id}/registrar-pago, POST /{id}/asignar-medico, POST /{id}/cerrar, POST /{id}/cancelar |
| `archivos.py` | `/archivos` | POST /upload, GET /{solicitud_id}/descargar/{archivo_id} |
| `promotores.py` | `/promotores` | GET /, POST /, GET /{id}, PATCH /{id} |
| `empleados.py` | `/empleados` | GET /, GET /{id} |
| `servicios.py` | `/servicios` | GET /, GET /{id} |
| `admin.py` | `/admin` | GET /usuarios, POST /usuarios, PATCH /usuarios/{id} |
| `reportes.py` | `/reportes` | GET /resumen, GET /por-estado, GET /por-medico, etc. |

Cada endpoint extrae `current_user` del estado del request (inyectado por el middleware de sesión).

---

### Módulo `models/` — Modelos ORM

| Archivo | Modelos |
|---------|---------|
| `persona.py` | `Persona` (base: nombres, apellidos, doc, contacto) |
| `user.py` | `User`, `UserRole`, `UserPermission`, `Session`, `PasswordReset` |
| `cliente.py` | `Cliente`, `ClienteApoderado` |
| `empleado.py` | `Empleado`, `MedicoExtra` |
| `promotor.py` | `Promotor` |
| `servicio.py` | `Servicio` |
| `solicitud.py` | `SolicitudCmep`, `SolicitudAsignacion`, `PagoSolicitud`, `Archivo`, `SolicitudArchivo`, `SolicitudEstadoHistorial`, `ResultadoMedico` |

**Modelo central: `SolicitudCmep`**

```python
class SolicitudCmep(Base):
    solicitud_id: UUID (PK)
    cliente_id: FK → clientes
    apoderado_id: FK → clientes (opcional)
    servicio_id: FK → servicios
    promotor_id: FK → promotores (opcional)
    estado_atencion: str  # REGISTRADO | EN_PROCESO | ATENDIDO | OBSERVADO | CANCELADO
    estado_pago: str      # PENDIENTE | PAGADO | OBSERVADO
    tarifa_monto: Decimal
    tarifa_moneda: str    # PEN | USD
    # audit fields: created_by, updated_by, created_at, updated_at
```

---

### Módulo `schemas/` — DTOs Pydantic

| Archivo | Schemas |
|---------|---------|
| `auth.py` | `LoginRequest`, `LoginResponse`, `UserMeResponse` |
| `solicitud.py` | `SolicitudCreateRequest`, `SolicitudUpdateRequest`, `SolicitudDetailResponse`, `AsignarGestorRequest`, `RegistrarPagoRequest`, `AsignarMedicoRequest`, `CerrarRequest` |
| `admin.py` | `UserCreateRequest`, `UserUpdateRequest`, `UserListResponse` |
| `promotor.py` | `PromotorCreateRequest`, `PromotorUpdateRequest`, `PromotorResponse` |

Los schemas de respuesta incluyen campos calculados como `estado_operativo` y `acciones_permitidas`.

---

### Módulo `services/` — Lógica de Negocio

#### `policy.py`
Define la **matriz de autorización**:

```python
POLICY = {
    UserRoleEnum.ADMIN: {
        EstadoOperativo.REGISTRADO: [Accion.EDITAR, Accion.ASIGNAR_GESTOR, Accion.CANCELAR],
        EstadoOperativo.ASIGNADO_GESTOR: [Accion.EDITAR, Accion.REGISTRAR_PAGO, Accion.CANCELAR],
        # ...
    },
    UserRoleEnum.OPERADOR: { ... },
    UserRoleEnum.GESTOR: { ... },
    UserRoleEnum.MEDICO: { ... },
}

def get_acciones_permitidas(rol, estado_operativo) -> list[Accion]: ...
def verificar_accion(rol, estado_operativo, accion) -> None:  # lanza HTTPException si no permitido
```

#### `estado_operativo.py`
Deriva el estado operativo a partir de los datos de la solicitud:

```python
def calcular_estado_operativo(solicitud, asignaciones, pagos) -> EstadoOperativo:
    if solicitud.estado_atencion == "CANCELADO":
        return EstadoOperativo.CANCELADO
    if solicitud.estado_atencion == "ATENDIDO":
        return EstadoOperativo.CERRADO
    if solicitud.estado_pago == "PAGADO" and tiene_medico_activo(asignaciones):
        return EstadoOperativo.ASIGNADO_MEDICO
    if solicitud.estado_pago == "PAGADO":
        return EstadoOperativo.PAGADO
    if tiene_gestor_activo(asignaciones):
        return EstadoOperativo.ASIGNADO_GESTOR
    return EstadoOperativo.REGISTRADO
```

#### `solicitud_service.py`
Orquesta todas las operaciones sobre solicitudes:
- CRUD completo (crear, leer, editar)
- Transiciones de workflow (asignar, pagar, cerrar, cancelar)
- Registro en historial de estados
- Gestión de asignaciones (activar/desactivar con `es_vigente`)

#### `file_storage.py`
Abstrae el almacenamiento de archivos:

```python
class FileStorageService:
    def upload(file, filename) -> str:   # ruta o S3 key
    def download(key) -> FileResponse | RedirectResponse
    def delete(key) -> None
```

- **local:** guarda en `uploads/` con nombre UUID
- **s3:** usa boto3 para subir/bajar con `presigned URLs`

#### `auth_service.py`
- Verifica credenciales con `bcrypt.verify`
- Crea/destruye sesiones en tabla `sessions`
- Carga datos completos del usuario

#### `reportes_service.py`
Ejecuta queries de agregación para reportes de gestión:
- Solicitudes por estado
- Solicitudes por médico
- Volumen por período
- Ingresos por servicio

#### `admin_service.py`
Gestión de usuarios: crear, listar, activar/suspender.

---

### Módulo `middleware/`

#### `session_middleware.py`
Se ejecuta en **cada petición**:

```
1. Lee cookie "session_id"
2. Busca en tabla `sessions` (no expirada)
3. Carga User + roles + permisos
4. Inyecta en request.state.current_user
5. Si no hay sesión válida → request.state.current_user = None
   (el endpoint decide si requiere auth con Depends)
```

---

### Módulo `utils/`

| Archivo | Función |
|---------|---------|
| `hashing.py` | `hash_password(plain)`, `verify_password(plain, hash)` usando bcrypt |
| `time.py` | `utcnow()` → datetime UTC para timestamps consistentes |

---

## Frontend

### Estructura de Carpetas

```
frontend/src/
├── main.tsx          → Punto de entrada React DOM
├── App.tsx           → Routing principal (React Router)
├── pages/            → Componentes de página (uno por ruta)
│   ├── Login.tsx
│   ├── Status.tsx
│   └── app/          → Páginas protegidas
├── components/       → Componentes reutilizables
├── hooks/            → Hooks personalizados
├── services/         → Cliente API HTTP
└── types/            → Interfaces TypeScript
```

---

### `App.tsx` — Routing

Define las rutas públicas y protegidas usando React Router v6:

```tsx
<Routes>
  <Route path="/" element={<Navigate to="/app" />} />
  <Route path="/login" element={<Login />} />
  <Route path="/status" element={<Status />} />
  <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
    <Route index element={<Inicio />} />
    <Route path="solicitudes" element={<SolicitudesLista />} />
    <Route path="solicitudes/nueva" element={<SolicitudNueva />} />
    <Route path="solicitudes/:id" element={<SolicitudDetalle />} />
    <Route path="promotores" element={<PromotoresLista />} />
    <Route path="usuarios" element={<UsuariosLista />} />
    <Route path="reportes-admin" element={<ReportesAdmin />} />
  </Route>
</Routes>
```

---

### `hooks/useAuth.ts` — Contexto de Autenticación

Provee `AuthContext` con:
- `user` → datos del usuario actual
- `login(email, password)` → llama POST /auth/login
- `logout()` → llama POST /auth/logout
- `isLoading` → estado de carga inicial
- `hasRole(rol)` → verifica rol del usuario

---

### `services/api.ts` — Cliente HTTP

Centraliza todas las llamadas a la API:

```typescript
const api = {
  get: (url) => fetch(BASE_URL + url, { credentials: 'include' }),
  post: (url, body) => fetch(...),
  patch: (url, body) => fetch(...),
  delete: (url) => fetch(...),
  upload: (url, formData) => fetch(...),
}
```

Usa `credentials: 'include'` para enviar cookies de sesión automáticamente.

---

### Páginas Principales

| Página | Archivo | Descripción |
|--------|---------|-------------|
| Dashboard | `Inicio.tsx` | Resumen de solicitudes recientes |
| Lista de solicitudes | `SolicitudesLista.tsx` | Tabla paginada con filtros por estado |
| Nueva solicitud | `SolicitudNueva.tsx` | Formulario multistep |
| Detalle de solicitud | `SolicitudDetalle.tsx` | Vista completa + acciones de workflow |
| Promotores | `PromotoresLista.tsx` | CRUD de promotores |
| Usuarios | `UsuariosLista.tsx` | Gestión de usuarios (solo ADMIN) |
| Reportes | `ReportesAdmin.tsx` | Gráficos y tablas de análisis |

---

### Componentes Reutilizables

#### `AppLayout.tsx`
Shell principal de la aplicación: navbar lateral, header, área de contenido. Controla navegación según rol.

#### `WorkflowStepper.tsx`
Visualiza el progreso de una solicitud en los estados del workflow. Recibe `estado_operativo` y resalta el paso actual.

#### `Modal.tsx`
Componente genérico de diálogo para confirmaciones y formularios inline.

---

### Bloques de Detalle de Solicitud

Ubicados en `pages/app/solicitud/`:

| Componente | Descripción |
|-----------|-------------|
| `BlockGestion.tsx` | Asignación de gestor y datos generales |
| `BlockPago.tsx` | Registro y visualización de pagos |
| `BlockEvaluacion.tsx` | Asignación de médico y resultado médico |
| `detailHelpers.ts` | Funciones auxiliares para el detalle |
