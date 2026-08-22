# Guarda este archivo como main.py
# Requiere: pip install fastapi uvicorn python-multipart pyodbc

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import time
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credenciales de Supabase
SUPABASE_URL = "TU_URL_DE_SUPABASE"
SUPABASE_KEY = "TU_API_KEY_ANON"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/api/lecturas")
async def guardar_lectura(
    id_medidor: int = Form(...),
    valor: float = Form(...),
    foto: UploadFile = File(...)
):
    try:
        # 1. Leer el archivo recibido
        file_bytes = await foto.read()
        
        # 2. Subir la imagen al Storage de Supabase
        timestamp = int(time.time())
        nombre_archivo = f"{id_medidor}_{timestamp}.jpg"
        
        # Sube al bucket 'evidencias_medidores'
        supabase.storage.from_("evidencias_medidores").upload(nombre_archivo, file_bytes)
        
        # Obtener la URL pública de la imagen
        public_url = supabase.storage.from_("evidencias_medidores").get_public_url(nombre_archivo)

        # 3. Insertar el registro en la tabla de PostgreSQL en Supabase
        datos_insert = {
            "id_medidor": id_medidor,
            "valor_lectura": valor,
            "ruta_evidencia": public_url
        }
        supabase.table("lecturas").insert(datos_insert).execute()

        return {"status": "success", "mensaje": "Lectura registrada con foto"}

    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

# Para ejecutar localmente mientras pruebas: uvicorn main:app --reload