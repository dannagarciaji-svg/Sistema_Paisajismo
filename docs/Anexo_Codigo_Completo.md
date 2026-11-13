# Anexo A — Código fuente completo

**Proyecto:** Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico

**Autora:** Danna Paulina García Jiménez

**Asignatura:** Bases de Datos II

**Generado:** 13/11/2026 00:07

Este anexo reúne, en orden de ejecución, todo el código que compone el sistema: el backend en Flask, la conexión con MongoDB Atlas, los seis módulos CRUD, las cinco consultas analíticas, el frontend en HTML/CSS/JavaScript, la semilla de datos, las pruebas y los archivos de despliegue.

> Las credenciales reales no se incluyen. La cadena de conexión se configura mediante la variable de entorno `MONGO_URI`, tal como se explica en el capítulo 6 del documento técnico.

## Índice de archivos

| # | Archivo | Contenido |
|---|---|---|
| 1 | `app.py` | Punto de entrada de Flask |
| 2 | `backend/config.py` | Conexión a MongoDB Atlas |
| 3 | `backend/utils.py` | Utilidades compartidas |
| 4 | `backend/validators.py` | Validaciones y reglas de negocio |
| 5 | `backend/inventario.py` | Control automático de inventario |
| 6 | `backend/routes/clientes.py` | CRUD de clientes |
| 7 | `backend/routes/propiedades.py` | CRUD de propiedades |
| 8 | `backend/routes/servicios_contratos.py` | CRUD de servicios y contratos |
| 9 | `backend/routes/personal.py` | CRUD de personal |
| 10 | `backend/routes/visitas_mantenimiento.py` | CRUD de visitas de mantenimiento |
| 11 | `backend/routes/insumos.py` | CRUD de insumos |
| 12 | `backend/routes/analitica.py` | Consultas analíticas (Aggregation Pipeline) |
| 13 | `frontend/index.html` | Interfaz web (HTML) |
| 14 | `frontend/css/estilos.css` | Interfaz web (CSS) |
| 15 | `frontend/js/api.js` | Cliente HTTP y utilidades del frontend |
| 16 | `frontend/js/formularios.js` | Formularios del frontend |
| 17 | `frontend/js/vistas.js` | Vistas, tablas y gráficas |
| 18 | `frontend/js/app.js` | Enrutador de la SPA |
| 19 | `seed.py` | Semilla de datos e índices |
| 20 | `pruebas/smoke_test.py` | Pruebas automatizadas |
| 21 | `requirements.txt` | Dependencias de producción |
| 22 | `requirements-dev.txt` | Dependencias de desarrollo |
| 23 | `Procfile` | Comando de arranque |
| 24 | `render.yaml` | Infraestructura como código |
| 25 | `.env.example` | Plantilla de variables de entorno |
| 26 | `.gitignore` | Exclusión de archivos sensibles |
| 27 | `docs/generar_diagramas.py` | Generador de diagramas |
| 28 | `docs/generar_docx.py` | Generador del documento técnico |

---

## A.1 Punto de entrada de Flask

**Archivo:** `app.py` · **106 líneas**

Crea la aplicación, registra los blueprints, expone /api/health y centraliza el manejo de errores.

```python
# ============================================================
#  Punto de entrada de la aplicación Flask
#  Sistema de Gestión de Servicios de Paisajismo
# ============================================================
import logging

from flask import Flask, jsonify, request, send_from_directory
from pymongo.errors import PyMongoError

from backend.config import COLECCIONES, MONGO_DB, verificar_conexion
from backend.routes.analitica import analitica_bp
from backend.routes.clientes import clientes_bp
from backend.routes.insumos import insumos_bp
from backend.routes.personal import personal_bp
from backend.routes.propiedades import propiedades_bp
from backend.routes.servicios_contratos import servicios_contratos_bp
from backend.routes.visitas_mantenimiento import visitas_mantenimiento_bp
from backend.utils import ErrorApi

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def crear_app():
    app = Flask(__name__, static_folder="frontend", static_url_path="/static")
    app.config["JSON_SORT_KEYS"] = False

    # Registro de los seis módulos CRUD + módulo analítico
    for blueprint in (
        clientes_bp,
        propiedades_bp,
        servicios_contratos_bp,
        personal_bp,
        visitas_mantenimiento_bp,
        insumos_bp,
        analitica_bp,
    ):
        app.register_blueprint(blueprint)

    @app.route("/")
    def inicio():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/api/health", methods=["GET"])
    def salud():
        conectado = verificar_conexion()
        conteos = {}
        if conectado:
            try:
                conteos = {nombre: coleccion.count_documents({}) for nombre, coleccion in COLECCIONES.items()}
            except PyMongoError:
                conectado = False
        return (
            jsonify(
                {
                    "estado": "ok" if conectado else "degradado",
                    "base_de_datos": MONGO_DB,
                    "colecciones": conteos,
                }
            ),
            200 if conectado else 503,
        )

    @app.errorhandler(ErrorApi)
    def manejar_error_api(error):
        cuerpo = {"error": error.mensaje}
        if error.campos:
            cuerpo["detalles"] = error.campos
        return jsonify(cuerpo), error.codigo

    @app.errorhandler(PyMongoError)
    def manejar_error_mongo(error):
        app.logger.exception("Error de MongoDB: %s", error)
        return (
            jsonify({"error": "No fue posible comunicarse con la base de datos en la nube."}),
            503,
        )

    @app.errorhandler(404)
    def no_encontrado(error):
        if request.path.startswith("/static/"):
            return jsonify({"error": "Recurso estático no encontrado."}), 404
        return jsonify({"error": "Ruta no encontrada."}), 404

    @app.errorhandler(405)
    def metodo_no_permitido(error):
        return jsonify({"error": "Método HTTP no permitido para esta ruta."}), 405

    @app.errorhandler(Exception)
    def error_no_controlado(error):
        app.logger.exception("Error no controlado: %s", error)
        return jsonify({"error": "Ocurrió un error interno en el servidor."}), 500

    @app.after_request
    def cabeceras_seguridad(respuesta):
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "SAMEORIGIN"
        respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return respuesta

    return app


app = crear_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
```

---

## A.2 Conexión a MongoDB Atlas

**Archivo:** `backend/config.py` · **59 líneas**

Lee las variables de entorno y crea el cliente único de PyMongo y las seis colecciones.

```python
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
```

---

## A.3 Utilidades compartidas

**Archivo:** `backend/utils.py` · **71 líneas**

Serialización de ObjectId/fechas, respuestas JSON y conversión segura de identificadores.

```python
# ============================================================
#  Utilidades comunes: serialización, ObjectId y errores API
# ============================================================
import re
from datetime import date, datetime, timezone

from bson import ObjectId
from flask import jsonify


class ErrorApi(Exception):
    """Excepción controlada que se traduce en una respuesta JSON."""

    def __init__(self, mensaje, codigo=400, campos=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.campos = campos or []


def serializar(valor):
    """Convierte ObjectId y fechas de BSON a tipos serializables en JSON."""
    if isinstance(valor, ObjectId):
        return str(valor)
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {clave: serializar(contenido) for clave, contenido in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [serializar(elemento) for elemento in valor]
    return valor


def serializar_documento(documento):
    """Serializa un documento de MongoDB y normaliza su _id a texto."""
    return serializar(documento)


def respuesta(datos=None, mensaje=None, codigo=200):
    cuerpo = {}
    if datos is not None:
        cuerpo["datos"] = datos
    if mensaje:
        cuerpo["mensaje"] = mensaje
    return jsonify(cuerpo), codigo


def convertir_object_id(valor, nombre_campo="id", codigo=400):
    """Valida y convierte un identificador a ObjectId."""
    if not isinstance(valor, str) or not ObjectId.is_valid(valor):
        raise ErrorApi(f"El campo '{nombre_campo}' no contiene un ObjectId válido.", codigo)
    return ObjectId(valor)


def escapar_regex(texto):
    """Escapa caracteres especiales antes de utilizarlo en una expresión regular."""
    return re.escape(texto)


def texto_busqueda(texto, maximo=80):
    """Normaliza y limita un término de búsqueda recibido por query string."""
    if not texto:
        return None
    limpio = str(texto).strip()
    if not limpio:
        return None
    return limpio[:maximo]
```

---

## A.4 Validaciones y reglas de negocio

**Archivo:** `backend/validators.py` · **235 líneas**

Funciones de validación de texto, correo, teléfono, documento, fechas, enums y estado de insumos.

```python
# ============================================================
#  Validaciones y reglas de negocio compartidas
# ============================================================
import re
from datetime import datetime, timezone

from backend.utils import ErrorApi

CORREO_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
TELEFONO_RE = re.compile(r"^[0-9+\s()-]{7,20}$")
DOCUMENTO_RE = re.compile(r"^[0-9]{6,15}$")

ESTADOS_CLIENTE = ["Activo", "Inactivo"]
ESTADOS_PERSONAL = ["Activo", "Inactivo"]
ESTADOS_CONTRATO = ["Activo", "Suspendido", "Finalizado", "Vencido"]
ESTADOS_VISITA = ["Programada", "En proceso", "Finalizada", "Cancelada"]
ESTADOS_INSUMO = ["Disponible", "Bajo stock", "Agotado"]
TIPOS_PROPIEDAD = ["Casa", "Finca", "Apartamento", "Oficina", "Conjunto residencial", "Parque"]
CARGOS_PERSONAL = ["Jardinero", "Paisajista", "Especialista botánico", "Supervisor", "Auxiliar de jardinería"]
UNIDADES_MEDIDA = ["Kilogramos", "Litros", "Unidades", "Bultos", "Metros", "Mililitros"]


def limpiar_texto(valor):
    if valor is None:
        return None
    return str(valor).strip()


def _agregar_error(errores, campo, mensaje):
    errores.append(f"{campo}: {mensaje}")


def validar_campos_requeridos(datos, campos):
    errores = []
    for campo in campos:
        valor = datos.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()) or (isinstance(valor, list) and not valor):
            _agregar_error(errores, campo, "es obligatorio")
    if errores:
        raise ErrorApi("Datos incompletos.", 400, errores)


def texto(datos, campo, requerido=True, minimo=1, maximo=150, errores=None):
    valor = limpiar_texto(datos.get(campo))
    if not valor:
        if requerido:
            raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400, [f"{campo}: es obligatorio"])
        return None
    if len(valor) < minimo or len(valor) > maximo:
        raise ErrorApi(
            f"El campo '{campo}' debe tener entre {minimo} y {maximo} caracteres.",
            400,
            [f"{campo}: longitud inválida"],
        )
    return valor


def correo(datos, campo="correo", requerido=True):
    valor = texto(datos, campo, requerido=requerido, maximo=120)
    if valor is None:
        return None
    if not CORREO_RE.match(valor):
        raise ErrorApi(f"El campo '{campo}' no tiene un formato de correo válido.", 400)
    return valor.lower()


def telefono(datos, campo="telefono", requerido=True):
    valor = texto(datos, campo, requerido=requerido, maximo=20)
    if valor is None:
        return None
    if not TELEFONO_RE.match(valor):
        raise ErrorApi(f"El campo '{campo}' no tiene un formato de teléfono válido.", 400)
    return valor


def documento(datos, campo="documento", requerido=True):
    valor = texto(datos, campo, requerido=requerido, minimo=6, maximo=15)
    if valor is None:
        return None
    if not DOCUMENTO_RE.match(valor):
        raise ErrorApi(f"El campo '{campo}' debe contener entre 6 y 15 dígitos numéricos.", 400)
    return valor


def enumeracion(datos, campo, permitidos, requerido=True, defecto=None):
    valor = limpiar_texto(datos.get(campo))
    if not valor:
        if requerido:
            raise ErrorApi(
                f"El campo '{campo}' es obligatorio.",
                400,
                [f"{campo}: valores permitidos: {', '.join(permitidos)}"],
            )
        return defecto
    if valor not in permitidos:
        raise ErrorApi(
            f"El valor de '{campo}' no es válido.",
            400,
            [f"{campo}: debe ser uno de {', '.join(permitidos)}"],
        )
    return valor


def numero_positivo(datos, campo, requerido=True, permitir_cero=False):
    valor = datos.get(campo)
    if valor is None or valor == "":
        if requerido:
            raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorApi(f"El campo '{campo}' debe ser un valor numérico.", 400)
    if permitir_cero and valor < 0:
        raise ErrorApi(f"El campo '{campo}' debe ser mayor o igual a cero.", 400)
    if not permitir_cero and valor <= 0:
        raise ErrorApi(f"El campo '{campo}' debe ser mayor que cero.", 400)
    return valor


def entero_no_negativo(datos, campo, requerido=True):
    valor = datos.get(campo)
    if valor is None or valor == "":
        if requerido:
            raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ErrorApi(f"El campo '{campo}' debe ser un número entero mayor o igual a cero.", 400)
    return valor


def fecha(datos, campo, requerido=True):
    valor = datos.get(campo)
    if valor is None or valor == "":
        if requerido:
            raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)
        return None
    if isinstance(valor, datetime):
        resultado = valor
    elif isinstance(valor, str):
        try:
            resultado = datetime.fromisoformat(valor.strip().replace("Z", "+00:00"))
        except ValueError:
            raise ErrorApi(
                f"El campo '{campo}' debe tener formato ISO 8601 (AAAA-MM-DD o AAAA-MM-DDTHH:MM:SS).",
                400,
            )
    else:
        raise ErrorApi(f"El campo '{campo}' debe ser una fecha válida.", 400)

    if resultado.tzinfo is not None:
        resultado = resultado.astimezone(timezone.utc).replace(tzinfo=None)
    return resultado


def lista(datos, campo, requerido=False, permitir_vacia=True):
    valor = datos.get(campo)
    if valor is None:
        if requerido:
            raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)
        return [] if not permitir_vacia else None
    if not isinstance(valor, list):
        raise ErrorApi(f"El campo '{campo}' debe ser una lista.", 400)
    if not permitir_vacia and len(valor) == 0:
        raise ErrorApi(f"El campo '{campo}' debe contener al menos un elemento.", 400)
    return valor


def especies(valor):
    lista_especies = lista({"especies": valor}, "especies", requerido=False) or []
    resultado = []
    for indice, item in enumerate(lista_especies, start=1):
        if not isinstance(item, dict):
            raise ErrorApi(f"La especie #{indice} debe ser un objeto.", 400)
        nombre_comun = limpiar_texto(item.get("nombre_comun"))
        nombre_cientifico = limpiar_texto(item.get("nombre_cientifico"))
        ubicacion = limpiar_texto(item.get("ubicacion"))
        cuidados = limpiar_texto(item.get("necesidades_cuidado"))
        cantidad = item.get("cantidad")
        if not nombre_comun or not nombre_cientifico:
            raise ErrorApi(
                f"La especie #{indice} requiere nombre_comun y nombre_cientifico.", 400
            )
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ErrorApi(f"La cantidad de la especie #{indice} debe ser un entero mayor que cero.", 400)
        resultado.append(
            {
                "nombre_comun": nombre_comun,
                "nombre_cientifico": nombre_cientifico,
                "cantidad": cantidad,
                "ubicacion": ubicacion or "No especificada",
                "necesidades_cuidado": cuidados or "Sin requerimientos registrados",
            }
        )
    return resultado


def servicios(valor):
    lista_servicios = lista({"servicios": valor}, "servicios", requerido=False) or []
    resultado = []
    for indice, item in enumerate(lista_servicios, start=1):
        if not isinstance(item, dict):
            raise ErrorApi(f"El servicio #{indice} debe ser un objeto.", 400)
        nombre = limpiar_texto(item.get("nombre"))
        descripcion = limpiar_texto(item.get("descripcion"))
        precio = item.get("precio_acordado")
        if not nombre:
            raise ErrorApi(f"El servicio #{indice} requiere un nombre.", 400)
        if isinstance(precio, bool) or not isinstance(precio, (int, float)) or precio <= 0:
            raise ErrorApi(f"El precio del servicio #{indice} debe ser mayor que cero.", 400)
        resultado.append(
            {
                "nombre": nombre,
                "descripcion": descripcion or "Sin descripción",
                "precio_acordado": precio,
            }
        )
    return resultado


def especialidades(valor):
    lista_especialidades = lista({"especialidades": valor}, "especialidades", requerido=False) or []
    resultado = []
    for indice, item in enumerate(lista_especialidades, start=1):
        texto_item = limpiar_texto(item)
        if not texto_item:
            raise ErrorApi(f"La especialidad #{indice} no puede estar vacía.", 400)
        resultado.append(texto_item)
    return resultado


def calcular_estado_insumo(existencias, stock_minimo):
    if existencias <= 0:
        return "Agotado"
    if existencias <= stock_minimo:
        return "Bajo stock"
    return "Disponible"
```

---

## A.5 Control automático de inventario

**Archivo:** `backend/inventario.py` · **48 líneas**

Descuenta y restaura existencias de forma atómica al registrar, editar o eliminar visitas.

```python
# ============================================================
#  Control de inventario: descuento y reposición de existencias
# ============================================================
from backend.config import insumos
from backend.utils import ErrorApi


def _pipeline_ajuste(delta):
    return [
        {"$set": {"existencias": {"$add": ["$existencias", delta]}}},
        {
            "$set": {
                "estado": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$existencias", 0]}, "then": "Agotado"},
                            {"case": {"$lte": ["$existencias", "$stock_minimo"]}, "then": "Bajo stock"},
                        ],
                        "default": "Disponible",
                    }
                }
            }
        },
    ]


def ajustar_existencias(insumo_id, delta):
    """
    Ajusta las existencias de un insumo de forma atómica.
    delta negativo = consumo; delta positivo = reposición.
    """
    if delta == 0:
        return

    filtro = {"_id": insumo_id}
    if delta < 0:
        filtro["existencias"] = {"$gte": abs(delta)}

    resultado = insumos.find_one_and_update(
        filtro,
        _pipeline_ajuste(delta),
        return_document=True,
    )
    if resultado is None:
        raise ErrorApi(
            "No hay existencias suficientes del insumo seleccionado para cubrir el consumo.",
            409,
        )
```

---

## A.6 CRUD de clientes

**Archivo:** `backend/routes/clientes.py` · **137 líneas**

Consulta, búsqueda, registro, actualización y eliminación con protección de integridad referencial.

```python
# ============================================================
#  Blueprint: Clientes
# ============================================================
from flask import Blueprint, jsonify, request

from backend.config import clientes, propiedades, servicios_contratos
from backend.utils import (
    ErrorApi,
    convertir_object_id,
    escapar_regex,
    respuesta,
    serializar_documento,
    texto_busqueda,
)
from backend.validators import ESTADOS_CLIENTE, correo, documento, enumeracion, telefono, texto

clientes_bp = Blueprint("clientes", __name__)

CAMPOS_EDITABLES = ["nombre", "documento", "telefono", "correo", "direccion", "estado"]


def _construir_filtros():
    filtros = {}
    busqueda = texto_busqueda(request.args.get("q"))
    if busqueda:
        patron = escapar_regex(busqueda)
        filtros["$or"] = [
            {"nombre": {"$regex": patron, "$options": "i"}},
            {"documento": {"$regex": patron, "$options": "i"}},
            {"correo": {"$regex": patron, "$options": "i"}},
            {"direccion": {"$regex": patron, "$options": "i"}},
        ]
    estado = texto_busqueda(request.args.get("estado"))
    if estado:
        filtros["estado"] = estado
    return filtros


def _validar_cuerpo(datos, parcial=False):
    if not isinstance(datos, dict) or not datos:
        raise ErrorApi("El cuerpo de la solicitud debe ser un objeto JSON con datos.", 400)

    if not parcial:
        for campo in ["nombre", "documento", "telefono", "correo", "direccion"]:
            if campo not in datos:
                raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)

    limpio = {}
    if "nombre" in datos:
        limpio["nombre"] = texto(datos, "nombre", maximo=120)
    if "documento" in datos:
        limpio["documento"] = documento(datos)
    if "telefono" in datos:
        limpio["telefono"] = telefono(datos)
    if "correo" in datos:
        limpio["correo"] = correo(datos)
    if "direccion" in datos:
        limpio["direccion"] = texto(datos, "direccion", maximo=180)
    if "estado" in datos or not parcial:
        limpio["estado"] = enumeracion(datos, "estado", ESTADOS_CLIENTE, requerido=False, defecto="Activo")
    return limpio


@clientes_bp.route("/clientes", methods=["GET"])
def consultar_clientes():
    filtros = _construir_filtros()
    lista = [serializar_documento(c) for c in clientes.find(filtros).sort("nombre", 1)]
    return jsonify({"datos": lista, "total": len(lista)}), 200


@clientes_bp.route("/clientes/<id_cliente>", methods=["GET"])
def consultar_cliente(id_cliente):
    cliente = clientes.find_one({"_id": convertir_object_id(id_cliente, "id_cliente")})
    if cliente is None:
        raise ErrorApi("Cliente no encontrado.", 404)
    return jsonify({"datos": serializar_documento(cliente)}), 200


@clientes_bp.route("/clientes", methods=["POST"])
def registrar_cliente():
    datos = _validar_cuerpo(request.get_json(silent=True))

    if clientes.find_one({"documento": datos["documento"]}):
        raise ErrorApi("Ya existe un cliente con ese número de documento.", 409)

    resultado = clientes.insert_one(datos)
    return (
        jsonify(
            {
                "mensaje": "Cliente registrado correctamente.",
                "id": str(resultado.inserted_id),
            }
        ),
        201,
    )


@clientes_bp.route("/clientes/<id_cliente>", methods=["PUT"])
def actualizar_cliente(id_cliente):
    object_id = convertir_object_id(id_cliente, "id_cliente")
    datos = _validar_cuerpo(request.get_json(silent=True), parcial=True)

    if not datos:
        raise ErrorApi("No se enviaron campos válidos para actualizar.", 400)

    if "documento" in datos:
        duplicado = clientes.find_one({"documento": datos["documento"], "_id": {"$ne": object_id}})
        if duplicado:
            raise ErrorApi("Ya existe otro cliente con ese número de documento.", 409)

    resultado = clientes.update_one({"_id": object_id}, {"$set": datos})
    if resultado.matched_count == 0:
        raise ErrorApi("Cliente no encontrado.", 404)
    return jsonify({"mensaje": "Cliente actualizado correctamente."}), 200


@clientes_bp.route("/clientes/<id_cliente>", methods=["DELETE"])
def eliminar_cliente(id_cliente):
    object_id = convertir_object_id(id_cliente, "id_cliente")

    if propiedades.count_documents({"cliente_id": object_id}) > 0:
        raise ErrorApi(
            "No se puede eliminar el cliente porque tiene propiedades asociadas. "
            "Elimine o reasigne primero sus propiedades.",
            409,
        )
    if servicios_contratos.count_documents({"cliente_id": object_id}) > 0:
        raise ErrorApi(
            "No se puede eliminar el cliente porque tiene contratos asociados. "
            "Elimine primero sus contratos.",
            409,
        )

    resultado = clientes.delete_one({"_id": object_id})
    if resultado.deleted_count == 0:
        raise ErrorApi("Cliente no encontrado.", 404)
    return jsonify({"mensaje": "Cliente eliminado correctamente."}), 200
```

---

## A.7 CRUD de propiedades

**Archivo:** `backend/routes/propiedades.py` · **187 líneas**

Gestión de predios con inventario botánico embebido y validación del cliente asociado.

```python
# ============================================================
#  Blueprint: Propiedades y control botánico
# ============================================================
from flask import Blueprint, jsonify, request

from backend.config import clientes, propiedades, visitas_mantenimiento
from backend.utils import (
    ErrorApi,
    convertir_object_id,
    escapar_regex,
    serializar_documento,
    texto_busqueda,
)
from backend.validators import TIPOS_PROPIEDAD, enumeracion, especies, numero_positivo, texto

propiedades_bp = Blueprint("propiedades", __name__)


def _cliente_existe(cliente_id):
    if clientes.find_one({"_id": cliente_id}, {"_id": 1}) is None:
        raise ErrorApi("El cliente relacionado no existe.", 404)


def _validar_cuerpo(datos, parcial=False):
    if not isinstance(datos, dict) or not datos:
        raise ErrorApi("El cuerpo de la solicitud debe ser un objeto JSON con datos.", 400)

    if not parcial:
        for campo in ["cliente_id", "nombre", "direccion", "ciudad", "tipo_propiedad", "area_m2"]:
            if campo not in datos:
                raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)

    limpio = {}
    if "cliente_id" in datos:
        cliente_id = convertir_object_id(datos.get("cliente_id"), "cliente_id")
        _cliente_existe(cliente_id)
        limpio["cliente_id"] = cliente_id
    if "nombre" in datos:
        limpio["nombre"] = texto(datos, "nombre", maximo=120)
    if "direccion" in datos:
        limpio["direccion"] = texto(datos, "direccion", maximo=180)
    if "ciudad" in datos:
        limpio["ciudad"] = texto(datos, "ciudad", maximo=80)
    if "tipo_propiedad" in datos:
        limpio["tipo_propiedad"] = enumeracion(datos, "tipo_propiedad", TIPOS_PROPIEDAD)
    if "area_m2" in datos:
        limpio["area_m2"] = numero_positivo(datos, "area_m2")
    if "especies" in datos:
        limpio["especies"] = especies(datos.get("especies"))
    return limpio


@propiedades_bp.route("/propiedades", methods=["GET"])
def consultar_propiedades():
    coincidencias = {}
    busqueda = texto_busqueda(request.args.get("q"))
    if busqueda:
        patron = escapar_regex(busqueda)
        coincidencias["$or"] = [
            {"nombre": {"$regex": patron, "$options": "i"}},
            {"direccion": {"$regex": patron, "$options": "i"}},
            {"ciudad": {"$regex": patron, "$options": "i"}},
            {"especies.nombre_comun": {"$regex": patron, "$options": "i"}},
            {"especies.nombre_cientifico": {"$regex": patron, "$options": "i"}},
        ]
    for campo in ["ciudad", "tipo_propiedad"]:
        valor = texto_busqueda(request.args.get(campo))
        if valor:
            coincidencias[campo] = valor
    cliente_id = texto_busqueda(request.args.get("cliente_id"))
    if cliente_id:
        coincidencias["cliente_id"] = convertir_object_id(cliente_id, "cliente_id")

    pipeline = [
        {"$match": coincidencias} if coincidencias else {"$match": {}},
        {
            "$lookup": {
                "from": "clientes",
                "localField": "cliente_id",
                "foreignField": "_id",
                "as": "cliente",
            }
        },
        {"$unwind": {"path": "$cliente", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "visitas_mantenimiento",
                "localField": "_id",
                "foreignField": "propiedad_id",
                "as": "visitas",
            }
        },
        {
            "$addFields": {
                "cliente_nombre": {"$ifNull": ["$cliente.nombre", "Cliente no disponible"]},
                "cliente_documento": {"$ifNull": ["$cliente.documento", ""]},
                "total_visitas": {"$size": "$visitas"},
                "total_especies": {"$size": {"$ifNull": ["$especies", []]}},
            }
        },
        {"$project": {"cliente": 0, "visitas": 0}},
        {"$sort": {"nombre": 1}},
    ]

    lista = [serializar_documento(p) for p in propiedades.aggregate(pipeline)]
    return jsonify({"datos": lista, "total": len(lista)}), 200


@propiedades_bp.route("/propiedades/<id_propiedad>", methods=["GET"])
def consultar_propiedad(id_propiedad):
    propiedad = propiedades.find_one({"_id": convertir_object_id(id_propiedad, "id_propiedad")})
    if propiedad is None:
        raise ErrorApi("Propiedad no encontrada.", 404)
    return jsonify({"datos": serializar_documento(propiedad)}), 200


@propiedades_bp.route("/propiedades/<id_propiedad>/historial", methods=["GET"])
def consultar_historial_propiedad(id_propiedad):
    object_id = convertir_object_id(id_propiedad, "id_propiedad")
    if propiedades.find_one({"_id": object_id}, {"_id": 1}) is None:
        raise ErrorApi("Propiedad no encontrada.", 404)

    pipeline = [
        {"$match": {"propiedad_id": object_id}},
        {"$sort": {"fecha_programada": -1}},
        {
            "$lookup": {
                "from": "servicios_contratos",
                "localField": "contrato_id",
                "foreignField": "_id",
                "as": "contrato",
            }
        },
        {"$unwind": {"path": "$contrato", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "contrato_estado": {"$ifNull": ["$contrato.estado", "No disponible"]},
                "servicios_contratados": {
                    "$ifNull": ["$contrato.servicios.nombre", []]
                },
            }
        },
        {"$project": {"contrato": 0}},
    ]
    historial = [serializar_documento(v) for v in visitas_mantenimiento.aggregate(pipeline)]
    return jsonify({"datos": historial, "total": len(historial)}), 200


@propiedades_bp.route("/propiedades", methods=["POST"])
def registrar_propiedad():
    datos = _validar_cuerpo(request.get_json(silent=True))
    datos.setdefault("especies", [])
    resultado = propiedades.insert_one(datos)
    return (
        jsonify({"mensaje": "Propiedad registrada correctamente.", "id": str(resultado.inserted_id)}),
        201,
    )


@propiedades_bp.route("/propiedades/<id_propiedad>", methods=["PUT"])
def actualizar_propiedad(id_propiedad):
    object_id = convertir_object_id(id_propiedad, "id_propiedad")
    datos = _validar_cuerpo(request.get_json(silent=True), parcial=True)

    if not datos:
        raise ErrorApi("No se enviaron campos válidos para actualizar.", 400)

    resultado = propiedades.update_one({"_id": object_id}, {"$set": datos})
    if resultado.matched_count == 0:
        raise ErrorApi("Propiedad no encontrada.", 404)
    return jsonify({"mensaje": "Propiedad actualizada correctamente."}), 200


@propiedades_bp.route("/propiedades/<id_propiedad>", methods=["DELETE"])
def eliminar_propiedad(id_propiedad):
    object_id = convertir_object_id(id_propiedad, "id_propiedad")

    if visitas_mantenimiento.count_documents({"propiedad_id": object_id}) > 0:
        raise ErrorApi(
            "No se puede eliminar la propiedad porque tiene visitas de mantenimiento asociadas.",
            409,
        )

    resultado = propiedades.delete_one({"_id": object_id})
    if resultado.deleted_count == 0:
        raise ErrorApi("Propiedad no encontrada.", 404)
    return jsonify({"mensaje": "Propiedad eliminada correctamente."}), 200
```

---

## A.8 CRUD de servicios y contratos

**Archivo:** `backend/routes/servicios_contratos.py` · **181 líneas**

Contratos con servicios embebidos, cálculo de valor_total y validación de fechas y estado.

```python
# ============================================================
#  Blueprint: Servicios y Contratos
# ============================================================
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.config import clientes, servicios_contratos, visitas_mantenimiento
from backend.utils import (
    ErrorApi,
    convertir_object_id,
    escapar_regex,
    serializar_documento,
    texto_busqueda,
)
from backend.validators import ESTADOS_CONTRATO, enumeracion, fecha, servicios

servicios_contratos_bp = Blueprint("servicios_contratos", __name__)


def _validar_fechas(fecha_inicio, fecha_fin):
    if fecha_fin <= fecha_inicio:
        raise ErrorApi("La fecha de finalización debe ser posterior a la fecha de inicio.", 400)


def _validar_cuerpo(datos, parcial=False, documento_actual=None):
    if not isinstance(datos, dict) or not datos:
        raise ErrorApi("El cuerpo de la solicitud debe ser un objeto JSON con datos.", 400)

    if not parcial:
        for campo in ["cliente_id", "servicios", "fecha_inicio", "fecha_fin"]:
            if campo not in datos:
                raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)

    limpio = {}
    if "cliente_id" in datos:
        cliente_id = convertir_object_id(datos.get("cliente_id"), "cliente_id")
        if clientes.find_one({"_id": cliente_id}, {"_id": 1}) is None:
            raise ErrorApi("El cliente relacionado no existe.", 404)
        limpio["cliente_id"] = cliente_id

    if "servicios" in datos:
        lista_servicios = servicios(datos.get("servicios"))
        if not lista_servicios:
            raise ErrorApi("El contrato debe incluir al menos un servicio.", 400)
        limpio["servicios"] = lista_servicios
        total_calculado = sum(servicio["precio_acordado"] for servicio in lista_servicios)
        if "valor_total" in datos and abs(float(datos["valor_total"]) - total_calculado) > 0.5:
            raise ErrorApi(
                "El valor total del contrato debe coincidir con la suma de los precios acordados "
                f"de sus servicios (${total_calculado:,.0f}).",
                400,
            )
        limpio["valor_total"] = total_calculado
    elif "valor_total" in datos:
        raise ErrorApi(
            "El valor total se calcula automáticamente a partir de los servicios; "
            "envíe el arreglo 'servicios' para actualizarlo.",
            400,
        )

    fecha_inicio = fecha(datos, "fecha_inicio") if "fecha_inicio" in datos else None
    fecha_fin = fecha(datos, "fecha_fin") if "fecha_fin" in datos else None

    if parcial and (fecha_inicio or fecha_fin):
        actual = documento_actual or {}
        inicio_final = fecha_inicio or actual.get("fecha_inicio")
        fin_final = fecha_fin or actual.get("fecha_fin")
        if inicio_final and fin_final:
            _validar_fechas(inicio_final, fin_final)

    if fecha_inicio is not None:
        limpio["fecha_inicio"] = fecha_inicio
    if fecha_fin is not None:
        limpio["fecha_fin"] = fecha_fin

    if "estado" in datos or not parcial:
        limpio["estado"] = enumeracion(datos, "estado", ESTADOS_CONTRATO, requerido=False, defecto="Activo")

    return limpio


@servicios_contratos_bp.route("/servicios_contratos", methods=["GET"])
def consultar_contratos():
    coincidencias = {}
    busqueda = texto_busqueda(request.args.get("q"))
    if busqueda:
        patron = escapar_regex(busqueda)
        coincidencias["$or"] = [
            {"servicios.nombre": {"$regex": patron, "$options": "i"}},
            {"servicios.descripcion": {"$regex": patron, "$options": "i"}},
        ]
    estado = texto_busqueda(request.args.get("estado"))
    if estado:
        coincidencias["estado"] = estado
    cliente_id = texto_busqueda(request.args.get("cliente_id"))
    if cliente_id:
        coincidencias["cliente_id"] = convertir_object_id(cliente_id, "cliente_id")
    if texto_busqueda(request.args.get("vigente")) == "true":
        ahora = datetime.utcnow()
        coincidencias["estado"] = "Activo"
        coincidencias["fecha_inicio"] = {"$lte": ahora}
        coincidencias["fecha_fin"] = {"$gte": ahora}

    pipeline = [
        {"$match": coincidencias} if coincidencias else {"$match": {}},
        {
            "$lookup": {
                "from": "clientes",
                "localField": "cliente_id",
                "foreignField": "_id",
                "as": "cliente",
            }
        },
        {"$unwind": {"path": "$cliente", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "cliente_nombre": {"$ifNull": ["$cliente.nombre", "Cliente no disponible"]},
                "cliente_documento": {"$ifNull": ["$cliente.documento", ""]},
                "total_servicios": {"$size": {"$ifNull": ["$servicios", []]}},
            }
        },
        {"$project": {"cliente": 0}},
        {"$sort": {"fecha_inicio": -1}},
    ]

    lista = [serializar_documento(c) for c in servicios_contratos.aggregate(pipeline)]
    return jsonify({"datos": lista, "total": len(lista)}), 200


@servicios_contratos_bp.route("/servicios_contratos/<id_contrato>", methods=["GET"])
def consultar_contrato(id_contrato):
    contrato = servicios_contratos.find_one({"_id": convertir_object_id(id_contrato, "id_contrato")})
    if contrato is None:
        raise ErrorApi("Contrato no encontrado.", 404)
    return jsonify({"datos": serializar_documento(contrato)}), 200


@servicios_contratos_bp.route("/servicios_contratos", methods=["POST"])
def registrar_contrato():
    datos = _validar_cuerpo(request.get_json(silent=True))
    _validar_fechas(datos["fecha_inicio"], datos["fecha_fin"])

    resultado = servicios_contratos.insert_one(datos)
    return (
        jsonify({"mensaje": "Contrato registrado correctamente.", "id": str(resultado.inserted_id)}),
        201,
    )


@servicios_contratos_bp.route("/servicios_contratos/<id_contrato>", methods=["PUT"])
def actualizar_contrato(id_contrato):
    object_id = convertir_object_id(id_contrato, "id_contrato")
    actual = servicios_contratos.find_one({"_id": object_id})
    if actual is None:
        raise ErrorApi("Contrato no encontrado.", 404)

    datos = _validar_cuerpo(request.get_json(silent=True), parcial=True, documento_actual=actual)
    if not datos:
        raise ErrorApi("No se enviaron campos válidos para actualizar.", 400)

    resultado = servicios_contratos.update_one({"_id": object_id}, {"$set": datos})
    if resultado.matched_count == 0:
        raise ErrorApi("Contrato no encontrado.", 404)
    return jsonify({"mensaje": "Contrato actualizado correctamente."}), 200


@servicios_contratos_bp.route("/servicios_contratos/<id_contrato>", methods=["DELETE"])
def eliminar_contrato(id_contrato):
    object_id = convertir_object_id(id_contrato, "id_contrato")

    if visitas_mantenimiento.count_documents({"contrato_id": object_id}) > 0:
        raise ErrorApi(
            "No se puede eliminar el contrato porque tiene visitas de mantenimiento asociadas.",
            409,
        )

    resultado = servicios_contratos.delete_one({"_id": object_id})
    if resultado.deleted_count == 0:
        raise ErrorApi("Contrato no encontrado.", 404)
    return jsonify({"mensaje": "Contrato eliminado correctamente."}), 200
```

---

## A.9 CRUD de personal

**Archivo:** `backend/routes/personal.py` · **137 líneas**

Gestión del personal técnico y operativo con documento único y cargos válidos.

```python
# ============================================================
#  Blueprint: Personal técnico y operativo
# ============================================================
from flask import Blueprint, jsonify, request

from backend.config import personal, visitas_mantenimiento
from backend.utils import (
    ErrorApi,
    convertir_object_id,
    escapar_regex,
    serializar_documento,
    texto_busqueda,
)
from backend.validators import (
    CARGOS_PERSONAL,
    ESTADOS_PERSONAL,
    correo,
    documento,
    enumeracion,
    especialidades,
    numero_positivo,
    telefono,
    texto,
)

personal_bp = Blueprint("personal", __name__)


def _validar_cuerpo(datos, parcial=False):
    if not isinstance(datos, dict) or not datos:
        raise ErrorApi("El cuerpo de la solicitud debe ser un objeto JSON con datos.", 400)

    if not parcial:
        for campo in ["nombre", "documento", "telefono", "correo", "cargo"]:
            if campo not in datos:
                raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)

    limpio = {}
    if "nombre" in datos:
        limpio["nombre"] = texto(datos, "nombre", maximo=120)
    if "documento" in datos:
        limpio["documento"] = documento(datos)
    if "telefono" in datos:
        limpio["telefono"] = telefono(datos)
    if "correo" in datos:
        limpio["correo"] = correo(datos)
    if "cargo" in datos:
        limpio["cargo"] = enumeracion(datos, "cargo", CARGOS_PERSONAL)
    if "salario" in datos:
        limpio["salario"] = numero_positivo(datos, "salario", requerido=False, permitir_cero=True)
    if "especialidades" in datos:
        limpio["especialidades"] = especialidades(datos.get("especialidades"))
    if "estado" in datos or not parcial:
        limpio["estado"] = enumeracion(datos, "estado", ESTADOS_PERSONAL, requerido=False, defecto="Activo")
    return limpio


@personal_bp.route("/personal", methods=["GET"])
def consultar_personal():
    filtros = {}
    busqueda = texto_busqueda(request.args.get("q"))
    if busqueda:
        patron = escapar_regex(busqueda)
        filtros["$or"] = [
            {"nombre": {"$regex": patron, "$options": "i"}},
            {"documento": {"$regex": patron, "$options": "i"}},
            {"correo": {"$regex": patron, "$options": "i"}},
            {"especialidades": {"$regex": patron, "$options": "i"}},
        ]
    for campo in ["cargo", "estado"]:
        valor = texto_busqueda(request.args.get(campo))
        if valor:
            filtros[campo] = valor
    especialidad = texto_busqueda(request.args.get("especialidad"))
    if especialidad:
        filtros["especialidades"] = {"$regex": escapar_regex(especialidad), "$options": "i"}

    lista = [serializar_documento(p) for p in personal.find(filtros).sort("nombre", 1)]
    return jsonify({"datos": lista, "total": len(lista)}), 200


@personal_bp.route("/personal/<id_personal>", methods=["GET"])
def consultar_empleado(id_personal):
    empleado = personal.find_one({"_id": convertir_object_id(id_personal, "id_personal")})
    if empleado is None:
        raise ErrorApi("Trabajador no encontrado.", 404)
    return jsonify({"datos": serializar_documento(empleado)}), 200


@personal_bp.route("/personal", methods=["POST"])
def registrar_empleado():
    datos = _validar_cuerpo(request.get_json(silent=True))

    if personal.find_one({"documento": datos["documento"]}):
        raise ErrorApi("Ya existe un trabajador con ese número de documento.", 409)

    resultado = personal.insert_one(datos)
    return (
        jsonify({"mensaje": "Trabajador registrado correctamente.", "id": str(resultado.inserted_id)}),
        201,
    )


@personal_bp.route("/personal/<id_personal>", methods=["PUT"])
def actualizar_empleado(id_personal):
    object_id = convertir_object_id(id_personal, "id_personal")
    datos = _validar_cuerpo(request.get_json(silent=True), parcial=True)

    if not datos:
        raise ErrorApi("No se enviaron campos válidos para actualizar.", 400)

    if "documento" in datos:
        duplicado = personal.find_one({"documento": datos["documento"], "_id": {"$ne": object_id}})
        if duplicado:
            raise ErrorApi("Ya existe otro trabajador con ese número de documento.", 409)

    resultado = personal.update_one({"_id": object_id}, {"$set": datos})
    if resultado.matched_count == 0:
        raise ErrorApi("Trabajador no encontrado.", 404)
    return jsonify({"mensaje": "Trabajador actualizado correctamente."}), 200


@personal_bp.route("/personal/<id_personal>", methods=["DELETE"])
def eliminar_empleado(id_personal):
    object_id = convertir_object_id(id_personal, "id_personal")

    asignado = visitas_mantenimiento.count_documents({"personal_asignado.personal_id": object_id})
    if asignado > 0:
        raise ErrorApi(
            "No se puede eliminar el trabajador porque está asignado a visitas de mantenimiento.",
            409,
        )

    resultado = personal.delete_one({"_id": object_id})
    if resultado.deleted_count == 0:
        raise ErrorApi("Trabajador no encontrado.", 404)
    return jsonify({"mensaje": "Trabajador eliminado correctamente."}), 200
```

---

## A.10 CRUD de visitas de mantenimiento

**Archivo:** `backend/routes/visitas_mantenimiento.py` · **385 líneas**

Entidad transaccional central: reglas de contrato activo, fechas, personal e insumos.

```python
# ============================================================
#  Blueprint: Visitas de mantenimiento
# ============================================================
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.config import (
    insumos,
    personal,
    propiedades,
    servicios_contratos,
    visitas_mantenimiento,
)
from backend.inventario import ajustar_existencias
from backend.utils import (
    ErrorApi,
    convertir_object_id,
    escapar_regex,
    serializar_documento,
    texto_busqueda,
)
from backend.validators import ESTADOS_VISITA, enumeracion, fecha, lista

visitas_mantenimiento_bp = Blueprint("visitas_mantenimiento", __name__)

ESTADOS_SIN_CONSUMO = ["Programada", "Cancelada"]


def _normalizar_personal_asignado(valor):
    lista_personal = lista({"personal_asignado": valor}, "personal_asignado", requerido=True)
    if not lista_personal:
        raise ErrorApi("Debe asignar al menos un trabajador a la visita.", 400)

    normalizado = []
    vistos = set()
    for indice, item in enumerate(lista_personal, start=1):
        if isinstance(item, dict):
            identificador = item.get("personal_id")
        else:
            identificador = item
        object_id = convertir_object_id(identificador, f"personal_asignado[{indice}]")
        clave = str(object_id)
        if clave in vistos:
            raise ErrorApi("No se puede asignar al mismo trabajador más de una vez en la visita.", 400)
        vistos.add(clave)

        empleado = personal.find_one({"_id": object_id})
        if empleado is None:
            raise ErrorApi(f"El trabajador con id {clave} no existe.", 404)
        if empleado.get("estado") != "Activo":
            raise ErrorApi(f"El trabajador {empleado.get('nombre', clave)} no está activo.", 400)
        normalizado.append({"personal_id": object_id, "nombre": empleado.get("nombre", "")})
    return normalizado


def _normalizar_insumos(valor, consumos_previos=None):
    lista_insumos = lista({"insumos_utilizados": valor}, "insumos_utilizados", requerido=False) or []
    normalizado = []
    vistos = set()
    consumos_previos = consumos_previos or {}

    for indice, item in enumerate(lista_insumos, start=1):
        if not isinstance(item, dict):
            raise ErrorApi(f"El insumo #{indice} debe ser un objeto con insumo_id y cantidad.", 400)

        object_id = convertir_object_id(item.get("insumo_id"), f"insumos_utilizados[{indice}].insumo_id")
        clave = str(object_id)
        if clave in vistos:
            raise ErrorApi("Un insumo no puede registrarse dos veces en la misma visita.", 400)
        vistos.add(clave)

        cantidad = item.get("cantidad")
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ErrorApi(f"La cantidad del insumo #{indice} debe ser un entero mayor que cero.", 400)

        insumo = insumos.find_one({"_id": object_id})
        if insumo is None:
            raise ErrorApi(f"El insumo con id {clave} no existe.", 404)

        consumo_previo = consumos_previos.get(clave, 0)
        incremento = cantidad - consumo_previo
        if incremento > insumo.get("existencias", 0):
            raise ErrorApi(
                f"No hay existencias suficientes de '{insumo.get('nombre')}'. "
                f"Disponible: {insumo.get('existencias', 0)} {insumo.get('unidad_medida', '')}, "
                f"requerido adicional: {incremento}.",
                409,
            )

        normalizado.append(
            {
                "insumo_id": object_id,
                "nombre": insumo.get("nombre", ""),
                "cantidad": cantidad,
                "unidad_medida": insumo.get("unidad_medida", ""),
            }
        )
    return normalizado


def _mapa_consumos(visita):
    mapa = {}
    for item in (visita or {}).get("insumos_utilizados", []) or []:
        identificador = item.get("insumo_id")
        if identificador is not None:
            mapa[str(identificador)] = mapa.get(str(identificador), 0) + int(item.get("cantidad", 0))
    return mapa


def _aplicar_deltas_consumo(lista_nueva, consumos_previos):
    """Aplica los deltas de consumo y devuelve los ajustes realizados."""
    aplicados = []
    try:
        for item in lista_nueva:
            clave = str(item["insumo_id"])
            previo = consumos_previos.get(clave, 0)
            delta = item["cantidad"] - previo
            if delta != 0:
                ajustar_existencias(item["insumo_id"], -delta)
                aplicados.append((item["insumo_id"], -delta))
        return aplicados
    except Exception:
        for insumo_id, delta_aplicado in aplicados:
            ajustar_existencias(insumo_id, -delta_aplicado)
        raise


def _validar_estado_consumo(estado, lista_insumos):
    if estado in ESTADOS_SIN_CONSUMO and lista_insumos:
        raise ErrorApi(
            f"Una visita en estado '{estado}' no puede registrar insumos utilizados. "
            "Registre el consumo cuando la visita esté 'En proceso' o 'Finalizada'.",
            400,
        )


def _validar_propiedad_y_contrato(propiedad_id, contrato_id, fecha_programada, exigir_contrato_activo=True):
    propiedad = propiedades.find_one({"_id": propiedad_id})
    if propiedad is None:
        raise ErrorApi("La propiedad relacionada no existe.", 404)

    contrato = servicios_contratos.find_one({"_id": contrato_id})
    if contrato is None:
        raise ErrorApi("El contrato relacionado no existe.", 404)

    if contrato.get("cliente_id") != propiedad.get("cliente_id"):
        raise ErrorApi(
            "El contrato y la propiedad deben pertenecer al mismo cliente.",
            400,
        )

    if exigir_contrato_activo and contrato.get("estado") != "Activo":
        raise ErrorApi("Solo se pueden programar visitas sobre contratos en estado Activo.", 400)

    if not (contrato.get("fecha_inicio") <= fecha_programada <= contrato.get("fecha_fin")):
        raise ErrorApi(
            "La fecha programada debe estar dentro del período de vigencia del contrato "
            f"({contrato.get('fecha_inicio').date()} a {contrato.get('fecha_fin').date()}).",
            400,
        )
    return propiedad, contrato


def _validar_cuerpo(datos, parcial=False, visita_actual=None):
    if not isinstance(datos, dict) or not datos:
        raise ErrorApi("El cuerpo de la solicitud debe ser un objeto JSON con datos.", 400)

    if not parcial:
        for campo in ["propiedad_id", "contrato_id", "fecha_programada", "personal_asignado"]:
            if campo not in datos:
                raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)

    limpio = {}
    if "propiedad_id" in datos:
        limpio["propiedad_id"] = convertir_object_id(datos.get("propiedad_id"), "propiedad_id")
    if "contrato_id" in datos:
        limpio["contrato_id"] = convertir_object_id(datos.get("contrato_id"), "contrato_id")
    if "fecha_programada" in datos:
        limpio["fecha_programada"] = fecha(datos, "fecha_programada")
    if "personal_asignado" in datos:
        limpio["personal_asignado"] = _normalizar_personal_asignado(datos.get("personal_asignado"))
    if "actividades_realizadas" in datos:
        lista(datos, "actividades_realizadas", requerido=False)
        limpio["actividades_realizadas"] = [
            str(a).strip() for a in (datos.get("actividades_realizadas") or []) if str(a).strip()
        ]
    if "observaciones" in datos:
        lista(datos, "observaciones", requerido=False)
        limpio["observaciones"] = [
            str(o).strip() for o in (datos.get("observaciones") or []) if str(o).strip()
        ]
    if "estado" in datos or not parcial:
        limpio["estado"] = enumeracion(datos, "estado", ESTADOS_VISITA, requerido=False, defecto="Programada")

    consumos_previos = _mapa_consumos(visita_actual) if visita_actual else {}
    if "insumos_utilizados" in datos:
        limpio["insumos_utilizados"] = _normalizar_insumos(
            datos.get("insumos_utilizados"), consumos_previos
        )

    estado_final = limpio.get("estado", (visita_actual or {}).get("estado", "Programada"))
    insumos_finales = limpio.get(
        "insumos_utilizados", (visita_actual or {}).get("insumos_utilizados", [])
    )
    _validar_estado_consumo(estado_final, insumos_finales)

    # Validación de coherencia entre propiedad, contrato y fecha (usando valores combinados)
    propiedad_id = limpio.get("propiedad_id", (visita_actual or {}).get("propiedad_id"))
    contrato_id = limpio.get("contrato_id", (visita_actual or {}).get("contrato_id"))
    fecha_programada = limpio.get("fecha_programada", (visita_actual or {}).get("fecha_programada"))
    if propiedad_id and contrato_id and fecha_programada:
        exigir_activo = not parcial or "contrato_id" in limpio
        _validar_propiedad_y_contrato(propiedad_id, contrato_id, fecha_programada, exigir_activo)

    return limpio


def _pipeline_base(match=None):
    pipeline = [{"$match": match or {}}]
    pipeline += [
        {
            "$lookup": {
                "from": "propiedades",
                "localField": "propiedad_id",
                "foreignField": "_id",
                "as": "propiedad",
            }
        },
        {"$unwind": {"path": "$propiedad", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "clientes",
                "localField": "propiedad.cliente_id",
                "foreignField": "_id",
                "as": "cliente",
            }
        },
        {"$unwind": {"path": "$cliente", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "servicios_contratos",
                "localField": "contrato_id",
                "foreignField": "_id",
                "as": "contrato",
            }
        },
        {"$unwind": {"path": "$contrato", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "propiedad_nombre": {"$ifNull": ["$propiedad.nombre", "Propiedad no disponible"]},
                "propiedad_ciudad": {"$ifNull": ["$propiedad.ciudad", ""]},
                "cliente_nombre": {"$ifNull": ["$cliente.nombre", "Cliente no disponible"]},
                "cliente_documento": {"$ifNull": ["$cliente.documento", ""]},
                "contrato_estado": {"$ifNull": ["$contrato.estado", "No disponible"]},
                "servicios_contratados": {"$ifNull": ["$contrato.servicios.nombre", []]},
                "total_personal": {"$size": {"$ifNull": ["$personal_asignado", []]}},
                "total_insumos": {"$size": {"$ifNull": ["$insumos_utilizados", []]}},
            }
        },
        {"$project": {"propiedad": 0, "cliente": 0, "contrato": 0}},
    ]
    return pipeline


@visitas_mantenimiento_bp.route("/visitas_mantenimiento", methods=["GET"])
def consultar_visitas():
    filtros = {}
    busqueda = texto_busqueda(request.args.get("q"))
    if busqueda:
        patron = escapar_regex(busqueda)
        filtros["$or"] = [
            {"actividades_realizadas": {"$regex": patron, "$options": "i"}},
            {"observaciones": {"$regex": patron, "$options": "i"}},
        ]
    estado = texto_busqueda(request.args.get("estado"))
    if estado:
        filtros["estado"] = estado
    for campo in ["propiedad_id", "contrato_id"]:
        valor = texto_busqueda(request.args.get(campo))
        if valor:
            filtros[campo] = convertir_object_id(valor, campo)
    personal_id = texto_busqueda(request.args.get("personal_id"))
    if personal_id:
        filtros["personal_asignado.personal_id"] = convertir_object_id(personal_id, "personal_id")

    rango = {}
    if request.args.get("desde"):
        rango["$gte"] = fecha(request.args, "desde")
    if request.args.get("hasta"):
        rango["$lte"] = fecha(request.args, "hasta")
    if rango:
        filtros["fecha_programada"] = rango

    pipeline = _pipeline_base(filtros)
    pipeline.append({"$sort": {"fecha_programada": -1}})
    lista = [serializar_documento(v) for v in visitas_mantenimiento.aggregate(pipeline)]
    return jsonify({"datos": lista, "total": len(lista)}), 200


@visitas_mantenimiento_bp.route("/visitas_mantenimiento/<id_visita>", methods=["GET"])
def consultar_visita(id_visita):
    object_id = convertir_object_id(id_visita, "id_visita")
    resultado = list(visitas_mantenimiento.aggregate(_pipeline_base({"_id": object_id})))
    if not resultado:
        raise ErrorApi("Visita de mantenimiento no encontrada.", 404)
    return jsonify({"datos": serializar_documento(resultado[0])}), 200


@visitas_mantenimiento_bp.route("/visitas_mantenimiento", methods=["POST"])
def registrar_visita():
    datos = _validar_cuerpo(request.get_json(silent=True))
    datos.setdefault("actividades_realizadas", [])
    datos.setdefault("observaciones", [])
    datos.setdefault("insumos_utilizados", [])

    _validar_propiedad_y_contrato(
        datos["propiedad_id"], datos["contrato_id"], datos["fecha_programada"]
    )

    # Reserva de inventario antes de persistir la visita.
    aplicados = []
    try:
        for item in datos["insumos_utilizados"]:
            ajustar_existencias(item["insumo_id"], -item["cantidad"])
            aplicados.append((item["insumo_id"], -item["cantidad"]))
        resultado = visitas_mantenimiento.insert_one(datos)
    except Exception:
        for insumo_id, delta_aplicado in aplicados:
            ajustar_existencias(insumo_id, -delta_aplicado)
        raise

    return (
        jsonify(
            {
                "mensaje": "Visita de mantenimiento registrada correctamente.",
                "id": str(resultado.inserted_id),
            }
        ),
        201,
    )


@visitas_mantenimiento_bp.route("/visitas_mantenimiento/<id_visita>", methods=["PUT"])
def actualizar_visita(id_visita):
    object_id = convertir_object_id(id_visita, "id_visita")
    actual = visitas_mantenimiento.find_one({"_id": object_id})
    if actual is None:
        raise ErrorApi("Visita de mantenimiento no encontrada.", 404)

    datos = _validar_cuerpo(request.get_json(silent=True), parcial=True, visita_actual=actual)
    if not datos:
        raise ErrorApi("No se enviaron campos válidos para actualizar.", 400)

    consumos_previos = _mapa_consumos(actual)
    aplicados = []
    try:
        if "insumos_utilizados" in datos:
            aplicados = _aplicar_deltas_consumo(datos["insumos_utilizados"], consumos_previos)
        resultado = visitas_mantenimiento.update_one({"_id": object_id}, {"$set": datos})
    except Exception:
        for insumo_id, delta_aplicado in aplicados:
            ajustar_existencias(insumo_id, -delta_aplicado)
        raise

    if resultado.matched_count == 0:
        raise ErrorApi("Visita de mantenimiento no encontrada.", 404)
    return jsonify({"mensaje": "Visita de mantenimiento actualizada correctamente."}), 200


@visitas_mantenimiento_bp.route("/visitas_mantenimiento/<id_visita>", methods=["DELETE"])
def eliminar_visita(id_visita):
    object_id = convertir_object_id(id_visita, "id_visita")
    visita = visitas_mantenimiento.find_one({"_id": object_id})
    if visita is None:
        raise ErrorApi("Visita de mantenimiento no encontrada.", 404)

    visitas_mantenimiento.delete_one({"_id": object_id})

    # Repone al inventario los insumos que había consumido la visita.
    for item in visita.get("insumos_utilizados", []) or []:
        if item.get("insumo_id") is not None:
            ajustar_existencias(item["insumo_id"], int(item.get("cantidad", 0)))

    return jsonify({"mensaje": "Visita de mantenimiento eliminada correctamente."}), 200
```

---

## A.11 CRUD de insumos

**Archivo:** `backend/routes/insumos.py` · **121 líneas**

Inventario de materiales con estado derivado de existencias y stock mínimo.

```python
# ============================================================
#  Blueprint: Insumos e inventario
# ============================================================
from flask import Blueprint, jsonify, request

from backend.config import insumos, visitas_mantenimiento
from backend.utils import (
    ErrorApi,
    convertir_object_id,
    escapar_regex,
    serializar_documento,
    texto_busqueda,
)
from backend.validators import (
    UNIDADES_MEDIDA,
    calcular_estado_insumo,
    entero_no_negativo,
    enumeracion,
    texto,
)

insumos_bp = Blueprint("insumos", __name__)


def _validar_cuerpo(datos, parcial=False, actual=None):
    if not isinstance(datos, dict) or not datos:
        raise ErrorApi("El cuerpo de la solicitud debe ser un objeto JSON con datos.", 400)

    if not parcial:
        for campo in ["nombre", "unidad_medida", "existencias", "stock_minimo"]:
            if campo not in datos:
                raise ErrorApi(f"El campo '{campo}' es obligatorio.", 400)

    limpio = {}
    if "nombre" in datos:
        limpio["nombre"] = texto(datos, "nombre", maximo=120)
    if "descripcion" in datos:
        limpio["descripcion"] = texto(datos, "descripcion", requerido=False, maximo=250) or ""
    if "unidad_medida" in datos:
        limpio["unidad_medida"] = enumeracion(datos, "unidad_medida", UNIDADES_MEDIDA)
    if "existencias" in datos:
        limpio["existencias"] = entero_no_negativo(datos, "existencias")
    if "stock_minimo" in datos:
        limpio["stock_minimo"] = entero_no_negativo(datos, "stock_minimo")

    # El estado nunca se recibe del usuario: se deriva de las existencias y el stock mínimo.
    existencias = limpio.get("existencias", (actual or {}).get("existencias", 0))
    stock_minimo = limpio.get("stock_minimo", (actual or {}).get("stock_minimo", 0))
    limpio["estado"] = calcular_estado_insumo(existencias, stock_minimo)
    return limpio


@insumos_bp.route("/insumos", methods=["GET"])
def consultar_insumos():
    filtros = {}
    busqueda = texto_busqueda(request.args.get("q"))
    if busqueda:
        patron = escapar_regex(busqueda)
        filtros["$or"] = [
            {"nombre": {"$regex": patron, "$options": "i"}},
            {"descripcion": {"$regex": patron, "$options": "i"}},
        ]
    estado = texto_busqueda(request.args.get("estado"))
    if estado:
        filtros["estado"] = estado
    if texto_busqueda(request.args.get("bajo_stock")) == "true":
        filtros["$expr"] = {"$lte": ["$existencias", "$stock_minimo"]}

    lista = [serializar_documento(i) for i in insumos.find(filtros).sort("nombre", 1)]
    return jsonify({"datos": lista, "total": len(lista)}), 200


@insumos_bp.route("/insumos/<id_insumo>", methods=["GET"])
def consultar_insumo(id_insumo):
    insumo = insumos.find_one({"_id": convertir_object_id(id_insumo, "id_insumo")})
    if insumo is None:
        raise ErrorApi("Insumo no encontrado.", 404)
    return jsonify({"datos": serializar_documento(insumo)}), 200


@insumos_bp.route("/insumos", methods=["POST"])
def registrar_insumo():
    datos = _validar_cuerpo(request.get_json(silent=True))
    resultado = insumos.insert_one(datos)
    return (
        jsonify({"mensaje": "Insumo registrado correctamente.", "id": str(resultado.inserted_id)}),
        201,
    )


@insumos_bp.route("/insumos/<id_insumo>", methods=["PUT"])
def actualizar_insumo(id_insumo):
    object_id = convertir_object_id(id_insumo, "id_insumo")
    actual = insumos.find_one({"_id": object_id})
    if actual is None:
        raise ErrorApi("Insumo no encontrado.", 404)

    datos = _validar_cuerpo(request.get_json(silent=True), parcial=True, actual=actual)
    if not datos:
        raise ErrorApi("No se enviaron campos válidos para actualizar.", 400)

    resultado = insumos.update_one({"_id": object_id}, {"$set": datos})
    if resultado.matched_count == 0:
        raise ErrorApi("Insumo no encontrado.", 404)
    return jsonify({"mensaje": "Insumo actualizado correctamente."}), 200


@insumos_bp.route("/insumos/<id_insumo>", methods=["DELETE"])
def eliminar_insumo(id_insumo):
    object_id = convertir_object_id(id_insumo, "id_insumo")

    if visitas_mantenimiento.count_documents({"insumos_utilizados.insumo_id": object_id}) > 0:
        raise ErrorApi(
            "No se puede eliminar el insumo porque registra consumos en visitas de mantenimiento.",
            409,
        )

    resultado = insumos.delete_one({"_id": object_id})
    if resultado.deleted_count == 0:
        raise ErrorApi("Insumo no encontrado.", 404)
    return jsonify({"mensaje": "Insumo eliminado correctamente."}), 200
```

---

## A.12 Consultas analíticas (Aggregation Pipeline)

**Archivo:** `backend/routes/analitica.py` · **452 líneas**

Las cinco consultas con $lookup, $match, $project, $sort, $limit, $group y $unwind, más los KPIs.

```python
# ============================================================
#  Blueprint: Consultas analíticas y reportes (Aggregation Pipeline)
# ============================================================
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from backend.config import (
    clientes,
    insumos,
    personal,
    propiedades,
    servicios_contratos,
    visitas_mantenimiento,
)
from backend.utils import serializar, texto_busqueda
from backend.validators import ESTADOS_VISITA

analitica_bp = Blueprint("analitica", __name__)

COLECCIONES_ANALITICA = {
    "clientes": clientes,
    "propiedades": propiedades,
    "servicios_contratos": servicios_contratos,
    "personal": personal,
    "visitas_mantenimiento": visitas_mantenimiento,
    "insumos": insumos,
}


def _resultado(pipeline, coleccion):
    return [serializar(documento) for documento in COLECCIONES_ANALITICA[coleccion].aggregate(pipeline)]


# ------------------------------------------------------------------
# Consulta 1: Clientes y sus propiedades registradas ($lookup + $addFields)
# ------------------------------------------------------------------
@analitica_bp.route("/analitica/clientes-propiedades", methods=["GET"])
def clientes_propiedades():
    pipeline = [
        {
            "$lookup": {
                "from": "propiedades",
                "localField": "_id",
                "foreignField": "cliente_id",
                "as": "propiedades",
            }
        },
        {
            "$addFields": {
                "total_propiedades": {"$size": "$propiedades"},
                "area_total_m2": {"$sum": "$propiedades.area_m2"},
                "total_especies": {
                    "$sum": {
                        "$map": {
                            "input": "$propiedades",
                            "as": "propiedad",
                            "in": {"$size": {"$ifNull": ["$$propiedad.especies", []]}},
                        }
                    }
                },
                "detalle_propiedades": {
                    "$map": {
                        "input": "$propiedades",
                        "as": "propiedad",
                        "in": {
                            "nombre": "$$propiedad.nombre",
                            "ciudad": "$$propiedad.ciudad",
                            "tipo_propiedad": "$$propiedad.tipo_propiedad",
                            "area_m2": "$$propiedad.area_m2",
                            "total_especies": {"$size": {"$ifNull": ["$$propiedad.especies", []]}},
                        },
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 1,
                "nombre": 1,
                "documento": 1,
                "correo": 1,
                "telefono": 1,
                "estado": 1,
                "total_propiedades": 1,
                "area_total_m2": 1,
                "total_especies": 1,
                "detalle_propiedades": 1,
            }
        },
        {"$sort": {"total_propiedades": -1, "nombre": 1}},
    ]
    datos = _resultado(pipeline, "clientes")
    return jsonify({"datos": datos, "total": len(datos)}), 200


# ------------------------------------------------------------------
# Consulta 2: Visitas con detalle de propiedad, cliente y contrato
#             (tres $lookup encadenados)
# ------------------------------------------------------------------
@analitica_bp.route("/analitica/visitas-detalle", methods=["GET"])
def visitas_detalle():
    coincidencias = {}
    estado = texto_busqueda(request.args.get("estado"))
    if estado in ESTADOS_VISITA:
        coincidencias["estado"] = estado

    pipeline = [
        {"$match": coincidencias} if coincidencias else {"$match": {}},
        {
            "$lookup": {
                "from": "propiedades",
                "localField": "propiedad_id",
                "foreignField": "_id",
                "as": "propiedad",
            }
        },
        {"$unwind": {"path": "$propiedad", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "clientes",
                "localField": "propiedad.cliente_id",
                "foreignField": "_id",
                "as": "cliente",
            }
        },
        {"$unwind": {"path": "$cliente", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "servicios_contratos",
                "localField": "contrato_id",
                "foreignField": "_id",
                "as": "contrato",
            }
        },
        {"$unwind": {"path": "$contrato", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "fecha_programada": 1,
                "estado": 1,
                "propiedad_nombre": {"$ifNull": ["$propiedad.nombre", "No disponible"]},
                "propiedad_ciudad": {"$ifNull": ["$propiedad.ciudad", ""]},
                "propiedad_direccion": {"$ifNull": ["$propiedad.direccion", ""]},
                "cliente_nombre": {"$ifNull": ["$cliente.nombre", "No disponible"]},
                "cliente_documento": {"$ifNull": ["$cliente.documento", ""]},
                "cliente_correo": {"$ifNull": ["$cliente.correo", ""]},
                "contrato_estado": {"$ifNull": ["$contrato.estado", "No disponible"]},
                "servicios_contratados": {"$ifNull": ["$contrato.servicios.nombre", []]},
                "personal_asignado": {
                    "$map": {
                        "input": {"$ifNull": ["$personal_asignado", []]},
                        "as": "persona",
                        "in": "$$persona.nombre",
                    }
                },
                "actividades_realizadas": 1,
                "observaciones": 1,
                "insumos_utilizados": {
                    "$map": {
                        "input": {"$ifNull": ["$insumos_utilizados", []]},
                        "as": "insumo",
                        "in": {
                            "nombre": "$$insumo.nombre",
                            "cantidad": "$$insumo.cantidad",
                            "unidad_medida": "$$insumo.unidad_medida",
                        },
                    }
                },
            }
        },
        {"$sort": {"fecha_programada": -1}},
    ]
    datos = _resultado(pipeline, "visitas_mantenimiento")
    return jsonify({"datos": datos, "total": len(datos)}), 200


# ------------------------------------------------------------------
# Consulta 3: Distribución y conteo de visitas por estado ($group + $sort)
# ------------------------------------------------------------------
@analitica_bp.route("/analitica/visitas-estado", methods=["GET"])
def visitas_por_estado():
    pipeline = [
        {
            "$facet": {
                "por_estado": [
                    {"$group": {"_id": "$estado", "total": {"$sum": 1}}},
                    {"$sort": {"total": -1}},
                ],
                "total_general": [{"$count": "valor"}],
            }
        },
        {"$unwind": {"path": "$total_general", "preserveNullAndEmptyArrays": True}},
        {"$unwind": "$por_estado"},
        {
            "$project": {
                "_id": 0,
                "estado": "$por_estado._id",
                "total": "$por_estado.total",
                "porcentaje": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$por_estado.total",
                                        {"$ifNull": ["$total_general.valor", 1]},
                                    ]
                                },
                                100,
                            ]
                        },
                        1,
                    ]
                },
            }
        },
        {"$sort": {"total": -1}},
    ]
    datos = _resultado(pipeline, "visitas_mantenimiento")
    return jsonify({"datos": datos, "total": len(datos)}), 200


# ------------------------------------------------------------------
# Consulta 4: Ranking de insumos más utilizados
#             ($unwind + $group + $lookup + $sort)
# ------------------------------------------------------------------
@analitica_bp.route("/analitica/insumos-mas-utilizados", methods=["GET"])
def insumos_mas_utilizados():
    limite = request.args.get("limite", default=10, type=int)
    limite = max(1, min(limite or 10, 50))

    pipeline = [
        {"$unwind": "$insumos_utilizados"},
        {
            "$group": {
                "_id": "$insumos_utilizados.insumo_id",
                "nombre": {"$first": "$insumos_utilizados.nombre"},
                "unidad_medida": {"$first": "$insumos_utilizados.unidad_medida"},
                "cantidad_total": {"$sum": "$insumos_utilizados.cantidad"},
                "visitas": {"$addToSet": "$_id"},
            }
        },
        {"$addFields": {"total_visitas": {"$size": "$visitas"}}},
        {
            "$lookup": {
                "from": "insumos",
                "localField": "_id",
                "foreignField": "_id",
                "as": "insumo",
            }
        },
        {"$unwind": {"path": "$insumo", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "insumo_id": "$_id",
                "nombre": 1,
                "unidad_medida": 1,
                "cantidad_total": 1,
                "total_visitas": 1,
                "existencias_actuales": {"$ifNull": ["$insumo.existencias", 0]},
                "stock_minimo": {"$ifNull": ["$insumo.stock_minimo", 0]},
                "estado_inventario": {"$ifNull": ["$insumo.estado", "No disponible"]},
            }
        },
        {"$sort": {"cantidad_total": -1, "nombre": 1}},
        {"$limit": limite},
    ]
    datos = _resultado(pipeline, "visitas_mantenimiento")
    return jsonify({"datos": datos, "total": len(datos)}), 200


# ------------------------------------------------------------------
# Consulta 5: Servicios más contratados
#             ($unwind + $group + $sort)
# ------------------------------------------------------------------
@analitica_bp.route("/analitica/servicios-mas-contratados", methods=["GET"])
def servicios_mas_contratados():
    pipeline = [
        {"$unwind": "$servicios"},
        {
            "$group": {
                "_id": "$servicios.nombre",
                "veces_contratado": {"$sum": 1},
                "ingreso_total": {"$sum": "$servicios.precio_acordado"},
                "precio_promedio": {"$avg": "$servicios.precio_acordado"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "servicio": "$_id",
                "veces_contratado": 1,
                "ingreso_total": 1,
                "precio_promedio": {"$round": ["$precio_promedio", 0]},
            }
        },
        {"$sort": {"veces_contratado": -1, "ingreso_total": -1}},
    ]
    datos = _resultado(pipeline, "servicios_contratos")
    return jsonify({"datos": datos, "total": len(datos)}), 200


# ------------------------------------------------------------------
# Indicadores clave de gestión (KPIs) para el tablero principal
# ------------------------------------------------------------------
@analitica_bp.route("/analitica/kpis", methods=["GET"])
def kpis():
    ahora = datetime.utcnow()
    inicio_semana = ahora
    fin_semana = ahora + timedelta(days=7)

    estados = list(
        visitas_mantenimiento.aggregate(
            [{"$group": {"_id": "$estado", "total": {"$sum": 1}}}]
        )
    )
    visitas_por_estado = {registro["_id"]: registro["total"] for registro in estados}
    total_visitas = sum(visitas_por_estado.values())
    finalizadas = visitas_por_estado.get("Finalizada", 0)
    tasa_cumplimiento = round((finalizadas / total_visitas) * 100, 1) if total_visitas else 0

    resumen_contratos = list(
        servicios_contratos.aggregate(
            [
                {"$match": {"estado": "Activo"}},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "valor_cartera": {"$sum": "$valor_total"},
                        "promedio": {"$avg": "$valor_total"},
                    }
                },
            ]
        )
    )
    contratos = resumen_contratos[0] if resumen_contratos else {"total": 0, "valor_cartera": 0, "promedio": 0}

    resumen_propiedades = list(
        propiedades.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "area_total": {"$sum": "$area_m2"},
                    }
                }
            ]
        )
    )
    propiedades_resumen = (
        resumen_propiedades[0] if resumen_propiedades else {"total": 0, "area_total": 0}
    )

    proximas = list(
        visitas_mantenimiento.aggregate(
            [
                {
                    "$match": {
                        "estado": {"$in": ["Programada", "En proceso"]},
                        "fecha_programada": {"$gte": inicio_semana, "$lte": fin_semana},
                    }
                },
                {
                    "$lookup": {
                        "from": "propiedades",
                        "localField": "propiedad_id",
                        "foreignField": "_id",
                        "as": "propiedad",
                    }
                },
                {"$unwind": {"path": "$propiedad", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": "clientes",
                        "localField": "propiedad.cliente_id",
                        "foreignField": "_id",
                        "as": "cliente",
                    }
                },
                {"$unwind": {"path": "$cliente", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": 1,
                        "fecha_programada": 1,
                        "estado": 1,
                        "propiedad_nombre": {"$ifNull": ["$propiedad.nombre", "No disponible"]},
                        "cliente_nombre": {"$ifNull": ["$cliente.nombre", "No disponible"]},
                        "personal_asignado": 1,
                    }
                },
                {"$sort": {"fecha_programada": 1}},
                {"$limit": 6},
            ]
        )
    )

    insumos_criticos = [
        serializar(documento)
        for documento in insumos.find(
            {"$expr": {"$lte": ["$existencias", "$stock_minimo"]}}
        ).sort("existencias", 1)
    ]

    top_insumo = list(
        visitas_mantenimiento.aggregate(
            [
                {"$unwind": "$insumos_utilizados"},
                {
                    "$group": {
                        "_id": "$insumos_utilizados.nombre",
                        "cantidad": {"$sum": "$insumos_utilizados.cantidad"},
                    }
                },
                {"$sort": {"cantidad": -1}},
                {"$limit": 1},
            ]
        )
    )

    return (
        jsonify(
            {
                "datos": {
                    "clientes_activos": clientes.count_documents({"estado": "Activo"}),
                    "clientes_total": clientes.count_documents({}),
                    "propiedades_total": propiedades_resumen.get("total", 0),
                    "area_total_m2": propiedades_resumen.get("area_total", 0),
                    "contratos_activos": contratos.get("total", 0),
                    "valor_cartera": contratos.get("valor_cartera", 0),
                    "valor_promedio_contrato": round(contratos.get("promedio", 0) or 0, 0),
                    "personal_activo": personal.count_documents({"estado": "Activo"}),
                    "personal_total": personal.count_documents({}),
                    "visitas_total": total_visitas,
                    "visitas_por_estado": visitas_por_estado,
                    "tasa_cumplimiento": tasa_cumplimiento,
                    "insumos_criticos": insumos_criticos,
                    "insumos_criticos_total": len(insumos_criticos),
                    "proximas_visitas": [serializar(v) for v in proximas],
                    "insumo_mas_consumido": (
                        {"nombre": top_insumo[0]["_id"], "cantidad": top_insumo[0]["cantidad"]}
                        if top_insumo
                        else None
                    ),
                }
            }
        ),
        200,
    )
```

---

## A.13 Interfaz web (HTML)

**Archivo:** `frontend/index.html` · **147 líneas**

Estructura de la SPA: barra lateral, panel, modales y carga de scripts.

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico" />
  <title>VerdeVivo · Gestión de Paisajismo</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/static/css/estilos.css" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌿</text></svg>" />
</head>
<body>
  <div class="app" id="app">
    <!-- ===================== BARRA LATERAL ===================== -->
    <aside class="sidebar" id="sidebar">
      <div class="brand">
        <span class="brand-mark">🌿</span>
        <div class="brand-text">
          <strong>VerdeVivo</strong>
          <small>Paisajismo &amp; Botánica</small>
        </div>
      </div>

      <nav class="nav" id="nav">
        <a class="nav-item" href="#/panel" data-vista="panel">
          <svg viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
          <span>Panel general</span>
        </a>
        <a class="nav-item" href="#/clientes" data-vista="clientes">
          <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
          <span>Clientes</span>
        </a>
        <a class="nav-item" href="#/propiedades" data-vista="propiedades">
          <svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          <span>Propiedades</span>
        </a>
        <a class="nav-item" href="#/contratos" data-vista="contratos">
          <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm2 18H6V4h7v5h5v11zM8 12h8v2H8zm0 4h8v2H8z"/></svg>
          <span>Contratos</span>
        </a>
        <a class="nav-item" href="#/personal" data-vista="personal">
          <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
          <span>Personal</span>
        </a>
        <a class="nav-item" href="#/visitas" data-vista="visitas">
          <svg viewBox="0 0 24 24"><path d="M19 3h-1V1h-2v2H8V1H6v2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm0 18H5V8h14v13zm-7-2l-4-4 1.41-1.41L12 16.17l4.59-4.58L18 13z"/></svg>
          <span>Visitas</span>
        </a>
        <a class="nav-item" href="#/insumos" data-vista="insumos">
          <svg viewBox="0 0 24 24"><path d="M20 8h-2.81a5.985 5.985 0 0 0-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5s-.96.06-1.41.17L8.41 3 7 4.41l1.62 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z"/></svg>
          <span>Insumos</span>
        </a>
        <a class="nav-item" href="#/analitica" data-vista="analitica">
          <svg viewBox="0 0 24 24"><path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z"/></svg>
          <span>Analítica</span>
        </a>
      </nav>

      <div class="sidebar-foot">
        <div class="db-status" id="db-status">
          <span class="dot dot-wait"></span>
          <div>
            <strong>Conectando…</strong>
            <small>MongoDB Atlas</small>
          </div>
        </div>
        <small class="version">Bases de Datos II · v1.0</small>
      </div>
    </aside>

    <!-- ===================== CONTENIDO ===================== -->
    <div class="main">
      <header class="topbar">
        <button class="icon-btn only-mobile" id="btn-menu" aria-label="Abrir menú">
          <svg viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
        </button>
        <div class="topbar-title">
          <h1 id="titulo-vista">Panel general</h1>
          <p id="subtitulo-vista">Resumen operativo del sistema de paisajismo</p>
        </div>
        <div class="topbar-actions">
          <button class="btn btn-ghost" id="btn-refrescar" title="Actualizar datos">
            <svg viewBox="0 0 24 24"><path d="M17.65 6.35A7.958 7.958 0 0 0 12 4a8 8 0 1 0 7.73 10h-2.08A6 6 0 1 1 12 6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
            <span>Actualizar</span>
          </button>
        </div>
      </header>

      <main class="content" id="contenido" aria-live="polite">
        <div class="skeleton-wrap">
          <div class="skeleton skeleton-card"></div>
          <div class="skeleton skeleton-card"></div>
          <div class="skeleton skeleton-card"></div>
        </div>
      </main>

      <footer class="footer">
        <span>Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico</span>
        <span>Flask · MongoDB Atlas · Aggregation Pipeline</span>
      </footer>
    </div>
  </div>

  <!-- ===================== MODAL GENÉRICO ===================== -->
  <div class="modal-backdrop" id="modal" hidden>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-titulo">
      <header class="modal-head">
        <div>
          <h2 id="modal-titulo">Formulario</h2>
          <p id="modal-subtitulo"></p>
        </div>
        <button class="icon-btn" id="modal-cerrar" aria-label="Cerrar">
          <svg viewBox="0 0 24 24"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </header>
      <div class="modal-body" id="modal-cuerpo"></div>
      <footer class="modal-foot" id="modal-pie"></footer>
    </div>
  </div>

  <!-- ===================== CONFIRMACIÓN ===================== -->
  <div class="modal-backdrop" id="confirmacion" hidden>
    <div class="modal modal-sm" role="alertdialog" aria-modal="true" aria-labelledby="confirmar-titulo">
      <header class="modal-head">
        <div>
          <h2 id="confirmar-titulo">Confirmar acción</h2>
          <p id="confirmar-texto"></p>
        </div>
      </header>
      <footer class="modal-foot">
        <button class="btn btn-ghost" id="confirmar-no">Cancelar</button>
        <button class="btn btn-danger" id="confirmar-si">Sí, continuar</button>
      </footer>
    </div>
  </div>

  <div class="toasts" id="toasts"></div>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script src="/static/js/api.js"></script>
  <script src="/static/js/formularios.js"></script>
  <script src="/static/js/vistas.js"></script>
  <script src="/static/js/app.js"></script>
</body>
</html>
```

---

## A.14 Interfaz web (CSS)

**Archivo:** `frontend/css/estilos.css` · **509 líneas**

Diseño responsivo, componentes, tablas, formularios y tarjetas del panel.

```css
/* ============================================================
   VerdeVivo · Sistema de Gestión de Servicios de Paisajismo
   Hoja de estilos principal
   ============================================================ */
:root {
  --verde-950: #0d2416;
  --verde-900: #143520;
  --verde-800: #1a4a2c;
  --verde-700: #22673c;
  --verde-600: #2b8150;
  --verde-500: #35a065;
  --verde-300: #8ed3a8;
  --verde-100: #e3f4e8;
  --lima: #b7d94b;
  --lima-soft: #eef7d4;
  --crema: #f4f1e8;
  --crema-2: #faf8f2;
  --tinta: #16211a;
  --tinta-suave: #5b6b60;
  --linea: #e2e0d4;
  --blanco: #ffffff;
  --rojo: #c2453c;
  --rojo-soft: #fbeae8;
  --ambar: #c07a13;
  --ambar-soft: #fdf3df;
  --azul: #2a6f97;
  --azul-soft: #e6f1f7;
  --sombra-sm: 0 1px 2px rgba(20, 53, 32, .06), 0 2px 8px rgba(20, 53, 32, .04);
  --sombra-md: 0 8px 28px rgba(20, 53, 32, .10);
  --sombra-lg: 0 24px 70px rgba(13, 36, 22, .22);
  --radio: 14px;
  --radio-sm: 10px;
  --sidebar: 256px;
  --fuente: "Manrope", system-ui, -apple-system, "Segoe UI", sans-serif;
  --display: "Fraunces", Georgia, serif;
}

* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  font-family: var(--fuente);
  color: var(--tinta);
  background: var(--crema);
  font-size: 14.5px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
svg { width: 20px; height: 20px; fill: currentColor; flex: none; }
a { color: inherit; text-decoration: none; }
button { font-family: inherit; }
h1, h2, h3, h4 { margin: 0; line-height: 1.25; }
p { margin: 0; }
[hidden] { display: none !important; }

/* ===================== ESTRUCTURA ===================== */
.app { display: flex; min-height: 100vh; }

.sidebar {
  width: var(--sidebar);
  flex: none;
  background: linear-gradient(180deg, var(--verde-950) 0%, var(--verde-900) 55%, #123020 100%);
  color: #d8e8dd;
  display: flex;
  flex-direction: column;
  padding: 22px 16px 18px;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 40;
  overflow-y: auto;
}
.brand { display: flex; align-items: center; gap: 12px; padding: 2px 8px 22px; }
.brand-mark {
  width: 44px; height: 44px; border-radius: 13px;
  display: grid; place-items: center;
  background: linear-gradient(145deg, var(--lima), var(--verde-500));
  font-size: 23px;
  box-shadow: 0 6px 18px rgba(183, 217, 75, .25);
}
.brand-text { display: flex; flex-direction: column; line-height: 1.2; }
.brand-text strong { font-family: var(--display); font-size: 21px; letter-spacing: .2px; color: #fff; }
.brand-text small { color: #8fb59d; font-size: 10.5px; letter-spacing: .7px; text-transform: uppercase; margin-top: 2px; }

.nav { display: flex; flex-direction: column; gap: 4px; margin-top: 6px; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 12px;
  border-radius: 10px;
  color: #b8cfc0;
  font-weight: 600;
  font-size: 13.5px;
  transition: background .18s, color .18s, transform .18s;
  position: relative;
}
.nav-item svg { width: 19px; height: 19px; opacity: .85; }
.nav-item:hover { background: rgba(255, 255, 255, .07); color: #fff; }
.nav-item.activo {
  background: linear-gradient(90deg, rgba(183, 217, 75, .18), rgba(183, 217, 75, .04));
  color: #fff;
}
.nav-item.activo::before {
  content: ""; position: absolute; left: -16px; top: 9px; bottom: 9px; width: 4px;
  border-radius: 0 4px 4px 0; background: var(--lima);
}
.nav-item.activo svg { color: var(--lima); opacity: 1; }

.sidebar-foot { margin-top: auto; padding: 18px 6px 0; display: flex; flex-direction: column; gap: 12px; }
.db-status {
  display: flex; align-items: center; gap: 10px;
  background: rgba(255, 255, 255, .06);
  border: 1px solid rgba(255, 255, 255, .08);
  padding: 10px 12px; border-radius: 11px;
}
.db-status strong { display: block; font-size: 12px; color: #fff; }
.db-status small { font-size: 10.5px; color: #8fb59d; }
.dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
.dot-ok { background: var(--lima); box-shadow: 0 0 0 4px rgba(183, 217, 75, .16); }
.dot-error { background: #ff7a6e; box-shadow: 0 0 0 4px rgba(255, 122, 110, .16); }
.dot-wait { background: #e9c46a; animation: latido 1.3s infinite; }
@keyframes latido { 50% { opacity: .35; } }
.version { color: #6f8f7b; font-size: 10.5px; padding-left: 4px; }

.main { flex: 1; min-width: 0; display: flex; flex-direction: column; min-height: 100vh; }

.topbar {
  display: flex; align-items: center; gap: 16px;
  padding: 20px 30px 16px;
  background: rgba(244, 241, 232, .82);
  backdrop-filter: blur(10px);
  position: sticky; top: 0; z-index: 30;
  border-bottom: 1px solid rgba(226, 224, 212, .7);
}
.topbar-title { flex: 1; min-width: 0; }
.topbar-title h1 { font-family: var(--display); font-size: 26px; font-weight: 600; color: var(--verde-950); }
.topbar-title p { color: var(--tinta-suave); font-size: 12.5px; margin-top: 2px; }
.topbar-actions { display: flex; gap: 10px; align-items: center; }

.content { padding: 24px 30px 40px; flex: 1; }
.footer {
  display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  padding: 14px 30px 22px; color: #8a978d; font-size: 11px;
  border-top: 1px solid rgba(226, 224, 212, .8);
}

/* ===================== BOTONES ===================== */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  border: 1px solid transparent; border-radius: 10px;
  padding: 9px 15px; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: transform .15s, box-shadow .15s, background .15s, color .15s;
  white-space: nowrap; background: var(--blanco); color: var(--tinta);
}
.btn svg { width: 16px; height: 16px; }
.btn:hover { transform: translateY(-1px); }
.btn:active { transform: translateY(0); }
.btn:disabled { opacity: .55; cursor: not-allowed; transform: none; }
.btn-primario { background: var(--verde-700); color: #fff; box-shadow: 0 4px 14px rgba(34, 103, 60, .22); }
.btn-primario:hover { background: var(--verde-600); }
.btn-lima { background: var(--lima); color: var(--verde-950); }
.btn-lima:hover { background: #c4e45a; }
.btn-ghost { background: transparent; border-color: var(--linea); color: var(--tinta-suave); }
.btn-ghost:hover { background: #fff; color: var(--tinta); border-color: #cfccbd; }
.btn-danger { background: var(--rojo); color: #fff; }
.btn-danger:hover { background: #a93a32; }
.btn-sm { padding: 6px 10px; font-size: 12px; border-radius: 8px; }
.btn-icon { padding: 7px; border-radius: 8px; background: transparent; border: 1px solid var(--linea); color: var(--tinta-suave); }
.btn-icon:hover { background: #fff; color: var(--verde-700); border-color: var(--verde-300); }
.btn-icon.peligro:hover { color: var(--rojo); border-color: #ecc6c2; background: var(--rojo-soft); }
.icon-btn {
  display: inline-grid; place-items: center;
  width: 36px; height: 36px; border-radius: 10px;
  border: 1px solid var(--linea); background: #fff; color: var(--tinta-suave);
  cursor: pointer; transition: background .15s, color .15s;
}
.icon-btn:hover { color: var(--verde-700); }
.only-mobile { display: none; }

/* ===================== TARJETAS ===================== */
.card {
  background: var(--blanco);
  border: 1px solid var(--linea);
  border-radius: var(--radio);
  box-shadow: var(--sombra-sm);
}
.card-pad { padding: 20px; }
.card-head {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 14px;
  padding: 18px 20px 14px;
}
.card-head h3 { font-size: 15px; font-weight: 800; }
.card-head p { color: var(--tinta-suave); font-size: 12px; margin-top: 2px; }

/* ===================== TABLERO ===================== */
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 16px; margin-bottom: 20px;
}
.kpi {
  background: var(--blanco); border: 1px solid var(--linea); border-radius: var(--radio);
  padding: 18px; box-shadow: var(--sombra-sm);
  position: relative; overflow: hidden;
}
.kpi::after {
  content: ""; position: absolute; right: -24px; top: -24px; width: 86px; height: 86px;
  border-radius: 50%; background: var(--verde-100); opacity: .7;
}
.kpi.kpi-alerta::after { background: var(--ambar-soft); }
.kpi.kpi-rojo::after { background: var(--rojo-soft); }
.kpi-label { color: var(--tinta-suave); font-size: 11.5px; font-weight: 700; letter-spacing: .5px; text-transform: uppercase; }
.kpi-valor { font-family: var(--display); font-size: 31px; font-weight: 600; margin: 6px 0 2px; color: var(--verde-950); position: relative; z-index: 1; }
.kpi-detalle { font-size: 11.5px; color: var(--tinta-suave); position: relative; z-index: 1; }
.kpi-icon {
  position: absolute; right: 16px; bottom: 14px; font-size: 26px; opacity: .9; z-index: 1;
}
.kpi-icon svg { width: 30px; height: 30px; color: var(--verde-600); }

.dashboard-grid { display: grid; grid-template-columns: 1.55fr 1fr; gap: 18px; margin-bottom: 18px; }
.dashboard-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

.chart-box { position: relative; height: 260px; padding: 6px 20px 20px; }
.chart-box.chart-sm { height: 210px; }

.lista-simple { display: flex; flex-direction: column; }
.lista-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 20px; border-top: 1px solid #f0eee4;
}
.lista-item:first-child { border-top: 0; }
.lista-item .avatar {
  width: 36px; height: 36px; border-radius: 10px; flex: none;
  display: grid; place-items: center; background: var(--verde-100); color: var(--verde-700);
  font-weight: 800; font-size: 12px;
}
.lista-item .avatar.alerta { background: var(--ambar-soft); color: var(--ambar); }
.lista-item .grow { flex: 1; min-width: 0; }
.lista-item strong { display: block; font-size: 12.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lista-item small { color: var(--tinta-suave); font-size: 11px; }
.lista-item .valor { font-weight: 800; font-size: 12px; color: var(--verde-700); }

/* ===================== BARRA DE HERRAMIENTAS ===================== */
.toolbar {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 16px;
}
.search-box { position: relative; flex: 1; min-width: 210px; max-width: 380px; }
.search-box svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); width: 17px; height: 17px; color: #94a39a; }
.search-box input { padding-left: 37px; }
.toolbar select, .toolbar input[type="date"] { min-width: 140px; }
.toolbar .spacer { flex: 1; }
.filtro-check {
  display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 600;
  color: var(--tinta-suave); padding: 9px 12px; background: #fff;
  border: 1px solid var(--linea); border-radius: 10px; cursor: pointer; user-select: none;
}
.filtro-check input { accent-color: var(--verde-700); width: 15px; height: 15px; }
.conteo { font-size: 12px; color: var(--tinta-suave); white-space: nowrap; }
.conteo b { color: var(--verde-800); }

/* ===================== FORMULARIOS ===================== */
input, select, textarea {
  width: 100%; font-family: inherit; font-size: 13px; color: var(--tinta);
  background: #fff; border: 1px solid var(--linea); border-radius: 9px;
  padding: 9px 11px; outline: none;
  transition: border-color .15s, box-shadow .15s;
}
input:focus, select:focus, textarea:focus {
  border-color: var(--verde-500); box-shadow: 0 0 0 3px rgba(53, 160, 101, .14);
}
input:disabled, select:disabled { background: #f6f5ee; color: #8a978d; }
textarea { resize: vertical; min-height: 74px; }
label.campo { display: flex; flex-direction: column; gap: 6px; font-size: 12px; font-weight: 700; color: #42544a; }
label.campo .req { color: var(--rojo); }
label.campo .ayuda { font-weight: 500; color: #93a096; font-size: 11px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; }
.form-grid .full { grid-column: 1 / -1; }
fieldset.bloque {
  border: 1px dashed #d8d5c6; border-radius: 12px; padding: 14px 16px 16px;
  margin: 18px 0 0; background: var(--crema-2);
}
fieldset.bloque legend {
  font-size: 11.5px; font-weight: 800; letter-spacing: .6px; text-transform: uppercase;
  color: var(--verde-700); padding: 0 8px;
}
.repetidor { display: flex; flex-direction: column; gap: 10px; }
.repetidor-fila {
  display: grid; gap: 8px; align-items: end;
  background: #fff; border: 1px solid var(--linea); border-radius: 10px; padding: 10px;
}
.repetidor-fila.especies { grid-template-columns: 1.1fr 1.2fr .55fr 1fr 1.3fr 34px; }
.repetidor-fila.servicios { grid-template-columns: 1.1fr 1.5fr .7fr 34px; }
.repetidor-fila.insumos { grid-template-columns: 2fr .8fr .8fr 34px; }
.repetidor-fila .mini { display: flex; flex-direction: column; gap: 4px; font-size: 10.5px; font-weight: 700; color: #718076; }
.repetidor-fila .mini input, .repetidor-fila .mini select { padding: 7px 9px; font-size: 12.5px; }
.btn-quitar {
  width: 34px; height: 34px; border-radius: 8px; border: 1px solid #ecc6c2;
  background: var(--rojo-soft); color: var(--rojo); cursor: pointer; display: grid; place-items: center;
}
.btn-quitar svg { width: 15px; height: 15px; }
.btn-agregar {
  align-self: flex-start; border: 1px dashed var(--verde-300); background: var(--verde-100);
  color: var(--verde-700); font-weight: 800; font-size: 12px; padding: 8px 12px;
  border-radius: 8px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;
}
.btn-agregar:hover { background: #d5ecdd; }
.form-error {
  display: none; margin-top: 14px; padding: 10px 12px; border-radius: 9px;
  background: var(--rojo-soft); border: 1px solid #ecc6c2; color: #8f2f28; font-size: 12.5px; font-weight: 600;
}
.form-error.visible { display: block; }
.checks-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px;
  max-height: 180px; overflow-y: auto; padding: 4px;
}
.check-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border: 1px solid var(--linea); border-radius: 8px; background: #fff;
  font-size: 12px; cursor: pointer;
}
.check-item:has(input:checked) { border-color: var(--verde-400, #63b985); background: var(--verde-100); }
.check-item input { width: 15px; height: 15px; accent-color: var(--verde-700); }
.check-item small { color: var(--tinta-suave); margin-left: auto; font-size: 10.5px; }
.total-live {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 10px; padding: 10px 14px; border-radius: 9px;
  background: var(--verde-100); color: var(--verde-800); font-size: 12.5px; font-weight: 700;
}
.total-live b { font-size: 16px; font-family: var(--display); }

/* ===================== TABLAS ===================== */
.tabla-wrap { overflow-x: auto; border-radius: 0 0 var(--radio) var(--radio); }
table.tabla { width: 100%; border-collapse: collapse; min-width: 720px; }
table.tabla thead th {
  text-align: left; font-size: 10.5px; letter-spacing: .7px; text-transform: uppercase;
  color: #77877d; font-weight: 800; padding: 10px 14px; background: #fbfaf5;
  border-bottom: 1px solid var(--linea); white-space: nowrap;
}
table.tabla tbody td {
  padding: 12px 14px; border-bottom: 1px solid #f1efe6; vertical-align: middle; font-size: 12.8px;
}
table.tabla tbody tr:last-child td { border-bottom: 0; }
table.tabla tbody tr { transition: background .12s; }
table.tabla tbody tr:hover { background: #fbfcf7; }
table.tabla .principal { font-weight: 700; color: var(--tinta); }
table.tabla .secundario { color: var(--tinta-suave); font-size: 11.5px; }
.celda-acciones { display: flex; gap: 6px; justify-content: flex-end; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.chips { display: flex; flex-wrap: wrap; gap: 4px; max-width: 260px; }
.chip {
  display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px;
  background: var(--verde-100); color: var(--verde-800); font-size: 10.5px; font-weight: 700;
  white-space: nowrap;
}
.chip.neutro { background: #f0efe7; color: #6b7a70; }
.chip.ambar { background: var(--ambar-soft); color: #96600d; }
.chip.rojo { background: var(--rojo-soft); color: #9c342d; }
.chip.azul { background: var(--azul-soft); color: var(--azul); }

.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 9px; border-radius: 999px; font-size: 10.5px; font-weight: 800;
  white-space: nowrap;
}
.badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.badge-verde { background: var(--verde-100); color: #1f6b3a; }
.badge-ambar { background: var(--ambar-soft); color: #96600d; }
.badge-rojo { background: var(--rojo-soft); color: #9c342d; }
.badge-azul { background: var(--azul-soft); color: var(--azul); }
.badge-gris { background: #f0efe7; color: #6b7a70; }

.vacio {
  padding: 46px 20px; text-align: center; color: var(--tinta-suave);
}
.vacio .emoji { font-size: 34px; display: block; margin-bottom: 8px; }
.vacio strong { display: block; color: var(--tinta); margin-bottom: 3px; }
.vacio small { font-size: 12px; }

/* ===================== MODAL ===================== */
.modal-backdrop {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(13, 36, 22, .48); backdrop-filter: blur(3px);
  display: grid; place-items: center; padding: 20px;
  animation: aparecer .16s ease;
}
@keyframes aparecer { from { opacity: 0; } }
.modal {
  width: min(780px, 100%); max-height: min(90vh, 900px);
  background: var(--blanco); border-radius: 18px; box-shadow: var(--sombra-lg);
  display: flex; flex-direction: column; overflow: hidden;
  animation: subir .2s cubic-bezier(.2, .8, .3, 1);
}
.modal.modal-sm { width: min(440px, 100%); }
.modal.modal-lg { width: min(980px, 100%); }
@keyframes subir { from { transform: translateY(14px) scale(.99); opacity: .6; } }
.modal-head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;
  padding: 20px 22px 14px; border-bottom: 1px solid #f0eee4;
}
.modal-head h2 { font-family: var(--display); font-size: 21px; font-weight: 600; color: var(--verde-950); }
.modal-head p { color: var(--tinta-suave); font-size: 12px; margin-top: 3px; }
.modal-body { padding: 20px 22px; overflow-y: auto; }
.modal-foot {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 22px 18px; border-top: 1px solid #f0eee4; background: #fdfcf8;
}
.modal-foot .izquierda { margin-right: auto; }

/* ===================== TOASTS ===================== */
.toasts {
  position: fixed; right: 22px; bottom: 22px; z-index: 200;
  display: flex; flex-direction: column; gap: 10px; max-width: 380px;
}
.toast {
  display: flex; gap: 10px; align-items: flex-start;
  background: var(--verde-950); color: #eaf5ee;
  padding: 12px 14px; border-radius: 11px; box-shadow: var(--sombra-md);
  font-size: 12.5px; animation: entrar-toast .22s ease;
  border-left: 4px solid var(--lima);
}
.toast.error { border-left-color: #ff7a6e; }
.toast.info { border-left-color: #7ec8e3; }
.toast strong { display: block; font-size: 12.5px; margin-bottom: 1px; }
.toast small { color: #a9c6b6; font-size: 11.5px; }
@keyframes entrar-toast { from { transform: translateX(20px); opacity: 0; } }

/* ===================== ESQUELETOS ===================== */
.skeleton-wrap { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.skeleton {
  border-radius: var(--radio); background: linear-gradient(90deg, #eceae0 25%, #f5f3ea 50%, #eceae0 75%);
  background-size: 200% 100%; animation: brillo 1.2s infinite;
}
.skeleton-card { height: 120px; }
@keyframes brillo { to { background-position: -200% 0; } }

/* ===================== ANALÍTICA ===================== */
.analitica-grid { display: grid; grid-template-columns: 1fr; gap: 18px; }
.reporte { overflow: hidden; }
.reporte-head {
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  padding: 16px 20px; border-bottom: 1px solid #f0eee4; flex-wrap: wrap;
}
.reporte-head .titulo { display: flex; align-items: center; gap: 12px; }
.reporte-num {
  width: 34px; height: 34px; border-radius: 10px; background: var(--verde-900); color: var(--lima);
  display: grid; place-items: center; font-family: var(--display); font-size: 16px; flex: none;
}
.reporte-head h3 { font-size: 14.5px; font-weight: 800; }
.reporte-head p { color: var(--tinta-suave); font-size: 11.5px; margin-top: 1px; }
.pipeline-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.pipeline-tags code {
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 10px;
  background: #f0efe7; color: #5d6d62; padding: 2px 7px; border-radius: 5px;
}
.reporte-cuerpo { display: grid; grid-template-columns: 1fr; }
.reporte-cuerpo.con-grafico { grid-template-columns: 1.4fr 1fr; }
.reporte-tabla { max-height: 420px; overflow: auto; }
.reporte-grafico { padding: 16px 20px; border-left: 1px solid #f0eee4; min-height: 260px; position: relative; }
.reporte-grafico canvas { max-height: 300px; }

.detalle-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.detalle-campo { background: #fbfaf5; border: 1px solid #f0eee4; border-radius: 9px; padding: 10px 12px; }
.detalle-campo small { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: .6px; color: #87948b; font-weight: 800; margin-bottom: 2px; }
.detalle-campo strong { font-size: 13px; }
.detalle-lista { margin: 0; padding-left: 18px; font-size: 12.5px; color: #4c5c52; }
.detalle-lista li { margin: 3px 0; }
.seccion-titulo {
  font-size: 11px; font-weight: 800; letter-spacing: .8px; text-transform: uppercase;
  color: var(--verde-700); margin: 18px 0 8px;
}
.seccion-titulo:first-child { margin-top: 0; }

/* ===================== RESPONSIVE ===================== */
@media (max-width: 1080px) {
  .dashboard-grid, .dashboard-grid-2, .reporte-cuerpo.con-grafico { grid-template-columns: 1fr; }
  .reporte-grafico { border-left: 0; border-top: 1px solid #f0eee4; }
  .form-grid { grid-template-columns: 1fr; }
  .repetidor-fila.especies { grid-template-columns: 1fr 1fr; }
  .repetidor-fila.especies .mini:nth-child(5) { grid-column: 1 / -1; }
}
@media (max-width: 860px) {
  .only-mobile { display: inline-grid; }
  .sidebar {
    position: fixed; left: 0; top: 0; bottom: 0; height: 100vh;
    transform: translateX(-105%); transition: transform .22s ease; box-shadow: var(--sombra-lg);
  }
  .sidebar.abierto { transform: translateX(0); }
  .main { width: 100%; }
  .topbar { padding: 16px 18px 14px; }
  .topbar-title h1 { font-size: 21px; }
  .content { padding: 18px; }
  .footer { padding: 12px 18px 20px; }
  .detalle-grid { grid-template-columns: 1fr; }
}
@media (max-width: 620px) {
  .kpi-grid { grid-template-columns: 1fr 1fr; }
  .kpi-valor { font-size: 25px; }
  .repetidor-fila.especies, .repetidor-fila.servicios, .repetidor-fila.insumos { grid-template-columns: 1fr 1fr; }
  .repetidor-fila .btn-quitar { width: 100%; }
  .modal { max-height: 94vh; }
  .toasts { left: 14px; right: 14px; max-width: none; }
}

/* ===================== IMPRESIÓN ===================== */
@media print {
  .sidebar, .topbar-actions, .toolbar, .footer, .btn, .toasts { display: none !important; }
  .main { width: 100%; }
  body { background: #fff; }
  .card { box-shadow: none; }
}
```

---

## A.15 Cliente HTTP y utilidades del frontend

**Archivo:** `frontend/js/api.js` · **236 líneas**

Envoltorio de fetch, manejo de errores, formato de fechas/números y avisos.

```javascript
/* ============================================================
   VerdeVivo · Utilidades de cliente: API, formato, interfaz
   ============================================================ */
(function () {
  "use strict";

  const API = "";

  /* ------------------------- HTTP ------------------------- */
  async function peticion(ruta, opciones = {}) {
    const config = {
      method: opciones.method || "GET",
      headers: { "Content-Type": "application/json" },
    };
    if (opciones.body !== undefined) config.body = JSON.stringify(opciones.body);

    let respuesta;
    try {
      respuesta = await fetch(API + ruta, config);
    } catch (error) {
      throw new Error("No fue posible comunicarse con el servidor. Verifique su conexión.");
    }

    let cuerpo = null;
    const texto = await respuesta.text();
    if (texto) {
      try { cuerpo = JSON.parse(texto); } catch (_) { cuerpo = { error: texto }; }
    }

    if (!respuesta.ok) {
      const detalle = cuerpo && cuerpo.detalles && cuerpo.detalles.length
        ? " " + cuerpo.detalles.join(" · ")
        : "";
      const error = new Error(((cuerpo && cuerpo.error) || "Error inesperado del servidor.") + detalle);
      error.estado = respuesta.status;
      error.cuerpo = cuerpo;
      throw error;
    }
    return cuerpo;
  }

  const api = {
    get: (ruta) => peticion(ruta),
    post: (ruta, body) => peticion(ruta, { method: "POST", body }),
    put: (ruta, body) => peticion(ruta, { method: "PUT", body }),
    del: (ruta) => peticion(ruta, { method: "DELETE" }),
  };

  /* ------------------------- Formato ------------------------- */
  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

  function escapar(valor) {
    return String(valor === null || valor === undefined ? "" : valor)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function moneda(valor) {
    const numero = Number(valor || 0);
    return "$" + numero.toLocaleString("es-CO", { maximumFractionDigits: 0 });
  }

  function numero(valor, decimales = 0) {
    return Number(valor || 0).toLocaleString("es-CO", {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    });
  }

  function fecha(valor, conHora = false) {
    if (!valor) return "—";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor);
    const base = `${String(d.getUTCDate()).padStart(2, "0")} ${MESES[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
    if (!conHora) return base;
    const h = String(d.getUTCHours()).padStart(2, "0");
    const m = String(d.getUTCMinutes()).padStart(2, "0");
    return `${base} · ${h}:${m}`;
  }

  function fechaCorta(valor) {
    if (!valor) return "—";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor);
    return `${String(d.getUTCDate()).padStart(2, "0")}/${String(d.getUTCMonth() + 1).padStart(2, "0")}/${d.getUTCFullYear()}`;
  }

  function paraInputFecha(valor, conHora = true) {
    if (!valor) return "";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor).slice(0, conHora ? 16 : 10);
    const iso = d.toISOString();
    return conHora ? iso.slice(0, 16) : iso.slice(0, 10);
  }

  function iniciales(nombre) {
    return String(nombre || "?")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0].toUpperCase())
      .join("");
  }

  /* ------------------------- Badges ------------------------- */
  const CLASES_ESTADO = {
    Activo: "verde", Inactivo: "gris",
    Disponible: "verde", "Bajo stock": "ambar", Agotado: "rojo",
    Programada: "azul", "En proceso": "ambar", Finalizada: "verde", Cancelada: "gris",
    Suspendido: "ambar", Vencido: "rojo",
  };

  function badge(estado) {
    const clase = CLASES_ESTADO[estado] || "gris";
    return `<span class="badge badge-${clase}">${escapar(estado || "—")}</span>`;
  }

  function chip(texto, clase = "") {
    return `<span class="chip ${clase}">${escapar(texto)}</span>`;
  }

  /* ------------------------- Toasts ------------------------- */
  function toast(mensaje, tipo = "ok", titulo) {
    const contenedor = document.getElementById("toasts");
    if (!contenedor) return;
    const el = document.createElement("div");
    el.className = "toast " + (tipo === "error" ? "error" : tipo === "info" ? "info" : "");
    const titulos = { ok: "Operación exitosa", error: "No se pudo completar", info: "Información" };
    el.innerHTML = `
      <div>
        <strong>${escapar(titulo || titulos[tipo] || titulos.ok)}</strong>
        <small>${escapar(mensaje)}</small>
      </div>`;
    contenedor.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity .25s, transform .25s";
      el.style.opacity = "0";
      el.style.transform = "translateX(16px)";
      setTimeout(() => el.remove(), 260);
    }, tipo === "error" ? 6200 : 3800);
  }

  /* ------------------------- Modal ------------------------- */
  const modal = document.getElementById("modal");
  const modalTitulo = document.getElementById("modal-titulo");
  const modalSub = document.getElementById("modal-subtitulo");
  const modalCuerpo = document.getElementById("modal-cuerpo");
  const modalPie = document.getElementById("modal-pie");

  function abrirModal({ titulo, subtitulo = "", cuerpo, pie = "", ancho = "" }) {
    modalTitulo.textContent = titulo;
    modalSub.textContent = subtitulo;
    modalCuerpo.innerHTML = cuerpo;
    modalPie.innerHTML = pie;
    modal.querySelector(".modal").className = "modal " + ancho;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    const primero = modalCuerpo.querySelector("input, select, textarea, button");
    if (primero) setTimeout(() => primero.focus(), 60);
  }

  function cerrarModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  /* ------------------------- Confirmación ------------------------- */
  const confirmacion = document.getElementById("confirmacion");
  let resolverConfirmacion = null;

  function confirmar({ titulo = "Confirmar acción", texto = "¿Desea continuar?", etiqueta = "Sí, continuar" }) {
    document.getElementById("confirmar-titulo").textContent = titulo;
    document.getElementById("confirmar-texto").textContent = texto;
    document.getElementById("confirmar-si").textContent = etiqueta;
    confirmacion.hidden = false;
    document.body.style.overflow = "hidden";
    return new Promise((resolver) => { resolverConfirmacion = resolver; });
  }

  function finalizarConfirmacion(valor) {
    confirmacion.hidden = true;
    document.body.style.overflow = "";
    if (resolverConfirmacion) resolverConfirmacion(valor);
    resolverConfirmacion = null;
  }

  /* ------------------------- Varios ------------------------- */
  function cargando(contenedor) {
    contenedor.innerHTML = `
      <div class="skeleton-wrap">
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
      </div>`;
  }

  function vacio(emoji, titulo, detalle) {
    return `<div class="vacio"><span class="emoji">${emoji}</span><strong>${escapar(titulo)}</strong><small>${escapar(detalle)}</small></div>`;
  }

  function boton(codigo) {
    return `<button class="btn btn-primario" id="btn-guardar" type="submit">${codigo}</button>`;
  }

  const iconos = {
    editar: '<svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>',
    eliminar: '<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>',
    ver: '<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17a5 5 0 1 1 0-10 5 5 0 0 1 0 10zm0-8a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/></svg>',
    mas: '<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
    buscar: '<svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg>',
  };

  window.Verde = {
    api, peticion,
    escapar, moneda, numero, fecha, fechaCorta, paraInputFecha, iniciales,
    badge, chip, toast, abrirModal, cerrarModal, confirmar, finalizarConfirmacion,
    cargando, vacio, boton, iconos,
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("modal-cerrar").addEventListener("click", cerrarModal);
    modal.addEventListener("click", (e) => { if (e.target === modal) cerrarModal(); });
    document.getElementById("confirmar-no").addEventListener("click", () => finalizarConfirmacion(false));
    document.getElementById("confirmar-si").addEventListener("click", () => finalizarConfirmacion(true));
    confirmacion.addEventListener("click", (e) => { if (e.target === confirmacion) finalizarConfirmacion(false); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (!confirmacion.hidden) finalizarConfirmacion(false);
        else if (!modal.hidden) cerrarModal();
      }
    });
  });
})();
```

---

## A.16 Formularios del frontend

**Archivo:** `frontend/js/formularios.js` · **618 líneas**

Construcción y validación de formularios para las seis entidades.

```javascript
/* ============================================================
   VerdeVivo · Formularios de creación y edición
   ============================================================ */
(function () {
  "use strict";
  const V = window.Verde;
  const { escapar, abrirModal, cerrarModal, toast } = V;

  /* ------------------------- Utilidades de formulario ------------------------- */
  async function pedir(ruta) {
    const r = await V.api.get(ruta);
    return (r && r.datos) || [];
  }

  function opciones(lista, seleccionado, etiqueta, valor = (x) => x._id, extra = "") {
    return lista
      .map((item) => {
        const v = valor(item);
        const sel = String(v) === String(seleccionado || "") ? " selected" : "";
        return `<option value="${escapar(v)}"${sel}>${escapar(etiqueta(item))}${extra}</option>`;
      })
      .join("");
  }

  function campo({ id, etiqueta, tipo = "text", valor = "", req = false, full = false, ayuda = "", attrs = "", placeholder = "" }) {
    return `
      <label class="campo ${full ? "full" : ""}" for="${id}">
        <span>${escapar(etiqueta)} ${req ? '<span class="req">*</span>' : ""}</span>
        <input id="${id}" name="${id}" type="${tipo}" value="${escapar(valor)}"
               placeholder="${escapar(placeholder)}" ${req ? "required" : ""} ${attrs} />
        ${ayuda ? `<span class="ayuda">${escapar(ayuda)}</span>` : ""}
      </label>`;
  }

  function selector({ id, etiqueta, contenido, req = false, full = false, ayuda = "", attrs = "" }) {
    return `
      <label class="campo ${full ? "full" : ""}" for="${id}">
        <span>${escapar(etiqueta)} ${req ? '<span class="req">*</span>' : ""}</span>
        <select id="${id}" name="${id}" ${req ? "required" : ""} ${attrs}>${contenido}</select>
        ${ayuda ? `<span class="ayuda">${escapar(ayuda)}</span>` : ""}
      </label>`;
  }

  function area({ id, etiqueta, valor = "", full = true, filas = 3, ayuda = "", placeholder = "" }) {
    return `
      <label class="campo ${full ? "full" : ""}" for="${id}">
        <span>${escapar(etiqueta)}</span>
        <textarea id="${id}" name="${id}" rows="${filas}" placeholder="${escapar(placeholder)}">${escapar(valor)}</textarea>
        ${ayuda ? `<span class="ayuda">${escapar(ayuda)}</span>` : ""}
      </label>`;
  }

  function pieFormulario(etiquetaGuardar = "Guardar registro") {
    return `
      <button class="btn btn-ghost" type="button" id="btn-cancelar">Cancelar</button>
      <button class="btn btn-primario" type="submit" id="btn-guardar">
        <svg viewBox="0 0 24 24"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        ${escapar(etiquetaGuardar)}
      </button>`;
  }

  function conectarCierre() {
    const cancelar = document.getElementById("btn-cancelar");
    if (cancelar) cancelar.addEventListener("click", cerrarModal);
  }

  function mostrarError(mensaje) {
    const caja = document.getElementById("form-error");
    if (!caja) { toast(mensaje, "error"); return; }
    caja.textContent = mensaje;
    caja.classList.add("visible");
    caja.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function limpiarError() {
    const caja = document.getElementById("form-error");
    if (caja) { caja.textContent = ""; caja.classList.remove("visible"); }
  }

  async function enviar(url, metodo, cuerpo, alGuardar) {
    const boton = document.getElementById("btn-guardar");
    limpiarError();
    if (boton) { boton.disabled = true; boton.dataset.texto = boton.innerHTML; boton.textContent = "Guardando…"; }
    try {
      const respuesta = metodo === "POST" ? await V.api.post(url, cuerpo) : await V.api.put(url, cuerpo);
      toast((respuesta && respuesta.mensaje) || "Registro guardado correctamente.");
      cerrarModal();
      if (alGuardar) await alGuardar();
    } catch (error) {
      mostrarError(error.message);
      toast(error.message, "error");
    } finally {
      if (boton) { boton.disabled = false; boton.innerHTML = boton.dataset.texto || "Guardar"; }
    }
  }

  /* ------------------------- CLIENTES ------------------------- */
  function formularioCliente(registro, alGuardar) {
    const r = registro || {};
    abrirModal({
      titulo: registro ? "Editar cliente" : "Nuevo cliente",
      subtitulo: registro ? "Actualice los datos del cliente" : "Registre una persona o empresa en el sistema",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${campo({ id: "nombre", etiqueta: "Nombre o razón social", valor: r.nombre || "", req: true, full: true, placeholder: "Ej. Laura Martínez" })}
            ${campo({ id: "documento", etiqueta: "Documento (6 a 15 dígitos)", valor: r.documento || "", req: true, attrs: 'inputmode="numeric"' })}
            ${campo({ id: "telefono", etiqueta: "Teléfono", valor: r.telefono || "", req: true, placeholder: "3001234567" })}
            ${campo({ id: "correo", etiqueta: "Correo electrónico", valor: r.correo || "", req: true, tipo: "email" })}
            ${selector({
              id: "estado", etiqueta: "Estado", req: true,
              contenido: opciones(["Activo", "Inactivo"].map((e) => ({ _id: e })), r.estado || "Activo", (x) => x._id),
            })}
            ${campo({ id: "direccion", etiqueta: "Dirección", valor: r.direccion || "", req: true, full: true })}
          </div>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar cliente"),
    });

    conectarCierre();
    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const cuerpo = {
        nombre: document.getElementById("nombre").value.trim(),
        documento: document.getElementById("documento").value.trim(),
        telefono: document.getElementById("telefono").value.trim(),
        correo: document.getElementById("correo").value.trim(),
        direccion: document.getElementById("direccion").value.trim(),
        estado: document.getElementById("estado").value,
      };
      enviar(registro ? `/clientes/${registro._id}` : "/clientes", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- PROPIEDADES ------------------------- */
  async function formularioPropiedad(registro, alGuardar) {
    const r = registro || {};
    let clientes = [];
    try { clientes = await pedir("/clientes"); } catch (e) { toast(e.message, "error"); return; }

    abrirModal({
      titulo: registro ? "Editar propiedad" : "Nueva propiedad",
      subtitulo: "Datos del predio y especies botánicas registradas",
      ancho: "modal-lg",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${selector({
              id: "cliente_id", etiqueta: "Cliente propietario", req: true, full: true,
              contenido: `<option value="">Seleccione un cliente…</option>` +
                opciones(clientes, r.cliente_id, (c) => `${c.nombre} · ${c.documento}`),
            })}
            ${campo({ id: "nombre", etiqueta: "Nombre de la propiedad", valor: r.nombre || "", req: true })}
            ${campo({ id: "ciudad", etiqueta: "Ciudad", valor: r.ciudad || "", req: true })}
            ${campo({ id: "direccion", etiqueta: "Dirección", valor: r.direccion || "", req: true })}
            ${campo({ id: "area_m2", etiqueta: "Área (m²)", valor: r.area_m2 ?? "", req: true, tipo: "number", attrs: 'min="0.01" step="0.01"' })}
            ${selector({
              id: "tipo_propiedad", etiqueta: "Tipo de propiedad", req: true,
              contenido: `<option value="">Seleccione…</option>` +
                opciones(["Casa", "Finca", "Apartamento", "Oficina", "Conjunto residencial", "Parque"].map((t) => ({ _id: t })), r.tipo_propiedad, (x) => x._id),
            })}
          </div>

          <fieldset class="bloque">
            <legend>Especies botánicas (documento embebido)</legend>
            <div class="repetidor" id="lista-especies"></div>
            <button type="button" class="btn-agregar" id="agregar-especie" style="margin-top:10px">
              ${V.iconos.mas} Agregar especie
            </button>
          </fieldset>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar propiedad"),
    });

    conectarCierre();
    const contenedor = document.getElementById("lista-especies");

    function filaEspecie(datos = {}) {
      const div = document.createElement("div");
      div.className = "repetidor-fila especies";
      div.innerHTML = `
        <div class="mini"><span>Nombre común</span><input data-campo="nombre_comun" value="${escapar(datos.nombre_comun || "")}" placeholder="Rosa" /></div>
        <div class="mini"><span>Nombre científico</span><input data-campo="nombre_cientifico" value="${escapar(datos.nombre_cientifico || "")}" placeholder="Rosa spp." /></div>
        <div class="mini"><span>Cantidad</span><input data-campo="cantidad" type="number" min="1" step="1" value="${escapar(datos.cantidad ?? 1)}" /></div>
        <div class="mini"><span>Ubicación</span><input data-campo="ubicacion" value="${escapar(datos.ubicacion || "")}" placeholder="Jardín delantero" /></div>
        <div class="mini"><span>Necesidades de cuidado</span><input data-campo="necesidades_cuidado" value="${escapar(datos.necesidades_cuidado || "")}" placeholder="Riego y poda" /></div>
        <button type="button" class="btn-quitar" title="Quitar especie">${V.iconos.eliminar}</button>`;
      div.querySelector(".btn-quitar").addEventListener("click", () => div.remove());
      contenedor.appendChild(div);
    }

    (r.especies || []).forEach(filaEspecie);
    document.getElementById("agregar-especie").addEventListener("click", () => filaEspecie());

    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const especies = [];
      contenedor.querySelectorAll(".repetidor-fila").forEach((fila) => {
        const valor = (c) => fila.querySelector(`[data-campo="${c}"]`).value.trim();
        const nombre_comun = valor("nombre_comun");
        if (!nombre_comun) return;
        especies.push({
          nombre_comun,
          nombre_cientifico: valor("nombre_cientifico"),
          cantidad: Number(valor("cantidad") || 0),
          ubicacion: valor("ubicacion"),
          necesidades_cuidado: valor("necesidades_cuidado"),
        });
      });

      const cuerpo = {
        cliente_id: document.getElementById("cliente_id").value,
        nombre: document.getElementById("nombre").value.trim(),
        ciudad: document.getElementById("ciudad").value.trim(),
        direccion: document.getElementById("direccion").value.trim(),
        tipo_propiedad: document.getElementById("tipo_propiedad").value,
        area_m2: Number(document.getElementById("area_m2").value),
        especies,
      };
      enviar(registro ? `/propiedades/${registro._id}` : "/propiedades", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- CONTRATOS ------------------------- */
  async function formularioContrato(registro, alGuardar) {
    const r = registro || {};
    let clientes = [];
    try { clientes = await pedir("/clientes"); } catch (e) { toast(e.message, "error"); return; }

    abrirModal({
      titulo: registro ? "Editar contrato" : "Nuevo contrato",
      subtitulo: "Servicios contratados, vigencia y valor acordado",
      ancho: "modal-lg",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${selector({
              id: "cliente_id", etiqueta: "Cliente", req: true, full: true,
              contenido: `<option value="">Seleccione un cliente…</option>` +
                opciones(clientes, r.cliente_id, (c) => `${c.nombre} · ${c.documento}`),
            })}
            ${campo({ id: "fecha_inicio", etiqueta: "Fecha de inicio", valor: V.paraInputFecha(r.fecha_inicio, false), req: true, tipo: "date" })}
            ${campo({ id: "fecha_fin", etiqueta: "Fecha de finalización", valor: V.paraInputFecha(r.fecha_fin, false), req: true, tipo: "date" })}
            ${selector({
              id: "estado", etiqueta: "Estado del contrato", req: true,
              contenido: opciones(["Activo", "Suspendido", "Finalizado", "Vencido"].map((e) => ({ _id: e })), r.estado || "Activo", (x) => x._id),
            })}
          </div>

          <fieldset class="bloque">
            <legend>Servicios del contrato (arreglo embebido)</legend>
            <div class="repetidor" id="lista-servicios"></div>
            <button type="button" class="btn-agregar" id="agregar-servicio" style="margin-top:10px">
              ${V.iconos.mas} Agregar servicio
            </button>
            <div class="total-live"><span>Valor total del contrato (calculado)</span><b id="total-contrato">$0</b></div>
          </fieldset>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar contrato"),
    });

    conectarCierre();
    const contenedor = document.getElementById("lista-servicios");
    const totalEl = document.getElementById("total-contrato");

    function recalcular() {
      let total = 0;
      contenedor.querySelectorAll('[data-campo="precio_acordado"]').forEach((i) => {
        total += Number(i.value || 0);
      });
      totalEl.textContent = V.moneda(total);
    }

    function filaServicio(datos = {}) {
      const div = document.createElement("div");
      div.className = "repetidor-fila servicios";
      div.innerHTML = `
        <div class="mini"><span>Nombre del servicio</span><input data-campo="nombre" value="${escapar(datos.nombre || "")}" placeholder="Poda de setos" /></div>
        <div class="mini"><span>Descripción</span><input data-campo="descripcion" value="${escapar(datos.descripcion || "")}" placeholder="Detalle del servicio" /></div>
        <div class="mini"><span>Precio acordado</span><input data-campo="precio_acordado" type="number" min="1" step="1" value="${escapar(datos.precio_acordado ?? "")}" placeholder="0" /></div>
        <button type="button" class="btn-quitar" title="Quitar servicio">${V.iconos.eliminar}</button>`;
      div.querySelector('[data-campo="precio_acordado"]').addEventListener("input", recalcular);
      div.querySelector(".btn-quitar").addEventListener("click", () => { div.remove(); recalcular(); });
      contenedor.appendChild(div);
    }

    (r.servicios || []).forEach(filaServicio);
    if (!(r.servicios || []).length) filaServicio();
    document.getElementById("agregar-servicio").addEventListener("click", () => filaServicio());
    recalcular();

    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const servicios = [];
      contenedor.querySelectorAll(".repetidor-fila").forEach((fila) => {
        const valor = (c) => fila.querySelector(`[data-campo="${c}"]`).value.trim();
        if (!valor("nombre")) return;
        servicios.push({
          nombre: valor("nombre"),
          descripcion: valor("descripcion"),
          precio_acordado: Number(valor("precio_acordado") || 0),
        });
      });
      const cuerpo = {
        cliente_id: document.getElementById("cliente_id").value,
        servicios,
        fecha_inicio: document.getElementById("fecha_inicio").value,
        fecha_fin: document.getElementById("fecha_fin").value,
        estado: document.getElementById("estado").value,
      };
      enviar(registro ? `/servicios_contratos/${registro._id}` : "/servicios_contratos", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- PERSONAL ------------------------- */
  function formularioPersonal(registro, alGuardar) {
    const r = registro || {};
    abrirModal({
      titulo: registro ? "Editar trabajador" : "Nuevo trabajador",
      subtitulo: "Datos del personal técnico y operativo",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${campo({ id: "nombre", etiqueta: "Nombre completo", valor: r.nombre || "", req: true, full: true })}
            ${campo({ id: "documento", etiqueta: "Documento (6 a 15 dígitos)", valor: r.documento || "", req: true, attrs: 'inputmode="numeric"' })}
            ${campo({ id: "telefono", etiqueta: "Teléfono", valor: r.telefono || "", req: true })}
            ${campo({ id: "correo", etiqueta: "Correo electrónico", valor: r.correo || "", req: true, tipo: "email" })}
            ${selector({
              id: "cargo", etiqueta: "Cargo", req: true,
              contenido: `<option value="">Seleccione…</option>` +
                opciones(["Jardinero", "Paisajista", "Especialista botánico", "Supervisor", "Auxiliar de jardinería"].map((c) => ({ _id: c })), r.cargo, (x) => x._id),
            })}
            ${campo({ id: "salario", etiqueta: "Salario (COP)", valor: r.salario ?? "", tipo: "number", attrs: 'min="0" step="1000"', ayuda: "Opcional" })}
            ${selector({
              id: "estado", etiqueta: "Estado", req: true,
              contenido: opciones(["Activo", "Inactivo"].map((e) => ({ _id: e })), r.estado || "Activo", (x) => x._id),
            })}
            ${campo({
              id: "especialidades", etiqueta: "Especialidades", full: true,
              valor: (r.especialidades || []).join(", "),
              ayuda: "Separe varias especialidades con comas. Ej. Poda, Riego, Control de plagas",
            })}
          </div>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar trabajador"),
    });

    conectarCierre();
    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const salarioTexto = document.getElementById("salario").value;
      const cuerpo = {
        nombre: document.getElementById("nombre").value.trim(),
        documento: document.getElementById("documento").value.trim(),
        telefono: document.getElementById("telefono").value.trim(),
        correo: document.getElementById("correo").value.trim(),
        cargo: document.getElementById("cargo").value,
        estado: document.getElementById("estado").value,
        especialidades: document.getElementById("especialidades").value
          .split(",").map((x) => x.trim()).filter(Boolean),
      };
      if (salarioTexto !== "") cuerpo.salario = Number(salarioTexto);
      enviar(registro ? `/personal/${registro._id}` : "/personal", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- INSUMOS ------------------------- */
  function formularioInsumo(registro, alGuardar) {
    const r = registro || {};
    abrirModal({
      titulo: registro ? "Editar insumo" : "Nuevo insumo",
      subtitulo: "Inventario de insumos y stock mínimo de seguridad",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${campo({ id: "nombre", etiqueta: "Nombre del insumo", valor: r.nombre || "", req: true, full: true, placeholder: "Ej. Fertilizante NPK" })}
            ${campo({ id: "descripcion", etiqueta: "Descripción", valor: r.descripcion || "", full: true })}
            ${selector({
              id: "unidad_medida", etiqueta: "Unidad de medida", req: true,
              contenido: `<option value="">Seleccione…</option>` +
                opciones(["Kilogramos", "Litros", "Unidades", "Bultos", "Metros", "Mililitros"].map((u) => ({ _id: u })), r.unidad_medida, (x) => x._id),
            })}
            ${campo({ id: "existencias", etiqueta: "Existencias actuales", valor: r.existencias ?? 0, req: true, tipo: "number", attrs: 'min="0" step="1"' })}
            ${campo({ id: "stock_minimo", etiqueta: "Stock mínimo", valor: r.stock_minimo ?? 0, req: true, tipo: "number", attrs: 'min="0" step="1"' })}
            <label class="campo" for="estado-calculado">
              <span>Estado del inventario (calculado)</span>
              <input id="estado-calculado" value="${escapar(r.estado || "Se calcula automáticamente")}" disabled />
              <span class="ayuda">Se deriva de las existencias y el stock mínimo.</span>
            </label>
          </div>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Registrar insumo"),
    });

    conectarCierre();
    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const cuerpo = {
        nombre: document.getElementById("nombre").value.trim(),
        descripcion: document.getElementById("descripcion").value.trim(),
        unidad_medida: document.getElementById("unidad_medida").value,
        existencias: Number(document.getElementById("existencias").value),
        stock_minimo: Number(document.getElementById("stock_minimo").value),
      };
      enviar(registro ? `/insumos/${registro._id}` : "/insumos", registro ? "PUT" : "POST", cuerpo, alGuardar);
    });
  }

  /* ------------------------- VISITAS ------------------------- */
  async function formularioVisita(registro, alGuardar) {
    const r = registro || {};
    let propiedades = [], contratos = [], personal = [], insumos = [];
    try {
      [propiedades, contratos, personal, insumos] = await Promise.all([
        pedir("/propiedades"), pedir("/servicios_contratos"), pedir("/personal"), pedir("/insumos"),
      ]);
    } catch (e) {
      toast(e.message, "error");
      return;
    }

    const estadosSinConsumo = ["Programada", "Cancelada"];

    abrirModal({
      titulo: registro ? "Editar visita de mantenimiento" : "Nueva visita de mantenimiento",
      subtitulo: "Programación, personal asignado y consumo de insumos",
      ancho: "modal-lg",
      cuerpo: `
        <form id="form-registro" novalidate>
          <div class="form-grid">
            ${selector({
              id: "propiedad_id", etiqueta: "Propiedad", req: true,
              contenido: `<option value="">Seleccione una propiedad…</option>` +
                opciones(propiedades, r.propiedad_id, (p) => `${p.nombre} · ${p.cliente_nombre || ""}`),
            })}
            ${selector({
              id: "contrato_id", etiqueta: "Contrato asociado", req: true,
              contenido: `<option value="">Seleccione un contrato…</option>` +
                opciones(contratos, r.contrato_id, (c) => `${c.cliente_nombre || "Cliente"} · ${c.estado} · ${V.fechaCorta(c.fecha_inicio)} a ${V.fechaCorta(c.fecha_fin)}`),
              ayuda: "El contrato debe estar activo y pertenecer al mismo cliente de la propiedad.",
            })}
            ${campo({ id: "fecha_programada", etiqueta: "Fecha y hora programada", valor: V.paraInputFecha(r.fecha_programada, true), req: true, tipo: "datetime-local" })}
            ${selector({
              id: "estado", etiqueta: "Estado de la visita", req: true,
              contenido: opciones(["Programada", "En proceso", "Finalizada", "Cancelada"].map((e) => ({ _id: e })), r.estado || "Programada", (x) => x._id),
            })}
          </div>

          <fieldset class="bloque">
            <legend>Personal asignado (referencia)</legend>
            <div class="checks-grid" id="lista-personal">
              ${personal.map((p) => {
                const asignado = (r.personal_asignado || []).some((x) => String(x.personal_id) === String(p._id));
                const inactivo = p.estado !== "Activo";
                return `<label class="check-item ${inactivo ? "inactivo" : ""}">
                  <input type="checkbox" value="${escapar(p._id)}" ${asignado ? "checked" : ""} ${inactivo ? "disabled" : ""} />
                  <span>${escapar(p.nombre)}</span><small>${escapar(p.cargo)}${inactivo ? " · Inactivo" : ""}</small>
                </label>`;
              }).join("") || '<small style="color:#87948b">No hay trabajadores registrados.</small>'}
            </div>
          </fieldset>

          <fieldset class="bloque" id="bloque-insumos">
            <legend>Insumos utilizados (control de inventario)</legend>
            <div class="repetidor" id="lista-insumos"></div>
            <button type="button" class="btn-agregar" id="agregar-insumo" style="margin-top:10px">
              ${V.iconos.mas} Agregar insumo
            </button>
            <div class="ayuda" style="margin-top:8px;font-size:11px;color:#87948b">
              El consumo solo se permite cuando la visita está <b>En proceso</b> o <b>Finalizada</b>.
              El stock se descuenta automáticamente.
            </div>
          </fieldset>

          <fieldset class="bloque">
            <legend>Actividades y observaciones</legend>
            <div class="form-grid">
              ${area({ id: "actividades", etiqueta: "Actividades realizadas (una por línea)", valor: (r.actividades_realizadas || []).join("\n"), filas: 3, full: true })}
              ${area({ id: "observaciones", etiqueta: "Observaciones (una por línea)", valor: (r.observaciones || []).join("\n"), filas: 2, full: true })}
            </div>
          </fieldset>
          <div class="form-error" id="form-error"></div>
        </form>`,
      pie: pieFormulario(registro ? "Guardar cambios" : "Programar visita"),
    });

    conectarCierre();

    const selPropiedad = document.getElementById("propiedad_id");
    const selContrato = document.getElementById("contrato_id");
    const selEstado = document.getElementById("estado");
    const bloqueInsumos = document.getElementById("bloque-insumos");
    const contenedor = document.getElementById("lista-insumos");
    const mapaPropiedades = Object.fromEntries(propiedades.map((p) => [p._id, p]));

    /* Filtra contratos por cliente de la propiedad seleccionada */
    function filtrarContratos() {
      const propiedad = mapaPropiedades[selPropiedad.value];
      const clienteId = propiedad ? propiedad.cliente_id : null;
      const seleccionado = selContrato.value || r.contrato_id || "";
      const disponibles = contratos.filter((c) => !clienteId || c.cliente_id === clienteId);
      selContrato.innerHTML = `<option value="">Seleccione un contrato…</option>` +
        opciones(disponibles, seleccionado, (c) => `${c.estado} · ${V.fechaCorta(c.fecha_inicio)} a ${V.fechaCorta(c.fecha_fin)} · ${V.moneda(c.valor_total)}`);
    }
    filtrarContratos();
    selPropiedad.addEventListener("change", () => { selContrato.value = ""; filtrarContratos(); });

    /* Insumos dinámicos */
    function filaInsumo(datos = {}) {
      const div = document.createElement("div");
      div.className = "repetidor-fila insumos";
      const seleccionado = datos.insumo_id || "";
      div.innerHTML = `
        <div class="mini"><span>Insumo</span>
          <select data-campo="insumo_id">
            <option value="">Seleccione…</option>
            ${insumos.map((i) => `<option value="${escapar(i._id)}" ${String(i._id) === String(seleccionado) ? "selected" : ""}>${escapar(i.nombre)} (${V.numero(i.existencias)} ${escapar(i.unidad_medida)})</option>`).join("")}
          </select>
        </div>
        <div class="mini"><span>Cantidad</span><input data-campo="cantidad" type="number" min="1" step="1" value="${escapar(datos.cantidad ?? 1)}" /></div>
        <div class="mini"><span>Unidad</span><input value="${escapar(datos.unidad_medida || "")}" disabled /></div>
        <button type="button" class="btn-quitar" title="Quitar insumo">${V.iconos.eliminar}</button>`;
      const select = div.querySelector('[data-campo="insumo_id"]');
      const unidad = div.querySelectorAll("input")[1];
      select.addEventListener("change", () => {
        const item = insumos.find((i) => i._id === select.value);
        unidad.value = item ? item.unidad_medida : "";
      });
      div.querySelector(".btn-quitar").addEventListener("click", () => div.remove());
      contenedor.appendChild(div);
    }

    (r.insumos_utilizados || []).forEach(filaInsumo);
    document.getElementById("agregar-insumo").addEventListener("click", () => filaInsumo());

    function aplicarEstado() {
      const sinConsumo = estadosSinConsumo.includes(selEstado.value);
      bloqueInsumos.style.display = sinConsumo ? "none" : "";
      if (sinConsumo) contenedor.innerHTML = "";
    }
    aplicarEstado();
    selEstado.addEventListener("change", aplicarEstado);

    document.getElementById("form-registro").addEventListener("submit", (e) => {
      e.preventDefault();
      const personalAsignado = Array.from(
        document.querySelectorAll("#lista-personal input:checked")
      ).map((i) => i.value);

      const insumosUtilizados = [];
      if (!estadosSinConsumo.includes(selEstado.value)) {
        contenedor.querySelectorAll(".repetidor-fila").forEach((fila) => {
          const insumo_id = fila.querySelector('[data-campo="insumo_id"]').value;
          if (!insumo_id) return;
          insumosUtilizados.push({
            insumo_id,
            cantidad: Number(fila.querySelector('[data-campo="cantidad"]').value || 0),
          });
        });
      }

      const cuerpo = {
        propiedad_id: selPropiedad.value,
        contrato_id: selContrato.value,
        fecha_programada: document.getElementById("fecha_programada").value,
        estado: selEstado.value,
        personal_asignado: personalAsignado,
        insumos_utilizados: insumosUtilizados,
        actividades_realizadas: document.getElementById("actividades").value.split("\n").map((x) => x.trim()).filter(Boolean),
        observaciones: document.getElementById("observaciones").value.split("\n").map((x) => x.trim()).filter(Boolean),
      };

      /* En edición se envían solo los campos modificados para no revalidar
         relaciones históricas (contratos finalizados, personal inactivo, etc.). */
      let payload = cuerpo;
      if (registro) {
        payload = {};
        const original = {
          propiedad_id: registro.propiedad_id,
          contrato_id: registro.contrato_id,
          fecha_programada: registro.fecha_programada,
          estado: registro.estado,
          personal_asignado: (registro.personal_asignado || []).map((p) => p.personal_id),
          insumos_utilizados: (registro.insumos_utilizados || []).map((i) => ({ insumo_id: i.insumo_id, cantidad: i.cantidad })),
          actividades_realizadas: registro.actividades_realizadas || [],
          observaciones: registro.observaciones || [],
        };
        Object.keys(cuerpo).forEach((clave) => {
          if (clave === "fecha_programada") {
            if (V.paraInputFecha(original.fecha_programada, true) !== cuerpo.fecha_programada) payload[clave] = cuerpo[clave];
          } else if (JSON.stringify(original[clave]) !== JSON.stringify(cuerpo[clave])) {
            payload[clave] = cuerpo[clave];
          }
        });
        if (!Object.keys(payload).length) {
          toast("No hay cambios por guardar.", "info");
          return;
        }
      }

      enviar(registro ? `/visitas_mantenimiento/${registro._id}` : "/visitas_mantenimiento", registro ? "PUT" : "POST", payload, alGuardar);
    });
  }

  window.Verde.formularios = {
    clientes: formularioCliente,
    propiedades: formularioPropiedad,
    contratos: formularioContrato,
    personal: formularioPersonal,
    insumos: formularioInsumo,
    visitas: formularioVisita,
  };
})();
```

---

## A.17 Vistas, tablas y gráficas

**Archivo:** `frontend/js/vistas.js` · **881 líneas**

Renderizado de módulos, tablas, detalle de propiedad y los cinco reportes con Chart.js.

```javascript
/* ============================================================
   VerdeVivo · Vistas de la aplicación
   ============================================================ */
(function () {
  "use strict";
  const V = window.Verde;
  const { escapar, moneda, numero, fecha, fechaCorta, badge, chip, toast, confirmar } = V;

  const graficos = [];
  function destruirGraficos() {
    while (graficos.length) {
      const g = graficos.pop();
      try { g.destroy(); } catch (_) { /* ignorar */ }
    }
  }

  function registrarGrafico(grafico) {
    if (grafico) graficos.push(grafico);
  }

  function barraBusqueda(placeholder) {
    return `<div class="search-box">${V.iconos.buscar}<input type="search" id="filtro-q" placeholder="${escapar(placeholder)}" autocomplete="off" /></div>`;
  }

  function selectFiltro(id, etiqueta, valores, actual = "") {
    return `<select id="${id}" aria-label="${escapar(etiqueta)}">
      <option value="">${escapar(etiqueta)}</option>
      ${valores.map((v) => `<option value="${escapar(v)}" ${v === actual ? "selected" : ""}>${escapar(v)}</option>`).join("")}
    </select>`;
  }

  function tabla(cabeceras, filas, vacio) {
    if (!filas.length) return vacio;
    return `<div class="tabla-wrap"><table class="tabla">
      <thead><tr>${cabeceras.map((c) => `<th>${c}</th>`).join("")}</tr></thead>
      <tbody>${filas.join("")}</tbody>
    </table></div>`;
  }

  function acciones(id, opciones = {}) {
    return `<div class="celda-acciones">
      ${opciones.ver ? `<button class="btn-icon" data-accion="ver" data-id="${id}" title="Ver detalle">${V.iconos.ver}</button>` : ""}
      ${opciones.editar !== false ? `<button class="btn-icon" data-accion="editar" data-id="${id}" title="Editar">${V.iconos.editar}</button>` : ""}
      <button class="btn-icon peligro" data-accion="eliminar" data-id="${id}" title="Eliminar">${V.iconos.eliminar}</button>
    </div>`;
  }

  function debounce(fn, ms = 320) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  }

  async function eliminarRegistro(ruta, nombre, alTerminar) {
    const ok = await confirmar({
      titulo: "Eliminar registro",
      texto: `¿Está seguro de eliminar ${nombre}? Esta acción no se puede deshacer.`,
      etiqueta: "Sí, eliminar",
    });
    if (!ok) return;
    try {
      const r = await V.api.del(ruta);
      toast((r && r.mensaje) || "Registro eliminado correctamente.");
      await alTerminar();
    } catch (error) {
      toast(error.message, "error");
    }
  }

  /* ============================================================
     PANEL GENERAL
     ============================================================ */
  async function panel(cont) {
    V.cargando(cont);
    let k;
    try {
      const r = await V.api.get("/analitica/kpis");
      k = r.datos;
    } catch (error) {
      cont.innerHTML = `<div class="card">${V.vacio("⚠️", "No fue posible cargar el tablero", error.message)}</div>`;
      return;
    }

    const porEstado = k.visitas_por_estado || {};
    const proximas = k.proximas_visitas || [];
    const criticos = k.insumos_criticos || [];

    cont.innerHTML = `
      <section class="kpi-grid">
        <article class="kpi">
          <div class="kpi-label">Clientes activos</div>
          <div class="kpi-valor">${numero(k.clientes_activos)}</div>
          <div class="kpi-detalle">de ${numero(k.clientes_total)} clientes registrados</div>
          <span class="kpi-icon">👥</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Propiedades gestionadas</div>
          <div class="kpi-valor">${numero(k.propiedades_total)}</div>
          <div class="kpi-detalle">${numero(k.area_total_m2)} m² de área total</div>
          <span class="kpi-icon">🌳</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Contratos activos</div>
          <div class="kpi-valor">${numero(k.contratos_activos)}</div>
          <div class="kpi-detalle">Cartera: ${moneda(k.valor_cartera)}</div>
          <span class="kpi-icon">📄</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Visitas registradas</div>
          <div class="kpi-valor">${numero(k.visitas_total)}</div>
          <div class="kpi-detalle">Cumplimiento: ${numero(k.tasa_cumplimiento, 1)}%</div>
          <span class="kpi-icon">🗓️</span>
        </article>
        <article class="kpi ${k.insumos_criticos_total ? "kpi-alerta" : ""}">
          <div class="kpi-label">Insumos críticos</div>
          <div class="kpi-valor">${numero(k.insumos_criticos_total)}</div>
          <div class="kpi-detalle">${k.insumo_mas_consumido ? "Más usado: " + escapar(k.insumo_mas_consumido.nombre) : "Sin consumos registrados"}</div>
          <span class="kpi-icon">🌱</span>
        </article>
        <article class="kpi">
          <div class="kpi-label">Personal activo</div>
          <div class="kpi-valor">${numero(k.personal_activo)}</div>
          <div class="kpi-detalle">de ${numero(k.personal_total)} trabajadores</div>
          <span class="kpi-icon">👷</span>
        </article>
      </section>

      <div class="dashboard-grid">
        <section class="card">
          <div class="card-head">
            <div>
              <h3>Distribución de visitas por estado</h3>
              <p>Seguimiento operativo de las visitas de mantenimiento</p>
            </div>
            <span class="chip">${numero(k.visitas_total)} visitas</span>
          </div>
          <div class="chart-box"><canvas id="grafico-estados"></canvas></div>
        </section>

        <section class="card">
          <div class="card-head">
            <div>
              <h3>Próximas visitas (7 días)</h3>
              <p>Programadas y en proceso</p>
            </div>
          </div>
          <div class="lista-simple">
            ${proximas.length ? proximas.map((v) => `
              <div class="lista-item">
                <span class="avatar">${escapar(V.iniciales(v.cliente_nombre))}</span>
                <div class="grow">
                  <strong>${escapar(v.propiedad_nombre)}</strong>
                  <small>${escapar(v.cliente_nombre)} · ${fecha(v.fecha_programada, true)}</small>
                </div>
                ${badge(v.estado)}
              </div>`).join("") : V.vacio("🌤️", "Sin visitas próximas", "No hay visitas programadas en los próximos 7 días.")}
          </div>
        </section>
      </div>

      <div class="dashboard-grid-2">
        <section class="card">
          <div class="card-head">
            <div>
              <h3>Insumos que requieren reposición</h3>
              <p>Existencias iguales o por debajo del stock mínimo</p>
            </div>
            <span class="chip ambar">${criticos.length} alertas</span>
          </div>
          <div class="lista-simple">
            ${criticos.length ? criticos.slice(0, 6).map((i) => `
              <div class="lista-item">
                <span class="avatar alerta">!</span>
                <div class="grow">
                  <strong>${escapar(i.nombre)}</strong>
                  <small>${numero(i.existencias)} ${escapar(i.unidad_medida)} disponibles · mínimo ${numero(i.stock_minimo)}</small>
                </div>
                ${badge(i.estado)}
              </div>`).join("") : V.vacio("✅", "Inventario saludable", "Ningún insumo está por debajo del stock mínimo.")}
          </div>
        </section>

        <section class="card">
          <div class="card-head">
            <div>
              <h3>Resumen de cartera</h3>
              <p>Contratos activos y valor promedio</p>
            </div>
          </div>
          <div class="card-pad">
            <div class="detalle-grid">
              <div class="detalle-campo"><small>Valor de cartera</small><strong>${moneda(k.valor_cartera)}</strong></div>
              <div class="detalle-campo"><small>Promedio por contrato</small><strong>${moneda(k.valor_promedio_contrato)}</strong></div>
              <div class="detalle-campo"><small>Área total gestionada</small><strong>${numero(k.area_total_m2)} m²</strong></div>
              <div class="detalle-campo"><small>Insumo más consumido</small><strong>${k.insumo_mas_consumido ? escapar(k.insumo_mas_consumido.nombre) + " · " + numero(k.insumo_mas_consumido.cantidad) : "—"}</strong></div>
            </div>
            <p class="seccion-titulo">Estado de las visitas</p>
            <div class="chips">
              ${Object.entries(porEstado).map(([estado, total]) => `<span class="chip">${escapar(estado)}: ${total}</span>`).join("") || '<span class="chip neutro">Sin datos</span>'}
            </div>
          </div>
        </section>
      </div>`;

    if (window.Chart && document.getElementById("grafico-estados")) {
      const etiquetas = Object.keys(porEstado);
      registrarGrafico(new Chart(document.getElementById("grafico-estados"), {
        type: "doughnut",
        data: {
          labels: etiquetas,
          datasets: [{
            data: etiquetas.map((e) => porEstado[e]),
            backgroundColor: ["#2b8150", "#c07a13", "#b7d94b", "#9aa79d", "#2a6f97"],
            borderWidth: 2,
            borderColor: "#fff",
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: "62%",
          plugins: {
            legend: { position: "bottom", labels: { boxWidth: 9, boxHeight: 9, usePointStyle: true, font: { size: 11, family: "Manrope" } } },
          },
        },
      }));
    }
  }

  /* ============================================================
     CLIENTES
     ============================================================ */
  async function clientes(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por nombre, documento, correo o dirección…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Activo", "Inactivo"])}
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo cliente</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      try {
        const r = await V.api.get("/clientes?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> registros`;
        contenedor.innerHTML = tabla(
          ["Cliente", "Documento", "Teléfono", "Correo", "Estado", ""],
          datos.map((c) => `
            <tr>
              <td><div class="principal">${escapar(c.nombre)}</div><div class="secundario">${escapar(c.direccion)}</div></td>
              <td>${escapar(c.documento)}</td>
              <td>${escapar(c.telefono)}</td>
              <td>${escapar(c.correo)}</td>
              <td>${badge(c.estado)}</td>
              <td>${acciones(c._id)}</td>
            </tr>`),
          V.vacio("👥", "No hay clientes", "Registre el primer cliente o ajuste los filtros de búsqueda.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar clientes", error.message);
      }
    }

    contenedor.addEventListener("click", async (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "editar") V.formularios.clientes(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/clientes/${registro._id}`, `al cliente "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.clientes(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     PROPIEDADES
     ============================================================ */
  async function propiedades(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por nombre, ciudad, dirección o especie…")}
        ${selectFiltro("filtro-tipo", "Todos los tipos", ["Casa", "Finca", "Apartamento", "Oficina", "Conjunto residencial", "Parque"])}
        <input type="search" id="filtro-ciudad" placeholder="Ciudad" style="max-width:150px" />
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nueva propiedad</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const tipo = document.getElementById("filtro-tipo").value;
      const ciudad = document.getElementById("filtro-ciudad").value.trim();
      if (q) params.set("q", q);
      if (tipo) params.set("tipo_propiedad", tipo);
      if (ciudad) params.set("ciudad", ciudad);
      try {
        const r = await V.api.get("/propiedades?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> propiedades`;
        contenedor.innerHTML = tabla(
          ["Propiedad", "Cliente", "Ciudad", "Tipo", "Área", "Especies", "Visitas", ""],
          datos.map((p) => `
            <tr>
              <td><div class="principal">${escapar(p.nombre)}</div><div class="secundario">${escapar(p.direccion)}</div></td>
              <td><div>${escapar(p.cliente_nombre)}</div><div class="secundario">${escapar(p.cliente_documento)}</div></td>
              <td>${escapar(p.ciudad)}</td>
              <td>${chip(p.tipo_propiedad, "neutro")}</td>
              <td class="num">${numero(p.area_m2)} m²</td>
              <td><span class="chip">${numero(p.total_especies)}</span></td>
              <td><span class="chip azul">${numero(p.total_visitas)}</span></td>
              <td>${acciones(p._id, { ver: true })}</td>
            </tr>`),
          V.vacio("🏡", "No hay propiedades", "Registre una propiedad o ajuste los filtros.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar propiedades", error.message);
      }
    }

    async function verDetalle(propiedad) {
      let historial = [];
      try {
        const r = await V.api.get(`/propiedades/${propiedad._id}/historial`);
        historial = r.datos || [];
      } catch (_) { /* historial opcional */ }

      V.abrirModal({
        titulo: propiedad.nombre,
        subtitulo: `${propiedad.tipo_propiedad} · ${propiedad.ciudad} · ${numero(propiedad.area_m2)} m²`,
        ancho: "modal-lg",
        cuerpo: `
          <div class="detalle-grid">
            <div class="detalle-campo"><small>Cliente</small><strong>${escapar(propiedad.cliente_nombre)}</strong></div>
            <div class="detalle-campo"><small>Documento</small><strong>${escapar(propiedad.cliente_documento || "—")}</strong></div>
            <div class="detalle-campo"><small>Dirección</small><strong>${escapar(propiedad.direccion)}</strong></div>
            <div class="detalle-campo"><small>Visitas registradas</small><strong>${numero(propiedad.total_visitas)}</strong></div>
          </div>
          <p class="seccion-titulo">Especies botánicas (${(propiedad.especies || []).length})</p>
          ${(propiedad.especies || []).length ? `<div class="tabla-wrap"><table class="tabla" style="min-width:520px">
            <thead><tr><th>Nombre común</th><th>Nombre científico</th><th>Cantidad</th><th>Ubicación</th><th>Cuidados</th></tr></thead>
            <tbody>${propiedad.especies.map((e) => `
              <tr><td class="principal">${escapar(e.nombre_comun)}</td><td><i>${escapar(e.nombre_cientifico)}</i></td>
              <td class="num">${numero(e.cantidad)}</td><td>${escapar(e.ubicacion)}</td><td class="secundario">${escapar(e.necesidades_cuidado)}</td></tr>`).join("")}
            </tbody></table></div>` : '<p class="secundario">Sin especies registradas.</p>'}
          <p class="seccion-titulo">Historial de mantenimiento (${historial.length})</p>
          ${historial.length ? `<div class="tabla-wrap"><table class="tabla" style="min-width:520px">
            <thead><tr><th>Fecha</th><th>Estado</th><th>Servicios del contrato</th><th>Actividades</th></tr></thead>
            <tbody>${historial.map((h) => `
              <tr><td>${fecha(h.fecha_programada, true)}</td><td>${badge(h.estado)}</td>
              <td><div class="chips">${(h.servicios_contratados || []).map((s) => chip(s)).join("") || "—"}</div></td>
              <td class="secundario">${(h.actividades_realizadas || []).join(" · ") || "—"}</td></tr>`).join("")}
            </tbody></table></div>` : '<p class="secundario">Esta propiedad aún no tiene visitas.</p>'}`,
        pie: `<button class="btn btn-ghost" type="button" id="btn-cancelar">Cerrar</button>`,
      });
      document.getElementById("btn-cancelar").addEventListener("click", V.cerrarModal);
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "ver") verDetalle(registro);
      if (boton.dataset.accion === "editar") V.formularios.propiedades(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/propiedades/${registro._id}`, `la propiedad "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.propiedades(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-ciudad").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-tipo").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     CONTRATOS
     ============================================================ */
  async function contratos(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por servicio o descripción…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Activo", "Suspendido", "Finalizado", "Vencido"])}
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo contrato</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      try {
        const r = await V.api.get("/servicios_contratos?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> contratos`;
        contenedor.innerHTML = tabla(
          ["Cliente", "Servicios", "Vigencia", "Valor total", "Estado", ""],
          datos.map((c) => {
            const servicios = c.servicios || [];
            return `<tr>
              <td><div class="principal">${escapar(c.cliente_nombre)}</div><div class="secundario">${escapar(c.cliente_documento)}</div></td>
              <td><div class="chips">
                ${servicios.slice(0, 2).map((s) => chip(s.nombre)).join("")}
                ${servicios.length > 2 ? chip(`+${servicios.length - 2}`, "neutro") : ""}
              </div></td>
              <td><div>${fechaCorta(c.fecha_inicio)}</div><div class="secundario">hasta ${fechaCorta(c.fecha_fin)}</div></td>
              <td class="num principal">${moneda(c.valor_total)}</td>
              <td>${badge(c.estado)}</td>
              <td>${acciones(c._id, { ver: true })}</td>
            </tr>`;
          }),
          V.vacio("📄", "No hay contratos", "Registre un contrato o ajuste los filtros.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar contratos", error.message);
      }
    }

    function verDetalle(contrato) {
      const servicios = contrato.servicios || [];
      V.abrirModal({
        titulo: "Contrato de " + contrato.cliente_nombre,
        subtitulo: `${contrato.estado} · ${fechaCorta(contrato.fecha_inicio)} a ${fechaCorta(contrato.fecha_fin)}`,
        cuerpo: `
          <div class="detalle-grid">
            <div class="detalle-campo"><small>Cliente</small><strong>${escapar(contrato.cliente_nombre)}</strong></div>
            <div class="detalle-campo"><small>Documento</small><strong>${escapar(contrato.cliente_documento || "—")}</strong></div>
            <div class="detalle-campo"><small>Valor total</small><strong>${moneda(contrato.valor_total)}</strong></div>
            <div class="detalle-campo"><small>Servicios</small><strong>${servicios.length}</strong></div>
          </div>
          <p class="seccion-titulo">Servicios contratados (documento embebido)</p>
          <div class="tabla-wrap"><table class="tabla" style="min-width:480px">
            <thead><tr><th>Servicio</th><th>Descripción</th><th class="num">Precio acordado</th></tr></thead>
            <tbody>${servicios.map((s) => `<tr><td class="principal">${escapar(s.nombre)}</td><td class="secundario">${escapar(s.descripcion)}</td><td class="num">${moneda(s.precio_acordado)}</td></tr>`).join("")}</tbody>
          </table></div>`,
        pie: `<button class="btn btn-ghost" type="button" id="btn-cancelar">Cerrar</button>`,
      });
      document.getElementById("btn-cancelar").addEventListener("click", V.cerrarModal);
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "ver") verDetalle(registro);
      if (boton.dataset.accion === "editar") V.formularios.contratos(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/servicios_contratos/${registro._id}`, "este contrato", cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.contratos(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     PERSONAL
     ============================================================ */
  async function personal(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar por nombre, documento, correo o especialidad…")}
        ${selectFiltro("filtro-cargo", "Todos los cargos", ["Jardinero", "Paisajista", "Especialista botánico", "Supervisor", "Auxiliar de jardinería"])}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Activo", "Inactivo"])}
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo trabajador</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const cargo = document.getElementById("filtro-cargo").value;
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (cargo) params.set("cargo", cargo);
      if (estado) params.set("estado", estado);
      try {
        const r = await V.api.get("/personal?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> trabajadores`;
        contenedor.innerHTML = tabla(
          ["Trabajador", "Documento", "Cargo", "Especialidades", "Salario", "Estado", ""],
          datos.map((p) => `
            <tr>
              <td><div class="principal">${escapar(p.nombre)}</div><div class="secundario">${escapar(p.correo)} · ${escapar(p.telefono)}</div></td>
              <td>${escapar(p.documento)}</td>
              <td>${chip(p.cargo, "neutro")}</td>
              <td><div class="chips">${(p.especialidades || []).slice(0, 3).map((e) => chip(e)).join("") || '<span class="secundario">—</span>'}</div></td>
              <td class="num">${p.salario ? moneda(p.salario) : "—"}</td>
              <td>${badge(p.estado)}</td>
              <td>${acciones(p._id)}</td>
            </tr>`),
          V.vacio("👷", "No hay trabajadores", "Registre personal técnico u operativo.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar personal", error.message);
      }
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "editar") V.formularios.personal(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/personal/${registro._id}`, `al trabajador "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.personal(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-cargo").addEventListener("change", cargar);
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     VISITAS
     ============================================================ */
  async function visitas(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar en actividades u observaciones…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Programada", "En proceso", "Finalizada", "Cancelada"])}
        <input type="date" id="filtro-desde" title="Desde" />
        <input type="date" id="filtro-hasta" title="Hasta" />
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nueva visita</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      const desde = document.getElementById("filtro-desde").value;
      const hasta = document.getElementById("filtro-hasta").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      if (desde) params.set("desde", desde);
      if (hasta) params.set("hasta", hasta + "T23:59:59");
      try {
        const r = await V.api.get("/visitas_mantenimiento?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> visitas`;
        contenedor.innerHTML = tabla(
          ["Fecha programada", "Propiedad / Cliente", "Contrato", "Personal", "Insumos", "Estado", ""],
          datos.map((v) => `
            <tr>
              <td><div class="principal">${fecha(v.fecha_programada, true)}</div><div class="secundario">${escapar(v.propiedad_ciudad)}</div></td>
              <td><div class="principal">${escapar(v.propiedad_nombre)}</div><div class="secundario">${escapar(v.cliente_nombre)}</div></td>
              <td>${badge(v.contrato_estado)}<div class="secundario" style="margin-top:3px">${(v.servicios_contratados || []).slice(0, 2).map(escapar).join(" · ") || "—"}</div></td>
              <td><span class="chip azul">${numero(v.total_personal)}</span></td>
              <td><span class="chip ${v.total_insumos ? "" : "neutro"}">${numero(v.total_insumos)}</span></td>
              <td>${badge(v.estado)}</td>
              <td>${acciones(v._id, { ver: true })}</td>
            </tr>`),
          V.vacio("🗓️", "No hay visitas", "Programe una visita o ajuste los filtros.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar visitas", error.message);
      }
    }

    function verDetalle(visita) {
      V.abrirModal({
        titulo: "Visita de mantenimiento",
        subtitulo: `${fecha(visita.fecha_programada, true)} · ${visita.estado}`,
        ancho: "modal-lg",
        cuerpo: `
          <div class="detalle-grid">
            <div class="detalle-campo"><small>Propiedad</small><strong>${escapar(visita.propiedad_nombre)}</strong></div>
            <div class="detalle-campo"><small>Cliente</small><strong>${escapar(visita.cliente_nombre)}</strong></div>
            <div class="detalle-campo"><small>Contrato</small><strong>${escapar(visita.contrato_estado)}</strong></div>
            <div class="detalle-campo"><small>Ciudad</small><strong>${escapar(visita.propiedad_ciudad)}</strong></div>
          </div>
          <p class="seccion-titulo">Personal asignado</p>
          <div class="chips">${(visita.personal_asignado || []).map((p) => chip(p.nombre)).join("") || '<span class="secundario">Sin personal asignado.</span>'}</div>
          <p class="seccion-titulo">Servicios del contrato</p>
          <div class="chips">${(visita.servicios_contratados || []).map((s) => chip(s, "neutro")).join("") || '<span class="secundario">Sin servicios.</span>'}</div>
          <p class="seccion-titulo">Insumos utilizados</p>
          ${(visita.insumos_utilizados || []).length ? `<div class="tabla-wrap"><table class="tabla" style="min-width:420px">
            <thead><tr><th>Insumo</th><th class="num">Cantidad</th><th>Unidad</th></tr></thead>
            <tbody>${visita.insumos_utilizados.map((i) => `<tr><td>${escapar(i.nombre)}</td><td class="num">${numero(i.cantidad)}</td><td>${escapar(i.unidad_medida)}</td></tr>`).join("")}</tbody>
          </table></div>` : '<p class="secundario">Sin consumo de insumos.</p>'}
          <p class="seccion-titulo">Actividades realizadas</p>
          ${(visita.actividades_realizadas || []).length ? `<ul class="detalle-lista">${visita.actividades_realizadas.map((a) => `<li>${escapar(a)}</li>`).join("")}</ul>` : '<p class="secundario">Sin actividades registradas.</p>'}
          <p class="seccion-titulo">Observaciones</p>
          ${(visita.observaciones || []).length ? `<ul class="detalle-lista">${visita.observaciones.map((o) => `<li>${escapar(o)}</li>`).join("")}</ul>` : '<p class="secundario">Sin observaciones.</p>'}`,
        pie: `<button class="btn btn-ghost" type="button" id="btn-cancelar">Cerrar</button>`,
      });
      document.getElementById("btn-cancelar").addEventListener("click", V.cerrarModal);
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "ver") verDetalle(registro);
      if (boton.dataset.accion === "editar") V.formularios.visitas(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/visitas_mantenimiento/${registro._id}`, "esta visita de mantenimiento", cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.visitas(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    document.getElementById("filtro-desde").addEventListener("change", cargar);
    document.getElementById("filtro-hasta").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     INSUMOS
     ============================================================ */
  async function insumos(cont) {
    cont.innerHTML = `
      <div class="toolbar">
        ${barraBusqueda("Buscar insumo por nombre o descripción…")}
        ${selectFiltro("filtro-estado", "Todos los estados", ["Disponible", "Bajo stock", "Agotado"])}
        <label class="filtro-check"><input type="checkbox" id="filtro-bajo" /> Solo stock crítico</label>
        <span class="spacer"></span>
        <span class="conteo" id="conteo"></span>
        <button class="btn btn-primario" id="btn-nuevo">${V.iconos.mas} Nuevo insumo</button>
      </div>
      <div class="card" id="tabla-contenedor"></div>`;

    const contenedor = document.getElementById("tabla-contenedor");
    let datos = [];

    async function cargar() {
      const params = new URLSearchParams();
      const q = document.getElementById("filtro-q").value.trim();
      const estado = document.getElementById("filtro-estado").value;
      if (q) params.set("q", q);
      if (estado) params.set("estado", estado);
      if (document.getElementById("filtro-bajo").checked) params.set("bajo_stock", "true");
      try {
        const r = await V.api.get("/insumos?" + params.toString());
        datos = r.datos || [];
        document.getElementById("conteo").innerHTML = `<b>${datos.length}</b> insumos`;
        contenedor.innerHTML = tabla(
          ["Insumo", "Unidad", "Existencias", "Stock mínimo", "Estado", ""],
          datos.map((i) => `
            <tr>
              <td><div class="principal">${escapar(i.nombre)}</div><div class="secundario">${escapar(i.descripcion || "Sin descripción")}</div></td>
              <td>${escapar(i.unidad_medida)}</td>
              <td class="num principal">${numero(i.existencias)}</td>
              <td class="num">${numero(i.stock_minimo)}</td>
              <td>${badge(i.estado)}</td>
              <td>${acciones(i._id)}</td>
            </tr>`),
          V.vacio("🌱", "No hay insumos", "Registre insumos para controlar el inventario.")
        );
      } catch (error) {
        contenedor.innerHTML = V.vacio("⚠️", "Error al consultar insumos", error.message);
      }
    }

    contenedor.addEventListener("click", (e) => {
      const boton = e.target.closest("[data-accion]");
      if (!boton) return;
      const registro = datos.find((d) => d._id === boton.dataset.id);
      if (!registro) return;
      if (boton.dataset.accion === "editar") V.formularios.insumos(registro, cargar);
      if (boton.dataset.accion === "eliminar") eliminarRegistro(`/insumos/${registro._id}`, `el insumo "${registro.nombre}"`, cargar);
    });

    document.getElementById("btn-nuevo").addEventListener("click", () => V.formularios.insumos(null, cargar));
    document.getElementById("filtro-q").addEventListener("input", debounce(cargar));
    document.getElementById("filtro-estado").addEventListener("change", cargar);
    document.getElementById("filtro-bajo").addEventListener("change", cargar);
    await cargar();
  }

  /* ============================================================
     ANALÍTICA · CINCO CONSULTAS DE AGREGACIÓN
     ============================================================ */
  function tarjetaReporte(numeroReporte, titulo, descripcion, etapas, cuerpo) {
    return `<section class="card reporte">
      <header class="reporte-head">
        <div class="titulo">
          <span class="reporte-num">${numeroReporte}</span>
          <div><h3>${escapar(titulo)}</h3><p>${escapar(descripcion)}</p></div>
        </div>
        <div class="pipeline-tags">${etapas.map((e) => `<code>${escapar(e)}</code>`).join("")}</div>
      </header>
      ${cuerpo}
    </section>`;
  }

  async function analitica(cont) {
    V.cargando(cont);
    let clientesProp, visitasDetalle, visitasEstado, insumosTop, serviciosTop;
    try {
      [clientesProp, visitasDetalle, visitasEstado, insumosTop, serviciosTop] = await Promise.all([
        V.api.get("/analitica/clientes-propiedades"),
        V.api.get("/analitica/visitas-detalle"),
        V.api.get("/analitica/visitas-estado"),
        V.api.get("/analitica/insumos-mas-utilizados?limite=8"),
        V.api.get("/analitica/servicios-mas-contratados"),
      ]);
    } catch (error) {
      cont.innerHTML = `<div class="card">${V.vacio("⚠️", "No fue posible cargar la analítica", error.message)}</div>`;
      return;
    }

    const a = clientesProp.datos || [];
    const b = visitasDetalle.datos || [];
    const c = visitasEstado.datos || [];
    const d = insumosTop.datos || [];
    const e = serviciosTop.datos || [];

    cont.innerHTML = `<div class="analitica-grid">
      ${tarjetaReporte(1, "Clientes y sus propiedades", "Total de propiedades, área gestionada y especies por cliente", ["$lookup", "$addFields", "$project", "$sort"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Cliente", "Propiedades", "Área total", "Especies", "Detalle"], a.map((x) => `
              <tr>
                <td><div class="principal">${escapar(x.nombre)}</div><div class="secundario">${escapar(x.documento)} · ${escapar(x.estado)}</div></td>
                <td class="num principal">${numero(x.total_propiedades)}</td>
                <td class="num">${numero(x.area_total_m2)} m²</td>
                <td class="num">${numero(x.total_especies)}</td>
                <td><div class="chips">${(x.detalle_propiedades || []).slice(0, 3).map((p) => chip(p.nombre, "neutro")).join("") || "—"}</div></td>
              </tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-clientes"></canvas></div>
        </div>`)}

      ${tarjetaReporte(2, "Visitas con detalle completo", "Propiedad, cliente, contrato, personal e insumos de cada visita", ["$lookup ×3", "$unwind", "$project", "$sort"], `
        <div class="reporte-tabla" style="max-height:460px">
          ${tabla(["Fecha", "Propiedad", "Cliente", "Contrato", "Personal", "Insumos", "Estado"], b.map((x) => `
            <tr>
              <td>${fecha(x.fecha_programada, true)}</td>
              <td><div class="principal">${escapar(x.propiedad_nombre)}</div><div class="secundario">${escapar(x.propiedad_ciudad)}</div></td>
              <td>${escapar(x.cliente_nombre)}</td>
              <td>${badge(x.contrato_estado)}</td>
              <td><div class="chips">${(x.personal_asignado || []).map((p) => chip(p)).join("") || "—"}</div></td>
              <td><div class="chips">${(x.insumos_utilizados || []).map((i) => chip(`${i.nombre} ×${i.cantidad}`, "neutro")).join("") || "—"}</div></td>
              <td>${badge(x.estado)}</td>
            </tr>`), "")}
        </div>`)}

      ${tarjetaReporte(3, "Distribución de visitas por estado", "Conteo y porcentaje de participación de cada estado", ["$facet", "$group", "$unwind", "$project", "$sort"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Estado", "Total", "Porcentaje"], c.map((x) => `
              <tr><td>${badge(x.estado)}</td><td class="num principal">${numero(x.total)}</td>
              <td class="num">${numero(x.porcentaje, 1)}%</td></tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-estados"></canvas></div>
        </div>`)}

      ${tarjetaReporte(4, "Insumos más utilizados", "Ranking por cantidad consumida y estado actual del inventario", ["$unwind", "$group", "$lookup", "$sort", "$limit"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Insumo", "Cantidad total", "Visitas", "Existencias", "Estado"], d.map((x) => `
              <tr><td class="principal">${escapar(x.nombre)}</td>
              <td class="num">${numero(x.cantidad_total)} ${escapar(x.unidad_medida)}</td>
              <td class="num">${numero(x.total_visitas)}</td>
              <td class="num">${numero(x.existencias_actuales)}</td>
              <td>${badge(x.estado_inventario)}</td></tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-insumos"></canvas></div>
        </div>`)}

      ${tarjetaReporte(5, "Servicios más contratados", "Frecuencia, ingreso total y precio promedio por servicio", ["$unwind", "$group", "$project", "$sort"], `
        <div class="reporte-cuerpo con-grafico">
          <div class="reporte-tabla">
            ${tabla(["Servicio", "Veces contratado", "Ingreso total", "Precio promedio"], e.map((x) => `
              <tr><td class="principal">${escapar(x.servicio)}</td>
              <td class="num">${numero(x.veces_contratado)}</td>
              <td class="num">${moneda(x.ingreso_total)}</td>
              <td class="num">${moneda(x.precio_promedio)}</td></tr>`), "")}
          </div>
          <div class="reporte-grafico"><canvas id="g-servicios"></canvas></div>
        </div>`)}
    </div>`;

    if (!window.Chart) return;

    const verde = "#2b8150", lima = "#b7d94b", ambar = "#c07a13", azul = "#2a6f97";
    const baseOpciones = {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10, family: "Manrope" }, color: "#5b6b60" } },
        y: { beginAtZero: true, grid: { color: "#f0eee4" }, ticks: { font: { size: 10, family: "Manrope" }, color: "#5b6b60" } },
      },
    };

    if (document.getElementById("g-clientes")) {
      registrarGrafico(new Chart(document.getElementById("g-clientes"), {
        type: "bar",
        data: {
          labels: a.slice(0, 8).map((x) => x.nombre.length > 18 ? x.nombre.slice(0, 17) + "…" : x.nombre),
          datasets: [{ label: "Área total (m²)", data: a.slice(0, 8).map((x) => x.area_total_m2), backgroundColor: verde, borderRadius: 6 }],
        },
        options: baseOpciones,
      }));
    }

    if (document.getElementById("g-estados")) {
      registrarGrafico(new Chart(document.getElementById("g-estados"), {
        type: "doughnut",
        data: {
          labels: c.map((x) => x.estado),
          datasets: [{ data: c.map((x) => x.total), backgroundColor: [verde, ambar, lima, "#9aa79d"], borderWidth: 2, borderColor: "#fff" }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: "60%",
          plugins: { legend: { position: "bottom", labels: { boxWidth: 9, usePointStyle: true, font: { size: 11, family: "Manrope" } } } },
        },
      }));
    }

    if (document.getElementById("g-insumos")) {
      registrarGrafico(new Chart(document.getElementById("g-insumos"), {
        type: "bar",
        data: {
          labels: d.map((x) => x.nombre.length > 16 ? x.nombre.slice(0, 15) + "…" : x.nombre),
          datasets: [{ label: "Cantidad consumida", data: d.map((x) => x.cantidad_total), backgroundColor: lima, borderRadius: 6 }],
        },
        options: { ...baseOpciones, indexAxis: "y", scales: { x: { beginAtZero: true, grid: { color: "#f0eee4" } }, y: { grid: { display: false } } } },
      }));
    }

    const opcionesHorizontales = {
      ...baseOpciones,
      indexAxis: "y",
      scales: { x: { beginAtZero: true, grid: { color: "#f0eee4" } }, y: { grid: { display: false } } },
    };

    if (document.getElementById("g-servicios")) {
      registrarGrafico(new Chart(document.getElementById("g-servicios"), {
        type: "bar",
        data: {
          labels: e.slice(0, 8).map((x) => x.servicio.length > 16 ? x.servicio.slice(0, 15) + "…" : x.servicio),
          datasets: [{ label: "Veces contratado", data: e.slice(0, 8).map((x) => x.veces_contratado), backgroundColor: azul, borderRadius: 6 }],
        },
        options: opcionesHorizontales,
      }));
    }
  }

  window.Verde.vistas = {
    panel, clientes, propiedades, contratos, personal, visitas, insumos, analitica, destruirGraficos,
  };
})();
```

---

## A.18 Enrutador de la SPA

**Archivo:** `frontend/js/app.js` · **136 líneas**

Navegación por hash, estado de la vista y verificación de conexión con la API.

```javascript
/* ============================================================
   VerdeVivo · Enrutador y arranque de la aplicación
   ============================================================ */
(function () {
  "use strict";
  const V = window.Verde;
  const contenido = document.getElementById("contenido");
  const titulo = document.getElementById("titulo-vista");
  const subtitulo = document.getElementById("subtitulo-vista");
  const sidebar = document.getElementById("sidebar");

  const RUTAS = {
    panel: {
      titulo: "Panel general",
      subtitulo: "Resumen operativo del sistema de paisajismo",
      render: V.vistas.panel,
    },
    clientes: {
      titulo: "Clientes",
      subtitulo: "Personas y empresas que contratan los servicios",
      render: V.vistas.clientes,
    },
    propiedades: {
      titulo: "Propiedades y control botánico",
      subtitulo: "Predios gestionados y especies vegetales registradas",
      render: V.vistas.propiedades,
    },
    contratos: {
      titulo: "Servicios y contratos",
      subtitulo: "Servicios contratados, vigencias y valor acordado",
      render: V.vistas.contratos,
    },
    personal: {
      titulo: "Personal técnico y operativo",
      subtitulo: "Jardineros, paisajistas y especialistas botánicos",
      render: V.vistas.personal,
    },
    visitas: {
      titulo: "Visitas de mantenimiento",
      subtitulo: "Programación, ejecución y consumo de insumos",
      render: V.vistas.visitas,
    },
    insumos: {
      titulo: "Insumos e inventario",
      subtitulo: "Existencias, stock mínimo y alertas de reposición",
      render: V.vistas.insumos,
    },
    analitica: {
      titulo: "Analítica y reportes",
      subtitulo: "Cinco consultas de agregación sobre MongoDB Atlas",
      render: V.vistas.analitica,
    },
  };

  let vistaActual = "panel";
  let renderizando = false;

  function rutaActual() {
    const hash = (location.hash || "#/panel").replace(/^#\/?/, "").split("?")[0];
    return RUTAS[hash] ? hash : "panel";
  }

  async function renderizar() {
    if (renderizando) return;
    renderizando = true;
    const clave = rutaActual();
    vistaActual = clave;
    const config = RUTAS[clave];

    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("activo", item.dataset.vista === clave);
    });
    titulo.textContent = config.titulo;
    subtitulo.textContent = config.subtitulo;
    document.title = `${config.titulo} · VerdeVivo`;

    V.vistas.destruirGraficos();
    sidebar.classList.remove("abierto");

    try {
      await config.render(contenido);
    } catch (error) {
      contenido.innerHTML = `<div class="card">${V.vacio("⚠️", "Ocurrió un error al cargar la vista", error.message)}</div>`;
    } finally {
      renderizando = false;
    }
  }

  async function verificarConexion() {
    const caja = document.getElementById("db-status");
    try {
      const r = await V.api.get("/api/health");
      const conteos = r.colecciones || {};
      const total = Object.values(conteos).reduce((a, b) => a + b, 0);
      caja.innerHTML = `
        <span class="dot dot-ok"></span>
        <div><strong>Base de datos conectada</strong><small>${V.escapar(r.base_de_datos)} · ${total} documentos</small></div>`;
    } catch (error) {
      caja.innerHTML = `
        <span class="dot dot-error"></span>
        <div><strong>Sin conexión a la base</strong><small>${V.escapar(error.message.slice(0, 46))}</small></div>`;
    }
  }

  document.getElementById("btn-refrescar").addEventListener("click", () => {
    renderizar();
    verificarConexion();
    V.toast("Datos actualizados.", "info", "Actualización");
  });

  document.getElementById("btn-menu").addEventListener("click", () => {
    sidebar.classList.toggle("abierto");
  });

  window.addEventListener("hashchange", renderizar);

  document.addEventListener("click", (e) => {
    if (window.innerWidth <= 860 && sidebar.classList.contains("abierto") &&
        !sidebar.contains(e.target) && !e.target.closest("#btn-menu")) {
      sidebar.classList.remove("abierto");
    }
  });

  function iniciar() {
    if (!location.hash) location.hash = "#/panel";
    verificarConexion();
    renderizar();
    setInterval(verificarConexion, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
```

---

## A.19 Semilla de datos e índices

**Archivo:** `seed.py` · **670 líneas**

Restablece las colecciones, crea los índices y carga los datos de demostración.

```python
# ============================================================
#  Semilla de datos de demostración - jardineria_db
#  Ejecutar:  python seed.py
#  ADVERTENCIA: elimina y vuelve a crear los documentos de las
#  seis colecciones del proyecto.
# ============================================================
from datetime import datetime

from backend.config import (
    clientes,
    db,
    insumos,
    personal,
    propiedades,
    servicios_contratos,
    visitas_mantenimiento,
)
from backend.validators import calcular_estado_insumo


def fecha(anio, mes, dia, hora=8, minuto=0):
    return datetime(anio, mes, dia, hora, minuto)


def limpiar():
    for coleccion in (
        visitas_mantenimiento,
        servicios_contratos,
        propiedades,
        clientes,
        personal,
        insumos,
    ):
        coleccion.delete_many({})
    print("Colecciones limpiadas.")


def crear_indices():
    clientes.create_index("documento", unique=True, name="uq_clientes_documento")
    clientes.create_index("nombre")
    clientes.create_index("estado")

    propiedades.create_index("cliente_id")
    propiedades.create_index("ciudad")
    propiedades.create_index("nombre")

    servicios_contratos.create_index("cliente_id")
    servicios_contratos.create_index("estado")
    servicios_contratos.create_index("fecha_inicio")

    personal.create_index("documento", unique=True, name="uq_personal_documento")
    personal.create_index("cargo")

    visitas_mantenimiento.create_index("propiedad_id")
    visitas_mantenimiento.create_index("contrato_id")
    visitas_mantenimiento.create_index("estado")
    visitas_mantenimiento.create_index("fecha_programada")
    visitas_mantenimiento.create_index("personal_asignado.personal_id")
    visitas_mantenimiento.create_index("insumos_utilizados.insumo_id")

    insumos.create_index("nombre")
    insumos.create_index("estado")
    print("Índices creados.")


def sembrar():
    limpiar()

    # ------------------------- CLIENTES -------------------------
    datos_clientes = [
        ("Laura Martínez", "1020304050", "3001234567", "laura.martinez@gmail.com", "Calle 20 #15-30", "Activo"),
        ("Carlos Gómez", "1030405060", "3009876543", "carlos.gomez@gmail.com", "Transversal Inferior #10-20", "Activo"),
        ("Constructora Verde S.A.S.", "900456789", "6044567890", "contacto@constructorverde.com", "Carrera 43A #1-50", "Activo"),
        ("Ana María Restrepo", "1010101010", "3112223344", "ana.restrepo@hotmail.com", "Carrera 70 #44-12", "Activo"),
        ("Hotel Jardines del Norte", "900789123", "6043219876", "reservas@jardinesnorte.com", "Calle 10 #40-20", "Activo"),
        ("Jorge Iván Ospina", "1040506070", "3156667788", "jorge.ospina@gmail.com", "Calle 50 #80-15", "Inactivo"),
        ("María Camila Torres", "1050607080", "3129998877", "camila.torres@gmail.com", "Carrera 25 #10-05", "Activo"),
        ("Urbanización Los Cedros", "900321654", "6045551234", "admin@loscedros.com", "Vía a Rionegro Km 5", "Activo"),
    ]
    ids_clientes = []
    for nombre, documento, telefono, correo, direccion, estado in datos_clientes:
        resultado = clientes.insert_one(
            {
                "nombre": nombre,
                "documento": documento,
                "telefono": telefono,
                "correo": correo,
                "direccion": direccion,
                "estado": estado,
            }
        )
        ids_clientes.append(resultado.inserted_id)

    laura, carlos, constructora, ana, hotel, jorge, camila, urbanizacion = ids_clientes

    # ------------------------ PROPIEDADES -----------------------
    datos_propiedades = [
        {
            "cliente_id": laura,
            "nombre": "Jardín Los Pinos",
            "direccion": "Carrera 45 #20-10",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 150,
            "especies": [
                {"nombre_comun": "Rosa", "nombre_cientifico": "Rosa spp.", "cantidad": 12, "ubicacion": "Jardín delantero", "necesidades_cuidado": "Riego frecuente, poda y abono cada 30 días"},
                {"nombre_comun": "Hortensia", "nombre_cientifico": "Hydrangea macrophylla", "cantidad": 6, "ubicacion": "Zona de sombra", "necesidades_cuidado": "Suelo húmedo y sombra parcial"},
                {"nombre_comun": "Césped San Agustín", "nombre_cientifico": "Stenotaphrum secundatum", "cantidad": 90, "ubicacion": "Jardín principal", "necesidades_cuidado": "Corte quincenal y riego moderado"},
            ],
        },
        {
            "cliente_id": carlos,
            "nombre": "Finca El Paraíso",
            "direccion": "Vía Las Palmas Km 12",
            "ciudad": "Envigado",
            "tipo_propiedad": "Finca",
            "area_m2": 500,
            "especies": [
                {"nombre_comun": "Palma Areca", "nombre_cientifico": "Dypsis lutescens", "cantidad": 18, "ubicacion": "Entrada principal", "necesidades_cuidado": "Riego moderado y fertilización semestral"},
                {"nombre_comun": "Limón Tahití", "nombre_cientifico": "Citrus latifolia", "cantidad": 8, "ubicacion": "Huerto", "necesidades_cuidado": "Poda de formación y control de plagas"},
                {"nombre_comun": "Bambú", "nombre_cientifico": "Bambusa vulgaris", "cantidad": 30, "ubicacion": "Cerca perimetral", "necesidades_cuidado": "Control de crecimiento y riego regular"},
            ],
        },
        {
            "cliente_id": constructora,
            "nombre": "Zonas verdes Torre Aurora",
            "direccion": "Carrera 43A #1-50",
            "ciudad": "Medellín",
            "tipo_propiedad": "Conjunto residencial",
            "area_m2": 800,
            "especies": [
                {"nombre_comun": "Ficus", "nombre_cientifico": "Ficus benjamina", "cantidad": 22, "ubicacion": "Zona común", "necesidades_cuidado": "Poda ornamental y riego quincenal"},
                {"nombre_comun": "Lantana", "nombre_cientifico": "Lantana camara", "cantidad": 40, "ubicacion": "Jardines laterales", "necesidades_cuidado": "Poda ligera y exposición al sol"},
                {"nombre_comun": "Césped San Agustín", "nombre_cientifico": "Stenotaphrum secundatum", "cantidad": 600, "ubicacion": "Zonas verdes", "necesidades_cuidado": "Corte quincenal y fertilización"},
            ],
        },
        {
            "cliente_id": ana,
            "nombre": "Jardín Casa de Ana",
            "direccion": "Carrera 70 #44-12",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 95,
            "especies": [
                {"nombre_comun": "Orquídea", "nombre_cientifico": "Phalaenopsis spp.", "cantidad": 14, "ubicacion": "Invernadero", "necesidades_cuidado": "Humedad controlada y sustrato especial"},
                {"nombre_comun": "Helecho de Boston", "nombre_cientifico": "Nephrolepis exaltata", "cantidad": 10, "ubicacion": "Terraza", "necesidades_cuidado": "Sombra y riego frecuente"},
            ],
        },
        {
            "cliente_id": hotel,
            "nombre": "Jardines Hotel del Norte",
            "direccion": "Calle 10 #40-20",
            "ciudad": "Bello",
            "tipo_propiedad": "Oficina",
            "area_m2": 1200,
            "especies": [
                {"nombre_comun": "Palma Real", "nombre_cientifico": "Roystonea regia", "cantidad": 16, "ubicacion": "Acceso vehicular", "necesidades_cuidado": "Poda de hojas secas y riego profundo"},
                {"nombre_comun": "Ave del Paraíso", "nombre_cientifico": "Strelitzia reginae", "cantidad": 25, "ubicacion": "Jardín interior", "necesidades_cuidado": "Sol directo y abono orgánico"},
                {"nombre_comun": "Bambú", "nombre_cientifico": "Bambusa vulgaris", "cantidad": 45, "ubicacion": "Zona de piscina", "necesidades_cuidado": "Control de crecimiento"},
            ],
        },
        {
            "cliente_id": jorge,
            "nombre": "Apartamento El Poblado",
            "direccion": "Calle 10 #30-20",
            "ciudad": "Medellín",
            "tipo_propiedad": "Apartamento",
            "area_m2": 60,
            "especies": [
                {"nombre_comun": "Suculentas", "nombre_cientifico": "Echeveria elegans", "cantidad": 18, "ubicacion": "Balcón", "necesidades_cuidado": "Riego escaso y luz indirecta"},
                {"nombre_comun": "Helecho", "nombre_cientifico": "Nephrolepis exaltata", "cantidad": 6, "ubicacion": "Sala", "necesidades_cuidado": "Riego frecuente sin encharcar"},
            ],
        },
        {
            "cliente_id": camila,
            "nombre": "Casa Campestre La Esperanza",
            "direccion": "Vía Sabaneta Km 2",
            "ciudad": "Sabaneta",
            "tipo_propiedad": "Finca",
            "area_m2": 320,
            "especies": [
                {"nombre_comun": "Limonero", "nombre_cientifico": "Citrus limon", "cantidad": 10, "ubicacion": "Huerto", "necesidades_cuidado": "Poda y fertilización orgánica"},
                {"nombre_comun": "Hortensia", "nombre_cientifico": "Hydrangea macrophylla", "cantidad": 20, "ubicacion": "Camino de entrada", "necesidades_cuidado": "Sombra parcial y suelo ácido"},
                {"nombre_comun": "Rosa", "nombre_cientifico": "Rosa spp.", "cantidad": 15, "ubicacion": "Jardín trasero", "necesidades_cuidado": "Poda y control fitosanitario"},
            ],
        },
        {
            "cliente_id": urbanizacion,
            "nombre": "Parque Central Los Cedros",
            "direccion": "Vía Rionegro Km 5",
            "ciudad": "Rionegro",
            "tipo_propiedad": "Parque",
            "area_m2": 2500,
            "especies": [
                {"nombre_comun": "Roble", "nombre_cientifico": "Quercus humboldtii", "cantidad": 35, "ubicacion": "Zona boscosa", "necesidades_cuidado": "Monitoreo fitosanitario y riego de establecimiento"},
                {"nombre_comun": "Césped San Agustín", "nombre_cientifico": "Stenotaphrum secundatum", "cantidad": 1800, "ubicacion": "Zona abierta", "necesidades_cuidado": "Corte y fertilización programada"},
                {"nombre_comun": "Lantana", "nombre_cientifico": "Lantana camara", "cantidad": 70, "ubicacion": "Senderos", "necesidades_cuidado": "Poda y control de crecimiento"},
            ],
        },
        {
            "cliente_id": laura,
            "nombre": "Oficina Administrativa 301",
            "direccion": "Calle 20 #15-30",
            "ciudad": "Medellín",
            "tipo_propiedad": "Oficina",
            "area_m2": 40,
            "especies": [
                {"nombre_comun": "Ficus", "nombre_cientifico": "Ficus benjamina", "cantidad": 4, "ubicacion": "Recepción", "necesidades_cuidado": "Luz indirecta y riego semanal"},
                {"nombre_comun": "Suculentas", "nombre_cientifico": "Echeveria elegans", "cantidad": 8, "ubicacion": "Escritorios", "necesidades_cuidado": "Riego escaso"},
            ],
        },
        {
            "cliente_id": constructora,
            "nombre": "Parque Empresarial Itagüí",
            "direccion": "Carrera 48 #20-114",
            "ciudad": "Itagüí",
            "tipo_propiedad": "Oficina",
            "area_m2": 450,
            "especies": [
                {"nombre_comun": "Bambú", "nombre_cientifico": "Bambusa vulgaris", "cantidad": 60, "ubicacion": "Fachada", "necesidades_cuidado": "Control de crecimiento y riego"},
                {"nombre_comun": "Ficus", "nombre_cientifico": "Ficus benjamina", "cantidad": 12, "ubicacion": "Lobby", "necesidades_cuidado": "Poda ornamental"},
            ],
        },
    ]
    ids_propiedades = []
    for propiedad in datos_propiedades:
        resultado = propiedades.insert_one(propiedad)
        ids_propiedades.append(resultado.inserted_id)

    (
        jardin_los_pinos,
        finca_paraiso,
        torre_aurora,
        casa_ana,
        hotel_norte,
        apartamento_poblado,
        casa_esperanza,
        parque_cedros,
        oficina_301,
        parque_empresarial,
    ) = ids_propiedades

    # ---------------------- SERVICIOS / CONTRATOS ----------------
    datos_contratos = [
        {
            "cliente_id": laura,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Poda, riego y limpieza mensual", "precio_acordado": 650000},
                {"nombre": "Fertilización", "descripcion": "Aplicación de fertilizante NPK trimestral", "precio_acordado": 500000},
            ],
            "fecha_inicio": fecha(2026, 10, 1),
            "fecha_fin": fecha(2027, 9, 30),
            "valor_total": 1150000,
            "estado": "Activo",
        },
        {
            "cliente_id": carlos,
            "servicios": [
                {"nombre": "Diseño paisajístico", "descripcion": "Rediseño integral del jardín principal", "precio_acordado": 1800000},
                {"nombre": "Poda de altura", "descripcion": "Poda técnica de árboles y palmas", "precio_acordado": 700000},
            ],
            "fecha_inicio": fecha(2026, 9, 15),
            "fecha_fin": fecha(2027, 3, 15),
            "valor_total": 2500000,
            "estado": "Activo",
        },
        {
            "cliente_id": constructora,
            "servicios": [
                {"nombre": "Mantenimiento de zonas verdes", "descripcion": "Corte, riego y limpieza de zonas comunes", "precio_acordado": 4200000},
                {"nombre": "Control de plagas", "descripcion": "Monitoreo y aplicación de control fitosanitario", "precio_acordado": 1800000},
            ],
            "fecha_inicio": fecha(2026, 1, 1),
            "fecha_fin": fecha(2026, 12, 31),
            "valor_total": 6000000,
            "estado": "Activo",
        },
        {
            "cliente_id": ana,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Riego, poda y cuidado de orquídeas", "precio_acordado": 600000},
            ],
            "fecha_inicio": fecha(2026, 11, 1),
            "fecha_fin": fecha(2027, 11, 1),
            "valor_total": 600000,
            "estado": "Activo",
        },
        {
            "cliente_id": hotel,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento integral de jardines y zonas comunes", "precio_acordado": 6500000},
                {"nombre": "Riego automatizado", "descripcion": "Instalación y mantenimiento de sistema de riego", "precio_acordado": 1500000},
            ],
            "fecha_inicio": fecha(2026, 10, 1),
            "fecha_fin": fecha(2027, 10, 1),
            "valor_total": 8000000,
            "estado": "Activo",
        },
        {
            "cliente_id": jorge,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento básico de balcón y materas", "precio_acordado": 400000},
            ],
            "fecha_inicio": fecha(2026, 1, 1),
            "fecha_fin": fecha(2026, 12, 31),
            "valor_total": 400000,
            "estado": "Finalizado",
        },
        {
            "cliente_id": camila,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento general de la casa campestre", "precio_acordado": 900000},
                {"nombre": "Poda de altura", "descripcion": "Poda de árboles frutales", "precio_acordado": 450000},
                {"nombre": "Siembra de especies", "descripcion": "Siembra y adecuación de nuevas zonas", "precio_acordado": 500000},
            ],
            "fecha_inicio": fecha(2026, 11, 1),
            "fecha_fin": fecha(2027, 11, 1),
            "valor_total": 1850000,
            "estado": "Activo",
        },
        {
            "cliente_id": urbanizacion,
            "servicios": [
                {"nombre": "Mantenimiento de zonas verdes", "descripcion": "Mantenimiento de 2.500 m² de zonas verdes", "precio_acordado": 9000000},
                {"nombre": "Fertilización", "descripcion": "Plan de fertilización semestral", "precio_acordado": 1500000},
                {"nombre": "Control de plagas", "descripcion": "Monitoreo fitosanitario permanente", "precio_acordado": 1500000},
            ],
            "fecha_inicio": fecha(2026, 7, 1),
            "fecha_fin": fecha(2027, 6, 30),
            "valor_total": 12000000,
            "estado": "Activo",
        },
        {
            "cliente_id": constructora,
            "servicios": [
                {"nombre": "Diseño paisajístico", "descripcion": "Diseño de zonas verdes del parque empresarial", "precio_acordado": 3200000},
            ],
            "fecha_inicio": fecha(2026, 10, 20),
            "fecha_fin": fecha(2027, 4, 20),
            "valor_total": 3200000,
            "estado": "Activo",
        },
        {
            "cliente_id": laura,
            "servicios": [
                {"nombre": "Mantenimiento de jardines", "descripcion": "Mantenimiento de materas de oficina", "precio_acordado": 480000},
            ],
            "fecha_inicio": fecha(2026, 8, 1),
            "fecha_fin": fecha(2027, 8, 1),
            "valor_total": 480000,
            "estado": "Activo",
        },
    ]
    ids_contratos = []
    for contrato in datos_contratos:
        resultado = servicios_contratos.insert_one(contrato)
        ids_contratos.append(resultado.inserted_id)

    (
        contrato_laura,
        contrato_carlos,
        contrato_constructora,
        contrato_ana,
        contrato_hotel,
        contrato_jorge,
        contrato_camila,
        contrato_urbanizacion,
        contrato_parque_empresarial,
        contrato_oficina,
    ) = ids_contratos

    # --------------------------- PERSONAL ------------------------
    datos_personal = [
        ("Carlos Ramírez", "1098765432", "3104567890", "carlos.ramirez@paisajismo.com", "Jardinero", 1800000, ["Poda de plantas", "Mantenimiento de jardines", "Control de plagas"], "Activo"),
        ("Lucía Pérez", "1012345678", "3209876543", "lucia.perez@paisajismo.com", "Paisajista", 2600000, ["Diseño paisajístico", "Selección de especies", "Siembra"], "Activo"),
        ("Andrés Mejía", "1087654321", "3012223344", "andres.mejia@paisajismo.com", "Especialista botánico", 2900000, ["Control botánico", "Fertilización", "Diagnóstico de plagas"], "Activo"),
        ("Diana Torres", "1023456789", "3145556677", "diana.torres@paisajismo.com", "Jardinera", 1750000, ["Riego", "Siembra", "Mantenimiento de jardines"], "Activo"),
        ("Felipe Cárdenas", "1034567890", "3167778899", "felipe.cardenas@paisajismo.com", "Supervisor", 3200000, ["Supervisión de obras", "Poda de altura", "Seguridad en alturas"], "Activo"),
        ("Sofía Herrera", "1045678901", "3188889900", "sofia.herrera@paisajismo.com", "Auxiliar de jardinería", 1500000, ["Limpieza", "Siembra", "Riego"], "Activo"),
        ("Mauricio López", "1056789012", "3199990011", "mauricio.lopez@paisajismo.com", "Jardinero", 1800000, ["Poda de plantas", "Mantenimiento de jardines"], "Inactivo"),
        ("Valentina Ríos", "1067890123", "3211112233", "valentina.rios@paisajismo.com", "Paisajista", 2550000, ["Diseño de jardines", "Riego automatizado"], "Activo"),
        ("Julián Zapata", "1078901234", "3223334455", "julian.zapata@paisajismo.com", "Especialista botánico", 2850000, ["Control fitosanitario", "Fertilización"], "Activo"),
    ]
    ids_personal = []
    for nombre, documento, telefono, correo, cargo, salario, especialidades, estado in datos_personal:
        resultado = personal.insert_one(
            {
                "nombre": nombre,
                "documento": documento,
                "telefono": telefono,
                "correo": correo,
                "cargo": cargo,
                "salario": salario,
                "especialidades": especialidades,
                "estado": estado,
            }
        )
        ids_personal.append(resultado.inserted_id)

    carlos_r, lucia, andres, diana, felipe, sofia, mauricio, valentina, julian = ids_personal
    nombres_personal = {
        str(carlos_r): "Carlos Ramírez",
        str(lucia): "Lucía Pérez",
        str(andres): "Andrés Mejía",
        str(diana): "Diana Torres",
        str(felipe): "Felipe Cárdenas",
        str(sofia): "Sofía Herrera",
        str(mauricio): "Mauricio López",
        str(valentina): "Valentina Ríos",
        str(julian): "Julián Zapata",
    }

    # --------------------------- INSUMOS -------------------------
    # Las existencias ya reflejan el consumo registrado en las visitas.
    datos_insumos = [
        ("Fertilizante NPK 10-30-10", "Fertilizante granular completo para nutrición de plantas y césped", "Kilogramos", 59, 15),
        ("Abono orgánico", "Compost natural para enriquecer la tierra y mejorar su estructura", "Bultos", 19, 8),
        ("Tierra abonada", "Mezcla de tierra negra y materia orgánica para siembra", "Bultos", 9, 10),
        ("Insecticida foliar", "Producto para el control de insectos en hojas y tallos", "Litros", 15, 5),
        ("Fungicida a base de cobre", "Protector fitosanitario contra hongos en jardines", "Kilogramos", 8, 4),
        ("Semilla de césped San Agustín", "Semilla certificada para resiembra de césped", "Kilogramos", 22, 10),
        ("Sustrato premium", "Sustrato especial para orquídeas y plantas de interior", "Bultos", 20, 6),
        ("Acondicionador de suelo", "Producto para regular el pH y mejorar la absorción de nutrientes", "Litros", 25, 25),
        ("Humus de lombriz", "Abono orgánico de alta concentración nutricional", "Bultos", 0, 5),
    ]
    ids_insumos = {}
    for nombre, descripcion, unidad, existencias, stock_minimo in datos_insumos:
        resultado = insumos.insert_one(
            {
                "nombre": nombre,
                "descripcion": descripcion,
                "unidad_medida": unidad,
                "existencias": existencias,
                "stock_minimo": stock_minimo,
                "estado": calcular_estado_insumo(existencias, stock_minimo),
            }
        )
        ids_insumos[nombre] = resultado.inserted_id

    def insumo(nombre, cantidad):
        return {
            "insumo_id": ids_insumos[nombre],
            "nombre": nombre,
            "cantidad": cantidad,
            "unidad_medida": next(item[2] for item in datos_insumos if item[0] == nombre),
        }

    def asignado(*ids):
        return [{"personal_id": id_personal, "nombre": nombres_personal[str(id_personal)]} for id_personal in ids]

    # --------------------------- VISITAS -------------------------
    datos_visitas = [
        {
            "propiedad_id": jardin_los_pinos,
            "contrato_id": contrato_laura,
            "fecha_programada": fecha(2026, 11, 5, 8, 0),
            "personal_asignado": asignado(carlos_r, diana),
            "actividades_realizadas": ["Poda de rosales", "Corte de césped", "Riego general"],
            "observaciones": ["El jardín se encuentra en buen estado general.", "Se recomienda reforzar el abono en la zona de hortensias."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 3), insumo("Abono orgánico", 2)],
        },
        {
            "propiedad_id": jardin_los_pinos,
            "contrato_id": contrato_laura,
            "fecha_programada": fecha(2026, 11, 12, 8, 0),
            "personal_asignado": asignado(carlos_r),
            "actividades_realizadas": ["Resiembra de césped en zona delantera"],
            "observaciones": ["Se detectó compactación del suelo en el acceso peatonal."],
            "estado": "En proceso",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 2), insumo("Semilla de césped San Agustín", 3)],
        },
        {
            "propiedad_id": jardin_los_pinos,
            "contrato_id": contrato_laura,
            "fecha_programada": fecha(2026, 11, 19, 9, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Riego y revisión de sistema de aspersión"],
            "observaciones": ["Visita de seguimiento programada."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": finca_paraiso,
            "contrato_id": contrato_carlos,
            "fecha_programada": fecha(2026, 10, 28, 7, 30),
            "personal_asignado": asignado(lucia, felipe),
            "actividades_realizadas": ["Poda de palmas", "Adecuación de huerto de limones", "Siembra de cobertura vegetal"],
            "observaciones": ["Se identificaron ramas secas en la palma de la entrada.", "Aplicar abono orgánico en el huerto."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Tierra abonada", 5), insumo("Abono orgánico", 4), insumo("Fertilizante NPK 10-30-10", 4)],
        },
        {
            "propiedad_id": finca_paraiso,
            "contrato_id": contrato_carlos,
            "fecha_programada": fecha(2026, 11, 14, 8, 30),
            "personal_asignado": asignado(lucia),
            "actividades_realizadas": ["Continuidad del diseño del jardín principal"],
            "observaciones": ["Confirmar disponibilidad de especies ornamentales."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": torre_aurora,
            "contrato_id": contrato_constructora,
            "fecha_programada": fecha(2026, 11, 3, 7, 0),
            "personal_asignado": asignado(carlos_r, sofia),
            "actividades_realizadas": ["Corte de césped", "Limpieza de zonas comunes", "Aplicación de insecticida"],
            "observaciones": ["Presencia de hormigas en el jardín lateral."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 8), insumo("Semilla de césped San Agustín", 15), insumo("Insecticida foliar", 3)],
        },
        {
            "propiedad_id": torre_aurora,
            "contrato_id": contrato_constructora,
            "fecha_programada": fecha(2026, 11, 10, 7, 30),
            "personal_asignado": asignado(andres, sofia),
            "actividades_realizadas": ["Control fitosanitario de ficus", "Aplicación de fungicida"],
            "observaciones": ["Se detectaron hongos foliares leves en dos ficus."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fungicida a base de cobre", 2), insumo("Insecticida foliar", 2)],
        },
        {
            "propiedad_id": torre_aurora,
            "contrato_id": contrato_constructora,
            "fecha_programada": fecha(2026, 11, 18, 7, 0),
            "personal_asignado": asignado(andres, carlos_r),
            "actividades_realizadas": ["Monitoreo de lantana y ficus"],
            "observaciones": ["Verificar evolución del tratamiento antifúngico."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": casa_ana,
            "contrato_id": contrato_ana,
            "fecha_programada": fecha(2026, 11, 7, 9, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Riego de orquídeas", "Poda de hojas secas", "Abonado de helechos"],
            "observaciones": ["Las orquídeas requieren cambio de sustrato en la próxima visita."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Abono orgánico", 3), insumo("Fertilizante NPK 10-30-10", 2)],
        },
        {
            "propiedad_id": casa_ana,
            "contrato_id": contrato_ana,
            "fecha_programada": fecha(2026, 11, 21, 9, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Cambio de sustrato de orquídeas"],
            "observaciones": ["Visita programada con insumos por definir."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": casa_ana,
            "contrato_id": contrato_ana,
            "fecha_programada": fecha(2026, 11, 9, 15, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Visita cancelada por solicitud del cliente"],
            "observaciones": ["El cliente reprogramará la visita."],
            "estado": "Cancelada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": hotel_norte,
            "contrato_id": contrato_hotel,
            "fecha_programada": fecha(2026, 11, 2, 6, 30),
            "personal_asignado": asignado(carlos_r, felipe, sofia),
            "actividades_realizadas": ["Poda de palmas", "Adecuación de jardín interior", "Mantenimiento de riego"],
            "observaciones": ["Se ajustó la programación del riego automático."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Fertilizante NPK 10-30-10", 6), insumo("Tierra abonada", 8), insumo("Fungicida a base de cobre", 4), insumo("Semilla de césped San Agustín", 10)],
        },
        {
            "propiedad_id": hotel_norte,
            "contrato_id": contrato_hotel,
            "fecha_programada": fecha(2026, 11, 16, 6, 30),
            "personal_asignado": asignado(felipe, carlos_r),
            "actividades_realizadas": ["Revisión de sistema de riego y poda de aves del paraíso"],
            "observaciones": ["Visita de mantenimiento preventivo."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": casa_esperanza,
            "contrato_id": contrato_camila,
            "fecha_programada": fecha(2026, 11, 8, 8, 0),
            "personal_asignado": asignado(lucia, diana),
            "actividades_realizadas": ["Poda de limoneros", "Siembra de hortensias", "Aplicación de humus"],
            "observaciones": ["Se amplió la zona de siembra junto al camino."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Abono orgánico", 6), insumo("Humus de lombriz", 10), insumo("Acondicionador de suelo", 5)],
        },
        {
            "propiedad_id": casa_esperanza,
            "contrato_id": contrato_camila,
            "fecha_programada": fecha(2026, 11, 22, 8, 0),
            "personal_asignado": asignado(lucia),
            "actividades_realizadas": ["Seguimiento de siembra y revisión de rosales"],
            "observaciones": ["Evaluar prendimiento de las nuevas hortensias."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": parque_cedros,
            "contrato_id": contrato_urbanizacion,
            "fecha_programada": fecha(2026, 11, 4, 7, 0),
            "personal_asignado": asignado(carlos_r, andres, sofia, felipe),
            "actividades_realizadas": ["Corte de césped", "Fertilización de zonas verdes", "Control de plagas en senderos"],
            "observaciones": ["Se recomienda programar resiembra en el sector oriental."],
            "estado": "Finalizada",
            "insumos_utilizados": [insumo("Abono orgánico", 6), insumo("Fertilizante NPK 10-30-10", 6), insumo("Fungicida a base de cobre", 4)],
        },
        {
            "propiedad_id": parque_cedros,
            "contrato_id": contrato_urbanizacion,
            "fecha_programada": fecha(2026, 11, 20, 7, 0),
            "personal_asignado": asignado(andres, carlos_r),
            "actividades_realizadas": ["Monitoreo fitosanitario de robles"],
            "observaciones": ["Revisar presencia de insectos en la zona boscosa."],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": parque_empresarial,
            "contrato_id": contrato_parque_empresarial,
            "fecha_programada": fecha(2026, 11, 11, 8, 0),
            "personal_asignado": asignado(valentina, julian),
            "actividades_realizadas": ["Trazado de jardineras", "Preparación del terreno"],
            "observaciones": ["Se requiere nivelar el terreno antes de sembrar."],
            "estado": "En proceso",
            "insumos_utilizados": [insumo("Tierra abonada", 8)],
        },
        {
            "propiedad_id": oficina_301,
            "contrato_id": contrato_oficina,
            "fecha_programada": fecha(2026, 11, 9, 12, 0),
            "personal_asignado": asignado(diana),
            "actividades_realizadas": ["Visita cancelada por remodelación de la oficina"],
            "observaciones": ["Reprogramar cuando finalicen las obras."],
            "estado": "Cancelada",
            "insumos_utilizados": [],
        },
        {
            "propiedad_id": apartamento_poblado,
            "contrato_id": contrato_jorge,
            "fecha_programada": fecha(2026, 8, 20, 10, 0),
            "personal_asignado": asignado(mauricio),
            "actividades_realizadas": ["Riego de suculentas", "Limpieza de balcón"],
            "observaciones": ["Servicio finalizado según lo pactado."],
            "estado": "Finalizada",
            "insumos_utilizados": [],
        },
    ]

    visitas_mantenimiento.insert_many(datos_visitas)

    crear_indices()

    print("\nDatos de demostración cargados correctamente:")
    print(f"  Clientes:               {clientes.count_documents({})}")
    print(f"  Propiedades:            {propiedades.count_documents({})}")
    print(f"  Contratos:              {servicios_contratos.count_documents({})}")
    print(f"  Personal:               {personal.count_documents({})}")
    print(f"  Visitas de mantenimiento:{visitas_mantenimiento.count_documents({})}")
    print(f"  Insumos:                {insumos.count_documents({})}")
    print(f"  Base de datos:          {db.name}")


if __name__ == "__main__":
    sembrar()
```

---

## A.20 Pruebas automatizadas

**Archivo:** `pruebas/smoke_test.py` · **250 líneas**

Suite de 28 pruebas de integración contra la API en ejecución.

```python
# ============================================================
#  Pruebas de integración de la API REST
#  Uso:  python pruebas/smoke_test.py [URL_BASE]
#  Por defecto: http://127.0.0.1:5000
# ============================================================
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
SUFIJO = str(int(time.time()))
RESULTADOS = []


def comprobar(nombre, condicion=True, detalle=""):
    estado = "APROBADA" if condicion else "FALLIDA"
    RESULTADOS.append((nombre, estado, detalle))
    print(f"[{estado}] {nombre}" + (f" -> {detalle}" if detalle else ""))


def solicitud(metodo, ruta, esperado, cuerpo=None):
    respuesta = requests.request(metodo, f"{BASE}{ruta}", json=cuerpo, timeout=30)
    if respuesta.status_code != esperado:
        raise AssertionError(
            f"{metodo} {ruta}: se esperaba {esperado} y se obtuvo {respuesta.status_code}: {respuesta.text[:300]}"
        )
    try:
        return respuesta.json()
    except ValueError:
        return {}


def main():
    print(f"Ejecutando pruebas contra {BASE}\n")

    salud = solicitud("GET", "/api/health", 200)
    comprobar("Conexión con MongoDB Atlas", salud.get("estado") == "ok", str(salud.get("colecciones")))

    # ------------------- Consultas generales -------------------
    for ruta, minimo in [
        ("/clientes", 1),
        ("/propiedades", 1),
        ("/servicios_contratos", 1),
        ("/personal", 1),
        ("/visitas_mantenimiento", 1),
        ("/insumos", 1),
    ]:
        datos = solicitud("GET", ruta, 200)
        comprobar(f"GET {ruta} retorna arreglo de datos", len(datos.get("datos", [])) >= minimo, f"{len(datos.get('datos', []))} registros")

    # ------------------------ Filtros --------------------------
    activos = solicitud("GET", "/clientes?estado=Activo", 200)
    comprobar(
        "Filtro de clientes por estado",
        all(c["estado"] == "Activo" for c in activos["datos"]),
        f"{len(activos['datos'])} clientes activos",
    )
    criticos = solicitud("GET", "/insumos?bajo_stock=true", 200)
    comprobar(
        "Filtro de insumos en nivel crítico",
        len(criticos["datos"]) >= 1,
        f"{len(criticos['datos'])} insumos críticos",
    )
    busqueda = solicitud("GET", "/propiedades?q=Rosa", 200)
    comprobar("Búsqueda por especie vegetal", len(busqueda["datos"]) >= 1, f"{len(busqueda['datos'])} coincidencias")

    # ------------------------- CRUD ----------------------------
    documento = f"99{SUFIJO[-8:]}"
    creado = solicitud(
        "POST",
        "/clientes",
        201,
        {
            "nombre": "Cliente de Prueba Automatizada",
            "documento": documento,
            "telefono": "3000000000",
            "correo": "prueba.automatizada@example.com",
            "direccion": "Calle de Prueba #1-01",
            "estado": "Activo",
        },
    )
    id_cliente = creado["id"]
    comprobar("POST /clientes crea un cliente", bool(id_cliente))

    solicitud(
        "POST",
        "/clientes",
        409,
        {
            "nombre": "Cliente Duplicado",
            "documento": documento,
            "telefono": "3000000001",
            "correo": "duplicado@example.com",
            "direccion": "Calle Duplicada",
            "estado": "Activo",
        },
    )
    comprobar("Regla de documento único en clientes (409)")

    solicitud(
        "PUT",
        f"/clientes/{id_cliente}",
        200,
        {"telefono": "3111111111", "direccion": "Carrera de Prueba #2-02"},
    )
    actualizado = solicitud("GET", f"/clientes/{id_cliente}", 200)["datos"]
    comprobar("PUT /clientes actualiza parcialmente", actualizado["telefono"] == "3111111111")

    solicitud("GET", "/clientes/identificador-invalido", 400)
    comprobar("Validación de ObjectId mal formado (400)")

    # ------------------ Integridad referencial -----------------
    solicitud(
        "POST",
        "/propiedades",
        404,
        {
            "cliente_id": "000000000000000000000000",
            "nombre": "Propiedad sin cliente",
            "direccion": "Calle 0 #0-0",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 100,
        },
    )
    comprobar("Propiedad con cliente inexistente rechazada (404)")

    solicitud(
        "POST",
        "/propiedades",
        400,
        {
            "cliente_id": id_cliente,
            "nombre": "Propiedad con área inválida",
            "direccion": "Calle 0 #0-0",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 0,
        },
    )
    comprobar("Validación de área mayor que cero (400)")

    solicitud(
        "POST",
        "/servicios_contratos",
        400,
        {
            "cliente_id": id_cliente,
            "servicios": [{"nombre": "Servicio de prueba", "descripcion": "Prueba", "precio_acordado": 100000}],
            "fecha_inicio": "2026-12-31",
            "fecha_fin": "2026-01-01",
            "valor_total": 100000,
            "estado": "Activo",
        },
    )
    comprobar("Coherencia cronológica de contratos (400)")

    solicitud(
        "POST",
        "/servicios_contratos",
        400,
        {
            "cliente_id": id_cliente,
            "servicios": [{"nombre": "Servicio de prueba", "descripcion": "Prueba", "precio_acordado": 100000}],
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2027-12-01",
            "valor_total": 500000,
            "estado": "Activo",
        },
    )
    comprobar("Validación de valor total contra servicios (400)")

    # ------------------- Reglas de inventario ------------------
    insumos = solicitud("GET", "/insumos", 200)["datos"]
    insumo = next(i for i in insumos if i["existencias"] > 0)
    propiedades = solicitud("GET", "/propiedades", 200)["datos"]
    contratos = solicitud("GET", "/servicios_contratos?estado=Activo", 200)["datos"]
    par = next(
        (c, p)
        for c in contratos
        for p in propiedades
        if p["cliente_id"] == c["cliente_id"]
    )
    contrato, propiedad = par
    personal_activo = solicitud("GET", "/personal?estado=Activo", 200)["datos"][0]

    solicitud(
        "POST",
        "/visitas_mantenimiento",
        404,
        {
            "propiedad_id": "000000000000000000000000",
            "contrato_id": contrato["_id"],
            "fecha_programada": "2026-11-15T08:00:00",
            "personal_asignado": [personal_activo["_id"]],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
    )
    comprobar("Visita con propiedad inexistente rechazada (404)")

    solicitud(
        "POST",
        "/visitas_mantenimiento",
        409,
        {
            "propiedad_id": propiedad["_id"],
            "contrato_id": contrato["_id"],
            "fecha_programada": "2026-11-15T08:00:00",
            "personal_asignado": [personal_activo["_id"]],
            "estado": "En proceso",
            "actividades_realizadas": ["Prueba de consumo"],
            "insumos_utilizados": [{"insumo_id": insumo["_id"], "cantidad": insumo["existencias"] + 1000}],
        },
    )
    comprobar("Rechazo de consumo superior al inventario (409)")

    # ------------------ Bloqueo de eliminación -----------------
    clientes = solicitud("GET", "/clientes", 200)["datos"]
    cliente_con_propiedades = next(c for c in clientes if c["nombre"] == "Laura Martínez")
    solicitud("DELETE", f"/clientes/{cliente_con_propiedades['_id']}", 409)
    comprobar("Bloqueo de eliminación de cliente con propiedades (409)")

    solicitud("DELETE", f"/clientes/{id_cliente}", 200)
    comprobar("DELETE /clientes elimina el registro de prueba")

    # ------------------- Consultas analíticas -----------------
    consultas = {
        "Consulta 1 - Clientes y propiedades": "/analitica/clientes-propiedades",
        "Consulta 2 - Visitas con detalle": "/analitica/visitas-detalle",
        "Consulta 3 - Visitas por estado": "/analitica/visitas-estado",
        "Consulta 4 - Insumos más utilizados": "/analitica/insumos-mas-utilizados",
        "Consulta 5 - Servicios más contratados": "/analitica/servicios-mas-contratados",
        "KPIs del tablero": "/analitica/kpis",
    }
    for nombre, ruta in consultas.items():
        respuesta = solicitud("GET", ruta, 200)
        comprobar(nombre, bool(respuesta.get("datos")), f"{len(respuesta.get('datos', []))} filas/indicadores")

    print("\n" + "=" * 64)
    aprobadas = sum(1 for _, estado, _ in RESULTADOS if estado == "APROBADA")
    print(f"Resultado: {aprobadas}/{len(RESULTADOS)} pruebas aprobadas.")
    print("=" * 64)
    if aprobadas != len(RESULTADOS):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## A.21 Dependencias de producción

**Archivo:** `requirements.txt` · **6 líneas**

Versiones fijas de Flask, PyMongo, dotenv, certifi y Gunicorn.

```text
Flask==3.1.3
pymongo==4.19.0
dnspython==2.9.2
python-dotenv==1.2.4
certifi==2026.10.23
gunicorn==23.0.0
```

---

## A.22 Dependencias de desarrollo

**Archivo:** `requirements-dev.txt` · **5 líneas**

Herramientas usadas solo para generar documentación y pruebas.

```text
-r requirements.txt
requests==2.34.2
python-docx==1.2.0
matplotlib==3.11.2
Pillow==13.0.0
```

---

## A.23 Comando de arranque

**Archivo:** `Procfile` · **1 líneas**

Define el proceso web para plataformas como Render o Heroku.

```text
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

---

## A.24 Infraestructura como código

**Archivo:** `render.yaml` · **15 líneas**

Blueprint de Render con build, start, health check y variables de entorno.

```yaml
services:
  - type: web
    name: verdevivo-paisajismo
    runtime: python
    plan: free
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
    healthCheckPath: /api/health
    autoDeploy: true
    envVars:
      - key: MONGO_URI
        sync: false
      - key: MONGO_DB
        value: jardineria_db
```

---

## A.25 Plantilla de variables de entorno

**Archivo:** `.env.example` · **4 líneas**

Muestra las variables necesarias sin incluir credenciales reales.

```dotenv
# Copie este archivo como .env y complete los valores reales.
# Nunca suba el archivo .env al repositorio.
MONGO_URI=mongodb+srv://USUARIO:CONTRASENA@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=jardineria_db
```

---

## A.26 Exclusión de archivos sensibles

**Archivo:** `.gitignore` · **27 líneas**

Evita subir .env, venv, cachés y archivos temporales al repositorio.

```text
# Entornos virtuales y dependencias locales
venv/
.venv/
env/

# Credenciales y configuración local
.env
.env.*
!.env.example

# Cachés de Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/

# Archivos temporales y del sistema
*.log
*.tmp
*.zip
~$*.docx
.DS_Store
Thumbs.db

# Editores
.vscode/
.idea/
```

---

## A.27 Generador de diagramas

**Archivo:** `docs/generar_diagramas.py` · **217 líneas**

Reproduce el diagrama de arquitectura y el modelo de datos con matplotlib.

```python
# -*- coding: utf-8 -*-
"""Genera los diagramas del modelo de datos y de arquitectura (PNG)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

DESTINO = Path(__file__).resolve().parent / "diagramas"
DESTINO.mkdir(parents=True, exist_ok=True)

VERDE = "#1f6f4a"
VERDE_CLARO = "#e8f5ee"
VERDE_BORDE = "#2f8f63"
GRIS = "#44514a"
NARANJA = "#c96a1b"
AZUL = "#245a8d"
FONDO = "#fbfdfb"


def caja(ax, x, y, w, h, titulo, campos, color=VERDE, relleno=VERDE_CLARO, fs=7.2):
    sombra = FancyBboxPatch((x + 0.004, y - 0.006), w, h,
                            boxstyle="round,pad=0.006,rounding_size=0.012",
                            linewidth=0, facecolor="#000000", alpha=0.10, zorder=1)
    ax.add_patch(sombra)
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.006,rounding_size=0.012",
                          linewidth=1.6, edgecolor=color, facecolor=relleno, zorder=2)
    ax.add_patch(rect)
    ax.add_patch(FancyBboxPatch((x, y + h - 0.052), w, 0.052,
                                boxstyle="round,pad=0.006,rounding_size=0.012",
                                linewidth=0, facecolor=color, zorder=3))
    ax.text(x + 0.012, y + h - 0.027, titulo, fontsize=10.5, fontweight="bold",
            color="white", va="center", ha="left", zorder=4)
    for i, campo in enumerate(campos):
        ax.text(x + 0.014, y + h - 0.078 - i * 0.0265, campo, fontsize=fs,
                color=GRIS, va="center", ha="left", family="DejaVu Sans Mono", zorder=4)


def flecha(ax, p1, p2, etiqueta, color=VERDE, rad=0.0, dx=0.0, dy=0.0, fs=8.5):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=16, linewidth=1.7,
        color=color, connectionstyle=f"arc3,rad={rad}", zorder=5,
        shrinkA=3, shrinkB=3,
    ))
    mx = (p1[0] + p2[0]) / 2 + dx
    my = (p1[1] + p2[1]) / 2 + dy
    ax.text(mx, my, etiqueta, fontsize=fs, color=color, fontweight="bold",
            ha="center", va="center", zorder=6,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                      edgecolor=color, linewidth=0.9, alpha=0.96))


def modelo_datos():
    fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
    fig.patch.set_facecolor(FONDO)
    ax.set_facecolor(FONDO)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.972, "Modelo de datos · Sistema de Gestión de Servicios de Paisajismo",
            fontsize=18, fontweight="bold", color=VERDE, ha="center", va="center")
    ax.text(0.5, 0.938, "MongoDB Atlas · base de datos jardineria_db · 6 colecciones",
            fontsize=10.5, color=GRIS, ha="center", va="center")

    caja(ax, 0.025, 0.615, 0.305, 0.285, "clientes", [
        "_id: ObjectId (PK)",
        "nombre: string",
        "documento: string (único)",
        "telefono: string",
        "correo: string",
        "direccion: string",
        "estado: Activo | Inactivo",
    ])

    caja(ax, 0.615, 0.615, 0.355, 0.285, "propiedades", [
        "_id: ObjectId (PK)",
        "cliente_id: ObjectId (FK → clientes)",
        "nombre: string",
        "direccion: string",
        "ciudad: string",
        "tipo_propiedad: enum",
        "area_m2: number",
        "especies: [ subdocumento embebido ]",
    ])

    caja(ax, 0.625, 0.315, 0.345, 0.235, "servicios_contratos", [
        "_id: ObjectId (PK)",
        "cliente_id: ObjectId (FK → clientes)",
        "servicios: [ subdocumento embebido ]",
        "fecha_inicio / fecha_fin: date",
        "valor_total: number (calculado)",
        "estado: Activo | Suspendido | ...",
    ])

    caja(ax, 0.305, 0.035, 0.375, 0.245, "visitas_mantenimiento", [
        "_id: ObjectId (PK)",
        "propiedad_id: ObjectId (FK → propiedades)",
        "contrato_id: ObjectId (FK → servicios_contratos)",
        "fecha_programada: date",
        "personal_asignado: [ ref → personal ]",
        "insumos_utilizados: [ ref → insumos ]",
        "estado: Programada | En proceso | ...",
    ])

    caja(ax, 0.025, 0.035, 0.245, 0.245, "personal", [
        "_id: ObjectId (PK)",
        "nombre: string",
        "documento: string (único)",
        "telefono / correo: string",
        "cargo: enum",
        "salario: number",
        "especialidades: [ string ]",
        "estado: Activo | Inactivo",
    ])

    caja(ax, 0.735, 0.025, 0.235, 0.245, "insumos", [
        "_id: ObjectId (PK)",
        "nombre: string",
        "unidad_medida: enum",
        "existencias: int",
        "stock_minimo: int",
        "estado: Disponible |",
        "        Bajo stock | Agotado",
    ])

    flecha(ax, (0.330, 0.760), (0.615, 0.760), "1 : N", dx=0.0, dy=0.018)
    flecha(ax, (0.245, 0.615), (0.625, 0.505), "1 : N", rad=-0.18, dx=-0.035, dy=0.030)
    flecha(ax, (0.615, 0.665), (0.600, 0.280), "1 : N", dx=-0.032, dy=0.0)
    flecha(ax, (0.790, 0.315), (0.680, 0.280), "1 : N", dx=0.020, dy=0.018)
    flecha(ax, (0.270, 0.157), (0.305, 0.157), "N : M", dx=0.0, dy=0.022, fs=7.4)
    flecha(ax, (0.735, 0.147), (0.680, 0.147), "N : M", dx=0.0, dy=0.022, fs=7.4, color=NARANJA)

    leyenda_y = 0.355
    ax.add_patch(FancyBboxPatch((0.035, leyenda_y - 0.075), 0.245, 0.13,
                                boxstyle="round,pad=0.006,rounding_size=0.01",
                                linewidth=1.0, edgecolor="#b9c9bf", facecolor="white", zorder=2))
    ax.text(0.050, leyenda_y + 0.028, "Convenciones", fontsize=9.5, fontweight="bold", color=VERDE)
    ax.text(0.050, leyenda_y + 0.002, "PK  Clave primaria", fontsize=8, color=GRIS)
    ax.text(0.050, leyenda_y - 0.024, "FK  Referencia entre colecciones", fontsize=8, color=GRIS)
    ax.text(0.050, leyenda_y - 0.050, "1:N / N:M  Cardinalidad", fontsize=8, color=GRIS)

    ax.text(0.5, 0.004,
            "Especies botánicas y servicios contratados se almacenan como subdocumentos embebidos; "
            "las demás relaciones usan referencias por ObjectId.",
            fontsize=8.6, color="#6b7a71", ha="center", va="bottom", style="italic")

    fig.savefig(DESTINO / "modelo_datos.png", bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)


def arquitectura():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.patch.set_facecolor(FONDO)
    ax.set_facecolor(FONDO)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.962, "Arquitectura de la solución",
            fontsize=19, fontweight="bold", color=VERDE, ha="center")
    ax.text(0.5, 0.925, "Aplicación web full-stack desplegada en la nube",
            fontsize=10.5, color=GRIS, ha="center")

    capas = [
        (0.715, "Usuario", "Navegador web (escritorio o móvil)\nHTTPS · interfaz en español", "#5c6f64", "#eef2ef"),
        (0.555, "Frontend · SPA", "HTML5 · CSS3 · JavaScript (ES6)\nChart.js · rutas hash · fetch/JSON", AZUL, "#e8f0f8"),
        (0.395, "Backend · API REST", "Flask 3 · 7 blueprints\nvalidaciones · reglas de negocio · inventario atómico", VERDE, VERDE_CLARO),
        (0.235, "Acceso a datos", "PyMongo 4 · certifi (TLS)\npool de conexiones · serialización BSON/JSON", NARANJA, "#fbf0e6"),
        (0.075, "MongoDB Atlas", "jardineria_db · 6 colecciones\níndices · Aggregation Pipeline", "#4b3f72", "#efecf7"),
    ]

    for y, titulo, detalle, color, relleno in capas:
        rect = FancyBboxPatch((0.245, y), 0.51, 0.115,
                              boxstyle="round,pad=0.008,rounding_size=0.018",
                              linewidth=1.8, edgecolor=color, facecolor=relleno, zorder=2)
        ax.add_patch(rect)
        ax.text(0.270, y + 0.079, titulo, fontsize=12, fontweight="bold", color=color, va="center")
        ax.text(0.270, y + 0.038, detalle, fontsize=8.8, color=GRIS, va="center")

    for y1, y2 in [(0.715, 0.670), (0.555, 0.510), (0.395, 0.350), (0.235, 0.190)]:
        ax.add_patch(FancyArrowPatch((0.500, y1), (0.500, y2), arrowstyle="<|-|>",
                                     mutation_scale=13, linewidth=1.5, color="#7d8c83", zorder=1))
    ax.text(0.515, 0.692, "HTTPS / JSON", fontsize=8, color="#6b7a71", rotation=90, va="center")
    ax.text(0.515, 0.532, "fetch()", fontsize=8, color="#6b7a71", rotation=90, va="center")
    ax.text(0.515, 0.372, "PyMongo", fontsize=8, color="#6b7a71", rotation=90, va="center")
    ax.text(0.515, 0.212, "TLS 1.2+", fontsize=8, color="#6b7a71", rotation=90, va="center")

    laterales = [
        (0.790, 0.760, "Render", "Despliegue del servicio\nweb con Gunicorn", "#2b6cb0", "#e6effa"),
        (0.790, 0.570, "GitHub", "Repositorio público\ndel código fuente", "#24292f", "#eef0f2"),
        (0.790, 0.380, "Variables de entorno", "MONGO_URI y MONGO_DB\nfuera del repositorio", "#8a5a00", "#fbf3e2"),
        (0.790, 0.190, "MongoDB Atlas", "Clúster administrado\ncopias y disponibilidad", "#4b3f72", "#efecf7"),
    ]
    for x, y, titulo, detalle, color, relleno in laterales:
        rect = FancyBboxPatch((x, y), 0.175, 0.115,
                              boxstyle="round,pad=0.008,rounding_size=0.016",
                              linewidth=1.4, edgecolor=color, facecolor=relleno, zorder=2)
        ax.add_patch(rect)
        ax.text(x + 0.014, y + 0.077, titulo, fontsize=9.4, fontweight="bold", color=color)
        ax.text(x + 0.014, y + 0.036, detalle, fontsize=7.4, color=GRIS)

    ax.text(0.245, 0.012,
            "El navegador consume la API REST; Flask aplica las reglas de negocio y PyMongo "
            "persiste en MongoDB Atlas. Las credenciales llegan por variables de entorno.",
            fontsize=8.6, color="#6b7a71", ha="left", va="bottom", style="italic")

    fig.savefig(DESTINO / "arquitectura.png", bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)


if __name__ == "__main__":
    modelo_datos()
    arquitectura()
    print("Diagramas generados en", DESTINO)
```

---

## A.28 Generador del documento técnico

**Archivo:** `docs/generar_docx.py` · **780 líneas**

Convierte la documentación Markdown al DOCX entregable con portada, tablas e imágenes.

```python
"""Genera el documento DOCX del proyecto a partir del Markdown técnico.

Uso:
    python docs/generar_docx.py

El script convierte encabezados, párrafos, listas, tablas, bloques de código,
imágenes, citas y enlaces. Las capturas muy altas se dividen en partes para que
se puedan leer dentro de una página A4.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from PIL import Image
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
ORIGEN = DOCS / "Documentacion_Tecnica_Sistema_Paisajismo.md"
DESTINO = DOCS / "Documentacion_Tecnica_Sistema_Paisajismo.docx"

VERDE = RGBColor(0x1F, 0x4D, 0x2E)
VERDE_CLARO = "E8F0E9"
VERDE_ENCABEZADO = "1F4D2E"
GRIS_TEXTO = RGBColor(0x44, 0x4B, 0x45)
GRIS_SUAVE = RGBColor(0x6B, 0x72, 0x6C)
FONDO_CODIGO = "F3F5F3"
ANCHO_UTIL_CM = 16.4
UMBRAL_DIVISION = 1.45


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------


def sombrear(elemento, relleno: str) -> None:
    """Aplica sombreado a una celda o a un párrafo."""
    propiedades = elemento.get_or_add_tcPr() if hasattr(elemento, "get_or_add_tcPr") else elemento.get_or_add_pPr()
    propiedades.append(parse_xml(rf'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{relleno}"/>'))


def borde_parrafo(parrafo, lado: str = "left", color: str = "1F4D2E", tamano: int = 18) -> None:
    pPr = parrafo._p.get_or_add_pPr()
    bordes = pPr.find(qn("w:pBdr"))
    if bordes is None:
        bordes = OxmlElement("w:pBdr")
        pPr.append(bordes)
    borde = OxmlElement(f"w:{lado}")
    borde.set(qn("w:val"), "single")
    borde.set(qn("w:sz"), str(tamano))
    borde.set(qn("w:space"), "6")
    borde.set(qn("w:color"), color)
    bordes.append(borde)


def agregar_hipervincular(parrafo, texto: str, url: str) -> None:
    relationship_id = parrafo.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hipervinculo = OxmlElement("w:hyperlink")
    hipervinculo.set(qn("r:id"), relationship_id)
    corrida = OxmlElement("w:r")
    propiedades = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1F5C99")
    subrayado = OxmlElement("w:u")
    subrayado.set(qn("w:val"), "single")
    propiedades.append(color)
    propiedades.append(subrayado)
    corrida.append(propiedades)
    nodo = OxmlElement("w:t")
    nodo.text = texto
    corrida.append(nodo)
    hipervinculo.append(corrida)
    parrafo._p.append(hipervinculo)


PATRON_ENLINEA = re.compile(
    r"(\*\*.+?\*\*|`[^`]+`|\*[^*\n]+?\*|\[[^\]]+\]\([^)]+\))",
    re.DOTALL,
)


def agregar_texto_enlinea(
    parrafo,
    texto: str,
    *,
    negrita: bool = False,
    cursiva: bool = False,
    tamano: float | None = None,
    color: RGBColor | None = None,
) -> None:
    """Agrega texto interpretando negrita, cursiva, código y enlaces."""
    posicion = 0
    for coincidencia in PATRON_ENLINEA.finditer(texto):
        if coincidencia.start() > posicion:
            _corrida(parrafo, texto[posicion : coincidencia.start()], negrita, cursiva, tamano, color)
        fragmento = coincidencia.group(0)
        if fragmento.startswith("**") and fragmento.endswith("**"):
            agregar_texto_enlinea(
                parrafo,
                fragmento[2:-2],
                negrita=True,
                cursiva=cursiva,
                tamano=tamano,
                color=color,
            )
        elif fragmento.startswith("`") and fragmento.endswith("`"):
            corrida = _corrida(parrafo, fragmento[1:-1], negrita, cursiva, tamano, color)
            corrida.font.name = "Consolas"
            corrida.font.size = Pt((tamano or 10.5) - 1.2)
            corrida.font.color.rgb = RGBColor(0x8A, 0x2E, 0x2E)
            sombrear_corrida(corrida, "F1F1F1")
        elif fragmento.startswith("*") and fragmento.endswith("*"):
            agregar_texto_enlinea(
                parrafo,
                fragmento[1:-1],
                negrita=negrita,
                cursiva=True,
                tamano=tamano,
                color=color,
            )
        else:
            enlace = re.match(r"\[([^\]]+)\]\(([^)]+)\)", fragmento)
            if enlace:
                agregar_hipervincular(parrafo, enlace.group(1), enlace.group(2))
        posicion = coincidencia.end()
    if posicion < len(texto):
        _corrida(parrafo, texto[posicion:], negrita, cursiva, tamano, color)


def _corrida(parrafo, texto, negrita, cursiva, tamano, color):
    corrida = parrafo.add_run(texto)
    corrida.bold = negrita
    corrida.italic = cursiva
    if tamano:
        corrida.font.size = Pt(tamano)
    if color:
        corrida.font.color.rgb = color
    return corrida


def sombrear_corrida(corrida, relleno: str) -> None:
    propiedades = corrida._r.get_or_add_rPr()
    propiedades.append(parse_xml(rf'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{relleno}"/>'))


# ---------------------------------------------------------------------------
# Configuración del documento
# ---------------------------------------------------------------------------


def configurar_estilos(documento: Document) -> None:
    estilos = documento.styles

    normal = estilos["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = GRIS_TEXTO
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    idioma = normal.element.get_or_add_rPr()
    idioma.append(parse_xml(rf'<w:lang {nsdecls("w")} w:val="es-CO" w:eastAsia="es-CO"/>'))

    h1 = estilos["Heading 1"]
    h1.font.name = "Calibri"
    h1.font.size = Pt(19)
    h1.font.bold = True
    h1.font.color.rgb = VERDE
    h1.paragraph_format.page_break_before = True
    h1.paragraph_format.space_before = Pt(0)
    h1.paragraph_format.space_after = Pt(14)
    h1.paragraph_format.keep_with_next = True
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    h2 = estilos["Heading 2"]
    h2.font.name = "Calibri"
    h2.font.size = Pt(13.5)
    h2.font.bold = True
    h2.font.color.rgb = VERDE
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    h2.paragraph_format.keep_with_next = True
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    h3 = estilos["Heading 3"]
    h3.font.name = "Calibri"
    h3.font.size = Pt(11.5)
    h3.font.bold = True
    h3.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    h3.paragraph_format.space_before = Pt(10)
    h3.paragraph_format.keep_with_next = True


def configurar_pagina(documento: Document) -> None:
    seccion = documento.sections[0]
    seccion.page_width = Cm(21)
    seccion.page_height = Cm(29.7)
    seccion.top_margin = Cm(2.2)
    seccion.bottom_margin = Cm(2.0)
    seccion.left_margin = Cm(2.3)
    seccion.right_margin = Cm(2.3)
    seccion.header_distance = Cm(1.0)
    seccion.footer_distance = Cm(0.9)
    seccion.different_first_page_header_footer = True

    encabezado = seccion.header
    parrafo_inicial = encabezado.paragraphs[0]
    parrafo_inicial._element.getparent().remove(parrafo_inicial._element)

    tabla_encabezado = encabezado.add_table(rows=1, cols=2, width=Cm(16.4))
    tabla_encabezado.autofit = False
    tabla_encabezado.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = tabla_encabezado._tbl.tblPr
    ancho_tabla = OxmlElement("w:tblW")
    ancho_tabla.set(qn("w:w"), "5000")
    ancho_tabla.set(qn("w:type"), "pct")
    tblPr.append(ancho_tabla)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    margenes = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        margen = OxmlElement(f"w:{lado}")
        margen.set(qn("w:w"), "0")
        margen.set(qn("w:type"), "dxa")
        margenes.append(margen)
    tblPr.append(margenes)
    bordes = OxmlElement("w:tblBorders")
    borde = OxmlElement("w:bottom")
    borde.set(qn("w:val"), "single")
    borde.set(qn("w:sz"), "6")
    borde.set(qn("w:space"), "0")
    borde.set(qn("w:color"), "C9D6CB")
    bordes.append(borde)
    tblPr.append(bordes)

    tabla_encabezado.columns[0].width = Cm(12.2)
    tabla_encabezado.columns[1].width = Cm(4.2)
    celda_izquierda, celda_derecha = tabla_encabezado.rows[0].cells
    celda_izquierda.width = Cm(12.2)
    celda_derecha.width = Cm(4.2)

    parrafo = celda_izquierda.paragraphs[0]
    parrafo.paragraph_format.space_after = Pt(0)
    corrida = parrafo.add_run("Sistema de Gestión de Servicios de Paisajismo")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    corrida.font.name = "Calibri"

    parrafo = celda_derecha.paragraphs[0]
    parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    parrafo.paragraph_format.space_after = Pt(0)
    corrida = parrafo.add_run("Bases de Datos II")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    corrida.font.name = "Calibri"

    cierre = encabezado.add_paragraph()
    cierre.paragraph_format.space_after = Pt(0)
    cierre.paragraph_format.line_spacing = Pt(1)
    corrida = cierre.add_run("")
    corrida.font.size = Pt(1)

    pie = seccion.footer
    parrafo = pie.paragraphs[0]
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    corrida = parrafo.add_run("Documentación técnica · ")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    _campo(parrafo, "PAGE")
    corrida = parrafo.add_run(" de ")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    _campo(parrafo, "NUMPAGES")


def _campo(parrafo, nombre: str) -> None:
    def corrida_con(elemento) -> None:
        corrida = parrafo.add_run()
        corrida.font.size = Pt(8)
        corrida.font.color.rgb = GRIS_SUAVE
        corrida._r.append(elemento)

    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    corrida_con(inicio)

    instruccion = OxmlElement("w:instrText")
    instruccion.set(qn("xml:space"), "preserve")
    instruccion.text = f" {nombre} "
    corrida_con(instruccion)

    separador = OxmlElement("w:fldChar")
    separador.set(qn("w:fldCharType"), "separate")
    corrida_con(separador)

    texto = OxmlElement("w:t")
    texto.text = "1"
    corrida_con(texto)

    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    corrida_con(fin)


def propiedades_documento(documento: Document) -> None:
    propiedades = documento.core_properties
    propiedades.title = "Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico"
    propiedades.subject = "Proyecto final de Bases de Datos II"
    propiedades.author = "Danna Paulina García Jiménez"
    propiedades.keywords = "MongoDB Atlas, Flask, Aggregation Pipeline, paisajismo, bases de datos"
    propiedades.comments = "Documentación técnica del proyecto final"


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------


def construir_portada(documento: Document, lineas: list[str]) -> None:
    titulo = ""
    subtitulo = ""
    metadatos: list[str] = []
    cita = ""

    for linea in lineas:
        limpia = linea.strip()
        if limpia.startswith("# ") and not titulo:
            titulo = limpia[2:].strip()
        elif limpia.startswith("## ") and not subtitulo:
            subtitulo = limpia[3:].strip()
        elif limpia.startswith(">"):
            cita = limpia[1:].strip()
        elif re.match(r"^\*\*[^*]+:\*\*\s", limpia):
            metadatos.append(limpia)

    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(70)
    parrafo.paragraph_format.space_after = Pt(10)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    corrida = parrafo.add_run("PROYECTO FINAL  ·  BASES DE DATOS II")
    corrida.font.size = Pt(10)
    corrida.font.bold = True
    corrida.font.color.rgb = RGBColor(0x6B, 0x8A, 0x70)
    corrida.font.name = "Calibri"

    parrafo = documento.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(6)
    corrida = parrafo.add_run(titulo)
    corrida.font.size = Pt(25)
    corrida.font.bold = True
    corrida.font.color.rgb = VERDE
    corrida.font.name = "Calibri"

    parrafo = documento.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(24)
    corrida = parrafo.add_run(subtitulo)
    corrida.font.size = Pt(13)
    corrida.font.color.rgb = GRIS_SUAVE
    corrida.font.name = "Calibri"

    linea = documento.add_paragraph()
    linea.alignment = WD_ALIGN_PARAGRAPH.CENTER
    borde_parrafo(linea, "bottom", "1F4D2E", 12)
    linea.paragraph_format.space_after = Pt(26)

    for metadato in metadatos:
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo.paragraph_format.space_after = Pt(4)
        agregar_texto_enlinea(parrafo, metadato, tamano=10.5)
        for corrida in parrafo.runs:
            if corrida.bold:
                corrida.font.color.rgb = VERDE

    if cita:
        parrafo = documento.add_paragraph()
        parrafo.paragraph_format.space_before = Pt(30)
        parrafo.paragraph_format.left_indent = Cm(2.2)
        parrafo.paragraph_format.right_indent = Cm(2.2)
        parrafo.paragraph_format.space_after = Pt(8)
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sombrear(parrafo._p, "F2F6F2")
        agregar_texto_enlinea(parrafo, cita, cursiva=True, tamano=9.5, color=GRIS_SUAVE)

    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(80)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    corrida = parrafo.add_run("Universidad Católica Luis Amigó  ·  Ingeniería de Sistemas  ·  2026")
    corrida.font.size = Pt(8.5)
    corrida.font.color.rgb = GRIS_SUAVE


# ---------------------------------------------------------------------------
# Bloques
# ---------------------------------------------------------------------------


def agregar_imagen(documento: Document, ruta: Path, alt: str, temporal: Path) -> None:
    if not ruta.exists():
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        corrida = parrafo.add_run(f"[Imagen no encontrada: {ruta.name}]")
        corrida.italic = True
        corrida.font.color.rgb = RGBColor(0xB0, 0x30, 0x30)
        return

    with Image.open(ruta) as imagen:
        ancho_px, alto_px = imagen.size

    relacion = alto_px / ancho_px
    partes: list[Path] = []
    if relacion > UMBRAL_DIVISION:
        cantidad = max(2, round(relacion / 1.15))
        alto_parte = alto_px // cantidad
        with Image.open(ruta) as imagen:
            for indice in range(cantidad):
                inicio = indice * alto_parte
                fin = alto_px if indice == cantidad - 1 else (indice + 1) * alto_parte
                recorte = imagen.crop((0, inicio, ancho_px, fin))
                destino = temporal / f"{ruta.stem}_parte{indice + 1}{ruta.suffix}"
                recorte.save(destino, quality=92)
                partes.append(destino)
    else:
        partes.append(ruta)

    for indice, parte in enumerate(partes, start=1):
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo.paragraph_format.space_before = Pt(6)
        parrafo.paragraph_format.space_after = Pt(2)
        parrafo.paragraph_format.keep_with_next = True
        corrida = parrafo.add_run()
        corrida.add_picture(str(parte), width=Cm(ANCHO_UTIL_CM))
        if len(partes) > 1:
            etiqueta = documento.add_paragraph()
            etiqueta.alignment = WD_ALIGN_PARAGRAPH.CENTER
            etiqueta.paragraph_format.space_after = Pt(2)
            corrida = etiqueta.add_run(f"{alt} — parte {indice} de {len(partes)}")
            corrida.font.size = Pt(8)
            corrida.italic = True
            corrida.font.color.rgb = GRIS_SUAVE


def agregar_tabla(documento: Document, filas: list[list[str]]) -> None:
    if not filas:
        return
    encabezado = filas[0]
    cuerpo = filas[1:]
    columnas = len(encabezado)
    tabla = documento.add_table(rows=1, cols=columnas)
    tabla.style = "Table Grid"
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.autofit = False

    tblPr = tabla._tbl.tblPr
    ancho = tblPr.find(qn("w:tblW"))
    if ancho is None:
        ancho = OxmlElement("w:tblW")
        tblPr.append(ancho)
    ancho.set(qn("w:w"), "4900")
    ancho.set(qn("w:type"), "pct")

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    margenes = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        margen = OxmlElement(f"w:{lado}")
        margen.set(qn("w:w"), "57")
        margen.set(qn("w:type"), "dxa")
        margenes.append(margen)
    tblPr.append(margenes)

    anchos = _calcular_anchos(filas, 16.2)
    for indice, valor in enumerate(anchos):
        tabla.columns[indice].width = Cm(valor)

    fila_encabezado = tabla.rows[0]
    _repetir_encabezado(fila_encabezado)
    for indice, texto in enumerate(encabezado):
        celda = fila_encabezado.cells[indice]
        celda.width = Cm(anchos[indice])
        celda.text = ""
        sombrear(celda._tc, VERDE_ENCABEZADO)
        parrafo = celda.paragraphs[0]
        parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        parrafo.paragraph_format.space_after = Pt(1)
        agregar_texto_enlinea(parrafo, texto, negrita=True, tamano=8.6, color=RGBColor(0xFF, 0xFF, 0xFF))

    for numero, fila in enumerate(cuerpo):
        celdas = tabla.add_row().cells
        _no_dividir_fila(tabla.rows[-1])
        for indice in range(columnas):
            texto = fila[indice] if indice < len(fila) else ""
            celda = celdas[indice]
            celda.width = Cm(anchos[indice])
            celda.text = ""
            if numero % 2 == 1:
                sombrear(celda._tc, VERDE_CLARO)
            parrafo = celda.paragraphs[0]
            parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
            parrafo.paragraph_format.space_after = Pt(1)
            parrafo.paragraph_format.line_spacing = 1.0
            agregar_texto_enlinea(parrafo, texto, tamano=8.6)

    documento.add_paragraph().paragraph_format.space_after = Pt(2)


def _calcular_anchos(filas: list[list[str]], total_cm: float) -> list[float]:
    """Distribuye el ancho de las columnas según el contenido esperado."""
    columnas = len(filas[0])
    pesos: list[float] = []
    for indice in range(columnas):
        textos = [fila[indice] for fila in filas if indice < len(fila)]
        largo_cuerpo = max((len(t) for t in textos[1:]), default=0)
        largo_encabezado = len(textos[0]) if textos else 0
        peso = max(8.0, largo_cuerpo, largo_encabezado * 1.15)
        pesos.append(min(peso, 70.0))

    suma = sum(pesos)
    minimo = min(1.55, total_cm / max(columnas, 1))
    disponible = max(0.0, total_cm - minimo * columnas)
    anchos = [minimo + disponible * peso / suma for peso in pesos]
    return anchos


def _repetir_encabezado(fila) -> None:
    trPr = fila._tr.get_or_add_trPr()
    trPr.append(parse_xml(rf'<w:tblHeader {nsdecls("w")} w:val="true"/>'))


def _no_dividir_fila(fila) -> None:
    trPr = fila._tr.get_or_add_trPr()
    trPr.append(parse_xml(rf'<w:cantSplit {nsdecls("w")} w:val="true"/>'))


def agregar_codigo(documento: Document, lineas: list[str]) -> None:
    if not lineas:
        lineas = [""]
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(6)
    parrafo.paragraph_format.space_after = Pt(8)
    parrafo.paragraph_format.line_spacing = 1.0
    parrafo.paragraph_format.left_indent = Cm(0.25)
    parrafo.paragraph_format.right_indent = Cm(0.15)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sombrear(parrafo._p, FONDO_CODIGO)
    borde_parrafo(parrafo, "left", "8FAE94", 18)
    for indice, linea in enumerate(lineas):
        corrida = parrafo.add_run(linea)
        corrida.font.name = "Consolas"
        corrida.font.size = Pt(8)
        corrida.font.color.rgb = RGBColor(0x2E, 0x33, 0x2F)
        if indice < len(lineas) - 1:
            corrida.add_break()


def agregar_cita(documento: Document, texto: str) -> None:
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.left_indent = Cm(0.6)
    parrafo.paragraph_format.right_indent = Cm(0.4)
    parrafo.paragraph_format.space_before = Pt(6)
    parrafo.paragraph_format.space_after = Pt(8)
    sombrear(parrafo._p, "F2F6F2")
    borde_parrafo(parrafo, "left", "1F4D2E", 18)
    agregar_texto_enlinea(parrafo, texto, cursiva=True, tamano=9.8, color=GRIS_SUAVE)


def agregar_caption(documento: Document, texto: str) -> None:
    parrafo = documento.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(10)
    agregar_texto_enlinea(parrafo, texto.strip("*"), cursiva=True, tamano=8.8, color=GRIS_SUAVE)


def agregar_lista(documento: Document, texto: str, nivel: int, marcador: str) -> None:
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.left_indent = Cm(0.65 + nivel * 0.55)
    parrafo.paragraph_format.first_line_indent = Cm(-0.45)
    parrafo.paragraph_format.space_after = Pt(3)
    parrafo.paragraph_format.line_spacing = 1.1
    parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    corrida = parrafo.add_run(f"{marcador}  ")
    corrida.font.color.rgb = VERDE
    corrida.bold = True
    agregar_texto_enlinea(parrafo, texto)


def agregar_regla(documento: Document) -> None:
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(4)
    parrafo.paragraph_format.space_after = Pt(10)
    borde_parrafo(parrafo, "bottom", "C9D6CB", 6)


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------


def es_separador_tabla(linea: str) -> bool:
    celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
    return bool(celdas) and all(re.fullmatch(r":?-{3,}:?", c) for c in celdas)


def dividir_fila(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def convertir_markdown(documento: Document, lineas: list[str], temporal: Path) -> None:
    indice = 0
    pendiente: list[str] = []

    def vaciar_pendiente() -> None:
        if not pendiente:
            return
        texto = " ".join(p.strip() for p in pendiente).strip()
        pendiente.clear()
        if not texto:
            return
        parrafo = documento.add_paragraph()
        agregar_texto_enlinea(parrafo, texto)

    while indice < len(lineas):
        linea = lineas[indice]
        limpia = linea.strip()

        if not limpia:
            vaciar_pendiente()
            indice += 1
            continue

        if limpia.startswith("```"):
            vaciar_pendiente()
            indice += 1
            codigo: list[str] = []
            while indice < len(lineas) and not lineas[indice].strip().startswith("```"):
                codigo.append(lineas[indice].rstrip())
                indice += 1
            indice += 1
            agregar_codigo(documento, codigo)
            continue

        if limpia.startswith("|") and indice + 1 < len(lineas) and es_separador_tabla(lineas[indice + 1]):
            vaciar_pendiente()
            filas = [dividir_fila(limpia)]
            indice += 2
            while indice < len(lineas) and lineas[indice].strip().startswith("|"):
                filas.append(dividir_fila(lineas[indice]))
                indice += 1
            agregar_tabla(documento, filas)
            continue

        imagen = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", limpia)
        if imagen:
            vaciar_pendiente()
            alt, ruta_relativa = imagen.group(1), imagen.group(2)
            agregar_imagen(documento, DOCS / ruta_relativa, alt, temporal)
            indice += 1
            continue

        if limpia.startswith("# "):
            vaciar_pendiente()
            documento.add_heading(limpia[2:].strip(), level=1)
            indice += 1
            continue

        if limpia.startswith("## "):
            vaciar_pendiente()
            documento.add_heading(limpia[3:].strip(), level=2)
            indice += 1
            continue

        if limpia.startswith("### "):
            vaciar_pendiente()
            documento.add_heading(limpia[4:].strip(), level=3)
            indice += 1
            continue

        if limpia.startswith(">"):
            vaciar_pendiente()
            agregar_cita(documento, limpia[1:].strip())
            indice += 1
            continue

        if re.fullmatch(r"-{3,}", limpia):
            vaciar_pendiente()
            agregar_regla(documento)
            indice += 1
            continue

        if re.match(r"^(\*[^*].*\*)$", limpia) and limpia.lower().startswith(("*figura", "*tabla")):
            vaciar_pendiente()
            agregar_caption(documento, limpia)
            indice += 1
            continue

        casilla = re.match(r"^[-*]\s+\[([ xX])\]\s+(.+)$", limpia)
        if casilla:
            vaciar_pendiente()
            marcador = "☑" if casilla.group(1).lower() == "x" else "☐"
            agregar_lista(documento, casilla.group(2), 0, marcador)
            indice += 1
            continue

        vineta = re.match(r"^(\s*)[-*]\s+(.+)$", linea)
        if vineta:
            vaciar_pendiente()
            nivel = len(vineta.group(1).replace("\t", "  ")) // 2
            agregar_lista(documento, vineta.group(2), nivel, "•")
            indice += 1
            continue

        numerada = re.match(r"^(\s*)(\d+)\.\s+(.+)$", linea)
        if numerada:
            vaciar_pendiente()
            nivel = len(numerada.group(1).replace("\t", "  ")) // 2
            agregar_lista(documento, numerada.group(3), nivel, f"{numerada.group(2)}.")
            indice += 1
            continue

        pendiente.append(linea)
        indice += 1

    vaciar_pendiente()


def main() -> None:
    if not ORIGEN.exists():
        raise SystemExit(f"No se encontró el documento de origen: {ORIGEN}")

    lineas = ORIGEN.read_text(encoding="utf-8").splitlines()

    try:
        corte = next(i for i, l in enumerate(lineas) if l.strip() == "# Contenido")
    except StopIteration as error:
        raise SystemExit("No se encontró el encabezado '# Contenido'.") from error

    documento = Document()
    propiedades_documento(documento)
    configurar_estilos(documento)
    configurar_pagina(documento)
    construir_portada(documento, lineas[:corte])

    # Tabla de entrega y resumen ejecutivo en una página aparte.
    inicio_resumen = next(
        (i for i, l in enumerate(lineas[:corte]) if l.strip().startswith("| Elemento de entrega")),
        corte,
    )
    documento.add_page_break()
    documento.add_heading("Resumen de la entrega", level=1)
    documento.paragraphs[-1].paragraph_format.page_break_before = False

    with tempfile.TemporaryDirectory(prefix="docx_imagenes_") as carpeta:
        convertir_markdown(documento, lineas[inicio_resumen:corte], Path(carpeta))
        convertir_markdown(documento, lineas[corte:], Path(carpeta))
        documento.save(DESTINO)

    print(f"Documento generado: {DESTINO}")


if __name__ == "__main__":
    main()
```

---

## Resumen

- Archivos incluidos: **28**
- Líneas de código y configuración: **6621**
- Credenciales incluidas: **ninguna** (se usan variables de entorno)
