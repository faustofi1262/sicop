from flask import Blueprint, render_template

from app.decorators import login_required

from app.database import get_connection

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
        # 2. BUSCAR SI YA EXISTE BITÁCORA PARA ESE REQUERIMIENTO
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
        # 3. SI NO EXISTE, CREAR BITÁCORA PRINCIPAL
        # ========================================================
        if fila_bitacora:

            bitacora_id = fila_bitacora[0]

            # Si seleccionó recomendación, actualizarla
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
                fecha_revision
        """, (
            bitacora_id,
            tipo_documento,
            referencia_requerimiento,
            observacion_analista,
            None,
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
                "fecha_revision": revision[3].isoformat()
                    if revision[3]
                    else ""
            }
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