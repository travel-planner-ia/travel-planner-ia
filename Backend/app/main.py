from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from models.user_request import Datos
from fastapi.middleware.cors import CORSMiddleware
from services.list_of_countries import list_of_countries
from services.stream_answer import stream_answer, procesar_respuesta;
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
    countries = return_countries()
    return {"mensaje": "Bienvenido a la aplicacion", "datos": countries}

# Ruta para enviar consultas al servidor
@app.post("/servidor")
async def post_to_servidor(datos: Datos):
    #"datos" es lo que nos llega desde el formulario de front
    print("datos =", datos)
    #Esto es lo que retornaremos al front
    #stream_answer(datos)
    procesar_respuesta()
    return {"mensaje": "Bienvenido al servidor", "datos":datos}