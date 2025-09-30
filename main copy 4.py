from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import zipfile
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple


from weasyprint import HTML, CSS
import base64
import re 
from fastapi_docswhatsapp.services.whatsapp_processor import WhatsAppProcessor
from fastapi_docswhatsapp.services.gemini_analyzer import GeminiAnalyzer
from fastapi_docswhatsapp.services.report_generator import ReportGenerator
from fastapi_docswhatsapp.services.supabase_client import SupabaseClient
from fastapi_docswhatsapp.config.settings import get_settings

app = FastAPI(
    title="WhatsApp Bitácora Generator",
    description="Genera informes de bitácora profesionales desde chats de WhatsApp usando Gemini AI y WeasyPrint",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

@app.get("/")
async def root():
    return {
        "message": "WhatsApp Chat Analyzer API", 
        "version": "2.0.0",
        "description": "Genera informes de bitácora profesionales desde chats de WhatsApp usando IA",
        "endpoint": {
            "crear-informe-final": "POST - Genera informe de bitácora profesional usando Gemini AI + WeasyPrint"
        },
        "usage": "Sube un archivo ZIP de WhatsApp exportado para generar un informe profesional"
    }



@app.post("/crear-informe-final", response_class=FileResponse)
async def crear_informe_final(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Genera un informe de bitácora profesional transformando el chat de WhatsApp usando Gemini AI.
    Convierte las conversaciones en un documento estructurado tipo informe final de proyecto.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    # Crear archivo temporal para el PDF
    temp_pdf_fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_pdf_fd)
    
    try:
        # Crear directorio temporal para procesamiento
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Guardar archivo ZIP subido
            zip_path = temp_path / file.filename
            content = await file.read()
            with open(zip_path, "wb") as f:
                f.write(content)
            
            # Extraer todos los archivos del ZIP
            extract_path = temp_path / "extracted"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Obtener texto del chat e imágenes
            chat_text, image_files = extract_chat_and_images(extract_path)
            
            if not chat_text:
                raise HTTPException(
                    status_code=400,
                    detail="No se encontró archivo de chat de WhatsApp en el ZIP"
                )
            
            print(f"Generando informe de bitácora con {len(image_files)} imágenes...")
            
            # Analizar el chat con Gemini para crear informe de bitácora
            analyzer = GeminiAnalyzer(settings.gemini_api_key, settings.gemini_model)
            informe_data = await analyzer.generate_project_report(chat_text)
            
            # Generar HTML del informe con imágenes
            html_content = generate_informe_html(informe_data, chat_text, image_files)
            
            # Convertir HTML a PDF usando WeasyPrint
            HTML(string=html_content).write_pdf(temp_pdf_path)
        
        # Programar limpieza del archivo temporal
        def cleanup_temp_file():
            try:
                os.unlink(temp_pdf_path)
            except OSError:
                pass
        
        background_tasks.add_task(cleanup_temp_file)
        
        # Retornar el PDF
        return FileResponse(
            temp_pdf_path,
            media_type='application/pdf',
            filename=f"bitacora_proyecto_{file.filename.replace('.zip', '.pdf')}",
            headers={
                "Content-Description": "Informe de bitácora del proyecto generado por Gemini AI",
                "X-Total-Images": str(len(image_files)),
                "X-AI-Processed": "true"
            }
        )
    
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error generando informe de bitácora: {str(e)}")

def generate_informe_html(informe_data: Dict[str, Any], chat_text: str, image_files: Dict[str, Path]) -> str:
    """
    Genera HTML del informe de bitácora profesional con imágenes integradas.
    """
    # CSS para el estilo profesional del informe
    css_style = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.8;
            margin: 0;
            padding: 40px;
            color: #2c3e50;
            background-color: #fff;
        }
        .report-header {
            text-align: center;
            margin-bottom: 50px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 30px;
        }
        .report-title {
            color: #2c3e50;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .report-subtitle {
            color: #7f8c8d;
            font-size: 16px;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 40px;
            page-break-inside: avoid;
        }
        .section-title {
            color: #2980b9;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            background-color: #f8f9fa;
            padding: 10px 15px;
        }
        .section-content {
            margin-left: 20px;
            text-align: justify;
        }
        .activity-item {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .activity-date {
            color: #3498db;
            font-weight: bold;
            font-size: 14px;
        }
        .activity-description {
            margin: 8px 0;
        }
        .activity-responsible {
            color: #7f8c8d;
            font-style: italic;
            font-size: 14px;
        }
        .list-item {
            background-color: #fff;
            border-left: 3px solid #27ae60;
            padding: 10px 15px;
            margin-bottom: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .report-image {
            max-width: 400px;
            height: auto;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            margin: 20px auto;
            display: block;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .image-caption {
            text-align: center;
            font-style: italic;
            color: #7f8c8d;
            margin-top: 10px;
            font-size: 14px;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }
        ul {
            padding-left: 0;
        }
        li {
            list-style: none;
        }
        @page {
            margin: 2cm;
        }
    </style>
    """
    
    # Función auxiliar para escapar HTML
    def escape_html(text):
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Función para insertar imágenes del chat en el informe
    def insert_images_from_chat():
        images_html = []
        # Buscar imágenes en el chat original y añadirlas como evidencia
        lines = chat_text.split('\n')
        attachment_patterns = [
            re.compile(r'<attached:\s*([^>]+\.(jpg|jpeg|png|gif|bmp))>', re.IGNORECASE),
            re.compile(r'‎<attached:\s*([^>]+\.(jpg|jpeg|png|gif|bmp))>', re.IGNORECASE),
        ]
        
        for line in lines:
            line = line.strip().lstrip('\u200e')
            for pattern in attachment_patterns:
                match = pattern.search(line)
                if match:
                    image_filename = match.group(1)
                    if image_filename in image_files:
                        try:
                            img_path = image_files[image_filename]
                            with open(img_path, 'rb') as img_file:
                                img_data = img_file.read()
                                img_base64 = base64.b64encode(img_data).decode('utf-8')
                            
                            img_ext = img_path.suffix.lower()
                            mime_type = {
                                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                                '.png': 'image/png', '.gif': 'image/gif',
                                '.bmp': 'image/bmp'
                            }.get(img_ext, 'image/jpeg')
                            
                            images_html.append(f'''
                                <img src="data:{mime_type};base64,{img_base64}" 
                                     alt="{image_filename}" class="report-image">
                                <div class="image-caption">Figura: {image_filename}</div>
                            ''')
                        except Exception:
                            pass
        
        return '\n'.join(images_html)
    
    # Iniciar HTML del informe
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="es">',
        '<head>',
        '<meta charset="utf-8">',
        f'<title>{informe_data.get("titulo_proyecto", "Informe de Bitácora")}</title>',
        css_style,
        '</head>',
        '<body>',
        
        # Header del informe
        '<div class="report-header">',
        f'<h1 class="report-title">📋 {escape_html(informe_data.get("titulo_proyecto", "Informe de Bitácora del Proyecto"))}</h1>',
        f'<div class="report-subtitle">Generado automáticamente el {datetime.now().strftime("%d de %B de %Y")}</div>',
        f'<div class="report-subtitle">Análisis realizado por Inteligencia Artificial</div>',
        '</div>',
        
        # Resumen Ejecutivo
        '<div class="section">',
        '<h2 class="section-title">📊 Resumen Ejecutivo</h2>',
        '<div class="section-content">',
        f'<p>{escape_html(informe_data.get("resumen_ejecutivo", "No disponible"))}</p>',
        '</div>',
        '</div>'
    ]
    
    # Objetivos
    if informe_data.get("objetivos"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">🎯 Objetivos del Proyecto</h2>',
            '<div class="section-content">',
            '<ul>'
        ])
        for objetivo in informe_data["objetivos"]:
            html_parts.append(f'<li class="list-item">• {escape_html(objetivo)}</li>')
        html_parts.extend(['</ul>', '</div>', '</div>'])
    
    # Actividades Realizadas
    if informe_data.get("actividades_realizadas"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">⚡ Actividades Realizadas</h2>',
            '<div class="section-content">'
        ])
        for actividad in informe_data["actividades_realizadas"]:
            if isinstance(actividad, dict):
                html_parts.append(f'''
                    <div class="activity-item">
                        <div class="activity-date">📅 {escape_html(actividad.get("fecha", "Sin fecha"))}</div>
                        <div class="activity-description">{escape_html(actividad.get("descripcion", "Sin descripción"))}</div>
                        <div class="activity-responsible">👤 Responsable: {escape_html(actividad.get("responsable", "No especificado"))}</div>
                    </div>
                ''')
            else:
                html_parts.append(f'<div class="activity-item"><div class="activity-description">{escape_html(str(actividad))}</div></div>')
        html_parts.extend(['</div>', '</div>'])
    
    # Resultados y Logros
    if informe_data.get("resultados_logros"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">🏆 Resultados y Logros</h2>',
            '<div class="section-content">',
            '<ul>'
        ])
        for resultado in informe_data["resultados_logros"]:
            html_parts.append(f'<li class="list-item">✅ {escape_html(resultado)}</li>')
        html_parts.extend(['</ul>', '</div>', '</div>'])
    
    # Evidencias Fotográficas (si hay imágenes)
    if image_files:
        images_html = insert_images_from_chat()
        if images_html:
            html_parts.extend([
                '<div class="section">',
                '<h2 class="section-title">📸 Evidencias Fotográficas</h2>',
                '<div class="section-content">',
                images_html,
                '</div>',
                '</div>'
            ])
    
    # Desafíos y Obstáculos
    if informe_data.get("desafios_obstaculos"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">⚠️ Desafíos y Obstáculos</h2>',
            '<div class="section-content">',
            '<ul>'
        ])
        for desafio in informe_data["desafios_obstaculos"]:
            html_parts.append(f'<li class="list-item">⚡ {escape_html(desafio)}</li>')
        html_parts.extend(['</ul>', '</div>', '</div>'])
    
    # Lecciones Aprendidas
    if informe_data.get("lecciones_aprendidas"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">💡 Lecciones Aprendidas</h2>',
            '<div class="section-content">',
            '<ul>'
        ])
        for leccion in informe_data["lecciones_aprendidas"]:
            html_parts.append(f'<li class="list-item">📚 {escape_html(leccion)}</li>')
        html_parts.extend(['</ul>', '</div>', '</div>'])
    
    # Conclusiones
    if informe_data.get("conclusiones"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">📋 Conclusiones</h2>',
            '<div class="section-content">',
            f'<p>{escape_html(informe_data["conclusiones"])}</p>',
            '</div>',
            '</div>'
        ])
    
    # Recomendaciones
    if informe_data.get("recomendaciones"):
        html_parts.extend([
            '<div class="section">',
            '<h2 class="section-title">💼 Recomendaciones</h2>',
            '<div class="section-content">',
            '<ul>'
        ])
        for recomendacion in informe_data["recomendaciones"]:
            html_parts.append(f'<li class="list-item">➡️ {escape_html(recomendacion)}</li>')
        html_parts.extend(['</ul>', '</div>', '</div>'])
    
    # Footer
    html_parts.extend([
        '<div class="footer">',
        f'<p>📊 Total de imágenes procesadas: {len(image_files)}</p>',
        '<p>🤖 Informe generado automáticamente con Inteligencia Artificial (Gemini) + FastAPI + WeasyPrint</p>',
        f'<p>Fecha de generación: {datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")}</p>',
        '</div>',
        '</body>',
        '</html>'
    ])
    
    return '\n'.join(html_parts)

def extract_chat_and_images(extract_path: Path) -> Tuple[str, Dict[str, Path]]:
    """
    Extrae el texto del chat y mapea las imágenes disponibles
    """
    # Buscar archivo de chat
    chat_text = ""
    chat_file = None
    
    for file_path in extract_path.rglob('*.txt'):
        if '_chat.txt' in file_path.name.lower() or 'whatsapp' in file_path.name.lower():
            chat_file = file_path
            break
    
    # Si no encuentra archivo específico, buscar el TXT más grande
    if not chat_file:
        txt_files = list(extract_path.rglob('*.txt'))
        if txt_files:
            chat_file = max(txt_files, key=lambda f: f.stat().st_size)
    
    if chat_file:
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                chat_text = f.read()
        except UnicodeDecodeError:
            with open(chat_file, 'r', encoding='latin-1') as f:
                chat_text = f.read()
    
    # Mapear imágenes disponibles
    image_files = {}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    for file_path in extract_path.rglob('*'):
        if file_path.suffix.lower() in image_extensions:
            image_files[file_path.name] = file_path
    
    return chat_text, image_files









@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "whatsapp-analyzer"}