from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import os
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from flask import render_template, abort
from num2words import num2words
from decimal import Decimal, ROUND_HALF_UP
from psycopg2.extras import RealDictCursor
from flask import jsonify
from io import BytesIO
from flask import send_file
from flask import send_file
from io import BytesIO
from app.services.pdf_orden_compra import generar_pdf_orden_compra

def valor_en_letras_con_decimales(valor):
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    entero = int(valor)
    decimal = int((valor - entero) * 100)

    letras = num2words(entero, lang="es").capitalize()
    return f"{letras} dólares con {decimal:02d}/100"

def generar_numero_verificacion(cur):
    year = datetime.now().year
    
    cur.execute("""
        SELECT COUNT(*) FROM verificaciones_procedimiento
        WHERE EXTRACT(YEAR FROM fecha_elaboracion) = %s
    """, (year,))
    count = cur.fetchone()[0] + 1
    return f"UCP-VERF-{year}-{str(count).zfill(4)}"

main = Blueprint(
    "main",
    __name__,
    template_folder="../templates"
)

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# 🔐 AQUÍ VA EL DECORADOR 
def login_required(role=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("main.login_form"))
            if role and session.get("rol") != role:
                return redirect(url_for("main.login_form"))
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

@main.route("/", methods=["GET"])
def inicio():
    return render_template("inicio.html")


@main.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")

@main.route("/login", methods=["POST"])
def login():
    usuario = request.form.get("usuario")
    password = request.form.get("password")

    if not usuario or not password:
        flash("Faltan datos", "error")
        return redirect(url_for("main.login_form"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, usuario, password_hash, rol
        FROM usuarios
        WHERE usuario = %s OR correo = %s
    """, (usuario, usuario))

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        flash("Usuario no encontrado", "error")
        return redirect(url_for("main.login_form"))

    user_id, user_usuario, password_hash, rol = user

    if not check_password_hash(password_hash, password):
        flash("Contraseña incorrecta", "error")
        return redirect(url_for("main.login_form"))

    # ✔ Login exitoso
    session["user_id"] = user_id
    session["usuario"] = user_usuario
    session["rol"] = rol

#==========================
# DIRECCIONAMIENTO DE ROLES
#==========================
# 🔀 Redirección por rol

    if rol.lower() == "administrador":
        return redirect(url_for("main.admin_dashboard"))
    elif rol.lower() == "analista":
        return redirect(url_for("main.analista_dashboard"))
    else:
        return redirect(url_for("main.user_dashboard"))


@main.route("/admin")
@login_required(role="Administrador")
def admin_dashboard():
    return render_template(
        "admin_dashboard.html",
        nombre=session.get("usuario")
    )

@main.route("/usuario")
@login_required(role="Usuario")
def user_dashboard():
    return render_template(
        "usuario_dashboard.html",
        nombre=session.get("usuario")
    )

@main.route("/admin/usuarios")
@login_required(role="Administrador")
def gestionar_usuarios():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, usuario, nombre, correo, rol
        FROM usuarios
        ORDER BY id
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    usuarios = []
    for r in rows:
        usuarios.append({
            "id": r[0],
            "usuario": r[1],
            "nombre": r[2],
            "correo": r[3],
            "rol": r[4]
        })

    return render_template("admin_usuarios.html", usuarios=usuarios)
#===================
# CREAR USUARIO
#===================
@main.route("/admin/usuarios/nuevo", methods=["GET", "POST"])
@login_required(role="Administrador")
def crear_usuario():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        password = request.form.get("password")
        rol = request.form.get("rol")

        password_hash = generate_password_hash(password)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO usuarios (usuario, nombre, correo, password_hash, rol)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario, nombre, correo, password_hash, rol))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("main.gestionar_usuarios"))

    return render_template("admin_usuario_nuevo.html")

#===================
#ELIMINAR USUARIO
#===================

@main.route("/admin/usuarios/eliminar/<int:user_id>", methods=["POST"])
@login_required(role="Administrador")
def eliminar_usuario(user_id):
    # Evitar que el admin se elimine a sí mismo
    if user_id == session.get("user_id"):
        return redirect(url_for("main.gestionar_usuarios"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("main.gestionar_usuarios"))
#===================
# EDITAR USUARIO
#===================

@main.route("/admin/usuarios/editar/<int:user_id>", methods=["GET", "POST"])
@login_required(role="Administrador")
def editar_usuario(user_id):
    # Evitar editar tu propio rol
    if user_id == session.get("user_id"):
        return redirect(url_for("main.gestionar_usuarios"))

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        nuevo_rol = request.form.get("rol")

        cur.execute("""
            UPDATE usuarios
            SET rol = %s
            WHERE id = %s
        """, (nuevo_rol, user_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("main.gestionar_usuarios"))

    # GET → cargar datos actuales
    cur.execute("""
        SELECT id, usuario, rol
        FROM usuarios
        WHERE id = %s
    """, (user_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return redirect(url_for("main.gestionar_usuarios"))

    usuario = {
        "id": row[0],
        "usuario": row[1],
        "rol": row[2]
    }

    return render_template("admin_usuario_editar.html", usuario=usuario)

#====================
#PERFIL ANALISTA Y USUARIO
#====================

@main.route("/analista")
@login_required(role="Analista")
def analista_dashboard():
    return render_template(
        "analista_dashboard.html",
        nombre=session.get("usuario")
    )
# ===============================
# INGRESOS DE REQUERIMIENTOS
# ===============================
@main.route("/requerimientos")
@login_required(role=None)
def listar_requerimientos():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.id,
               r.mem_requi,
               r.fecha_memo_requi,
               u.nombre_unidad,
               r.monto_req
        FROM requerimientos r
        LEFT JOIN unidades u ON u.id = r.unid_requirente
        ORDER BY r.id DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    requerimientos = [
        {
            "id": r[0],
            "mem_requi": r[1],
            "fecha_memo_requi": r[2],
            "unidad": r[3],
            "monto_req": r[4],
        }
        for r in rows
    ]

    return render_template(
        "requerimientos/requerimientos_list.html",
        requerimientos=requerimientos
    )
# ===============================
# NUEVO REQUERIMIENTOS
# ===============================
@main.route("/requerimientos/nuevo")
@login_required(role=None)  # Admin y Analista
def nuevo_requerimiento():
    conn = get_connection()
    cur = conn.cursor()

    # Unidades
    cur.execute("SELECT id, nombre_unidad FROM unidades ORDER BY nombre_unidad")
    unidades = cur.fetchall()

    # Funcionarios (usuarios)
    cur.execute("SELECT nombre FROM usuarios ORDER BY nombre")
    funcionarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "requerimientos/requerimiento_form.html",
        unidades=unidades,
        funcionarios=funcionarios
    )
# ===============================
# GUARDAR REQUERIMIENTOS
# ===============================
@main.route("/requerimientos/guardar", methods=["POST"])
@login_required(role=None)
def guardar_requerimiento():
    conn = get_connection()
    cur = conn.cursor()

    requerimiento_id = request.form.get("id")  # 👈 CLAVE

    if requerimiento_id:
        # =====================
        # UPDATE
        # =====================
        cur.execute("""
            UPDATE requerimientos SET
                mem_requi = %s,
                fecha_memo_requi = %s,
                unid_requirente = %s,
                funcionario_encargado = %s,
                memo_vice_ad = %s,
                fecha_memo_vice_ad = %s,
                memo_dir_ad = %s,
                fecha_memo_dir_ad = %s,
                fecha_recep_req = %s,
                breve_descr = %s,
                descripcion = %s,
                monto_req = %s
            WHERE id = %s
        """, (
            request.form["mem_requi"],
            request.form["fecha_memo_requi"],
            request.form["unid_requirente"],
            request.form.get("funcionario_encargado"),
            request.form.get("memo_vice_ad"),
            request.form.get("fecha_memo_vice_ad"),
            request.form.get("memo_dir_ad"),
            request.form.get("fecha_memo_dir_ad"),
            request.form.get("fecha_recep_req"),
            request.form.get("breve_descr"),
            request.form["descripcion"],
            request.form["monto_req"],
            requerimiento_id
        ))

        conn.commit()
        cur.close()
        conn.close()

        # 👉 vuelve al listado
        return redirect(url_for("main.listar_requerimientos"))

    else:
        # =====================
        # INSERT
        # =====================
        cur.execute("""
            INSERT INTO requerimientos (
                mem_requi,
                fecha_memo_requi,
                unid_requirente,
                funcionario_encargado,
                memo_vice_ad,
                fecha_memo_vice_ad,
                memo_dir_ad,
                fecha_memo_dir_ad,
                fecha_recep_req,
                breve_descr,
                descripcion,
                monto_req
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            request.form["mem_requi"],
            request.form["fecha_memo_requi"],
            request.form["unid_requirente"],
            request.form.get("funcionario_encargado"),
            request.form.get("memo_vice_ad"),
            request.form.get("fecha_memo_vice_ad"),
            request.form.get("memo_dir_ad"),
            request.form.get("fecha_memo_dir_ad"),
            request.form.get("fecha_recep_req"),
            request.form.get("breve_descr"),
            request.form["descripcion"],
            request.form["monto_req"]
        ))

        nuevo_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        # 👉 luego de crear, lo mandamos a editar (para partidas)
        return redirect(url_for("main.editar_requerimiento", id=nuevo_id))
# ===============================
# EDITAR REQUERIMIENTOS
# ===============================    
@main.route("/requerimientos/<int:id>")
@login_required(role=None)
def editar_requerimiento(id):
    conn = get_connection()
    cur = conn.cursor()

    # Requerimiento (columnas explícitas)
    cur.execute("""
        SELECT
            id,
            mem_requi,
            fecha_memo_requi,
            unid_requirente,
            funcionario_encargado,
            memo_vice_ad,
            fecha_memo_vice_ad,
            memo_dir_ad,
            fecha_memo_dir_ad,
            fecha_recep_req,
            breve_descr,
            descripcion,
            monto_req
        FROM requerimientos
        WHERE id = %s
    """, (id,))

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return redirect(url_for("main.listar_requerimientos"))

    # 🔑 convertir a dict
    requerimiento = {
        "id": row[0],
        "mem_requi": row[1],
        "fecha_memo_requi": row[2],
        "unid_requirente": row[3],
        "funcionario_encargado": row[4],
        "memo_vice_ad": row[5],
        "fecha_memo_vice_ad": row[6],
        "memo_dir_ad": row[7],
        "fecha_memo_dir_ad": row[8],
        "fecha_recep_req": row[9],
        "breve_descr": row[10],
        "descripcion": row[11],
        "monto_req": row[12],
    }

    # Unidades
    cur.execute("SELECT id, nombre_unidad FROM unidades ORDER BY nombre_unidad")
    unidades = cur.fetchall()

    # Funcionarios
    cur.execute("SELECT nombre FROM usuarios ORDER BY nombre")
    funcionarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "requerimientos/requerimiento_form.html",
        requerimiento=requerimiento,
        unidades=unidades,
        funcionarios=funcionarios
    )

# ===============================
# INGRESAR PARTIDAS A REQUERIMIENTOS
# ===============================
@main.route("/requerimientos/<int:requerimiento_id>/partidas")
@login_required(role=None)
def partidas_requerimiento(requerimiento_id):
    conn = get_connection()
    cur = conn.cursor()

    # Partidas
    cur.execute("""
        SELECT id, nombre_part, num_part, programa, fuente, monto
        FROM partidas
        WHERE requerimiento_id = %s
        ORDER BY id
    """, (requerimiento_id,))
    partidas = cur.fetchall()

    # 🔢 Total de partidas
    cur.execute("""
        SELECT COALESCE(SUM(monto), 0)
        FROM partidas
        WHERE requerimiento_id = %s
    """, (requerimiento_id,))
    total_partidas = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "requerimientos/partidas_form.html",
        requerimiento_id=requerimiento_id,
        partidas=partidas,
        total_partidas=total_partidas
    )
@main.route('/partidas/editar/<int:id_partida>')
@login_required(role=None)
def partida_editar(id_partida):
    conn = get_connection()
    cur = conn.cursor()

    # Partida a editar
    cur.execute("""
        SELECT id, nombre_part, num_part, programa, fuente, monto, requerimiento_id
        FROM partidas
        WHERE id = %s
    """, (id_partida,))
    partida = cur.fetchone()

    # Partidas del mismo requerimiento
    cur.execute("""
        SELECT id, nombre_part, num_part, programa, fuente, monto
        FROM partidas
        WHERE requerimiento_id = %s
        ORDER BY id
    """, (partida[6],))
    partidas = cur.fetchall()

    # Total
    cur.execute("""
        SELECT COALESCE(SUM(monto), 0)
        FROM partidas
        WHERE requerimiento_id = %s
    """, (partida[6],))
    total_partidas = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "requerimientos/partidas_form.html",
        partida=partida,
        partidas=partidas,
        total_partidas=total_partidas,
        requerimiento_id=partida[6]
    )
@main.route('/partidas/eliminar/<int:id_partida>')
@login_required(role=None)
def partida_eliminar(id_partida):
    conn = get_connection()
    cur = conn.cursor()

    # Obtener requerimiento_id
    cur.execute("""
        SELECT requerimiento_id
        FROM partidas
        WHERE id = %s
    """, (id_partida,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        flash("❌ La partida no existe.", "danger")
        return redirect(url_for("main.partidas_requerimiento", requerimiento_id=0))

    requerimiento_id = row[0]

    # 🔒 VALIDACIÓN: ¿la partida está siendo usada en tareas?
    cur.execute("""
        SELECT COUNT(*)
        FROM tareas
        WHERE partida_id = %s
    """, (id_partida,))
    en_uso = cur.fetchone()[0]

    if en_uso > 0:
        cur.close()
        conn.close()
        flash(
            "⚠️ No se puede eliminar la partida porque ya está asociada a una o más tareas.",
            "warning"
        )
        return redirect(
            url_for("main.partidas_requerimiento", requerimiento_id=requerimiento_id)
        )

    # 🗑️ Eliminar partida (seguro)
    cur.execute("""
        DELETE FROM partidas
        WHERE id = %s
    """, (id_partida,))

    conn.commit()
    cur.close()
    conn.close()

    flash("✅ Partida eliminada correctamente.", "success")

    return redirect(
        url_for("main.partidas_requerimiento", requerimiento_id=requerimiento_id)
    )

# ===============================
# GUARDAR PARTIDAS REQUERIMIENTOS
# ===============================
@main.route("/requerimientos/<int:requerimiento_id>/partidas/guardar", methods=["POST"])
@login_required(role=None)
def guardar_partida(requerimiento_id):
    conn = get_connection()
    cur = conn.cursor()

    id_partida = request.form.get("id_partida")

    if id_partida:
        # 🔄 UPDATE (editar partida)
        cur.execute("""
            UPDATE partidas
            SET nombre_part = %s,
                num_part = %s,
                programa = %s,
                fuente = %s,
                monto = %s
            WHERE id = %s
        """, (
            request.form["nombre_part"],
            request.form["num_part"],
            request.form["programa"],
            request.form["fuente"],
            request.form["monto"],
            id_partida
        ))
    else:
        # ➕ INSERT (nueva partida)
        cur.execute("""
            INSERT INTO partidas (nombre_part, num_part, programa, fuente, monto, requerimiento_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            request.form["nombre_part"],
            request.form["num_part"],
            request.form["programa"],
            request.form["fuente"],
            request.form["monto"],
            requerimiento_id
        ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(
        url_for("main.partidas_requerimiento", requerimiento_id=requerimiento_id)
    )

# ===============================
# ELIMINAR REQUERIMIENTOS
# ===============================
@main.route("/requerimientos/eliminar/<int:id>", methods=["POST"])
@login_required(role=None)
def eliminar_requerimiento(id):
    conn = get_connection()
    cur = conn.cursor()

    # 1️⃣ Eliminar partidas asociadas
    cur.execute("""
        DELETE FROM partidas
        WHERE requerimiento_id = %s
    """, (id,))

    # 2️⃣ Eliminar requerimiento
    cur.execute("""
        DELETE FROM requerimientos
        WHERE id = %s
    """, (id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("main.listar_requerimientos"))

# =================
# NUEVA TAREAS
# ================
@main.route("/tareas/nueva")
@login_required()
def tareas_nueva():
    conn = get_connection()
    cur = conn.cursor()

    # Requerimientos (para memo)
    cur.execute("""
        SELECT id, memo_vice_ad
        FROM requerimientos
        ORDER BY memo_vice_ad
    """)
    requerimientos = cur.fetchall()

    # Tipos de proceso
    cur.execute("""
        SELECT id, nombre_proceso
        FROM tipo_procesos
        ORDER BY nombre_proceso
    """)
    tipos_proceso = cur.fetchall()

    # Tipos de régimen
    cur.execute("""
        SELECT id, nombre_regimen
        FROM tipo_regimen
        ORDER BY nombre_regimen
    """)
    tipos_regimen = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "tareas/tareas_form.html",
        requerimientos=requerimientos,
        tipos_proceso=tipos_proceso,
        tipos_regimen=tipos_regimen
    )
# =================
# EDITAR TAREAS
# =================
@main.route("/tareas/editar/<int:id>")
@login_required()
def tareas_editar(id):
    conn = get_connection()
    cur = conn.cursor()
    # 🔹 Requerimientos (para memo)
    cur.execute("""
    SELECT id, memo_vice_ad
    FROM requerimientos
    ORDER BY memo_vice_ad
    """)
    requerimientos = cur.fetchall()

    # 🔹 Traer la tarea
    cur.execute("""
    SELECT
        id,                         -- 0
        tipo_proceso,               -- 1
        estado_requerimiento,       -- 2
        objeto_contratacion,        -- 3
        codigo_proceso,             -- 4
        fecha_recepcion,            -- 5
        valor_sin_iva,              -- 6
        valor_exento,               -- 7
        valor_en_letras,            -- 8
        tipo_regimen,               -- 9
        base_legal,                 -- 10
        observaciones,              -- 11
        funcionario_encargado,      -- 12
        unidad_solicitante,         -- 13
        requerimiento_id,           -- 14

        -- 🔹 GESTIÓN DE OBSERVACIONES
        fecha_envio_observaciones,  -- 15
        fecha_correccion_observacion, -- 16
        nombre_jefe_compras,        -- 17

        -- 🔹 VERIFICACIÓN DOCUMENTAL (BOOLEANOS)
        presenta_estudio_previo,        -- 18
        presenta_terminos_referencia,   -- 19
        presenta_estudio_mercado,       -- 20
        presenta_especificaciones,      -- 21
        presenta_proformas,             -- 22
        determinacion_necesidad,        -- 23
        consta_catalogo_electronico,    -- 24
        consta_poa,                     -- 25
        consta_pac,                     -- 26
        presenta_errores,               -- 27
        cumple_normativa                -- 28
          -- 🔹 NUEVOS CAMPOS
        presenta_planos,                -- 29
        presenta_apus,                  -- 30
        presenta_condiciones_contratacion, -- 31
        presenta_viabilidad_tecnico_economica -- 32
    FROM tareas
    WHERE id = %s
""", (id,))

    tarea = cur.fetchone()

    if not tarea:
        conn.close()
        flash("Tarea no encontrada", "danger")
        return redirect(url_for("main.tareas"))

    # 🔹 Traer combos (ESTO FALTABA)
    cur.execute("SELECT id, nombre_proceso FROM tipo_procesos ORDER BY nombre_proceso")
    tipos_proceso = cur.fetchall()

    cur.execute("SELECT id, nombre_regimen FROM tipo_regimen ORDER BY nombre_regimen")
    tipos_regimen = cur.fetchall()

    conn.close()

    return render_template(
        "tareas/tareas_form.html",
        tarea=tarea,
        requerimientos=requerimientos,
        tipos_proceso=tipos_proceso,
        tipos_regimen=tipos_regimen
    )
# =================
# GUARDAR / EDITAR TAREAS (SIN DUPLICAR)
# =================
def to_decimal(valor):
    try:
        if valor in (None, "", " "):
            return 0
        return float(valor)
    except Exception:
        return 0

def to_bool(name):
    return True if request.form.get(name) == "on" else False


@main.route("/tareas/guardar", methods=["POST"])
@login_required()
def guardar_tarea():
    conn = get_connection()
    cur = conn.cursor()

    # -------------------------
    # 1) TOMAR ID (SI VIENE)
    # -------------------------
    tarea_id_raw = request.form.get("id", "").strip()
    tarea_id = int(tarea_id_raw) if tarea_id_raw.isdigit() else None

    # Debug opcional:
    print("ID RECIBIDO:", tarea_id)

    # -------------------------
    # 2) CAMPOS PRINCIPALES
    # -------------------------
    codigo_proceso = (request.form.get("codigo_proceso") or "").strip()
    nombre_jefe = (request.form.get("nombre_jefe_compras") or "").strip()
    tipo_compra = (request.form.get("tipo_compra") or "").strip()

    # -------------------------
    # 3) PROTEGER NOMBRE JEFE (EDICIÓN)
    # -------------------------
    if tarea_id and not nombre_jefe:
        cur.execute("SELECT nombre_jefe_compras FROM tareas WHERE id = %s", (tarea_id,))
        row = cur.fetchone()
        if row and row[0]:
            nombre_jefe = row[0]

    # Si es NUEVA tarea, jefe es obligatorio
    if not tarea_id and not nombre_jefe:
        flash("⚠️ Debe ingresar el nombre del Jefe de Compras Públicas.", "danger")
        cur.close()
        conn.close()
        return redirect(url_for("main.tareas_nueva"))

    # -------------------------
    # 4) CHECKBOX
    # -------------------------
    presenta_estudio_previo = to_bool("presenta_estudio_previo")
    presenta_terminos_referencia = to_bool("presenta_terminos_referencia")
    presenta_estudio_mercado = to_bool("presenta_estudio_mercado")
    presenta_especificaciones = to_bool("presenta_especificaciones")
    presenta_proformas = to_bool("presenta_proformas")
    determinacion_necesidad = to_bool("determinacion_necesidad")
    consta_catalogo_electronico = to_bool("consta_catalogo_electronico")
    consta_poa = to_bool("consta_poa")
    consta_pac = to_bool("consta_pac")
    presenta_errores = to_bool("presenta_errores")
    cumple_normativa = to_bool("cumple_normativa")

    # SOLO OBRAS
    presenta_planos = to_bool("presenta_planos")
    presenta_apus = to_bool("presenta_apus")
    presenta_condiciones_contratacion = to_bool("presenta_condiciones_contratacion")

    # SOLO CEP
    presenta_viabilidad_tecnico_economica = to_bool("presenta_viabilidad_tecnico_economica")

    # -------------------------
    # 5) VALIDAR CÓDIGO REPETIDO
    # -------------------------
    if codigo_proceso:
        if tarea_id:
            cur.execute(
                "SELECT 1 FROM tareas WHERE codigo_proceso = %s AND id <> %s",
                (codigo_proceso, tarea_id)
            )
        else:
            cur.execute(
                "SELECT 1 FROM tareas WHERE codigo_proceso = %s",
                (codigo_proceso,)
            )

        if cur.fetchone():
            flash("⚠️ Código de proceso repetido", "danger")
            cur.close()
            conn.close()
            return redirect(
                url_for("main.tareas_editar", id=tarea_id) if tarea_id else url_for("main.tareas_nueva")
            )

    # -------------------------
    # 6) SI HAY ID -> ASEGURAR QUE EXISTA (ANTI-DUPLICADO)
    # -------------------------
    if tarea_id:
        cur.execute("SELECT 1 FROM tareas WHERE id = %s", (tarea_id,))
        if not cur.fetchone():
            # Si llega un id inválido, NO INSERTES JAMÁS (evita duplicación)
            flash("⚠️ No se pudo editar: el ID de la tarea no existe o no llegó correctamente.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("main.tareas"))

        # =========================
        # UPDATE (EDITAR)
        # =========================
        cur.execute("""
            UPDATE tareas SET
                tipo_proceso = %s,
                estado_requerimiento = %s,
                objeto_contratacion = %s,
                codigo_proceso = %s,
                fecha_recepcion = %s,
                valor_sin_iva = %s,
                valor_exento = %s,
                valor_en_letras = %s,
                tipo_regimen = %s,
                tipo_compra = %s,
                base_legal = %s,
                observaciones = %s,
                funcionario_encargado = %s,
                nombre_jefe_compras = %s,
                unidad_solicitante = %s,
                requerimiento_id = %s,

                presenta_estudio_previo = %s,
                presenta_terminos_referencia = %s,
                presenta_estudio_mercado = %s,
                presenta_especificaciones = %s,
                presenta_proformas = %s,
                determinacion_necesidad = %s,
                consta_catalogo_electronico = %s,
                consta_poa = %s,
                consta_pac = %s,
                presenta_errores = %s,
                cumple_normativa = %s,

                presenta_planos = %s,
                presenta_apus = %s,
                presenta_condiciones_contratacion = %s,
                presenta_viabilidad_tecnico_economica = %s
            WHERE id = %s
        """, (
            request.form.get("tipo_proceso"),
            request.form.get("estado_requerimiento"),
            request.form.get("objeto_contratacion"),
            codigo_proceso,
            request.form.get("fecha_recepcion"),
            to_decimal(request.form.get("valor_sin_iva")),
            to_decimal(request.form.get("valor_exento")),
            request.form.get("valor_en_letras"),
            request.form.get("tipo_regimen"),
            tipo_compra,
            request.form.get("base_legal"),
            request.form.get("observaciones"),
            request.form.get("funcionario_encargado"),
            nombre_jefe,
            request.form.get("unidad_solicitante"),
            request.form.get("requerimiento_id"),

            presenta_estudio_previo,
            presenta_terminos_referencia,
            presenta_estudio_mercado,
            presenta_especificaciones,
            presenta_proformas,
            determinacion_necesidad,
            consta_catalogo_electronico,
            consta_poa,
            consta_pac,
            presenta_errores,
            cumple_normativa,

            presenta_planos,
            presenta_apus,
            presenta_condiciones_contratacion,
            presenta_viabilidad_tecnico_economica,

            tarea_id
        ))

        flash("✅ Tarea actualizada correctamente", "success")

    else:
        # =========================
        # INSERT (NUEVA)
        # =========================
        cur.execute("""
            INSERT INTO tareas (
                tipo_proceso, estado_requerimiento, objeto_contratacion,
                codigo_proceso, fecha_recepcion,
                valor_sin_iva, valor_exento, valor_en_letras,
                tipo_regimen, tipo_compra, base_legal, observaciones,
                funcionario_encargado, nombre_jefe_compras, unidad_solicitante,
                requerimiento_id,

                presenta_estudio_previo,
                presenta_terminos_referencia,
                presenta_estudio_mercado,
                presenta_especificaciones,
                presenta_proformas,
                determinacion_necesidad,
                consta_catalogo_electronico,
                consta_poa,
                consta_pac,
                presenta_errores,
                cumple_normativa,

                presenta_planos,
                presenta_apus,
                presenta_condiciones_contratacion,
                presenta_viabilidad_tecnico_economica
            )
            VALUES (
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,

                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,

                %s,%s,%s,%s,%s
            )
        """, (
            request.form.get("tipo_proceso"),
            request.form.get("estado_requerimiento"),
            request.form.get("objeto_contratacion"),
            codigo_proceso,
            request.form.get("fecha_recepcion"),
            to_decimal(request.form.get("valor_sin_iva")),
            to_decimal(request.form.get("valor_exento")),
            request.form.get("valor_en_letras"),
            request.form.get("tipo_regimen"),
            tipo_compra,
            request.form.get("base_legal"),
            request.form.get("observaciones"),
            request.form.get("funcionario_encargado"),
            nombre_jefe,
            request.form.get("unidad_solicitante"),
            request.form.get("requerimiento_id"),

            presenta_estudio_previo,
            presenta_terminos_referencia,
            presenta_estudio_mercado,
            presenta_especificaciones,
            presenta_proformas,
            determinacion_necesidad,
            consta_catalogo_electronico,
            consta_poa,
            consta_pac,
            presenta_errores,
            cumple_normativa,

            presenta_planos,
            presenta_apus,
            presenta_condiciones_contratacion,
            presenta_viabilidad_tecnico_economica
        ))

        flash("✅ Tarea guardada correctamente", "success")

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("main.tareas"))

# =================
# LISTAR  TAREAS
# ================
@main.route("/tareas")
@login_required()
def tareas():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        t.id,
        t.codigo_proceso,
        t.objeto_contratacion,
        tp.nombre_proceso,
        t.estado_requerimiento,
        t.fecha_recepcion
    FROM tareas t
    LEFT JOIN tipo_procesos tp
        ON t.tipo_proceso = tp.id::TEXT
    ORDER BY t.id DESC
""")


    tareas = cur.fetchall()
    conn.close()

    return render_template("tareas_list.html", tareas=tareas)

# =================
# ELIMINAR  TAREAS
# ================
@main.route("/tareas/eliminar/<int:id>", methods=["POST"])
@login_required()
def tareas_eliminar(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM tareas WHERE id = %s", (id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("🗑️ Tarea eliminada correctamente", "success")
    return redirect(url_for("main.tareas"))

# =================
# DEVUELVE DATOS  TAREAS
# ================
@main.route("/api/requerimiento/<int:requerimiento_id>")
@login_required()
def api_requerimiento(requerimiento_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.nombre_unidad, r.funcionario_encargado
        FROM requerimientos r
        JOIN unidades u ON u.id = r.unid_requirente
        WHERE r.id = %s
    """, (requerimiento_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return {
            "unidad": row[0],
            "funcionario": row[1]
        }

    return {}
# =========================
# LISTADO ORDENES DE COMPRA
# =========================
@main.route("/ordenes_compra")
@login_required()
def ordenes_compra():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            numero_oc,
            fecha,
            proveedor,
            total
        FROM ordenes_compra
        ORDER BY fecha DESC
    """)

    ordenes = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "ordenes_compra/ordenes_compra_list.html",
        ordenes=ordenes
    )
# =========================
# PDF ORDEN DE COMPRA
# =========================
@main.route("/ordenes_compra/pdf/<int:id>")
@login_required()
def orden_compra_pdf(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM ordenes_compra
        WHERE id = %s
    """, (id,))
    orden = cur.fetchone()

    cur.execute("""
        SELECT
            id,
            descripcion,
            unidad,
            cantidad,
            valor_uni,
            cantidad * valor_uni AS valor_total,
            cpc
        FROM productos
        WHERE orden_compra_id = %s
        ORDER BY id
    """, (id,))
    productos = cur.fetchall()

    cur.close()
    conn.close()

    if not orden:
        abort(404)

    buffer = generar_pdf_orden_compra(orden, productos)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"orden_compra_{id}.pdf",
        mimetype="application/pdf"
    )
# =========================
# NUEVA ORDEN DE COMPRA
# =========================
@main.route("/ordenes_compra/nueva")
@login_required()
def ordenes_compra_nueva():
    conn = get_connection()
    cur = conn.cursor()

    # Para asociar a una tarea (solo referencia)
    cur.execute("""
            SELECT
            t.id,
            t.codigo_proceso,
            r.memo_vice_ad
        FROM tareas t
        JOIN requerimientos r ON r.id = t.requerimiento_id
        ORDER BY t.codigo_proceso
    """)
    tareas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "ordenes_compra/ordenes_compra_form.html",
         tareas=tareas,
        orden=None,
        items=[]
    )
# =========================
# GUARDAR ORDEN DE COMPRA
# =========================
@main.route("/ordenes_compra/guardar", methods=["POST"])
@login_required()
def ordenes_compra_guardar():

    conn = get_connection()
    cur = conn.cursor()

    orden_id = request.form.get("id")  # 🔑 CLAVE

    # ============================
    # 1️⃣ VALIDACIÓN DE CAMPOS OBLIGATORIOS
    # ============================
    campos_obligatorios = {
        "tarea_id": "Proceso asociado",
        "numero_oc": "Número de Orden de Compra",
        "fecha": "Fecha",
        "area_requirente": "Área requirente",
        "objeto": "Objeto de contratación",
        "proveedor": "Proveedor",
        "ruc": "RUC"
    }

    faltantes = []
    for campo, nombre in campos_obligatorios.items():
        valor = request.form.get(campo)
        if not valor or not valor.strip():
            faltantes.append(nombre)

    if faltantes:
        mensaje = "🚨 FALTA DE LLENAR LOS SIGUIENTES CAMPOS:<br>" + "<br>".join(
            f"• {c}" for c in faltantes
        )
        flash(mensaje, "danger")
        cur.close()
        conn.close()
        return redirect(request.referrer)

    try:
        # ============================
        # 2️⃣ INSERT o UPDATE CABECERA
        # ============================
        if orden_id:  # ✏️ EDITAR
            cur.execute("""
                UPDATE ordenes_compra SET
                    numero_oc=%s, fecha=%s, area_requirente=%s, cert_presupuestaria=%s,
                    objeto=%s, proveedor=%s, ruc=%s, telefono=%s, direccion=%s, correo=%s,
                    proforma_num=%s, proforma_fecha=%s, contacto=%s, vigencia=%s,
                    forma_pago=%s, plazo_ejecucion=%s, lugar_entrega=%s,
                    administrador_orden=%s,
                    maxima_autoridad=%s,
                    cargo_maxima_autoridad=%s,
                    subtotal=%s, iva=%s, total=%s,
                    observaciones=%s, tarea_id=%s
                WHERE id=%s
            """, (
                request.form["numero_oc"],
                request.form["fecha"],
                request.form["area_requirente"],
                request.form["cert_presupuestaria"],
                request.form["objeto"],
                request.form["proveedor"],
                request.form["ruc"],
                request.form["telefono"],
                request.form["direccion"],
                request.form["correo"],
                request.form["proforma_num"],
                request.form["proforma_fecha"],
                request.form["contacto"],
                request.form["vigencia"],
                request.form["forma_pago"],
                request.form["plazo_ejecucion"],
                request.form["lugar_entrega"],
                request.form["administrador_orden"],
                request.form.get("maxima_autoridad"),
                request.form.get("cargo_maxima_autoridad"),
                request.form.get("subtotal", 0),
                request.form.get("iva", 0),
                request.form.get("total", 0),
                request.form.get("observaciones"),
                request.form["tarea_id"],
                orden_id
            ))

            # 🧹 borrar ítems anteriores
            cur.execute("DELETE FROM productos WHERE orden_compra_id = %s", (orden_id,))
            orden_compra_id = orden_id

        else:  # ➕ NUEVA
            cur.execute("""
                INSERT INTO ordenes_compra (
                    numero_oc, fecha, area_requirente, cert_presupuestaria,
                    objeto, proveedor, ruc, telefono, direccion, correo,
                    proforma_num, proforma_fecha, contacto, vigencia,
                    forma_pago, plazo_ejecucion, lugar_entrega,
                    administrador_orden,
                    maxima_autoridad,
                    cargo_maxima_autoridad,
                    subtotal, iva, total,
                    observaciones, tarea_id
                )
                VALUES (
                    %s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,
                    %s,%s,%s,
                    %s,
                    %s,
                    %s,    
                    %s,%s,%s,
                    %s,%s
                )
                RETURNING id
            """, (
                request.form["numero_oc"],
                request.form["fecha"],
                request.form["area_requirente"],
                request.form["cert_presupuestaria"],
                request.form["objeto"],
                request.form["proveedor"],
                request.form["ruc"],
                request.form["telefono"],
                request.form["direccion"],
                request.form["correo"],
                request.form["proforma_num"],
                request.form["proforma_fecha"],
                request.form["contacto"],
                request.form["vigencia"],
                request.form["forma_pago"],
                request.form["plazo_ejecucion"],
                request.form["lugar_entrega"],
                request.form["administrador_orden"],
                request.form.get("maxima_autoridad"),
                request.form.get("cargo_maxima_autoridad"),
                request.form.get("subtotal", 0),
                request.form.get("iva", 0),
                request.form.get("total", 0),
                request.form.get("observaciones"),
                request.form["tarea_id"]
            ))

            orden_compra_id = cur.fetchone()[0]

        # ============================
        # 3️⃣ GUARDAR ÍTEMS
        # ============================
        descripciones = request.form.getlist("descripcion[]")
        unidades = request.form.getlist("unidad[]")
        cantidades = request.form.getlist("cantidad[]")
        valores = request.form.getlist("valor_unitario[]")

        cpcs = request.form.getlist("cpc[]")

        for i in range(len(descripciones)):

            if not descripciones[i].strip():
                continue

            cantidad = cantidades[i] if i < len(cantidades) else 0
            valor = valores[i] if i < len(valores) else 0
            unidad = unidades[i] if i < len(unidades) else None
            cpc = cpcs[i] if i < len(cpcs) else None

          
            cur.execute("""
               INSERT INTO productos (
                    descripcion,
                    unidad,
                    cantidad,
                    valor_uni,
                    orden_compra_id,
                    cpc
                )
                VALUES (%s,%s,%s,%s,%s,%s)                
            """, (
                descripciones[i],
                unidad,
                cantidad,
                valor,                
                orden_compra_id,
                cpc
            ))

        conn.commit()
        flash("✅ Orden de Compra guardada correctamente", "success")
        return redirect(url_for("main.ordenes_compra"))

    except Exception as e:
        conn.rollback()
        print("🔥 ERROR OC:", e)   # 👈 AGREGA EST
        flash(f"❌ Error al guardar la Orden de Compra: {e}", "danger")
        return redirect(request.referrer)

    finally:
        cur.close()
        conn.close()


@main.route("/ordenes_compra/eliminar/<int:id>", methods=["POST"])
@login_required()
def ordenes_compra_eliminar(id):
    
    try:
        conn = get_connection()
        print("✔ conexión creada")

        cur = conn.cursor()
        print("✔ cursor creado")

        cur.execute(
            "DELETE FROM productos WHERE orden_compra_id = %s",
            (id,)
        )
        print("Productos eliminados:", cur.rowcount)

        cur.execute(
            "DELETE FROM ordenes_compra WHERE id = %s",
            (id,)
        )
        print("Orden eliminada:", cur.rowcount)

        conn.commit()
        print("✔ commit realizado")

    except Exception as e:
        print("❌ ERROR:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("main.ordenes_compra"))

@main.route("/api/tarea/<int:id>")
@login_required()
def api_tarea(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.codigo_proceso,
            t.objeto_contratacion,
            u.nombre_unidad
        FROM tareas t
        JOIN requerimientos r ON r.id = t.requerimiento_id
        JOIN unidades u ON u.id = r.unid_requirente
        WHERE t.id = %s
    """, (id,))

    row = cur.fetchone()
    print("ROW API TAREA:", row)
    cur.close()
    conn.close()

    if not row:
        return jsonify({}), 404

    return jsonify({
        "codigo_proceso": row[0],
        "objeto": row[1],
        "unidad": row[2]
    })

# ================================
# EDITAR ORDEN DE COMPRA
# ================================
@main.route("/ordenes_compra/editar/<int:id>")
@login_required()
def ordenes_compra_editar(id):
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM ordenes_compra WHERE id=%s", (id,))
        orden = cur.fetchone()

    # Cabecera
        cur.execute("""
        SELECT *
        FROM ordenes_compra
        WHERE id = %s
    """, (id,))
        orden = cur.fetchone()

    # Productos
        cur.execute("""
        SELECT id, descripcion, unidad, cantidad, valor_uni
        FROM productos
        WHERE orden_compra_id = %s
        ORDER BY id
    """, (id,))
        productos = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
        "ordenes_compra/ordenes_compra_form.html",
        orden=orden,
        productos=productos
    )
# =========================
# LISTAR SEGUIMIENTO CONTRATOS CON ALERTAS
# =========================
@main.route("/seguimiento_contratos")
@login_required()
def seguimiento_contratos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            codigo_proceso,
            objeto_contratacion,
            numero_contrato,
            administrador_contrato,
            fecha_fin_estimada,
            estado
        FROM seguimiento_contratos
        ORDER BY id DESC
    """)

    contratos_db = cur.fetchall()

    contratos = []

    hoy = date.today()

    for c in contratos_db:

        dias_restantes = None
        alerta = "Sin fecha"
        color_alerta = "secondary"

        fecha_fin = c[5]

        if fecha_fin:
            dias_restantes = (fecha_fin - hoy).days

            if dias_restantes < 0:
                alerta = f"Vencido hace {abs(dias_restantes)} días"
                color_alerta = "danger"

            elif dias_restantes <= 5:
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "danger"

            elif dias_restantes <= 15:
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "warning"

            elif dias_restantes <= 30:
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "info"

            else:
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "success"

        contratos.append({
            "id": c[0],
            "codigo_proceso": c[1],
            "objeto_contratacion": c[2],
            "numero_contrato": c[3],
            "administrador_contrato": c[4],
            "fecha_fin_estimada": c[5],
            "estado": c[6],
            "dias_restantes": dias_restantes,
            "alerta": alerta,
            "color_alerta": color_alerta
        })

    cur.close()
    conn.close()

    return render_template(
        "seguimiento_contratos/seguimiento_contratos_list.html",
        contratos=contratos
    )
# =========================
# DASHBOARD SEGUIMIENTO CONTRACTUAL
# =========================
@main.route("/seguimiento_contratos/dashboard")
@login_required()
def seguimiento_contratos_dashboard():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            codigo_proceso,
            objeto_contratacion,
            numero_contrato,
            administrador_contrato,
            fecha_fin_estimada,
            estado
        FROM seguimiento_contratos
        ORDER BY fecha_fin_estimada ASC
    """)

    contratos_db = cur.fetchall()

    cur.close()
    conn.close()

    hoy = date.today()

    total_contratos = len(contratos_db)
    activos = 0
    por_vencer_30 = 0
    por_vencer_15 = 0
    por_vencer_5 = 0
    vencidos = 0
    finalizados = 0

    contratos_alerta = []

    for c in contratos_db:

        estado = (c[6] or "").upper()
        fecha_fin = c[5]

        dias_restantes = None
        alerta = "Sin fecha"
        color_alerta = "secondary"

        if estado == "FINALIZADO":
            finalizados += 1
        else:
            activos += 1

        if fecha_fin:

            dias_restantes = (fecha_fin - hoy).days

            if dias_restantes < 0 and estado != "FINALIZADO":
                vencidos += 1
                alerta = f"Vencido hace {abs(dias_restantes)} días"
                color_alerta = "danger"

            elif dias_restantes <= 5 and estado != "FINALIZADO":
                por_vencer_5 += 1
                por_vencer_15 += 1
                por_vencer_30 += 1
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "danger"

            elif dias_restantes <= 15 and estado != "FINALIZADO":
                por_vencer_15 += 1
                por_vencer_30 += 1
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "warning"

            elif dias_restantes <= 30 and estado != "FINALIZADO":
                por_vencer_30 += 1
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "info"

            else:
                alerta = f"Vence en {dias_restantes} días"
                color_alerta = "success"

        if estado != "FINALIZADO" and (
            dias_restantes is not None and dias_restantes <= 30
        ):
            contratos_alerta.append({
                "id": c[0],
                "codigo_proceso": c[1],
                "objeto_contratacion": c[2],
                "numero_contrato": c[3],
                "administrador_contrato": c[4],
                "fecha_fin_estimada": c[5],
                "estado": c[6],
                "dias_restantes": dias_restantes,
                "alerta": alerta,
                "color_alerta": color_alerta
            })

    return render_template(
        "seguimiento_contratos/dashboard_contratos.html",
        total_contratos=total_contratos,
        activos=activos,
        por_vencer_30=por_vencer_30,
        por_vencer_15=por_vencer_15,
        por_vencer_5=por_vencer_5,
        vencidos=vencidos,
        finalizados=finalizados,
        contratos_alerta=contratos_alerta
    )


# =========================
# NUEVO CONTRATO
# =========================
@main.route("/seguimiento_contratos/nuevo")
@login_required()
def seguimiento_contratos_nuevo():

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Tipos de proceso
    cur.execute("""
        SELECT id, nombre_proceso
        FROM tipo_procesos
        ORDER BY nombre_proceso
    """)
    tipos_proceso = cur.fetchall()

    # Unidades
    cur.execute("""
        SELECT id, nombre_unidad
        FROM unidades
        ORDER BY nombre_unidad
    """)
    unidades = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "seguimiento_contratos/seguimiento_contratos_form.html",
        tipos_proceso=tipos_proceso,
        unidades=unidades
    )

@main.route("/seguimiento_contratos/guardar", methods=["POST"])
@login_required()
def seguimiento_contratos_guardar():

    contrato_id = request.form.get("id")

    conn = get_connection()
    cur = conn.cursor()

    try:
        if contrato_id:
            cur.execute("""
                UPDATE seguimiento_contratos
                SET
                    codigo_proceso = %s,
                    objeto_contratacion = %s,
                    numero_contrato = %s,
                    proveedor = %s,
                    ruc = %s,
                    administrador_contrato = %s,
                    correo_administrador = %s,
                    fecha_suscripcion = %s,
                    fecha_inicio = %s,
                    fecha_fin_estimada = %s,
                    plazo_contractual = %s,
                    monto_contractual = %s,
                    unidad_requirente = %s,
                    tipo_procedimiento = %s,
                    estado = %s,
                    observaciones = %s
                WHERE id = %s
            """, (
                request.form.get("codigo_proceso"),
                request.form.get("objeto_contratacion"),
                request.form.get("numero_contrato"),
                request.form.get("proveedor"),
                request.form.get("ruc"),
                request.form.get("administrador_contrato"),
                request.form.get("correo_administrador"),
                request.form.get("fecha_suscripcion") or None,
                request.form.get("fecha_inicio") or None,
                request.form.get("fecha_fin_estimada") or None,
                request.form.get("plazo_contractual") or None,
                request.form.get("monto_contractual") or 0,
                request.form.get("unidad_requirente"),
                request.form.get("tipo_procedimiento"),
                request.form.get("estado"),
                request.form.get("observaciones"),
                contrato_id
            ))

            flash("✅ Contrato actualizado correctamente", "success")

        else:
            cur.execute("""
                INSERT INTO seguimiento_contratos (
                    codigo_proceso,
                    objeto_contratacion,
                    numero_contrato,
                    proveedor,
                    ruc,
                    administrador_contrato,
                    correo_administrador,
                    fecha_suscripcion,
                    fecha_inicio,
                    fecha_fin_estimada,
                    plazo_contractual,
                    monto_contractual,
                    unidad_requirente,
                    tipo_procedimiento,
                    estado,
                    observaciones
                )
                VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s
                )
            """, (
                request.form.get("codigo_proceso"),
                request.form.get("objeto_contratacion"),
                request.form.get("numero_contrato"),
                request.form.get("proveedor"),
                request.form.get("ruc"),
                request.form.get("administrador_contrato"),
                request.form.get("correo_administrador"),
                request.form.get("fecha_suscripcion") or None,
                request.form.get("fecha_inicio") or None,
                request.form.get("fecha_fin_estimada") or None,
                request.form.get("plazo_contractual") or None,
                request.form.get("monto_contractual") or 0,
                request.form.get("unidad_requirente"),
                request.form.get("tipo_procedimiento"),
                request.form.get("estado"),
                request.form.get("observaciones")
            ))

            flash("✅ Contrato registrado correctamente", "success")

        conn.commit()

        return redirect(url_for("main.seguimiento_contratos"))

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al guardar contrato: {e}", "danger")
        return redirect(request.referrer)

    finally:
        cur.close()
        conn.close()
# =========================
# DETALLE PROFESIONAL DEL CONTRATO
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/seguimientos")
@login_required()
def seguimiento_contratos_detalle(contrato_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            sc.id,
            sc.codigo_proceso,
            sc.objeto_contratacion,
            sc.numero_contrato,
            sc.proveedor,
            sc.ruc,
            sc.administrador_contrato,
            sc.correo_administrador,
            sc.fecha_suscripcion,
            sc.fecha_inicio,
            sc.fecha_fin_estimada,
            sc.plazo_contractual,
            sc.monto_contractual,
            sc.unidad_requirente,
            sc.tipo_procedimiento,
            sc.estado,
            sc.observaciones
        FROM seguimiento_contratos sc
        WHERE sc.id = %s
    """, (contrato_id,))
    contrato = cur.fetchone()
    cur.execute("""
        SELECT
            id,
            fecha_seguimiento,
            tipo_gestion,
            descripcion,
            compromiso,
            fecha_compromiso,
            estado
        FROM seguimiento_contrato_detalle
        WHERE contrato_id = %s
        ORDER BY fecha_seguimiento DESC, id DESC
    """, (contrato_id,))
    seguimientos = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            numero_memorando,
            fecha_memorando,
            asunto,
            descripcion,
            archivo_pdf,
            fecha_registro
        FROM contrato_memorandos
        WHERE contrato_id = %s
        ORDER BY fecha_memorando DESC, id DESC
    """, (contrato_id,))

    memorandos = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            tipo_comunicacion,
            fecha_comunicacion,
            asunto,
            participantes,
            descripcion,
            archivo_pdf
        FROM contrato_comunicaciones
        WHERE contrato_id = %s
        ORDER BY fecha_comunicacion DESC, id DESC
    """, (contrato_id,))

    comunicaciones = cur.fetchall()


    cur.execute("""
        SELECT
            id,
            tipo_informe,
            numero_informe,
            fecha_informe,
            asunto,
            descripcion,
            archivo_pdf
        FROM contrato_informes
        WHERE contrato_id = %s
        ORDER BY fecha_informe DESC, id DESC
    """, (contrato_id,))

    informes = cur.fetchall()

    cur.close()
    conn.close()

    if not contrato:
        abort(404)
   
    return render_template(
        "seguimiento_contratos/seguimiento_contratos_detalle.html",
        contrato=contrato,
        seguimientos=seguimientos,
        memorandos=memorandos,
        comunicaciones=comunicaciones,
        informes=informes
    )
# =========================
# NUEVO SEGUIMIENTO
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/seguimientos/nuevo")
@login_required()
def seguimiento_nuevo(contrato_id):

    return render_template(
        "seguimiento_contratos/seguimiento_nuevo.html",
        contrato_id=contrato_id
    )
# =========================
# EDITAR SEGUIMIENTO CONTRATO
# =========================
@main.route("/seguimiento_contratos/editar/<int:contrato_id>")
@login_required()
def seguimiento_contratos_editar(contrato_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT *
        FROM seguimiento_contratos
        WHERE id = %s
    """, (contrato_id,))
    contrato = cur.fetchone()

    cur.execute("""
        SELECT id, nombre_unidad
        FROM unidades
        ORDER BY nombre_unidad
    """)
    unidades = cur.fetchall()

    cur.execute("""
        SELECT id, nombre_proceso
        FROM tipo_procesos
        ORDER BY nombre_proceso
    """)
    tipos_proceso = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "seguimiento_contratos/seguimiento_contratos_form.html",
        contrato=contrato,
        unidades=unidades,
        tipos_proceso=tipos_proceso
    )

# =========================
# NUEVO MEMORANDO
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/memorando/nuevo")
@login_required()
def memorando_nuevo(contrato_id):

    return render_template(
        "seguimiento_contratos/memorando_form.html",
        contrato_id=contrato_id
    )
# =========================
# NUEVA COMUNICACIÓN
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/comunicacion/nueva")
@login_required()
def comunicacion_nueva(contrato_id):

    return render_template(
        "seguimiento_contratos/comunicacion_form.html",
        contrato_id=contrato_id
    )
# =========================
# NUEVO INFORME
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/informe/nuevo")
@login_required()
def informe_nuevo(contrato_id):

    return render_template(
        "seguimiento_contratos/informe_form.html",
        contrato_id=contrato_id
    )


# =========================
# GUARDAR INFORME
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/informe/guardar", methods=["POST"])
@login_required()
def informe_guardar(contrato_id):

    conn = get_connection()
    cur = conn.cursor()

    try:
        archivo_pdf = None

        if "archivo_pdf" in request.files:
            archivo = request.files["archivo_pdf"]

            if archivo.filename:
                from werkzeug.utils import secure_filename

                carpeta = os.path.join(
                    "app",
                    "static",
                    "uploads",
                    "informes"
                )

                os.makedirs(carpeta, exist_ok=True)

                nombre_archivo = secure_filename(archivo.filename)

                archivo.save(
                    os.path.join(carpeta, nombre_archivo)
                )

                archivo_pdf = nombre_archivo

        cur.execute("""
            INSERT INTO contrato_informes (
                contrato_id,
                tipo_informe,
                numero_informe,
                fecha_informe,
                asunto,
                descripcion,
                archivo_pdf
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            contrato_id,
            request.form.get("tipo_informe"),
            request.form.get("numero_informe"),
            request.form.get("fecha_informe"),
            request.form.get("asunto"),
            request.form.get("descripcion"),
            archivo_pdf
        ))

        conn.commit()
        flash("✅ Informe registrado correctamente", "success")

        return redirect(
            url_for(
                "main.seguimiento_contratos_detalle",
                contrato_id=contrato_id
            )
        )

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al guardar informe: {e}", "danger")
        return redirect(request.referrer)

    finally:
        cur.close()
        conn.close()
# =========================
# GUARDAR MEMORANDO
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/memorando/guardar", methods=["POST"])
@login_required()
def memorando_guardar(contrato_id):

    conn = get_connection()
    cur = conn.cursor()

    try:
        archivo_binario = None
        archivo_nombre = None
        archivo_tipo = None

        archivo = request.files.get("archivo_pdf")

        if archivo and archivo.filename:
            from werkzeug.utils import secure_filename

            archivo_nombre = secure_filename(archivo.filename)
            archivo_tipo = archivo.content_type
            archivo_binario = archivo.read()

        cur.execute("""
            INSERT INTO contrato_memorandos (
                contrato_id,
                numero_memorando,
                fecha_memorando,
                asunto,
                descripcion,
                archivo_pdf,
                archivo_binario,
                archivo_nombre,
                archivo_tipo
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            contrato_id,
            request.form.get("numero_memorando"),
            request.form.get("fecha_memorando"),
            request.form.get("asunto"),
            request.form.get("descripcion"),
            archivo_nombre,
            archivo_binario,
            archivo_nombre,
            archivo_tipo
        ))

        conn.commit()

        flash("✅ Memorando registrado correctamente", "success")

        return redirect(url_for(
            "main.seguimiento_contratos_detalle",
            contrato_id=contrato_id
        ))

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error: {e}", "danger")
        return redirect(request.referrer)

    finally:
        cur.close()
        conn.close()
# =========================
# GUARDAR SEGUIMIENTO
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/seguimientos/guardar", methods=["POST"])
@login_required()
def seguimiento_guardar(contrato_id):

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO seguimiento_contrato_detalle (
                contrato_id,
                fecha_seguimiento,
                tipo_gestion,
                descripcion,
                compromiso,
                fecha_compromiso,
                estado
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            contrato_id,
            request.form.get("fecha_seguimiento"),
            request.form.get("tipo_gestion"),
            request.form.get("descripcion"),
            request.form.get("compromiso"),
            request.form.get("fecha_compromiso") or None,
            request.form.get("estado")
        ))

        conn.commit()
        flash("✅ Seguimiento registrado correctamente", "success")

        return redirect(
            url_for("main.seguimiento_contratos_detalle", contrato_id=contrato_id)
        )

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al guardar seguimiento: {e}", "danger")
        return redirect(request.referrer)

    finally:
        cur.close()
        conn.close()

# =========================
# GUARDAR COMUNICACIÓN
# =========================
@main.route(
    "/seguimiento_contratos/<int:contrato_id>/comunicacion/guardar",
    methods=["POST"]
)
@login_required()
def comunicacion_guardar(contrato_id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        archivo_pdf = None

        if "archivo_pdf" in request.files:

            archivo = request.files["archivo_pdf"]

            if archivo.filename:

                from werkzeug.utils import secure_filename

                carpeta = os.path.join(
                    "app",
                    "static",
                    "uploads",
                    "comunicaciones"
                )

                os.makedirs(carpeta, exist_ok=True)

                nombre_archivo = secure_filename(
                    archivo.filename
                )

                archivo.save(
                    os.path.join(carpeta, nombre_archivo)
                )

                archivo_pdf = nombre_archivo

        cur.execute("""
            INSERT INTO contrato_comunicaciones (
                contrato_id,
                tipo_comunicacion,
                fecha_comunicacion,
                asunto,
                participantes,
                descripcion,
                archivo_pdf
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (

            contrato_id,
            request.form.get("tipo_comunicacion"),
            request.form.get("fecha_comunicacion"),
            request.form.get("asunto"),
            request.form.get("participantes"),
            request.form.get("descripcion"),
            archivo_pdf

        ))

        conn.commit()

        flash(
            "✅ Comunicación registrada correctamente",
            "success"
        )

        return redirect(
            url_for(
                "main.seguimiento_contratos_detalle",
                contrato_id=contrato_id
            )
        )

    except Exception as e:

        conn.rollback()

        flash(f"❌ Error: {e}", "danger")

        return redirect(request.referrer)

    finally:

        cur.close()
        conn.close()


# ================================
# INFORME DE VERIFICACIÓN (AUTOMÁTICO)
# ================================
@main.route('/informe/verificacion/<int:id_tarea>')
@login_required()
def informe_verificacion(id_tarea):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            t.*,
            tp.nombre_proceso AS tipo_proceso_nombre
        FROM tareas t
        LEFT JOIN tipo_procesos tp ON t.tipo_proceso::INTEGER = tp.id
        WHERE t.id = %s
    """, (id_tarea,))   
    tarea = cur.fetchone()

    conn.close()

    if not tarea:
        abort(404)

    year = datetime.now().year
    codigo_verificacion = f"UCP-VERF-{year}-{str(id_tarea).zfill(4)}"

    return render_template(
        'verificaciones/informe_verificacion.html',

            fecha=datetime.now().strftime('%d/%m/%Y'),
            codigo_verificacion=codigo_verificacion,

            unidad_solicitante=tarea['unidad_solicitante'],
            funcionario_encargado=tarea['funcionario_encargado'],
            objeto_contratacion=tarea['objeto_contratacion'],
            codigo_proceso=tarea['codigo_proceso'],
            tipo_proceso=tarea['tipo_proceso_nombre'],
            tipo_compra=tarea['tipo_compra'],
            valor_sin_iva=tarea['valor_sin_iva'],
            valor_exento=tarea['valor_exento'],
            valor_en_letras=tarea['valor_en_letras'],

            base_legal="LOSNCP y su Reglamento General",
            observaciones="La documentación cumple con los requisitos formales.",
            nombre_jefe_compras=tarea['nombre_jefe_compras'],
             # 🔹 VERIFICACIÓN DOCUMENTAL
            presenta_estudio_previo=tarea['presenta_estudio_previo'],
            presenta_terminos_referencia=tarea['presenta_terminos_referencia'],
            presenta_estudio_mercado=tarea['presenta_estudio_mercado'],
            presenta_especificaciones=tarea['presenta_especificaciones'],
            presenta_proformas=tarea['presenta_proformas'],
            determinacion_necesidad=tarea['determinacion_necesidad'],
            consta_catalogo_electronico=tarea['consta_catalogo_electronico'],
            consta_poa=tarea['consta_poa'],
            consta_pac=tarea['consta_pac'],
            presenta_errores=tarea['presenta_errores'],
            cumple_normativa=tarea['cumple_normativa'],

            # 🔹 SOLO PARA OBRAS
            presenta_planos=tarea['presenta_planos'],
            presenta_apus=tarea['presenta_apus'],
            presenta_condiciones_contratacion=tarea['presenta_condiciones_contratacion'],

            # 🔹 SOLO CEP
            presenta_viabilidad_tecnico_economica=tarea['presenta_viabilidad_tecnico_economica'],

            # 🔹 PARA CONDICIONAR VISTAS
            tipo_proceso_nombre=tarea['tipo_proceso_nombre'],
            tipo_regimen=tarea['tipo_regimen']
            
        )
  
@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login_form"))
# =========================
# EXPEDIENTE ELECTRÓNICO
# =========================
@main.route("/seguimiento_contratos/<int:contrato_id>/expediente")
@login_required()
def expediente_contrato(contrato_id):

    conn = get_connection()
    cur = conn.cursor()

    # CONTRATO
    cur.execute("""
        SELECT *
        FROM seguimiento_contratos
        WHERE id = %s
    """, (contrato_id,))
    contrato = cur.fetchone()
    
    # MEMORANDOS
    cur.execute("""
        SELECT *
        FROM contrato_memorandos
        WHERE contrato_id = %s
        ORDER BY fecha_memorando DESC
    """, (contrato_id,))
    memorandos = cur.fetchall()
   
    # COMUNICACIONES
    cur.execute("""
        SELECT *
        FROM contrato_comunicaciones
        WHERE contrato_id = %s
        ORDER BY fecha_comunicacion DESC
    """, (contrato_id,))
    comunicaciones = cur.fetchall()

    # INFORMES
    cur.execute("""
        SELECT *
        FROM contrato_informes
        WHERE contrato_id = %s
        ORDER BY fecha_informe DESC
    """, (contrato_id,))
    informes = cur.fetchall()

    # SEGUIMIENTOS
    cur.execute("""
        SELECT *
        FROM seguimiento_contrato_detalle
        WHERE contrato_id = %s
        ORDER BY fecha_seguimiento DESC
    """, (contrato_id,))
    seguimientos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "seguimiento_contratos/expediente_contrato.html",
        contrato=contrato,
        memorandos=memorandos,
        comunicaciones=comunicaciones,
        informes=informes,
        seguimientos=seguimientos
    )
# =========================
# LISTAR UNIDADES
# =========================
@main.route("/unidades")
@login_required()
def unidades_listar():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre_unidad
        FROM unidades
        ORDER BY nombre_unidad
    """)
    unidades = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("catalogos/unidades_list.html", unidades=unidades)


# =========================
# NUEVA UNIDAD
# =========================
@main.route("/unidades/nueva")
@login_required()
def unidades_nueva():
    return render_template("catalogos/unidades_form.html", unidad=None)


# =========================
# GUARDAR UNIDAD
# =========================
@main.route("/unidades/guardar", methods=["POST"])
@login_required()
def unidades_guardar():
    nombre_unidad = request.form.get("nombre_unidad")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO unidades (nombre_unidad)
            VALUES (%s)
        """, (nombre_unidad,))

        conn.commit()
        flash("✅ Unidad registrada correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al guardar unidad: {e}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("main.unidades_listar"))
# =========================
# EDITAR UNIDAD
# =========================
@main.route("/unidades/editar/<int:id>")
@login_required()
def unidades_editar(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre_unidad
        FROM unidades
        WHERE id = %s
    """, (id,))
    unidad = cur.fetchone()

    cur.close()
    conn.close()

    if not unidad:
        abort(404)

    return render_template(
        "catalogos/unidades_form.html",
        unidad=unidad
    )


# =========================
# ACTUALIZAR UNIDAD
# =========================
@main.route("/unidades/actualizar/<int:id>", methods=["POST"])
@login_required()
def unidades_actualizar(id):
    nombre_unidad = request.form.get("nombre_unidad")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE unidades
            SET nombre_unidad = %s
            WHERE id = %s
        """, (nombre_unidad, id))

        conn.commit()
        flash("✅ Unidad actualizada correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Error al actualizar unidad: {e}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("main.unidades_listar"))


# =========================
# ELIMINAR UNIDAD
# =========================
@main.route("/unidades/eliminar/<int:id>")
@login_required()
def unidades_eliminar(id):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM unidades
            WHERE id = %s
        """, (id,))

        conn.commit()
        flash("✅ Unidad eliminada correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ No se pudo eliminar la unidad: {e}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("main.unidades_listar"))
# =========================
# LISTAR TIPOS DE PROCESO
# =========================
@main.route("/tipo_procesos")
@login_required()
def tipo_procesos_listar():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre_proceso
        FROM tipo_procesos
        ORDER BY nombre_proceso
    """)

    tipos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "catalogos/tipo_procesos_list.html",
        tipos=tipos
    )


# =========================
# NUEVO TIPO DE PROCESO
# =========================
@main.route("/tipo_procesos/nuevo")
@login_required()
def tipo_procesos_nuevo():
    return render_template(
        "catalogos/tipo_procesos_form.html",
        tipo=None
    )


# =========================
# GUARDAR TIPO DE PROCESO
# =========================
@main.route("/tipo_procesos/guardar", methods=["POST"])
@login_required()
def tipo_procesos_guardar():

    nombre_proceso = request.form.get("nombre_proceso")

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            INSERT INTO tipo_procesos (
                nombre_proceso
            )
            VALUES (%s)
        """, (nombre_proceso,))

        conn.commit()

        flash(
            "✅ Tipo de proceso registrado correctamente",
            "success"
        )

    except Exception as e:

        conn.rollback()

        flash(
            f"❌ Error: {e}",
            "danger"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("main.tipo_procesos_listar")
    )


# =========================
# EDITAR TIPO DE PROCESO
# =========================
@main.route("/tipo_procesos/editar/<int:id>")
@login_required()
def tipo_procesos_editar(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre_proceso
        FROM tipo_procesos
        WHERE id = %s
    """, (id,))

    tipo = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "catalogos/tipo_procesos_form.html",
        tipo=tipo
    )


# =========================
# ACTUALIZAR TIPO DE PROCESO
# =========================
@main.route("/tipo_procesos/actualizar/<int:id>", methods=["POST"])
@login_required()
def tipo_procesos_actualizar(id):

    nombre_proceso = request.form.get("nombre_proceso")

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE tipo_procesos
            SET nombre_proceso = %s
            WHERE id = %s
        """, (
            nombre_proceso,
            id
        ))

        conn.commit()

        flash(
            "✅ Tipo de proceso actualizado correctamente",
            "success"
        )

    except Exception as e:

        conn.rollback()

        flash(
            f"❌ Error: {e}",
            "danger"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("main.tipo_procesos_listar")
    )


# =========================
# ELIMINAR TIPO DE PROCESO
# =========================
@main.route("/tipo_procesos/eliminar/<int:id>")
@login_required()
def tipo_procesos_eliminar(id):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            DELETE FROM tipo_procesos
            WHERE id = %s
        """, (id,))

        conn.commit()

        flash(
            "✅ Tipo de proceso eliminado correctamente",
            "success"
        )

    except Exception as e:

        conn.rollback()

        flash(
            f"❌ Error: {e}",
            "danger"
        )

    finally:

        cur.close()
        conn.close()

    return redirect(
        url_for("main.tipo_procesos_listar")
    )