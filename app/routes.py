from flask import Blueprint, session, redirect, render_template
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
