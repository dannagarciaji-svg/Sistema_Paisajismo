"""Genera el documento DOCX del proyecto a partir del Markdown técnico.

Uso:
    python docs/generar_docx.py

El script convierte encabezados, párrafos, listas, tablas, bloques de código,
imágenes, citas y enlaces. Las capturas muy altas se dividen en partes para que
se puedan leer dentro de una página A4.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from PIL import Image
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
ORIGEN = DOCS / "Documentacion_Tecnica_Sistema_Paisajismo.md"
DESTINO = DOCS / "Documentacion_Tecnica_Sistema_Paisajismo.docx"

VERDE = RGBColor(0x1F, 0x4D, 0x2E)
VERDE_CLARO = "E8F0E9"
VERDE_ENCABEZADO = "1F4D2E"
GRIS_TEXTO = RGBColor(0x44, 0x4B, 0x45)
GRIS_SUAVE = RGBColor(0x6B, 0x72, 0x6C)
FONDO_CODIGO = "F3F5F3"
ANCHO_UTIL_CM = 16.4
UMBRAL_DIVISION = 1.45


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------


def sombrear(elemento, relleno: str) -> None:
    """Aplica sombreado a una celda o a un párrafo."""
    propiedades = elemento.get_or_add_tcPr() if hasattr(elemento, "get_or_add_tcPr") else elemento.get_or_add_pPr()
    propiedades.append(parse_xml(rf'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{relleno}"/>'))


def borde_parrafo(parrafo, lado: str = "left", color: str = "1F4D2E", tamano: int = 18) -> None:
    pPr = parrafo._p.get_or_add_pPr()
    bordes = pPr.find(qn("w:pBdr"))
    if bordes is None:
        bordes = OxmlElement("w:pBdr")
        pPr.append(bordes)
    borde = OxmlElement(f"w:{lado}")
    borde.set(qn("w:val"), "single")
    borde.set(qn("w:sz"), str(tamano))
    borde.set(qn("w:space"), "6")
    borde.set(qn("w:color"), color)
    bordes.append(borde)


def agregar_hipervincular(parrafo, texto: str, url: str) -> None:
    relationship_id = parrafo.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hipervinculo = OxmlElement("w:hyperlink")
    hipervinculo.set(qn("r:id"), relationship_id)
    corrida = OxmlElement("w:r")
    propiedades = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "1F5C99")
    subrayado = OxmlElement("w:u")
    subrayado.set(qn("w:val"), "single")
    propiedades.append(color)
    propiedades.append(subrayado)
    corrida.append(propiedades)
    nodo = OxmlElement("w:t")
    nodo.text = texto
    corrida.append(nodo)
    hipervinculo.append(corrida)
    parrafo._p.append(hipervinculo)


PATRON_ENLINEA = re.compile(
    r"(\*\*.+?\*\*|`[^`]+`|\*[^*\n]+?\*|\[[^\]]+\]\([^)]+\))",
    re.DOTALL,
)


def agregar_texto_enlinea(
    parrafo,
    texto: str,
    *,
    negrita: bool = False,
    cursiva: bool = False,
    tamano: float | None = None,
    color: RGBColor | None = None,
) -> None:
    """Agrega texto interpretando negrita, cursiva, código y enlaces."""
    posicion = 0
    for coincidencia in PATRON_ENLINEA.finditer(texto):
        if coincidencia.start() > posicion:
            _corrida(parrafo, texto[posicion : coincidencia.start()], negrita, cursiva, tamano, color)
        fragmento = coincidencia.group(0)
        if fragmento.startswith("**") and fragmento.endswith("**"):
            agregar_texto_enlinea(
                parrafo,
                fragmento[2:-2],
                negrita=True,
                cursiva=cursiva,
                tamano=tamano,
                color=color,
            )
        elif fragmento.startswith("`") and fragmento.endswith("`"):
            corrida = _corrida(parrafo, fragmento[1:-1], negrita, cursiva, tamano, color)
            corrida.font.name = "Consolas"
            corrida.font.size = Pt((tamano or 10.5) - 1.2)
            corrida.font.color.rgb = RGBColor(0x8A, 0x2E, 0x2E)
            sombrear_corrida(corrida, "F1F1F1")
        elif fragmento.startswith("*") and fragmento.endswith("*"):
            agregar_texto_enlinea(
                parrafo,
                fragmento[1:-1],
                negrita=negrita,
                cursiva=True,
                tamano=tamano,
                color=color,
            )
        else:
            enlace = re.match(r"\[([^\]]+)\]\(([^)]+)\)", fragmento)
            if enlace:
                agregar_hipervincular(parrafo, enlace.group(1), enlace.group(2))
        posicion = coincidencia.end()
    if posicion < len(texto):
        _corrida(parrafo, texto[posicion:], negrita, cursiva, tamano, color)


def _corrida(parrafo, texto, negrita, cursiva, tamano, color):
    corrida = parrafo.add_run(texto)
    corrida.bold = negrita
    corrida.italic = cursiva
    if tamano:
        corrida.font.size = Pt(tamano)
    if color:
        corrida.font.color.rgb = color
    return corrida


def sombrear_corrida(corrida, relleno: str) -> None:
    propiedades = corrida._r.get_or_add_rPr()
    propiedades.append(parse_xml(rf'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{relleno}"/>'))


# ---------------------------------------------------------------------------
# Configuración del documento
# ---------------------------------------------------------------------------


def configurar_estilos(documento: Document) -> None:
    estilos = documento.styles

    normal = estilos["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = GRIS_TEXTO
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    idioma = normal.element.get_or_add_rPr()
    idioma.append(parse_xml(rf'<w:lang {nsdecls("w")} w:val="es-CO" w:eastAsia="es-CO"/>'))

    h1 = estilos["Heading 1"]
    h1.font.name = "Calibri"
    h1.font.size = Pt(19)
    h1.font.bold = True
    h1.font.color.rgb = VERDE
    h1.paragraph_format.page_break_before = True
    h1.paragraph_format.space_before = Pt(0)
    h1.paragraph_format.space_after = Pt(14)
    h1.paragraph_format.keep_with_next = True
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    h2 = estilos["Heading 2"]
    h2.font.name = "Calibri"
    h2.font.size = Pt(13.5)
    h2.font.bold = True
    h2.font.color.rgb = VERDE
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    h2.paragraph_format.keep_with_next = True
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    h3 = estilos["Heading 3"]
    h3.font.name = "Calibri"
    h3.font.size = Pt(11.5)
    h3.font.bold = True
    h3.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    h3.paragraph_format.space_before = Pt(10)
    h3.paragraph_format.keep_with_next = True


def configurar_pagina(documento: Document) -> None:
    seccion = documento.sections[0]
    seccion.page_width = Cm(21)
    seccion.page_height = Cm(29.7)
    seccion.top_margin = Cm(2.2)
    seccion.bottom_margin = Cm(2.0)
    seccion.left_margin = Cm(2.3)
    seccion.right_margin = Cm(2.3)
    seccion.header_distance = Cm(1.0)
    seccion.footer_distance = Cm(0.9)
    seccion.different_first_page_header_footer = True

    encabezado = seccion.header
    parrafo_inicial = encabezado.paragraphs[0]
    parrafo_inicial._element.getparent().remove(parrafo_inicial._element)

    tabla_encabezado = encabezado.add_table(rows=1, cols=2, width=Cm(16.4))
    tabla_encabezado.autofit = False
    tabla_encabezado.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = tabla_encabezado._tbl.tblPr
    ancho_tabla = OxmlElement("w:tblW")
    ancho_tabla.set(qn("w:w"), "5000")
    ancho_tabla.set(qn("w:type"), "pct")
    tblPr.append(ancho_tabla)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    margenes = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        margen = OxmlElement(f"w:{lado}")
        margen.set(qn("w:w"), "0")
        margen.set(qn("w:type"), "dxa")
        margenes.append(margen)
    tblPr.append(margenes)
    bordes = OxmlElement("w:tblBorders")
    borde = OxmlElement("w:bottom")
    borde.set(qn("w:val"), "single")
    borde.set(qn("w:sz"), "6")
    borde.set(qn("w:space"), "0")
    borde.set(qn("w:color"), "C9D6CB")
    bordes.append(borde)
    tblPr.append(bordes)

    tabla_encabezado.columns[0].width = Cm(12.2)
    tabla_encabezado.columns[1].width = Cm(4.2)
    celda_izquierda, celda_derecha = tabla_encabezado.rows[0].cells
    celda_izquierda.width = Cm(12.2)
    celda_derecha.width = Cm(4.2)

    parrafo = celda_izquierda.paragraphs[0]
    parrafo.paragraph_format.space_after = Pt(0)
    corrida = parrafo.add_run("Sistema de Gestión de Servicios de Paisajismo")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    corrida.font.name = "Calibri"

    parrafo = celda_derecha.paragraphs[0]
    parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    parrafo.paragraph_format.space_after = Pt(0)
    corrida = parrafo.add_run("Bases de Datos II")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    corrida.font.name = "Calibri"

    cierre = encabezado.add_paragraph()
    cierre.paragraph_format.space_after = Pt(0)
    cierre.paragraph_format.line_spacing = Pt(1)
    corrida = cierre.add_run("")
    corrida.font.size = Pt(1)

    pie = seccion.footer
    parrafo = pie.paragraphs[0]
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    corrida = parrafo.add_run("Documentación técnica · ")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    _campo(parrafo, "PAGE")
    corrida = parrafo.add_run(" de ")
    corrida.font.size = Pt(8)
    corrida.font.color.rgb = GRIS_SUAVE
    _campo(parrafo, "NUMPAGES")


def _campo(parrafo, nombre: str) -> None:
    def corrida_con(elemento) -> None:
        corrida = parrafo.add_run()
        corrida.font.size = Pt(8)
        corrida.font.color.rgb = GRIS_SUAVE
        corrida._r.append(elemento)

    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    corrida_con(inicio)

    instruccion = OxmlElement("w:instrText")
    instruccion.set(qn("xml:space"), "preserve")
    instruccion.text = f" {nombre} "
    corrida_con(instruccion)

    separador = OxmlElement("w:fldChar")
    separador.set(qn("w:fldCharType"), "separate")
    corrida_con(separador)

    texto = OxmlElement("w:t")
    texto.text = "1"
    corrida_con(texto)

    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    corrida_con(fin)


def propiedades_documento(documento: Document) -> None:
    propiedades = documento.core_properties
    propiedades.title = "Sistema de Gestión de Servicios de Paisajismo, Mantenimiento de Jardines y Control Botánico"
    propiedades.subject = "Proyecto final de Bases de Datos II"
    propiedades.author = "Danna Paulina García Jiménez"
    propiedades.keywords = "MongoDB Atlas, Flask, Aggregation Pipeline, paisajismo, bases de datos"
    propiedades.comments = "Documentación técnica del proyecto final"


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------


def construir_portada(documento: Document, lineas: list[str]) -> None:
    titulo = ""
    subtitulo = ""
    metadatos: list[str] = []
    cita = ""

    for linea in lineas:
        limpia = linea.strip()
        if limpia.startswith("# ") and not titulo:
            titulo = limpia[2:].strip()
        elif limpia.startswith("## ") and not subtitulo:
            subtitulo = limpia[3:].strip()
        elif limpia.startswith(">"):
            cita = limpia[1:].strip()
        elif re.match(r"^\*\*[^*]+:\*\*\s", limpia):
            metadatos.append(limpia)

    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(70)
    parrafo.paragraph_format.space_after = Pt(10)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    corrida = parrafo.add_run("PROYECTO FINAL  ·  BASES DE DATOS II")
    corrida.font.size = Pt(10)
    corrida.font.bold = True
    corrida.font.color.rgb = RGBColor(0x6B, 0x8A, 0x70)
    corrida.font.name = "Calibri"

    parrafo = documento.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(6)
    corrida = parrafo.add_run(titulo)
    corrida.font.size = Pt(25)
    corrida.font.bold = True
    corrida.font.color.rgb = VERDE
    corrida.font.name = "Calibri"

    parrafo = documento.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(24)
    corrida = parrafo.add_run(subtitulo)
    corrida.font.size = Pt(13)
    corrida.font.color.rgb = GRIS_SUAVE
    corrida.font.name = "Calibri"

    linea = documento.add_paragraph()
    linea.alignment = WD_ALIGN_PARAGRAPH.CENTER
    borde_parrafo(linea, "bottom", "1F4D2E", 12)
    linea.paragraph_format.space_after = Pt(26)

    for metadato in metadatos:
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo.paragraph_format.space_after = Pt(4)
        agregar_texto_enlinea(parrafo, metadato, tamano=10.5)
        for corrida in parrafo.runs:
            if corrida.bold:
                corrida.font.color.rgb = VERDE

    if cita:
        parrafo = documento.add_paragraph()
        parrafo.paragraph_format.space_before = Pt(30)
        parrafo.paragraph_format.left_indent = Cm(2.2)
        parrafo.paragraph_format.right_indent = Cm(2.2)
        parrafo.paragraph_format.space_after = Pt(8)
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sombrear(parrafo._p, "F2F6F2")
        agregar_texto_enlinea(parrafo, cita, cursiva=True, tamano=9.5, color=GRIS_SUAVE)

    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(80)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    corrida = parrafo.add_run("Universidad Católica Luis Amigó  ·  Ingeniería de Sistemas  ·  2026")
    corrida.font.size = Pt(8.5)
    corrida.font.color.rgb = GRIS_SUAVE


# ---------------------------------------------------------------------------
# Bloques
# ---------------------------------------------------------------------------


def agregar_imagen(documento: Document, ruta: Path, alt: str, temporal: Path) -> None:
    if not ruta.exists():
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        corrida = parrafo.add_run(f"[Imagen no encontrada: {ruta.name}]")
        corrida.italic = True
        corrida.font.color.rgb = RGBColor(0xB0, 0x30, 0x30)
        return

    with Image.open(ruta) as imagen:
        ancho_px, alto_px = imagen.size

    relacion = alto_px / ancho_px
    partes: list[Path] = []
    if relacion > UMBRAL_DIVISION:
        cantidad = max(2, round(relacion / 1.15))
        alto_parte = alto_px // cantidad
        with Image.open(ruta) as imagen:
            for indice in range(cantidad):
                inicio = indice * alto_parte
                fin = alto_px if indice == cantidad - 1 else (indice + 1) * alto_parte
                recorte = imagen.crop((0, inicio, ancho_px, fin))
                destino = temporal / f"{ruta.stem}_parte{indice + 1}{ruta.suffix}"
                recorte.save(destino, quality=92)
                partes.append(destino)
    else:
        partes.append(ruta)

    for indice, parte in enumerate(partes, start=1):
        parrafo = documento.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        parrafo.paragraph_format.space_before = Pt(6)
        parrafo.paragraph_format.space_after = Pt(2)
        parrafo.paragraph_format.keep_with_next = True
        corrida = parrafo.add_run()
        corrida.add_picture(str(parte), width=Cm(ANCHO_UTIL_CM))
        if len(partes) > 1:
            etiqueta = documento.add_paragraph()
            etiqueta.alignment = WD_ALIGN_PARAGRAPH.CENTER
            etiqueta.paragraph_format.space_after = Pt(2)
            corrida = etiqueta.add_run(f"{alt} — parte {indice} de {len(partes)}")
            corrida.font.size = Pt(8)
            corrida.italic = True
            corrida.font.color.rgb = GRIS_SUAVE


def agregar_tabla(documento: Document, filas: list[list[str]]) -> None:
    if not filas:
        return
    encabezado = filas[0]
    cuerpo = filas[1:]
    columnas = len(encabezado)
    tabla = documento.add_table(rows=1, cols=columnas)
    tabla.style = "Table Grid"
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.autofit = False

    tblPr = tabla._tbl.tblPr
    ancho = tblPr.find(qn("w:tblW"))
    if ancho is None:
        ancho = OxmlElement("w:tblW")
        tblPr.append(ancho)
    ancho.set(qn("w:w"), "4900")
    ancho.set(qn("w:type"), "pct")

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    margenes = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        margen = OxmlElement(f"w:{lado}")
        margen.set(qn("w:w"), "57")
        margen.set(qn("w:type"), "dxa")
        margenes.append(margen)
    tblPr.append(margenes)

    anchos = _calcular_anchos(filas, 16.2)
    for indice, valor in enumerate(anchos):
        tabla.columns[indice].width = Cm(valor)

    fila_encabezado = tabla.rows[0]
    _repetir_encabezado(fila_encabezado)
    for indice, texto in enumerate(encabezado):
        celda = fila_encabezado.cells[indice]
        celda.width = Cm(anchos[indice])
        celda.text = ""
        sombrear(celda._tc, VERDE_ENCABEZADO)
        parrafo = celda.paragraphs[0]
        parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        parrafo.paragraph_format.space_after = Pt(1)
        agregar_texto_enlinea(parrafo, texto, negrita=True, tamano=8.6, color=RGBColor(0xFF, 0xFF, 0xFF))

    for numero, fila in enumerate(cuerpo):
        celdas = tabla.add_row().cells
        _no_dividir_fila(tabla.rows[-1])
        for indice in range(columnas):
            texto = fila[indice] if indice < len(fila) else ""
            celda = celdas[indice]
            celda.width = Cm(anchos[indice])
            celda.text = ""
            if numero % 2 == 1:
                sombrear(celda._tc, VERDE_CLARO)
            parrafo = celda.paragraphs[0]
            parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
            parrafo.paragraph_format.space_after = Pt(1)
            parrafo.paragraph_format.line_spacing = 1.0
            agregar_texto_enlinea(parrafo, texto, tamano=8.6)

    documento.add_paragraph().paragraph_format.space_after = Pt(2)


def _calcular_anchos(filas: list[list[str]], total_cm: float) -> list[float]:
    """Distribuye el ancho de las columnas según el contenido esperado."""
    columnas = len(filas[0])
    pesos: list[float] = []
    for indice in range(columnas):
        textos = [fila[indice] for fila in filas if indice < len(fila)]
        largo_cuerpo = max((len(t) for t in textos[1:]), default=0)
        largo_encabezado = len(textos[0]) if textos else 0
        peso = max(8.0, largo_cuerpo, largo_encabezado * 1.15)
        pesos.append(min(peso, 70.0))

    suma = sum(pesos)
    minimo = min(1.55, total_cm / max(columnas, 1))
    disponible = max(0.0, total_cm - minimo * columnas)
    anchos = [minimo + disponible * peso / suma for peso in pesos]
    return anchos


def _repetir_encabezado(fila) -> None:
    trPr = fila._tr.get_or_add_trPr()
    trPr.append(parse_xml(rf'<w:tblHeader {nsdecls("w")} w:val="true"/>'))


def _no_dividir_fila(fila) -> None:
    trPr = fila._tr.get_or_add_trPr()
    trPr.append(parse_xml(rf'<w:cantSplit {nsdecls("w")} w:val="true"/>'))


def agregar_codigo(documento: Document, lineas: list[str]) -> None:
    if not lineas:
        lineas = [""]
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(6)
    parrafo.paragraph_format.space_after = Pt(8)
    parrafo.paragraph_format.line_spacing = 1.0
    parrafo.paragraph_format.left_indent = Cm(0.25)
    parrafo.paragraph_format.right_indent = Cm(0.15)
    parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sombrear(parrafo._p, FONDO_CODIGO)
    borde_parrafo(parrafo, "left", "8FAE94", 18)
    for indice, linea in enumerate(lineas):
        corrida = parrafo.add_run(linea)
        corrida.font.name = "Consolas"
        corrida.font.size = Pt(8)
        corrida.font.color.rgb = RGBColor(0x2E, 0x33, 0x2F)
        if indice < len(lineas) - 1:
            corrida.add_break()


def agregar_cita(documento: Document, texto: str) -> None:
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.left_indent = Cm(0.6)
    parrafo.paragraph_format.right_indent = Cm(0.4)
    parrafo.paragraph_format.space_before = Pt(6)
    parrafo.paragraph_format.space_after = Pt(8)
    sombrear(parrafo._p, "F2F6F2")
    borde_parrafo(parrafo, "left", "1F4D2E", 18)
    agregar_texto_enlinea(parrafo, texto, cursiva=True, tamano=9.8, color=GRIS_SUAVE)


def agregar_caption(documento: Document, texto: str) -> None:
    parrafo = documento.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(10)
    agregar_texto_enlinea(parrafo, texto.strip("*"), cursiva=True, tamano=8.8, color=GRIS_SUAVE)


def agregar_lista(documento: Document, texto: str, nivel: int, marcador: str) -> None:
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.left_indent = Cm(0.65 + nivel * 0.55)
    parrafo.paragraph_format.first_line_indent = Cm(-0.45)
    parrafo.paragraph_format.space_after = Pt(3)
    parrafo.paragraph_format.line_spacing = 1.1
    parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    corrida = parrafo.add_run(f"{marcador}  ")
    corrida.font.color.rgb = VERDE
    corrida.bold = True
    agregar_texto_enlinea(parrafo, texto)


def agregar_regla(documento: Document) -> None:
    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_before = Pt(4)
    parrafo.paragraph_format.space_after = Pt(10)
    borde_parrafo(parrafo, "bottom", "C9D6CB", 6)


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------


def es_separador_tabla(linea: str) -> bool:
    celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
    return bool(celdas) and all(re.fullmatch(r":?-{3,}:?", c) for c in celdas)


def dividir_fila(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def convertir_markdown(documento: Document, lineas: list[str], temporal: Path) -> None:
    indice = 0
    pendiente: list[str] = []

    def vaciar_pendiente() -> None:
        if not pendiente:
            return
        texto = " ".join(p.strip() for p in pendiente).strip()
        pendiente.clear()
        if not texto:
            return
        parrafo = documento.add_paragraph()
        agregar_texto_enlinea(parrafo, texto)

    while indice < len(lineas):
        linea = lineas[indice]
        limpia = linea.strip()

        if not limpia:
            vaciar_pendiente()
            indice += 1
            continue

        if limpia.startswith("```"):
            vaciar_pendiente()
            indice += 1
            codigo: list[str] = []
            while indice < len(lineas) and not lineas[indice].strip().startswith("```"):
                codigo.append(lineas[indice].rstrip())
                indice += 1
            indice += 1
            agregar_codigo(documento, codigo)
            continue

        if limpia.startswith("|") and indice + 1 < len(lineas) and es_separador_tabla(lineas[indice + 1]):
            vaciar_pendiente()
            filas = [dividir_fila(limpia)]
            indice += 2
            while indice < len(lineas) and lineas[indice].strip().startswith("|"):
                filas.append(dividir_fila(lineas[indice]))
                indice += 1
            agregar_tabla(documento, filas)
            continue

        imagen = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", limpia)
        if imagen:
            vaciar_pendiente()
            alt, ruta_relativa = imagen.group(1), imagen.group(2)
            agregar_imagen(documento, DOCS / ruta_relativa, alt, temporal)
            indice += 1
            continue

        if limpia.startswith("# "):
            vaciar_pendiente()
            documento.add_heading(limpia[2:].strip(), level=1)
            indice += 1
            continue

        if limpia.startswith("## "):
            vaciar_pendiente()
            documento.add_heading(limpia[3:].strip(), level=2)
            indice += 1
            continue

        if limpia.startswith("### "):
            vaciar_pendiente()
            documento.add_heading(limpia[4:].strip(), level=3)
            indice += 1
            continue

        if limpia.startswith(">"):
            vaciar_pendiente()
            agregar_cita(documento, limpia[1:].strip())
            indice += 1
            continue

        if re.fullmatch(r"-{3,}", limpia):
            vaciar_pendiente()
            agregar_regla(documento)
            indice += 1
            continue

        if re.match(r"^(\*[^*].*\*)$", limpia) and limpia.lower().startswith(("*figura", "*tabla")):
            vaciar_pendiente()
            agregar_caption(documento, limpia)
            indice += 1
            continue

        casilla = re.match(r"^[-*]\s+\[([ xX])\]\s+(.+)$", limpia)
        if casilla:
            vaciar_pendiente()
            marcador = "☑" if casilla.group(1).lower() == "x" else "☐"
            agregar_lista(documento, casilla.group(2), 0, marcador)
            indice += 1
            continue

        vineta = re.match(r"^(\s*)[-*]\s+(.+)$", linea)
        if vineta:
            vaciar_pendiente()
            nivel = len(vineta.group(1).replace("\t", "  ")) // 2
            agregar_lista(documento, vineta.group(2), nivel, "•")
            indice += 1
            continue

        numerada = re.match(r"^(\s*)(\d+)\.\s+(.+)$", linea)
        if numerada:
            vaciar_pendiente()
            nivel = len(numerada.group(1).replace("\t", "  ")) // 2
            agregar_lista(documento, numerada.group(3), nivel, f"{numerada.group(2)}.")
            indice += 1
            continue

        pendiente.append(linea)
        indice += 1

    vaciar_pendiente()


def main() -> None:
    if not ORIGEN.exists():
        raise SystemExit(f"No se encontró el documento de origen: {ORIGEN}")

    lineas = ORIGEN.read_text(encoding="utf-8").splitlines()

    try:
        corte = next(i for i, l in enumerate(lineas) if l.strip() == "# Contenido")
    except StopIteration as error:
        raise SystemExit("No se encontró el encabezado '# Contenido'.") from error

    documento = Document()
    propiedades_documento(documento)
    configurar_estilos(documento)
    configurar_pagina(documento)
    construir_portada(documento, lineas[:corte])

    # Tabla de entrega y resumen ejecutivo en una página aparte.
    inicio_resumen = next(
        (i for i, l in enumerate(lineas[:corte]) if l.strip().startswith("| Elemento de entrega")),
        corte,
    )
    documento.add_page_break()
    documento.add_heading("Resumen de la entrega", level=1)
    documento.paragraphs[-1].paragraph_format.page_break_before = False

    with tempfile.TemporaryDirectory(prefix="docx_imagenes_") as carpeta:
        convertir_markdown(documento, lineas[inicio_resumen:corte], Path(carpeta))
        convertir_markdown(documento, lineas[corte:], Path(carpeta))
        documento.save(DESTINO)

    print(f"Documento generado: {DESTINO}")


if __name__ == "__main__":
    main()
