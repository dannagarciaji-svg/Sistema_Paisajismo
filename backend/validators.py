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
