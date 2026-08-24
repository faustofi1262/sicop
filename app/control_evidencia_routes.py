from io import BytesIO

from flask import send_file

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)
from flask import Blueprint, render_template
from flask import jsonify
from app.decorators import login_required
from flask import Blueprint, render_template, request, jsonify, session
from app.database import get_connection
from flask import (Blueprint, render_template, request, jsonify)
from app.services.pdf_control_service import (
    extraer_texto_pdf_control
)

from app.services.control_ia_service import (
    analizar_documento_control
)

# ==========================================================
# BLUEPRINT: CONTROL Y EVIDENCIA
# ==========================================================
# Este blueprint agrupa todas las rutas relacionadas con:
# - Seguimiento de recomendaciones
# - Bitácora de control
# - Evidencias documentales
# - Acciones de seguimiento
# - Informes de control
#
# Se mantiene separado de routes.py para evitar seguir
# creciendo el archivo principal del sistema.
# ==========================================================

control_evidencia_bp = Blueprint(
    "control_evidencia",
    __name__,
    url_prefix="/control-evidencia"
)


# ==========================================================
# PORTADA PRINCIPAL DEL MÓDULO
# ==========================================================
# Esta ruta muestra la pantalla inicial del módulo.
# Por ahora no consulta la base de datos.
# Su objetivo inicial es validar la estructura visual
# y servir como menú principal de Control y Evidencia.
# ==========================================================

@control_evidencia_bp.route("/")
@login_required(role=None)
def inicio():

    return render_template(
        "control_evidencia/control_evidencia_inicio.html"
    )
# ============================================================
# BITÁCORA DE CONTROL
# Formulario para registrar la revisión y seguimiento
# de los requerimientos y procedimientos de contratación.
# ============================================================

@control_evidencia_bp.route("/bitacora/nueva", methods=["GET"])
@login_required()
def bitacora_nueva():

    conn = get_connection()
    cur = conn.cursor()

    # ============================================================
    # CARGAR OFICIOS DE VICERRECTORADO
    # Se muestran únicamente requerimientos que tengan
    # registrado el memorando/oficio de Vicerrectorado.
    # ============================================================
    cur.execute("""
        SELECT
            r.id,
            r.memo_vice_ad
        FROM requerimientos r
        WHERE r.memo_vice_ad IS NOT NULL
        AND TRIM(r.memo_vice_ad) <> ''
        ORDER BY r.id DESC
    """)

    filas = cur.fetchall()

    requerimientos = [
        {
            "id": fila[0],
            "memo_vice_ad": fila[1]
        }
        for fila in filas
    ]

    # --------------------------------------------------------
    # Cargar recomendaciones de organismos de control.
    # Estas recomendaciones podrán vincularse posteriormente
    # con cada registro de revisión de la bitácora.
    # --------------------------------------------------------
    cur.execute("""
        SELECT
            id,
            numero_recomendacion,
            organismo_control,
            informe_origen,
            recomendacion
        FROM recomendaciones_control
        WHERE activo = TRUE
        ORDER BY id DESC
    """)

    filas_recomendaciones = cur.fetchall()

    recomendaciones = [
        {
            "id": fila[0],
            "numero_recomendacion": fila[1],
            "organismo_control": fila[2],
            "informe_origen": fila[3],
            "recomendacion": fila[4]
        }
        for fila in filas_recomendaciones
    ]

    cur.close()
    conn.close()

    # --------------------------------------------------------
    # Mostrar formulario de Bitácora de Control.
    # --------------------------------------------------------
    return render_template(
        "control_evidencia/bitacora_form.html",
        requerimientos=requerimientos,
        recomendaciones=recomendaciones
    )
# ============================================================
# API - DATOS DEL REQUERIMIENTO PARA BITÁCORA
# ============================================================

@control_evidencia_bp.route("/api/requerimiento/<int:requerimiento_id>")
@login_required()
def api_requerimiento_bitacora(requerimiento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            r.fecha_recep_req,
            r.funcionario_elaborador,
            r.funcionario_encargado,
            u.nombre_unidad,
            t.codigo_proceso
        FROM requerimientos r
        LEFT JOIN unidades u
               ON u.id = r.unid_requirente
        LEFT JOIN tareas t
               ON t.requerimiento_id = r.id
        WHERE r.id = %s
        ORDER BY t.id DESC
        LIMIT 1
    """, (requerimiento_id,))

    fila = cur.fetchone()

    cur.close()
    conn.close()

    if not fila:
        return {
            "ok": False
        }, 404

    return {
        "ok": True,
        "fecha_ingreso": fila[0].isoformat() if fila[0] else "",
        "funcionario_elaborador": fila[1] or "",
        "servidor_revision": fila[2] or "",
        "unidad_requirente": fila[3] or "",
        "codigo_proceso": fila[4] or ""
    }
# ============================================================
# GUARDAR REVISIÓN DOCUMENTAL DE CONTROL
# ============================================================

from flask import request, jsonify, session
@control_evidencia_bp.route(
    "/bitacora/guardar-revision",
    methods=["POST"]
)
@login_required()
def guardar_revision_documental():

    data = request.get_json()

    requerimiento_id = data.get("requerimiento_id")
    recomendacion_id = data.get("recomendacion_id")
    tipo_documento = data.get("tipo_documento")
    observacion_analista = data.get("observacion_analista")

    # NUEVO:
    # Resultado completo que devolvió la IA
    resultado_ia = data.get("resultado_ia") or None


    # ============================================================
    # VALIDACIONES
    # ============================================================

    if not requerimiento_id:
        return jsonify({
            "ok": False,
            "mensaje": "Debe seleccionar un requerimiento."
        }), 400

    if not tipo_documento:
        return jsonify({
            "ok": False,
            "mensaje": "Debe seleccionar el documento revisado."
        }), 400

    if not observacion_analista:
        return jsonify({
            "ok": False,
            "mensaje": "Debe registrar una observación."
        }), 400


    conn = get_connection()
    cur = conn.cursor()

    try:

        # ========================================================
        # 1. OBTENER DATOS DEL REQUERIMIENTO
        # ========================================================

        cur.execute("""
            SELECT
                r.memo_vice_ad,
                r.fecha_recep_req,
                r.funcionario_elaborador,
                r.funcionario_encargado,
                u.nombre_unidad,
                t.codigo_proceso

            FROM requerimientos r

            LEFT JOIN unidades u
                ON u.id = r.unid_requirente

            LEFT JOIN tareas t
                ON t.requerimiento_id = r.id

            WHERE r.id = %s

            ORDER BY t.id DESC
            LIMIT 1
        """, (requerimiento_id,))

        req = cur.fetchone()

        if not req:

            return jsonify({
                "ok": False,
                "mensaje": "No se encontró el requerimiento."
            }), 404


        referencia_requerimiento = req[0]
        fecha_ingreso = req[1]
        funcionario_elaborador = req[2]
        servidor_revision = req[3]
        unidad_requirente = req[4]
        codigo_proceso = req[5]


        # ========================================================
        # 2. BUSCAR BITÁCORA EXISTENTE
        # ========================================================

        cur.execute("""
            SELECT id
            FROM bitacora_control

            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'

            ORDER BY id DESC
            LIMIT 1
        """, (requerimiento_id,))

        fila_bitacora = cur.fetchone()


        # ========================================================
        # 3. UTILIZAR O CREAR BITÁCORA
        # ========================================================

        if fila_bitacora:

            bitacora_id = fila_bitacora[0]

            # Si escogió recomendación, actualizar vínculo
            if recomendacion_id:

                cur.execute("""
                    UPDATE bitacora_control

                    SET recomendacion_id = %s

                    WHERE id = %s
                """, (
                    recomendacion_id,
                    bitacora_id
                ))

        else:

            cur.execute("""
                INSERT INTO bitacora_control (
                    recomendacion_id,
                    codigo_proceso,
                    tipo_actuacion,
                    descripcion,
                    resultado,
                    fecha_actuacion,
                    usuario_id,
                    origen,
                    origen_id,
                    estado,
                    referencia_requerimiento,
                    unidad_requirente,
                    fecha_ingreso,
                    servidor_responsable
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_DATE,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )

                RETURNING id
            """, (
                recomendacion_id,
                codigo_proceso,
                "REVISION DOCUMENTAL",
                "Revisión documental de requerimiento",
                "PENDIENTE",
                session.get("usuario_id"),
                "REQUERIMIENTO",
                requerimiento_id,
                "ACTIVO",
                referencia_requerimiento,
                unidad_requirente,
                fecha_ingreso,
                servidor_revision
            ))

            bitacora_id = cur.fetchone()[0]


        # ========================================================
        # 4. GUARDAR REVISIÓN DOCUMENTAL
        # ========================================================

        cur.execute("""
            INSERT INTO revisiones_documentales_control (
                bitacora_id,
                tipo_documento,
                referencia_documento,
                observacion_analista,
                resultado_ia,
                usuario_id
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )

            RETURNING
                id,
                tipo_documento,
                observacion_analista,
                resultado_ia,
                fecha_revision
        """, (
            bitacora_id,
            tipo_documento,
            referencia_requerimiento,
            observacion_analista.strip(),
            resultado_ia,
            session.get("usuario_id")
        ))

        revision = cur.fetchone()

        conn.commit()


        # ========================================================
        # 5. DEVOLVER DATOS AL FRONT
        # ========================================================

        return jsonify({
            "ok": True,
            "mensaje": "Revisión guardada correctamente.",

            "bitacora_id": bitacora_id,

            "revision": {
                "id": revision[0],
                "tipo_documento": revision[1],
                "observacion": revision[2],
                "resultado_ia": revision[3],
                "fecha_revision": (
                    revision[4].isoformat()
                    if revision[4]
                    else ""
                )
            }
        })


    except Exception as e:

        conn.rollback()

        print(
            "ERROR GUARDANDO REVISIÓN DOCUMENTAL:",
            e
        )

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 500


    finally:

        cur.close()
        conn.close()

# ============================================================
# API - CARGAR REVISIONES EXISTENTES DE UN REQUERIMIENTO
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/revisiones/<int:requerimiento_id>",
    methods=["GET"]
)
@login_required()
def obtener_revisiones_bitacora(requerimiento_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        # Buscar bitácora activa del requerimiento
        cur.execute("""
            SELECT id
            FROM bitacora_control
            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'
            ORDER BY id DESC
            LIMIT 1
        """, (requerimiento_id,))

        bitacora = cur.fetchone()

        # Todavía no existe bitácora
        if not bitacora:
            return jsonify({
                "ok": True,
                "existe_bitacora": False,
                "bitacora_id": None,
                "revisiones": []
            })

        bitacora_id = bitacora[0]

        # Cargar documentos ya revisados
        cur.execute("""
            SELECT
                id,
                tipo_documento,
                observacion_analista,
                fecha_revision
            FROM revisiones_documentales_control
            WHERE bitacora_id = %s
            ORDER BY id ASC
        """, (bitacora_id,))

        filas = cur.fetchall()

        revisiones = []

        for fila in filas:

            revisiones.append({
                "id": fila[0],
                "tipo_documento": fila[1],
                "observacion": fila[2],
                "fecha_revision": (
                    fila[3].isoformat()
                    if fila[3]
                    else ""
                )
            })

        return jsonify({
            "ok": True,
            "existe_bitacora": True,
            "bitacora_id": bitacora_id,
            "total": len(revisiones),
            "revisiones": revisiones
        })

    finally:
        cur.close()
        conn.close()
# ============================================================
# EDITAR REVISIÓN DOCUMENTAL
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/revision/<int:revision_id>/editar",
    methods=["PUT"]
)
@login_required()
def editar_revision_documental(revision_id):

    data = request.get_json()

    tipo_documento = data.get("tipo_documento")
    observacion_analista = data.get("observacion_analista")
    resultado_ia = data.get("resultado_ia") or None

    if not tipo_documento:
        return jsonify({
            "ok": False,
            "mensaje": "Debe seleccionar el documento revisado."
        }), 400

    if not observacion_analista:
        return jsonify({
            "ok": False,
            "mensaje": "Debe registrar una observación."
        }), 400

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE revisiones_documentales_control
            SET
                tipo_documento = %s,
                observacion_analista = %s,
                resultado_ia = %s,
                fecha_revision = CURRENT_DATE
            WHERE id = %s
            RETURNING id
        """, (
            tipo_documento,
            observacion_analista.strip(),
            resultado_ia,
            revision_id
        ))

        fila = cur.fetchone()

        if not fila:

            conn.rollback()

            return jsonify({
                "ok": False,
                "mensaje": "La revisión no existe."
            }), 404

        conn.commit()

        return jsonify({
            "ok": True,
            "mensaje": "Revisión actualizada correctamente."
        })

    except Exception as e:

        conn.rollback()

        print("ERROR EDITANDO REVISIÓN:", e)

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()

# ============================================================
# ELIMINAR REVISIÓN DOCUMENTAL
# ============================================================
@control_evidencia_bp.route(
    "/bitacora/revision/<int:revision_id>/eliminar",
    methods=["POST"]
)
@login_required()
def eliminar_revision_documental(revision_id):

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM revisiones_documentales_control
            WHERE id = %s
            RETURNING id
        """, (revision_id,))

        fila = cur.fetchone()

        if not fila:
            conn.rollback()
            return jsonify({
                "ok": False,
                "mensaje": "La revisión no existe."
            }), 404

        conn.commit()

        return jsonify({
            "ok": True,
            "mensaje": "Revisión eliminada correctamente."
        })

    except Exception as e:
        conn.rollback()
        print("ERROR ELIMINANDO REVISIÓN:", e)

        return jsonify({
            "ok": False,
            "mensaje": "No se pudo eliminar la revisión."
        }), 500

    finally:
        cur.close()
        conn.close()
# ============================================================
# REVISIÓN DOCUMENTAL CON IA
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/revisar-ia",
    methods=["POST"]
)
@login_required()
def revisar_documento_ia():

    archivo = request.files.get("archivo")

    tipo_documento = str(
        request.form.get("tipo_documento") or ""
    ).strip()


    # ========================================================
    # VALIDACIONES
    # ========================================================

    if not tipo_documento:

        return jsonify({
            "ok": False,
            "mensaje":
                "Debe seleccionar el tipo de documento."
        }), 400


    if not archivo or not archivo.filename:

        return jsonify({
            "ok": False,
            "mensaje":
                "Debe seleccionar un archivo PDF."
        }), 400


    nombre_archivo = archivo.filename.lower()

    if not nombre_archivo.endswith(".pdf"):

        return jsonify({
            "ok": False,
            "mensaje":
                "Solo se permiten archivos PDF."
        }), 400


    try:

        # ====================================================
        # 1. EXTRAER TEXTO DEL PDF EN MEMORIA
        # ====================================================

        texto_documento = (
            extraer_texto_pdf_control(
                archivo
            )
        )


        # ====================================================
        # 2. ANALIZAR CON IA
        # ====================================================

        resultado_ia = (
            analizar_documento_control(
                tipo_documento,
                texto_documento
            )
        )


        # ====================================================
        # 3. DEVOLVER RESULTADO
        #
        # NO guardamos el PDF.
        # NO guardamos todavía el análisis.
        # Solo lo mostramos al analista.
        # ====================================================

        return jsonify({
            "ok": True,
            "tipo_documento": tipo_documento,
            "archivo": archivo.filename,
            "resultado": resultado_ia
        })


    except ValueError as e:

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 400


    except Exception as e:

        import traceback
        traceback.print_exc()

        return jsonify({
            "ok": False,
            "mensaje":
                "No fue posible realizar la revisión "
                "del documento con IA.",
            "detalle": str(e)
        }), 500
        
# ============================================================
# VER DETALLE DE UNA REVISIÓN DOCUMENTAL
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/revision/<int:revision_id>",
    methods=["GET"]
)
@login_required()
def ver_revision_documental(revision_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                bitacora_id,
                tipo_documento,
                referencia_documento,
                observacion_analista,
                resultado_ia,
                fecha_revision,
                usuario_id,
                fecha_registro
            FROM revisiones_documentales_control
            WHERE id = %s
        """, (revision_id,))

        fila = cur.fetchone()

        if not fila:

            return jsonify({
                "ok": False,
                "mensaje": "La revisión no existe."
            }), 404


        return jsonify({
            "ok": True,

            "revision": {
                "id": fila[0],
                "bitacora_id": fila[1],
                "tipo_documento": fila[2],
                "referencia_documento": fila[3],
                "observacion_analista": fila[4],
                "resultado_ia": fila[5],
                "fecha_revision": (
                    fila[6].isoformat()
                    if fila[6]
                    else ""
                ),
                "usuario_id": fila[7],
                "fecha_registro": (
                    fila[8].isoformat()
                    if fila[8]
                    else ""
                )
            }
        })

    except Exception as e:

        print(
            "ERROR CONSULTANDO REVISIÓN:",
            e
        )

        return jsonify({
            "ok": False,
            "mensaje":
                "No fue posible consultar la revisión."
        }), 500

    finally:

        cur.close()
        conn.close()
# ============================================================
# INFORME DE OBSERVACIONES - BITÁCORA DE CONTROL
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/informe-observaciones/<int:requerimiento_id>",
    methods=["GET"]
)
@login_required()
def informe_observaciones(requerimiento_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        # ========================================================
        # 1. DATOS DEL REQUERIMIENTO
        # ========================================================

        cur.execute("""
            SELECT
                r.memo_vice_ad,
                r.fecha_recep_req,
                r.funcionario_elaborador,
                r.funcionario_encargado,
                u.nombre_unidad,
                t.codigo_proceso

            FROM requerimientos r

            LEFT JOIN unidades u
                ON u.id = r.unid_requirente

            LEFT JOIN tareas t
                ON t.requerimiento_id = r.id

            WHERE r.id = %s

            ORDER BY t.id DESC
            LIMIT 1
        """, (requerimiento_id,))

        fila = cur.fetchone()

        if not fila:
            return "No se encontró el requerimiento.", 404

        requerimiento = {
            "memo": fila[0] or "",
            "fecha_ingreso": fila[1],
            "funcionario_elaborador": fila[2] or "",
            "servidor_revision": fila[3] or "",
            "unidad_requirente": fila[4] or "",
            "codigo_proceso": fila[5] or ""
        }


        # ========================================================
        # 2. BUSCAR BITÁCORA
        # ========================================================

        cur.execute("""
            SELECT
                id,
                recomendacion_id
            FROM bitacora_control
            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'
            ORDER BY id DESC
            LIMIT 1
        """, (requerimiento_id,))

        bitacora = cur.fetchone()

        if not bitacora:
            return "Este requerimiento todavía no tiene revisiones.", 404

        bitacora_id = bitacora[0]


        # ========================================================
        # 3. REVISIONES DOCUMENTALES
        # ========================================================

        cur.execute("""
            SELECT
                tipo_documento,
                observacion_analista,
                fecha_revision
            FROM revisiones_documentales_control
            WHERE bitacora_id = %s
            ORDER BY id ASC
        """, (bitacora_id,))

        filas = cur.fetchall()

        revisiones = []

        for revision in filas:

            revisiones.append({
                "tipo_documento": revision[0],
                "observacion": revision[1] or "",
                "fecha_revision": revision[2]
            })


        # ========================================================
        # 4. RECOMENDACIÓN VINCULADA
        # ========================================================

        recomendacion = None

        if bitacora[1]:

            cur.execute("""
                SELECT
                    numero_recomendacion,
                    organismo_control,
                    informe_origen,
                    recomendacion
                FROM recomendaciones_control
                WHERE id = %s
            """, (bitacora[1],))

            rec = cur.fetchone()

            if rec:
                recomendacion = {
                    "numero": rec[0] or "",
                    "organismo": rec[1] or "",
                    "informe": rec[2] or "",
                    "texto": rec[3] or ""
                }


        return render_template(
            "control_evidencia/informe_observaciones.html",
            requerimiento=requerimiento,
            revisiones=revisiones,
            recomendacion=recomendacion
        )

    finally:

        cur.close()
        conn.close()
# ============================================================
# PDF - INFORME DE OBSERVACIONES
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/informe-observaciones/<int:requerimiento_id>/pdf",
    methods=["GET"]
)
@login_required()
def informe_observaciones_pdf(requerimiento_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        # ========================================================
        # 1. DATOS DEL REQUERIMIENTO
        # ========================================================

        cur.execute("""
            SELECT
                r.memo_vice_ad,
                r.fecha_recep_req,
                r.funcionario_elaborador,
                r.funcionario_encargado,
                u.nombre_unidad,
                t.codigo_proceso

            FROM requerimientos r

            LEFT JOIN unidades u
                ON u.id = r.unid_requirente

            LEFT JOIN tareas t
                ON t.requerimiento_id = r.id

            WHERE r.id = %s

            ORDER BY t.id DESC
            LIMIT 1
        """, (requerimiento_id,))

        fila = cur.fetchone()

        if not fila:
            return "No se encontró el requerimiento.", 404

        memo = fila[0] or ""
        fecha_ingreso = fila[1]
        funcionario_elaborador = fila[2] or ""
        servidor_revision = fila[3] or ""
        unidad_requirente = fila[4] or ""
        codigo_proceso = fila[5] or ""


        # ========================================================
        # 2. BITÁCORA
        # ========================================================

        cur.execute("""
            SELECT
                id,
                recomendacion_id
            FROM bitacora_control
            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'
            ORDER BY id DESC
            LIMIT 1
        """, (requerimiento_id,))

        bitacora = cur.fetchone()

        if not bitacora:
            return "Este requerimiento no tiene revisiones.", 404

        bitacora_id = bitacora[0]
        recomendacion_id = bitacora[1]


        # ========================================================
        # 3. REVISIONES
        # ========================================================

        cur.execute("""
            SELECT
                tipo_documento,
                observacion_analista,
                fecha_revision
            FROM revisiones_documentales_control
            WHERE bitacora_id = %s
            ORDER BY id ASC
        """, (bitacora_id,))

        revisiones = cur.fetchall()


        # ========================================================
        # 4. RECOMENDACIÓN
        # ========================================================

        recomendacion = None

        if recomendacion_id:

            cur.execute("""
                SELECT
                    numero_recomendacion,
                    organismo_control,
                    informe_origen,
                    recomendacion
                FROM recomendaciones_control
                WHERE id = %s
            """, (recomendacion_id,))

            recomendacion = cur.fetchone()


        # ========================================================
        # 5. CREAR PDF
        # ========================================================

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=16 * mm
        )

        styles = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            "Titulo",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=colors.HexColor("#173F5F"),
            alignment=TA_CENTER,
            spaceAfter=5
        )

        estilo_subtitulo = ParagraphStyle(
            "Subtitulo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6B7C8C"),
            alignment=TA_CENTER
        )

        estilo_seccion = ParagraphStyle(
            "Seccion",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#173F5F"),
            spaceBefore=8,
            spaceAfter=6
        )

        estilo_texto = ParagraphStyle(
            "Texto",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#263746"),
            alignment=TA_JUSTIFY,
            spaceAfter=5
        )

        estilo_negrita = ParagraphStyle(
            "TextoNegrita",
            parent=estilo_texto,
            fontName="Helvetica-Bold"
        )

        story = []


        # ========================================================
        # ENCABEZADO
        # ========================================================

        story.append(
            Paragraph(
                "UNIVERSIDAD TÉCNICA DE MACHALA",
                ParagraphStyle(
                    "Universidad",
                    parent=estilo_titulo,
                    fontSize=11
                )
            )
        )

        story.append(
            Paragraph(
                "UNIDAD DE COMPRAS PÚBLICAS",
                estilo_subtitulo
            )
        )

        story.append(Spacer(1, 5 * mm))

        story.append(
            Paragraph(
                "INFORME DE OBSERVACIONES",
                estilo_titulo
            )
        )

        story.append(
            Paragraph(
                "Revisión documental de procedimientos de contratación pública",
                estilo_subtitulo
            )
        )

        story.append(Spacer(1, 6 * mm))


        # ========================================================
        # DATOS GENERALES
        # ========================================================

        fecha_txt = (
            fecha_ingreso.strftime("%d/%m/%Y")
            if fecha_ingreso else ""
        )

        datos = [
            [
                Paragraph(
                    "<b>OFICIO DE VICERRECTORADO</b><br/>" + memo,
                    estilo_texto
                ),
                Paragraph(
                    "<b>FECHA DE INGRESO</b><br/>" + fecha_txt,
                    estilo_texto
                )
            ],
            [
                Paragraph(
                    "<b>CÓDIGO DEL PROCESO</b><br/>" + codigo_proceso,
                    estilo_texto
                ),
                Paragraph(
                    "<b>UNIDAD REQUIRENTE</b><br/>" + unidad_requirente,
                    estilo_texto
                )
            ],
            [
                Paragraph(
                    "<b>FUNCIONARIO ELABORADOR</b><br/>" +
                    (funcionario_elaborador or "—"),
                    estilo_texto
                ),
                Paragraph(
                    "<b>SERVIDOR QUE REALIZÓ LA REVISIÓN</b><br/>" +
                    "Ing. " + servidor_revision,
                    estilo_texto
                )
            ]
        ]

        tabla_datos = Table(
            datos,
            colWidths=[91 * mm, 91 * mm]
        )

        tabla_datos.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7E1E8")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ])
        )

        story.append(tabla_datos)
        story.append(Spacer(1, 6 * mm))


        # ========================================================
        # RECOMENDACIÓN DE CONTROL
        # ========================================================

        if recomendacion:

            story.append(
                Paragraph(
                    "Recomendación de control vinculada",
                    estilo_seccion
                )
            )

            numero = str(recomendacion[0] or "")
            organismo = str(recomendacion[1] or "")
            informe = str(recomendacion[2] or "")
            texto_rec = str(recomendacion[3] or "")

            contenido_rec = [
                Paragraph(
                    f"<b>Recomendación {numero} - {organismo}</b>",
                    estilo_texto
                ),
                Paragraph(
                    f"<b>Informe de origen:</b> {informe}",
                    estilo_texto
                ),
                Paragraph(
                    texto_rec,
                    estilo_texto
                )
            ]

            tabla_rec = Table(
                [[contenido_rec]],
                colWidths=[182 * mm]
            )

            tabla_rec.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF9EE")),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#E6B14A")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ])
            )

            story.append(tabla_rec)
            story.append(Spacer(1, 6 * mm))


        # ========================================================
        # REVISIONES DOCUMENTALES
        # ========================================================

        story.append(
            Paragraph(
                "Observaciones de la revisión documental",
                estilo_seccion
            )
        )

        nombres_documentos = {
            "ESTUDIOS_PREVIOS": "Estudios previos",
            "DETERMINACION_NECESIDAD": "Determinación de la necesidad",
            "ESPECIFICACIONES_TECNICAS": "Especificaciones técnicas",
            "TERMINOS_REFERENCIA": "Términos de referencia",
            "PRESUPUESTO_REFERENCIAL": "Determinación del presupuesto referencial",
            "PROFORMAS": "Proformas",
            "OTROS_DOCUMENTOS": "Otros documentos"
        }

        for indice, revision in enumerate(revisiones, start=1):

            tipo = revision[0]
            observacion = revision[1] or ""
            fecha_revision = revision[2]

            nombre_documento = nombres_documentos.get(
                tipo,
                tipo
            )

            fecha_rev_txt = (
                fecha_revision.strftime("%d/%m/%Y")
                if fecha_revision else ""
            )

            cabecera = Table(
                [[
                    Paragraph(
                        f"<b>{indice}. {nombre_documento}</b>",
                        estilo_texto
                    ),
                    Paragraph(
                        f"Revisado: {fecha_rev_txt}",
                        ParagraphStyle(
                            "FechaRevision",
                            parent=estilo_texto,
                            fontSize=8,
                            textColor=colors.HexColor("#718291"),
                            alignment=2
                        )
                    )
                ]],
                colWidths=[140 * mm, 42 * mm]
            )

            cabecera.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF3F8")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CFDDE6")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ])
            )

            story.append(cabecera)
            story.append(Spacer(1, 3 * mm))

            # Convertir saltos de línea para ReportLab
            texto_observacion = observacion.replace(
                "\n",
                "<br/>"
            )

            # Formatear **texto** como negrita
            import re

            texto_observacion = re.sub(
                r"\*\*([^*]+)\*\*",
                r"<b>\1</b>",
                texto_observacion
            )

            texto_observacion = texto_observacion.replace(
                "INCONSISTENCIAS O RIESGOS:",
                "<b>INCONSISTENCIAS O RIESGOS</b><br/><br/>"
            )

            texto_observacion = texto_observacion.replace(
                "RECOMENDACIONES:",
                "<br/><b>RECOMENDACIONES</b><br/><br/>"
            )

            story.append(
                Paragraph(
                    texto_observacion,
                    estilo_texto
                )
            )

            story.append(
                Spacer(1, 5 * mm)
            )


        # ========================================================
        # FIRMAS
        # ========================================================

        story.append(
            Spacer(1, 14 * mm)
        )

        firmas = Table(
            [[
                Paragraph(
                    "<br/><br/><br/>"
                    "<b>Ing. " + servidor_revision + "</b><br/>"
                    "Analista",
                    ParagraphStyle(
                        "Firma1",
                        parent=estilo_texto,
                        alignment=TA_CENTER
                    )
                ),

                Paragraph(
                    "<br/><br/><br/>"
                    "<b>JEFE DE COMPRAS PÚBLICAS</b><br/>"
                    "Unidad de Compras Públicas",
                    ParagraphStyle(
                        "Firma2",
                        parent=estilo_texto,
                        alignment=TA_CENTER
                    )
                )
            ]],
            colWidths=[91 * mm, 91 * mm]
        )

        firmas.setStyle(
            TableStyle([
                ("LINEABOVE", (0, 0), (0, 0), 0.5, colors.HexColor("#687985")),
                ("LINEABOVE", (1, 0), (1, 0), 0.5, colors.HexColor("#687985")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        story.append(firmas)


        # ========================================================
        # CONSTRUIR PDF
        # ========================================================

        doc.build(story)

        buffer.seek(0)

        nombre_archivo = (
            f"Informe_Observaciones_{codigo_proceso or requerimiento_id}.pdf"
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=nombre_archivo
        )


    finally:

        cur.close()
        conn.close()
# ============================================================
# GUARDAR COMUNICACIÓN DE OBSERVACIONES
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/guardar-comunicacion",
    methods=["POST"]
)
@login_required()
def guardar_comunicacion_observaciones():

    data = request.get_json()

    requerimiento_id = data.get("requerimiento_id")
    numero_memorando = (data.get("numero_memorando_observacion") or "").strip()
    fecha_devolucion = data.get("fecha_devolucion")

    if not requerimiento_id:
        return jsonify({
            "ok": False,
            "mensaje": "Debe seleccionar un requerimiento."
        }), 400

    if not numero_memorando:
        return jsonify({
            "ok": False,
            "mensaje": "Debe ingresar el número de memorando."
        }), 400

    if not fecha_devolucion:
        return jsonify({
            "ok": False,
            "mensaje": "Debe ingresar la fecha de comunicación."
        }), 400

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT id
            FROM bitacora_control
            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'
            ORDER BY id DESC
            LIMIT 1
        """, (requerimiento_id,))

        fila = cur.fetchone()

        if not fila:
            return jsonify({
                "ok": False,
                "mensaje": "Primero debe existir una revisión documental."
            }), 400

        bitacora_id = fila[0]

        cur.execute("""
            UPDATE bitacora_control
            SET
                numero_memorando_observacion = %s,
                fecha_devolucion = %s
            WHERE id = %s
        """, (
            numero_memorando,
            fecha_devolucion,
            bitacora_id
        ))

        conn.commit()

        return jsonify({
            "ok": True,
            "mensaje": "Comunicación guardada correctamente."
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 500

    finally:
        cur.close()
        conn.close()
# ============================================================
# GUARDAR SUBSANACIÓN / VERIFICACIÓN
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/guardar-verificacion",
    methods=["POST"]
)
@login_required()
def guardar_verificacion_observaciones():

    data = request.get_json()

    requerimiento_id = data.get("requerimiento_id")
    respuesta_subsanacion = (data.get("respuesta_subsanacion") or "").strip()
    resultado = (data.get("resultado") or "").strip()
    fecha_subsanacion = data.get("fecha_subsanacion")

    if not requerimiento_id:
        return jsonify({
            "ok": False,
            "mensaje": "Debe seleccionar un requerimiento."
        }), 400

    if not respuesta_subsanacion:
        return jsonify({
            "ok": False,
            "mensaje": "Debe registrar la respuesta o subsanación recibida."
        }), 400

    if not resultado:
        return jsonify({
            "ok": False,
            "mensaje": "Debe seleccionar el resultado de la verificación."
        }), 400

    if not fecha_subsanacion:
        return jsonify({
            "ok": False,
            "mensaje": "Debe ingresar la fecha de subsanación."
        }), 400

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                numero_memorando_observacion,
                fecha_devolucion
            FROM bitacora_control
            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'
            ORDER BY id DESC
            LIMIT 1
        """, (requerimiento_id,))

        fila = cur.fetchone()

        if not fila:
            return jsonify({
                "ok": False,
                "mensaje": "No existe una bitácora activa."
            }), 400

        bitacora_id = fila[0]
        numero_memorando = fila[1]
        fecha_devolucion = fila[2]

        # No permitir saltarse la comunicación
        if not numero_memorando or not fecha_devolucion:
            return jsonify({
                "ok": False,
                "mensaje": "Primero debe guardar la comunicación de las observaciones."
            }), 400

        cur.execute("""
            UPDATE bitacora_control
            SET
                respuesta_subsanacion = %s,
                resultado = %s,
                fecha_subsanacion = %s
            WHERE id = %s
        """, (
            respuesta_subsanacion,
            resultado,
            fecha_subsanacion,
            bitacora_id
        ))

        conn.commit()

        return jsonify({
            "ok": True,
            "mensaje": "Verificación guardada correctamente."
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 500

    finally:
        cur.close()
        conn.close()
# ============================================================
# CARGAR ESTADO DE COMUNICACIÓN Y VERIFICACIÓN
# ============================================================

@control_evidencia_bp.route(
    "/bitacora/estado/<int:requerimiento_id>",
    methods=["GET"]
)
@login_required()
def cargar_estado_bitacora(requerimiento_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                numero_memorando_observacion,
                fecha_devolucion,
                respuesta_subsanacion,
                resultado,
                fecha_subsanacion
            FROM bitacora_control
            WHERE origen = 'REQUERIMIENTO'
              AND origen_id = %s
              AND estado = 'ACTIVO'
            ORDER BY id DESC
            LIMIT 1
        """, (
            requerimiento_id,
        ))

        fila = cur.fetchone()

        if not fila:

            return jsonify({
                "ok": True,
                "bitacora": None
            })

        return jsonify({
            "ok": True,

            "bitacora": {

                "numero_memorando_observacion":
                    fila[0] or "",

                "fecha_devolucion":
                    fila[1].isoformat()
                    if fila[1]
                    else "",

                "respuesta_subsanacion":
                    fila[2] or "",

                "resultado":
                    fila[3] or "",

                "fecha_subsanacion":
                    fila[4].isoformat()
                    if fila[4]
                    else ""
            }
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()