# ============================================================
#  Punto de entrada de la aplicación Flask
#  Sistema de Gestión de Servicios de Paisajismo
# ============================================================
import logging

from flask import Flask, jsonify, request, send_from_directory
from pymongo.errors import PyMongoError

from backend.config import COLECCIONES, MONGO_DB, verificar_conexion
from backend.routes.analitica import analitica_bp
from backend.routes.clientes import clientes_bp
from backend.routes.insumos import insumos_bp
from backend.routes.personal import personal_bp
from backend.routes.propiedades import propiedades_bp
from backend.routes.servicios_contratos import servicios_contratos_bp
from backend.routes.visitas_mantenimiento import visitas_mantenimiento_bp
from backend.utils import ErrorApi

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def crear_app():
    app = Flask(__name__, static_folder="frontend", static_url_path="/static")
    app.config["JSON_SORT_KEYS"] = False

    # Registro de los seis módulos CRUD + módulo analítico
    for blueprint in (
        clientes_bp,
        propiedades_bp,
        servicios_contratos_bp,
        personal_bp,
        visitas_mantenimiento_bp,
        insumos_bp,
        analitica_bp,
    ):
        app.register_blueprint(blueprint)

    @app.route("/")
    def inicio():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/api/health", methods=["GET"])
    def salud():
        conectado = verificar_conexion()
        conteos = {}
        if conectado:
            try:
                conteos = {nombre: coleccion.count_documents({}) for nombre, coleccion in COLECCIONES.items()}
            except PyMongoError:
                conectado = False
        return (
            jsonify(
                {
                    "estado": "ok" if conectado else "degradado",
                    "base_de_datos": MONGO_DB,
                    "colecciones": conteos,
                }
            ),
            200 if conectado else 503,
        )

    @app.errorhandler(ErrorApi)
    def manejar_error_api(error):
        cuerpo = {"error": error.mensaje}
        if error.campos:
            cuerpo["detalles"] = error.campos
        return jsonify(cuerpo), error.codigo

    @app.errorhandler(PyMongoError)
    def manejar_error_mongo(error):
        app.logger.exception("Error de MongoDB: %s", error)
        return (
            jsonify({"error": "No fue posible comunicarse con la base de datos en la nube."}),
            503,
        )

    @app.errorhandler(404)
    def no_encontrado(error):
        if request.path.startswith("/static/"):
            return jsonify({"error": "Recurso estático no encontrado."}), 404
        return jsonify({"error": "Ruta no encontrada."}), 404

    @app.errorhandler(405)
    def metodo_no_permitido(error):
        return jsonify({"error": "Método HTTP no permitido para esta ruta."}), 405

    @app.errorhandler(Exception)
    def error_no_controlado(error):
        app.logger.exception("Error no controlado: %s", error)
        return jsonify({"error": "Ocurrió un error interno en el servidor."}), 500

    @app.after_request
    def cabeceras_seguridad(respuesta):
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "SAMEORIGIN"
        respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return respuesta

    return app


app = crear_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
