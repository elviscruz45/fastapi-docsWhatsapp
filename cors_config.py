# Configuración de CORS para el proyecto
import os

# Orígenes permitidos para CORS
ALLOWED_ORIGINS = [
    "https://platform.minetrack.site",
    "https://www.platform.minetrack.site",
    "http://localhost:19006",  # Expo development
    "http://localhost:3000",   # React development
    "http://localhost:8080",   # Vue/other development
    "http://localhost:8000",   # FastAPI development
]

# En producción, también permitir el dominio de la API
if os.getenv("ENVIRONMENT") == "production":
    ALLOWED_ORIGINS.extend([
        "https://api.minetrack.site",
        "https://www.api.minetrack.site"
    ])

# Configuración completa de CORS
CORS_CONFIG = {
    "allow_origins": ALLOWED_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "allow_headers": ["*"],
    "expose_headers": ["*"],
}