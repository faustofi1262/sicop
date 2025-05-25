from flask import Blueprint, session, redirect, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect('/login')

@main.route('/admin_dashboard')
def admin_dashboard():
    if session.get('rol') != 'Administrador':
        return redirect('/login')
    return render_template('admin_dashboard.html', nombre=session.get('user_name'))

@main.route('/analista_dashboard')
def analista_dashboard():
    if session.get('rol') != 'Analista':
        return redirect('/login')
    return render_template('analista_dashboard.html', nombre=session.get('user_name'))

@main.route('/jefe_dashboard')
def jefe_dashboard():
    if session.get('rol') != 'Jefe':
        return redirect('/login')
    return render_template('jefe_dashboard.html', nombre=session.get('user_name'))

@main.route('/invitado_dashboard')
def invitado_dashboard():
    if session.get('rol') != 'Invitado':
        return redirect('/login')
    return render_template('invitado_dashboard.html', nombre=session.get('user_name'))
