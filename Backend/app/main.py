from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from models.user_request import Datos
from fastapi.middleware.cors import CORSMiddleware
from services.list_of_countries import list_of_countries
from services.stream_answer import stream_answer, procesar_respuesta;
from services.travel_rag import Embedder, Scrapper
# from services.get_countries import return_countries;
# import bs4
#print(bs4.__version__)


app = FastAPI()

origins = [
    "http://localhost:3000",  # origen del frontend
    "null"  # origen del frontend cuando se ejecuta desde un archivo local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta inicial
@app.get("/")
async def get_home():
    countries = list_of_countries
    return {"mensaje": "Bienvenido a la aplicacion", "datos": countries}

# Ruta para enviar consultas al servidor
@app.post("/servidor")
async def post_to_servidor(frontRequest: Datos):
    #"frontRequest" es lo que nos llega desde el formulario de front
    print("frontRequest =", frontRequest)

    json_de_data = frontRequest.dict(exclude_unset=True)
    print("json_de_data =", json_de_data)

    #Aquí haremos la llamada
    try:
        embedder = Embedder("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")
        respuestas = await embedder.rag_pais(frontRequest.destination)

    except Exception as e:
        print("Error en la llamada al RAG")
        print(e)
    #Respuesta de la llamada

    #Esto es lo que retornaremos al front
    
    return {"mensaje": "Bienvenido al servidor", "datos":procesar_respuesta()}
