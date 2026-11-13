# ============================================================
#  Genera el anexo con el código fuente completo del proyecto
#  y un ZIP con todo el sistema (sin credenciales ni venv).
#  Uso:  python docs/generar_anexo_codigo.py
# ============================================================
from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
SALIDA_MD = DOCS / "Anexo_Codigo_Completo.md"
SALIDA_ZIP = RAIZ / "Sistema_Paisajismo_Codigo.zip"

# (ruta relativa, título de la sección, descripción)
ARCHIVOS = [
    ("app.py", "Punto de entrada de Flask", "Crea la aplicación, registra los blueprints, expone /api/health y centraliza el manejo de errores."),
    ("backend/config.py", "Conexión a MongoDB Atlas", "Lee las variables de entorno y crea el cliente único de PyMongo y las seis colecciones."),
    ("backend/utils.py", "Utilidades compartidas", "Serialización de ObjectId/fechas, respuestas JSON y conversión segura de identificadores."),
    ("backend/validators.py", "Validaciones y reglas de negocio", "Funciones de validación de texto, correo, teléfono, documento, fechas, enums y estado de insumos."),
    ("backend/inventario.py", "Control automático de inventario", "Descuenta y restaura existencias de forma atómica al registrar, editar o eliminar visitas."),
    ("backend/routes/clientes.py", "CRUD de clientes", "Consulta, búsqueda, registro, actualización y eliminación con protección de integridad referencial."),
    ("backend/routes/propiedades.py", "CRUD de propiedades", "Gestión de predios con inventario botánico embebido y validación del cliente asociado."),
    ("backend/routes/servicios_contratos.py", "CRUD de servicios y contratos", "Contratos con servicios embebidos, cálculo de valor_total y validación de fechas y estado."),
    ("backend/routes/personal.py", "CRUD de personal", "Gestión del personal técnico y operativo con documento único y cargos válidos."),
    ("backend/routes/visitas_mantenimiento.py", "CRUD de visitas de mantenimiento", "Entidad transaccional central: reglas de contrato activo, fechas, personal e insumos."),
    ("backend/routes/insumos.py", "CRUD de insumos", "Inventario de materiales con estado derivado de existencias y stock mínimo."),
    ("backend/routes/analitica.py", "Consultas analíticas (Aggregation Pipeline)", "Las cinco consultas con $lookup, $match, $project, $sort, $limit, $group y $unwind, más los KPIs."),
    ("frontend/index.html", "Interfaz web (HTML)", "Estructura de la SPA: barra lateral, panel, modales y carga de scripts."),
    ("frontend/css/estilos.css", "Interfaz web (CSS)", "Diseño responsivo, componentes, tablas, formularios y tarjetas del panel."),
    ("frontend/js/api.js", "Cliente HTTP y utilidades del frontend", "Envoltorio de fetch, manejo de errores, formato de fechas/números y avisos."),
    ("frontend/js/formularios.js", "Formularios del frontend", "Construcción y validación de formularios para las seis entidades."),
    ("frontend/js/vistas.js", "Vistas, tablas y gráficas", "Renderizado de módulos, tablas, detalle de propiedad y los cinco reportes con Chart.js."),
    ("frontend/js/app.js", "Enrutador de la SPA", "Navegación por hash, estado de la vista y verificación de conexión con la API."),
    ("seed.py", "Semilla de datos e índices", "Restablece las colecciones, crea los índices y carga los datos de demostración."),
    ("pruebas/smoke_test.py", "Pruebas automatizadas", "Suite de 28 pruebas de integración contra la API en ejecución."),
    ("requirements.txt", "Dependencias de producción", "Versiones fijas de Flask, PyMongo, dotenv, certifi y Gunicorn."),
    ("requirements-dev.txt", "Dependencias de desarrollo", "Herramientas usadas solo para generar documentación y pruebas."),
    ("Procfile", "Comando de arranque", "Define el proceso web para plataformas como Render o Heroku."),
    ("render.yaml", "Infraestructura como código", "Blueprint de Render con build, start, health check y variables de entorno."),
    (".env.example", "Plantilla de variables de entorno", "Muestra las variables necesarias sin incluir credenciales reales."),
    (".gitignore", "Exclusión de archivos sensibles", "Evita subir .env, venv, cachés y archivos temporales al repositorio."),
    ("docs/generar_diagramas.py", "Generador de diagramas", "Reproduce el diagrama de arquitectura y el modelo de datos con matplotlib."),
    ("docs/generar_docx.py", "Generador del documento técnico", "Convierte la documentación Markdown al DOCX entregable con portada, tablas e imágenes."),
]

LENGUAJES = {
    ".py": "python",
    ".html": "html",
    ".css": "css",
    ".js": "javascript",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".example": "dotenv",
}


def lenguaje(ruta: Path) -> str:
    if ruta.name == ".gitignore":
        return "text"
    return LENGUAJES.get(ruta.suffix, "text")


def leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()


def generar_markdown() -> None:
    total_lineas = 0
    partes: list[str] = [
        "# Anexo A — Código fuente completo",
        "",
        "**Proyecto:** Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico",
        "",
        "**Autora:** Danna Paulina García Jiménez",
        "",
        "**Asignatura:** Bases de Datos II",
        "",
        f"**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "Este anexo reúne, en orden de ejecución, todo el código que compone el sistema: "
        "el backend en Flask, la conexión con MongoDB Atlas, los seis módulos CRUD, las cinco "
        "consultas analíticas, el frontend en HTML/CSS/JavaScript, la semilla de datos, las "
        "pruebas y los archivos de despliegue.",
        "",
        "> Las credenciales reales no se incluyen. La cadena de conexión se configura mediante "
        "la variable de entorno `MONGO_URI`, tal como se explica en el capítulo 6 del documento técnico.",
        "",
        "## Índice de archivos",
        "",
        "| # | Archivo | Contenido |",
        "|---|---|---|",
    ]

    for indice, (ruta_rel, titulo, descripcion) in enumerate(ARCHIVOS, start=1):
        partes.append(f"| {indice} | `{ruta_rel}` | {titulo} |")
    partes.append("")

    for indice, (ruta_rel, titulo, descripcion) in enumerate(ARCHIVOS, start=1):
        ruta = RAIZ / ruta_rel
        if not ruta.exists():
            continue
        codigo = leer(ruta)
        lineas = codigo.count("\n") + 1
        total_lineas += lineas
        partes.extend(
            [
                "---",
                "",
                f"## A.{indice} {titulo}",
                "",
                f"**Archivo:** `{ruta_rel}` · **{lineas} líneas**",
                "",
                descripcion,
                "",
                f"```{lenguaje(ruta)}",
                codigo,
                "```",
                "",
            ]
        )

    partes.extend(
        [
            "---",
            "",
            "## Resumen",
            "",
            f"- Archivos incluidos: **{len(ARCHIVOS)}**",
            f"- Líneas de código y configuración: **{total_lineas}**",
            "- Credenciales incluidas: **ninguna** (se usan variables de entorno)",
            "",
        ]
    )

    SALIDA_MD.write_text("\n".join(partes), encoding="utf-8")
    print(f"Anexo generado: {SALIDA_MD} ({total_lineas} lineas)")


def generar_zip() -> None:
    excluir_dirs = {".git", "venv", ".venv", "__pycache__", ".pytest_cache", "node_modules"}
    excluir_archivos = {".env", SALIDA_ZIP.name}
    incluir_docs = True

    with zipfile.ZipFile(SALIDA_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for ruta in RAIZ.rglob("*"):
            if any(parte in excluir_dirs for parte in ruta.parts):
                continue
            if ruta.name in excluir_archivos:
                continue
            if ruta.suffix in {".pyc", ".pyo", ".zip"}:
                continue
            if not incluir_docs and "docs" in ruta.parts:
                continue
            if ruta.is_file():
                zf.write(ruta, ruta.relative_to(RAIZ).as_posix())

    tamano = SALIDA_ZIP.stat().st_size / (1024 * 1024)
    print(f"ZIP generado: {SALIDA_ZIP} ({tamano:.1f} MB)")


if __name__ == "__main__":
    generar_markdown()
    generar_zip()
