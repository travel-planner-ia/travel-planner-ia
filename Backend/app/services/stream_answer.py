import requests
import time
import os
from dotenv import load_dotenv
import json
load_dotenv()

# print(os.getenv('USER_EMAIL'))
# print(os.getenv('API_KEY'))
# Endpoint y API Key
url = "https://api-nextai-challenge.codingbuddy-4282826dce7d155229a320302e775459-0000.eu-de.containers.appdomain.cloud/aigen/research/stream/wx"


data = {
    "model": "meta-llama/llama-3-1-70b-instruct",
    "uuid": "EscuelasViewnextIA-testEPG-19283746",
    "message": {
        "role": "user",
        "content": "Cuenta un pequeño cuento de 50 palabras como tope"
    },
    "prompt": None, 
    "temperature": 0,
    "plugin_id": None, # Meter pluggin de rag si fuese necesario
    "vectorization_model": None, 
    "origin": "EscuelasViewnextIA",
    "origin_detail": "web",
    "language": "es",
    "user": os.getenv('USER_EMAIL')
}

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": os.getenv('API_KEY')
}

def procesar_respuesta(texto:str):
    #array de texto
    array_de_texto= texto.split('.')

    respuesta = []

    for linea in array_de_texto:
        linea = linea= linea + "."
        respuesta.append(linea)
    respuesta.append('-'*20)
    return respuesta

def stream_answer(input):
    print(url)
    print(input)
    # Realizar la solicitud POST
    try:
        with requests.post(url, json=data, headers=headers, stream=True) as response:
            resp = response.raise_for_status()  
            print("resp =", resp)
            text_to_stream = response.iter_lines(decode_unicode=True)
            print("\ntext_to_stream = ",text_to_stream)
            my_info_to_send = ""

            for line in text_to_stream:
                print("line =", line)
            print("\nMy info to send = ", my_info_to_send) 

    except requests.exceptions.RequestException as e:
        print("Error al realizar la solicitud:", e)