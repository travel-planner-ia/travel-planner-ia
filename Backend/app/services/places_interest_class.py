import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage
from pydantic import BaseModel
from dotenv import load_dotenv
from get_places_interest import AmadeusAPI  # Asegúrate de importar la nueva clase

# Cargar variables de entorno
load_dotenv()

# Configuración de Groq LLM
groq_api_key = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

# Clase para manejar el estado del grafo
class GraphState(BaseModel):
    messages: list
    number_interactions: int = 0
    verbose: bool = True

# Clase principal para manejar la búsqueda y análisis de lugares de interés
class PlacesInterest:
    def __init__(self, input_data):
        self.model = ChatGroq(temperature=0, model_name=MODEL, api_key=groq_api_key)
        self.graph = StateGraph(GraphState)
        self.graph.add_node("agent", self.call_model)
        self.graph.add_edge(START, "agent")
        self.graph.add_edge("agent", END)
        self.agent = self.graph.compile()
        self.input_data = input_data
        self.amadeus_api = AmadeusAPI()

    def call_model(self, state):
        if state.verbose:
            print("---- Llamando al modelo ----")
        state.number_interactions += 1
        state.messages = self.model.invoke(state.messages)
        return state

    def run(self):
        latitude, longitude = self.input_data["latitude"], self.input_data["longitude"]
        places_info = self.get_places_info(latitude, longitude)
        
        if not places_info:
            return "No se encontraron lugares de interés en la ubicación especificada."

        messages = [
            SystemMessage(content=f"""Eres un asistente de viajes. Analiza los siguientes lugares de interés y proporciona un resumen 
                              y recomendaciones según el tipo de viajero.\n{places_info}""")
        ]

        resp = self.agent.invoke({"messages": messages, "verbose": False})

        return resp['messages'].content

    def get_places_info(self, latitude, longitude, radius=1):
        """Obtiene los lugares de interés y formatea la respuesta"""
        try:
            activities = self.amadeus_api.get_activities(latitude, longitude, radius)
            
            # Formatear la información de las actividades
            places_info = f"Aquí están las actividades disponibles en la ubicación ({latitude}, {longitude}):\n\n"

            activity_list = activities.get("data", [])
            if not activity_list:
                places_info += "No se encontraron actividades en esta ubicación.\n"
            else:
                for idx, activity in enumerate(activity_list, 1):
                    name = activity.get("name", "Nombre no disponible")
                    description = activity.get("description", "Descripción no disponible")[:500]  # Limitar a 500 caracteres
                    places_info += f"Actividad #{idx}: {name}\nDescripción: {description}\n---\n"

            return places_info
        except Exception as e:
            return f"Error al obtener actividades: {str(e)}"

# Prueba del script
if __name__ == "__main__":
    input_data = {
        "latitude": 40.4168,  # Ejemplo: Madrid
        "longitude": -3.7038
    }
    agent = PlacesInterest(input_data)
    print(agent.run())
