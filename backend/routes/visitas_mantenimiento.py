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
