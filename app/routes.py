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

    # Datos para el formulario (sirven para GET y re-render)
    cur.execute("SELECT nombre_proceso FROM tipo_procesos")
    tipos_proceso = cur.fetchall()

    cur.execute("""
        SELECT r.id, r.memo_vice_ad, u.nombre_unidad, r.funcionario_encargado
        FROM requerimientos r
        JOIN unidades u ON r.unid_requirente = u.id
    """)
    requerimientos = cur.fetchall()
    # Cargar tipos de régimen para el <select>
    cur.execute("SELECT id, nombre_regimen FROM tipo_regimen ORDER BY nombre_regimen ASC")
    regimenes = cur.fetchall()

    if request.method == 'POST':
        # ---- TODO lo que usa request.form VA DENTRO DEL POST ----
        imagen = request.files.get('imagen_pac')
        imagen_data = imagen.read() if imagen and imagen.filename else None

        # Valor en letras (backend)
        valor_sin_iva = float(request.form.get('valor_sin_iva') or 0)
        valor_exento = float(request.form.get('valor_exento') or 0)
        valor_total = valor_sin_iva + valor_exento
        entero = int(valor_total)
        centavos = int(round((valor_total - entero) * 100))
        letras = num2words.num2words(entero, lang='es').capitalize()
        valor_en_letras = f"{letras} con {centavos:02d}/100 dólares americanos"

        # Validar código único
        codigo = (request.form.get('codigo_proceso') or '').strip()
        if codigo:
            cur.execute("SELECT 1 FROM tareas WHERE codigo_proceso = %s", (codigo,))
            if cur.fetchone():
                # recargar tabla y volver con error
                cur.execute("""
                    SELECT t.id, r.memo_vice_ad, r.unid_requirente, t.funcionario_encargado,
                           t.estado_requerimiento, t.tipo_proceso
                    FROM tareas t
                    JOIN requerimientos r ON t.requerimiento_id = r.id
                """)
                tareas_list = cur.fetchall()
                conn.close()
                return render_template('tareas_admin.html',
                                       requerimientos=requerimientos,
                                       tareas=tareas_list,
                                       tipos_proceso=tipos_proceso,
                                       regimenes=regimenes,   # <- AÑADIR
                                       error_codigo="El código de proceso ya existe. Debe ser único.")
        numero_certificacion = request.form.get('numero_certificacion')
        data = (
            request.form.get('requerimiento_id'),
            request.form.get('funcionario_encargado'),
            request.form.get('tipo_proceso'),
            request.form.get('estado_requerimiento'),
            request.form.get('objeto_contratacion'),
            codigo,  # usamos el validado
            request.form.get('fecha_recepcion') or None,
            valor_sin_iva,
            valor_exento,
            valor_en_letras,
            request.form.get('tipo_regimen'),
            request.form.get('base_legal'),
            request.form.get('observaciones'),
            request.form.get('fecha_envio_observaciones') or None,
            request.form.get('fecha_correccion_observacion') or None,
            request.form.get('nombre_jefe_compras'),
            request.form.get('unidad_solicitante') or None,
            request.form.get('administrador_contrato') or None,
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
            numero_certificacion,
            imagen_data,
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
                presenta_errores, cumple_normativa, numero_certificacion, imagen_pac
            )
            VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,
            %s,%s
            )
        """, data)
        conn.commit()

    # Listar tareas (sirve para GET y POST exitoso)
    cur.execute("""
        SELECT t.id, r.memo_vice_ad, r.unid_requirente, t.funcionario_encargado,
               t.estado_requerimiento, t.tipo_proceso
        FROM tareas t
        JOIN requerimientos r ON t.requerimiento_id = r.id
    """)
    tareas_list = cur.fetchall()
    conn.close()

    return render_template('tareas_admin.html',
                           requerimientos=requerimientos,
                           tareas=tareas_list,
                           tipos_proceso=tipos_proceso,
                           regimenes=regimenes)  # <- AÑADIR

# The following block was removed because it was outside any function and caused a "cur is not defined" error.

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

    cur.execute("SELECT id, memo_vice_ad, unid_requirente, funcionario_encargado FROM requerimientos")
    requerimientos = cur.fetchall()
    cur.execute("SELECT nombre_proceso FROM tipo_procesos")
    tipos_proceso = cur.fetchall()
    cur.execute("SELECT * FROM tareas WHERE id = %s", (id,))
    tarea = cur.fetchone()
    cur.execute("SELECT id, nombre_regimen FROM tipo_regimen ORDER BY nombre_regimen ASC")
    regimenes = cur.fetchall()
    if request.method == 'POST':
        # Valor en letras
        valor_sin_iva = float(request.form.get('valor_sin_iva') or 0)
        valor_exento = float(request.form.get('valor_exento') or 0)
        valor_total = valor_sin_iva + valor_exento
        entero = int(valor_total)
        centavos = int(round((valor_total - entero) * 100))
        letras = num2words.num2words(entero, lang='es').capitalize()
        valor_en_letras = f"{letras} con {centavos:02d}/100 dólares americanos"

        # Validar código único (excluyendo esta tarea)
        codigo = (request.form.get('codigo_proceso') or '').strip()
        if codigo:
            cur.execute("SELECT 1 FROM tareas WHERE codigo_proceso = %s AND id <> %s", (codigo, id))
            if cur.fetchone():
                conn.close()
                return render_template('editar_tarea.html',
                                       requerimientos=requerimientos,
                                       tarea=tarea,
                                       tipos_proceso=tipos_proceso,
                                       regimenes=regimenes,
                                       error_codigo="El código de proceso ya existe. Debe ser único.")

        data = (
            request.form.get('funcionario_encargado'),
            request.form.get('tipo_proceso'),
            request.form.get('estado_requerimiento'),
            request.form.get('objeto_contratacion'),
            codigo,
            request.form.get('fecha_recepcion') or None,
            valor_sin_iva,
            valor_exento,
            valor_en_letras,
            request.form.get('tipo_regimen'),
            request.form.get('base_legal'),
            request.form.get('observaciones'),
            request.form.get('fecha_envio_observaciones') or None,
            request.form.get('fecha_correccion_observacion') or None,
            request.form.get('nombre_jefe_compras'),
            request.form.get('unidad_solicitante') or None,
            request.form.get('administrador_contrato') or None,
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
            request.form.get('numero_certificacion'),
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
                consta_pac=%s, presenta_errores=%s, cumple_normativa=%s, numero_certificacion=%s
            WHERE id=%s
        """, data)
        conn.commit()
        conn.close()
        return redirect('/admin/tareas')

    conn.close()
    return render_template('editar_tarea.html',
                           requerimientos=requerimientos,
                           tarea=tarea,
                           tipos_proceso=tipos_proceso,
                           regimenes=regimenes)
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
# ------------------- TIPOS DE PROCESOS -------------------
@main.route('/admin/tipo_procesos', methods=['GET', 'POST'])
def tipo_procesos():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form.get('nombre_proceso', '').strip()
        if nombre:
            # Evita duplicados
            cur.execute("SELECT 1 FROM tipo_procesos WHERE nombre_proceso = %s", (nombre,))
            if not cur.fetchone():
                cur.execute("INSERT INTO tipo_procesos (nombre_proceso) VALUES (%s)", (nombre,))
                conn.commit()

    cur.execute("SELECT id, nombre_proceso FROM tipo_procesos ORDER BY id ASC")
    procesos = cur.fetchall()
    conn.close()

    return render_template('tipo_procesos.html', procesos=procesos)

@main.route('/admin/tipo_procesos/eliminar/<int:proc_id>', methods=['POST'])
def eliminar_tipo_proceso(proc_id):
    conn = get_db_connection()
    cur = conn.cursor()

    error_msg = None
    try:
        cur.execute("DELETE FROM tipo_procesos WHERE id = %s", (proc_id,))
        conn.commit()
    except Exception as e:
        # Si está referenciado en tareas u otra tabla, habrá error de integridad
        conn.rollback()
        error_msg = "No se puede eliminar: el tipo de proceso está en uso."
    finally:
        cur.execute("SELECT id, nombre_proceso FROM tipo_procesos ORDER BY id ASC")
        procesos = cur.fetchall()
        conn.close()

    # Volvemos a la misma página y, si hubo problema, mostramos el mensaje
    return render_template('tipo_procesos.html', procesos=procesos, error=error_msg)



# ------------------- TIPOS DE RÉGIMEN -------------------
@main.route('/admin/tipo_regimen', methods=['GET', 'POST'])
def tipo_regimen():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form.get('nombre_regimen', '').strip()
        if nombre:
            # Evita duplicados
            cur.execute("SELECT 1 FROM tipo_regimen WHERE nombre_regimen = %s", (nombre,))
            if not cur.fetchone():
                cur.execute("INSERT INTO tipo_regimen (nombre_regimen) VALUES (%s)", (nombre,))
                conn.commit()

    cur.execute("SELECT id, nombre_regimen FROM tipo_regimen ORDER BY id ASC")
    regimenes = cur.fetchall()
    conn.close()

    return render_template('tipo_regimen.html', regimenes=regimenes)
# ------------------- ÓRDENES DE COMPRA -------------------
@main.route('/admin/ordenes_compra', methods=['GET', 'POST'])
def ordenes_compra():
    conn = get_db_connection()
    cur = conn.cursor()

    # ---------- GET: listar y mostrar formulario ----------
    if request.method == 'GET':
        # Lista de OCs
        cur.execute("""
            SELECT id, numero_oc, fecha, proveedor, total
            FROM ordenes_compra
            ORDER BY id DESC
        """)
        ocs = cur.fetchall()

        # Memos de tareas para el selector del formulario
        cur.execute("""
            SELECT t.id, r.memo_vice_ad
            FROM tareas t
            JOIN requerimientos r ON t.requerimiento_id = r.id
            ORDER BY r.memo_vice_ad ASC
        """)
        tareas_memos = cur.fetchall()

        conn.close()
        return render_template('ordenes_compra.html',
                               ocs=ocs,
                               tareas_memos=tareas_memos)

    # ---------- POST: crear OC ----------
    # Cabecera
    numero_oc = (request.form.get('numero_oc') or '').strip()
    fecha = request.form.get('fecha') or None
    area_requirente = request.form.get('area_requirente')
    cert_presupuestaria = request.form.get('cert_presupuestaria')
    objeto = request.form.get('objeto')

    proveedor = request.form.get('proveedor')
    ruc = request.form.get('ruc')
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    correo = request.form.get('correo')

    proforma_num = request.form.get('proforma_num')
    proforma_fecha = request.form.get('proforma_fecha') or None
    contacto = request.form.get('contacto')
    vigencia = request.form.get('vigencia')

    forma_pago = request.form.get('forma_pago')
    plazo_ejecucion = request.form.get('plazo_ejecucion')
    lugar_entrega = request.form.get('lugar_entrega')
    administrador_orden = request.form.get('administrador_orden')
    multas = request.form.get('multas')
    garantia = request.form.get('garantia')
    base_legal = request.form.get('base_legal')

    subtotal = float(request.form.get('subtotal') or 0)
    iva = float(request.form.get('iva') or 0)
    total = float(request.form.get('total') or 0)
    observaciones = request.form.get('observaciones')

    # Si vino tarea_id, completar y aplicar la regla de Ínfima Cuantía
    tarea_id = request.form.get('tarea_id')
    if tarea_id:
        cur.execute("""
            SELECT 
                t.tipo_proceso,
                t.codigo_proceso,
                u.nombre_unidad AS area_requirente_src,
                t.objeto_contratacion AS objeto_src,
                COALESCE(t.numero_certificacion,'') AS cert_src
            FROM tareas t
            JOIN requerimientos r ON t.requerimiento_id = r.id
            JOIN unidades u       ON r.unid_requirente = u.id
            WHERE t.id = %s
        """, (tarea_id,))
        row = cur.fetchone()
        if row:
            tipo, cod_proc, area_src, obj_src, cert_src = row
            # Normaliza: í,á,é,ó,ú -> i,a,e,o,u
            tipo_norm = (tipo or '').lower()
            for a,b in (('í','i'),('á','a'),('é','e'),('ó','o'),('ú','u')):
                tipo_norm = tipo_norm.replace(a,b)
            es_infima = ('infima' in tipo_norm) and ('cuantia' in tipo_norm)

            if es_infima and cod_proc:
                numero_oc = cod_proc  # forzar número de OC = código del proceso

            if not area_requirente:
                area_requirente = area_src
            if not objeto:
                objeto = obj_src
            if not cert_presupuestaria:
                cert_presupuestaria = cert_src

    # Validar número de OC único
    cur.execute("SELECT 1 FROM ordenes_compra WHERE numero_oc = %s", (numero_oc,))
    if cur.fetchone():
        # Re-render con error (y volver a pasar tareas_memos)
        cur.execute("""
            SELECT t.id, r.memo_vice_ad
            FROM tareas t
            JOIN requerimientos r ON t.requerimiento_id = r.id
            ORDER BY r.memo_vice_ad ASC
        """)
        tareas_memos = cur.fetchall()

        cur.execute("""
            SELECT id, numero_oc, fecha, proveedor, total
            FROM ordenes_compra
            ORDER BY id DESC
        """)
        ocs = cur.fetchall()
        conn.close()
        return render_template('ordenes_compra.html',
                               ocs=ocs,
                               tareas_memos=tareas_memos,
                               error="El número de Orden de Compra ya existe.")

    # Insert cabecera OC
    cur.execute("""
        INSERT INTO ordenes_compra (
            numero_oc, fecha, area_requirente, cert_presupuestaria, objeto,
            proveedor, ruc, telefono, direccion, correo,
            proforma_num, proforma_fecha, contacto, vigencia,
            forma_pago, plazo_ejecucion, lugar_entrega, administrador_orden, multas, garantia, base_legal,
            subtotal, iva, total, observaciones
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (numero_oc, fecha, area_requirente, cert_presupuestaria, objeto,
          proveedor, ruc, telefono, direccion, correo,
          proforma_num, proforma_fecha, contacto, vigencia,
          forma_pago, plazo_ejecucion, lugar_entrega, administrador_orden, multas, garantia, base_legal,
          subtotal, iva, total, observaciones))
    oc_id = cur.fetchone()[0]

    # Insert ítems
    items = request.form.getlist('item[]')
    cpcs = request.form.getlist('cpc[]')
    descs = request.form.getlist('descripcion[]')
    unidades = request.form.getlist('unidad[]')
    cants = request.form.getlist('cantidad[]')
    vunits = request.form.getlist('v_unitario[]')
    vtotals = request.form.getlist('v_total[]')

    for i in range(len(items)):
        if not descs[i].strip():
            continue
        cur.execute("""
            INSERT INTO oc_items (oc_id, item, cpc, descripcion, unidad, cantidad, v_unitario, v_total)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            oc_id,
            int(items[i] or 0),
            cpcs[i] or None,
            descs[i],
            unidades[i] or None,
            float(cants[i] or 0),
            float(vunits[i] or 0),
            float(vtotals[i] or 0),
        ))

    conn.commit()
    conn.close()
    return redirect('/admin/ordenes_compra')

@main.route('/admin/ordenes_compra/eliminar/<int:oc_id>', methods=['POST'])
def eliminar_oc(oc_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ordenes_compra WHERE id = %s", (oc_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/ordenes_compra')


@main.route('/informe/orden_compra/<int:oc_id>')
def imprimir_oc(oc_id):
    # Render “PDF friendly” (imprime desde el navegador)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ordenes_compra WHERE id = %s", (oc_id,))
    oc = cur.fetchone()

    cur.execute("""SELECT item, cpc, descripcion, unidad, cantidad, v_unitario, v_total
                   FROM oc_items WHERE oc_id = %s ORDER BY item ASC""", (oc_id,))
    items = cur.fetchall()
    conn.close()

    if not oc:
        return "OC no encontrada", 404

    # total en letras (xx/100 dólares americanos)
    from num2words import num2words
    total = float(oc[24] or 0)  # índice 24 = total según la tabla propuesta
    entero = int(total)
    centavos = int(round((total - entero) * 100))
    letras = num2words(entero, lang='es').capitalize()
    total_letras = f"{letras} con {centavos:02d}/100 dólares americanos"

    return render_template('orden_compra_print.html', oc=oc, items=items, total_letras=total_letras)
@main.route('/api/tarea/<int:tarea_id>')
def api_tarea(tarea_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            t.id,
            r.memo_vice_ad,
            u.nombre_unidad   AS area_requirente,
            t.objeto_contratacion,
            t.codigo_proceso,
            t.tipo_proceso,
            COALESCE(t.numero_certificacion,'') AS numero_certificacion
        FROM tareas t
        JOIN requerimientos r ON t.requerimiento_id = r.id
        JOIN unidades u       ON r.unid_requirente = u.id
        WHERE t.id = %s
    """, (tarea_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "No existe la tarea"}), 404

    return jsonify({
        "id": row[0],
        "memo": row[1],
        "area_requirente": row[2],
        "objeto_contratacion": row[3],
        "codigo_proceso": row[4],
        "tipo_proceso": row[5],
        "numero_certificacion": row[6],
    })

