from dotenv import load_dotenv
from models.amadeus_class import AmadeusAPI

load_dotenv()

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