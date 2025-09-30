# Makefile para WhatsApp Analyzer
.PHONY: help build dev prod stop logs health clean test

# Variables
DOCKER_COMPOSE = docker-compose
SERVICE_NAME = whatsapp-analyzer

help: ## Mostrar esta ayuda
	@echo "WhatsApp Analyzer - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Configuración inicial
	@echo "🔧 Configuración inicial..."
	@if [ ! -f .env ]; then \
		echo "Creando archivo .env desde .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Por favor configura las variables en .env"; \
	else \
		echo "✅ Archivo .env ya existe"; \
	fi

build: ## Construir imagen Docker
	@echo "🏗️  Construyendo imagen Docker..."
	$(DOCKER_COMPOSE) build --no-cache

dev: ## Ejecutar en modo desarrollo
	@echo "🛠️  Iniciando modo desarrollo..."
	$(DOCKER_COMPOSE) --profile dev up whatsapp-analyzer-dev

prod: build ## Ejecutar en modo producción
	@echo "🚀 Iniciando modo producción..."
	$(DOCKER_COMPOSE) up -d $(SERVICE_NAME)
	@echo "✅ Servicio disponible en http://localhost:8000"

stop: ## Detener servicios
	@echo "⏹️  Deteniendo servicios..."
	$(DOCKER_COMPOSE) down

restart: stop prod ## Reiniciar servicios en producción

logs: ## Ver logs del servicio
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

health: ## Verificar salud del servicio
	@echo "🏥 Verificando salud del servicio..."
	@curl -f http://localhost:8000/health > /dev/null 2>&1 && \
		echo "✅ Servicio funcionando correctamente" || \
		echo "❌ Servicio no está respondiendo"

clean: stop ## Limpiar containers, imágenes y volúmenes
	@echo "🧹 Limpiando recursos Docker..."
	$(DOCKER_COMPOSE) down -v --rmi local
	docker system prune -f

test: ## Ejecutar tests (cuando estén disponibles)
	@echo "🧪 Ejecutando tests..."
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python -m pytest

shell: ## Acceder al shell del container
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) bash

ps: ## Ver estado de containers
	$(DOCKER_COMPOSE) ps

stats: ## Ver estadísticas de recursos
	docker stats $(SERVICE_NAME) --no-stream

# Comandos para desarrollo
install-deps: ## Instalar dependencias localmente
	pip install -r requirements.txt

format: ## Formatear código (requiere black)
	black . --line-length 100

lint: ## Revisar código (requiere flake8)
	flake8 . --max-line-length 100 --exclude venv,env,.venv,.env

# Comandos para deployment
deploy-check: ## Verificar configuración para deployment
	@echo "🔍 Verificando configuración para deployment..."
	@test -f .env || (echo "❌ Archivo .env faltante" && exit 1)
	@test -f Dockerfile || (echo "❌ Dockerfile faltante" && exit 1)
	@test -f docker-compose.yml || (echo "❌ docker-compose.yml faltante" && exit 1)
	@grep -q "GEMINI_API_KEY" .env || (echo "❌ GEMINI_API_KEY no configurado" && exit 1)
	@echo "✅ Configuración lista para deployment"

# Backup y restore (para cuando tengas persistencia)
backup: ## Crear backup de datos
	@echo "💾 Creando backup..."
	# Agregar comandos de backup cuando sea necesario

restore: ## Restaurar datos desde backup
	@echo "📥 Restaurando backup..."
	# Agregar comandos de restore cuando sea necesario