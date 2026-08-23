from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import time

# Inicializamos la aplicación FastAPI
app = FastAPI()

# Configuramos CORS para permitir que tu frontend en GitHub Pages
# pueda comunicarse con este servidor sin ser bloqueado por el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credenciales de Supabase
# IMPORTANTE: Reemplazar con las que obtuviste del panel Settings > API
SUPABASE_URL = "https://pjhjcaznmyeeinvrftde.supabase.co"
SUPABASE_KEY = "sb_publishable_mCDAE9iyg5QYLCzosksHvA_XoqOR9vv"

# Conexión con Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- ENDPOINTS DE LA APLICACIÓN ---

@app.get("/api/medidores/{id_medidor}")
async def obtener_medidor(id_medidor: int):
    """
    Recibe el número del código de barras escaneado por el operario
    y devuelve el nombre del lote asociado buscando en la tabla 'medidores'.
    """
    try:
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
    """
    Recibe el ID, el consumo y el archivo de imagen desde el celular.
    Sube la foto al storage de Supabase y guarda el registro en la tabla 'lecturas'.
    (La fecha se carga sola en PostgreSQL gracias a la función now() que configuramos).
    """
    try:
        # 1. Leemos los bytes de la foto que mandó el celular
        file_bytes = await foto.read()
        
        # 2. Generamos un nombre único para la imagen
        timestamp = int(time.time())
        nombre_archivo = f"{id_medidor}_{timestamp}.jpg"
        
        # 3. Subimos la foto al bucket
        supabase.storage.from_("evidencias_medidores").upload(nombre_archivo, file_bytes)
        
        # 4. Obtenemos la URL pública para poder verla desde el panel de admin
        public_url = supabase.storage.from_("evidencias_medidores").get_public_url(nombre_archivo)

        # 5. Insertamos los datos en la tabla 'lecturas'
        datos_insert = {
            "id_medidor": id_medidor,
            "valor_lectura": valor,
            "ruta_evidencia": public_url
        }
        supabase.table("lecturas").insert(datos_insert).execute()

        return {"status": "success", "mensaje": "Lectura registrada con foto"}

    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


@app.get("/api/lecturas")
async def listar_lecturas():
    """
    Devuelve el historial usando la vista de PostgreSQL 
    que ya calcula el consumo neto contra el mes anterior.
    """
    try:
        response = supabase.table("vista_consumos").select("*").order("fecha_lectura", desc=True).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}