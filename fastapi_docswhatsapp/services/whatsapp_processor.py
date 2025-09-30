import zipfile
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os
from PIL import Image

from fastapi_docswhatsapp.models import WhatsAppMessage, ChatData

class WhatsAppProcessor:
    """Clase para procesar archivos ZIP exportados de WhatsApp"""
    
    def __init__(self):
        # Patrón para mensajes de WhatsApp en español
        self.message_pattern = re.compile(
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*(?:a\.\s*m\.|p\.\s*m\.)?\s*-\s*([^:]+):\s*(.*)'
        )
        
        # Patrones para detectar tipos de mensajes especiales
        self.media_patterns = {
            'image': re.compile(r'<se omitió multimedia>|<Media omitted>|\(archivo adjunto\)'),
            'document': re.compile(r'documento|document|archivo|file'),
            'audio': re.compile(r'audio|voice note|nota de voz'),
            'video': re.compile(r'video|vídeo'),
            'location': re.compile(r'ubicación compartida|location shared')
        }
    
    def process_zip(self, zip_path: Path) -> Dict[str, Any]:
        """
        Procesa el archivo ZIP del chat de WhatsApp
        """
        chat_data = {
            'messages': [],
            'participants': set(),
            'media_files': [],
            'chat_name': '',
            'date_range': {'start': None, 'end': None}
        }
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extraer contenido a directorio temporal
            extract_path = zip_path.parent / 'extracted'
            zip_ref.extractall(extract_path)
            
            # Buscar archivo de chat (usualmente _chat.txt)
            chat_file = self._find_chat_file(extract_path)
            if chat_file:
                chat_data['chat_name'] = chat_file.stem.replace('_chat', '')
                messages = self._parse_chat_file(chat_file)
                chat_data['messages'] = messages
                
                # Extraer participantes únicos
                chat_data['participants'] = list(set(msg.sender for msg in messages))
                
                # Determinar rango de fechas
                if messages:
                    chat_data['date_range']['start'] = min(msg.timestamp for msg in messages)
                    chat_data['date_range']['end'] = max(msg.timestamp for msg in messages)
            
            # Procesar archivos multimedia
            media_files = self._process_media_files(extract_path)
            chat_data['media_files'] = media_files
        
        chat_data['total_messages'] = len(chat_data['messages'])
        
        return chat_data
    
    def _find_chat_file(self, extract_path: Path) -> Path:
        """Busca el archivo principal del chat"""
        for file in extract_path.rglob('*.txt'):
            if '_chat' in file.name.lower() or 'whatsapp' in file.name.lower():
                return file
        
        # Si no encuentra archivo específico, busca el TXT más grande
        txt_files = list(extract_path.rglob('*.txt'))
        if txt_files:
            return max(txt_files, key=lambda f: f.stat().st_size)
        
        return None
    
    def _parse_chat_file(self, chat_file: Path) -> List[WhatsAppMessage]:
        """Parsea el archivo de texto del chat"""
        messages = []
        
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Intentar con otra codificación
            with open(chat_file, 'r', encoding='latin-1') as f:
                content = f.read()
        
        lines = content.split('\n')
        current_message = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Verificar si es una nueva línea de mensaje
            match = self.message_pattern.match(line)
            if match:
                # Guardar mensaje anterior si existe
                if current_message:
                    messages.append(current_message)
                
                # Crear nuevo mensaje
                date_str, time_str, sender, content = match.groups()
                
                # Parsear fecha y hora
                timestamp = self._parse_datetime(date_str, time_str)
                
                # Determinar tipo de mensaje
                message_type = self._determine_message_type(content)
                
                current_message = WhatsAppMessage(
                    timestamp=timestamp,
                    sender=sender.strip(),
                    content=content.strip(),
                    message_type=message_type
                )
            else:
                # Continuar mensaje anterior (mensaje multilínea)
                if current_message:
                    current_message.content += f"\n{line}"
        
        # Agregar último mensaje
        if current_message:
            messages.append(current_message)
        
        return messages
    
    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """Parsea fecha y hora de WhatsApp"""
        # Limpiar y normalizar formato de fecha
        date_str = date_str.replace(',', '').strip()
        time_str = time_str.strip()
        
        # Formatos comunes de fecha de WhatsApp
        date_formats = [
            '%d/%m/%Y',
            '%d/%m/%y', 
            '%m/%d/%Y',
            '%m/%d/%y'
        ]
        
        # Formatos de hora
        time_formats = [
            '%H:%M',
            '%I:%M'
        ]
        
        parsed_date = None
        for date_fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_fmt).date()
                break
            except ValueError:
                continue
        
        if not parsed_date:
            # Fecha por defecto si no se puede parsear
            parsed_date = datetime.now().date()
        
        parsed_time = None
        for time_fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, time_fmt).time()
                break
            except ValueError:
                continue
        
        if not parsed_time:
            # Hora por defecto
            parsed_time = datetime.now().time()
        
        return datetime.combine(parsed_date, parsed_time)
    
    def _determine_message_type(self, content: str) -> str:
        """Determina el tipo de mensaje basado en el contenido"""
        content_lower = content.lower()
        
        for msg_type, pattern in self.media_patterns.items():
            if pattern.search(content_lower):
                return msg_type
        
        return 'text'
    
    def _process_media_files(self, extract_path: Path) -> List[str]:
        """Procesa archivos multimedia del chat"""
        media_files = []
        
        # Extensiones de archivos multimedia comunes
        media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                          '.mp4', '.avi', '.mov', '.mp3', '.wav', '.ogg',
                          '.pdf', '.doc', '.docx', '.txt'}
        
        for file_path in extract_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                media_files.append(str(file_path))
                
                # Si es imagen, verificar que se puede abrir
                if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
                    try:
                        with Image.open(file_path) as img:
                            # Validar que la imagen es válida
                            img.verify()
                    except Exception:
                        # Remover archivos corruptos
                        media_files.pop()
        
        return media_files