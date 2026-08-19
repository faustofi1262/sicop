from flask import Blueprint, render_template, request

from app.decorators import login_required

from flask import Blueprint, render_template
from app.database import get_connection
from app.decorators import login_required


# ==========================================================
# BLUEPRINT - CONSULTAS Y CRUCES
# ==========================================================

consultas_bp = Blueprint(
    "consultas",
    __name__,
    url_prefix="/consultas"
)


# ==========================================================
# PORTADA CONSULTAS Y CRUCES
# ==========================================================

@consultas_bp.route("/")
@login_required(role=None)
def inicio():

    return render_template(
        "consultas/consultas_inicio.html"
    )
# ==========================================================
# REQUERIMIENTO VS PAC
# ==========================================================
@consultas_bp.route("/requerimiento-pac")
@login_required(role=None)
def requerimiento_pac():

    conn = get_connection()
    cur = conn.cursor()

    # ======================================================
    # 1. LISTADO DE REQUERIMIENTOS
    # ======================================================
    cur.execute("""
        SELECT
            r.id,
            r.mem_requi,
            r.fecha_recep_req,
            r.descripcion,
            r.monto_req,
            u.nombre_unidad,
            u.departamento_principal,
            u.bloque

        FROM requerimientos r

        LEFT JOIN unidades u
            ON u.id = r.unid_requirente

        ORDER BY
            r.fecha_recep_req DESC NULLS LAST,
            r.id DESC
    """)

    requerimientos = cur.fetchall()


    # ======================================================
    # 2. REQUERIMIENTO SELECCIONADO
    # ======================================================
    requerimiento_id = request.args.get(
        "requerimiento_id",
        type=int
    )

    requerimiento = None
    partidas = []


    if requerimiento_id:

        # ==================================================
        # DATOS GENERALES
        # ==================================================
        cur.execute("""
            SELECT
                r.id,
                r.mem_requi,
                r.fecha_memo_requi,
                r.fecha_recep_req,
                r.breve_descr,
                r.descripcion,
                r.monto_req,
                r.funcionario_encargado,

                u.nombre_unidad,
                u.departamento_principal,
                u.bloque,

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

        requerimiento = cur.fetchone()


        # ==================================================
        # PARTIDAS DEL REQUERIMIENTO
        # ==================================================
        cur.execute("""
            SELECT
                id,
                nombre_part,
                num_part,
                fuente,
                programa,
                monto

            FROM partidas

            WHERE requerimiento_id = %s

            ORDER BY
                programa,
                num_part,
                fuente
        """, (requerimiento_id,))

        partidas = cur.fetchall()


    cur.close()
    conn.close()


    return render_template(
        "consultas/requerimiento_pac.html",

        requerimientos=requerimientos,

        requerimiento=requerimiento,
        partidas=partidas,

        requerimiento_id=requerimiento_id
    )