# 🚀 Guía de Despliegue - WhatsApp Analyzer

## 📋 Índice

- [Requisitos Previos](#requisitos-previos)
- [Configuración Local](#configuración-local)
- [Docker Development](#docker-development)
- [Docker Production](#docker-production)
- [Despliegue en DigitalOcean](#despliegue-en-digitalocean)
- [Comandos Útiles](#comandos-útiles)
- [Troubleshooting](#troubleshooting)

## 🔧 Requisitos Previos

### Sistema Local

- Docker (versión 20.10 o superior)
- Docker Compose (versión 2.0 o superior)
- Git

### Cuentas de Servicio

- **Google AI Studio**: API Key para Gemini
- **Supabase**: URL y API Key (opcional)
- **DigitalOcean**: Cuenta para deployment

## ⚙️ Configuración Local

### 1. Clonar y Configurar

```bash
git clone <tu-repo>
cd fastapi-docswhatsapp

# Copiar archivo de configuración
cp .env.example .env
```

### 2. Configurar Variables de Entorno

Edita el archivo `.env`:

```bash
# Google Gemini Configuration (OBLIGATORIO)
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
GEMINI_MODEL=gemini-2.5-flash-lite

# Supabase Configuration (Opcional)
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
SUPABASE_STORAGE_BUCKET=whatsapp-reports

# Application Configuration
APP_NAME=WhatsApp Chat Analyzer API
APP_VERSION=2.0.0
DEBUG=False

# File Configuration
MAX_FILE_SIZE=52428800
MAX_MESSAGES_TO_ANALYZE=1000
MAX_ANALYSIS_TOKENS=8000

# CORS Configuration
CORS_ORIGINS=["*"]
```

## 🛠️ Docker Development

### Modo Desarrollo (Con Hot Reload)

```bash
# Usar el script de despliegue
./deploy.sh dev

# O manualmente
docker-compose --profile dev up whatsapp-analyzer-dev
```

**Acceso:**

- API: http://localhost:8001
- Documentación: http://localhost:8001/docs
- Health Check: http://localhost:8001/health

### Características del Modo Dev:

- ✅ Hot reload automático
- ✅ Código montado como volumen
- ✅ Logs detallados
- ✅ Puerto 8001 para evitar conflictos

## 🚀 Docker Production

### Modo Producción

```bash
# Usar el script de despliegue
./deploy.sh prod

# O manualmente
docker-compose up -d whatsapp-analyzer
```

**Acceso:**

- API: http://localhost:8000
- Documentación: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Comandos de Gestión

```bash
# Ver logs
./deploy.sh logs

# Verificar salud del servicio
./deploy.sh health

# Detener servicios
./deploy.sh stop
```

## ☁️ Despliegue en DigitalOcean

### Opción 1: DigitalOcean App Platform (Recomendado)

#### Paso 1: Preparar Repositorio

```bash
# Hacer commit de todos los cambios
git add .
git commit -m "feat: Docker configuration for deployment"
git push origin main
```

#### Paso 2: Crear App en DigitalOcean

1. Ve a [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Conecta tu repositorio de GitHub
4. Selecciona la rama `main`
5. DigitalOcean detectará automáticamente Python

#### Paso 3: Configurar Variables de Entorno

En la sección "Environment Variables":

| Variable         | Valor                      | Tipo   |
| ---------------- | -------------------------- | ------ |
| `GEMINI_API_KEY` | tu_api_key                 | SECRET |
| `GEMINI_MODEL`   | gemini-2.5-flash-lite      | TEXT   |
| `SUPABASE_URL`   | tu_supabase_url            | SECRET |
| `SUPABASE_KEY`   | tu_supabase_key            | SECRET |
| `APP_NAME`       | WhatsApp Chat Analyzer API | TEXT   |
| `DEBUG`          | False                      | TEXT   |
| `FASTAPI_ENV`    | production                 | TEXT   |

#### Paso 4: Configurar Recursos

- **Plan**: Basic ($5/mes)
- **CPU**: 0.5 vCPU
- **RAM**: 512 MB
- **Instancias**: 1

#### Paso 5: Desplegar

```bash
# Información del deployment
./deploy.sh deploy-do
```

### Opción 2: Droplet con Docker

#### Crear Droplet

```bash
# Instalar doctl (CLI de DigitalOcean)
# En el droplet
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Clonar repositorio
git clone <tu-repo>
cd fastapi-docswhatsapp

# Configurar .env
cp .env.example .env
nano .env  # Editar con tus variables

# Desplegar
./deploy.sh prod
```

## 🔨 Comandos Útiles

### Docker

```bash
# Rebuild completo
docker-compose build --no-cache

# Ver containers activos
docker ps

# Logs en tiempo real
docker-compose logs -f

# Eliminar todo (containers, images, volumes)
docker-compose down -v --rmi all

# Acceder al container
docker exec -it whatsapp-analyzer bash
```

### Debug

```bash
# Ver variables de entorno en el container
docker exec whatsapp-analyzer env | grep GEMINI

# Test de conexión
curl -f http://localhost:8000/health

# Ver logs específicos
docker logs whatsapp-analyzer --tail 50
```

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Error: "GEMINI_API_KEY not found"

**Solución:**

```bash
# Verificar archivo .env
cat .env | grep GEMINI_API_KEY

# Reconstruir container
docker-compose down
docker-compose up --build
```

#### 2. Error: "WeasyPrint dependencies missing"

**Causa:** Dependencias del sistema faltantes
**Solución:** Ya incluidas en el Dockerfile

#### 3. Puerto 8000 ya en uso

**Solución:**

```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8080:8000"  # Usar puerto 8080 localmente
```

#### 4. Container se cierra inmediatamente

**Debug:**

```bash
# Ver logs de error
docker-compose logs whatsapp-analyzer

# Ejecutar en modo interactivo
docker run -it --rm whatsapp-analyzer bash
```

### Verificación de Salud

#### Health Check Manual

```bash
curl -v http://localhost:8000/health
```

**Respuesta esperada:**

```json
{
  "status": "healthy",
  "service": "whatsapp-analyzer"
}
```

#### Test de Funcionalidad

```bash
# Test del endpoint principal (necesita archivo ZIP)
curl -X POST "http://localhost:8000/crear-informe-final" \
  -H "accept: application/pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_chat.zip"
```

### Logs y Monitoring

#### Ver Logs por Servicio

```bash
# Solo API
docker-compose logs api

# Con timestamp
docker-compose logs -t api

# Últimas 100 líneas
docker-compose logs --tail 100 api
```

#### Monitoring de Recursos

```bash
# Uso de CPU/RAM
docker stats whatsapp-analyzer

# Espacio en disco
docker system df
```

## 📊 Métricas de Performance

### Recursos Recomendados

- **Desarrollo**: 512 MB RAM, 0.25 CPU
- **Producción**: 1 GB RAM, 0.5 CPU
- **Alto Tráfico**: 2 GB RAM, 1 CPU

### Límites de Archivos

- Tamaño máximo de ZIP: 50 MB
- Tiempo máximo de procesamiento: 2 minutos
- Tokens máximos para Gemini: 8,000

## 🔐 Seguridad

### Variables Sensibles

- Nunca commitear archivos `.env` con datos reales
- Usar secrets en DigitalOcean App Platform
- Rotar API keys periódicamente

### Network Security

- El container corre con usuario no-root
- Puerto expuesto solo el necesario (8000)
- No se almacenan archivos permanentemente

---

## 📞 Soporte

Si tienes problemas:

1. **Revisa los logs**: `./deploy.sh logs`
2. **Verifica salud**: `./deploy.sh health`
3. **Rebuild limpio**: `docker-compose build --no-cache`
4. **Verifica variables**: Asegúrate que `.env` esté correcto

**¡Listo para desplegar! 🚀**
