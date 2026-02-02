# CMEP — Estrategia de Testing

## 1. Principios

1. **Cada modulo trae sus tests** — no se avanza al siguiente sin que pasen.
2. **Tests automatizados son la puerta de calidad** — si falla un test, se corrige antes de continuar.
3. **Smoke flow manual complementa** — para validar UX y flujos visuales.
4. **La BD de test es efimera** — se crea, migra, seedea y destruye por sesion de test.

## 2. Tipos de test

### 2.1 Tests unitarios

**Herramienta:** pytest
**Ubicacion:** `backend/tests/unit/`
**Alcance:** logica pura sin BD ni I/O

| Modulo | Que se testea |
|--------|---------------|
| M1 | Hash/verify password, normalizacion email |
| M2 | Validacion schemas Pydantic |
| M3 | derivar_estado_operativo() — todos los casos |
| M3 | POLICY dict — matriz completa 4 roles x 6 estados |
| M3 | assert_allowed() — permite y rechaza correctamente |
| M4 | Validacion tipo/tamano de archivo |
| M5 | Validacion datos de usuario |

**Ejecucion:**
```bash
cd backend
pytest tests/unit/ -v
```

### 2.2 Tests de integracion

**Herramienta:** pytest + httpx (TestClient de FastAPI)
**Ubicacion:** `backend/tests/integration/`
**Alcance:** endpoints reales contra BD de test (MySQL en Docker)

| Modulo | Que se testea |
|--------|---------------|
| M0 | GET /health retorna 200 |
| M1 | Login crea sesion, logout invalida, /me funciona, middleware rechaza sin auth |
| M2 | CRUD completo de solicitudes, filtros, paginacion, auditoria |
| M3 | Flujo completo REGISTRADO->CERRADO, acciones bloqueadas por POLICY, R10, 403/422/409 |
| M4 | Upload, download, asociacion a solicitud/pago |
| M5 | CRUD usuarios, suspension invalida sesiones, reset password |

**Ejecucion:**
```bash
cd backend
pytest tests/integration/ -v
```

**Setup de BD de test:**
- Docker compose levanta MySQL de test (`cmep_test`)
- Alembic aplica migraciones
- Fixture crea datos seed antes de cada sesion de test
- Teardown limpia BD despues de cada test (rollback o truncate)

### 2.3 Smoke flow manual

**Proposito:** validar flujos end-to-end desde el navegador, incluyendo UX.

**Formato por modulo:**
```
Paso | Accion | Resultado esperado | OK?
-----|--------|--------------------|----|
1    | ...    | ...                | [ ]
```

#### Smoke M0 — Bootstrap
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | `docker-compose up` | 3 servicios levantan sin errores |
| 2 | `curl localhost:8000/health` | `{"ok": true}` |
| 3 | Abrir `localhost:3000` | Pantalla con estado "Conectado" |

#### Smoke M1 — Auth
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | Abrir `/login` | Formulario email + password |
| 2 | Login con admin seed | Redirect a `/app`, muestra nombre |
| 3 | Abrir `/app` en tab nueva | Sesion activa, carga inicio |
| 4 | Logout | Redirect a `/login` |
| 5 | Abrir `/app` | Redirect a `/login` (sin sesion) |
| 6 | Login con user SUSPENDIDO | Mensaje de error, no entra |

#### Smoke M2 — Solicitudes
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | Login como OPERADOR | Acceso a app |
| 2 | Ir a `/app/solicitudes/nueva` | Formulario de registro |
| 3 | Llenar datos minimos y enviar | Redirect a lista, solicitud aparece |
| 4 | Click en solicitud | Detalle con estado REGISTRADO |
| 5 | Editar un campo | Campo actualizado, historial registrado |

#### Smoke M3 — Workflow completo
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | Login como ADMIN | Acceso completo |
| 2 | Crear solicitud | Estado: REGISTRADO |
| 3 | Asignar gestor | Estado: ASIGNADO_GESTOR |
| 4 | Login como GESTOR | Ver solicitud asignada |
| 5 | Registrar pago | Estado: PAGADO |
| 6 | Asignar medico | Estado: ASIGNADO_MEDICO |
| 7 | Login como MEDICO | Ver solicitud asignada |
| 8 | Cerrar solicitud | Estado: CERRADO |
| 9 | Login como ADMIN | Override en solicitud cerrada |
| 10 | Intentar accion no permitida | 403 / modal "No autorizado" |

#### Smoke M4 — Archivos
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | Abrir detalle de solicitud | Seccion archivos visible |
| 2 | Subir archivo | Archivo aparece en lista |
| 3 | Descargar archivo | Archivo se descarga correctamente |

#### Smoke M5 — Admin
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | Login como ADMIN | Menu "Usuarios" visible |
| 2 | Crear usuario OPERADOR | Usuario aparece en lista |
| 3 | Logout, login como nuevo usuario | Acceso con rol correcto |
| 4 | Login como ADMIN, suspender usuario | Usuario suspendido |
| 5 | Intentar login como suspendido | Login rechazado |

#### Smoke M6 — Cloud
| Paso | Accion | Resultado esperado |
|------|--------|--------------------|
| 1 | Abrir URL publica | Frontend carga via HTTPS |
| 2 | Login | Sesion funciona con cookies |
| 3 | Flujo completo (M3 smoke) | Funciona igual que en local |
| 4 | Upload archivo | Se sube a S3 correctamente |

## 3. Estructura de archivos de test

```
backend/tests/
  conftest.py              # fixtures globales: DB session, test client, seed data
  unit/
    test_hashing.py
    test_email_normalization.py
    test_estado_operativo.py
    test_policy.py
    test_schemas.py
  integration/
    test_health.py
    test_auth.py
    test_solicitudes_crud.py
    test_solicitudes_workflow.py
    test_archivos.py
    test_admin.py
```

## 4. Fixtures principales (conftest.py)

```python
# Conceptual — no es codigo final
@fixture(scope="session")
def db_engine():
    # Conexion a MySQL de test
    # Ejecutar Alembic upgrade head

@fixture(scope="function")
def db_session(db_engine):
    # Crear session con rollback automatico

@fixture
def client(db_session):
    # TestClient de FastAPI con override de DB

@fixture
def admin_user(db_session):
    # Usuario ADMIN con sesion activa

@fixture
def operador_user(db_session):
    # Usuario OPERADOR con sesion activa

@fixture
def sample_solicitud(db_session, admin_user):
    # Solicitud de prueba en estado REGISTRADO
```

## 5. Criterios de cobertura

| Tipo | Objetivo minimo |
|------|-----------------|
| Unitario | 100% de derivar_estado_operativo, POLICY, hashing |
| Integracion | Todos los endpoints con happy path + errores principales |
| Smoke manual | Flujo completo por modulo |

## 6. CI/CD (futuro)

Para V1 MVP, los tests se ejecutan manualmente:
```bash
# Levantar BD de test
docker-compose -f infra/docker-compose.test.yml up -d

# Ejecutar tests
cd backend && pytest tests/ -v --tb=short

# Apagar BD de test
docker-compose -f infra/docker-compose.test.yml down -v
```

En fases futuras: GitHub Actions con MySQL service container.
