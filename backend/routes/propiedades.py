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
