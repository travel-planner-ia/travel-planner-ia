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
import os
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_PROMPT = """
{chunk}
"""

SYSTEM_PROMPT = """
You are an expert tourist guide and expert in extracting key insights from texts. Your task is to provide accurate and engaging answers based only on the given context.
 
If the information about a topic is not present in the provided context, simply state that you cannot answer the question with the information available.
"""

#Embbeder y RAG
class Embedder:

    def __init__(self, api_key: str, db_path: str = "readmes.sqlite3"):
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=128)
            self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
            self.temperature = 0
            self.db = sqlite3.connect(db_path)
            self._setup_db()
            self.responses = []

    def _setup_db(self):
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)

    def call_model(self, prompt: str, messages=[]) -> ChatCompletionMessage:
        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=self.temperature
        )
        return response.choices[0].message.content
    
    def non_contextual_chunks(self, chunks, document: str):
        contextual_chunks = []
        for chunk in chunks:
            prompt = EMBEDDING_PROMPT.format(chunk=chunk)
            contextual_chunks.append(f"{prompt}")
        return contextual_chunks
    
    def save_chunks(self, chunks, doc_id):
        chunk_embeddings = list(self.embedding_model.embed_documents(chunks))
        for chunk, embedding in zip(chunks, chunk_embeddings):
            result = self.db.execute(
                "INSERT INTO chunks(document_id, text) VALUES(?, ?)", [doc_id, chunk]
            )
            chunk_id = result.lastrowid
            self.db.execute(
                "INSERT INTO chunk_embeddings(id, embedding) VALUES (?, ?)",
                [chunk_id, serialize_float32(embedding)],
            )

    def guardar_chunk(self, doc_text, doc_id):
        chunks_doc = self.text_splitter.split_text(doc_text)
        non_c_chunks = self.non_contextual_chunks(chunks_doc, doc_text)
        self.save_chunks(non_c_chunks, doc_id)
        return "Chunks guardados con éxito"
    
    def retrieve_context(self, query: str, k: int = 3) -> str:
        query_embedding = list(self.embedding_model.embed_documents([query]))[0]
        results = self.db.execute(
            """
            SELECT chunk_embeddings.id, distance, text
            FROM chunk_embeddings
            LEFT JOIN chunks ON chunks.id = chunk_embeddings.id
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
            """, [serialize_float32(query_embedding), k]
        ).fetchall()
        return "\n-----\n".join([item[2] for item in results])
    
    def ask_question(self, query: str) -> str:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
        ]
        context = self.retrieve_context(query)
        prompt = dedent(f"""
        Use the following information:

        ```
        {context}
        ```

        to answer the question:
        {query}
        """)
        return self.call_model(prompt, messages), context
    
    def get_travel_queries(self, pais: str):
        travel_queries = [
            "¿Existen áreas en {} que se deban evitar debido a conflictos o riesgos para la seguridad?",
            "¿Es necesario obtener una visa para ingresar a {}?",
            "¿Qué documentos de viaje son obligatorios para los ciudadanos españoles en {}?",
            "¿Se requieren vacunas específicas para viajar a {}?",
            "¿Qué medios de transporte son más seguros y recomendados para desplazarse dentro de {}?",
            "¿Hay leyes específicas en {} que los turistas deben conocer para evitar infracciones?",
            "¿Cuál es la moneda oficial de {} y es ampliamente aceptada?",
            "¿Dónde se encuentra la embajada o consulado español más cercano en {}?"
        ]

        return [{"id": i+1, "query": query.format(pais)} for i, query in enumerate(travel_queries)]
    
    def rag_pais(self, pais: str):
        # Para borrar las tablas y volver a crearlas a medida que se hacen pruebas
        self.db.execute("DROP TABLE IF EXISTS chunk;")
        self.db.execute("DROP TABLE IF EXISTS documents;")
        self.db.execute("DROP TABLE IF EXISTS chunk_embeddings;")
        self.db.execute("DROP TABLE IF EXISTS chunks;")

        self.db.execute(
            """
            CREATE TABLE documents(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT
            );
            """
        )

        self.db.execute(
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
        url_text = scraper.extraer_contenido_recomendacion_viaje(urls[1])
        documents = url_text
        
        document_embeddings = list(self.embedding_model.embed_documents(documents))
        document_embeddings = np.array(document_embeddings)
        

        self.db.execute(
            f"""
                CREATE VIRTUAL TABLE chunk_embeddings USING vec0(
                    id INTEGER PRIMARY KEY,
                    embedding FLOAT[{document_embeddings[0].shape[0]}],
                );
            """
        )
        
        with self.db:
            for doc in documents:
                self.db.execute("INSERT INTO documents(text) VALUES(?)", [doc])
        
        with self.db:
            document_rows = self.db.execute("SELECT id, text FROM documents").fetchall()
            for row in document_rows:
                doc_id, doc_text = row
                self.guardar_chunk(doc_text, doc_id)

        queries_con_pais = self.get_travel_queries(pais)

        for query in queries_con_pais:
            response = self.ask_question(query["query"])  # Extrae la consulta del diccionario
            self.responses.append({"id": query["id"], "query": query["query"], "response": response})

        return self.responses

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

    def extraer_contenido_pdf_informacion(self, url: str):#Lo saca separando por contenido
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

            return pdf_text
        except requests.exceptions.RequestException as e:
            return f'Error al realizar la solicitud HTTP: {e}'

    def extraer_contenido_recomendacion_viaje(self, url: str):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            div_principal = soup.find('div', id='ctl00_ctl48_g_b1cd54bc_3d61_4c2b_a319_b305ee4143d3')
            secciones = []
            for section in div_principal.find_all("div", class_="single__text panel ltr-text"):
              contenido = section.get_text(separator='\n', strip=False)
              secciones.append(contenido)
            return secciones
        except requests.exceptions.RequestException as e:
            return f'Error al realizar la solicitud HTTP: {e}'

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="RAG")
#     parser.add_argument("pais", type=str, help="País")
#     args = parser.parse_args()

#     # query_rag = QueryRAG()
#     embedder = Embedder("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")

#     respuestas = embedder.rag_pais(args.pais)
#     for res in respuestas:
#       print(res)
