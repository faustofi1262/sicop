from flask import Blueprint, session, redirect, render_template, request
import psycopg2
import os
from flask import jsonify
import num2words
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

@main.route('/analista_dashboard')
def analista_dashboard():
    if session.get('rol') != 'Analista':
        return redirect('/login')
    return render_template('analista_dashboard.html', nombre=session.get('user_name'))

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
    # Obtener lista de funcionarios desde la tabla usuarios
    cur.execute("SELECT nombre FROM usuarios")
    funcionarios = cur.fetchall()

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
            request.form['monto_req'],
            request.form['funcionario_encargado'] 
        )

        cur.execute("""
            INSERT INTO requerimientos (
                mem_requi, fecha_memo_requi, unid_requirente,
                memo_vice_ad, fecha_memo_vice_ad,
                memo_dir_ad, fecha_memo_dir_ad,
                fecha_recep_req, breve_descr, monto_req, funcionario_encargado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

    return render_template("requerimientos_admin.html",  requerimientos=requerimientos, funcionarios=funcionarios, unidades=unidades)
@main.route('/admin/tareas', methods=['GET', 'POST'])
def tareas():
    conn = get_db_connection()
    cur = conn.cursor()

    # Cargar tipos de proceso
    cur.execute("SELECT nombre_proceso FROM tipo_procesos")
    tipos_proceso = cur.fetchall()

    # Obtener requerimientos para el selector
    cur.execute("""
        SELECT r.id, r.memo_vice_ad, u.nombre_unidad, r.funcionario_encargado
        FROM requerimientos r
        JOIN unidades u ON r.unid_requirente = u.id
    """)
    requerimientos = cur.fetchall()
    if request.method == 'POST':
        imagen = request.files.get('imagen_pac')
        imagen_data = imagen.read() if imagen and imagen.filename else None

        data = (
            request.form['requerimiento_id'],
            request.form['funcionario_encargado'],
            request.form['tipo_proceso'],
            request.form['estado_requerimiento'],
            request.form['objeto_contratacion'],
            request.form['codigo_proceso'],
            request.form['fecha_recepcion'],
            float(request.form.get('valor_sin_iva') or 0),
            float(request.form.get('valor_exento') or 0),
            request.form['valor_en_letras'],
            request.form['tipo_regimen'],
            request.form['base_legal'],
            request.form['observaciones'],
            request.form.get('fecha_envio_observaciones') or None,
            request.form.get('fecha_correccion_observacion') or None,
            request.form['nombre_jefe_compras'],
            request.form['unidad_solicitante'] or None,
            request.form['administrador_contrato'] or None,
            'presenta_estudio_previo' in request.form,
            'presenta_especificaciones' in request.form,
            'presenta_terminos_referencia' in request.form,
            'presenta_proformas' in request.form,
            'presenta_estudio_mercado' in request.form,
            'determinacion_necesidad' in request.form,
            'consta_catalogo_electronico' in request.form,
            'consta_poa' in request.form,
            'consta_pac' in request.form,
            'presenta_errores' in request.form,
            'cumple_normativa' in request.form,
            imagen_data
        )

        cur.execute("""
            INSERT INTO tareas (
                requerimiento_id, funcionario_encargado, tipo_proceso, estado_requerimiento,
                objeto_contratacion, codigo_proceso, fecha_recepcion, valor_sin_iva,
                valor_exento, valor_en_letras, tipo_regimen, base_legal, observaciones,
                fecha_envio_observaciones, fecha_correccion_observacion, nombre_jefe_compras,
                unidad_solicitante, administrador_contrato,
                presenta_estudio_previo, presenta_especificaciones, presenta_terminos_referencia,
                presenta_proformas, presenta_estudio_mercado, determinacion_necesidad,
                consta_catalogo_electronico, consta_poa, consta_pac,
                presenta_errores, cumple_normativa,
                imagen_pac
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        conn.commit()

    cur.execute("""
            INSERT INTO tareas (
                requerimiento_id, funcionario_encargado, tipo_proceso, estado_requerimiento,
                objeto_contratacion, codigo_proceso, fecha_recepcion, valor_sin_iva,
                valor_exento, valor_en_letras, tipo_regimen, base_legal, observaciones,
                fecha_envio_observaciones, fecha_correccion_observacion, nombre_jefe_compras,
                unidad_solicitante, administrador_contrato,
                presenta_estudio_previo, presenta_especificaciones, presenta_terminos_referencia,
                presenta_proformas, presenta_estudio_mercado, determinacion_necesidad,
                consta_catalogo_electronico, consta_poa, consta_pac,
                presenta_errores, cumple_normativa
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
    conn.commit()

    cur.execute("""
        SELECT t.id, r.memo_vice_ad, r.unid_requirente, t.funcionario_encargado,
               t.estado_requerimiento, t.tipo_proceso
        FROM tareas t
        JOIN requerimientos r ON t.requerimiento_id = r.id
    """)
    tareas = cur.fetchall()
    conn.close()

    return render_template('tareas_admin.html', requerimientos=requerimientos, tareas=tareas, tipos_proceso=tipos_proceso)


@main.route('/admin/tareas/eliminar/<int:id>', methods=['POST'])
def eliminar_tarea(id):
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tareas WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin/tareas')
@main.route('/admin/tareas/editar/<int:id>', methods=['GET', 'POST'])
def editar_tarea(id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Obtener requerimientos para selector
    cur.execute("SELECT id, memo_vice_ad, unid_requirente, funcionario_encargado FROM requerimientos")
    requerimientos = cur.fetchall()

    # Obtener tipos de proceso (esto FALTABA si no estaba antes del return)
    cur.execute("SELECT nombre_proceso FROM tipo_procesos")
    tipos_proceso = cur.fetchall()

    # Obtener la tarea a editar
    cur.execute("SELECT * FROM tareas WHERE id = %s", (id,))
    tarea = cur.fetchone()

    if request.method == 'POST':
        data = (
            request.form['funcionario_encargado'],
            request.form['tipo_proceso'],
            request.form['estado_requerimiento'],
            request.form['objeto_contratacion'],
            request.form['codigo_proceso'],
            request.form['fecha_recepcion'],
            float(request.form.get('valor_sin_iva') or 0),
            float(request.form.get('valor_exento') or 0),
            request.form['valor_en_letras'],
            request.form['tipo_regimen'],
            request.form['base_legal'],
            request.form['observaciones'],
            request.form.get('fecha_envio_observaciones') or None,
            request.form.get('fecha_correccion_observacion') or None,
            request.form['nombre_jefe_compras'],
            request.form['unidad_solicitante'] or None,
            request.form['administrador_contrato'] or None,
            'presenta_estudio_previo' in request.form,
            'presenta_especificaciones' in request.form,
            'presenta_terminos_referencia' in request.form,
            'presenta_proformas' in request.form,
            'presenta_estudio_mercado' in request.form,
            'determinacion_necesidad' in request.form,
            'consta_catalogo_electronico' in request.form,
            'consta_poa' in request.form,
            'consta_pac' in request.form,
            'presenta_errores' in request.form,
            'cumple_normativa' in request.form,
            id
        )
        cur.execute("""
            UPDATE tareas SET
                funcionario_encargado=%s, tipo_proceso=%s, estado_requerimiento=%s,
                objeto_contratacion=%s, codigo_proceso=%s, fecha_recepcion=%s,
                valor_sin_iva=%s, valor_exento=%s, valor_en_letras=%s,
                tipo_regimen=%s, base_legal=%s, observaciones=%s,
                fecha_envio_observaciones=%s, fecha_correccion_observacion=%s,
                nombre_jefe_compras=%s, unidad_solicitante=%s, administrador_contrato=%s,
                presenta_estudio_previo=%s, presenta_especificaciones=%s,
                presenta_terminos_referencia=%s, presenta_proformas=%s,
                presenta_estudio_mercado=%s, determinacion_necesidad=%s,
                consta_catalogo_electronico=%s, consta_poa=%s,
                consta_pac=%s, presenta_errores=%s, cumple_normativa=%s
            WHERE id=%s
        """, data)
        conn.commit()
        conn.close()
        return redirect('/admin/tareas')

    conn.close()
    return render_template('editar_tarea.html', requerimientos=requerimientos, tarea=tarea, tipos_proceso=tipos_proceso)
@main.route('/convertir_a_letras')
def convertir_a_letras():
    valor = float(request.args.get("valor", 0))
    letras = num2words.num2words(valor, lang='es').capitalize()
    return letras
@main.route('/admin/requerimientos/editar/<int:id>', methods=['GET', 'POST'])
def editar_requerimiento(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, nombre_unidad FROM unidades")
    unidades = cur.fetchall()

    cur.execute("SELECT nombre FROM usuarios")
    funcionarios = cur.fetchall()

    cur.execute("SELECT * FROM requerimientos WHERE id = %s", (id,))
    req = cur.fetchone()

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
            request.form['monto_req'],
            request.form['funcionario_encargado'],
            id
        )
        cur.execute("""
            UPDATE requerimientos SET
                mem_requi=%s, fecha_memo_requi=%s, unid_requirente=%s,
                memo_vice_ad=%s, fecha_memo_vice_ad=%s,
                memo_dir_ad=%s, fecha_memo_dir_ad=%s,
                fecha_recep_req=%s, breve_descr=%s, monto_req=%s,
                funcionario_encargado=%s
            WHERE id=%s
        """, data)
        conn.commit()
        conn.close()
        return redirect('/admin/requerimientos')

    conn.close()
    return render_template('editar_requerimiento.html', req=req, unidades=unidades, funcionarios=funcionarios)
#AGREGAR BOTON ELIMINAR REQUERIMIENTO
@main.route('/admin/requerimientos/eliminar/<int:id>', methods=['POST'])
def eliminar_requerimiento(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM requerimientos WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/requerimientos')

#agrega botn para agregar partidas
@main.route('/admin/requerimientos/<int:req_id>/partidas', methods=['GET', 'POST'])
def gestionar_partidas(req_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre_part = request.form['nombre_part']
        num_part = request.form['num_part']
        fuente = request.form['fuente']
        programa = request.form['programa']
        monto = request.form['monto']

        cur.execute("""
            INSERT INTO partidas (requerimiento_id, nombre_part, num_part, fuente, programa, monto)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (req_id, nombre_part, num_part, fuente, programa, monto))
        conn.commit()

    cur.execute("""
        SELECT id, nombre_part, num_part, fuente, programa, monto
        FROM partidas
        WHERE requerimiento_id = %s
        ORDER BY id ASC
    """, (req_id,))
    partidas = cur.fetchall()
    conn.close()

    return render_template("partidas_form.html", partidas=partidas, req_id=req_id)
@main.route('/admin/partidas/editar/<int:partida_id>', methods=['GET', 'POST'])
def editar_partida(partida_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre_part = request.form['nombre_part']
        num_part = request.form['num_part']
        fuente = request.form['fuente']
        programa = request.form['programa']
        monto = request.form['monto']

        cur.execute("""
            UPDATE partidas
            SET nombre_part=%s, num_part=%s, fuente=%s, programa=%s, monto=%s
            WHERE id=%s
        """, (nombre_part, num_part, fuente, programa, monto, partida_id))
        conn.commit()
        conn.close()
        return redirect(request.referrer)

    cur.execute("SELECT * FROM partidas WHERE id = %s", (partida_id,))
    partida = cur.fetchone()
    conn.close()
    return render_template('editar_partida.html', partida=partida)


@main.route('/admin/partidas/eliminar/<int:partida_id>', methods=['POST'])
def eliminar_partida(partida_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM partidas WHERE id = %s", (partida_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer)
@main.route('/informe/verificacion/<int:id_tarea>')
def generar_informe_verificacion(id_tarea):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = %s", (id_tarea,))
    tarea = cur.fetchone()
    conn.close()

    if not tarea:
        return "Tarea no encontrada", 404

    from datetime import date

    # 👉 Aquí agregas esta línea
    codigo_verificacion = f"VERF-UTMACH-2025-{str(id_tarea).zfill(3)}"

    return render_template("informe_verificacion.html",
        codigo_verificacion=codigo_verificacion,  # 👉 lo envías al template
        fecha=date.today().strftime('%d/%m/%Y'),
        unidad_solicitante=tarea[16],
        funcionario_encargado=tarea[1],
        objeto_contratacion=tarea[4],
        codigo_proceso=tarea[5],
        tipo_proceso=tarea[2],
        valor_sin_iva=tarea[7],
        valor_exento=tarea[8],
        valor_en_letras=tarea[9],
        tipo_regimen=tarea[10],
        base_legal=tarea[11],
        observaciones=tarea[12],
        presenta_estudio_previo=tarea[18],
        presenta_especificaciones=tarea[19],
        presenta_terminos_referencia=tarea[20],
        presenta_proformas=tarea[21],
        presenta_estudio_mercado=tarea[22],
        determinacion_necesidad=tarea[23],
        consta_catalogo_electronico=tarea[24],
        consta_poa=tarea[25],
        consta_pac=tarea[26],
        presenta_errores=tarea[27],
        cumple_normativa=tarea[28],
        nombre_jefe_compras=tarea[15]
    )
@main.route('/informe/catalogo/<int:tarea_id>')
def generar_informe_catalogo(tarea_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = %s", (tarea_id,))
    tarea = cur.fetchone()
    conn.close()

    if not tarea:
        return "Tarea no encontrada", 404

    from datetime import date
    return render_template("informe_catalogo.html",
        fecha=date.today().strftime('%d/%m/%Y'),
        unidad_solicitante=tarea[16],
        funcionario_encargado=tarea[1],
        objeto_contratacion=tarea[4],
        codigo_proceso=tarea[5],
        tipo_proceso=tarea[2],
        valor_sin_iva=tarea[7],
        valor_exento=tarea[8],
        valor_en_letras=tarea[9],
        tipo_regimen=tarea[10],
        base_legal=tarea[11],
        observaciones=tarea[12],
        presenta_estudio_previo=tarea[18],
        presenta_especificaciones=tarea[19],
        presenta_terminos_referencia=tarea[20],
        presenta_proformas=tarea[21],
        presenta_estudio_mercado=tarea[22],
        determinacion_necesidad=tarea[23],
        consta_catalogo_electronico=tarea[24],
        consta_poa=tarea[25],
        consta_pac=tarea[26],
        presenta_errores=tarea[27],
        cumple_normativa=tarea[28],
        nombre_jefe_compras=tarea[15],
        tarea_id=tarea_id  # ← ESTA ES LA CLAVE
    )
    # AGREGA CERTIFICACION PAC 
@main.route('/informe/pac/<int:tarea_id>')
def informe_pac(tarea_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = %s", (tarea_id,))
    tarea = cur.fetchone()
    conn.close()

    if not tarea:
        return "Tarea no encontrada", 404

    from datetime import date
    return render_template('informe_pac.html',
        tarea_id=tarea_id,
        fecha=date.today().strftime('%d/%m/%Y'),
        unidad_solicitante=tarea[16],
        funcionario_encargado=tarea[1],
        objeto_contratacion=tarea[4],
        codigo_proceso=tarea[5],
        tipo_proceso=tarea[2],
        valor_sin_iva=tarea[7],
        valor_exento=tarea[8],
        valor_en_letras=tarea[9],
        tipo_regimen=tarea[10],
        base_legal=tarea[11],
        observaciones=tarea[12],
        imagen_pac=tarea[30] if len(tarea) > 30 else None  # Ajusta según tu tabla
    )
@main.route('/admin/permisos', methods=['GET', 'POST'])
def gestionar_permisos():
    if session.get('rol') != 'Administrador':
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    # Definir roles y módulos disponibles
    roles = ['Analista', 'Invitado', 'Jefe']
    modulos = ['requerimientos', 'tareas', 'ordenes_compra', 'crear_pliegos', 'reportes']

    # POST: Guardar cambios
    if request.method == 'POST':
        cur.execute("DELETE FROM permisos")  # Limpia permisos existentes (simplificado)
        for rol in roles:
            for modulo in modulos:
                checkbox_name = f"perm_{rol}_{modulo}"
                if checkbox_name in request.form:
                    cur.execute("INSERT INTO permisos (rol, modulo) VALUES (%s, %s)", (rol, modulo))
        conn.commit()
    
    # GET: Cargar permisos actuales
    cur.execute("SELECT rol, modulo FROM permisos")
    rows = cur.fetchall()
    permisos = {rol: {modulo: False for modulo in modulos} for rol in roles}
    for rol, modulo in rows:
        permisos[rol][modulo] = True

    conn.close()

    return render_template("gestionar_permisos.html", roles=roles, modulos=modulos, permisos=permisos)

