import os

from io import BytesIO
from flask import current_app, send_file

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether
)
# ==========================================
# PDF CERTIFICACIÓN PAC
# ==========================================
def crear_estilos_certificacion():

    styles = getSampleStyleSheet()

    estilo_institucion = ParagraphStyle(
        "InstitucionCertificacion",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER
    )

    estilo_titulo = ParagraphStyle(
        "TituloCertificacion",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    estilo_normal = ParagraphStyle(
        "NormalCertificacion",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        alignment=TA_JUSTIFY
    )

    estilo_celda = ParagraphStyle(
        "CeldaCertificacion",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12
    )

    estilo_celda_bold = ParagraphStyle(
        "CeldaBoldCertificacion",
        parent=estilo_celda,
        fontName="Helvetica-Bold"
    )

    estilo_firma = ParagraphStyle(
        "FirmaCertificacion",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER
    )

    return {
        "institucion": estilo_institucion,
        "titulo": estilo_titulo,
        "normal": estilo_normal,
        "celda": estilo_celda,
        "celda_bold": estilo_celda_bold,
        "firma": estilo_firma
    }



# ==========================================
# PDF CERTIFICACIÓN CATE
# ==========================================
def generar_pdf_cate(datos, capturas):

    fecha_certificacion = datos[1]
    codigo_proceso = datos[2]
    objeto_contratacion = datos[3]
    tipo_proceso = datos[4] or ""
    analista = datos[5]
    jefe_compras = datos[6]
    consta_catalogo = bool(datos[7])

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Certificación de Verificación de Catálogo Electrónico"
    )

    estilos = crear_estilos_certificacion()

    estilo_institucion = estilos["institucion"]
    estilo_titulo = estilos["titulo"]
    estilo_normal = estilos["normal"]
    estilo_celda = estilos["celda"]
    estilo_celda_bold = estilos["celda_bold"]
    estilo_firma = estilos["firma"]

    elementos = []

    # ==========================
    # ENCABEZADO CON LOGO
    # ==========================
    logo_path = os.path.join(
        current_app.root_path,
        "static",
        "logo.png"
    )

    if os.path.exists(logo_path):
        logo = RLImage(
            logo_path,
            width=1.8 * cm,
            height=1.8 * cm
        )
    else:
        logo = Paragraph("", estilo_normal)

    encabezado_texto = Paragraph(
        """
        UNIVERSIDAD TÉCNICA DE MACHALA<br/>
        UNIDAD DE COMPRAS PÚBLICAS
        """,
        estilo_institucion
    )

    tabla_encabezado = Table(
        [[logo, encabezado_texto, ""]],
        colWidths=[3 * cm, 11.5 * cm, 3 * cm]
    )

    tabla_encabezado.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabla_encabezado)
    elementos.append(Spacer(1, 8))

    elementos.append(
        Paragraph(
            """
            CERTIFICACIÓN DE VERIFICACIÓN<br/>
            DE CATÁLOGO ELECTRÓNICO
            """,
            estilo_titulo
        )
    )

    # ==========================
    # DATOS DEL PROCESO
    # ==========================
    fecha_texto = (
        fecha_certificacion.strftime("%d/%m/%Y")
        if fecha_certificacion
        else ""
    )

    datos_proceso = [
        [
            Paragraph("Fecha:", estilo_celda_bold),
            Paragraph(fecha_texto, estilo_celda),
        ],
        [
            Paragraph("Código del proceso:", estilo_celda_bold),
            Paragraph(str(codigo_proceso or ""), estilo_celda),
        ],
        [
            Paragraph("Tipo de proceso:", estilo_celda_bold),
            Paragraph(str(tipo_proceso or ""), estilo_celda),
        ],
        [
            Paragraph("Objeto de contratación:", estilo_celda_bold),
            Paragraph(str(objeto_contratacion or ""), estilo_celda),
        ],
    ]

    tabla_datos = Table(
        datos_proceso,
        colWidths=[4.2 * cm, 12.8 * cm]
    )

    tabla_datos.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf2f8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 14))

    # ==========================
    # BASE LEGAL
    # ==========================
    elementos.append(
        Paragraph("<b>BASE LEGAL</b>", estilo_titulo)
    )

    texto_articulo = """
    <b>Art. 46.- Obligaciones de las entidades contratantes.-</b>
    Las entidades contratantes deberán consultar el
    Catálogo Electrónico y sus distintas modalidades, previamente a establecer procedimientos de
    adquisición de bienes y servicios. Solo en caso de que el bien o servicio requerido no se encuentre
    catalogado se podrá realizar otros procedimientos precontractuales para la adquisición de bienes o
    servicios, de conformidad con la presente Ley y su Reglamento.                                     

    <b>Art. 66.- Certificaciones PAC y Verificación Catálogo Electrónico.-</b>
    La entidad contratante elaborará e incluirá en cada proceso de contratación
    la respectiva certificación, a excepción de los procedimientos que no estén
    obligados a su publicación en el PAC, en la que se hará constar que la
    contratación se encuentra debidamente planificada y publicada en el Portal
    de Contratación Pública. La certificación de que la contratación no se
    encuentra en el Catálogo Electrónico aplicará exclusivamente para cuando
    se trate de contratación de bienes o servicios.
    """

    elementos.append(
        Paragraph(texto_articulo, estilo_normal)
    )

    elementos.append(Spacer(1, 14))

    # ==========================
    # TEXTO DE CERTIFICACIÓN
    # ==========================
    elementos.append(
        Paragraph("<b>CERTIFICACIÓN</b>", estilo_titulo)
    )

    if consta_catalogo:

        texto_certificacion = f"""
        Una vez realizada la verificación correspondiente en el Portal de
        Contratación Pública, respecto del objeto:
        <b>{objeto_contratacion or ""}</b>, se certifica que los bienes o servicios
        requeridos <b>SÍ SE ENCUENTRAN disponibles en el Catálogo Electrónico</b>,
        conforme se demuestra en la captura de respaldo incorporada al presente
        documento.
        """

    else:

        texto_certificacion = f"""
        Una vez realizada la verificación correspondiente en el Portal de
        Contratación Pública, respecto del objeto:
        <b>{objeto_contratacion or ""}</b>, se certifica que los bienes o servicios
        requeridos <b>NO SE ENCUENTRAN disponibles en el Catálogo Electrónico</b>,
        conforme se demuestra en la captura de respaldo incorporada al presente
        documento.
        """

    elementos.append(
        Paragraph(texto_certificacion, estilo_normal)
    )

    elementos.append(Spacer(1, 14))

    # ==========================
    # CAPTURAS GUARDADAS EN BD
    # ==========================
    if capturas:

        for numero, captura_bd in enumerate(capturas, start=1):

            elementos.append(
                Paragraph(
                    f"<b>CAPTURA DE VERIFICACIÓN N.º {numero}</b>",
                    estilo_titulo
                )
            )

            try:
                imagen_bytes = captura_bd[3]
                imagen_buffer = BytesIO(bytes(imagen_bytes))

                lector = ImageReader(imagen_buffer)
                ancho_original, alto_original = lector.getSize()

                ancho_maximo = 13.5 * cm
                alto_maximo = 8 * cm

                escala = min(
                    ancho_maximo / ancho_original,
                    alto_maximo / alto_original
                )

                ancho_final = ancho_original * escala
                alto_final = alto_original * escala

                imagen_buffer.seek(0)

                captura = RLImage(
                    imagen_buffer,
                    width=ancho_final,
                    height=alto_final
                )

                tabla_imagen = Table(
                    [[captura]],
                    colWidths=[17 * cm]
                )

                tabla_imagen.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.grey),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))

                elementos.append(tabla_imagen)
                elementos.append(Spacer(1, 14))

            except Exception as e:
                print(
                    f"🔥 ERROR AL CARGAR CAPTURA CATE {numero}:",
                    e
                )

                elementos.append(
                    Paragraph(
                        f"No fue posible incorporar la captura N.º {numero}.",
                        estilo_normal
                    )
                )

    else:
        elementos.append(
            Paragraph(
                "No existen capturas de respaldo registradas.",
                estilo_normal
            )
        )

    # ==========================
    # RESPONSABLES Y FIRMAS
    # OPCIÓN A:
    # EL ANALISTA ELABORA Y VERIFICA
    # EL JEFE CERTIFICA Y FIRMA
    # ==========================
    firma_analista = Paragraph(
        f"""
        <b>ELABORADO Y VERIFICADO POR:</b><br/><br/><br/>
        ___________________________________<br/>
        <b>{analista or ""}</b><br/>
        Analista de Compras Públicas
        """,
        estilo_firma
    )

    firma_jefe = Paragraph(
        f"""
        <b>CERTIFICADO POR:</b><br/><br/><br/>
        ___________________________________<br/>
        <b>{jefe_compras or ""}</b><br/>
        Jefe de Compras Públicas
        """,
        estilo_firma
    )

    tabla_firmas = Table(
        [[firma_analista, firma_jefe]],
        colWidths=[8.5 * cm, 8.5 * cm]
    )

    tabla_firmas.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(
        KeepTogether([tabla_firmas])
    )

    doc.build(elementos)

    buffer.seek(0)

    nombre_pdf = (
        f"certificacion_cate_{codigo_proceso or certificacion_id}.pdf"
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )

    return send_file(
        buffer,
        as_attachment=False,
        download_name=nombre_pdf,
        mimetype="application/pdf"
    )
# ==========================================
# PDF CERTIFICACIÓN PAC
# ==========================================

def generar_pdf_pac(datos, capturas):
    fecha_certificacion = datos[1]
    codigo_proceso = datos[2]
    objeto_contratacion = datos[3]
    tipo_proceso = datos[4] or ""
    analista = datos[5]
    jefe_compras = datos[6]
    consta_pac = bool(datos[7])

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Certificación del Plan Anual de Contratación - PAC"
    )

    estilos = crear_estilos_certificacion()

    estilo_institucion = estilos["institucion"]
    estilo_titulo = estilos["titulo"]
    estilo_normal = estilos["normal"]
    estilo_celda = estilos["celda"]
    estilo_celda_bold = estilos["celda_bold"]
    estilo_firma = estilos["firma"]

    elementos = []

    # ==========================
    # ENCABEZADO CON LOGO
    # ==========================
    logo_path = os.path.join(
        current_app.root_path,
        "static",
        "logo.png"
    )

    if os.path.exists(logo_path):
        logo = RLImage(
            logo_path,
            width=1.8 * cm,
            height=1.8 * cm
        )
    else:
        logo = Paragraph("", estilo_normal)

    encabezado_texto = Paragraph(
        """
        UNIVERSIDAD TÉCNICA DE MACHALA<br/>
        UNIDAD DE COMPRAS PÚBLICAS
        """,
        estilo_institucion
    )

    tabla_encabezado = Table(
        [[logo, encabezado_texto, ""]],
        colWidths=[3 * cm, 11.5 * cm, 3 * cm]
    )

    tabla_encabezado.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabla_encabezado)
    elementos.append(Spacer(1, 8))

    elementos.append(
        Paragraph(
            """
            CERTIFICACIÓN DE VERIFICACIÓN<br/>
            DEL PLAN ANUAL DE CONTRATACIÓN (PAC)
            """,
            estilo_titulo
        )
    )

    # ==========================
    # DATOS DEL PROCESO
    # ==========================
    fecha_texto = (
        fecha_certificacion.strftime("%d/%m/%Y")
        if fecha_certificacion
        else ""
    )

    datos_proceso = [
        [
            Paragraph("Fecha:", estilo_celda_bold),
            Paragraph(fecha_texto, estilo_celda),
        ],
        [
            Paragraph("Código del proceso:", estilo_celda_bold),
            Paragraph(str(codigo_proceso or ""), estilo_celda),
        ],
        [
            Paragraph("Tipo de proceso:", estilo_celda_bold),
            Paragraph(str(tipo_proceso or ""), estilo_celda),
        ],
        [
            Paragraph("Objeto de contratación:", estilo_celda_bold),
            Paragraph(str(objeto_contratacion or ""), estilo_celda),
        ],
    ]

    tabla_datos = Table(
        datos_proceso,
        colWidths=[4.2 * cm, 12.8 * cm]
    )

    tabla_datos.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf2f8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 14))

    # ==========================
    # BASE LEGAL
    # ==========================
    elementos.append(
        Paragraph("<b>BASE LEGAL</b>", estilo_titulo)
    )

    texto_articulo = """
    <b>Art. 66.- Certificaciones PAC y Verificación Catálogo Electrónico.-</b>
    La entidad contratante elaborará e incluirá en cada proceso de contratación
    la respectiva certificación, a excepción de los procedimientos que no estén
    obligados a su publicación en el PAC, en la que se hará constar que la
    contratación se encuentra debidamente planificada y publicada en el Portal
    de Contratación Pública.                                
    """

    elementos.append(
        Paragraph(texto_articulo, estilo_normal)
    )

    elementos.append(Spacer(1, 14))

    # ==========================
    # TEXTO DE CERTIFICACIÓN
    # ==========================
    elementos.append(
        Paragraph("<b>CERTIFICACIÓN</b>", estilo_titulo)
    )

    if consta_pac:

        texto_certificacion = f"""
        Una vez realizada la verificación correspondiente del Plan Anual de Contratación (PAC), se certifica que la contratación correspondiente al objeto:
        <b>{objeto_contratacion or ""}</b>,
        <b>SÍ SE ENCUENTRA debidamente planificada y publicada en el
        Plan Anual de Contratación - PAC</b>, conforme se demuestra en
        las capturas de respaldo incorporadas al presente documento.
        """

    else:

        texto_certificacion = f"""
        Una vez realizada la verificación correspondiente del Plan Anual de Contratación (PAC), se certifica que la contratación correspondiente al objeto:
        <b>{objeto_contratacion or ""}</b>,
        <b>NO SE ENCUENTRA registrada en el Plan Anual de Contratación - PAC</b>,
        conforme se demuestra en las capturas de respaldo incorporadas
        al presente documento.
        """

    elementos.append(
        Paragraph(texto_certificacion, estilo_normal)
    )

    elementos.append(Spacer(1, 14))

    # ==========================
    # CAPTURA DE VERIFICACIÓN DEL PAC
    # ==========================
    if capturas:

        for numero, captura_bd in enumerate(capturas, start=1):

            elementos.append(
                Paragraph(
                    f"<b>CAPTURA DE VERIFICACIÓN PAC N.º {numero}</b>",
                    estilo_titulo
                )
            )

            try:
                imagen_bytes = captura_bd[3]
                imagen_buffer = BytesIO(bytes(imagen_bytes))

                lector = ImageReader(imagen_buffer)
                ancho_original, alto_original = lector.getSize()

                ancho_maximo = 13.5 * cm
                alto_maximo = 8 * cm

                escala = min(
                    ancho_maximo / ancho_original,
                    alto_maximo / alto_original
                )

                ancho_final = ancho_original * escala
                alto_final = alto_original * escala

                imagen_buffer.seek(0)

                captura = RLImage(
                    imagen_buffer,
                    width=ancho_final,
                    height=alto_final
                )

                tabla_imagen = Table(
                    [[captura]],
                    colWidths=[17 * cm]
                )

                tabla_imagen.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.grey),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))

                elementos.append(tabla_imagen)
                elementos.append(Spacer(1, 14))

            except Exception as e:
                print(
                    f"🔥 ERROR AL CARGAR CAPTURA CATE {numero}:",
                    e
                )

                elementos.append(
                    Paragraph(
                        f"No fue posible incorporar la captura N.º {numero}.",
                        estilo_normal
                    )
                )

    else:
        elementos.append(
            Paragraph(
                "No existen capturas de respaldo registradas.",
                estilo_normal
            )
        )

    # ==========================
    # RESPONSABLES Y FIRMAS
    # OPCIÓN A:
    # EL ANALISTA ELABORA Y VERIFICA
    # EL JEFE CERTIFICA Y FIRMA
    # ==========================
    firma_analista = Paragraph(
        f"""
        <b>ELABORADO Y VERIFICADO POR:</b><br/><br/><br/>
        ___________________________________<br/>
        <b>{analista or ""}</b><br/>
        Analista de Compras Públicas
        """,
        estilo_firma
    )

    firma_jefe = Paragraph(
        f"""
        <b>CERTIFICADO POR:</b><br/><br/><br/>
        ___________________________________<br/>
        <b>{jefe_compras or ""}</b><br/>
        Jefe de Compras Públicas
        """,
        estilo_firma
    )

    tabla_firmas = Table(
        [[firma_analista, firma_jefe]],
        colWidths=[8.5 * cm, 8.5 * cm]
    )

    tabla_firmas.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(
        KeepTogether([tabla_firmas])
    )

    doc.build(elementos)

    buffer.seek(0)

    nombre_pdf = (
        f"certificacion_pac_{codigo_proceso or datos[0]}.pdf"
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )

    return send_file(
        buffer,
        as_attachment=False,
        download_name=nombre_pdf,
        mimetype="application/pdf"
    )
