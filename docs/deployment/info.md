```markdown
# CMEP – Infraestructura AWS (Actualizada)

---

## 🌎 Región
- **us-east-1 (N. Virginia)**
- Seleccionada por:
  - Menor costo relativo
  - Alta disponibilidad
  - Soporte completo para RDS, App Runner, S3 y Secrets Manager

---

## 🧱 VPC

- Nombre: `vpc-cmep-prod`
- CIDR: `10.0.0.0/16`
- DNS Resolution: Enabled
- DNS Hostnames: Enabled

Uso:
- Aislamiento de red para CMEP
- Control de tráfico interno y externo

---

## 🌐 Internet Gateway

- Nombre: `igw-cmep-prod`
- Función:
  - Permitir acceso público controlado
  - Necesario para App Runner y accesos administrativos

---

## 🌐 Subnets Públicas

| Subnet | AZ | CIDR |
|------|-------------|-------------|
| subnet-cmep-public-1 | us-east-1a | 10.0.10.0/24 |
| subnet-cmep-public-2 | us-east-1b | 10.0.11.0/24 |

Configuración:
- Auto assign public IP: Enabled
- Route table pública asociada
- Usadas por App Runner y accesos administrativos

---

## 🔐 Security Groups

### SG-RDS-CMEP
**Uso:** Base de datos MySQL

Inbound:
- MySQL 3306 desde IPs administrativas autorizadas
- MySQL 3306 desde `SG-AppRunner-CMEP`

Outbound:
- All traffic

---

### SG-AppRunner-CMEP
**Uso:** Backend FastAPI

Inbound:
- Ninguno (App Runner maneja HTTP)

Outbound:
- MySQL 3306 hacia `SG-RDS-CMEP`

---

## 🗄 Base de Datos – RDS MySQL

- Engine: MySQL 8
- Instancia: `db.t3.micro`
- Storage: 20 GiB
- Deployment: Single-AZ
- Public Access: Enabled (temporal / controlado)
- Encryption: AWS KMS Enabled
- Backups automáticos: 7 días
- Actualizaciones menores automáticas: Enabled

---

## 📂 Database

- Nombre: `cmep_prod`
- Charset: `utf8mb4`
- Collation: `utf8mb4_unicode_ci`

---

## 🔑 Acceso a Base de Datos

### Administrador
- Usuario: `admin`
- Uso:
  - Administración
  - Migraciones estructurales
  - Debug
- Acceso:
  - MySQL Workbench
  - MySQL CLI
  - SSL obligatorio

---

### Aplicación
- Usuario: `cmep_user`
- Permisos:
  - SELECT
  - INSERT
  - UPDATE
  - DELETE
- Scope:
  - Solo sobre `cmep_prod.*`
- Uso:
  - Backend FastAPI (App Runner)
- Credenciales:
  - Almacenadas en AWS Secrets Manager

---

## 🌐 Endpoint RDS

```

cmep-db-prod.csrc06e8u5uo.us-east-1.rds.amazonaws.com
Puerto: 3306

```

---

## 🗂 S3

### cmep-archivos-prod
- Uso: Documentos y adjuntos
- Acceso: Controlado
- Cifrado: SSE-S3

### cmep-frontend-prod
- Uso: Hosting frontend
- Acceso: Público
- Cifrado: SSE-S3

---

## 🔐 Secrets Manager

Secret: `cmep-prod-secrets`

Contiene:
- DB_URL
- DB_USER
- DB_PASSWORD
- SESSION_SECRET
- S3_BUCKET

---

## 🔒 Seguridad

- Acceso RDS restringido por IP y SG
- SSL obligatorio en MySQL
- Cifrado en reposo (KMS)
- Cifrado en tránsito
- Backups automáticos
- Principio de mínimo privilegio aplicado

---

## 📊 Monitoreo

- CloudWatch Metrics:
  - CPU RDS
  - Conexiones MySQL
  - Storage
- Alarmas (pendiente):
  - CPU alta
  - Storage bajo
  - Fallos de conexión

---

## 📌 Estado Actual

Completado:
- VPC y red pública
- RDS MySQL operativo
- Security Groups configurados
- Buckets S3 creados
- Secrets Manager operativo
- Usuario `cmep_user` creado con permisos mínimos

---

## 🚀 Próximos Pasos
Pendiente
```
