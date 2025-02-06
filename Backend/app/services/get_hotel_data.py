import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph
from langgraph.graph import END
import requests

# Load environment variables
load_dotenv()

# Initialize Groq (Llama 3)
MODEL = "llama-3.3-70b-versatile"
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(temperature=0, model_name=MODEL, api_key=groq_api_key)

class HotelState(BaseModel):
    """State for the hotel search workflow"""
    messages: List[Dict[str, Any]] = []
    hotel_data: Dict[str, Any] = {}
    current_step: str = "start"
    error: str = ""
    user_input: Dict[str, Any] = {}

class AmadeusAPI:
    def __init__(self):
        self.base_url_v1 = "https://test.api.amadeus.com/v1"
        self.token = None
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    def get_access_token(self) -> str:
        """Get access token from Amadeus API"""
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return self.token
        else:
            raise Exception(f"Failed to get access token: {response.text}")

    def search_city(self, city_name: str) -> List[Dict[str, Any]]:
        """Search for city codes"""
        if not self.token:
            self.get_access_token()

        endpoint = "reference-data/locations"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {
            "subType": "CITY",
            "keyword": city_name,
            "page[limit]": "5"
        }
        
        url = f"{self.base_url_v1}/{endpoint}"
        print(f"\nBuscando código de ciudad para: {city_name}")
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"Error response: {response.text}")
            raise Exception(f"City search failed: {response.text}")

    def search_hotels_by_city(self, city_code: str, radius: int = 5, amenities: List[str] = None, ratings: List[str] = None) -> Dict[str, Any]:
        """Search for hotels in a city"""
        if not self.token:
            self.get_access_token()
        
        endpoint = "reference-data/locations/hotels/by-city"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {
            "cityCode": city_code.upper(),
            "radius": radius,
            "radiusUnit": "KM",
            "hotelSource": "ALL"
        }
        
        if amenities:
            params["amenities"] = ",".join(amenities)
        if ratings:
            params["ratings"] = ",".join(ratings)
        
        url = f"{self.base_url_v1}/{endpoint}"
        print(f"Buscando hoteles en: {city_code} (radio: {radius}km)")
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            raise Exception(f"Hotel search failed: {response.text}")

def get_city_code(api: AmadeusAPI, city_name: str) -> str:
    """Get city code for a city"""
    cities = api.search_city(city_name)
    
    if not cities:
        raise ValueError(f"No se encontró la ciudad: {city_name}")
    
    # Buscar coincidencia exacta primero
    for city in cities:
        if city["name"].lower() == city_name.lower():
            return city["iataCode"]
    
    # Como último recurso, usar el primer código disponible
    return cities[0]["iataCode"]
def process_hotel_data(state: HotelState) -> HotelState:
    """Procesar los datos de hoteles desde la API de Amadeus"""
    try:
        # Validar fechas si están presentes
        if state.user_input.get("check_in") and state.user_input.get("check_out"):
            check_in = datetime.strptime(state.user_input["check_in"], "%Y-%m-%d")
            check_out = datetime.strptime(state.user_input["check_out"], "%Y-%m-%d")
            
            if check_in < datetime.now():
                raise ValueError("La fecha de entrada no puede ser anterior a hoy")
            if check_out <= check_in:
                raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada")

        # Obtener datos de hoteles usando la nueva función
        hotel_data = get_hotel_data(
            city=state.user_input["city"],
            radius=state.user_input.get("radius", 5),
            amenities=state.user_input.get("amenities"),
            ratings=state.user_input.get("ratings")
        )
        
        # Manejar los datos obtenidos o errores
        if "error" in hotel_data:
            state.messages.append({
                "role": "assistant",
                "content": hotel_data["error"]
            })
            state.current_step = "error"
        else:
            state.hotel_data = hotel_data
            state.messages.append({
                "role": "assistant",
                "content": f"Se encontraron {len(hotel_data['data'])} hoteles en {state.user_input['city']}."
            })
            state.current_step = "process_complete"
    
    except ValueError as e:
        state.error = str(e)
        state.current_step = "error"
        state.messages.append({
            "role": "assistant",
            "content": f"Error de validación: {str(e)}"
        })
    except Exception as e:
        state.error = str(e)
        state.current_step = "error"
        state.messages.append({
            "role": "assistant",
            "content": f"Error al buscar hoteles: {str(e)}"
        })
        print(f"Error in process_hotel_data: {e}")
    
    return state

def get_hotel_data(city: str, radius: int = 5, amenities: List[str] = None, ratings: List[str] = None) -> Dict[str, Any]:
    """Obtener información de hoteles para familias según la ciudad, radio de búsqueda, amenities y ratings"""
    amadeus = AmadeusAPI()
    try:
        # Validación de parámetros si es necesario
        city_code = get_city_code(amadeus, city)  # Obtiene el código de ciudad

        # Filtros adicionales para familias
        family_amenities = ["FAMILY_ROOMS", "KIDS_CLUB", "KIDS_POOL", "PLAYGROUND", "CHILD_CARE"]

        # Si ya hay amenities dados, combinarlos con los específicos para familias
        if amenities:
            amenities += family_amenities
        else:
            amenities = family_amenities

        # Buscar hoteles con los parámetros dados
        hotel_data = amadeus.search_hotels_by_city(
            city_code=city_code,
            radius=radius,
            amenities=amenities,
            ratings=ratings
        )

        # Si no se encuentran hoteles
        if not hotel_data.get("data"):
            return {"error": f"No se encontraron hoteles familiares en {city} con los criterios especificados."}
        
        return hotel_data
    
    except Exception as e:
        return {"error": f"Error al obtener los datos de hoteles: {str(e)}"}

