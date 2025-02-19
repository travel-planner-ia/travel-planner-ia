from pydantic import BaseModel
from typing import List

# Clase para representar los datos de la solicitud del usuario que provienen del frontend.
class Datos(BaseModel):
    origin:str
    country:str
    destination: str
    adults: int
    children: int
    departureDate: str
    returnDate: str
    budget: int
    medicalCondition: str
    additionalInfo: str
    tags: List[str]