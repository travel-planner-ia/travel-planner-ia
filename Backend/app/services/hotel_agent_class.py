from get_hotel_data import get_hotel_data
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState, StateGraph
from langchain_core.tools import tool
from langgraph.graph import START, END
from pydantic import BaseModel

groq_api_key = "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"
MODEL = "llama-3.3-70b-versatile"

class GraphState(BaseModel):
    messages: list
    number_interactions: int = 0
    verbose: bool = True

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
            print("---- Calling Model ----")
        state.number_interactions += 1
        state.messages = self.model.invoke(state.messages)
        return state
    
    def run(self):
        city, check_in, check_out, radius, amenities, ratings = self.input_data['city'], self.input_data['check_in'], self.input_data['check_out'], self.input_data['radius'], self.input_data['amenities'], self.input_data['ratings']
        
        # Get hotel data from the API
        results = self.get_hotel_data(city, radius, amenities, ratings)
        
        # If the result contains an error, return that
        if 'error' in results:
            return results['error']
        
        # Print the hotel data to check its structure
        # print(results)

        # Prepare the results to pass into the model
        results_str = "\n".join([f"Hotel: {hotel['name']}, Location: {hotel.get('location', 'No disponible')}, Amenities: {hotel.get('amenities', 'No disponible')}" for hotel in results['data']])
        
        # Create the message for the model
        messages = [
            SystemMessage(content=f"""Eres un asistente de hotel útil. Analiza la siguiente información del hotel y proporciona un resumen claro y conciso de los 5 mejores hoteles en función de sus servicios, calificaciones y calidad general:
                                    \n{results_str}""")
        ]
        
        # Run the agent and return the response
        resp = self.agent.invoke({"messages": messages, "verbose": False})
        return resp['messages'].content



if __name__ == "__main__": 
    input_data = {
        'city': 'Paris',
        'check_in': '2025-03-01',
        'check_out': '2025-03-10',
        'radius': 5,
        'amenities': ['SWIMMING_POOL', 'WIFI'],
        'ratings': ['4', '5']
    }
    
    # Create the HotelAgent and run the process
    agent = HotelAgent(input_data)
    print(agent.run())
