import requests
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Clase para interactuar con la API de Amadeus
class AmadeusAPI:
    def __init__(self):
        self.base_url_v1 = "https://test.api.amadeus.com/v1"  
        self.base_url_v2 = "https://test.api.amadeus.com/v2"  
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


    # Método para buscar aeropuertos por nombre de ciudad
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

    # Método para buscar vuelos por origen, destino y fecha.
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
    
    # Método para obtener el código IATA de un aeropuerto a partir del nombre de la ciudad.
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
    

    # Método para obtener las actividades en una ciudad.
    def get_activities(self, latitude: float, longitude: float, radius: int = 1) -> Dict[str, Any]:
        """Get activities around a given location"""
        if not self.token:
            self.get_access_token()
        endpoint = "shopping/activities"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"latitude": latitude, "longitude": longitude, "radius": radius}
        url = f"{self.base_url_v1}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            activities = response.json()
            # Limitar a las 30 primeras actividades
            if 'data' in activities:
                activities['data'] = activities['data'][:15]
            return activities
        else:
            raise Exception(f"Failed to get activities: {response.text}")
    
    # Método para buscar el código de una ciudad.
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

    # Método para buscar hoteles en una ciudad.
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

    def get_city_code(self, city_name: str) -> str:
        """Get city code for a city"""
        cities = self.search_city(city_name)
        
        if not cities:
            raise ValueError(f"No se encontró la ciudad: {city_name}")
        
        # Buscar coincidencia exacta primero
        for city in cities:
            if city["name"].lower() == city_name.lower():
                return city["iataCode"]
        
        # Como último recurso, usar el primer código disponible
        return cities[0]["iataCode"]
    
    # Método para obtener la latitud y longitud de una ciudad a partir de su nombre.
    def get_lat_lon(self, city_name: str) -> Dict[str, float]:
        """Get latitude and longitude of a city"""
        if not self.token:
            self.get_access_token()

        endpoint = "reference-data/locations/cities"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        params = {
            "keyword": city_name,
            "max": 5,  # Solo devolver el primer resultado
            "include": "AIRPORTS"  # Incluir aeropuertos si es necesario
        }

        url = f"{self.base_url_v1}/{endpoint}"

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                city_data = data["data"][0]
                geo_code = city_data.get("geoCode", {})
                latitude = geo_code.get("latitude")
                longitude = geo_code.get("longitude")
                return {"latitude": latitude, "longitude": longitude}
            else:
                raise Exception(f"No se encontró la ciudad: {city_name}")
        else:
            print(f"Error response: {response.text}")
            raise Exception(f"Failed to get latitude and longitude: {response.text}")
    
