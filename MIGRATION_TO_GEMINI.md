# Migración a Google Gemini

Este documento explica los cambios realizados para migrar de OpenAI a Google Gemini.

## ✅ Cambios realizados

### 1. Dependencias actualizadas

- ❌ Removido: `openai>=1.12.0`
- ✅ Agregado: `google-generativeai>=0.3.0`

### 2. Configuración actualizada

En `fastapi_docswhatsapp/config/settings.py`:

- ❌ Removido: `openai_api_key`, `openai_model`
- ✅ Agregado: `gemini_api_key`, `gemini_model`

### 3. Archivo renombrado

- ❌ `openai_analyzer.py` → ✅ `gemini_analyzer.py`

### 4. Clase actualizada

- ❌ `OpenAIAnalyzer` → ✅ `GeminiAnalyzer`

### 5. Variables de entorno actualizadas

En `.env` y `.env.example`:

```env
# Antes (OpenAI)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Ahora (Gemini)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash
```

## 🔧 Configuración requerida

### 1. Instalar nuevas dependencias

```bash
poetry install
# o
pip install google-generativeai>=0.3.0
```

### 2. Obtener API Key de Google Gemini

1. Ve a [Google AI Studio](https://aistudio.google.com/)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Get API Key"
4. Crea un nuevo proyecto si es necesario
5. Copia tu API Key

### 3. Actualizar archivo .env

```env
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
GEMINI_MODEL=gemini-1.5-flash
```

## 🚀 Ventajas de usar Gemini

- **Mayor límite de tokens**: 8000 tokens vs 4000 de OpenAI
- **Mejor análisis multimodal**: Procesamiento mejorado de imágenes
- **Costo menor**: Más económico que GPT-4
- **Integración nativa con Google**: Mejor ecosistema
- **Respuestas más largas**: Permite análisis más detallados

## 📊 Diferencias técnicas

### Implementación anterior (OpenAI)

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=api_key)
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    temperature=0.7,
    max_tokens=3000
)
```

### Implementación actual (Gemini)

```python
import google.generativeai as genai

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")
response = await asyncio.to_thread(
    model.generate_content,
    prompt,
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=4000,
    )
)
```

## 🔍 Validación

Para verificar que la migración funciona correctamente:

1. **Ejecutar la API**:

```bash
uvicorn main:app --reload
```

2. **Probar endpoint**:

```bash
curl -X GET "http://localhost:8000/health"
```

3. **Verificar documentación**:

- Abrir: `http://localhost:8000/docs`
- Confirmar que aparece "Google Gemini" en la descripción

## ⚠️ Notas importantes

- **Formato de respuesta**: Gemini puede generar respuestas ligeramente diferentes a OpenAI
- **Rate limits**: Google Gemini tiene límites diferentes de velocidad
- **Compatibilidad**: El formato JSON de salida se mantiene igual
- **Fallback**: Se mantiene el sistema de análisis de emergencia si falla la IA

## 🆘 Solución de problemas

### Error: "Import google.generativeai could not be resolved"

```bash
pip install google-generativeai
```

### Error: "API key not valid"

1. Verificar que la API key es correcta
2. Confirmar que el proyecto de Google AI Studio está habilitado
3. Revisar que no hay espacios extra en el archivo .env

### Error: "Model not found"

Verificar que el modelo especificado existe:

- `gemini-1.5-flash` (recomendado)
- `gemini-1.5-pro`
- `gemini-1.0-pro`
