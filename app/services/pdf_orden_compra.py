from io import BytesIO
from annotated_types import doc
from pymupdf import Story
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
import os
from reportlab.platypus import Image
from reportlab.pdfgen import canvas
from datetime import datetime

def P(texto, style):
    return Paragraph(str(texto or ""), style)


def money(valor):
    try:
        return f"{float(valor):,.2f}"
    except:
        return "0.00"


def generar_pdf_orden_compra(orden, productos):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8,
        leading=9,
        alignment=0
    )

    normal_center = ParagraphStyle(
        "normal_center",
        parent=normal,
        alignment=1
    )

    bold = ParagraphStyle(
        "bold",
        parent=normal,
        fontName="Times-Bold"
    )

    bold_center = ParagraphStyle(
        "bold_center",
        parent=bold,
        alignment=1
    )

    title = ParagraphStyle(
        "title",
        parent=bold_center,
        fontSize=14,
        leading=16
    )

    story = []

    # Como orden viene en tupla SELECT *
    # Índices según tu INSERT:
    # id, numero_oc, fecha, area_requirente, cert_presupuestaria,
    # objeto, proveedor, ruc, telefono, direccion, correo,
    # proforma_num, proforma_fecha, contacto, vigencia,
    # forma_pago, plazo_ejecucion, lugar_entrega,
    # administrador_orden, subtotal, iva, total, observaciones, tarea_id

    numero_oc = orden[1]
    fecha = orden[2]
    area = orden[3]
    cert = orden[4]
    objeto = orden[5]
    proveedor = orden[6]
    ruc = orden[7]
    telefono = orden[8]
    direccion = orden[9]
    correo = orden[10]
    proforma = orden[11]
    proforma_fecha = orden[12]
    contacto = orden[13]
    vigencia = orden[14]
    forma_pago = orden[15]
    plazo = orden[16]
    lugar = orden[17]
    administrador = orden[18]
    maxima_autoridad = orden[27]
    cargo_maxima_autoridad = orden[28]
    subtotal = 0

    for p in productos:
        try:
            subtotal += float(p[3] or 0) * float(p[4] or 0)
        except:
            pass

    iva = subtotal * 0.12
    total = subtotal + iva

    logo_path = os.path.join("app", "static", "logo.png")

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*cm, height=2*cm)
    else:
        logo = ""

    encabezado_inst = Table([
        [
            logo,
            P(
                "UNIVERSIDAD TÉCNICA DE MACHALA<br/>"
                "DIRECCIÓN ADMINISTRATIVA<br/><br/>"
                "ORDEN DE COMPRA<br/>"
                "ÍNFIMA CUANTÍA",
                title
            )
        ]
    ], colWidths=[3*cm, 15*cm])

    encabezado_inst.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
    ]))

    story.append(encabezado_inst)
    story.append(Spacer(1, 0.3*cm))
    encabezado = Table([
        [
            P("No. DE ORDEN DE COMPRA: SERVICIO / BIEN / OBRA", bold_center),
            P(f"IC – ENTIDAD CONTRATANTE<br/>{numero_oc}", bold_center)
        ]
    ], colWidths=[13.5 * cm, 4.5 * cm])

    encabezado.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(encabezado)

    datos = [
        [P(f"<b>FECHA:</b> {fecha}", normal)],
        [P(f"<b>ÁREA REQUIRENTE:</b> {area}", normal)],
        [P(f"<b>NÚMERO DE CERTIFICACIÓN PRESUPUESTARIA:</b> {cert}", normal)],
        [P(
            f"<b>OBJETO DE CONTRATACIÓN:</b> El Contratista se obliga con la "
            f"UNIVERSIDAD TÉCNICA DE MACHALA a proveer los bienes/servicios requeridos "
            f"a entera satisfacción de la contratante, conforme el siguiente detalle: "
            f"{objeto}",
            normal
        )],
    ]

    tabla_datos = Table(datos, colWidths=[18 * cm])
    tabla_datos.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(tabla_datos)

    proveedor_tbl = Table([
        [
            P(f"<b>PROVEEDOR:</b> {proveedor}<br/>"
              f"<b>RUC:</b> {ruc}<br/>"
              f"<b>TELÉFONO:</b> {telefono}<br/>"
              f"<b>DIRECCIÓN:</b> {direccion}<br/>"
              f"<b>CORREO:</b> {correo}", normal),
            P(f"<b>PROFORMA Nro.:</b> {proforma}<br/>"
              f"<b>FECHA:</b> {proforma_fecha}<br/>"
              f"<b>CONTACTO:</b> {contacto}<br/>"
              f"<b>VIGENCIA:</b> {vigencia}", normal),
        ]
    ], colWidths=[9 * cm, 9 * cm])

    proveedor_tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(proveedor_tbl)

    items = [[
        P("ITEM", bold_center),
        P("CPC", bold_center),
        P("DESCRIPCIÓN", bold_center),
        P("UNIDAD DE MEDIDA", bold_center),
        P("CANTIDAD", bold_center),
        P("V. UNITARIO", bold_center),
        P("V. TOTAL", bold_center),
    ]]

    contador = 1
    for p in productos:
        descripcion = p[1]
        unidad = p[2]
        cantidad = p[3]
        valor_uni = p[4]
        valor_total = p[5]
        cpc = p[6] 

        items.append([
            P(contador, normal_center),
            P(cpc, normal_center),
            #P("", normal_center),
            P(descripcion, normal),
            P(unidad, normal_center),
            P(cantidad, normal_center),
            P(money(valor_uni), normal_center),
            P(money(valor_total), normal_center),
        ])
        contador += 1

  
    items.append(["", "", "", "", "", P("SUBTOTAL", bold), P("$ " + money(subtotal), normal)])
    items.append(["", "", "", "", "", P("IVA 12%", bold), P("$ " + money(iva), normal)])
    items.append(["", "", "", "", "", P("TOTAL", bold), P("$ " + money(total), normal)])

    tabla_items = Table(
        items,
        colWidths=[1*cm, 1.8*cm, 6.4*cm, 2*cm, 2*cm, 2.4*cm, 2.4*cm],
        repeatRows=1
    )

    tabla_items.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (0, -3), (4, -3)),
        ("SPAN", (0, -2), (4, -2)),
        ("SPAN", (0, -1), (4, -1)),
    ]))
    story.append(tabla_items)

    notas = P(
        "<b>Notas:</b><br/>"
        "- Según la naturaleza de la contratación, en caso de requerirse, se puede incluir otras particularidades, "
        "para la correcta ejecución de la orden de compra.<br/>"
        "- Para el caso de obras se deberá anexar los Análisis de Precios Unitarios (APU´s).<br/>"
        "- Lo no contemplado en la presente orden de compra, se estará a las disposiciones de la Ley Orgánica "
        "del Sistema Nacional de Contratación Pública, su Reglamento General de aplicación, y demás normativa "
        "secundaria emitida para el efecto por parte del SERCOP.",
        normal
    )

    story.append(notas)

    bloques = [
        [
            P("ADMINISTRADOR DE LA ORDEN<br/>COMPRA", bold),
            P(
                f"La administración de la orden de compra, estará a cargo de "
                f"<b>{administrador}</b>, quien velará por el cabal y oportuno cumplimiento "
                f"de todas y cada una de las obligaciones derivadas de la Orden de Compra "
                f"y verificará que los bienes adquiridos/servicios contratados/obras ejecutadas, "
                f"cumplan con las especificaciones técnicas/términos de referencia establecidas "
                f"en el objeto contractual.<br/><br/>"
                f"La máxima autoridad o su delegado, podrá cambiar de administrador de la orden "
                f"de compra, en cualquier momento durante la ejecución del referido instrumento, "
                f"para lo cual bastará únicamente la notificación al contratista.",
                normal
            )
        ],
        [
            P("FORMA DE PAGO:", bold),
            P(
                f"La UNIVERSIDAD TÉCNICA DE MACHALA pagará la orden de compra para "
                f"“<b>{objeto}</b>”, una vez que se hayan ejecutado y cumplido con todos "
                f"los componentes de los bienes/servicios/obras, conforme con el siguiente detalle:<br/><br/>"
                f"{forma_pago}",
                normal
            )
        ],
        [
            P("PLAZO DE EJECUCIÓN:", bold),
            P(
                f"El plazo para la ejecución de la orden de compra será de <b>{plazo}</b>, "
                f"contados a partir de la fecha de suscripción de la orden de compra.",
                normal
            )
        ],
        [
            P("OBLIGACIONES DEL CONTRATISTA", bold),
            P("Dar cumplimiento cabal a lo establecido en los Términos de Referencia y/o Especificaciones Técnicas.", normal)
        ],
        [
            P("MULTAS:", bold),
            P(
                "Se aplicará la multa, en ningún caso inferior al 1x1000, por cada día de retardo "
                "en la ejecución de las obligaciones contractuales. Las multas se calcularán sobre "
                "el porcentaje de las obligaciones que se encuentren pendientes de ejecutarse.",
                normal
            )
        ],
        [
            P("GARANTÍA:", bold),
            P(
                "De ser el caso, en esta orden de compra se rendirá la garantía técnica, de conformidad "
                "con lo establecido en la Ley Orgánica del Sistema Nacional de Contratación Pública "
                "y su Reglamento General de aplicación.",
                normal
            )
        ],
        [
            P("LUGAR DE ENTREGA:", bold),
            P(
                f"El lugar designado para la entrega es <b>{lugar}</b>, según las especificaciones técnicas "
                f"y/o términos de referencia, que se agregan y forman parte integrante de esta orden de compra.",
                normal
            )
        ],
        [
            P("RECEPCIÓN:", bold),
            P(
                "La recepción de los bienes adquiridos/servicios contratados/obras ejecutadas se realizará "
                "conforme lo dispuesto en el artículo 321 del Reglamento General a la Ley Orgánica "
                "del Sistema Nacional de Contratación Pública.",
                normal
            )
        ],
        [
            P("COMUNICACIONES ENTRE LAS PARTES:", bold),
            P(
                "Todas las comunicaciones entre las partes, relativas al objeto de esta contratación, "
                "sin excepción, serán formuladas por escrito y en idioma castellano. Las comunicaciones "
                "también podrán efectuarse a través de medios electrónicos.",
                normal
            )
        ],
        [
            P("DOCUMENTOS HABILITANTES:", bold),
            P(
                "- Términos de referencia y/o especificaciones técnicas de la contratante.<br/>"
                "- La garantía técnica presentada por el contratista, de ser el caso.<br/>"
                "- Certificación presupuestaria.<br/>"
                "- Proforma.",
                normal
            )
        ],
        [
            P("ACEPTACIÓN:", bold),
            P(
                f"{proveedor}, con RUC {ruc}, certifica e informa que el bien/servicio/obra cumplirá "
                f"con las especificaciones descritas en la proforma aceptada por la contratante, la misma "
                f"que forma parte integrante de esta orden de compra y garantiza su calidad.",
                normal
            )
        ],
        [
            P("BASE LEGAL", bold),
            P(
                "El artículo 52.1 de la Ley Orgánica del Sistema Nacional de Contratación Pública prevé "
                "la contratación bajo el procedimiento de ínfima cuantía, conforme los casos y condiciones "
                "establecidos en dicha norma. El artículo 71 de la LOSNCP regula la imposición de multas "
                "por retardo en la ejecución de las obligaciones contractuales.",
                normal
            )
        ],
    ]

    tabla_bloques = Table(bloques, colWidths=[5.2 * cm, 12.8 * cm])
    tabla_bloques.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(tabla_bloques)

    story.append(Spacer(1, 1 * cm))

    firmas = Table([
        [
            P("MÁXIMA AUTORIDAD O SU DELEGADO", bold_center),
            P("CONTRATISTA", bold_center)
        ],
        [
            "",
            ""
        ],
        [
            P(
                f"{maxima_autoridad or 'NOMBRE COMPLETO'}<br/>"
                f"{cargo_maxima_autoridad or 'CARGO'}",
                bold_center
            ),
            P(f"{proveedor}<br/>RUC: {ruc}", bold_center)
        ]
    ],
    colWidths=[9 * cm, 9 * cm],
    rowHeights=[1 * cm, 3.5 * cm, 1 * cm]
    )

    firmas.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(firmas)

    def pie_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 7)
        canvas.drawString(1.2 * cm, 0.8 * cm, "Universidad Técnica de Machala - Sistema SICOP")
        canvas.drawRightString(19.8 * cm, 0.8 * cm, f"Página {doc.page}")
        canvas.drawCentredString(10.5 * cm, 0.8 * cm, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=pie_pagina,
        onLaterPages=pie_pagina
    )

    buffer.seek(0)
    return buffer