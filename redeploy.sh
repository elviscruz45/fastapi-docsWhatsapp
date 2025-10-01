#!/bin/bash

# Script para redeploy con cambios de CORS
echo "🔄 Rebuilding and redeploying with CORS fixes..."

# Parar contenedores existentes
docker-compose down

# Rebuild la imagen
docker-compose build --no-cache

# Levantar servicios
docker-compose up -d

echo "✅ Redeploy completed!"
echo "🌐 API running on: http://localhost:8000"
echo "📋 Test CORS at: http://localhost:8000/test-cors"
echo ""
echo "🚀 Para production, ejecuta:"
echo "   docker build -t fastapi-docswhatsapp ."
echo "   docker run -p 8000:8000 fastapi-docswhatsapp"