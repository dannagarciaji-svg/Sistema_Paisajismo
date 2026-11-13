# ============================================================
#  Configuración central de la conexión a MongoDB Atlas
#  Sistema de Gestión de Servicios de Paisajismo
# ============================================================
import os

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

# Carga las variables del archivo .env ubicado en la raíz del proyecto.
# El archivo .env está excluido del repositorio mediante .gitignore.
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RAIZ_PROYECTO, ".env"))

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "jardineria_db")

if not MONGO_URI:
    raise RuntimeError(
        "No se encontró la variable MONGO_URI. "
        "Cree un archivo .env en la raíz del proyecto a partir de .env.example."
    )

# Cliente único reutilizado por toda la aplicación (patrón Singleton).
client = MongoClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=15000,
    appname="SistemaPaisajismo",
)

db = client[MONGO_DB]

# Colecciones del dominio
clientes = db["clientes"]
propiedades = db["propiedades"]
servicios_contratos = db["servicios_contratos"]
personal = db["personal"]
visitas_mantenimiento = db["visitas_mantenimiento"]
insumos = db["insumos"]

COLECCIONES = {
    "clientes": clientes,
    "propiedades": propiedades,
    "servicios_contratos": servicios_contratos,
    "personal": personal,
    "visitas_mantenimiento": visitas_mantenimiento,
    "insumos": insumos,
}


def verificar_conexion():
    """Ejecuta un ping contra el clúster y devuelve True si responde."""
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
