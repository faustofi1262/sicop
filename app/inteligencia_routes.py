from flask import Blueprint, render_template, flash
from app.database import get_connection
from app.routes import login_required


inteligencia = Blueprint(
    "inteligencia",
    __name__
)


# ==========================================
# CENTRO DE INTELIGENCIA SICOP
# ==========================================
@inteligencia.route("/centro_inteligencia")
@login_required()
def centro_inteligencia():

    conn = get_connection()
    cur = conn.cursor()

    try:

        # Aquí irá la consulta de trazabilidad
        trazabilidad = []

    except Exception as e:

        print(
            "ERROR CENTRO DE INTELIGENCIA:",
            e
        )

        trazabilidad = []

        flash(
            f"❌ No fue posible cargar la trazabilidad: {e}",
            "danger"
        )

    finally:

        cur.close()
        conn.close()

    return render_template(
        "inteligencia/centro_inteligencia.html",
        trazabilidad=trazabilidad
    )