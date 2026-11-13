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
