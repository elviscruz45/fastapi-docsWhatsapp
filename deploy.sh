#!/bin/bash

# Script de despliegue para WhatsApp Analyzer
set -e

echo "🚀 Iniciando proceso de despliegue para WhatsApp Analyzer..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Verificar que docker-compose esté disponible
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "docker-compose no está disponible. Por favor instala docker-compose."
    exit 1
fi

# Usar docker compose o docker-compose según disponibilidad
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

# Verificar archivo .env
if [ ! -f .env ]; then
    warn "Archivo .env no encontrado. Creando desde .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        warn "Por favor configura las variables en .env antes de continuar."
        exit 1
    else
        error "No se encontró .env.example. Crea el archivo .env manualmente."
        exit 1
    fi
fi

# Verificar variables críticas
log "Verificando configuración..."
if ! grep -q "GEMINI_API_KEY=" .env || ! grep -q "SUPABASE_URL=" .env; then
    error "Variables críticas faltantes en .env (GEMINI_API_KEY, SUPABASE_URL)"
    exit 1
fi

# Build de la imagen
log "Construyendo imagen Docker..."
$COMPOSE_CMD build --no-cache

# Función para modo desarrollo
dev() {
    log "Iniciando en modo desarrollo..."
    $COMPOSE_CMD --profile dev up whatsapp-analyzer-dev
}

# Función para modo producción
prod() {
    log "Iniciando en modo producción..."
    $COMPOSE_CMD up -d whatsapp-analyzer
    log "Servicio iniciado en http://localhost:8000"
    log "Documentación disponible en http://localhost:8000/docs"
    log "Health check: http://localhost:8000/health"
}

# Función para detener servicios
stop() {
    log "Deteniendo servicios..."
    $COMPOSE_CMD down
}

# Función para mostrar logs
logs() {
    $COMPOSE_CMD logs -f whatsapp-analyzer
}

# Función para verificar salud del servicio
health() {
    log "Verificando salud del servicio..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        log "✅ Servicio está funcionando correctamente"
    else
        error "❌ Servicio no está respondiendo"
        exit 1
    fi
}

# Función para deployment en DigitalOcean
deploy_do() {
    log "Preparando deployment para DigitalOcean..."
    
    if [ ! -f .do/app.yaml ]; then
        error "Archivo .do/app.yaml no encontrado"
        exit 1
    fi
    
    log "Configuración encontrada:"
    log "1. Asegúrate de tener doctl instalado y autenticado"
    log "2. Configura las variables de entorno en DigitalOcean App Platform"
    log "3. Ejecuta: doctl apps create .do/app.yaml"
    log "4. O usa la interfaz web de DigitalOcean"
    
    warn "Variables de entorno requeridas en DigitalOcean:"
    echo "  - GEMINI_API_KEY (SECRET)"
    echo "  - SUPABASE_URL (SECRET)"
    echo "  - SUPABASE_KEY (SECRET)"
}

# Parse de argumentos
case "$1" in
    "dev")
        dev
        ;;
    "prod")
        prod
        ;;
    "stop")
        stop
        ;;
    "logs")
        logs
        ;;
    "health")
        health
        ;;
    "deploy-do")
        deploy_do
        ;;
    *)
        echo "Uso: $0 {dev|prod|stop|logs|health|deploy-do}"
        echo ""
        echo "Comandos:"
        echo "  dev       - Ejecutar en modo desarrollo con hot reload"
        echo "  prod      - Ejecutar en modo producción"
        echo "  stop      - Detener todos los servicios"
        echo "  logs      - Ver logs del servicio"
        echo "  health    - Verificar salud del servicio"
        echo "  deploy-do - Información para deployment en DigitalOcean"
        exit 1
        ;;
esac