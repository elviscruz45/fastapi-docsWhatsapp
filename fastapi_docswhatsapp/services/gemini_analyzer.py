import google.generativeai as genai
from typing import Dict, Any, List
import json
import re
from datetime import datetime
import asyncio

from fastapi_docswhatsapp.models import ProjectAnalysis

class GeminiAnalyzer:
    """Clase para analizar chats de WhatsApp con Google Gemini y extraer información de proyectos"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        
    async def analyze_project_progress(self, chat_data: Dict[str, Any]) -> ProjectAnalysis:
        """
        Analiza el chat de WhatsApp para extraer información sobre avances del proyecto
        """
        # Preparar contexto del chat
        chat_context = self._prepare_chat_context(chat_data)
        
        # Prompt para análisis del proyecto
        system_instruction = """
        Eres un experto analista de proyectos. Tu tarea es analizar conversaciones de WhatsApp 
        de equipos de trabajo para extraer información valiosa sobre el progreso de proyectos.
        
        Debes identificar:
        1. Resumen general del proyecto y su estado actual
        2. Hitos y logros alcanzados
        3. Indicadores de progreso (porcentajes, fechas, entregas)
        4. Desafíos o problemas identificados
        5. Recomendaciones para mejorar el proyecto
        6. Análisis de timeline y fechas importantes
        7. Contribuciones de cada participante
        
        Responde siempre en formato JSON válido con la estructura especificada.
        """
        
        user_prompt = f"""
        Analiza la siguiente conversación de WhatsApp de un equipo de proyecto:
        
        INFORMACIÓN DEL CHAT:
        - Nombre del chat: {chat_data.get('chat_name', 'Sin nombre')}
        - Participantes: {', '.join(chat_data.get('participants', []))}
        - Período: {chat_data.get('date_range', {}).get('start', '')} hasta {chat_data.get('date_range', {}).get('end', '')}
        - Total de mensajes: {chat_data.get('total_messages', 0)}
        
        CONVERSACIÓN:
        {chat_context}
        
        Por favor, proporciona un análisis completo en formato JSON con esta estructura:
        {{
            "summary": "Resumen general del proyecto y estado actual",
            "key_milestones": ["hito1", "hito2", "hito3"],
            "progress_indicators": [
                {{
                    "indicator": "nombre del indicador",
                    "value": "valor o porcentaje",
                    "date": "fecha si aplica",
                    "description": "descripción del progreso"
                }}
            ],
            "challenges_identified": ["desafío1", "desafío2"],
            "recommendations": ["recomendación1", "recomendación2"],
            "timeline_analysis": {{
                "project_start": "fecha estimada de inicio",
                "current_phase": "fase actual del proyecto",
                "key_dates": ["fecha1: evento1", "fecha2: evento2"],
                "estimated_completion": "fecha estimada de finalización"
            }},
            "participant_contributions": {{
                "participante1": "resumen de contribuciones",
                "participante2": "resumen de contribuciones"
            }}
        }}
        """
        
        try:
            # Combinar instrucción del sistema con el prompt del usuario
            full_prompt = f"{system_instruction}\n\n{user_prompt}"
            
            # Generar respuesta con Gemini de forma asíncrona
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=4000,
                )
            )
            
            # Parsear respuesta JSON
            analysis_text = response.text
            analysis_data = json.loads(analysis_text)
            
            return ProjectAnalysis(**analysis_data)
            
        except json.JSONDecodeError as e:
            # Fallback si el JSON no es válido
            return self._create_fallback_analysis(chat_data, analysis_text)
        except Exception as e:
            # Análisis de emergencia
            return self._create_emergency_analysis(chat_data, str(e))
    
    def _prepare_chat_context(self, chat_data: Dict[str, Any]) -> str:
        """
        Prepara el contexto del chat para enviar a OpenAI
        """
        messages = chat_data.get('messages', [])
        
        # Limitar el número de mensajes para no exceder el límite de tokens
        max_messages = 200
        if len(messages) > max_messages:
            # Tomar los primeros y últimos mensajes para mantener contexto
            selected_messages = messages[:max_messages//2] + messages[-max_messages//2:]
        else:
            selected_messages = messages
        
        # Formatear mensajes
        formatted_messages = []
        for msg in selected_messages:
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            formatted_messages.append(f"[{timestamp}] {msg.sender}: {msg.content}")
        
        return "\n".join(formatted_messages)
    
    def _create_fallback_analysis(self, chat_data: Dict[str, Any], raw_response: str) -> ProjectAnalysis:
        """
        Crea un análisis básico cuando falla el parsing de JSON
        """
        return ProjectAnalysis(
            summary=f"Análisis del chat '{chat_data.get('chat_name', 'Sin nombre')}' con {chat_data.get('total_messages', 0)} mensajes entre {len(chat_data.get('participants', []))} participantes.",
            key_milestones=["Análisis automático realizado"],
            progress_indicators=[
                {
                    "indicator": "Mensajes procesados",
                    "value": str(chat_data.get('total_messages', 0)),
                    "date": datetime.now().isoformat(),
                    "description": "Total de mensajes analizados en el chat"
                }
            ],
            challenges_identified=["No se pudo procesar completamente el análisis de IA"],
            recommendations=["Revisar manualmente el contenido del chat", "Verificar la calidad de los datos"],
            timeline_analysis={
                "project_start": str(chat_data.get('date_range', {}).get('start', '')),
                "current_phase": "Análisis en proceso",
                "key_dates": [],
                "estimated_completion": "Pendiente de análisis manual"
            },
            participant_contributions={
                participant: f"Participante activo en el chat"
                for participant in chat_data.get('participants', [])
            }
        )
    
    def _create_emergency_analysis(self, chat_data: Dict[str, Any], error_msg: str) -> ProjectAnalysis:
        """
        Crea un análisis mínimo cuando falla completamente el análisis de IA
        """
        return ProjectAnalysis(
            summary=f"Chat procesado automáticamente. Error en análisis de IA: {error_msg}",
            key_milestones=["Procesamiento básico completado"],
            progress_indicators=[
                {
                    "indicator": "Estado del procesamiento",
                    "value": "Completado con errores",
                    "date": datetime.now().isoformat(),
                    "description": "El chat fue procesado pero el análisis de IA falló"
                }
            ],
            challenges_identified=["Error en el análisis automatizado"],
            recommendations=["Contactar al administrador del sistema", "Revisar configuración de OpenAI"],
            timeline_analysis={
                "project_start": "No determinado",
                "current_phase": "Error de análisis",
                "key_dates": [],
                "estimated_completion": "Requiere análisis manual"
            },
            participant_contributions={}
        )
    
    async def generate_summary(self, messages: List[Dict]) -> str:
        """
        Genera un resumen ejecutivo del chat
        """
        if not messages:
            return "No hay mensajes para analizar"
        
        # Tomar muestra representativa de mensajes
        sample_size = min(50, len(messages))
        sample_messages = messages[:sample_size]
        
        context = "\n".join([
            f"{msg.get('sender', 'Unknown')}: {msg.get('content', '')[:200]}"
            for msg in sample_messages
        ])
        
        prompt = f"""
        Genera un resumen ejecutivo breve (máximo 3 párrafos) de la siguiente conversación de proyecto:
        
        {context}
        
        El resumen debe incluir:
        - Tema principal del proyecto
        - Actividades o tareas principales discutidas
        - Estado general del progreso
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=1000,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            return f"Resumen del chat con {len(messages)} mensajes. Error en generación automática: {str(e)}"
    
    async def generate_project_report(self, chat_text: str) -> Dict[str, Any]:
        """
        Genera un informe de bitácora estructurado a partir del texto del chat de WhatsApp
        """
        system_instruction = """
        Eres un analista de proyectos experto que convierte conversaciones de WhatsApp 
        en informes de bitácora profesionales tipo informe final de proyecto.
        
        Tu tarea es analizar el chat y crear un informe estructurado que incluya:
        1. Título del proyecto (inferido del contexto)
        2. Resumen ejecutivo
        3. Objetivos identificados
        4. Actividades realizadas (cronológico)
        5. Resultados y logros
        6. Desafíos y obstáculos
        7. Lecciones aprendidas
        8. Conclusiones y recomendaciones
        
        Responde SIEMPRE en formato JSON válido.
        """
        
        user_prompt = f"""
        Analiza el siguiente chat de WhatsApp y transforma la información en un informe 
        de bitácora de proyecto profesional. 
        
        IMPORTANTE: Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin markdown, sin explicaciones.

        CHAT:
        {chat_text[:100000]}
        
        Devuelve EXACTAMENTE este formato JSON (sin ```json ni otros marcadores):
        {{
            "titulo_proyecto": "Nombre del proyecto basado en el contexto del chat",
            "resumen_ejecutivo": "Resumen detallado del proyecto de 2-3 párrafos basado en la conversación",
            "objetivos": ["Objetivo principal 1", "Objetivo principal 2", "Objetivo principal 3"],
            "actividades_realizadas": [
                {{
                    "fecha": "DD/MM/YYYY",
                    "descripcion": "Descripción detallada de la actividad realizada",
                    "responsable": "Nombre de la persona responsable"
                }}
            ],
            "resultados_logros": ["Logro específico 1", "Logro específico 2", "Logro específico 3"],
            "desafios_obstaculos": ["Desafío 1", "Desafío 2"],
            "lecciones_aprendidas": ["Lección importante 1", "Lección importante 2"],
            "conclusiones": "Conclusiones detalladas del proyecto basadas en la conversación",
            "recomendaciones": ["Recomendación práctica 1", "Recomendación práctica 2"]
        }}
        
        Asegúrate de que cada sección tenga contenido relevante extraído del chat."""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=40000,
                )
            )
            
            # Intentar parsear como JSON
            try:
                # Limpiar respuesta de markdown code blocks si los tiene
                response_text = response.text.strip()
                
                # Buscar JSON entre ```json y ``` o ```
                json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                json_match = re.search(json_pattern, response_text)
                
                if json_match:
                    json_text = json_match.group(1).strip()
                else:
                    json_text = response_text
                
                # Parsear JSON
                informe_data = json.loads(json_text)
                return informe_data
                
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw response: {response.text[:500]}...")
                
                # Si falla el JSON, crear estructura básica
                return {
                    "titulo_proyecto": "Informe de Proyecto WhatsApp",
                    "resumen_ejecutivo": "No se pudo procesar automáticamente el análisis del chat. Revise el contenido original.",
                    "objetivos": ["Analizar contenido del chat de WhatsApp"],
                    "actividades_realizadas": [],
                    "resultados_logros": [],
                    "desafios_obstaculos": [],
                    "lecciones_aprendidas": [],
                    "conclusiones": "Análisis requiere revisión manual",
                    "recomendaciones": ["Revisar el chat original para obtener más detalles"]
                }
            
        except Exception as e:
            # Fallback en caso de error
            return {
                "titulo_proyecto": "Informe de Proyecto",
                "resumen_ejecutivo": f"Error en el análisis automático: {str(e)}",
                "objetivos": [],
                "actividades_realizadas": [],
                "resultados_logros": [],
                "desafios_obstaculos": [],
                "lecciones_aprendidas": [],
                "conclusiones": "No se pudo completar el análisis",
                "recomendaciones": []
            }