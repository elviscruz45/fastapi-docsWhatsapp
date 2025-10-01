from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Gemini
    gemini_api_key: str = Field(..., description="API Key de Google Gemini")
    gemini_model: str = Field(default="gemini-2.5-flash-lite", description="Modelo de Gemini a usar")
    
    # Supabase
    supabase_url: str = Field(..., description="URL de Supabase")
    supabase_key: str = Field(..., description="API Key de Supabase")
    supabase_storage_bucket: str = Field(default="whatsapp-reports", description="Bucket de Storage")
    
    # FastAPI
    app_name: str = Field(default="WhatsApp Chat Analyzer API", description="Nombre de la aplicación")
    app_version: str = Field(default="1.0.0", description="Versión de la aplicación")
    debug: bool = Field(default=False, description="Modo debug")
    
    # Configuración de archivos
    max_file_size: int = Field(default=50 * 1024 * 1024, description="Tamaño máximo de archivo (50MB)")
    allowed_extensions: list = Field(default=[".zip"], description="Extensiones permitidas")
    
    # Configuración de procesamiento
    max_messages_to_analyze: int = Field(default=1000, description="Máximo número de mensajes a analizar")
    max_analysis_tokens: int = Field(default=8000, description="Máximo de tokens para análisis de Gemini")
    
    # CORS
    # cors_origins: list = Field(default=["*"], description="Orígenes permitidos para CORS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración de la aplicación (cached)"""
    return Settings()