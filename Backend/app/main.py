from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from models.user_request import Datos
from fastapi.middleware.cors import CORSMiddleware

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
    return {"mensaje": "Bienvenido a la aplicacion"}

# Ruta para enviar consultas al servidor
@app.post("/servidor")
async def post_to_servidor(datos: Datos):
    print("datos =", datos)
    return {"mensaje": "Bienvenido al servidor", "datos":datos}