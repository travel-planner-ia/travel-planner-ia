import requests
import time
import os
from dotenv import load_dotenv
import json
load_dotenv()

print(os.getenv('USER_EMAIL'))
print(os.getenv('API_KEY'))
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

    #este texto será el texto a mostrar por pantalla
    #texto =  "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?"
    
    #array de texto
    array_de_texto= texto.split('.')

    respuesta = []

    for linea in array_de_texto:
        linea = linea= linea + "."
        respuesta.append(linea)
    respuesta.append('-'*20)
    return respuesta
    
    # try:
    #     response = requests.post(url, json=data, headers=headers)
    #     response.raise_for_status()
    #     try:
    #         json_response = response.json()
    #         print("json_response =",json_response)
    #         texto_respuesta = json_response.get("texto")  # Ajusta el nombre de la clave según la estructura del JSON
    #         print("texto_respuesta =",texto_respuesta)
            
    #         array_respuesta = texto_respuesta.split("\n")
    #         json_salida = {"respuesta": array_respuesta}
    #         print(json_salida)
    #         return json.dumps(json_salida, indent=4)
    #     except json.JSONDecodeError as e:
    #         print("Error al parsear la respuesta como JSON:", e)
    #         print("Respuesta del servidor:", response.text)
    #         return None
    # except requests.exceptions.RequestException as e:
    #     print("Error al realizar la solicitud:", e)
    #     return None


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
            #print("Respuesta en streaming:")
            my_info_to_send = ""

            for line in text_to_stream:
                print("line =", line)

            # for line in text_to_stream:
            #     if line: 
            #         for char in line: 
            #             print(char, end="", flush=True) 
            #             time.sleep(0.01)  
            #             my_info_to_send += char
                        
                        #enviar aquí al front un json pequeño 
                        #split("\n") y luego emitir un json
            print("\nMy info to send = ", my_info_to_send) 

    except requests.exceptions.RequestException as e:
        print("Error al realizar la solicitud:", e)