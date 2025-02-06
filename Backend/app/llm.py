#from fastembed import TextEmbedding #En caso de que acabemos haciendolo con esta librería que a mi no me funciona
from groq import Groq
from textwrap import dedent
from dotenv import load_dotenv
load_dotenv()


#Embbeder y RAG
class LLM:

    def __init__(self, api_key: str):
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
            self.temperature = 0
            self.respuesta = ''
    
    def _prompting(self,rag_response:str,amadeus_response:str,formulario:str):
          prompt = dedent(f"""
            Actúa como un experto asistente de viajes y guía turístico especializado en recomendaciones para viajes familiares. A continuación, te proporciono información clave:  

            1. **Recomendaciones previas basadas en el contexto:**  
            {rag_response}  

            2. **Información estructurada sobre vuelos, hoteles y lugares de interés:**  
            {amadeus_response}  

            3. **Información adicional con los detalles del viaje:**  
            {formulario}  

            Con base a estos datos:  

            - Haz recomendaciones personalizadas para familias, considerando comodidad, seguridad y actividades para todas las edades.  
            - Señala opciones destacadas de vuelos y hoteles adecuados para familias.  
            - Propón actividades que puedan disfrutar tanto adultos como niños.  
            - Menciona consejos prácticos para mejorar la experiencia de viaje, como mejor época para visitar o itinerarios optimizados.  
            - Recomendaciones sanitarias, restricciones y consejos sobre transporte, movilidad y seguridad en el país
            Responde de manera clara, directa y organizada para facilitar la planificación del viaje familiar.  
            """)
          return prompt
    
    def _llamada_llm(self,query_final):
        response = self.client.chat.completions.create(
                model=self.model, messages=query_final, temperature=self.temperature
            )
        return response.choices[0].message.content
          

