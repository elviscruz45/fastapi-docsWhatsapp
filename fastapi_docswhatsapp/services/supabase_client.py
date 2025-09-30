from supabase import create_client, Client
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import aiofiles
import os

from fastapi_docswhatsapp.models import ProjectAnalysis, ProjectExtract

class SupabaseClient:
    """Cliente para interactuar con Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
        self.storage_bucket = "whatsapp-reports"
        self.extracts_table = "project_extracts"
    
    async def save_project_extracts(self, analysis: ProjectAnalysis) -> str:
        """
        Guarda los extractos del análisis del proyecto en Supabase
        """
        try:
            # Crear extracto del proyecto
            extract = ProjectExtract(
                id=str(uuid.uuid4()),
                chat_name=analysis.timeline_analysis.get('project_start', 'Proyecto WhatsApp'),
                analysis_date=datetime.now(),
                summary=analysis.summary,
                milestones=analysis.key_milestones,
                progress_percentage=self._calculate_progress_percentage(analysis),
                key_insights=analysis.recommendations[:5],  # Limitar a 5 insights principales
                created_at=datetime.now()
            )
            
            # Convertir a diccionario para Supabase
            extract_data = {
                "id": extract.id,
                "chat_name": extract.chat_name,
                "analysis_date": extract.analysis_date.isoformat(),
                "summary": extract.summary,
                "milestones": extract.milestones,
                "progress_percentage": extract.progress_percentage,
                "key_insights": extract.key_insights,
                "created_at": extract.created_at.isoformat()
            }
            
            # Insertar en Supabase
            result = self.client.table(self.extracts_table).insert(extract_data).execute()
            
            if result.data:
                return result.data[0]["id"]
            else:
                raise Exception("No se pudo insertar el extracto en Supabase")
                
        except Exception as e:
            # Log del error y retornar ID temporal
            print(f"Error guardando extractos en Supabase: {str(e)}")
            return "error_" + str(uuid.uuid4())
    
    async def upload_pdf(self, pdf_path: Path) -> str:
        """
        Sube el PDF generado a Supabase Storage
        """
        try:
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_{timestamp}_{pdf_path.name}"
            
            # Leer archivo PDF
            async with aiofiles.open(pdf_path, 'rb') as f:
                pdf_content = await f.read()
            
            # Subir a Supabase Storage
            result = self.client.storage.from_(self.storage_bucket).upload(
                filename,
                pdf_content,
                file_options={"content-type": "application/pdf"}
            )
            
            if result:
                # Generar URL pública
                url_result = self.client.storage.from_(self.storage_bucket).get_public_url(filename)
                return url_result
            else:
                raise Exception("Error subiendo PDF a Supabase Storage")
                
        except Exception as e:
            print(f"Error subiendo PDF a Supabase: {str(e)}")
            return f"error_upload_{pdf_path.name}"
    
    async def get_project_history(self, chat_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de análisis de un proyecto específico
        """
        try:
            result = self.client.table(self.extracts_table).select("*").eq("chat_name", chat_name).order("created_at", desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error obteniendo historial del proyecto: {str(e)}")
            return []
    
    async def get_all_projects_summary(self) -> List[Dict[str, Any]]:
        """
        Obtiene un resumen de todos los proyectos analizados
        """
        try:
            result = self.client.table(self.extracts_table).select(
                "chat_name, analysis_date, progress_percentage, summary"
            ).order("analysis_date", desc=True).limit(50).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error obteniendo resumen de proyectos: {str(e)}")
            return []
    
    async def update_project_progress(self, project_id: str, new_progress: float, 
                                     new_insights: List[str]) -> bool:
        """
        Actualiza el progreso de un proyecto existente
        """
        try:
            update_data = {
                "progress_percentage": new_progress,
                "key_insights": new_insights,
                "analysis_date": datetime.now().isoformat()
            }
            
            result = self.client.table(self.extracts_table).update(update_data).eq("id", project_id).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            print(f"Error actualizando progreso del proyecto: {str(e)}")
            return False
    
    async def delete_old_extracts(self, days_old: int = 90) -> int:
        """
        Elimina extractos antiguos para mantener la base de datos limpia
        """
        try:
            cutoff_date = datetime.now().replace(day=1)  # Simplificado para ejemplo
            cutoff_date_str = cutoff_date.isoformat()
            
            result = self.client.table(self.extracts_table).delete().lt("created_at", cutoff_date_str).execute()
            
            return len(result.data) if result.data else 0
            
        except Exception as e:
            print(f"Error eliminando extractos antiguos: {str(e)}")
            return 0
    
    def _calculate_progress_percentage(self, analysis: ProjectAnalysis) -> float:
        """
        Calcula un porcentaje de progreso basado en el análisis
        """
        try:
            # Algoritmo simple para calcular progreso
            base_progress = 0.0
            
            # Puntos por hitos completados
            if analysis.key_milestones:
                milestone_points = min(len(analysis.key_milestones) * 15, 60)
                base_progress += milestone_points
            
            # Puntos por indicadores de progreso
            if analysis.progress_indicators:
                indicator_points = min(len(analysis.progress_indicators) * 10, 30)
                base_progress += indicator_points
            
            # Restar puntos por desafíos
            if analysis.challenges_identified:
                challenge_penalty = min(len(analysis.challenges_identified) * 5, 20)
                base_progress -= challenge_penalty
            
            # Asegurar que esté entre 0 y 100
            return max(0.0, min(100.0, base_progress))
            
        except Exception as e:
            print(f"Error calculando porcentaje de progreso: {str(e)}")
            return 0.0
    
    async def setup_database_schema(self) -> bool:
        """
        Configura el schema de la base de datos (ejecutar una vez)
        """
        try:
            # Esta función debería ejecutarse manualmente en Supabase SQL Editor
            # o mediante migraciones. Aquí está el SQL de referencia:
            
            sql_commands = [
                """
                CREATE TABLE IF NOT EXISTS project_extracts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chat_name TEXT NOT NULL,
                    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    summary TEXT NOT NULL,
                    milestones TEXT[] DEFAULT '{}',
                    progress_percentage REAL DEFAULT 0.0,
                    key_insights TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_project_extracts_chat_name 
                ON project_extracts(chat_name);
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_project_extracts_analysis_date 
                ON project_extracts(analysis_date DESC);
                """
            ]
            
            print("Para configurar la base de datos, ejecuta estos comandos SQL en Supabase:")
            for i, sql in enumerate(sql_commands, 1):
                print(f"\n-- Comando {i}:")
                print(sql)
            
            return True
            
        except Exception as e:
            print(f"Error configurando schema de base de datos: {str(e)}")
            return False
    
    async def create_storage_bucket(self) -> bool:
        """
        Crea el bucket de storage para PDFs (ejecutar una vez)
        """
        try:
            # Crear bucket si no existe
            buckets = self.client.storage.list_buckets()
            
            bucket_exists = any(bucket.name == self.storage_bucket for bucket in buckets)
            
            if not bucket_exists:
                result = self.client.storage.create_bucket(
                    self.storage_bucket,
                    options={"public": True}
                )
                print(f"Bucket '{self.storage_bucket}' creado exitosamente")
                return True
            else:
                print(f"Bucket '{self.storage_bucket}' ya existe")
                return True
                
        except Exception as e:
            print(f"Error creando bucket de storage: {str(e)}")
            return False