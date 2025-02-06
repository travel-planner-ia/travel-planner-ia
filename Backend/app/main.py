from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
from models.user_request import Datos
from fastapi.middleware.cors import CORSMiddleware
from services.list_of_countries import list_of_countries
from services.stream_answer import stream_answer, procesar_respuesta;
from services.travel_rag import Embedder, Scrapper
from models.final_agent_amadeus import GeneralAgent
from llm import LLM
import asyncio
# from services.get_countries import return_countries;
# import bs4
#print(bs4.__version__)


app = FastAPI()
semaforo = asyncio.Semaphore(1)
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


async def procesar_respuestas(front_request):
    # Llamadas a procesos pesados (RAG y Amadeus) en paralelo
    async def obtener_rag():
        try:
            embedder = Embedder("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")
            return await embedder.rag_pais(front_request.destination)
        except Exception as e:
            print("Error en la llamada a RAG:", e)
            return None

    async def obtener_amadeus():
        try:
            # Simulación de llamada sincrónica convertida en asíncrona
            await asyncio.sleep(1)  # Simulación de retardo
            return """
                **Vuelos:**  
                - Aerolínea: Air Family  
                - Vuelo: AF1234  
                - Precio: 250€  
                
                **Hoteles:**  
                - Hotel Familiar París (150€/noche)  
            """
        except Exception as e:
            print("Error en la llamada a Amadeus:", e)
            return None

    # Ejecuta en paralelo y espera ambas respuestas
    respuestas_rag, respuestas_amadeus = await asyncio.gather(
        obtener_rag(), obtener_amadeus()
    )

    return respuestas_rag, respuestas_amadeus


@app.post("/servidor")
async def post_to_servidor(frontRequest: Datos):
    print("frontRequest =", frontRequest)

    # Procesa tareas concurrentemente con semáforo para la sección crítica
    async with semaforo:
        respuestas_rag, respuestas_amaedeus = await procesar_respuestas(frontRequest)

        try:
            if respuestas_rag and respuestas_amaedeus:
                llm = LLM('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')
                prompt = llm._prompting(respuestas_rag, respuestas_amaedeus, frontRequest)
                respuesta_final = llm._llamada_llm(prompt)
                return {"mensaje": "Respuesta procesada", "datos": procesar_respuesta(respuesta_final)}
            else:
                return {"error": "Fallo en la obtención de respuestas RAG o Amadeus"}
        except Exception as e:
            print("Error en la llamada final al LLM:", e)
            return {"error": "Error procesando la respuesta final"}


'''
# Ruta para enviar consultas al servidor
@app.post("/servidor")
async def post_to_servidor(frontRequest: Datos):
    #"frontRequest" es lo que nos llega desde el formulario de front
    print("frontRequest =", frontRequest)
    #Aquí haremos la llamada
    try:
        embedder = Embedder("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")
        respuestas_rag = await embedder.rag_pais(frontRequest.destination)

    except Exception as e:
        print("Error en la llamada al RAG")
        print(e)

    # try:
    #     amadeus = GeneralAgent(frontRequest)
    #     #respuestas_amaedeus = await amadeus.run()
    #     respuestas_amaedeus = amadeus.run()
    # except Exception as e:
    #     print("Error en la llamada a Amadeus")
    #     print(e)
    
    respuestas_amaedeus  = """
            **Vuelos:**  
            - Aerolínea: Air Family  
            - Vuelo: AF1234  
            - Salida: 15 de marzo de 2025 desde Madrid-Barajas (MAD)  
            - Llegada: 15 de marzo de 2025 a París-Charles de Gaulle (CDG)  
            - Duración: 2 horas y 15 minutos  
            - Precio: 250€ por persona  

            **Hoteles:**  
            1. Hotel Familiar París  
            - Ubicación: Distrito 7, cerca de la Torre Eiffel  
            - Habitaciones familiares disponibles  
            - Precio: 150€ por noche  
            - Servicios: Zona de juegos, servicio de niñera  

            2. Resort Tranquille  
            - Ubicación: Afueras de París  
            - Precio: 200€ por noche  
            - Servicios: Piscina, actividades infantiles, transporte al centro  

            **Lugares de interés:**  
            - Disneyland París: Parque temático para todas las edades  
            - Jardines de Luxemburgo: Espacio perfecto para un paseo familiar  
            - Museo de Ciencias Palais de la Découverte: Actividades interactivas para niños  
            """  

    async with semaforo:
        try:
            llm = LLM()
            prompt = llm._prompting(respuestas_rag,respuestas_amaedeus,frontRequest)
            respuesta_final = llm._llamada_llm(prompt)
        except Exception as e:
            print("Error en la llamada final al LLM de Llama")
            print(e)  
    #Respuesta de la llamada

    #Esto es lo que retornaremos al front
    #procesar_respuesta()
    return {"mensaje": "Bienvenido al servidor", "datos": procesar_respuesta(respuesta_final)}
'''