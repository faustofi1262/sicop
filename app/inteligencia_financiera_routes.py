from flask import Blueprint, render_template, request
from app.decorators import login_required
from app.database import get_connection
from datetime import datetime
import calendar


inteligencia_financiera = Blueprint(
    "inteligencia_financiera",
    __name__,
    url_prefix="/inteligencia-financiera"
)

@inteligencia_financiera.route("/")
@login_required()
def dashboard():
    fecha_inicio = (request.args.get("fecha_inicio") or "").strip()
    fecha_corte = (request.args.get("fecha_corte") or "").strip()
    proyectar_hasta = (request.args.get("proyectar_hasta") or "").strip()

    unidad = (request.args.get("unidad") or "").strip()
    programa = (request.args.get("programa") or "").strip()
    partida = (request.args.get("partida") or "").strip()
    fuente = (request.args.get("fuente") or "").strip()
   
    conn = get_connection()
    cur = conn.cursor()

    try:

        # ==========================================
        # 1. PAC VIGENTE
        # ==========================================
        cur.execute("""
            SELECT
                pv.id,
                pv.anio,
                pv.numero_reforma,
                COALESCE(SUM(pd.subtotal), 0) AS total_pac
            FROM pac_versiones pv

            LEFT JOIN pac_detalle pd
                ON pd.pac_version_id = pv.id

            WHERE pv.estado = 'VIGENTE'

            GROUP BY
                pv.id,
                pv.anio,
                pv.numero_reforma

            ORDER BY
                pv.anio DESC,
                pv.id DESC

            LIMIT 1
        """)

        pac_vigente = cur.fetchone()


        # ==========================================
        # 2. MONTO INGRESADO
        #
        # Excluimos:
        # - DEVUELTOS
        # - VERIFICACIÓN PRODUCCIÓN NACIONAL
        # - ARRENDAMIENTOS DE BIENES MUEBLES
        # ==========================================
        cur.execute("""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN EXISTS (
                                SELECT 1
                                FROM certificaciones_plurianuales cp
                                WHERE cp.tarea_id = t.id
                            )
                            THEN COALESCE(t.valor_certificacion, 0)

                            ELSE
                                COALESCE(t.valor_sin_iva, 0)
                                +
                                COALESCE(t.valor_exento, 0)
                        END
                    ),
                    0
                )
            FROM tareas t

            LEFT JOIN tipo_procesos tp
                ON t.tipo_proceso = tp.id::TEXT

            WHERE
                UPPER(
                    TRIM(
                        COALESCE(
                            t.estado_requerimiento,
                            ''
                        )
                    )
                ) <> 'DEVUELTO'

                AND UPPER(
                    TRIM(
                        COALESCE(
                            tp.nombre_proceso,
                            ''
                        )
                    )
                ) NOT IN (
                    'VERIFICACION DE PRODUCCION NACIONAL',
                    'ARRENDAMIENTOS DE BIENES MUEBLES'
                )
        """)

        monto_ingresado = cur.fetchone()[0] or 0


        # ==========================================
        # 3. MONTO CERTIFICADO
        # ==========================================
        cur.execute("""
            SELECT
                COALESCE(
                    SUM(
                        COALESCE(
                            t.valor_certificacion,
                            0
                        )
                    ),
                    0
                )
            FROM tareas t

            LEFT JOIN tipo_procesos tp
                ON t.tipo_proceso = tp.id::TEXT

            WHERE
                UPPER(
                    TRIM(
                        COALESCE(
                            t.estado_requerimiento,
                            ''
                        )
                    )
                ) <> 'DEVUELTO'

                AND UPPER(
                    TRIM(
                        COALESCE(
                            tp.nombre_proceso,
                            ''
                        )
                    )
                ) NOT IN (
                    'VERIFICACION DE PRODUCCION NACIONAL',
                    'ARRENDAMIENTOS DE BIENES MUEBLES'
                )
        """)

        monto_certificado = cur.fetchone()[0] or 0


        # ==========================================
        # 4. MONTO ADJUDICADO
        # ==========================================
        cur.execute("""
            WITH adjudicado_tarea AS (

                SELECT
                    a.tarea_id,

                    COALESCE(
                        SUM(ap.monto_adjudicado),
                        0
                    ) AS monto_adjudicado

                FROM adjudicaciones a

                LEFT JOIN adjudicacion_partidas ap
                    ON ap.adjudicacion_id = a.id

                GROUP BY
                    a.tarea_id
            )

            SELECT
                COALESCE(
                    SUM(at.monto_adjudicado),
                    0
                )

            FROM tareas t

            LEFT JOIN tipo_procesos tp
                ON t.tipo_proceso = tp.id::TEXT

            LEFT JOIN adjudicado_tarea at
                ON at.tarea_id = t.id

            WHERE
                UPPER(
                    TRIM(
                        COALESCE(
                            t.estado_requerimiento,
                            ''
                        )
                    )
                ) <> 'DEVUELTO'

                AND UPPER(
                    TRIM(
                        COALESCE(
                            tp.nombre_proceso,
                            ''
                        )
                    )
                ) NOT IN (
                    'VERIFICACION DE PRODUCCION NACIONAL',
                    'ARRENDAMIENTOS DE BIENES MUEBLES'
                )
        """)

        monto_adjudicado = cur.fetchone()[0] or 0


        # ==========================================
        # 5. DATOS PAC
        # ==========================================
        pac_id = None
        pac_anio = None
        pac_reforma = None
        monto_pac = 0

        if pac_vigente:

            pac_id = pac_vigente[0]
            pac_anio = pac_vigente[1]
            pac_reforma = pac_vigente[2]
            monto_pac = pac_vigente[3] or 0
        # ==========================================
        # OPCIONES DE FILTRO
        # ==========================================

        cur.execute("""
            SELECT DISTINCT
                CASE
                    WHEN UPPER(TRIM(unidad)) IN ('DECANATO', 'SUBDECANATO')
                        AND bloque IS NOT NULL
                        AND TRIM(bloque) <> ''
                    THEN unidad || ' - ' || bloque

                    ELSE unidad
                END AS unidad_visible

            FROM pac_detalle

            WHERE unidad IS NOT NULL
            AND TRIM(unidad) <> ''

            ORDER BY unidad_visible
        """)

        unidades_filtro = [
            fila[0]
            for fila in cur.fetchall()
        ]


        cur.execute("""
            SELECT DISTINCT programa
            FROM pac_detalle
            WHERE programa IS NOT NULL
            AND TRIM(programa) <> ''
            ORDER BY programa
        """)
        programas_filtro = [
            fila[0]
            for fila in cur.fetchall()
        ]


        cur.execute("""
            SELECT DISTINCT partida
            FROM pac_detalle
            WHERE partida IS NOT NULL
            AND TRIM(partida) <> ''
            ORDER BY partida
        """)
        partidas_filtro = [
            fila[0]
            for fila in cur.fetchall()
        ]


        cur.execute("""
            SELECT DISTINCT fuente
            FROM pac_detalle
            WHERE fuente IS NOT NULL
            AND TRIM(fuente) <> ''
            ORDER BY fuente
        """)
        fuentes_filtro = [
            fila[0]
            for fila in cur.fetchall()
        ]
        # ==========================================================
        # 6. SERIE MENSUAL REAL - MONTO INGRESADO
        #
        # Esta serie será la base matemática del motor de proyección.
        #
        # Solo se calcula cuando el usuario ha indicado:
        # - Fecha inicial
        # - Fecha de corte
        #
        # Por ahora analizamos el flujo real de procesos ingresados.
        # ==========================================================

        meses_labels = []
        montos_mensuales = []
        total_periodo_analizado = 0

        analisis_generado = False
        mensaje_analisis = None


        # ==========================================================
        # 6.1 VALIDAR FECHAS DEL PERÍODO DE ANÁLISIS
        # ==========================================================

        if fecha_inicio and fecha_corte:

            try:

                fecha_inicio_dt = datetime.strptime(
                    fecha_inicio,
                    "%Y-%m-%d"
                ).date()

                fecha_corte_dt = datetime.strptime(
                    fecha_corte,
                    "%Y-%m-%d"
                ).date()

                if fecha_inicio_dt > fecha_corte_dt:

                    mensaje_analisis = (
                        "La fecha inicial no puede ser posterior "
                        "a la fecha de corte."
                    )

                else:

                    analisis_generado = True


                    # ==================================================
                    # 6.2 CONDICIONES ECONÓMICAS DE LA SERIE
                    #
                    # No participan económicamente:
                    # - Procesos DEVUELTOS
                    # - Verificación de Producción Nacional
                    # - Arrendamientos de Bienes Muebles
                    # ==================================================

                    condiciones_mensuales = [
                        "t.fecha_recepcion >= %s",
                        "t.fecha_recepcion <= %s",

                        """
                        UPPER(
                            TRIM(
                                COALESCE(
                                    t.estado_requerimiento,
                                    ''
                                )
                            )
                        ) <> 'DEVUELTO'
                        """,

                        """
                        UPPER(
                            TRIM(
                                COALESCE(
                                    tp.nombre_proceso,
                                    ''
                                )
                            )
                        ) NOT IN (
                            'VERIFICACION DE PRODUCCION NACIONAL',
                            'ARRENDAMIENTOS DE BIENES MUEBLES'
                        )
                        """
                    ]

                    parametros_mensuales = [
                        fecha_inicio,
                        fecha_corte
                    ]

                    # ==================================================
                    # 6.3 FILTRO POR UNIDAD
                    # ==================================================

                    if unidad:

                        if " - " in unidad:

                            nombre_unidad, bloque_unidad = unidad.split(
                                " - ",
                                1
                            )

                            condiciones_mensuales.append("""
                                EXISTS (
                                    SELECT 1
                                    FROM requerimientos r_unidad
                                    JOIN unidades u_unidad
                                        ON u_unidad.id = r_unidad.unid_requirente

                                    WHERE r_unidad.id = t.requerimiento_id

                                    AND UPPER(
                                            TRIM(
                                                COALESCE(
                                                    u_unidad.bloque,
                                                    ''
                                                )
                                            )
                                        ) = UPPER(TRIM(%s))
                                )
                            """)

                            parametros_mensuales.append(
                                bloque_unidad
                            )

                        else:

                            condiciones_mensuales.append("""
                                EXISTS (
                                    SELECT 1
                                    FROM requerimientos r_unidad
                                    JOIN unidades u_unidad
                                        ON u_unidad.id = r_unidad.unid_requirente

                                    WHERE r_unidad.id = t.requerimiento_id

                                    AND UPPER(
                                            TRIM(
                                                u_unidad.nombre_unidad
                                            )
                                        ) = UPPER(TRIM(%s))
                                )
                            """)

                            parametros_mensuales.append(
                                unidad
                            )
                    


                    # ==================================================
                    # 6.4 FILTROS PRESUPUESTARIOS
                    #
                    # Programa, partida y fuente se validan mediante
                    # las partidas asociadas al requerimiento.
                    #
                    # EXISTS evita duplicar una tarea cuando tiene
                    # varias partidas presupuestarias.
                    # ==================================================

                    filtros_partida = []
                    parametros_partida = []

                    if programa:

                        filtros_partida.append(
                            "p.programa = %s"
                        )

                        parametros_partida.append(
                            programa
                        )


                    if partida:

                        filtros_partida.append(
                            "p.num_part = %s"
                        )

                        parametros_partida.append(
                            partida
                        )


                    if fuente:

                        filtros_partida.append(
                            "p.fuente = %s"
                        )

                        parametros_partida.append(
                            fuente
                        )


                    if filtros_partida:

                        condiciones_mensuales.append(
                            f"""
                            EXISTS (
                                SELECT 1
                                FROM partidas p
                                WHERE
                                    p.requerimiento_id =
                                    t.requerimiento_id

                                    AND {
                                        " AND ".join(
                                            filtros_partida
                                        )
                                    }
                            )
                            """
                        )

                        parametros_mensuales.extend(
                            parametros_partida
                        )


                    # ==================================================
                    # 6.5 CONSULTA DEL FLUJO ECONÓMICO MENSUAL
                    #
                    # Agrupamos los procesos por mes de recepción.
                    # ==================================================

                    where_mensual = (
                        " WHERE "
                        + " AND ".join(
                            condiciones_mensuales
                        )
                    )


                    sql_mensual = f"""
                        SELECT
                            DATE_TRUNC(
                                'month',
                                t.fecha_recepcion
                            )::date AS mes,

                            COALESCE(
                                SUM(
                                    CASE
                                        WHEN EXISTS (
                                            SELECT 1
                                            FROM certificaciones_plurianuales cp
                                            WHERE cp.tarea_id = t.id
                                        )
                                        THEN COALESCE(
                                            t.valor_certificacion,
                                            0
                                        )

                                        ELSE
                                            COALESCE(
                                                t.valor_sin_iva,
                                                0
                                            )
                                            +
                                            COALESCE(
                                                t.valor_exento,
                                                0
                                            )
                                    END
                                ),
                                0
                            ) AS monto

                        FROM tareas t

                        LEFT JOIN tipo_procesos tp
                            ON t.tipo_proceso =
                               tp.id::TEXT

                        {where_mensual}

                        GROUP BY
                            DATE_TRUNC(
                                'month',
                                t.fecha_recepcion
                            )

                        ORDER BY
                            mes
                    """


                    cur.execute(
                        sql_mensual,
                        parametros_mensuales
                    )

                    flujo_mensual = cur.fetchall()


                    # ==================================================
                    # 6.6 PREPARAR DATOS PARA EL GRÁFICO
                    # ==================================================

                    nombres_meses = {
                        1: "Enero",
                        2: "Febrero",
                        3: "Marzo",
                        4: "Abril",
                        5: "Mayo",
                        6: "Junio",
                        7: "Julio",
                        8: "Agosto",
                        9: "Septiembre",
                        10: "Octubre",
                        11: "Noviembre",
                        12: "Diciembre"
                    }


                    for fila in flujo_mensual:

                        fecha_mes = fila[0]

                        monto_mes = float(
                            fila[1] or 0
                        )

                        etiqueta = (
                            nombres_meses[
                                fecha_mes.month
                            ]
                            +
                            " "
                            +
                            str(fecha_mes.year)
                        )

                        meses_labels.append(
                            etiqueta
                        )

                        montos_mensuales.append(
                            round(
                                monto_mes,
                                2
                            )
                        )

                        total_periodo_analizado += (
                            monto_mes
                        )


                    total_periodo_analizado = round(
                        total_periodo_analizado,
                        2
                    )


            except ValueError:

                mensaje_analisis = (
                    "Las fechas ingresadas no son válidas."
                )
        # ==========================================================
        # 7. MOTOR BASE DE PROYECCIÓN FINANCIERA
        #
        # Metodología inicial:
        #
        # 1. Toma los montos mensuales reales del período analizado.
        # 2. Si el mes de corte está incompleto, calcula su ritmo
        #    diario y estima cuánto podría cerrar ese mes.
        # 3. Calcula un promedio mensual ajustado.
        # 4. Utiliza ese promedio como escenario base para los
        #    meses futuros hasta el mes seleccionado.
        #
        # Esta primera versión es deliberadamente transparente:
        # todavía NO utiliza IA ni modelos estadísticos complejos.
        # ==========================================================

        proyeccion_generada = False
        mensaje_proyeccion = None

        ritmo_diario_mes_corte = 0
        monto_mes_corte_real = 0
        monto_mes_corte_estimado = 0

        promedio_mensual_proyectado = 0
        proyeccion_acumulada_objetivo = 0

        mes_corte_es_parcial = False

        grafico_labels = list(meses_labels)
        serie_real_grafico = list(montos_mensuales)

        serie_proyectada_grafico = [
            None
            for _ in grafico_labels
        ]


        # ==========================================================
        # 7.1 SOLO PROYECTAR SI EXISTE UN PERÍODO REAL VÁLIDO
        #     Y EL USUARIO SELECCIONÓ UN MES OBJETIVO
        # ==========================================================

        if (
            analisis_generado
            and proyectar_hasta
            and fecha_inicio
            and fecha_corte
        ):

            try:

                mes_objetivo = int(
                    proyectar_hasta
                )

                fecha_inicio_dt = datetime.strptime(
                    fecha_inicio,
                    "%Y-%m-%d"
                ).date()

                fecha_corte_dt = datetime.strptime(
                    fecha_corte,
                    "%Y-%m-%d"
                ).date()


                # ==================================================
                # 7.2 VALIDAR QUE EL MES OBJETIVO SEA FUTURO
                #
                # Por ahora el selector trabaja dentro del mismo año
                # de la fecha de corte.
                # ==================================================

                if mes_objetivo <= fecha_corte_dt.month:

                    mensaje_proyeccion = (
                        "El mes de proyección debe ser posterior "
                        "al mes correspondiente a la fecha de corte."
                    )

                else:

                    # ==================================================
                    # 7.3 CONVERTIR LA SERIE REAL EN UN DICCIONARIO
                    #
                    # Ejemplo:
                    # (2026, 6) -> 1,180,000
                    # (2026, 7) ->   430,000
                    # ==================================================

                    valores_por_mes = {}

                    for fila in flujo_mensual:

                        fecha_mes = fila[0]

                        valores_por_mes[
                            (
                                fecha_mes.year,
                                fecha_mes.month
                            )
                        ] = float(
                            fila[1] or 0
                        )


                    # ==================================================
                    # 7.4 IDENTIFICAR EL MONTO REAL DEL MES DE CORTE
                    # ==================================================

                    clave_mes_corte = (
                        fecha_corte_dt.year,
                        fecha_corte_dt.month
                    )

                    monto_mes_corte_real = float(
                        valores_por_mes.get(
                            clave_mes_corte,
                            0
                        )
                    )


                    # ==================================================
                    # 7.5 DETERMINAR SI EL MES DE CORTE ESTÁ INCOMPLETO
                    #
                    # Ejemplo:
                    # Corte: 14/08/2026
                    # Agosto tiene 31 días.
                    # Entonces agosto todavía es un mes parcial.
                    # ==================================================

                    dias_mes_corte = calendar.monthrange(
                        fecha_corte_dt.year,
                        fecha_corte_dt.month
                    )[1]

                    mes_corte_es_parcial = (
                        fecha_corte_dt.day
                        <
                        dias_mes_corte
                    )


                    # ==================================================
                    # 7.6 NORMALIZAR EL MES PARCIAL
                    #
                    # Ritmo diario =
                    # monto acumulado del mes / días transcurridos
                    #
                    # Cierre estimado =
                    # ritmo diario * días totales del mes
                    # ==================================================

                    if mes_corte_es_parcial:

                        if fecha_corte_dt.day > 0:

                            ritmo_diario_mes_corte = (
                                monto_mes_corte_real
                                /
                                fecha_corte_dt.day
                            )

                            monto_mes_corte_estimado = (
                                ritmo_diario_mes_corte
                                *
                                dias_mes_corte
                            )

                    else:

                        monto_mes_corte_estimado = (
                            monto_mes_corte_real
                        )

                        if dias_mes_corte > 0:

                            ritmo_diario_mes_corte = (
                                monto_mes_corte_real
                                /
                                dias_mes_corte
                            )


                    # ==================================================
                    # 7.7 CONSTRUIR LOS MESES QUE FORMAN LA BASE
                    #     HISTÓRICA DEL PRONÓSTICO
                    #
                    # Los meses sin procesos también cuentan como cero.
                    # Eso evita inflar artificialmente el promedio.
                    # ==================================================

                    valores_base_proyeccion = []

                    anio_cursor = (
                        fecha_inicio_dt.year
                    )

                    mes_cursor = (
                        fecha_inicio_dt.month
                    )


                    while (
                        anio_cursor
                        <
                        fecha_corte_dt.year
                        or
                        (
                            anio_cursor
                            ==
                            fecha_corte_dt.year
                            and
                            mes_cursor
                            <=
                            fecha_corte_dt.month
                        )
                    ):

                        clave_cursor = (
                            anio_cursor,
                            mes_cursor
                        )


                        # ==============================================
                        # Para el mes de corte usamos su cierre
                        # estimado si todavía está incompleto.
                        # ==============================================

                        if (
                            anio_cursor
                            ==
                            fecha_corte_dt.year
                            and
                            mes_cursor
                            ==
                            fecha_corte_dt.month
                            and
                            mes_corte_es_parcial
                        ):

                            valor_mes_base = (
                                monto_mes_corte_estimado
                            )

                        else:

                            valor_mes_base = float(
                                valores_por_mes.get(
                                    clave_cursor,
                                    0
                                )
                            )


                        valores_base_proyeccion.append(
                            valor_mes_base
                        )


                        # ==============================================
                        # Avanzar un mes
                        # ==============================================

                        mes_cursor += 1

                        if mes_cursor == 13:

                            mes_cursor = 1
                            anio_cursor += 1


                    # ==================================================
                    # 7.8 PROMEDIO MENSUAL AJUSTADO
                    #
                    # Este valor será nuestro escenario base.
                    # ==================================================

                    if valores_base_proyeccion:

                        promedio_mensual_proyectado = (
                            sum(
                                valores_base_proyeccion
                            )
                            /
                            len(
                                valores_base_proyeccion
                            )
                        )


                    # ==================================================
                    # 7.9 PREPARAR LA LÍNEA PROYECTADA DEL GRÁFICO
                    #
                    # La línea proyectada comienza en el último dato real
                    # para que visualmente continúe la curva existente.
                    # ==================================================

                    #if serie_real_grafico:

                        #serie_proyectada_grafico[
                            #len(
                                #serie_real_grafico
                            #) - 1
                        #] = serie_real_grafico[-1]


                    # ==================================================
                    # 7.10 SI EL MES DE CORTE ES PARCIAL,
                    #      MOSTRAR SU CIERRE ESTIMADO
                    # ==================================================

                    nombres_meses_proyeccion = {
                        1: "Enero",
                        2: "Febrero",
                        3: "Marzo",
                        4: "Abril",
                        5: "Mayo",
                        6: "Junio",
                        7: "Julio",
                        8: "Agosto",
                        9: "Septiembre",
                        10: "Octubre",
                        11: "Noviembre",
                        12: "Diciembre"
                    }


                    if mes_corte_es_parcial:

                        grafico_labels.append(
                            nombres_meses_proyeccion[
                                fecha_corte_dt.month
                            ]
                            +
                            " cierre est."
                        )

                        serie_real_grafico.append(
                            None
                        )

                        serie_proyectada_grafico.append(
                            round(
                                monto_mes_corte_estimado,
                                2
                            )
                        )


                    # ==================================================
                    # 7.11 GENERAR LOS MESES FUTUROS
                    #      HASTA EL MES OBJETIVO
                    # ==================================================

                    mes_futuro = (
                        fecha_corte_dt.month
                        + 1
                    )

                    meses_futuros_generados = 0


                    while (
                        mes_futuro
                        <=
                        mes_objetivo
                    ):

                        grafico_labels.append(
                            nombres_meses_proyeccion[
                                mes_futuro
                            ]
                            +
                            " "
                            +
                            str(
                                fecha_corte_dt.year
                            )
                        )

                        serie_real_grafico.append(
                            None
                        )

                        serie_proyectada_grafico.append(
                            round(
                                promedio_mensual_proyectado,
                                2
                            )
                        )

                        meses_futuros_generados += 1

                        mes_futuro += 1


                    # ==================================================
                    # 7.12 PROYECCIÓN ACUMULADA DEL PERÍODO
                    #
                    # Partimos del monto REAL registrado entre
                    # fecha inicial y fecha de corte.
                    #
                    # Si el mes actual está incompleto:
                    # agregamos únicamente lo que falta para completar
                    # su cierre estimado.
                    #
                    # Después sumamos los meses futuros proyectados.
                    # ==================================================

                    proyeccion_acumulada_objetivo = (
                        total_periodo_analizado
                    )


                    if mes_corte_es_parcial:

                        diferencia_cierre_mes = (
                            monto_mes_corte_estimado
                            -
                            monto_mes_corte_real
                        )

                        if diferencia_cierre_mes > 0:

                            proyeccion_acumulada_objetivo += (
                                diferencia_cierre_mes
                            )


                    proyeccion_acumulada_objetivo += (
                        promedio_mensual_proyectado
                        *
                        meses_futuros_generados
                    )


                    # ==================================================
                    # 7.13 REDONDEAR RESULTADOS FINANCIEROS
                    # ==================================================

                    ritmo_diario_mes_corte = round(
                        ritmo_diario_mes_corte,
                        2
                    )

                    monto_mes_corte_real = round(
                        monto_mes_corte_real,
                        2
                    )

                    monto_mes_corte_estimado = round(
                        monto_mes_corte_estimado,
                        2
                    )

                    promedio_mensual_proyectado = round(
                        promedio_mensual_proyectado,
                        2
                    )

                    proyeccion_acumulada_objetivo = round(
                        proyeccion_acumulada_objetivo,
                        2
                    )

                    proyeccion_generada = True


            except (
                ValueError,
                TypeError
            ):

                mensaje_proyeccion = (
                    "No fue posible calcular la proyección "
                    "con los parámetros seleccionados."
                )
                # ==========================================================
        # 8. COMPARACIÓN DE LA PROYECCIÓN CONTRA EL PAC
        #
        # La fecha inicial sirve para estudiar la tendencia.
        #
        # Para comparar contra el PAC debemos conservar también
        # los procesos económicos que ingresaron ANTES de esa fecha
        # dentro del mismo ejercicio fiscal.
        #
        # Ejemplo:
        #   Histórico enero-mayo
        # + Proyección junio-octubre
        # = Acumulado esperado a octubre
        # ==========================================================

        pac_ambito_seleccionado = 0
        monto_anterior_periodo = 0

        monto_proyectado_acumulado = 0
        porcentaje_pac_proyectado = 0
        saldo_pac_proyectado = 0

       
        # ==========================================================
        # 8.1 CALCULAR PAC DEL ÁMBITO SELECCIONADO
        #
        # Si no existen filtros:
        #     utiliza todo el PAC vigente.
        #
        # Si existen filtros:
        #     calcula únicamente la parte del PAC correspondiente
        #     a Unidad, Programa, Partida y/o Fuente.
        #
        # Siempre se utiliza SUBTOTAL = valor SIN IVA.
        # ==========================================================

        if pac_id:

            condiciones_pac = [
                "pac_version_id = %s"
            ]

            parametros_pac = [
                pac_id
            ]

            if unidad:

                if " - " in unidad:

                    nombre_unidad, bloque_unidad = unidad.split(
                        " - ",
                        1
                    )

                    # Para facultades analizamos TODO el bloque
                    condiciones_pac.append(
                        "UPPER(TRIM(bloque)) = UPPER(TRIM(%s))"
                    )

                    parametros_pac.append(
                        bloque_unidad
                    )

                else:

                    condiciones_pac.append(
                        "UPPER(TRIM(unidad)) = UPPER(TRIM(%s))"
                    )

                    parametros_pac.append(
                        unidad
                    )
            

            if programa:

                condiciones_pac.append(
                    "programa = %s"
                )

                parametros_pac.append(
                    programa
                )


            if partida:

                condiciones_pac.append(
                    "partida = %s"
                )

                parametros_pac.append(
                    partida
                )


            if fuente:

                condiciones_pac.append(
                    "fuente = %s"
                )

                parametros_pac.append(
                    fuente
                )


            where_pac = (
                " WHERE "
                + " AND ".join(
                    condiciones_pac
                )
            )


            cur.execute(
                f"""
                SELECT
                    COALESCE(
                        SUM(subtotal),
                        0
                    )
                FROM pac_detalle
                {where_pac}
                """,
                parametros_pac
            )


            pac_ambito_seleccionado = float(
                cur.fetchone()[0] or 0
            )


        # ==========================================================
        # 8.2 CALCULAR MONTO REAL ANTERIOR AL PERÍODO ANALIZADO
        #
        # Si el usuario estudia desde junio, aquí recuperamos todo
        # lo que ya había ingresado desde enero hasta mayo.
        #
        # Solamente se considera el mismo ejercicio fiscal.
        # ==========================================================

        if (
            proyeccion_generada
            and fecha_inicio
        ):

            inicio_ejercicio = (
                f"{fecha_inicio_dt.year}-01-01"
            )


            condiciones_anteriores = [

                "t.fecha_recepcion >= %s",

                "t.fecha_recepcion < %s",

                """
                UPPER(
                    TRIM(
                        COALESCE(
                            t.estado_requerimiento,
                            ''
                        )
                    )
                ) <> 'DEVUELTO'
                """,

                """
                UPPER(
                    TRIM(
                        COALESCE(
                            tp.nombre_proceso,
                            ''
                        )
                    )
                ) NOT IN (
                    'VERIFICACION DE PRODUCCION NACIONAL',
                    'ARRENDAMIENTOS DE BIENES MUEBLES'
                )
                """
            ]


            parametros_anteriores = [
                inicio_ejercicio,
                fecha_inicio
            ]
            # ======================================================
            # 8.3 FILTRO POR UNIDAD
            # ======================================================

            if unidad:

                if " - " in unidad:

                    nombre_unidad, bloque_unidad = unidad.split(
                        " - ",
                        1
                    )

                    condiciones_anteriores.append("""
                        EXISTS (
                            SELECT 1
                            FROM requerimientos r_unidad
                            JOIN unidades u_unidad
                                ON u_unidad.id = r_unidad.unid_requirente

                            WHERE r_unidad.id = t.requerimiento_id

                            AND UPPER(
                                    TRIM(
                                        COALESCE(
                                            u_unidad.bloque,
                                            ''
                                        )
                                    )
                                ) = UPPER(TRIM(%s))
                        )
                    """)

                    parametros_anteriores.append(
                        bloque_unidad
                    )

                else:

                    condiciones_anteriores.append("""
                        EXISTS (
                            SELECT 1
                            FROM requerimientos r_unidad
                            JOIN unidades u_unidad
                                ON u_unidad.id = r_unidad.unid_requirente

                            WHERE r_unidad.id = t.requerimiento_id

                            AND UPPER(
                                    TRIM(
                                        u_unidad.nombre_unidad
                                    )
                                ) = UPPER(TRIM(%s))
                        )
                    """)

                    parametros_anteriores.append(
                        unidad
                    )    

            # ======================================================
            # 8.4 FILTROS PRESUPUESTARIOS
            #
            # Se utiliza EXISTS para no duplicar tareas que tengan
            # varias partidas presupuestarias.
            # ======================================================

            filtros_partidas_anteriores = []
            parametros_partidas_anteriores = []


            if programa:

                filtros_partidas_anteriores.append(
                    "p.programa = %s"
                )

                parametros_partidas_anteriores.append(
                    programa
                )


            if partida:

                filtros_partidas_anteriores.append(
                    "p.num_part = %s"
                )

                parametros_partidas_anteriores.append(
                    partida
                )


            if fuente:

                filtros_partidas_anteriores.append(
                    "p.fuente = %s"
                )

                parametros_partidas_anteriores.append(
                    fuente
                )


            if filtros_partidas_anteriores:

                condiciones_anteriores.append(
                    f"""
                    EXISTS (
                        SELECT 1
                        FROM partidas p

                        WHERE
                            p.requerimiento_id =
                            t.requerimiento_id

                            AND {
                                " AND ".join(
                                    filtros_partidas_anteriores
                                )
                            }
                    )
                    """
                )

                parametros_anteriores.extend(
                    parametros_partidas_anteriores
                )


            where_anteriores = (
                " WHERE "
                + " AND ".join(
                    condiciones_anteriores
                )
            )


            cur.execute(
                f"""
                SELECT
                    COALESCE(
                        SUM(
                            CASE
                                WHEN EXISTS (
                                    SELECT 1
                                    FROM certificaciones_plurianuales cp
                                    WHERE cp.tarea_id = t.id
                                )
                                THEN COALESCE(
                                    t.valor_certificacion,
                                    0
                                )

                                ELSE
                                    COALESCE(
                                        t.valor_sin_iva,
                                        0
                                    )
                                    +
                                    COALESCE(
                                        t.valor_exento,
                                        0
                                    )
                            END
                        ),
                        0
                    )

                FROM tareas t

                LEFT JOIN tipo_procesos tp
                    ON t.tipo_proceso =
                       tp.id::TEXT

                {where_anteriores}
                """,
                parametros_anteriores
            )


            monto_anterior_periodo = float(
                cur.fetchone()[0] or 0
            )


            # ======================================================
            # 8.5 MONTO ACUMULADO PROYECTADO AL MES OBJETIVO
            #
            # Histórico previo
            # +
            # período real/proyectado calculado por el motor.
            # ======================================================

            monto_proyectado_acumulado = (
                monto_anterior_periodo
                +
                proyeccion_acumulada_objetivo
            )


            # ======================================================
            # 8.6 PORCENTAJE PROYECTADO DEL PAC
            # ======================================================

            if pac_ambito_seleccionado > 0:

                porcentaje_pac_proyectado = (
                    monto_proyectado_acumulado
                    /
                    pac_ambito_seleccionado
                    *
                    100
                )


            # ======================================================
            # 8.7 SALDO DEL PAC QUE SE ESTIMA NO HABRÁ INGRESADO
            #     AL MES OBJETIVO
            #
            # Todavía NO significa "no devengado".
            # Es únicamente PAC no movilizado a contratación.
            # ======================================================

            saldo_pac_proyectado = (
                pac_ambito_seleccionado
                -
                monto_proyectado_acumulado
            )


            if saldo_pac_proyectado < 0:

                saldo_pac_proyectado = 0


            # ======================================================
            # 8.8 REDONDEAR INDICADORES EJECUTIVOS
            # ======================================================

            pac_ambito_seleccionado = round(
                pac_ambito_seleccionado,
                2
            )

            monto_anterior_periodo = round(
                monto_anterior_periodo,
                2
            )

            monto_proyectado_acumulado = round(
                monto_proyectado_acumulado,
                2
            )

            porcentaje_pac_proyectado = round(
                porcentaje_pac_proyectado,
                2
            )

            saldo_pac_proyectado = round(
                saldo_pac_proyectado,
                2
            )
        # ==========================================================
        # 9. ESCENARIOS DE PROYECCIÓN
        #
        # Conservador  = -20% sobre el ritmo actual
        # Actual       = ritmo proyectado actual
        # Acelerado    = +20% sobre el ritmo actual
        # ==========================================================

        escenario_conservador_pct = 0
        escenario_actual_pct = 0
        escenario_acelerado_pct = 0

        escenario_conservador_monto = 0
        escenario_actual_monto = 0
        escenario_acelerado_monto = 0

        escenario_conservador_pendiente = 0
        escenario_actual_pendiente = 0
        escenario_acelerado_pendiente = 0


        if (
            proyeccion_generada
            and pac_ambito_seleccionado > 0
        ):

            # ==============================================
            # BASE MENSUAL DE CADA ESCENARIO
            # ==============================================

            ritmo_conservador = (
                promedio_mensual_proyectado
                * 0.80
            )

            ritmo_actual = (
                promedio_mensual_proyectado
            )

            ritmo_acelerado = (
                promedio_mensual_proyectado
                * 1.20
            )


            # ==============================================
            # MONTO YA REALIZADO HASTA EL CORTE
            #
            # Este valor no cambia entre escenarios.
            # ==============================================

            base_real = (
                monto_anterior_periodo
                +
                total_periodo_analizado
            )


            # ==============================================
            # SI EL MES DE CORTE ESTÁ PARCIAL,
            # CALCULAMOS SOLO LO QUE FALTA PARA CERRARLO
            # ==============================================

            faltante_mes_corte = 0

            if mes_corte_es_parcial:

                faltante_mes_corte = max(
                    0,
                    monto_mes_corte_estimado
                    -
                    monto_mes_corte_real
                )


            # ==============================================
            # MESES FUTUROS COMPLETOS
            # ==============================================

            meses_futuros = (
                meses_futuros_generados
            )


            # ==============================================
            # ESCENARIO CONSERVADOR
            # ==============================================

            escenario_conservador_monto = (
                base_real
                +
                faltante_mes_corte
                +
                (
                    ritmo_conservador
                    *
                    meses_futuros
                )
            )


            # ==============================================
            # ESCENARIO ACTUAL
            # ==============================================

            escenario_actual_monto = (
                base_real
                +
                faltante_mes_corte
                +
                (
                    ritmo_actual
                    *
                    meses_futuros
                )
            )


            # ==============================================
            # ESCENARIO ACELERADO
            # ==============================================

            escenario_acelerado_monto = (
                base_real
                +
                faltante_mes_corte
                +
                (
                    ritmo_acelerado
                    *
                    meses_futuros
                )
            )


            # ==============================================
            # LIMITAR AL PAC ANALIZADO
            # ==============================================

            escenario_conservador_monto = min(
                escenario_conservador_monto,
                pac_ambito_seleccionado
            )

            escenario_actual_monto = min(
                escenario_actual_monto,
                pac_ambito_seleccionado
            )

            escenario_acelerado_monto = min(
                escenario_acelerado_monto,
                pac_ambito_seleccionado
            )


            # ==============================================
            # PORCENTAJES
            # ==============================================

            escenario_conservador_pct = (
                escenario_conservador_monto
                /
                pac_ambito_seleccionado
                *
                100
            )

            escenario_actual_pct = (
                escenario_actual_monto
                /
                pac_ambito_seleccionado
                *
                100
            )

            escenario_acelerado_pct = (
                escenario_acelerado_monto
                /
                pac_ambito_seleccionado
                *
                100
            )


            # ==============================================
            # SALDO PENDIENTE
            # ==============================================

            escenario_conservador_pendiente = max(
                0,
                pac_ambito_seleccionado
                -
                escenario_conservador_monto
            )

            escenario_actual_pendiente = max(
                0,
                pac_ambito_seleccionado
                -
                escenario_actual_monto
            )

            escenario_acelerado_pendiente = max(
                0,
                pac_ambito_seleccionado
                -
                escenario_acelerado_monto
            )


            # ==============================================
            # REDONDEAR
            # ==============================================

            escenario_conservador_monto = round(
                escenario_conservador_monto,
                2
            )

            escenario_actual_monto = round(
                escenario_actual_monto,
                2
            )

            escenario_acelerado_monto = round(
                escenario_acelerado_monto,
                2
            )

            escenario_conservador_pct = round(
                escenario_conservador_pct,
                2
            )

            escenario_actual_pct = round(
                escenario_actual_pct,
                2
            )

            escenario_acelerado_pct = round(
                escenario_acelerado_pct,
                2
            )

            escenario_conservador_pendiente = round(
                escenario_conservador_pendiente,
                2
            )

            escenario_actual_pendiente = round(
                escenario_actual_pendiente,
                2
            )

            escenario_acelerado_pendiente = round(
                escenario_acelerado_pendiente,
                2
            )
        # ==========================================================
        # 10. ANALISIS POR PARTIDA PRESUPUESTARIA
        # ==========================================================

        partidas_analisis = []

        if pac_id:

            # ==============================================
            # 10.1 PAC POR PARTIDA
            # ==============================================

            condiciones_partidas_pac = [
                "pac_version_id = %s"
            ]

            parametros_partidas_pac = [
                pac_id
            ]

            if unidad:

                if " - " in unidad:

                    nombre_unidad, bloque_unidad = unidad.split(
                        " - ",
                        1
                    )

                    condiciones_partidas_pac.append(
                        "UPPER(TRIM(bloque)) = UPPER(TRIM(%s))"
                    )

                    parametros_partidas_pac.append(
                        bloque_unidad
                    )

                else:

                    condiciones_partidas_pac.append(
                        "UPPER(TRIM(unidad)) = UPPER(TRIM(%s))"
                    )

                    parametros_partidas_pac.append(
                        unidad
                    )

            if programa:

                condiciones_partidas_pac.append(
                    "programa = %s"
                )

                parametros_partidas_pac.append(
                    programa
                )

            if partida:

                condiciones_partidas_pac.append(
                    "partida = %s"
                )

                parametros_partidas_pac.append(
                    partida
                )

            if fuente:

                condiciones_partidas_pac.append(
                    "fuente = %s"
                )

                parametros_partidas_pac.append(
                    fuente
                )

            where_partidas_pac = (
                " WHERE "
                + " AND ".join(
                    condiciones_partidas_pac
                )
            )

            cur.execute(
                f"""
                SELECT
                    partida,
                    COALESCE(SUM(subtotal), 0) AS monto_pac
                FROM pac_detalle

                {where_partidas_pac}

                GROUP BY partida

                ORDER BY partida
                """,
                parametros_partidas_pac
            )

            pac_por_partida = {
                fila[0]: float(fila[1] or 0)
                for fila in cur.fetchall()
            }


            # ==============================================
            # 10.2 MONTO INGRESADO POR PARTIDA
            # ==============================================

            condiciones_partidas_ingreso = [

                """
                UPPER(
                    TRIM(
                        COALESCE(
                            t.estado_requerimiento,
                            ''
                        )
                    )
                ) <> 'DEVUELTO'
                """,

                """
                UPPER(
                    TRIM(
                        COALESCE(
                            tp.nombre_proceso,
                            ''
                        )
                    )
                ) NOT IN (
                    'VERIFICACION DE PRODUCCION NACIONAL',
                    'ARRENDAMIENTOS DE BIENES MUEBLES'
                )
                """
            ]

            parametros_partidas_ingreso = []


            if unidad:

                if " - " in unidad:

                    nombre_unidad, bloque_unidad = unidad.split(
                        " - ",
                        1
                    )

                    condiciones_partidas_ingreso.append("""
                        EXISTS (
                            SELECT 1
                            FROM requerimientos r_unidad
                            JOIN unidades u_unidad
                                ON u_unidad.id = r_unidad.unid_requirente

                            WHERE r_unidad.id = t.requerimiento_id
                            AND UPPER(TRIM(u_unidad.bloque)) = UPPER(TRIM(%s))
                        )
                    """)

                    parametros_partidas_ingreso.append(
                        bloque_unidad
                    )

                else:

                    condiciones_partidas_ingreso.append("""
                        EXISTS (
                            SELECT 1
                            FROM requerimientos r_unidad
                            JOIN unidades u_unidad
                                ON u_unidad.id = r_unidad.unid_requirente

                            WHERE r_unidad.id = t.requerimiento_id
                            AND UPPER(TRIM(u_unidad.nombre_unidad)) = UPPER(TRIM(%s))
                        )
                    """)

                    parametros_partidas_ingreso.append(
                        unidad
                    )


            if programa:

                condiciones_partidas_ingreso.append(
                    "p.programa = %s"
                )

                parametros_partidas_ingreso.append(
                    programa
                )


            if partida:

                condiciones_partidas_ingreso.append(
                    "p.num_part = %s"
                )

                parametros_partidas_ingreso.append(
                    partida
                )


            if fuente:

                condiciones_partidas_ingreso.append(
                    "p.fuente = %s"
                )

                parametros_partidas_ingreso.append(
                    fuente
                )


            where_partidas_ingreso = (
                " WHERE "
                + " AND ".join(
                    condiciones_partidas_ingreso
                )
            )


            cur.execute(
                f"""
                SELECT
                    p.num_part,
                    COALESCE(
                        SUM(
                            COALESCE(
                                p.monto,
                                0
                            )
                        ),
                        0
                    ) AS monto_ingresado

                FROM partidas p

                JOIN tareas t
                    ON t.requerimiento_id = p.requerimiento_id

                LEFT JOIN tipo_procesos tp
                    ON t.tipo_proceso = tp.id::TEXT

                {where_partidas_ingreso}

                GROUP BY
                    p.num_part

                ORDER BY
                    p.num_part
                """,
                parametros_partidas_ingreso
            )

            ingresado_por_partida = {
                fila[0]: float(fila[1] or 0)
                for fila in cur.fetchall()
            }


            # ==============================================
            # 10.3 COMPARACION PAC VS INGRESADO
            # ==============================================

            for numero_partida, monto_pac_partida in pac_por_partida.items():

                monto_ingresado_partida = float(
                    ingresado_por_partida.get(
                        numero_partida,
                        0
                    )
                )

                pendiente_partida = max(
                    0,
                    monto_pac_partida
                    -
                    monto_ingresado_partida
                )

                porcentaje_partida = 0

                if monto_pac_partida > 0:

                    porcentaje_partida = min(
                        100,
                        (
                            monto_ingresado_partida
                            /
                            monto_pac_partida
                            *
                            100
                        )
                    )

                partidas_analisis.append({
                    "partida": numero_partida,
                    "pac": round(
                        monto_pac_partida,
                        2
                    ),
                    "ingresado": round(
                        monto_ingresado_partida,
                        2
                    ),
                    "pendiente": round(
                        pendiente_partida,
                        2
                    ),
                    "porcentaje": round(
                        porcentaje_partida,
                        2
                    )
                })    
            
            
       
        return render_template(
            "inteligencia_financiera/dashboard.html",

            pac_id=pac_id,
            pac_anio=pac_anio,
            pac_reforma=pac_reforma,

            monto_pac=monto_pac,
            monto_ingresado=monto_ingresado,
            monto_certificado=monto_certificado,
            monto_adjudicado=monto_adjudicado,
            fecha_inicio=fecha_inicio,
            fecha_corte=fecha_corte,
            proyectar_hasta=proyectar_hasta,

            unidad=unidad,
            programa=programa,
            partida=partida,
            fuente=fuente,

            unidades_filtro=unidades_filtro,
            programas_filtro=programas_filtro,
            partidas_filtro=partidas_filtro,
            fuentes_filtro=fuentes_filtro,
            
            analisis_generado=analisis_generado,
            mensaje_analisis=mensaje_analisis,

            meses_labels=meses_labels,
            montos_mensuales=montos_mensuales,

            total_periodo_analizado=total_periodo_analizado,
            # ==========================================
            # DATOS DEL MOTOR DE PROYECCIÓN
            # ==========================================
            proyeccion_generada=proyeccion_generada,
            mensaje_proyeccion=mensaje_proyeccion,

            ritmo_diario_mes_corte=ritmo_diario_mes_corte,
            monto_mes_corte_real=monto_mes_corte_real,
            monto_mes_corte_estimado=monto_mes_corte_estimado,

            promedio_mensual_proyectado=promedio_mensual_proyectado,
            proyeccion_acumulada_objetivo=proyeccion_acumulada_objetivo,

            mes_corte_es_parcial=mes_corte_es_parcial,

            grafico_labels=grafico_labels,
            serie_real_grafico=serie_real_grafico,
            serie_proyectada_grafico=serie_proyectada_grafico,
            # ==========================================
            # COMPARACIÓN PROYECTADA CONTRA EL PAC
            # ==========================================
            pac_ambito_seleccionado=pac_ambito_seleccionado,
            monto_anterior_periodo=monto_anterior_periodo,
            monto_proyectado_acumulado=monto_proyectado_acumulado,
            porcentaje_pac_proyectado=porcentaje_pac_proyectado,
            saldo_pac_proyectado=saldo_pac_proyectado,
            
            escenario_conservador_monto=escenario_conservador_monto,
            escenario_actual_monto=escenario_actual_monto,
            escenario_acelerado_monto=escenario_acelerado_monto,

            escenario_conservador_pct=escenario_conservador_pct,
            escenario_actual_pct=escenario_actual_pct,
            escenario_acelerado_pct=escenario_acelerado_pct,

            escenario_conservador_pendiente=escenario_conservador_pendiente,
            escenario_actual_pendiente=escenario_actual_pendiente,
            escenario_acelerado_pendiente=escenario_acelerado_pendiente,
            partidas_analisis=partidas_analisis,
        )
    
    finally:

        cur.close()
        conn.close()