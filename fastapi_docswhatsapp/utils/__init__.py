"""
Utilidades generales para la aplicación
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
import uuid
import shutil

def create_temp_directory() -> Path:
    """Crea un directorio temporal único"""
    temp_dir = Path(tempfile.gettempdir()) / f"whatsapp_analysis_{uuid.uuid4()}"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

def cleanup_temp_directory(temp_dir: Path) -> bool:
    """Limpia un directorio temporal"""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        print(f"Error limpiando directorio temporal: {e}")
        return False

def validate_file_size(file_size: int, max_size: int = 50 * 1024 * 1024) -> bool:
    """Valida el tamaño de un archivo"""
    return file_size <= max_size

def sanitize_filename(filename: str) -> str:
    """Sanitiza un nombre de archivo"""
    # Remover caracteres especiales y espacios
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    sanitized = "".join(c for c in filename if c in safe_chars)
    return sanitized or "archivo_sin_nombre"

def format_file_size(size_bytes: int) -> str:
    """Formatea el tamaño de archivo en formato legible"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"