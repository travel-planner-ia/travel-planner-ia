from services.get_hotel_data import get_hotel_data
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY_HOTELS")
MODEL = "llama-3.3-70b-versatile"

class GraphState(BaseModel):
    messages: list
    number_interactions: int = 0
    verbose: bool = True

# Clase que representa al agente de hoteles encargado de recomendar hoteles en base a la información proporcionada.
class HotelAgent():
    def __init__(self, input_data):
        self.model = ChatGroq(temperature=0, model_name=MODEL, api_key=groq_api_key)
        self.graph = StateGraph(GraphState)
        self.graph.add_node("agent", self.call_model)
        self.graph.add_edge(START, "agent")
        self.graph.add_edge("agent", END)
        self.agent = self.graph.compile()
        self.input_data = input_data
        self.get_hotel_data = get_hotel_data
        
    def call_model(self, state):
        if state.verbose:
            print("---- Call Model ----")
        state.number_interactions += 1
        state.messages = self.model.invoke(state.messages)
        return state
    
    def run(self):
        print(f'HOTEL!!!!!!!!!!!!!!!')
        check_in, check_out, city_name = self.input_data['departureDate'], self.input_data['returnDate'], self.input_data['destination']
        results = self.get_hotel_data(check_in, check_out, city_name)
        messages = [
            SystemMessage(content=f"""Eres un asistente de viajes experto en familias. Analiza la siguiente información
                          de hoteles y proporciona recomendaciones: \n {results} \n
                          Por favor, proporciona:
                            1. Un resumen de las mejores opciones basado en la ubicación y servicios disponibles
                            2. Cualquier observación importante sobre la ubicación o servicios especiales""")
        ]
        resp = self.agent.invoke({"messages": messages, "verbose": True})
        return resp['messages'].content
    