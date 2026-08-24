import os
from openai import OpenAI

CRITERIOS_DOCUMENTO = {

    "ESTUDIOS_PREVIOS": """
Analiza el documento como ESTUDIOS PREVIOS de un procedimiento
de contratación pública.

Revisa especialmente:
- justificación de la contratación;
- antecedentes;
- objetivo;
- alcance;
- coherencia entre necesidad y contratación;
- información técnica utilizada;
- identificación de riesgos o inconsistencias;
- coherencia con el objeto de contratación;
- posibles direccionamientos;
- información que pudiera afectar la competencia;
- ausencia de información necesaria para continuar el procedimiento.
""",

    "DETERMINACION_NECESIDAD": """
Analiza el documento como DETERMINACIÓN DE LA NECESIDAD.

Revisa especialmente:
- identificación clara de la necesidad institucional;
- relación con las competencias institucionales;
- beneficio, eficiencia y efectividad;
- justificación suficiente;
- coherencia con el objeto de contratación;
- relación con planificación;
- razonabilidad de la necesidad;
- posibles inconsistencias o vacíos.
""",

    "ESPECIFICACIONES_TECNICAS": """
Analiza el documento como ESPECIFICACIONES TÉCNICAS.

Revisa especialmente:
- claridad y precisión técnica;
- características necesarias del bien;
- requisitos restrictivos o direccionados;
- referencias a marcas;
- dimensiones, capacidades y características;
- normas técnicas;
- garantías;
- condiciones de entrega;
- consistencia entre las diferentes especificaciones;
- requisitos desproporcionados.
""",

    "TERMINOS_REFERENCIA": """
Analiza el documento como TÉRMINOS DE REFERENCIA.

Revisa especialmente:
- antecedentes;
- objetivos;
- alcance;
- metodología;
- información disponible;
- productos o servicios esperados;
- plazo;
- forma de pago;
- obligaciones;
- requisitos técnicos;
- coherencia interna;
- requisitos restrictivos o innecesarios.
""",

    "PRESUPUESTO_REFERENCIAL": """
Analiza el documento como DETERMINACIÓN DEL PRESUPUESTO REFERENCIAL.

Revisa especialmente:
- metodología utilizada;
- estudio de mercado;
- fuentes consultadas;
- comparabilidad de ofertas;
- precios utilizados;
- vigencia de la información;
- cálculos;
- cantidades;
- valores unitarios;
- coherencia con el objeto;
- posibles errores o inconsistencias.
""",

    "PROFORMAS": """
Analiza las PROFORMAS utilizadas dentro del procedimiento.

Revisa especialmente:
- comparabilidad;
- descripción de productos o servicios;
- cantidades;
- precios unitarios y totales;
- impuestos;
- fechas;
- condiciones comerciales;
- posibles diferencias entre proformas;
- errores matemáticos;
- señales de falta de comparabilidad.
""",

    "OTROS_DOCUMENTOS": """
Realiza una revisión técnico-administrativa del documento.

Identifica:
- objeto y finalidad;
- inconsistencias;
- contradicciones;
- información incompleta;
- riesgos;
- datos relevantes para el procedimiento;
- aspectos que deberían ser verificados por el analista.
"""
}


def construir_prompt(tipo_documento, texto_documento):

    criterio = CRITERIOS_DOCUMENTO.get(
        tipo_documento,
        CRITERIOS_DOCUMENTO["OTROS_DOCUMENTOS"]
    )

    return f"""
Eres un asistente especializado en control previo y revisión de
documentación de contratación pública.

Tu función es apoyar a un analista humano.

NO debes inventar datos.
NO debes asumir información que no conste en el documento.
NO debes limitarte a decir "cumple" o "no cumple".
NO debes validar ni exigir el número, código o identificación formal
del documento.

Debes realizar una revisión profunda, objetiva y explicada.

TIPO DE DOCUMENTO:
{tipo_documento}

CRITERIOS ESPECÍFICOS:
{criterio}

DOCUMENTO:
-------------------------
{texto_documento}
-------------------------

Devuelve el análisis con EXACTAMENTE esta estructura:

## RESUMEN
Síntesis breve del contenido revisado.

## HALLAZGOS
Enumera los aspectos relevantes identificados.

## INCONSISTENCIAS O RIESGOS
Explica los errores, vacíos, contradicciones o riesgos encontrados.
Si no identificas ninguno, indícalo expresamente.

## NORMATIVA O CRITERIOS RELACIONADOS
Relaciona los hallazgos con principios, requisitos o normativa
únicamente cuando exista una relación razonable.
No inventes artículos.

## RECOMENDACIONES PARA EL ANALISTA
Indica qué debería revisar, solicitar, aclarar o corregir.

## CONCLUSIÓN
Indica una de estas opciones y explica brevemente:

- SIN OBSERVACIONES RELEVANTES
- CON OBSERVACIONES
- REQUIERE REVISIÓN ADICIONAL
"""


def analizar_documento_control(tipo_documento, texto_documento):

    # ============================================================
    # VALIDAR TEXTO DEL DOCUMENTO
    # ============================================================
    if not texto_documento or not texto_documento.strip():
        raise ValueError(
            "No se encontró texto suficiente para realizar el análisis."
        )


    # ============================================================
    # OBTENER API KEY
    # ============================================================
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "No está configurada la variable OPENAI_API_KEY."
        )


    # ============================================================
    # CREAR CLIENTE OPENAI
    # Se crea solamente cuando realmente se utiliza la IA.
    # ============================================================
    client = OpenAI(
        api_key=api_key
    )


    # ============================================================
    # CONSTRUIR PROMPT SEGÚN TIPO DE DOCUMENTO
    # ============================================================
    prompt = construir_prompt(
        tipo_documento,
        texto_documento
    )


    # ============================================================
    # ANALIZAR DOCUMENTO
    # ============================================================
    response = client.responses.create(
        model="gpt-5.6-terra",
        input=prompt
    )


    # ============================================================
    # DEVOLVER RESULTADO
    # ============================================================
    resultado = response.output_text

    if not resultado or not resultado.strip():
        raise ValueError(
            "La IA no devolvió un resultado de análisis."
        )

    return resultado.strip()
