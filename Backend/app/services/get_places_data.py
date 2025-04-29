from dotenv import load_dotenv
from models.amadeus_class import AmadeusAPI
import asyncio

load_dotenv()

def get_places_data(city_name:str, radius: int = 1) -> str:
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
        lat_lon_dict = amadeus.get_lat_lon(city_name)
        latitude = lat_lon_dict.get("latitude")
        longitude = lat_lon_dict.get("longitude")
        
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
