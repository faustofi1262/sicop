from flask import Blueprint, render_template, flash, session
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
        # ==========================================
        # SEMÁFORO DEL FLUJO - PUBLICACIONES
        # ==========================================

        # Publicaciones finalizadas
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad
            WHERE UPPER(COALESCE(estado, '')) = 'FINALIZADA'
        """)
        publicaciones_verde = cur.fetchone()[0]


        # Publicaciones activas dentro del plazo
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad
            WHERE UPPER(COALESCE(estado, '')) = 'PUBLICADA'
            AND (
                    fecha_limite IS NULL
                    OR fecha_limite >= CURRENT_DATE
                )
        """)
        publicaciones_amarillo = cur.fetchone()[0]


        # Publicaciones vencidas que aún aparecen activas
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad
            WHERE UPPER(COALESCE(estado, '')) = 'PUBLICADA'
            AND fecha_limite < CURRENT_DATE
        """)
        publicaciones_rojo = cur.fetchone()[0]


        # ==========================================
        # SEMÁFORO DEL FLUJO - PROFORMAS
        # ==========================================

        # Publicaciones que sí tienen proformas
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad p
            WHERE (
                COALESCE(p.proformas_historicas, 0)
                +
                (
                    SELECT COUNT(*)
                    FROM proformas_publicacion pr
                    WHERE pr.publicacion_id = p.id
                )
            ) > 0
        """)
        proformas_verde = cur.fetchone()[0]


        # Publicaciones activas sin proformas y todavía en plazo
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad p
            WHERE UPPER(COALESCE(p.estado, '')) = 'PUBLICADA'
            AND (
                    p.fecha_limite IS NULL
                    OR p.fecha_limite >= CURRENT_DATE
                )
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
        proformas_amarillo = cur.fetchone()[0]


        # Publicaciones vencidas sin proformas
        cur.execute("""
            SELECT COUNT(*)
            FROM publicaciones_necesidad p
            WHERE UPPER(COALESCE(p.estado, '')) = 'PUBLICADA'
            AND p.fecha_limite < CURRENT_DATE
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
        proformas_rojo = cur.fetchone()[0]
        # ==========================================
        # SEMÁFORO DEL FLUJO - REQUERIMIENTOS
        # ==========================================

        # Con tarea creada
        cur.execute("""
        SELECT COUNT(*)
        FROM requerimientos r
        WHERE EXISTS (
            SELECT 1
            FROM tareas t
            WHERE t.requerimiento_id = r.id
        )
        """)
        requerimientos_verde = cur.fetchone()[0]


        # Sin tarea
        cur.execute("""
        SELECT COUNT(*)
        FROM requerimientos r
        WHERE NOT EXISTS (
            SELECT 1
            FROM tareas t
            WHERE t.requerimiento_id = r.id
        )
        """)
        requerimientos_amarillo = cur.fetchone()[0]


       # Requerimientos con tarea observada
        cur.execute("""
            SELECT COUNT(DISTINCT r.id)
            FROM requerimientos r
            JOIN tareas t
                ON t.requerimiento_id = r.id
            WHERE UPPER(COALESCE(t.estado_requerimiento, '')) = 'OBSERVADO'
        """)
        requerimientos_rojo = cur.fetchone()[0]
        # ==========================================
        # SEMÁFORO DEL FLUJO - TAREAS
        # ==========================================

        # Tareas avanzadas o finalizadas
        cur.execute("""
            SELECT COUNT(*)
            FROM tareas
            WHERE UPPER(TRIM(COALESCE(estado_requerimiento, ''))) IN (
                'ADJUDICADA',
                'CONTRATO SUSCRITO',
                'EN EJECUCIÓN',
                'ORDEN DE COMPRA ENVIADA',
                'FINALIZADA',
                'PAGADA'
            )
        """)
        tareas_verde = cur.fetchone()[0]


        # Tareas en trámite
        cur.execute("""
            SELECT COUNT(*)
            FROM tareas
            WHERE UPPER(TRIM(COALESCE(estado_requerimiento, ''))) IN (
                'RECIBIDA',
                'PUBLICADA',
                'CON CERTIFICACION',
                'SOLICITUD DE CERTIFICACIÓN',
                'ENVIADO AUTORIZAR'
            )
        """)
        tareas_amarillo = cur.fetchone()[0]


        # Tareas devueltas
        cur.execute("""
            SELECT COUNT(*)
            FROM tareas
            WHERE UPPER(TRIM(COALESCE(estado_requerimiento, ''))) = 'DEVUELTO'
        """)
        tareas_rojo = cur.fetchone()[0]
        # ==========================================
        # SEMÁFORO - ÓRDENES DE ÍNFIMA CUANTÍA
        # ==========================================

        cur.execute("""
            SELECT COUNT(DISTINCT t.id)
            FROM tareas t
            JOIN ordenes_compra oc
                ON oc.tarea_id = t.id
            WHERE UPPER(TRIM(COALESCE(t.codigo_proceso, '')))
                LIKE 'IC-%'
        """)
        ordenes_verde = cur.fetchone()[0]


        cur.execute("""
            SELECT COUNT(*)
            FROM tareas t
            WHERE UPPER(TRIM(COALESCE(t.codigo_proceso, '')))
                LIKE 'IC-%'
            AND NOT EXISTS (
                SELECT 1
                FROM ordenes_compra oc
                WHERE oc.tarea_id = t.id
            )
        """)
        ordenes_amarillo = cur.fetchone()[0]


        cur.execute("""
            SELECT COUNT(*)
            FROM ordenes_compra oc
            JOIN tareas t
                ON t.id = oc.tarea_id
            WHERE UPPER(TRIM(COALESCE(t.codigo_proceso, '')))
                LIKE 'IC-%'
            AND (
                oc.proveedor IS NULL
                OR TRIM(oc.proveedor) = ''
                OR oc.administrador_orden IS NULL
                OR TRIM(oc.administrador_orden) = ''
                OR oc.total IS NULL
                OR oc.total <= 0
            )
        """)
        ordenes_rojo = cur.fetchone()[0]
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
        publicaciones_verde = 0
        publicaciones_amarillo = 0
        publicaciones_rojo = 0

        proformas_verde = 0
        proformas_amarillo = 0
        proformas_rojo = 0
        requerimientos_verde = 0
        requerimientos_amarillo = 0
        requerimientos_rojo = 0
        tareas_verde = 0
        tareas_amarillo = 0
        tareas_rojo = 0        
        ordenes_verde = 0
        ordenes_amarillo = 0
        ordenes_rojo = 0

        flash(
            f"Error: {e}",
            "danger"
        )

    finally:

        cur.close()
        conn.close()
    rol_actual = session.get("rol", "").strip().lower()
    
    return render_template(
        "inteligencia/centro_inteligencia.html",

        total_requerimientos=total_requerimientos,
        total_tareas=total_tareas,
        total_publicaciones=total_publicaciones,
        total_ordenes=total_ordenes,
        total_contratos=total_contratos,
        total_alertas=total_alertas,
        rol_actual=rol_actual,
        alerta_publicaciones_sin_proformas=
            alerta_publicaciones_sin_proformas,

        alerta_contratos_por_vencer=
            alerta_contratos_por_vencer,
        publicaciones_verde=publicaciones_verde,
        publicaciones_amarillo=publicaciones_amarillo,
        publicaciones_rojo=publicaciones_rojo,

        proformas_verde=proformas_verde,
        proformas_amarillo=proformas_amarillo,
        proformas_rojo=proformas_rojo,
        requerimientos_verde=requerimientos_verde,
        requerimientos_amarillo=requerimientos_amarillo,
        requerimientos_rojo=requerimientos_rojo,
        tareas_verde=tareas_verde,
        tareas_amarillo=tareas_amarillo,
        tareas_rojo=tareas_rojo,
        ordenes_verde=ordenes_verde,
        ordenes_amarillo=ordenes_amarillo,
        ordenes_rojo=ordenes_rojo
        
    )
    