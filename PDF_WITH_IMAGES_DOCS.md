# PDF con Imágenes - Endpoint Documentation

## 📋 Descripción

El endpoint `/generate-chat-pdf-with-images` genera un PDF que incluye tanto el texto del chat de WhatsApp como las imágenes incrustadas directamente en el documento.

### ✨ Características principales:

- **Texto completo**: Incluye todos los mensajes del chat
- **Imágenes incrustadas**: Las referencias de archivos adjuntos se reemplazan por las imágenes reales
- **Formato ordenado**: Mantiene la cronología y formato del chat
- **Optimización automática**: Redimensiona imágenes para el PDF
- **PDF descargable**: Resultado listo para compartir o archivar

## 🔗 Endpoint

**URL:** `POST /generate-chat-pdf-with-images`

**Parámetros:**

- `file`: Archivo ZIP exportado de WhatsApp (multipart/form-data)

**Respuesta:** PDF descargable con chat e imágenes

## 📝 Formato de entrada esperado

### Estructura del ZIP de WhatsApp:

```
chat_export.zip
├── _chat.txt                           # Texto del chat
├── 00000016-PHOTO-2025-07-21-21-57-58.jpg
├── 00000027-PHOTO-2025-07-23-02-30-19.jpg
├── 00000043-PHOTO-2025-07-23-15-46-52.jpg
└── ... más archivos multimedia
```

### Formato del texto de chat:

```
[25/07/25, 3:36:30 PM] Alonzo Zavala: ‎<attached: 00000085-PHOTO-2025-07-25-15-36-30.jpg>
[25/07/25, 3:37:15 PM] María López: Excelente foto!
[25/07/25, 3:38:00 PM] Juan Pérez: <attached: 00000086-PHOTO-2025-07-25-15-38-00.jpg>
```

## 🛠️ Cómo usar

### Con curl:

```bash
curl -X POST "http://localhost:8000/generate-chat-pdf-with-images" \
     -H "accept: application/pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@chat_export.zip" \
     --output chat_con_imagenes.pdf
```

### Con Python:

```python
import requests

def generate_chat_pdf_with_images(zip_file_path):
    with open(zip_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            'http://localhost:8000/generate-chat-pdf-with-images',
            files=files
        )

        if response.status_code == 200:
            with open('chat_con_imagenes.pdf', 'wb') as pdf_file:
                pdf_file.write(response.content)
            print("PDF generado exitosamente!")
        else:
            print(f"Error: {response.text}")

# Uso
generate_chat_pdf_with_images('mi_chat.zip')
```

### Con Insomnia/Postman:

1. **Method:** POST
2. **URL:** `http://localhost:8000/generate-chat-pdf-with-images`
3. **Body:** Multipart Form
   - Field name: `file`
   - Type: File
   - Value: Seleccionar archivo ZIP de WhatsApp
4. **Send** → El PDF se descargará automáticamente

## 📊 Características del PDF generado

### Estructura del documento:

- **Título**: "Chat de WhatsApp con Imágenes"
- **Fecha de generación**: Timestamp automático
- **Mensajes ordenados cronológicamente**
- **Imágenes incrustadas en su posición correcta**
- **Formato legible y profesional**

### Procesamiento de imágenes:

- **Redimensionamiento automático**: Max 4" ancho × 3" alto
- **Mantiene proporción**: No distorsiona las imágenes
- **Optimización**: Compresión JPEG 85% para reducir tamaño
- **Compatibilidad**: Convierte formatos a RGB si es necesario

### Manejo de errores:

- **Imagen no encontrada**: Muestra "📷 Imagen no encontrada: filename.jpg"
- **Error de carga**: Muestra "❌ Error cargando imagen: filename.jpg"
- **Formato no soportado**: Ignora y continúa con el siguiente

## 🎯 Casos de uso

### Para individuos:

- **Archivo personal**: Guardar conversaciones importantes con fotos
- **Recuerdos**: Crear álbum de momentos especiales del chat grupal
- **Backup visual**: Respaldo completo con imágenes incluidas

### Para empresas:

- **Documentación de proyectos**: Evidencia visual de avances
- **Reportes**: Incluir capturas y fotos en documentos oficiales
- **Auditoría**: Registro completo de comunicaciones con imágenes

### Para equipos:

- **Memoria de reuniones**: Fotos de pizarras, esquemas, etc.
- **Seguimiento visual**: Progreso de trabajos con imágenes
- **Compartir contexto**: PDF completo para nuevos miembros

## ⚡ Rendimiento y limitaciones

### Archivos soportados:

- **Imágenes**: JPG, JPEG, PNG, GIF, BMP, WEBP
- **Tamaño máximo recomendado**: ZIP de hasta 100MB
- **Número de imágenes**: Sin límite teórico, pero afecta tiempo de procesamiento

### Tiempo de procesamiento:

- **Chat pequeño (< 10 imágenes)**: 5-15 segundos
- **Chat mediano (10-50 imágenes)**: 30-60 segundos
- **Chat grande (> 50 imágenes)**: 1-5 minutos

### Tamaño del PDF resultante:

- **Depende del número y tamaño de imágenes**
- **Típico**: 5-20MB para chats con 20-50 fotos
- **Optimización automática** reduce el tamaño final

## 🔧 Configuración avanzada

### Headers de respuesta útiles:

- `X-Total-Images`: Número de imágenes procesadas
- `Content-Description`: Descripción del archivo generado

### Personalización potencial (futuras versiones):

- Calidad de compresión de imágenes
- Tamaño máximo de imágenes en el PDF
- Filtros de fecha para el chat
- Selección de participantes específicos

## 🆘 Solución de problemas

### Error: "No se encontró archivo de chat"

- Verificar que el ZIP contiene un archivo `_chat.txt`
- Confirmar que es un export válido de WhatsApp

### Error: "Error generando PDF"

- Revisar que las imágenes no estén corruptas
- Verificar espacio en disco disponible
- Comprobar que el ZIP no esté dañado

### PDF muy grande:

- Reducir número de imágenes en el chat original
- Usar el endpoint `/process-chat` para análisis sin imágenes
- Dividir chats muy largos en períodos más pequeños

### Imágenes no aparecen:

- Verificar que los nombres de archivo coincidan exactamente
- Confirmar que las imágenes estén en formatos soportados
- Revisar que el ZIP incluya los archivos multimedia

## 📈 Ejemplo de salida

El PDF generado tendrá un formato similar a:

```
Chat de WhatsApp con Imágenes
Generado el: 21/09/2025 14:30

[25/07/25, 3:36:30 PM] Alonzo Zavala:
📷 Imagen: 00000085-PHOTO-2025-07-25-15-36-30.jpg
[IMAGEN INCRUSTADA AQUÍ]

[25/07/25, 3:37:15 PM] María López:
Excelente foto!

[25/07/25, 3:38:00 PM] Juan Pérez:
📷 Imagen: 00000086-PHOTO-2025-07-25-15-38-00.jpg
[IMAGEN INCRUSTADA AQUÍ]
```

¡Este endpoint te permite crear un archivo PDF completamente autónomo con todo el contexto visual del chat de WhatsApp!
