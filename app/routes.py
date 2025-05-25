from flask import Blueprint, session, redirect, render_template, request
import psycopg2
import os
main = Blueprint('main', __name__)
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))
@main.route('/')
def index():
    return redirect('/login')

@main.route('/admin_dashboard')
def admin_dashboard():
    if session.get('rol') != 'Administrador':
        return redirect('/login')
    return render_template('admin_dashboard.html', nombre=session.get('user_name'))

@main.route('/admin/usuarios', methods=['GET', 'POST'])
def gestionar_usuarios():
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        rol = request.form['rol']

        cur.execute("""
            INSERT INTO usuarios (nombre, correo, contraseña, rol)
            VALUES (%s, %s, %s, %s)
        """, (nombre, correo, contraseña, rol))
        conn.commit()

    cur.execute("SELECT id, nombre, correo, rol FROM usuarios")
    usuarios = cur.fetchall()
    conn.close()

    return render_template('usuarios_admin.html', usuarios=usuarios)
@main.route('/admin/unidades', methods=['GET', 'POST'])
def gestionar_unidades():
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre_unidad']
        ubicacion = request.form['ubicacion']
        cur.execute("INSERT INTO unidades (nombre_unidad, ubicacion) VALUES (%s, %s)", (nombre, ubicacion))
        conn.commit()

    cur.execute("SELECT id, nombre_unidad, ubicacion FROM unidades")
    unidades = cur.fetchall()
    conn.close()

    return render_template('unidades_admin.html', unidades=unidades)
@main.route('/admin/procesos', methods=['GET', 'POST'])
def gestionar_procesos():
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre_proceso']
        regimen = request.form['tipo_regimen']
        cur.execute("INSERT INTO tipo_procesos (nombre_proceso, tipo_regimen) VALUES (%s, %s)", (nombre, regimen))
        conn.commit()

    cur.execute("SELECT id, nombre_proceso, tipo_regimen FROM tipo_procesos")
    procesos = cur.fetchall()
    conn.close()

    return render_template('procesos_admin.html', procesos=procesos)
@main.route('/admin/productos', methods=['GET', 'POST'])
def gestionar_productos():
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        descripcion = request.form['descripcion']
        unidad = request.form['unidad']
        cantidad = int(request.form['cantidad'])
        valor_uni = float(request.form['valor_uni'])

        cur.execute("""
            INSERT INTO productos (descripcion, unidad, cantidad, valor_uni)
            VALUES (%s, %s, %s, %s)
        """, (descripcion, unidad, cantidad, valor_uni))
        conn.commit()

    cur.execute("SELECT id, descripcion, unidad, cantidad, valor_uni, total FROM productos")
    productos = cur.fetchall()
    conn.close()

    return render_template('productos_admin.html', productos=productos)
@main.route('/admin/requerimientos', methods=['GET', 'POST'])
def gestionar_requerimientos():
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    # Obtener unidades para el selector
    cur.execute("SELECT id, nombre_unidad FROM unidades")
    unidades = cur.fetchall()

    if request.method == 'POST':
        data = (
            request.form['mem_requi'],
            request.form['fecha_memo_requi'],
            request.form['unid_requirente'],
            request.form['memo_vice_ad'],
            request.form['fecha_memo_vice_ad'],
            request.form['memo_dir_ad'],
            request.form['fecha_memo_dir_ad'],
            request.form['fecha_recep_req'],
            request.form['breve_descr'],
            request.form['monto_req']
        )

        cur.execute("""
            INSERT INTO requerimientos (
                mem_requi, fecha_memo_requi, unid_requirente,
                memo_vice_ad, fecha_memo_vice_ad,
                memo_dir_ad, fecha_memo_dir_ad,
                fecha_recep_req, breve_descr, monto_req
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        conn.commit()

    # Obtener todos los requerimientos para listar
    cur.execute("""
        SELECT r.id, r.mem_requi, r.fecha_memo_requi, u.nombre_unidad, r.monto_req
        FROM requerimientos r
        JOIN unidades u ON r.unid_requirente = u.id
    """)
    requerimientos = cur.fetchall()
    conn.close()

    return render_template('requerimientos_admin.html', requerimientos=requerimientos, unidades=unidades)
