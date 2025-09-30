#!/bin/bash

# Script de verificación pre-deployment
echo "🔍 Verificando configuración del proyecto..."

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

checks_passed=0
total_checks=0

check() {
    ((total_checks++))
    if eval "$2"; then
        echo -e "${GREEN}✅${NC} $1"
        ((checks_passed++))
        return 0
    else
        echo -e "${RED}❌${NC} $1"
        if [ ! -z "$3" ]; then
            echo -e "   ${YELLOW}💡${NC} $3"
        fi
        return 1
    fi
}

echo ""
echo "📋 Verificando archivos necesarios..."

check "Dockerfile existe" "[ -f Dockerfile ]" "Ejecuta: Revisa los archivos creados"
check "docker-compose.yml existe" "[ -f docker-compose.yml ]"
check "requirements.txt existe" "[ -f requirements.txt ]"
check ".dockerignore existe" "[ -f .dockerignore ]"
check "Script de deployment existe" "[ -f deploy.sh ]"
check "Makefile existe" "[ -f Makefile ]"

echo ""
echo "🔑 Verificando configuración..."

check "Archivo .env existe" "[ -f .env ]" "Copia .env.example a .env y configúralo"

if [ -f .env ]; then
    check "GEMINI_API_KEY configurado" "grep -q '^GEMINI_API_KEY=' .env && ! grep -q 'your_gemini_api_key_here' .env" "Configura tu API key de Gemini en .env"
    check "GEMINI_MODEL configurado" "grep -q '^GEMINI_MODEL=' .env"
fi

echo ""
echo "🐳 Verificando Docker..."

check "Docker instalado" "command -v docker >/dev/null 2>&1" "Instala Docker desde https://docker.com"
check "Docker compose disponible" "docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1" "Instala Docker Compose"

if command -v docker >/dev/null 2>&1; then
    check "Docker daemon corriendo" "docker ps >/dev/null 2>&1" "Inicia Docker Desktop o el servicio de Docker"
fi

echo ""
echo "📁 Verificando estructura del proyecto..."

check "Directorio main app existe" "[ -d fastapi_docswhatsapp ]"
check "main.py existe" "[ -f main.py ]"
check "Servicios Gemini existe" "[ -f fastapi_docswhatsapp/services/gemini_analyzer.py ]"
check "Configuración existe" "[ -f fastapi_docswhatsapp/config/settings.py ]"

echo ""
echo "🧪 Verificando imports críticos..."

if [ -f main.py ]; then
    check "Import de FastAPI correcto" "grep -q 'from fastapi import FastAPI' main.py"
    check "Import de WeasyPrint correcto" "grep -q 'from weasyprint import HTML' main.py"
    check "Import de Gemini correcto" "grep -q 'GeminiAnalyzer' main.py"
fi

echo ""
echo "📊 Resumen de verificación:"
echo "   Verificaciones pasadas: $checks_passed/$total_checks"

if [ $checks_passed -eq $total_checks ]; then
    echo -e "${GREEN}🎉 ¡Todas las verificaciones pasaron! El proyecto está listo para deployment.${NC}"
    echo ""
    echo "🚀 Próximos pasos:"
    echo "   1. Configurar variables en .env"
    echo "   2. Ejecutar: ./deploy.sh dev (desarrollo)"
    echo "   3. Ejecutar: ./deploy.sh prod (producción)"
    echo "   4. Para DigitalOcean: ./deploy.sh deploy-do"
    exit 0
else
    failed=$((total_checks - checks_passed))
    echo -e "${RED}⚠️  $failed verificaciones fallaron. Por favor corrige los problemas antes de continuar.${NC}"
    exit 1
fi