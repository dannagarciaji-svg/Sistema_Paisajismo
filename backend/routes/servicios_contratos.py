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
