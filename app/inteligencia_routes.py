from flask import Blueprint, render_template, flash
from app.database import get_connection
from app.decorators import login_required

inteligencia = Blueprint(
    "inteligencia",
    __name__
)


# ==========================================
# CENTRO DE INTELIGENCIA SICOP
# DASHBOARD EJECUTIVO
# ==========================================
@inteligencia.route("/centro_inteligencia")
@login_required()
def centro_inteligencia():

    conn = get_connection()
    cur = conn.cursor()

    try:

        # ======================================
        # TOTALES
        # ======================================

        cur.execute("SELECT COUNT(*) FROM requerimientos")
        total_requerimientos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tareas")
        total_tareas = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM publicaciones_necesidad")
        total_publicaciones = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ordenes_compra")
        total_ordenes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM seguimiento_contratos")
        total_contratos = cur.fetchone()[0]

        # ======================================
        # ALERTAS
        # ======================================

        # Publicaciones activas sin proformas
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad p
            WHERE UPPER(COALESCE(p.estado, '')) = 'PUBLICADA'
            AND (
                    COALESCE(p.proformas_historicas, 0)
                    +
                    (
                        SELECT COUNT(*)
                        FROM proformas_publicacion pr
                        WHERE pr.publicacion_id = p.id
                    )
                ) = 0
        """)

        alerta_publicaciones_sin_proformas = cur.fetchone()[0]


        # Contratos próximos a vencer en 15 días
        cur.execute("""
            SELECT COUNT(*)
            FROM seguimiento_contratos
            WHERE fecha_fin_estimada
                BETWEEN CURRENT_DATE
                AND CURRENT_DATE + INTERVAL '15 days'
            AND UPPER(COALESCE(estado, '')) IN (
                'EN EJECUCIÓN',
                'EN EJECUCION'
            )
        """)

        alerta_contratos_por_vencer = cur.fetchone()[0]


        total_alertas = (
            alerta_publicaciones_sin_proformas
            + alerta_contratos_por_vencer
        )

    except Exception as e:

        print(e)

        total_requerimientos = 0
        total_tareas = 0
        total_publicaciones = 0
        total_ordenes = 0
        total_contratos = 0
        total_alertas = 0
        alerta_publicaciones_sin_proformas = 0
        alerta_contratos_por_vencer = 0

        flash(
            f"Error: {e}",
            "danger"
        )

    finally:

        cur.close()
        conn.close()

    return render_template(
        "inteligencia/centro_inteligencia.html",

        total_requerimientos=total_requerimientos,
        total_tareas=total_tareas,
        total_publicaciones=total_publicaciones,
        total_ordenes=total_ordenes,
        total_contratos=total_contratos,
        total_alertas=total_alertas,
        alerta_publicaciones_sin_proformas=
            alerta_publicaciones_sin_proformas,

        alerta_contratos_por_vencer=
            alerta_contratos_por_vencer
    )