import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage
from pydantic import BaseModel
from dotenv import load_dotenv
from services.get_places_data import get_places_data

# Cargar variables de entorno
load_dotenv()

# Configuración de Groq LLM
groq_api_key = os.getenv("GROQ_API_KEY_PLACES")
MODEL = "llama-3.3-70b-versatile"

# Clase para manejar el estado del grafo
class GraphState(BaseModel):
    messages: list
    number_interactions: int = 0
    verbose: bool = True

# Clase principal para manejar la búsqueda y análisis de lugares de interés
class PlacesAgent:
    def __init__(self, input_data):
        self.model = ChatGroq(temperature=0, model_name=MODEL, api_key=groq_api_key)
        self.graph = StateGraph(GraphState)
        self.graph.add_node("agent", self.call_model)
        self.graph.add_edge(START, "agent")
        self.graph.add_edge("agent", END)
        self.agent = self.graph.compile()
        self.input_data = input_data
        self.get_places_data = get_places_data

    def call_model(self, state):
        if state.verbose:
            print("---- Llamando al modelo ----")
        state.number_interactions += 1
        state.messages = self.model.invoke(state.messages)
        return state

    def run(self):
        city_name = self.input_data.get("destination")
        places_info = self.get_places_data(city_name=city_name)
        
        if not places_info:
            return "No se encontraron lugares de interés en la ubicación especificada."

        messages = [
            SystemMessage(content=f""""Eres un asistente de viajes especializado en familias. Analiza los siguientes
                          lugares de interés en {places_info} y proporciona un resumen con cinco actividades
                          recomendadas para una familia. Para cada actividad, menciona dos o tres lugares que sean ideales
                           para disfrutarla, junto con un breve consejo útil para hacer la experiencia más agradable. Asegúrate
                           de considerar opciones que sean aptas para diferentes edades y que brinden una experiencia única.\n""")
        ]

        resp = self.agent.invoke({"messages": messages, "verbose": False})

        return resp['messages'].content

