import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class AmadeusAPI:
    def __init__(self):
        self.base_url_v1 = "https://test.api.amadeus.com/v1"  # For airport search
        self.base_url_v2 = "https://test.api.amadeus.com/v2"  # For flight search
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

    def search_airport(self, city_name: str) -> List[Dict[str, Any]]:
        """Search for airports by city name"""
        if not self.token:
            self.get_access_token()

        endpoint = "reference-data/locations"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {
            "subType": "CITY,AIRPORT",
            "keyword": city_name,
            "page[limit]": "5"
        }
        
        url = f"{self.base_url_v1}/{endpoint}"
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"Error response: {response.text}")
            raise Exception(f"Airport search failed: {response.text}")

    def search_flights(self, origin: str, destination: str, date: str) -> Dict[str, Any]:
        """Search for flights using Amadeus API"""
        if not self.token:
            self.get_access_token()
        
        endpoint = "shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": date,
            "adults": "1",
            "currencyCode": "EUR",
            "nonStop": "false",
            "max": "5"
        }
        
        url = f"{self.base_url_v2}/{endpoint}"  # Using v2 for flight search
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            if "Invalid API call" in response.text:
                raise Exception("Error: Asegúrate de que tu cuenta de Amadeus tiene acceso a Flight Offers Search API")
            raise Exception(f"Flight search failed: {response.text}")
    
    def get_iata_code(self, city_name: str) -> str:
        """Get IATA code for a city's main airport"""
        airports = self.search_airport(city_name)
        
        if not airports:
            raise Exception(f"No se encontraron aeropuertos para {city_name}")
        
        # Primero, intentar encontrar un aeropuerto que coincida exactamente con el nombre de la ciudad
        for airport in airports:
            city = airport.get("address", {}).get("cityName", "").lower()
            if city == city_name.lower() and airport.get("subType") == "AIRPORT":
                return airport["iataCode"]
        
        # Si no se encuentra coincidencia exacta, tomar el primer aeropuerto de la lista
        for airport in airports:
            if airport.get("subType") == "AIRPORT":
                return airport["iataCode"]
        
        # Si no hay aeropuertos, usar el primer código IATA disponible
        return airports[0]["iataCode"]

def get_flight_data(origin: str, destination: str, departure_date: str, return_date: str) -> str:
    """
    Get flight data based on origin, destination, departure_date and return_date provided by user.

    Args: 
     origin (str): Origin airport
     destination (str): Destination airport
     departure_date (str): Departure date
     return_date (str): Return date
    """
    amadeus = AmadeusAPI()
    origin = amadeus.get_iata_code(origin)
    destination = amadeus.get_iata_code(destination)    
    flight_data = amadeus.search_flights(origin, destination, departure_date) 
    return_flight_data = amadeus.search_flights(destination, origin, return_date)
    data = {
        'flight_data': flight_data,
        'return_flight_data': return_flight_data
    }
    
    # Formateando data
    prompt = f"Aquí están los vuelos disponibles:\n\n"
    prompt += "VUELOS DE IDA:\n"
    flights = data["flight_data"].get("data", [])
    if not flights:
        prompt += "No se encontraron vuelos de ida para la fecha especificada.\n"
    else:
        for idx, flight in enumerate(flights, 1):
            offer = flight["itineraries"][0]
            segments = offer["segments"]
            price = flight["price"]["total"]
            currency = flight["price"]["currency"]
            
            departure = segments[0]["departure"]
            arrival = segments[-1]["arrival"]
            
            prompt += f"Vuelo {idx}:\n"
            prompt += f"Desde: {departure['iataCode']} a las {departure['at']}\n"
            prompt += f"Hasta: {arrival['iataCode']} a las {arrival['at']}\n"
            prompt += f"Precio: {price} {currency}\n\n"
    
    # Formatear vuelos de vuelta si existen
    if data['return_flight_data']:
        prompt += "\nVUELOS DE VUELTA:\n"
        return_flights = data['return_flight_data'].get("data", [])
        if not return_flights:
            prompt += "No se encontraron vuelos de vuelta para la fecha especificada.\n"
        else:
            for idx, flight in enumerate(return_flights, 1):
                offer = flight["itineraries"][0]
                segments = offer["segments"]
                price = flight["price"]["total"]
                currency = flight["price"]["currency"]
                
                departure = segments[0]["departure"]
                arrival = segments[-1]["arrival"]
                
                prompt += f"Vuelo {idx}:\n"
                prompt += f"Desde: {departure['iataCode']} a las {departure['at']}\n"
                prompt += f"Hasta: {arrival['iataCode']} a las {arrival['at']}\n"
                prompt += f"Precio: {price} {currency}\n\n"
    
    return prompt

# if __name__=='__main__':
#     prompt = get_flight_data('Barcelona', 'Madrid', '2025-03-01', '2025-04-10')
#     print(prompt)