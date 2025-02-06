from services.get_flight_data import get_flight_data
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

class GraphState(BaseModel):
    messages: list
    number_interactions: int = 0
    verbose: bool = True

class FlightAgent():
    def __init__(self, input_data):
        self.model = ChatGroq(temperature=0, model_name=MODEL, api_key=groq_api_key)
        self.graph = StateGraph(GraphState)
        self.graph.add_node("agent", self.call_model)
        self.graph.add_edge(START, "agent")
        self.graph.add_edge("agent", END)
        self.agent = self.graph.compile()
        self.input_data = input_data
        self.get_flight_data = get_flight_data
        
    def call_model(self, state):
        if state.verbose:
            print("---- Call Model ----")
        state.number_interactions += 1
        state.messages = self.model.invoke(state.messages)
        return state
    
    def run(self):
        origin, destination, departure_date, return_date = self.input_data['origin'], self.input_data['destination'], self.input_data['departure_date'], self.input_data['return_date']
        results = self.get_flight_data(origin, destination, departure_date, return_date)
        messages = [
            SystemMessage(content=f"""Eres un asistente especializado en información sobre vuelos y viajes familiares. Analiza la 
                          información sobre vuelos y proporciona una respuesta clara, concisa y que sugiera las mejores opciones
                          para un usuario que desea realizar un viaje en familia. Cuando te refieras a un vuelo, debes de añadir toda la información
                          asociada al mismo. \n {results}""")
        ]
        resp = self.agent.invoke({"messages": messages, "verbose": True})
        return resp['messages'].content

    