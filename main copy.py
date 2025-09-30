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
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from PIL import Image
import io
from weasyprint import HTML, CSS
import base64

from fastapi_docswhatsapp.services.whatsapp_processor import WhatsAppProcessor
from fastapi_docswhatsapp.services.gemini_analyzer import GeminiAnalyzer
from fastapi_docswhatsapp.services.report_generator import ReportGenerator
from fastapi_docswhatsapp.services.supabase_client import SupabaseClient
from fastapi_docswhatsapp.config.settings import get_settings

app = FastAPI(
    title="WhatsApp Chat Analyzer API",
    description="API para procesar chats exportados de WhatsApp y generar reportes de avances de proyecto usando Google Gemini",
    version="1.0.0"
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
        "version": "1.0.0",
        "endpoints": {
            "process-chat": "Procesa ZIP completo y genera PDF con análisis de Gemini",
            "extract-text": "Extrae texto del ZIP con estadísticas detalladas (JSON)",
            "extract-text-plain": "Extrae solo el texto del ZIP (JSON simple)",
            "extract-text-raw": "Extrae texto como respuesta de texto plano (descargable)",
            "generate-chat-pdf-with-images": "Genera PDF del chat con imágenes incrustadas (descargable)",
            "generate-chat-pdf-with-images-preserved": "Genera PDF preservando formato original completo",
            "crear-informe-final": "Genera PDF final con HTML+CSS usando WeasyPrint (recomendado)"
        }
    }

@app.post("/process-chat", response_class=FileResponse)
async def process_chat(file: UploadFile = File(...)):
    """
    Procesa un archivo ZIP de chat exportado de WhatsApp y genera un reporte PDF.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    try:
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Guardar archivo ZIP subido
            zip_path = temp_path / file.filename
            content = await file.read()
            with open(zip_path, "wb") as f:
                f.write(content)
            
            # Procesar el chat de WhatsApp
            processor = WhatsAppProcessor()
            chat_data = processor.process_zip(zip_path)
            
            # Analizar con Gemini
            analyzer = GeminiAnalyzer(settings.gemini_api_key, settings.gemini_model)
            analysis = await analyzer.analyze_project_progress(chat_data)
            
            # Generar reporte
            report_generator = ReportGenerator()
            pdf_path, excel_path = await report_generator.generate_reports(
                chat_data, analysis, temp_path
            )
            
            # Subir a Supabase
            supabase_client = SupabaseClient(
                settings.supabase_url,
                settings.supabase_key
            )
            
            # Guardar extractos en Supabase
            await supabase_client.save_project_extracts(analysis)
            
            # Subir PDF a Supabase Storage
            pdf_url = await supabase_client.upload_pdf(pdf_path)
            
            # Retornar el PDF
            return FileResponse(
                pdf_path,
                media_type='application/pdf',
                filename=f"reporte_whatsapp_{file.filename.replace('.zip', '.pdf')}",
                headers={
                    "X-PDF-URL": pdf_url,
                    "X-Analysis-Summary": f"Procesados {len(chat_data.get('messages', []))} mensajes"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el chat: {str(e)}")

@app.post("/extract-text")
async def extract_text_from_zip(file: UploadFile = File(...)):
    """
    Extrae y retorna solo el texto plano del archivo de chat de WhatsApp desde un ZIP.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    try:
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Guardar archivo ZIP subido
            zip_path = temp_path / file.filename
            content = await file.read()
            with open(zip_path, "wb") as f:
                f.write(content)
            
            # Extraer y encontrar el archivo de texto del chat
            chat_text = extract_chat_text_from_zip(zip_path)
            
            if not chat_text:
                raise HTTPException(
                    status_code=400, 
                    detail="No se encontró archivo de chat de WhatsApp en el ZIP"
                )
            
            # Contar líneas y obtener estadísticas básicas
            lines = chat_text.split('\n')
            stats = get_basic_text_stats(chat_text)
            
            return {
                "filename": file.filename,
                "extraction_time": datetime.now().isoformat(),
                "stats": stats,
                "raw_text": chat_text,
                "preview": lines[:10] if len(lines) > 10 else lines  # Primeras 10 líneas como preview
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo texto: {str(e)}")

@app.post("/extract-text-plain")
async def extract_plain_text_only(file: UploadFile = File(...)):
    """
    Extrae solo el texto plano del chat de WhatsApp sin estadísticas ni metadatos.
    Útil para copiar/pegar o procesar externamente.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    try:
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Guardar archivo ZIP subido
            zip_path = temp_path / file.filename
            content = await file.read()
            with open(zip_path, "wb") as f:
                f.write(content)
            
            # Extraer texto del chat
            chat_text = extract_chat_text_from_zip(zip_path)
            
            if not chat_text:
                raise HTTPException(
                    status_code=400, 
                    detail="No se encontró archivo de chat de WhatsApp en el ZIP"
                )
            
            # Retornar solo el texto plano
            return {
                "text": chat_text
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo texto: {str(e)}")

@app.post("/extract-text-raw", response_class=PlainTextResponse)
async def extract_raw_text_response(file: UploadFile = File(...)):
    """
    Extrae el texto del chat y lo retorna como respuesta de texto plano.
    Ideal para descargar directamente como archivo .txt
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    try:
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Guardar archivo ZIP subido
            zip_path = temp_path / file.filename
            content = await file.read()
            with open(zip_path, "wb") as f:
                f.write(content)
            
            # Extraer texto del chat
            chat_text = extract_chat_text_from_zip(zip_path)
            
            if not chat_text:
                raise HTTPException(
                    status_code=400, 
                    detail="No se encontró archivo de chat de WhatsApp en el ZIP"
                )
            
            # Retornar texto plano con headers para descarga
            return PlainTextResponse(
                content=chat_text,
                headers={
                    "Content-Disposition": f"attachment; filename={file.filename.replace('.zip', '_chat.txt')}",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo texto: {str(e)}")

@app.post("/generate-chat-pdf-with-images", response_class=FileResponse)
async def generate_chat_pdf_with_images(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Genera un PDF con el texto del chat de WhatsApp incluyendo las imágenes incrustadas.
    Reemplaza las referencias de archivos adjuntos por las imágenes reales.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    # Crear archivo temporal para el PDF fuera del contexto del directorio temporal
    temp_pdf_fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_pdf_fd)  # Cerrar el file descriptor, solo necesitamos el path
    
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
            
            # Generar PDF con texto e imágenes en el archivo temporal persistente
            generate_pdf_with_images(chat_text, image_files, Path(temp_pdf_path), extract_path)
        
        # El directorio temporal se limpia aquí, pero el PDF persiste
        
        # Programar limpieza del archivo temporal después de la respuesta
        def cleanup_temp_file():
            try:
                os.unlink(temp_pdf_path)
            except OSError:
                pass  # El archivo ya fue eliminado o no existe
        
        background_tasks.add_task(cleanup_temp_file)
        
        # Retornar el PDF
        return FileResponse(
            temp_pdf_path,
            media_type='application/pdf',
            filename=f"chat_con_imagenes_{file.filename.replace('.zip', '.pdf')}",
            headers={
                "Content-Description": "Chat de WhatsApp con imágenes incrustadas",
                "X-Total-Images": str(len(image_files))
            }
        )
            
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error generando PDF con imágenes: {str(e)}")

@app.post("/generate-chat-pdf-with-images-preserved", response_class=FileResponse)
async def generate_chat_pdf_with_images_preserved(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Genera un PDF con el texto del chat de WhatsApp preservando el formato original completo
    e incluyendo las imágenes incrustadas sin eliminar el texto de referencia.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un ZIP")
    
    # Crear archivo temporal para el PDF fuera del contexto del directorio temporal
    temp_pdf_fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_pdf_fd)  # Cerrar el file descriptor, solo necesitamos el path
    
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
            
            # Generar PDF preservando formato original
            generate_pdf_with_images_preserved(chat_text, image_files, Path(temp_pdf_path), extract_path)
        
        # El directorio temporal se limpia aquí, pero el PDF persiste
        
        # Programar limpieza del archivo temporal después de la respuesta
        def cleanup_temp_file():
            try:
                os.unlink(temp_pdf_path)
            except OSError:
                pass  # El archivo ya fue eliminado o no existe
        
        background_tasks.add_task(cleanup_temp_file)
        
        # Retornar el PDF
        return FileResponse(
            temp_pdf_path,
            media_type='application/pdf',
            filename=f"chat_preservado_{file.filename.replace('.zip', '.pdf')}",
            headers={
                "Content-Description": "Chat de WhatsApp con formato original preservado e imágenes incrustadas",
                "X-Total-Images": str(len(image_files))
            }
        )
            
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error generando PDF preservado con imágenes: {str(e)}")

@app.post("/crear-informe-final", response_class=FileResponse)
async def crear_informe_final(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Genera un PDF combinando texto del chat e imágenes usando WeasyPrint.
    Crea un HTML con el chat en orden cronológico e imágenes insertadas.
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
            
            # Generar HTML del chat con imágenes
            html_content = generate_chat_html(chat_text, image_files)
            
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
            filename=f"informe_final_{file.filename.replace('.zip', '.pdf')}",
            headers={
                "Content-Description": "Informe final del chat de WhatsApp con imágenes integradas",
                "X-Total-Images": str(len(image_files))
            }
        )
    
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error generando informe final: {str(e)}")

def generate_chat_html(chat_text: str, image_files: Dict[str, Path]) -> str:
    """
    Genera HTML con el chat y las imágenes insertadas en orden cronológico.
    """
    # CSS para el estilo del PDF
    css_style = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 20px;
            color: #333;
        }
        .chat-header {
            text-align: center;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            border-radius: 5px;
        }
        .sender-info {
            font-weight: bold;
            color: #2980b9;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .message-content {
            margin: 5px 0;
        }
        .chat-image {
            max-width: 300px;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .image-not-found {
            color: #e74c3c;
            font-style: italic;
            background-color: #fdf2f2;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #f5c6cb;
        }
        .generation-info {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.8em;
            margin-top: 30px;
            border-top: 1px solid #ecf0f1;
            padding-top: 10px;
        }
    </style>
    """
    
    # Iniciar HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="utf-8">',
        '<title>Informe Final - Chat WhatsApp</title>',
        css_style,
        '</head>',
        '<body>',
        '<div class="chat-header">',
        '<h1>📱 Informe Final - Chat de WhatsApp</h1>',
        f'<p>Generado el: {datetime.now().strftime("%d/%m/%Y a las %H:%M")}</p>',
        '</div>'
    ]
    
    # Procesar líneas del chat
    lines = chat_text.split('\n')
    
    # Patrones para mensajes de WhatsApp
    patterns = [
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}:\d{2})\s+(AM|PM)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s+(AM|PM)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}:\d{2})\s+([ap]\.?\s*m\.?)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s+([ap]\.?\s*m\.?)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
    ]
    
    # Patrones para archivos adjuntos
    attachment_patterns = [
        re.compile(r'<attached:\s+([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),
        re.compile(r'<attached:([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),
        re.compile(r'‎<attached:\s+([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),
        re.compile(r'‎<attached:([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),
    ]
    
    for line_num, line in enumerate(lines, 1):
        #line = line.strip()
        line = line.strip().lstrip('\u200e')

        if not line:
            continue
        
        # Intentar hacer match con patrones de mensaje
        match = None
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                break
        
        if match:
            groups = match.groups()
            if len(groups) >= 5:
                date_str, time_str, am_pm, sender, content = groups[:5]
            else:
                date_str, time_str, am_pm, sender, content = groups
            
            # Normalizar formato de tiempo
            full_time = f"{time_str} {am_pm.upper()}"
            
            # Escapar HTML en el contenido
            safe_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe_sender = sender.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Iniciar div del mensaje
            html_parts.append('<div class="message">')
            html_parts.append(f'<div class="sender-info">[{date_str}, {full_time}] {safe_sender}:</div>')
            html_parts.append(f'<div class="message-content">{safe_content}</div>')
            
            # Buscar archivos adjuntos
            attachment_match = None
            for att_pattern in attachment_patterns:
                attachment_match = att_pattern.search(content)
                if attachment_match:
                    break
            
            if attachment_match:
                image_filename = attachment_match.group(1)
                
                # Intentar encontrar y convertir la imagen a base64
                if image_filename in image_files:
                    try:
                        img_path = image_files[image_filename]
                        
                        # Convertir imagen a base64 para insertar en HTML
                        with open(img_path, 'rb') as img_file:
                            img_data = img_file.read()
                            img_base64 = base64.b64encode(img_data).decode('utf-8')
                            
                        # Determinar tipo MIME
                        img_ext = img_path.suffix.lower()
                        mime_type = {
                            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                            '.png': 'image/png', '.gif': 'image/gif',
                            '.bmp': 'image/bmp', '.webp': 'image/webp'
                        }.get(img_ext, 'image/jpeg')
                        
                        # Insertar imagen en HTML
                        html_parts.append(
                            f'<img src="data:{mime_type};base64,{img_base64}" '
                            f'alt="{image_filename}" class="chat-image">'
                        )
                    
                    except Exception as e:
                        html_parts.append(
                            f'<div class="image-not-found">❌ Error cargando imagen: {image_filename}</div>'
                        )
                else:
                    html_parts.append(
                        f'<div class="image-not-found">📷 Imagen no encontrada: {image_filename}</div>'
                    )
            
            html_parts.append('</div>')  # Cerrar div del mensaje
        
        else:
            # Líneas que no son mensajes
            if line and not line.startswith('‎'):
                safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<p style="color: #7f8c8d; font-size: 0.9em;">{safe_line}</p>')
    
    # Cerrar HTML
    html_parts.extend([
        '<div class="generation-info">',
        f'<p>📊 Total de imágenes procesadas: {len(image_files)}</p>',
        '<p>Generado con FastAPI + WeasyPrint</p>',
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

def generate_pdf_with_images(chat_text: str, image_files: Dict[str, Path], 
                           output_path: Path, extract_path: Path):
    """
    Genera un PDF con el texto del chat incluyendo las imágenes incrustadas
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, 
                          topMargin=0.5*inch, bottomMargin=0.5*inch,
                          leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    message_style = ParagraphStyle(
        'MessageStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=10,
        alignment=TA_LEFT
    )
    
    sender_style = ParagraphStyle(
        'SenderStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.blue,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Título del PDF
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=20,
        alignment=TA_LEFT
    )
    
    story.append(Paragraph("Chat de WhatsApp con Imágenes", title_style))
    story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Procesar líneas del chat
    lines = chat_text.split('\n')
    
    # Patrón para mensajes de WhatsApp
    message_pattern = re.compile(
        r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*(?:a\.\s*m\.|p\.\s*m\.|AM|PM)?\s*\]\s*([^:]+):\s*(.*)'
    )
    
    # Patrón para archivos adjuntos (formato WhatsApp)
    attachment_pattern = re.compile(
        r'<attached:\s*([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>|‎<attached:\s*([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE
    )
    
    for line in lines:
        # line = line.strip()
        line = line.strip().lstrip('\u200e')

        if not line:
            continue
        
        # Verificar si es un mensaje válido
        match = message_pattern.match(line)
        if match:
            date_str, time_str, sender, content = match.groups()
            
            # Agregar información del remitente y fecha
            sender_info = f"[{date_str}, {time_str}] {sender}:"
            story.append(Paragraph(sender_info, sender_style))
            
            # Verificar si el contenido contiene una imagen adjunta
            attachment_match = attachment_pattern.search(content)
            
            if attachment_match:
                # El patrón tiene múltiples grupos, buscar el que no sea None
                image_filename = attachment_match.group(1) or attachment_match.group(3)
                
                # Buscar la imagen en los archivos extraídos
                if image_filename in image_files:
                    try:
                        # Procesar y agregar la imagen
                        img_path = image_files[image_filename]
                        processed_image = process_image_for_pdf(img_path)
                        
                        if processed_image:
                            story.append(processed_image)
                            story.append(Spacer(1, 10))
                        
                        # Agregar texto indicando que se incluyó la imagen
                        story.append(Paragraph(f"📷 Imagen: {image_filename}", message_style))
                        
                    except Exception as e:
                        # Si hay error con la imagen, mostrar texto alternativo
                        story.append(Paragraph(f"❌ Error cargando imagen: {image_filename}", message_style))
                else:
                    # Si no se encuentra la imagen
                    story.append(Paragraph(f"📷 Imagen no encontrada: {image_filename}", message_style))
                
                # Remover la referencia del texto original y agregar contenido restante
                clean_content = attachment_pattern.sub('', content).strip()
                if clean_content:
                    story.append(Paragraph(clean_content, message_style))
            else:
                # Mensaje de texto normal
                story.append(Paragraph(content, message_style))
            
            story.append(Spacer(1, 8))
        else:
            # Líneas que no son mensajes (metadatos, etc.)
            if line and not line.startswith('‎'):  # Ignorar caracteres especiales de WhatsApp
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 4))
    
    # Construir PDF
    doc.build(story)

def process_image_for_pdf(image_path: Path) -> ReportLabImage:
    """
    Procesa una imagen para incluirla en el PDF, redimensionándola si es necesario
    """
    try:
        # Abrir imagen con PIL
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calcular nuevas dimensiones manteniendo aspecto
            max_width = 4 * inch  # Ancho máximo en el PDF
            max_height = 3 * inch  # Alto máximo en el PDF
            
            width, height = img.size
            
            # Calcular ratio de redimensionamiento
            width_ratio = max_width / width
            height_ratio = max_height / height
            ratio = min(width_ratio, height_ratio, 1.0)  # No agrandar imágenes pequeñas
            
            new_width = width * ratio
            new_height = height * ratio
            
            # Redimensionar imagen si es necesario
            if ratio < 1.0:
                img = img.resize((int(new_width / ratio * ratio), int(new_height / ratio * ratio)), Image.Resampling.LANCZOS)
            
            # Guardar imagen procesada en memoria
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            # Crear imagen para ReportLab
            return ReportLabImage(img_buffer, width=new_width, height=new_height)
            
    except Exception as e:
        print(f"Error procesando imagen {image_path}: {str(e)}")
        return None

def generate_pdf_with_images_preserved(chat_text: str, image_files: Dict[str, Path], 
                                     output_path: Path, extract_path: Path):
    """
    Genera un PDF con el texto del chat preservando el formato original completo
    e incluyendo las imágenes incrustadas SIN eliminar el texto de referencia.
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, 
                          topMargin=0.5*inch, bottomMargin=0.5*inch,
                          leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    message_style = ParagraphStyle(
        'MessageStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        wordWrap='LTR'
    )
    
    sender_style = ParagraphStyle(
        'SenderStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.blue,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=20,
        alignment=TA_LEFT
    )
    
    story = []
    story.append(Paragraph("Chat de WhatsApp con Formato Preservado", title_style))
    story.append(Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Procesar líneas del chat
    lines = chat_text.split('\n')
    
    # Debug: Add info about image files found
    print(f"DEBUG: Found {len(image_files)} image files: {list(image_files.keys())}")
    
    # Multiple patterns to match different WhatsApp formats
    patterns = [
        # Format: [30/07/25, 7:04:01 PM] Elvis: <attached: image.jpg>
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}:\d{2})\s+(AM|PM)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
        # Format: [30/07/25, 7:04 PM] Elvis: <attached: image.jpg>  
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s+(AM|PM)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
        # Format: [dd/mm/yy, h:mm:ss a.m./p.m.] User: message
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}:\d{2})\s+([ap]\.?\s*m\.?)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
        # Format: [dd/mm/yy, h:mm a.m./p.m.] User: message
        re.compile(r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s+([ap]\.?\s*m\.?)\]\s+([^:]+):\s*(.*)', re.IGNORECASE),
    ]
    
    # Pattern for attachments - matches your exact format: <attached: filename.jpg>
    attachment_patterns = [
        re.compile(r'<attached:\s+([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),  # With space after colon
        re.compile(r'<attached:([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),     # Without space after colon  
        re.compile(r'‎<attached:\s+([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE), # With special char and space
        re.compile(r'‎<attached:([^>]+\.(jpg|jpeg|png|gif|bmp|webp))>', re.IGNORECASE),    # With special char, no space
    ]
    
    for line_num, line in enumerate(lines, 1):
        # line = line.strip()
        line = line.strip().lstrip('\u200e')

        if not line:
            continue
        
        # Try to match message patterns
        match = None
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                break
        
        if match:
            groups = match.groups()
            if len(groups) >= 5:
                date_str, time_str, am_pm, sender, content = groups[:5]
            else:
                date_str, time_str, am_pm, sender, content = groups
            
            # Normalize time format
            full_time = f"{time_str} {am_pm.upper()}"
            
            # Add sender info 
            sender_info = f"[{date_str}, {full_time}] {sender}:"
            story.append(Paragraph(sender_info, sender_style))
            
            # STEP 1: Show original message content FIRST (preserving ALL text including <attached:...>)
            story.append(Paragraph(content, message_style))
            print(f"DEBUG: Line {line_num} - Added original text: {content[:100]}...")
            
            # STEP 2: Look for attachment references to ADD image (without removing text)
            attachment_match = None
            for i, att_pattern in enumerate(attachment_patterns):
                attachment_match = att_pattern.search(content)
                if attachment_match:
                    print(f"DEBUG: Line {line_num} - Pattern {i+1} matched attachment")
                    break
            
            if attachment_match:
                image_filename = attachment_match.group(1)
                print(f"DEBUG: Line {line_num} - Found attachment: '{image_filename}'")
                
                # Try to find and add the image
                if image_filename in image_files:
                    try:
                        img_path = image_files[image_filename]
                        print(f"DEBUG: Processing image: {img_path}")
                        processed_image = process_image_for_pdf(img_path)
                        
                        if processed_image:
                            story.append(Spacer(1, 5))
                            story.append(processed_image)
                            story.append(Spacer(1, 5))
                            print(f"DEBUG: Successfully added image: {image_filename}")
                        else:
                            story.append(Paragraph(f"❌ Error processing image: {image_filename}", message_style))
                        
                    except Exception as e:
                        print(f"DEBUG: Error with image {image_filename}: {str(e)}")
                        story.append(Paragraph(f"❌ Error loading image: {str(e)}", message_style))
                else:
                    print(f"DEBUG: Image not found in files: {image_filename}")
                    # Show available files for debugging
                    similar_files = [f for f in image_files.keys() if image_filename.split('.')[0].lower() in f.lower()]
                    if similar_files:
                        print(f"DEBUG: Similar files found: {similar_files}")
                    story.append(Paragraph(f"📷 Image not found: {image_filename}", message_style))
            
            story.append(Spacer(1, 8))
        else:
            # Non-message lines
            if line and not line.startswith('‎'):
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 4))
    
    # Build PDF
    doc.build(story)

def extract_chat_text_from_zip(zip_path: Path) -> str:
    """
    Extrae el contenido de texto del chat desde un archivo ZIP de WhatsApp
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Buscar archivo de chat (usualmente _chat.txt)
        chat_file = None
        
        for file_info in zip_ref.filelist:
            filename = file_info.filename.lower()
            if filename.endswith('.txt') and ('chat' in filename or 'whatsapp' in filename):
                chat_file = file_info.filename
                break
        
        # Si no encuentra archivo específico, buscar el TXT más grande
        if not chat_file:
            txt_files = [f for f in zip_ref.filelist if f.filename.endswith('.txt')]
            if txt_files:
                chat_file = max(txt_files, key=lambda f: f.file_size).filename
        
        if not chat_file:
            return ""
        
        # Leer contenido del archivo
        try:
            with zip_ref.open(chat_file) as f:
                content = f.read()
                # Intentar decodificar con UTF-8 primero
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    # Si falla, intentar con latin-1
                    return content.decode('latin-1')
        except Exception:
            return ""

def get_basic_text_stats(text: str) -> Dict[str, Any]:
    """
    Obtiene estadísticas básicas del texto del chat
    """
    lines = text.split('\n')
    
    # Patrón para mensajes de WhatsApp
    message_pattern = re.compile(
        r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*(?:a\.\s*m\.|p\.\s*m\.)?\s*-\s*([^:]+):\s*(.*)'
    )
    
    total_lines = len(lines)
    message_lines = 0
    participants = set()
    
    for line in lines:
        match = message_pattern.match(line.strip())
        if match:
            message_lines += 1
            sender = match.group(3).strip()
            participants.add(sender)
    
    return {
        "total_lines": total_lines,
        "message_lines": message_lines,
        "non_message_lines": total_lines - message_lines,
        "total_participants": len(participants),
        "participants": list(participants),
        "total_characters": len(text),
        "total_words": len(text.split()) if text else 0,
        "file_size_kb": round(len(text.encode('utf-8')) / 1024, 2)
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "whatsapp-analyzer"}