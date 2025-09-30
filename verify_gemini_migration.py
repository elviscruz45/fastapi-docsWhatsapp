#!/usr/bin/env python3
"""
Script para verificar que la migración a Gemini funciona correctamente
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    try:
        import google.generativeai as genai
        print("✅ google-generativeai instalado correctamente")
        return True
    except ImportError:
        print("❌ google-generativeai no está instalado")
        print("Ejecuta: pip install google-generativeai")
        return False

def check_env_vars():
    """Verificar variables de entorno"""
    gemini_key = os.getenv('GEMINI_API_KEY')
    gemini_model = os.getenv('GEMINI_MODEL')
    
    if not gemini_key or gemini_key == 'your_gemini_api_key_here':
        print("❌ GEMINI_API_KEY no está configurada correctamente")
        print("Configura tu API key en el archivo .env")
        return False
    
    print(f"✅ GEMINI_API_KEY configurada")
    print(f"✅ GEMINI_MODEL: {gemini_model}")
    return True

def test_gemini_connection():
    """Probar conexión con Gemini"""
    try:
        import google.generativeai as genai
        
        # Configurar Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Prueba simple
        response = model.generate_content("Responde solo con 'OK' si me puedes entender")
        print(f"✅ Conexión exitosa con Gemini")
        print(f"Respuesta de prueba: {response.text.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Gemini: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🔍 Verificando migración a Google Gemini...")
    print("-" * 50)
    
    all_good = True
    
    # Verificar dependencias
    if not check_dependencies():
        all_good = False
    
    print()
    
    # Verificar variables de entorno
    if not check_env_vars():
        all_good = False
    
    print()
    
    # Probar conexión (solo si las otras verificaciones pasaron)
    if all_good:
        if not test_gemini_connection():
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 ¡Migración completada exitosamente!")
        print("La API está lista para usar Google Gemini")
    else:
        print("❌ Hay problemas que necesitan resolverse")
        print("Revisa los errores anteriores")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())