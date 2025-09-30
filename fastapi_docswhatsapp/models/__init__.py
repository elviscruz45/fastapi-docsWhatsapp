from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class WhatsAppMessage(BaseModel):
    """Modelo para un mensaje individual de WhatsApp"""
    timestamp: datetime
    sender: str
    content: str
    message_type: str  # 'text', 'image', 'document', 'audio', etc.
    media_path: Optional[str] = None
    
class ChatData(BaseModel):
    """Modelo para todos los datos del chat"""
    messages: List[WhatsAppMessage]
    participants: List[str]
    chat_name: str
    date_range: Dict[str, datetime]
    media_files: List[str]
    total_messages: int

class ProjectAnalysis(BaseModel):
    """Modelo para el análisis del proyecto por OpenAI"""
    summary: str
    key_milestones: List[str]
    progress_indicators: List[Dict[str, Any]]
    challenges_identified: List[str]
    recommendations: List[str]
    timeline_analysis: Dict[str, Any]
    participant_contributions: Dict[str, Any]
    
class ProjectExtract(BaseModel):
    """Modelo para extractos de avances guardados en Supabase"""
    id: Optional[str] = None
    chat_name: str
    analysis_date: datetime
    summary: str
    milestones: List[str]
    progress_percentage: float
    key_insights: List[str]
    created_at: Optional[datetime] = None