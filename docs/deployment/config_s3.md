# AWS App Runner + RDS + S3 Privado — Checklist Reutilizable

## Objetivo
Backend en App Runner conectado a RDS privado y S3 sin usar NAT Gateway, usando VPC Endpoint para reducir costos y mejorar seguridad.

---

## Arquitectura
App Runner → Custom VPC → Subnets Privadas → RDS Privado  
App Runner → Custom VPC → Subnets Privadas → VPC Endpoint S3 → S3 Bucket  

---

## Recursos Base (Ejemplo CMEP)
VPC: vpc-cmep-prod (vpc-094b487cd8aee9831)  
Subnets Públicas: subnet-cmep-public-1, subnet-cmep-public-2  
Subnets Privadas: subnet-cmep-private-1, subnet-cmep-private-2  
Route Table Privada: rtb-cmep-private (rtb-06111a46b25f19511)  
Security Group Backend: SG-AppRunner-CMEP  
Security Group DB: SG-RDS-CMEP  
Bucket S3: cmep-archivos-prod  
Endpoint S3: cmep-endpoint-s3  

---

## Paso 1 — Subnets
Subnets públicas deben tener ruta 0.0.0.0/0 hacia Internet Gateway.  
Subnets privadas NO deben tener salida directa a internet.

---

## Paso 2 — RDS Privado
Ubicar RDS en subnets privadas.  
Security Group RDS debe permitir puerto 3306 desde SG-AppRunner-CMEP.

---

## Paso 3 — Configurar App Runner
Outgoing network traffic debe ser Custom VPC.  
Seleccionar subnets privadas.  
Asignar Security Group SG-AppRunner-CMEP.

---

## Paso 4 — Crear Endpoint S3
Ir a VPC → Endpoints → Create endpoint.  
Seleccionar servicio com.amazonaws.us-east-1.s3.  
Tipo Gateway.  
Seleccionar VPC principal.  
Asociar route table privada rtb-cmep-private.  
Policy Full Access.

---

## Paso 5 — Validar Route Table Privada
Debe existir ruta automática hacia S3 usando prefix list apuntando al VPC Endpoint.

---

## Paso 6 — Configurar Security Group Backend
Outbound debe permitir:
Puerto 443 HTTPS hacia 0.0.0.0/0  
Puerto 3306 hacia SG-RDS-CMEP  

---

## Paso 7 — IAM Role App Runner
Permisos mínimos:
s3:PutObject  
s3:GetObject  
s3:DeleteObject  
s3:ListBucket  

---

## Qué NO usar
No crear NAT Gateway si solo se necesita acceso a S3 y RDS.  
No exponer RDS públicamente.  
No usar access keys en código.

---

## Cuándo usar NAT Gateway
Solo si backend necesita consumir APIs externas, OAuth, SMTP externo, scraping o SaaS públicos.

---

## Troubleshooting
Timeout S3 indica problema de red o Security Group.  
AccessDenied indica problema IAM o bucket policy.  
Verificar que App Runner use subnets privadas correctas.  
Verificar endpoint asociado a route table correcta.  
Verificar outbound 443 habilitado.

---

## Buenas Prácticas
Usar IAM roles.  
Mantener RDS privado.  
Separar Security Groups por servicio.  
Preferir VPC Endpoints antes que NAT.  
Validar conectividad antes de producción.

---

## Checklist Final
App Runner en Custom VPC configurado  
Subnets privadas configuradas  
RDS accesible desde backend  
Endpoint S3 creado y asociado  
Security Group outbound 443 habilitado  
Permisos IAM configurados  
Subida a S3 validada
