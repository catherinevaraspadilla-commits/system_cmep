
## Operaciones Recurrentes

### Redesplegar backend (cambios de codigo)

#### Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 114082792962.dkr.ecr.us-east-1.amazonaws.com

#### Comandos
```bash
# 1. Build y push imagen
Opción 1 — desde la raíz del proyecto (sin el cd backend):
docker build -t cmep-backend ./backend

Opción 2 — si ya estás dentro de backend/:
docker build -t cmep-backend .

docker tag cmep-backend:latest 114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest
docker push 114082792962.dkr.ecr.us-east-1.amazonaws.com/cmep-backend:latest

# 2. App Runner detecta nueva imagen y redespliega automaticamente (si auto-deploy esta ON)
#    Si no, ir a App Runner > Deploy
```

### Redesplegar frontend (cambios de UI)
```bash
# 1. Build
cd frontend
$env:VITE_API_URL="https://api.cmepdoc.com"
npm run build

# 2. Upload
aws s3 sync dist/ s3://cmep-archivos-frontend/ --delete

aws cloudfront create-invalidation --distribution-id E2QYC21NF9GJUY --paths "/index.html" "/assets/*"

# 3. Invalidar cache
aws cloudfront create-invalidation --distribution-id E2QYC21NF9GJUY --paths "/*"

aws cloudfront create-invalidation --distribution-id E2QYC21NF9GJUY --paths "/index.html" "/assets/*"