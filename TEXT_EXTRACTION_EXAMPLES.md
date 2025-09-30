# Ejemplos de uso de los nuevos endpoints de extracción de texto

## Endpoints disponibles para extracción de texto

### 1. `/extract-text` - Texto con estadísticas completas

Extrae el texto del chat y proporciona estadísticas detalladas.

**Ejemplo de uso:**

```bash
curl -X POST "http://localhost:8000/extract-text" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@chat_export.zip"
```

**Respuesta esperada:**

```json
{
  "filename": "chat_export.zip",
  "extraction_time": "2025-09-20T15:30:45.123456",
  "stats": {
    "total_lines": 1250,
    "message_lines": 1100,
    "non_message_lines": 150,
    "total_participants": 5,
    "participants": ["Juan", "María", "Carlos", "Ana", "Luis"],
    "total_characters": 125000,
    "total_words": 18500,
    "file_size_kb": 122.5
  },
  "raw_text": "Contenido completo del chat...",
  "preview": [
    "12/09/2024, 10:15 - Juan: Hola equipo",
    "12/09/2024, 10:16 - María: Buenos días",
    "..."
  ]
}
```

### 2. `/extract-text-plain` - Solo texto simple

Extrae únicamente el texto del chat sin estadísticas adicionales.

**Ejemplo de uso:**

```bash
curl -X POST "http://localhost:8000/extract-text-plain" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@chat_export.zip"
```

**Respuesta esperada:**

```json
{
  "text": "Contenido completo del chat de WhatsApp..."
}
```

### 3. `/extract-text-raw` - Descarga como archivo de texto

Retorna el texto como respuesta de texto plano, ideal para descargar como archivo .txt.

**Ejemplo de uso:**

```bash
curl -X POST "http://localhost:8000/extract-text-raw" \
     -H "accept: text/plain" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@chat_export.zip" \
     --output chat_extraido.txt
```

**Respuesta:** Archivo de texto plano descargable

## Casos de uso

### Para desarrolladores

- **Debugging**: Usar `/extract-text` para ver estadísticas y verificar el formato
- **Procesamiento**: Usar `/extract-text-plain` para obtener solo el texto y procesarlo
- **Backup**: Usar `/extract-text-raw` para guardar una copia limpia del texto

### Para usuarios finales

- **Visualización rápida**: Usar `/extract-text` para ver preview y estadísticas
- **Descarga**: Usar `/extract-text-raw` para descargar el texto como archivo

## Validaciones incluidas

- ✅ Verifica que el archivo sea un ZIP
- ✅ Busca automáticamente el archivo de chat dentro del ZIP
- ✅ Maneja diferentes codificaciones (UTF-8, Latin-1)
- ✅ Proporciona mensajes de error descriptivos
- ✅ Limpia archivos temporales automáticamente

## Estadísticas que calcula `/extract-text`

- **total_lines**: Total de líneas en el archivo
- **message_lines**: Líneas que contienen mensajes válidos de WhatsApp
- **non_message_lines**: Líneas de metadatos, espacios vacíos, etc.
- **total_participants**: Número de participantes únicos
- **participants**: Lista de nombres de participantes
- **total_characters**: Número total de caracteres
- **total_words**: Número total de palabras
- **file_size_kb**: Tamaño del texto en KB

## Integración con JavaScript

```javascript
async function extractText(zipFile) {
  const formData = new FormData();
  formData.append("file", zipFile);

  const response = await fetch("/extract-text", {
    method: "POST",
    body: formData,
  });

  if (response.ok) {
    const data = await response.json();
    console.log("Estadísticas:", data.stats);
    console.log("Preview:", data.preview);
    return data.raw_text;
  } else {
    throw new Error("Error extrayendo texto");
  }
}
```

## Integración con Python

```python
import requests

def extract_whatsapp_text(zip_file_path):
    with open(zip_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:8000/extract-text', files=files)

    if response.status_code == 200:
        data = response.json()
        return data['raw_text'], data['stats']
    else:
        raise Exception(f"Error: {response.json()['detail']}")

# Uso
text, stats = extract_whatsapp_text('mi_chat.zip')
print(f"Chat con {stats['total_participants']} participantes")
print(f"Total de mensajes: {stats['message_lines']}")
```
