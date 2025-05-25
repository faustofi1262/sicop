from flask import Blueprint, render_template, request, redirect, session
import psycopg2
import os

auth = Blueprint('auth', __name__)

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, rol FROM usuarios WHERE correo = %s AND contraseña = %s", (correo, contraseña))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['rol'] = user[2]

            if user[2] == 'Administrador':
                return redirect('/admin_dashboard')
            else:
                return redirect('/login')
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')

    return render_template('login.html')