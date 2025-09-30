#!/usr/bin/env python3
"""
Script para probar el endpoint de generación de PDF con imágenes
"""

import requests
import sys
from pathlib import Path

def test_pdf_with_images_endpoint(zip_file_path=None):
    """
    Prueba el endpoint /generate-chat-pdf-with-images
    """
    print("🧪 Probando endpoint /generate-chat-pdf-with-images...")
    
    if not zip_file_path:
        print("❌ Necesitas proporcionar la ruta del archivo ZIP de WhatsApp")
        print("Uso: python test_pdf_images.py <ruta_del_zip>")
        return False
    
    zip_path = Path(zip_file_path)
    if not zip_path.exists():
        print(f"❌ El archivo {zip_file_path} no existe")
        return False
    
    try:
        with open(zip_path, 'rb') as f:
            files = {'file': (zip_path.name, f, 'application/zip')}
            
            print(f"📤 Subiendo archivo: {zip_path.name}")
            print("⏳ Generando PDF con imágenes... (esto puede tomar un momento)")
            
            response = requests.post(
                'http://localhost:8000/generate-chat-pdf-with-images', 
                files=files,
                timeout=300  # 5 minutos de timeout para archivos grandes
            )
            
            if response.status_code == 200:
                # Guardar el PDF generado
                output_filename = f"chat_con_imagenes_{zip_path.stem}.pdf"
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                print("✅ PDF generado exitosamente!")
                print(f"📄 Archivo guardado como: {output_filename}")
                
                # Mostrar información de headers
                if 'X-Total-Images' in response.headers:
                    print(f"🖼️  Total de imágenes procesadas: {response.headers['X-Total-Images']}")
                
                print(f"📊 Tamaño del PDF: {len(response.content) / 1024:.1f} KB")
                return True
                
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a la API. ¿Está ejecutándose en localhost:8000?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout: El procesamiento tomó demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def analyze_zip_content(zip_file_path):
    """
    Analiza el contenido del ZIP para mostrar información útil
    """
    import zipfile
    
    print(f"\n🔍 Analizando contenido de {zip_file_path}...")
    
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            files = zip_ref.filelist
            
            txt_files = [f for f in files if f.filename.endswith('.txt')]
            image_files = [f for f in files if any(f.filename.lower().endswith(ext) 
                          for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])]
            other_files = [f for f in files if f not in txt_files and f not in image_files]
            
            print(f"📄 Archivos de texto: {len(txt_files)}")
            for txt_file in txt_files:
                print(f"   - {txt_file.filename}")
            
            print(f"🖼️  Archivos de imagen: {len(image_files)}")
            if len(image_files) <= 10:
                for img_file in image_files:
                    print(f"   - {img_file.filename}")
            else:
                for img_file in image_files[:5]:
                    print(f"   - {img_file.filename}")
                print(f"   ... y {len(image_files) - 5} más")
            
            print(f"📁 Otros archivos: {len(other_files)}")
            
            return len(txt_files) > 0 and len(image_files) > 0
            
    except Exception as e:
        print(f"❌ Error analizando ZIP: {str(e)}")
        return False

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("🔍 Probador del endpoint de generación de PDF con imágenes")
        print("=" * 60)
        print("Uso: python test_pdf_images.py <archivo_whatsapp.zip>")
        print("\nEjemplo:")
        print("python test_pdf_images.py chat_export.zip")
        print("\nEste script:")
        print("1. Analiza el contenido del ZIP")
        print("2. Envía el archivo al endpoint")
        print("3. Guarda el PDF generado")
        return 1
    
    zip_file_path = sys.argv[1]
    
    print("🔍 Probador del endpoint de generación de PDF con imágenes")
    print("=" * 60)
    
    # Analizar contenido del ZIP
    if analyze_zip_content(zip_file_path):
        print("✅ El ZIP contiene archivos de texto e imágenes")
    else:
        print("⚠️  El ZIP podría no tener el formato esperado")
    
    print()
    
    # Probar el endpoint
    success = test_pdf_with_images_endpoint(zip_file_path)
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 ¡Prueba completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Abrir el PDF generado para verificar las imágenes")
        print("2. Revisar que el formato del texto sea correcto")
        print("3. Confirmar que las imágenes se muestren correctamente")
    else:
        print("❌ La prueba falló")
        print("\nRecomendaciones:")
        print("1. Verificar que la API esté ejecutándose")
        print("2. Confirmar que el ZIP sea un export válido de WhatsApp")
        print("3. Revisar los logs de la aplicación para errores detallados")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())