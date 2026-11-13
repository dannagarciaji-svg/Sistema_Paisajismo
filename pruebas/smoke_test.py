# ============================================================
#  Pruebas de integración de la API REST
#  Uso:  python pruebas/smoke_test.py [URL_BASE]
#  Por defecto: http://127.0.0.1:5000
# ============================================================
import sys
import time

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
SUFIJO = str(int(time.time()))
RESULTADOS = []


def comprobar(nombre, condicion=True, detalle=""):
    estado = "APROBADA" if condicion else "FALLIDA"
    RESULTADOS.append((nombre, estado, detalle))
    print(f"[{estado}] {nombre}" + (f" -> {detalle}" if detalle else ""))


def solicitud(metodo, ruta, esperado, cuerpo=None):
    respuesta = requests.request(metodo, f"{BASE}{ruta}", json=cuerpo, timeout=30)
    if respuesta.status_code != esperado:
        raise AssertionError(
            f"{metodo} {ruta}: se esperaba {esperado} y se obtuvo {respuesta.status_code}: {respuesta.text[:300]}"
        )
    try:
        return respuesta.json()
    except ValueError:
        return {}


def main():
    print(f"Ejecutando pruebas contra {BASE}\n")

    salud = solicitud("GET", "/api/health", 200)
    comprobar("Conexión con MongoDB Atlas", salud.get("estado") == "ok", str(salud.get("colecciones")))

    # ------------------- Consultas generales -------------------
    for ruta, minimo in [
        ("/clientes", 1),
        ("/propiedades", 1),
        ("/servicios_contratos", 1),
        ("/personal", 1),
        ("/visitas_mantenimiento", 1),
        ("/insumos", 1),
    ]:
        datos = solicitud("GET", ruta, 200)
        comprobar(f"GET {ruta} retorna arreglo de datos", len(datos.get("datos", [])) >= minimo, f"{len(datos.get('datos', []))} registros")

    # ------------------------ Filtros --------------------------
    activos = solicitud("GET", "/clientes?estado=Activo", 200)
    comprobar(
        "Filtro de clientes por estado",
        all(c["estado"] == "Activo" for c in activos["datos"]),
        f"{len(activos['datos'])} clientes activos",
    )
    criticos = solicitud("GET", "/insumos?bajo_stock=true", 200)
    comprobar(
        "Filtro de insumos en nivel crítico",
        len(criticos["datos"]) >= 1,
        f"{len(criticos['datos'])} insumos críticos",
    )
    busqueda = solicitud("GET", "/propiedades?q=Rosa", 200)
    comprobar("Búsqueda por especie vegetal", len(busqueda["datos"]) >= 1, f"{len(busqueda['datos'])} coincidencias")

    # ------------------------- CRUD ----------------------------
    documento = f"99{SUFIJO[-8:]}"
    creado = solicitud(
        "POST",
        "/clientes",
        201,
        {
            "nombre": "Cliente de Prueba Automatizada",
            "documento": documento,
            "telefono": "3000000000",
            "correo": "prueba.automatizada@example.com",
            "direccion": "Calle de Prueba #1-01",
            "estado": "Activo",
        },
    )
    id_cliente = creado["id"]
    comprobar("POST /clientes crea un cliente", bool(id_cliente))

    solicitud(
        "POST",
        "/clientes",
        409,
        {
            "nombre": "Cliente Duplicado",
            "documento": documento,
            "telefono": "3000000001",
            "correo": "duplicado@example.com",
            "direccion": "Calle Duplicada",
            "estado": "Activo",
        },
    )
    comprobar("Regla de documento único en clientes (409)")

    solicitud(
        "PUT",
        f"/clientes/{id_cliente}",
        200,
        {"telefono": "3111111111", "direccion": "Carrera de Prueba #2-02"},
    )
    actualizado = solicitud("GET", f"/clientes/{id_cliente}", 200)["datos"]
    comprobar("PUT /clientes actualiza parcialmente", actualizado["telefono"] == "3111111111")

    solicitud("GET", "/clientes/identificador-invalido", 400)
    comprobar("Validación de ObjectId mal formado (400)")

    # ------------------ Integridad referencial -----------------
    solicitud(
        "POST",
        "/propiedades",
        404,
        {
            "cliente_id": "000000000000000000000000",
            "nombre": "Propiedad sin cliente",
            "direccion": "Calle 0 #0-0",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 100,
        },
    )
    comprobar("Propiedad con cliente inexistente rechazada (404)")

    solicitud(
        "POST",
        "/propiedades",
        400,
        {
            "cliente_id": id_cliente,
            "nombre": "Propiedad con área inválida",
            "direccion": "Calle 0 #0-0",
            "ciudad": "Medellín",
            "tipo_propiedad": "Casa",
            "area_m2": 0,
        },
    )
    comprobar("Validación de área mayor que cero (400)")

    solicitud(
        "POST",
        "/servicios_contratos",
        400,
        {
            "cliente_id": id_cliente,
            "servicios": [{"nombre": "Servicio de prueba", "descripcion": "Prueba", "precio_acordado": 100000}],
            "fecha_inicio": "2026-12-31",
            "fecha_fin": "2026-01-01",
            "valor_total": 100000,
            "estado": "Activo",
        },
    )
    comprobar("Coherencia cronológica de contratos (400)")

    solicitud(
        "POST",
        "/servicios_contratos",
        400,
        {
            "cliente_id": id_cliente,
            "servicios": [{"nombre": "Servicio de prueba", "descripcion": "Prueba", "precio_acordado": 100000}],
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2027-12-01",
            "valor_total": 500000,
            "estado": "Activo",
        },
    )
    comprobar("Validación de valor total contra servicios (400)")

    # ------------------- Reglas de inventario ------------------
    insumos = solicitud("GET", "/insumos", 200)["datos"]
    insumo = next(i for i in insumos if i["existencias"] > 0)
    propiedades = solicitud("GET", "/propiedades", 200)["datos"]
    contratos = solicitud("GET", "/servicios_contratos?estado=Activo", 200)["datos"]
    par = next(
        (c, p)
        for c in contratos
        for p in propiedades
        if p["cliente_id"] == c["cliente_id"]
    )
    contrato, propiedad = par
    personal_activo = solicitud("GET", "/personal?estado=Activo", 200)["datos"][0]

    solicitud(
        "POST",
        "/visitas_mantenimiento",
        404,
        {
            "propiedad_id": "000000000000000000000000",
            "contrato_id": contrato["_id"],
            "fecha_programada": "2026-11-15T08:00:00",
            "personal_asignado": [personal_activo["_id"]],
            "estado": "Programada",
            "insumos_utilizados": [],
        },
    )
    comprobar("Visita con propiedad inexistente rechazada (404)")

    solicitud(
        "POST",
        "/visitas_mantenimiento",
        409,
        {
            "propiedad_id": propiedad["_id"],
            "contrato_id": contrato["_id"],
            "fecha_programada": "2026-11-15T08:00:00",
            "personal_asignado": [personal_activo["_id"]],
            "estado": "En proceso",
            "actividades_realizadas": ["Prueba de consumo"],
            "insumos_utilizados": [{"insumo_id": insumo["_id"], "cantidad": insumo["existencias"] + 1000}],
        },
    )
    comprobar("Rechazo de consumo superior al inventario (409)")

    # ------------------ Bloqueo de eliminación -----------------
    clientes = solicitud("GET", "/clientes", 200)["datos"]
    cliente_con_propiedades = next(c for c in clientes if c["nombre"] == "Laura Martínez")
    solicitud("DELETE", f"/clientes/{cliente_con_propiedades['_id']}", 409)
    comprobar("Bloqueo de eliminación de cliente con propiedades (409)")

    solicitud("DELETE", f"/clientes/{id_cliente}", 200)
    comprobar("DELETE /clientes elimina el registro de prueba")

    # ------------------- Consultas analíticas -----------------
    consultas = {
        "Consulta 1 - Clientes y propiedades": "/analitica/clientes-propiedades",
        "Consulta 2 - Visitas con detalle": "/analitica/visitas-detalle",
        "Consulta 3 - Visitas por estado": "/analitica/visitas-estado",
        "Consulta 4 - Insumos más utilizados": "/analitica/insumos-mas-utilizados",
        "Consulta 5 - Servicios más contratados": "/analitica/servicios-mas-contratados",
        "KPIs del tablero": "/analitica/kpis",
    }
    for nombre, ruta in consultas.items():
        respuesta = solicitud("GET", ruta, 200)
        comprobar(nombre, bool(respuesta.get("datos")), f"{len(respuesta.get('datos', []))} filas/indicadores")

    print("\n" + "=" * 64)
    aprobadas = sum(1 for _, estado, _ in RESULTADOS if estado == "APROBADA")
    print(f"Resultado: {aprobadas}/{len(RESULTADOS)} pruebas aprobadas.")
    print("=" * 64)
    if aprobadas != len(RESULTADOS):
        sys.exit(1)


if __name__ == "__main__":
    main()
