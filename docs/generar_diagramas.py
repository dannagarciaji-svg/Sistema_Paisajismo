# -*- coding: utf-8 -*-
"""Genera los diagramas del modelo de datos y de arquitectura (PNG)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

DESTINO = Path(__file__).resolve().parent / "diagramas"
DESTINO.mkdir(parents=True, exist_ok=True)

VERDE = "#1f6f4a"
VERDE_CLARO = "#e8f5ee"
VERDE_BORDE = "#2f8f63"
GRIS = "#44514a"
NARANJA = "#c96a1b"
AZUL = "#245a8d"
FONDO = "#fbfdfb"


def caja(ax, x, y, w, h, titulo, campos, color=VERDE, relleno=VERDE_CLARO, fs=7.2):
    sombra = FancyBboxPatch((x + 0.004, y - 0.006), w, h,
                            boxstyle="round,pad=0.006,rounding_size=0.012",
                            linewidth=0, facecolor="#000000", alpha=0.10, zorder=1)
    ax.add_patch(sombra)
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.006,rounding_size=0.012",
                          linewidth=1.6, edgecolor=color, facecolor=relleno, zorder=2)
    ax.add_patch(rect)
    ax.add_patch(FancyBboxPatch((x, y + h - 0.052), w, 0.052,
                                boxstyle="round,pad=0.006,rounding_size=0.012",
                                linewidth=0, facecolor=color, zorder=3))
    ax.text(x + 0.012, y + h - 0.027, titulo, fontsize=10.5, fontweight="bold",
            color="white", va="center", ha="left", zorder=4)
    for i, campo in enumerate(campos):
        ax.text(x + 0.014, y + h - 0.078 - i * 0.0265, campo, fontsize=fs,
                color=GRIS, va="center", ha="left", family="DejaVu Sans Mono", zorder=4)


def flecha(ax, p1, p2, etiqueta, color=VERDE, rad=0.0, dx=0.0, dy=0.0, fs=8.5):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=16, linewidth=1.7,
        color=color, connectionstyle=f"arc3,rad={rad}", zorder=5,
        shrinkA=3, shrinkB=3,
    ))
    mx = (p1[0] + p2[0]) / 2 + dx
    my = (p1[1] + p2[1]) / 2 + dy
    ax.text(mx, my, etiqueta, fontsize=fs, color=color, fontweight="bold",
            ha="center", va="center", zorder=6,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                      edgecolor=color, linewidth=0.9, alpha=0.96))


def modelo_datos():
    fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
    fig.patch.set_facecolor(FONDO)
    ax.set_facecolor(FONDO)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.972, "Modelo de datos · Sistema de Gestión de Servicios de Paisajismo",
            fontsize=18, fontweight="bold", color=VERDE, ha="center", va="center")
    ax.text(0.5, 0.938, "MongoDB Atlas · base de datos jardineria_db · 6 colecciones",
            fontsize=10.5, color=GRIS, ha="center", va="center")

    caja(ax, 0.025, 0.615, 0.305, 0.285, "clientes", [
        "_id: ObjectId (PK)",
        "nombre: string",
        "documento: string (único)",
        "telefono: string",
        "correo: string",
        "direccion: string",
        "estado: Activo | Inactivo",
    ])

    caja(ax, 0.615, 0.615, 0.355, 0.285, "propiedades", [
        "_id: ObjectId (PK)",
        "cliente_id: ObjectId (FK → clientes)",
        "nombre: string",
        "direccion: string",
        "ciudad: string",
        "tipo_propiedad: enum",
        "area_m2: number",
        "especies: [ subdocumento embebido ]",
    ])

    caja(ax, 0.625, 0.315, 0.345, 0.235, "servicios_contratos", [
        "_id: ObjectId (PK)",
        "cliente_id: ObjectId (FK → clientes)",
        "servicios: [ subdocumento embebido ]",
        "fecha_inicio / fecha_fin: date",
        "valor_total: number (calculado)",
        "estado: Activo | Suspendido | ...",
    ])

    caja(ax, 0.305, 0.035, 0.375, 0.245, "visitas_mantenimiento", [
        "_id: ObjectId (PK)",
        "propiedad_id: ObjectId (FK → propiedades)",
        "contrato_id: ObjectId (FK → servicios_contratos)",
        "fecha_programada: date",
        "personal_asignado: [ ref → personal ]",
        "insumos_utilizados: [ ref → insumos ]",
        "estado: Programada | En proceso | ...",
    ])

    caja(ax, 0.025, 0.035, 0.245, 0.245, "personal", [
        "_id: ObjectId (PK)",
        "nombre: string",
        "documento: string (único)",
        "telefono / correo: string",
        "cargo: enum",
        "salario: number",
        "especialidades: [ string ]",
        "estado: Activo | Inactivo",
    ])

    caja(ax, 0.735, 0.025, 0.235, 0.245, "insumos", [
        "_id: ObjectId (PK)",
        "nombre: string",
        "unidad_medida: enum",
        "existencias: int",
        "stock_minimo: int",
        "estado: Disponible |",
        "        Bajo stock | Agotado",
    ])

    flecha(ax, (0.330, 0.760), (0.615, 0.760), "1 : N", dx=0.0, dy=0.018)
    flecha(ax, (0.245, 0.615), (0.625, 0.505), "1 : N", rad=-0.18, dx=-0.035, dy=0.030)
    flecha(ax, (0.615, 0.665), (0.600, 0.280), "1 : N", dx=-0.032, dy=0.0)
    flecha(ax, (0.790, 0.315), (0.680, 0.280), "1 : N", dx=0.020, dy=0.018)
    flecha(ax, (0.270, 0.157), (0.305, 0.157), "N : M", dx=0.0, dy=0.022, fs=7.4)
    flecha(ax, (0.735, 0.147), (0.680, 0.147), "N : M", dx=0.0, dy=0.022, fs=7.4, color=NARANJA)

    leyenda_y = 0.355
    ax.add_patch(FancyBboxPatch((0.035, leyenda_y - 0.075), 0.245, 0.13,
                                boxstyle="round,pad=0.006,rounding_size=0.01",
                                linewidth=1.0, edgecolor="#b9c9bf", facecolor="white", zorder=2))
    ax.text(0.050, leyenda_y + 0.028, "Convenciones", fontsize=9.5, fontweight="bold", color=VERDE)
    ax.text(0.050, leyenda_y + 0.002, "PK  Clave primaria", fontsize=8, color=GRIS)
    ax.text(0.050, leyenda_y - 0.024, "FK  Referencia entre colecciones", fontsize=8, color=GRIS)
    ax.text(0.050, leyenda_y - 0.050, "1:N / N:M  Cardinalidad", fontsize=8, color=GRIS)

    ax.text(0.5, 0.004,
            "Especies botánicas y servicios contratados se almacenan como subdocumentos embebidos; "
            "las demás relaciones usan referencias por ObjectId.",
            fontsize=8.6, color="#6b7a71", ha="center", va="bottom", style="italic")

    fig.savefig(DESTINO / "modelo_datos.png", bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)


def arquitectura():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    fig.patch.set_facecolor(FONDO)
    ax.set_facecolor(FONDO)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.962, "Arquitectura de la solución",
            fontsize=19, fontweight="bold", color=VERDE, ha="center")
    ax.text(0.5, 0.925, "Aplicación web full-stack desplegada en la nube",
            fontsize=10.5, color=GRIS, ha="center")

    capas = [
        (0.715, "Usuario", "Navegador web (escritorio o móvil)\nHTTPS · interfaz en español", "#5c6f64", "#eef2ef"),
        (0.555, "Frontend · SPA", "HTML5 · CSS3 · JavaScript (ES6)\nChart.js · rutas hash · fetch/JSON", AZUL, "#e8f0f8"),
        (0.395, "Backend · API REST", "Flask 3 · 7 blueprints\nvalidaciones · reglas de negocio · inventario atómico", VERDE, VERDE_CLARO),
        (0.235, "Acceso a datos", "PyMongo 4 · certifi (TLS)\npool de conexiones · serialización BSON/JSON", NARANJA, "#fbf0e6"),
        (0.075, "MongoDB Atlas", "jardineria_db · 6 colecciones\níndices · Aggregation Pipeline", "#4b3f72", "#efecf7"),
    ]

    for y, titulo, detalle, color, relleno in capas:
        rect = FancyBboxPatch((0.245, y), 0.51, 0.115,
                              boxstyle="round,pad=0.008,rounding_size=0.018",
                              linewidth=1.8, edgecolor=color, facecolor=relleno, zorder=2)
        ax.add_patch(rect)
        ax.text(0.270, y + 0.079, titulo, fontsize=12, fontweight="bold", color=color, va="center")
        ax.text(0.270, y + 0.038, detalle, fontsize=8.8, color=GRIS, va="center")

    for y1, y2 in [(0.715, 0.670), (0.555, 0.510), (0.395, 0.350), (0.235, 0.190)]:
        ax.add_patch(FancyArrowPatch((0.500, y1), (0.500, y2), arrowstyle="<|-|>",
                                     mutation_scale=13, linewidth=1.5, color="#7d8c83", zorder=1))
    ax.text(0.515, 0.692, "HTTPS / JSON", fontsize=8, color="#6b7a71", rotation=90, va="center")
    ax.text(0.515, 0.532, "fetch()", fontsize=8, color="#6b7a71", rotation=90, va="center")
    ax.text(0.515, 0.372, "PyMongo", fontsize=8, color="#6b7a71", rotation=90, va="center")
    ax.text(0.515, 0.212, "TLS 1.2+", fontsize=8, color="#6b7a71", rotation=90, va="center")

    laterales = [
        (0.790, 0.760, "Render", "Despliegue del servicio\nweb con Gunicorn", "#2b6cb0", "#e6effa"),
        (0.790, 0.570, "GitHub", "Repositorio público\ndel código fuente", "#24292f", "#eef0f2"),
        (0.790, 0.380, "Variables de entorno", "MONGO_URI y MONGO_DB\nfuera del repositorio", "#8a5a00", "#fbf3e2"),
        (0.790, 0.190, "MongoDB Atlas", "Clúster administrado\ncopias y disponibilidad", "#4b3f72", "#efecf7"),
    ]
    for x, y, titulo, detalle, color, relleno in laterales:
        rect = FancyBboxPatch((x, y), 0.175, 0.115,
                              boxstyle="round,pad=0.008,rounding_size=0.016",
                              linewidth=1.4, edgecolor=color, facecolor=relleno, zorder=2)
        ax.add_patch(rect)
        ax.text(x + 0.014, y + 0.077, titulo, fontsize=9.4, fontweight="bold", color=color)
        ax.text(x + 0.014, y + 0.036, detalle, fontsize=7.4, color=GRIS)

    ax.text(0.245, 0.012,
            "El navegador consume la API REST; Flask aplica las reglas de negocio y PyMongo "
            "persiste en MongoDB Atlas. Las credenciales llegan por variables de entorno.",
            fontsize=8.6, color="#6b7a71", ha="left", va="bottom", style="italic")

    fig.savefig(DESTINO / "arquitectura.png", bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)


if __name__ == "__main__":
    modelo_datos()
    arquitectura()
    print("Diagramas generados en", DESTINO)
