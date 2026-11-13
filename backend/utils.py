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
