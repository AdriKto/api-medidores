from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credenciales de Supabase (Reemplazar por las tuyas)
SUPABASE_URL = "https://pjhjcaznmyeeinvrftde.supabase.co"
SUPABASE_KEY = "sb_publishable_mCDAE9iyg5QYLCzosksHvA_XoqOR9vv"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/api/medidores/{id_medidor}")
async def obtener_medidor(id_medidor: int):
    """Consulta de qué lote es el medidor escaneado"""
    try:
        # Busca en la tabla 'medidores' de Supabase
        response = supabase.table("medidores").select("lote").eq("id", id_medidor).execute()
        
        datos = response.data
        if not datos:
            return {"status": "error", "mensaje": "Medidor no encontrado en la base de datos"}
            
        return {"status": "success", "lote": datos[0]["lote"]}

    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


@app.post("/api/lecturas")
async def guardar_lectura(
    id_medidor: int = Form(...),
    valor: float = Form(...),
    foto: UploadFile = File(...)
):
    """Guarda la lectura y sube la foto a Supabase"""
    try:
        file_bytes = await foto.read()
        
        timestamp = int(time.time())
        nombre_archivo = f"{id_medidor}_{timestamp}.jpg"
        
        # Sube al bucket 'evidencias_medidores'
        supabase.storage.from_("evidencias_medidores").upload(nombre_archivo, file_bytes)
        
        # Obtener la URL pública de la imagen
        public_url = supabase.storage.from_("evidencias_medidores").get_public_url(nombre_archivo)

        # Insertar el registro en la tabla de PostgreSQL en Supabase
        datos_insert = {
            "id_medidor": id_medidor,
            "valor_lectura": valor,
            "ruta_evidencia": public_url
        }
        supabase.table("lecturas").insert(datos_insert).execute()

        return {"status": "success", "mensaje": "Lectura registrada con foto"}

    except Exception as e:
        return {"status": "error", "mensaje": str(e)}