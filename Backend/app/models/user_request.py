from pydantic import BaseModel
from typing import List

class Datos(BaseModel):
    destination: str
    adults: int
    children: int
    departureDate: str
    returnDate: str
    budget: int
    medicalCondition: str
    additionalInfo: str
    tags: List[str]