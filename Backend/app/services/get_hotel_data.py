from typing import Dict, Any, List
from dotenv import load_dotenv
from datetime import datetime
from models.amadeus_class import AmadeusAPI
import asyncio

load_dotenv()

# Método para obtener los hoteles disponibles por ciudad, fecha de entrada y fecha de salida.
def get_hotel_data(check_in: str, check_out: str, city_name: str, 
                   radius: int = 5, amenities: List[str] = None, 
                   ratings: List[str] = None) -> Dict[str, Any]:
    """Get hotel data using Amadeus API"""

    amadeus = AmadeusAPI()
    prompt = f"Buscando hoteles en {city_name} del {check_in} al {check_out} \n"

    check_in = datetime.strptime(check_in, "%Y-%m-%d")
    check_out = datetime.strptime(check_out, "%Y-%m-%d")
    city_code = amadeus.get_city_code(city_name)

    hotel_data =  amadeus.search_hotels_by_city(
            city_code=city_code,
            radius=radius,
            amenities=amenities,
            ratings=ratings
        )
    
    if not hotel_data.get('data'):
        prompt += f"No se encontraron hoteles en {city_name} con los criterios especificados."
        return prompt
    else :
        prompt += f"Se encontraron {len(hotel_data['data'])} hoteles en {city_name} \n"
        hotels = hotel_data.get("data", [])
        if not hotels:
            return "No se encontraron hoteles con los criterios especificados."
        
        hotel_info = []
        for idx, hotel in enumerate(hotels, 1):
            name = hotel.get("name", "Nombre no disponible")
            
            # Obtener información de ubicación
            address = hotel.get("address", {})
            location = f"{address.get('cityName', '')}, {address.get('countryCode', '')}"
            
            # Obtener coordenadas
            geo_code = hotel.get("geoCode", {})
            coordinates = f"({geo_code.get('latitude', 'N/A')}, {geo_code.get('longitude', 'N/A')})"
            
            # Obtener amenities si están disponibles
            amenities = hotel.get("amenities", [])
            amenities_str = ", ".join(amenities) if amenities else "No disponible"
            
            hotel_info.append(
                f"Hotel #{idx}: {name}\n"
                f"Ubicación: {location}\n"
                f"Coordenadas: {coordinates}\n"
                f"Servicios: {amenities_str}\n"
                f"---"
            )
    
        formatted_info = "\n".join(hotel_info)
        prompt += f"Aquí están los hoteles disponibles:\n\n{formatted_info}"

        return prompt