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
