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
