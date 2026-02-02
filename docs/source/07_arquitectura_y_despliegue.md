# Arquitectura Cloud (AWS) y Diseño Web + Móvil sin Doble Esfuerzo

## Objetivo
Construir CMEP como una sola aplicación web accesible desde escritorio y móvil mediante una única URL.  
No se implementa PWA en la V1.

El diseño deja preparado el frontend para una futura incorporación de PWA sin retrabajo, manteniendo:
- un solo frontend
- un solo backend
- una sola fuente de verdad para permisos y estados

## Principios de Diseño (para evitar retrabajo)
- Single Frontend: frontend web responsive (mobile-first)
- Single Backend: API en Python con sesiones del lado del servidor
- Una sola fuente de verdad: el backend valida permisos, estados y reglas; el frontend solo presenta UI
- Infra cloud desacoplada: frontend estático, backend de aplicación, base de datos transaccional y almacenamiento de archivos independientes
- Evolución sin retrabajo: arquitectura preparada para agregar PWA en una fase posterior

## Componentes AWS Requeridos

### 1) Amazon RDS (MySQL) — Persistencia Transaccional
Propósito:
- Almacenar información transaccional del sistema CMEP
- Soportar autenticación basada en sesiones

Uso funcional:
- Persistencia de usuarios
- Persistencia de sesiones activas
- Persistencia de solicitudes y su evolución
- Persistencia de metadatos de archivos

Uso técnico:
- Validación de credenciales
- Creación y validación de sesiones
- Lectura y escritura transaccional del negocio

Configuración mínima recomendada:
- MySQL 8
- Instancia pequeña (t3.micro o t3.small)
- Backups automáticos (7–14 días)
- Acceso solo desde backend
- Preparado para alta disponibilidad futura

### 2) AWS App Runner — Backend de Aplicación
Propósito:
- Ejecutar el backend Python como servicio administrado

Uso técnico:
- Recibe requests del frontend
- Aplica autenticación, autorización y reglas de negocio
- Se comunica con la base de datos
- Gestiona subida y descarga de archivos

Configuración mínima:
- Despliegue desde repo o imagen Docker
- Recursos escalables
- Variables de entorno externas
- Rol IAM con acceso controlado a:
  - secretos
  - almacenamiento de archivos

### 3) Amazon S3 — Almacenamiento de Archivos y Frontend
Propósito:
- Almacenar archivos del negocio
- Alojar frontend web estático

Uso técnico (archivos):
- Archivos fuera de la base de datos
- Acceso controlado por backend
- Uso de URLs firmadas con vencimiento

Uso técnico (frontend):
- Build del frontend como contenido estático
- Un solo index.html para toda la app

Configuración mínima:
- Bucket privado para archivos
- Bucket separado para frontend
- Cifrado por defecto habilitado

### 4) Amazon CloudFront — CDN y HTTPS
Propósito:
- Distribuir frontend de forma segura y eficiente

Uso técnico:
- Origen: bucket de frontend
- Soporte SPA con fallback a index.html
- Terminación HTTPS

### 5) AWS Secrets Manager
Propósito:
- Gestión segura de secretos

Uso técnico:
- Backend obtiene secretos en runtime
- No hay secretos en código ni repositorio

### 6) Amazon CloudWatch
Propósito:
- Observabilidad del sistema

Uso técnico:
- Logs centralizados del backend
- Métricas y alarmas por errores o carga

### 7) EventBridge + Lambda — Tareas Programadas
Propósito:
- Ejecutar tareas de mantenimiento

Uso técnico:
- Limpieza de sesiones expiradas
- Ejecución automática periódica

### 8) AWS IAM
Propósito:
- Control de acceso entre componentes

Uso técnico:
- Acceso mínimo necesario
- Principio de menor privilegio

## Diseño Web y Móvil sin Doble Esfuerzo

### Frontend Web Responsive
- Un solo frontend para escritorio y móvil
- Mobile-first real
- Preparado para futura PWA sin reescritura

### Autenticación en Web
Objetivo:
- Autenticación consistente en desktop y móvil

Flujo técnico:
1. El frontend envía credenciales
2. El backend valida y crea sesión
3. El backend devuelve cookie segura
4. Cada request privado valida sesión y permisos

## Fases de Desarrollo

### Fase Inicial
- Estructura de repositorio clara
- Separación frontend / backend
- Definición temprana de rutas privadas

### Desarrollo Local
- Backend completo en local
- Frontend responsive desde el inicio
- Pruebas tempranas en navegador móvil

### Despliegue en AWS
- Migración sin cambios de arquitectura
- Pruebas de login y sesiones en entorno real

## Consideraciones de Desarrollo
- Variables por entorno bien definidas
- Pruebas de cookies y CORS desde el inicio
- Build reproducible del frontend
- Enfoque mobile-first real
