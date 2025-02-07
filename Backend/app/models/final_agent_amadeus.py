from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
import os
from dotenv import load_dotenv
load_dotenv()
from models.hotel_agent_class import HotelAgent
from models.flight_agent_class import FlightAgent
from models.places_agent_class import PlacesAgent
from pydantic import BaseModel

groq_api_key = os.getenv("GROQ_API_KEY_FINAL_AGENT")
MODEL = "llama-3.3-70b-versatile"

class GraphState(BaseModel):
    messages: list
    number_interactions: int = 0
    verbose: bool = True

# Agente final que se encarga de hacer un resumen general de la información proporcionada por los agentes especializados en vuelos, 
# hoteles y lugares de interés
class GeneralAgent:
    def __init__(self, input_data):
        self.hotel_agent = HotelAgent(input_data)
        self.flight_agent = FlightAgent(input_data)
        self.places_agent = PlacesAgent(input_data)
        self.model = ChatGroq(temperature=0, model_name=MODEL, api_key=groq_api_key)
        self.graph = StateGraph(GraphState)
        self.graph.add_node("agent", self.call_model)
        self.graph.add_edge(START, "agent")
        self.graph.add_edge("agent", END)
        self.agent = self.graph.compile()
    
    def call_model(self, state):
        if state.verbose:
            print("---- Llamando al modelo ----")
        state.number_interactions += 1
        state.messages = self.model.invoke(state.messages)
        return state
    
    def run(self):
        try:
            hotel_response = self.hotel_agent.run()
        except Exception as e:
            hotel_response = "No has podido encontrar hoteles disponibles en la ubicación especificada."
        try:
            flight_response = self.flight_agent.run()
        except Exception as e:
            flight_response = "No has podido encontrar vuelos disponibles en la ubicación especificada."
        try:
            places_response = self.places_agent.run()
        except Exception as e:  
            places_response = "No has podido encontrar lugares de interés en la ubicación especificada."
        
        
        messages = [
            SystemMessage(content=f"""Eres un asistente de viajes especializado en familias. Analiza la siguiente información sobre vuelos, hoteles y lugares de interés
                          . Cada uno de los asistentes especializados en vuelos, hoteles y lugares de interés te ha proporcionado información específica sobre 
                          cada uno de los temas. \n **Vuelos** {flight_response} \n **Hoteles** {hotel_response} \n **Lugares de interés** {places_response} \n 
                          Por favor, proporciona un resumen general de las mejores opciones para un viaje en familia, considerando la información proporcionada por los asistentes.
                          Cuando hagas referencia a vuelos, hoteles o lugares asegurate de especificar el nombre de los mismos, sin usar números. Si no hay información en las secciones
                          Hoteles, Vuelos o Lugares de Interés, simplemente responde que no tienes información, es decir, usa solo la información que se te da.\n""")
        ]

        resp = self.agent.invoke({"messages": messages, "verbose": False})
        return resp['messages'].content