from get_flight_data import get_flight_data
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState, StateGraph
from langchain_core.tools import tool
from langgraph.graph import START, END
from pydantic import BaseModel

groq_api_key="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"
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
            SystemMessage(content=f"""You are a helpful flight assistant. Analyze the flight information and provide a clear, concise 
                          summary of the available options. \n {results}""")
        ]
        resp = self.agent.invoke({"messages": messages, "verbose": False})
        return resp['messages'].content

if __name__ == "__main__": 
    input_data = {
        'origin': 'Madrid',
        'destination': 'Barcelona',
        'departure_date': '2025-03-01',
        'return_date': '2025-04-10'
    }
    agent = FlightAgent(input_data)
    print(agent.run())