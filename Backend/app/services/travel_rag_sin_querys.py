import sqlite_vec
import time
import argparse
import sqlite3
#from fastembed import TextEmbedding #En caso de que acabemos haciendolo con esta librería que a mi no me funciona
from langchain.embeddings import HuggingFaceEmbeddings
from groq import Groq
from groq.types.chat import ChatCompletionMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlite_vec import serialize_float32
from tqdm import tqdm
import numpy as np
from textwrap import dedent
import requests
from bs4 import BeautifulSoup
import pdfplumber
from io import BytesIO

text_splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=128)

EMBEDDING_PROMPT = """
{chunk}
"""

SYSTEM_PROMPT = """
You are an expert in extracting key insights from texts. Your task is to summarize and highlight the most important features.

Use only the provided context to identify the key characteristics. If you don't find information about the topic just answer that you can't answer that question with the infomation provided.
"""

#Las diferents Api-keys que he ido generando en Groq, según se vayan agotando probad con otras, las dos primeras creo que estan baneadas
#client = Groq(api_key="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")
#client = Groq(api_key='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')
#client = Groq(api_key = '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')
client = Groq(api_key="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")
#client = Groq(api_key = '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')

MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0

db = sqlite3.connect("readmes.sqlite3")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)


#Función que vectoriza
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def call_model(prompt: str, messages=[]) -> ChatCompletionMessage:
    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content

def non_contextual_chunks(chunks, document: str):
    contextual_chunks = []
    for chunk in chunks:
        prompt = EMBEDDING_PROMPT.format(chunk=chunk)
        #chunk_context = call_model(prompt)
        contextual_chunks.append(f"{prompt}")
    return contextual_chunks


def save_chunks(chunks,doc_id):
    chunk_embeddings = list(embedding_model.embed_documents(chunks))
    for chunk, embedding in zip(chunks, chunk_embeddings):
        result = db.execute(
            "INSERT INTO chunks(document_id, text) VALUES(?, ?)", [doc_id, chunk]
        )
        chunk_id = result.lastrowid
        db.execute(
            "INSERT INTO chunk_embeddings(id, embedding) VALUES (?, ?)",
            [chunk_id, serialize_float32(embedding)],
        )


# Función para hacer una petición con manejo del límite de tokens
def guardar_chunk(doc_text,doc_id):
      chunks_doc = text_splitter.split_text(doc_text)
      non_c_chunks = non_contextual_chunks(chunks_doc, doc_text)
      save_chunks(non_c_chunks,doc_id)
      return('Chunks guardados con éxito')

def retrieve_context(
    query: str, k: int = 3, embedding_model: HuggingFaceEmbeddings = embedding_model
) -> str:
    query_embedding = list(embedding_model.embed_documents([query]))[0]
    results = db.execute(
        """
    SELECT
        chunk_embeddings.id,
        distance,
        text
    FROM chunk_embeddings
    LEFT JOIN chunks ON chunks.id = chunk_embeddings.id
    WHERE embedding MATCH ? AND k = ?
    ORDER BY distance
        """,
        [serialize_float32(query_embedding), k],
    ).fetchall()
    return "\n-----\n".join([item[2] for item in results])


def ask_question(query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]
    context = retrieve_context(query)
    prompt = dedent(
        f"""
Use the following information:

```
{context}
```

to answer the question:
{query}
    """
    )
    return call_model(prompt, messages), context

#WebScrapper
class Scrapper:

    def __init__(self, pais: str):
        self.pais = pais
        self.base_url = "https://www.exteriores.gob.es/es/ServiciosAlCiudadano/Paginas/Recomendaciones-de-viaje.aspx#alphabet"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })

    def buscar_urls_pais(self):
        try:
            response = self.session.get(self.base_url, timeout=10)  # Timeout de 10 segundos
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f'Error al realizar la solicitud HTTP: {e}'

        # Analizar el HTML con BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        h2_tags = soup.find_all('h2')

        pais_encontrado = False
        for h2_tag in h2_tags:
            country_name = h2_tag.text.strip()

            if self.pais.lower() in country_name.lower():
                row_div = h2_tag.find_next("div", class_="row")
                if row_div:
                    links = row_div.find_all("a", href=True)
                    urls = ["https://www.exteriores.gob.es" + link["href"] for link in links]

                    print(f"País encontrado: {country_name}")
                    for i, url in enumerate(urls[:3], 1):
                        print(f"URL {i}: {url}")

                    return urls[:3]  # Retornar solo las tres primeras URLs encontradas

                pais_encontrado = True
                break

        if not pais_encontrado:
            print(f"El país {self.pais} no fue encontrado.")
            return []

    def extraer_contenido_pdf_informacion(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "application/pdf",
            "Referer": "https://www.exteriores.gob.es/",
            "Connection": "keep-alive"
        }

        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()

            with pdfplumber.open(BytesIO(response.content)) as pdf:
                pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            chunks = []
            start = 0
            chunk_test = []
            while start < len(pdf_text):
                end = start + 2000

                if end < len(pdf_text):
                    last_newline = pdf_text.rfind('\n', start, end)
                    if last_newline != -1:
                        end = last_newline
                    else:
                        end = start + 2000

                chunks.append(pdf_text[start:end].strip())
                start = end  # Avanza al siguiente trozo

            chunk_test.append(chunks)
            return chunk_test[0]
        except requests.exceptions.RequestException as e:
            return f'Error al realizar la solicitud HTTP: {e}'

    def extraer_contenido_recomendacion_viaje(self, url: str):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            div_principal = soup.find('div', id='ctl00_ctl48_g_b1cd54bc_3d61_4c2b_a319_b305ee4143d3')

            if not div_principal:
                return ''
            secciones = []
            for section in div_principal.find_all("div", class_="single__text panel ltr-text"):
              contenido = section.get_text(separator='\n', strip=False)
              secciones.append(contenido)
            return secciones
        except requests.exceptions.RequestException as e:
            return f'Error al realizar la solicitud HTTP: {e}'

def rag_pais(pais:str,query:str):
    #Para borrar las tablas y volver a crearlas a medida que se hacen pruebas
  db.execute("DROP TABLE IF EXISTS chunk;")
  db.execute("DROP TABLE IF EXISTS documents;")
  db.execute("DROP TABLE IF EXISTS chunk_embeddings;")
  db.execute("DROP TABLE IF EXISTS chunks;")

  db.execute(
      """
  CREATE TABLE documents(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      text TEXT
  );
  """
  )

  db.execute(
      """
  CREATE TABLE chunks(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      document_id INTEGER,
      text TEXT,
      FOREIGN KEY(document_id) REFERENCES documents(id)
  );
  """
  )

  scraper = Scrapper(pais)
  urls = scraper.buscar_urls_pais()
  textos=[]
  for url in urls:
    try:
        t = scraper.extraer_contenido_recomendacion_viaje(url)
        textos.append(t)
    except:
        t = scraper.extraer_contenido_pdf_informacion(url)
        textos.append(t)
  textos_aplanados = [sublista for lista in textos for sublista in lista]
  documents = textos_aplanados
  
  document_embeddings = list(embedding_model.embed_documents(documents))

  document_embeddings = np.array(document_embeddings)
  db.execute(
      f"""
          CREATE VIRTUAL TABLE chunk_embeddings USING vec0(
            id INTEGER PRIMARY KEY,
            embedding FLOAT[{document_embeddings[0].shape[0]}],
          );
      """
  )
  with db:
      for doc in documents:
          db.execute("INSERT INTO documents(text) VALUES(?)", [doc])
  with db:
    document_rows = db.execute("SELECT id, text FROM documents").fetchall()
    for row in document_rows:
          doc_id, doc_text = row
          guardar_chunk(doc_text,doc_id)

  
  response, context = ask_question(query)
  return(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG")
    parser.add_argument("pais", type=str, help="País")
    parser.add_argument("query", type=str, help="Query")
    args = parser.parse_args()
    try:
        print(rag_pais(args.pais, args.query))
    except:
        print('País no encontrado')