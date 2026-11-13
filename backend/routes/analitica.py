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
