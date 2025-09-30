#!/usr/bin/env python3
"""
Script para probar los nuevos endpoints de extracción de texto
"""

import requests
import json
import sys
from pathlib import Path

def test_extract_text_endpoint():
    """Prueba el endpoint /extract-text"""
    print("🧪 Probando endpoint /extract-text...")
    
    # Crear un ZIP de prueba simple (simulado)
    test_files = {'file': ('test_chat.zip', b'fake zip content', 'application/zip')}
    
    try:
        response = requests.post('http://localhost:8000/extract-text', files=test_files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funciona correctamente")
            print(f"  - Estructura de respuesta: {list(data.keys())}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API. ¿Está ejecutándose en localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def test_extract_text_plain_endpoint():
    """Prueba el endpoint /extract-text-plain"""
    print("🧪 Probando endpoint /extract-text-plain...")
    
    test_files = {'file': ('test_chat.zip', b'fake zip content', 'application/zip')}
    
    try:
        response = requests.post('http://localhost:8000/extract-text-plain', files=test_files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint funciona correctamente")
            print(f"  - Tiene campo 'text': {'text' in data}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def test_extract_text_raw_endpoint():
    """Prueba el endpoint /extract-text-raw"""
    print("🧪 Probando endpoint /extract-text-raw...")
    
    test_files = {'file': ('test_chat.zip', b'fake zip content', 'application/zip')}
    
    try:
        response = requests.post('http://localhost:8000/extract-text-raw', files=test_files)
        
        if response.status_code == 200:
            print("✅ Endpoint funciona correctamente")
            print(f"  - Content-Type: {response.headers.get('content-type', 'No especificado')}")
            print(f"  - Tamaño respuesta: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def test_root_endpoint():
    """Prueba el endpoint raíz para ver la información actualizada"""
    print("🧪 Probando endpoint raíz (/)...")
    
    try:
        response = requests.get('http://localhost:8000/')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint raíz actualizado correctamente")
            
            if 'endpoints' in data:
                print("  - Endpoints documentados:")
                for endpoint, description in data['endpoints'].items():
                    print(f"    • {endpoint}: {description}")
                return True
            else:
                print("  - ⚠️  Falta documentación de endpoints")
                return False
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def test_docs_endpoint():
    """Verifica que la documentación de Swagger esté disponible"""
    print("🧪 Verificando documentación de Swagger...")
    
    try:
        response = requests.get('http://localhost:8000/docs')
        
        if response.status_code == 200:
            print("✅ Documentación de Swagger disponible")
            print("  - URL: http://localhost:8000/docs")
            return True
        else:
            print(f"❌ Error {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print("🔍 Probando nuevos endpoints de extracción de texto...")
    print("=" * 60)
    
    tests = [
        test_root_endpoint,
        test_docs_endpoint,
        test_extract_text_endpoint,
        test_extract_text_plain_endpoint,
        test_extract_text_raw_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Línea en blanco entre pruebas
    
    print("=" * 60)
    print(f"📊 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los endpoints funcionan correctamente!")
        print("\nPróximos pasos:")
        print("1. Probar con un archivo ZIP real de WhatsApp")
        print("2. Verificar la extracción de texto en la interfaz Swagger")
        print("3. Probar la descarga de archivos de texto")
    else:
        print("⚠️  Algunos endpoints necesitan atención")
        print("\nRecomendaciones:")
        print("1. Verificar que la API esté ejecutándose: uvicorn main:app --reload")
        print("2. Revisar los logs de la aplicación para errores")
        print("3. Confirmar que todas las dependencias estén instaladas")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())