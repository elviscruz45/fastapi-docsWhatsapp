# 📱 WhatsApp Bitácora Generator

API profesional para transformar chats de WhatsApp en informes de bitácora de proyectos usando **Gemini AI** y **WeasyPrint**.

🐳 **¡Ahora con soporte completo para Docker y deployment en DigitalOcean!**

## 🚀 Características

- **Procesamiento de chats de WhatsApp**: Extrae y analiza mensajes, imágenes y metadatos de archivos ZIP exportados
- **Análisis inteligente con Google Gemini**: Identifica hitos, desafíos, progreso y recomendaciones del proyecto
- **Reportes automáticos**: Genera PDFs profesionales y hojas de Excel con análisis detallado
- **Almacenamiento en Supabase**: Guarda extractos de avances y PDFs en la nube
- **API REST moderna**: Construida con FastAPI para fácil integración

## 📋 Requisitos

- Python 3.13+
- Cuenta de Google AI Studio con API Key de Gemini
- Proyecto de Supabase configurado
- Poetry (recomendado) o pip para gestión de dependencias

## � Instalación con Docker (Recomendado)

### Inicio Rápido

```bash
# 1. Clonar y configurar
git clone <tu-repositorio>
cd fastapi-docswhatsapp

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu GEMINI_API_KEY

# 3. Verificar configuración
./verify-setup.sh

# 4. Ejecutar en desarrollo
./deploy.sh dev
# O en producción
./deploy.sh prod
```

### Comandos Docker Disponibles

```bash
make help          # Ver todos los comandos
make setup         # Configuración inicial
make dev          # Modo desarrollo con hot reload
make prod         # Modo producción
make logs         # Ver logs
make health       # Verificar estado del servicio
make stop         # Detener servicios
```

📖 **Ver [DEPLOYMENT.md](DEPLOYMENT.md) para guía completa de deployment**

---

## 🛠️ Instalación Manual (Local)

1. **Clona el repositorio y configura**:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
# Google Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here

# Application Configuration
DEBUG=False
```

## 🤖 Configuración de Google Gemini

1. **Obtener API Key**:

   - Ve a [Google AI Studio](https://aistudio.google.com/)
   - Inicia sesión con tu cuenta de Google
   - Haz clic en "Get API Key"
   - Crea un nuevo proyecto si es necesario
   - Copia tu API Key y agrégala al archivo `.env`

2. **Modelos disponibles**:
   - `gemini-1.5-flash`: Modelo rápido y eficiente (recomendado)
   - `gemini-1.5-pro`: Modelo más potente para análisis complejos
   - `gemini-1.0-pro`: Modelo estándar

## 🗄️ Configuración de Supabase

1. **Crear tabla para extractos** (ejecutar en SQL Editor de Supabase):

```sql
CREATE TABLE project_extracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_name TEXT NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
    summary TEXT NOT NULL,
    milestones TEXT[] DEFAULT '{}',
    progress_percentage REAL DEFAULT 0.0,
    key_insights TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_project_extracts_chat_name ON project_extracts(chat_name);
CREATE INDEX idx_project_extracts_analysis_date ON project_extracts(analysis_date DESC);
```

2. **Crear bucket de Storage**:
   - Ve a Storage en tu dashboard de Supabase
   - Crea un nuevo bucket llamado `whatsapp-reports`
   - Marca como público para acceso directo a PDFs

## 🚀 Uso

### Ejecutar la API

```bash
# Con Poetry
poetry run uvicorn main:app --reload

# Con uvicorn directamente
uvicorn main:app --reload --port 8000
```

La API estará disponible en: `http://localhost:8000`

### Documentación automática

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints principales

#### `POST /process-chat`

Procesa un archivo ZIP de chat de WhatsApp y retorna un PDF con el análisis.

**Parámetros**:

- `file`: Archivo ZIP exportado desde WhatsApp (multipart/form-data)

**Respuesta**:

- PDF con reporte completo del análisis
- Headers adicionales con URL de Supabase y resumen

**Ejemplo usando curl**:

```bash
curl -X POST "http://localhost:8000/process-chat" \
     -H "accept: application/pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@chat_export.zip" \
     --output reporte.pdf
```

#### `GET /health`

Verifica el estado de la API.

## 📱 Cómo exportar un chat de WhatsApp

1. **En el teléfono**:

   - Abre el chat grupal que quieres analizar
   - Toca el nombre del grupo (Android) o la información del grupo (iOS)
   - Selecciona "Exportar chat"
   - Elige "Incluir archivos multimedia" para análisis completo
   - El archivo ZIP se guardará en tu dispositivo

2. **Formatos soportados**:
   - Archivos `.zip` únicamente
   - Tamaño máximo: 50MB
   - Incluye texto, imágenes y metadatos

## 📊 Qué analiza la API

La API utiliza Google Gemini para extraer automáticamente:

- **Resumen ejecutivo** del proyecto
- **Hitos clave** identificados en las conversaciones
- **Indicadores de progreso** con fechas y porcentajes
- **Desafíos identificados** y obstáculos
- **Recomendaciones** para mejorar el proyecto
- **Análisis de cronograma** con fechas importantes
- **Contribuciones por participante**

## 📋 Estructura de archivos generados

### PDF de reporte

- Información general del chat
- Resumen ejecutivo
- Hitos y progreso identificados
- Desafíos y recomendaciones
- Cronograma del proyecto
- Contribuciones por participante

### Excel de datos

- **Hoja "Resumen"**: Información general y resumen
- **Hoja "Mensajes"**: Todos los mensajes procesados
- **Hoja "Análisis Detallado"**: Hitos, desafíos y recomendaciones
- **Hoja "Cronograma"**: Fechas y timeline del proyecto

## 🔧 Desarrollo

### Estructura del proyecto

```
fastapi-docswhatsapp/
├── main.py                          # Archivo principal de FastAPI
├── pyproject.toml                   # Configuración de dependencias
├── .env.example                     # Ejemplo de variables de entorno
├── fastapi_docswhatsapp/
│   ├── __init__.py
│   ├── models/                      # Modelos de datos Pydantic
│   │   └── __init__.py
│   ├── services/                    # Lógica de negocio
│   │   ├── whatsapp_processor.py    # Procesamiento de ZIP
│   │   ├── gemini_analyzer.py       # Análisis con Gemini
│   │   ├── report_generator.py      # Generación de reportes
│   │   └── supabase_client.py       # Cliente de Supabase
│   ├── config/                      # Configuración
│   │   └── settings.py              # Variables de entorno
│   └── utils/                       # Utilidades generales
│       └── __init__.py
└── tests/                           # Tests unitarios
    └── __init__.py
```

### Ejecutar tests

```bash
poetry run pytest
```

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas:

1. **Revisa los logs** de la aplicación para errores específicos
2. **Verifica las variables de entorno** estén correctamente configuradas
3. **Confirma las credenciales** de Google Gemini y Supabase sean válidas
4. **Revisa el formato** del archivo ZIP de WhatsApp

### Errores comunes

- **Error 400**: El archivo no es un ZIP válido
- **Error 500**: Problema con Google Gemini (revisar API key) o Supabase (revisar configuración)
- **Memoria insuficiente**: El chat es muy grande, la API tiene límites de procesamiento

### Contacto

Para reportar bugs o sugerir mejoras, crea un issue en el repositorio del proyecto.

## 🎯 Roadmap

- [ ] Soporte para más idiomas de WhatsApp
- [ ] Análisis de sentimientos en las conversaciones
- [ ] Dashboard web para visualizar múltiples proyectos
- [ ] Integración con Slack y Telegram
- [ ] API para consultar historiales de proyectos
- [ ] Notificaciones automáticas de progreso
# fastapi-docsWhatsapp
