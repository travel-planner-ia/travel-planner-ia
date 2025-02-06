import requests
from bs4 import BeautifulSoup

#URL de la página principal
url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Recomendaciones-de-viaje.aspx#alphabet"

#Simular navegador en los headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def scrap_countries():
    #Crear una sesión
    session = requests.Session()
    session.headers.update(headers)

    #Obtener la página principal
    response = session.get(url)
    response.raise_for_status()

    #Analizar el HTML con BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    #Lista para almacenar los nombres de los países extraídos de los <h2>
    country_names = []

    #Buscar los elementos <h2> que contienen los nombres de los países
    h2_tags = soup.find_all('h2')

    #Extraer el texto de cada <h2> y agregarlo a la lista
    for h2_tag in h2_tags:
        country_names.append(h2_tag.text.strip())  # .strip() elimina espacios extra

    return country_names


def return_countries():
    country_names = scrap_countries()
    return country_names