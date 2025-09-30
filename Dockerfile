# Usar imagen base de Python 3.13 slim
FROM python:3.13-slim

# Instalar dependencias del sistema necesarias para WeasyPrint y procesamiento de imágenes
# Se usa 'curl' para el HEALTHCHECK
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    libffi-dev \
    libgdk-pixbuf-2.0-dev \
    libpango1.0-dev \
    libxml2-dev \
    libxslt1-dev \
    shared-mime-info \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    gcc \
    g++ \
    make \
    curl \
    # Limpiar caché para reducir el tamaño de la imagen
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar Poetry
RUN pip install --no-cache-dir poetry

# Establecer directorio de trabajo
WORKDIR /app

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Copiar archivos de dependencia
COPY pyproject.toml ./
COPY poetry.lock ./

# Instalar dependencias con Poetry (sin entorno virtual, sin instalar el proyecto actual)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# *** CORRECCIÓN CRÍTICA: Cambiar el usuario predeterminado de ejecución a 'app' ***
# Esto asegura que el CMD se ejecute con los permisos correctos
USER app

# Copiar el resto del código
COPY . .

# Exponer puerto (documentación)
EXPOSE 8000

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FASTAPI_ENV=production

# Comando de salud para Docker
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto - Utiliza 0.0.0.0 para que el servidor escuche tráfico externo
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]