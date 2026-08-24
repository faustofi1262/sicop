from flask import (
    Blueprint,
    render_template,
    request,
    jsonify
)

from app.database import get_connection
from app.routes import login_required


normativa_control_bp = Blueprint(
    "normativa_control",
    __name__,
    url_prefix="/normativa-control"
)


# ============================================================
# INICIO DEL MÓDULO
# ============================================================

@normativa_control_bp.route("/")
@login_required()
def inicio_normativa_control():

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                id,
                nombre,
                tipo_norma,
                numero_norma,
                fecha_publicacion,
                vigente,
                fuente_oficial
            FROM normativas_control
            ORDER BY id DESC
        """)

        filas = cur.fetchall()

        normativas = []

        for fila in filas:

            normativas.append({
                "id": fila[0],
                "nombre": fila[1],
                "tipo_norma": fila[2],
                "numero_norma": fila[3],
                "fecha_publicacion": fila[4],
                "vigente": fila[5],
                "fuente_oficial": fila[6]
            })

        return render_template(
            "normativa_control/normativa_inicio.html",
            normativas=normativas
        )

    finally:

        cur.close()
        conn.close()


# ============================================================
# GUARDAR CABECERA DE NORMATIVA
# ============================================================
@normativa_control_bp.route(
    "/guardar",
    methods=["POST"]
)
@login_required()
def guardar_normativa_control():

    import os
    import tempfile

    from app.services.normativa_control_service import (
        extraer_texto_pdf,
        extraer_articulos
    )

    nombre = (
        request.form.get("nombre")
        or ""
    ).strip()

    tipo_norma = (
        request.form.get("tipo_norma")
        or ""
    ).strip()

    numero_norma = (
        request.form.get("numero_norma")
        or ""
    ).strip()

    fecha_publicacion = (
        request.form.get("fecha_publicacion")
        or None
    )

    fuente_oficial = (
        request.form.get("fuente_oficial")
        or ""
    ).strip()

    observaciones = (
        request.form.get("observaciones")
        or ""
    ).strip()

    archivo_pdf = request.files.get(
        "archivo_pdf"
    )


    # ========================================================
    # VALIDACIONES
    # ========================================================

    if not nombre:

        return jsonify({
            "ok": False,
            "mensaje":
                "Debe ingresar el nombre de la normativa."
        }), 400


    if not archivo_pdf:

        return jsonify({
            "ok": False,
            "mensaje":
                "Debe seleccionar el PDF de la normativa."
        }), 400


    nombre_archivo = (
        archivo_pdf.filename
        or ""
    ).lower()


    if not nombre_archivo.endswith(".pdf"):

        return jsonify({
            "ok": False,
            "mensaje":
                "El archivo seleccionado debe ser PDF."
        }), 400


    conn = get_connection()
    cur = conn.cursor()

    ruta_temporal = None


    try:

        # ====================================================
        # 1. GUARDAR PDF TEMPORALMENTE
        # ====================================================

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temporal:

            archivo_pdf.save(
                temporal.name
            )

            ruta_temporal = (
                temporal.name
            )


        # ====================================================
        # 2. EXTRAER TEXTO
        # ====================================================

        texto = extraer_texto_pdf(
            ruta_temporal
        )


        # ====================================================
        # 3. EXTRAER ARTÍCULOS
        # ====================================================

        articulos = extraer_articulos(
            texto
        )
        if len(articulos) > 500:
            raise ValueError(
                f"Se detectaron {len(articulos)} artículos, "
                "lo que parece incorrecto. Revise el PDF o el patrón de extracción."
            )

        if not articulos:

            raise ValueError(
                "No se identificaron artículos "
                "en la normativa."
            )


        # ====================================================
        # 4. INSERTAR NORMATIVA
        # ====================================================

        cur.execute("""
            INSERT INTO normativas_control (
                nombre,
                tipo_norma,
                numero_norma,
                fecha_publicacion,
                vigente,
                fuente_oficial,
                observaciones
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                TRUE,
                %s,
                %s
            )
            RETURNING id
        """, (
            nombre,
            tipo_norma or None,
            numero_norma or None,
            fecha_publicacion,
            fuente_oficial or None,
            observaciones or None
        ))

        normativa_id = (
            cur.fetchone()[0]
        )


        # ====================================================
        # 5. INSERTAR ARTÍCULOS
        # ====================================================

        total_articulos = 0

        for articulo in articulos:

            cur.execute("""
                INSERT INTO articulos_normativa_control (
                    normativa_id,
                    numero_articulo,
                    titulo,
                    contenido,
                    palabras_clave,
                    activo
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
            """, (
                normativa_id,
                articulo["numero_articulo"],
                articulo["titulo"],
                articulo["contenido"],
                articulo["palabras_clave"]
            ))

            total_articulos += 1


        # ====================================================
        # 6. CONFIRMAR TODO
        # ====================================================

        conn.commit()


        return jsonify({
            "ok": True,

            "mensaje":
                f"Normativa registrada correctamente. "
                f"Se cargaron {total_articulos} artículos.",

            "normativa_id":
                normativa_id,

            "total_articulos":
                total_articulos
        })


    except Exception as e:

        conn.rollback()

        print(
            "ERROR CARGANDO NORMATIVA:",
            e
        )

        return jsonify({
            "ok": False,
            "mensaje": str(e)
        }), 500


    finally:

        cur.close()
        conn.close()

        # ====================================================
        # 7. ELIMINAR PDF TEMPORAL
        # ====================================================

        if (
            ruta_temporal
            and
            os.path.exists(
                ruta_temporal
            )
        ):

            try:

                os.remove(
                    ruta_temporal
                )

            except Exception:

                pass