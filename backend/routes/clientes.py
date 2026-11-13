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
