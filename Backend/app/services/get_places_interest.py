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
                activities['data'] = activities['data'][:30]
            return activities
        else:
            raise Exception(f"Failed to get activities: {response.text}")

def get_places_data(latitude: float, longitude: float, radius: int = 1) -> str:
    """
    Get activities based on latitude and longitude provided by user.

    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
        radius (int): Search radius in kilometers (default is 1)

    Returns:
        str: Formatted string with available activities
    """
    amadeus = AmadeusAPI()

    try:
        activities = amadeus.get_activities(latitude, longitude, radius)
        
        # Formatear la información de las actividades
        prompt = f"Aquí están las actividades disponibles en la ubicación ({latitude}, {longitude}):\n\n"

        activity_list = activities.get("data", [])
        if not activity_list:
            prompt += "No se encontraron actividades en esta ubicación.\n"
        else:
            for idx, activity in enumerate(activity_list, 1):
                name = activity.get("name", "Nombre no disponible")
                description = activity.get("description", "Descripción no disponible")[:500]  # Limitar a 500 caracteres
                prompt += f"Actividad #{idx}: {name}\nDescripción: {description}\n---\n"
        
        return prompt

    except Exception as e:
        return f"Error al obtener actividades: {str(e)}"
