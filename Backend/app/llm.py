#from fastembed import TextEmbedding #En caso de que acabemos haciendolo con esta librería que a mi no me funciona
from groq import Groq
from textwrap import dedent
from dotenv import load_dotenv
load_dotenv()


#Clase que se encarga de recopilar la información de RAG y Amadeus para luego enviarla a LLM y obtener una respuesta final.
class LLM:

    def __init__(self, api_key: str):
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
            self.temperature = 0
            self.respuesta = ''

    # Construye el prompt para LLM a partir de las respuestas de RAG y Amadeus.
    def _prompting(self, rag_response:str, amadeus_response:str, formulario:str):
          
          # Convertir rag_response en un string legible
          rag_text = "\n".join([f"- **{item['query']}**: {item['response']}" for item in rag_response])

          prompt = dedent(f"""
            Actúa como un experto asistente de viajes y guía turístico especializado en recomendaciones para viajes familiares. A continuación, te proporciono información clave:  

            1. **Recomendaciones previas basadas en el contexto:**  
            {rag_text}  

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
    
    # Función que se encarga de llamar a LLM con el prompt y obtener la respuesta final.
    def _llamada_llm(self,query_final, messages=[]):
        messages.append(
            {
                "role": "user",
                "content": query_final,
            }
        )
        response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=self.temperature
            )
        return response.choices[0].message.content
          

