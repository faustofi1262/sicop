import re
from pypdf import PdfReader


def extraer_texto_pdf(ruta_pdf):
    """
    Extrae texto de un PDF.
    El archivo se usa solo temporalmente.
    """

    reader = PdfReader(ruta_pdf)

    partes = []

    for pagina in reader.pages:

        texto = pagina.extract_text() or ""

        if texto.strip():
            partes.append(texto)

    texto_completo = "\n".join(partes)

    if not texto_completo.strip():
        raise ValueError(
            "No se pudo extraer texto del PDF."
        )

    return texto_completo


def limpiar_texto(texto):

    texto = texto.replace("\r", "\n")

    texto = re.sub(
        r"\n{3,}",
        "\n\n",
        texto
    )

    return texto.strip()


def extraer_articulos(texto):
    """
    Extrae únicamente ARTÍCULOS reales de la normativa.

    Reconoce formatos como:
    Art. 1.-
    Art. 2.-
    Artículo 3.-
    Artículo 121.-

    Se detiene cuando encuentra secciones como:
    DISPOSICIONES GENERALES
    DISPOSICIONES TRANSITORIAS
    DISPOSICIONES REFORMATORIAS
    DISPOSICIONES DEROGATORIAS
    DISPOSICIÓN FINAL
    """

    texto = limpiar_texto(texto)

    # =========================================================
    # 1. CORTAR EL TEXTO ANTES DE LAS DISPOSICIONES
    # =========================================================

    texto_articulos = texto


    # =========================================================
    # 2. BUSCAR SOLO ENCABEZADOS REALES DE ARTÍCULO
    # =========================================================

    patron_articulo = re.compile(
        r"""
        ^\s*
        (?:ART[ÍI]CULO|ART\.)
        \s*
        (\d{1,3})
        \s*
        (?:[\.\-–—:]+)
        """,
        re.IGNORECASE | re.MULTILINE | re.VERBOSE
    )

    coincidencias = list(
        patron_articulo.finditer(texto_articulos)
    )

    if not coincidencias:
        raise ValueError(
            "No se pudieron identificar artículos en el PDF."
        )


    articulos = []


    # =========================================================
    # 3. EXTRAER BLOQUE DE CADA ARTÍCULO
    # =========================================================

    for indice, coincidencia in enumerate(coincidencias):

        inicio = coincidencia.start()

        if indice + 1 < len(coincidencias):
            fin = coincidencias[indice + 1].start()
        else:
            fin = len(texto_articulos)

        bloque = texto_articulos[inicio:fin].strip()

        numero_articulo = coincidencia.group(1)


        titulo = extraer_titulo_articulo(
            bloque,
            numero_articulo
        )


        palabras_clave = generar_palabras_clave(
            bloque
        )


        articulos.append({
            "numero_articulo": numero_articulo,
            "titulo": titulo,
            "contenido": bloque,
            "palabras_clave": palabras_clave
        })


    # =========================================================
    # 4. EVITAR DUPLICADOS
    # =========================================================

    articulos_unicos = {}

    for articulo in articulos:

        numero = articulo["numero_articulo"]

        if numero not in articulos_unicos:
            articulos_unicos[numero] = articulo


    resultado = list(
        articulos_unicos.values()
    )


    # =========================================================
    # 5. ORDENAR NUMÉRICAMENTE
    # =========================================================

    resultado.sort(
        key=lambda x: int(x["numero_articulo"])
    )


    return resultado
def extraer_titulo_articulo(
    bloque,
    numero_articulo
):
    """
    Obtiene únicamente el título del artículo.

    Ejemplo:
    Art. 121.- Procedimiento sancionatorio.- Cuando...
    
    devuelve:
    Procedimiento sancionatorio
    """

    if not bloque:
        return None

    # Unir saltos de línea para poder detectar el título
    texto = re.sub(
        r"\s+",
        " ",
        bloque
    ).strip()

    # Quitar "Art. 121.-" o "Artículo 121.-"
    texto = re.sub(
        rf"""
        ^\s*
        (?:ART[ÍI]CULO|ART\.)
        \s*
        {re.escape(str(numero_articulo))}
        \s*
        [\.\-–—:]*
        \s*
        """,
        "",
        texto,
        flags=re.IGNORECASE | re.VERBOSE
    )

    # Buscar el primer ".-" que normalmente
    # separa el título del cuerpo del artículo
    separador = re.search(
        r"\.\s*[-–—]\s*",
        texto
    )

    if separador:

        titulo = texto[
            :separador.start()
        ].strip()

    else:

        # Si el artículo no tiene el formato ".-",
        # usamos solamente una porción prudente
        titulo = texto[:200].strip()

    # Limpiar guiones sobrantes
    titulo = titulo.strip(
        " .-–—:"
    )

    if not titulo:
        return None

    return titulo[:250]



def generar_palabras_clave(texto):
    """
    Generación inicial simple.
    Después podemos mejorarla con IA.
    """

    texto_minuscula = texto.lower()

    palabras_interes = [
        "necesidad",
        "planificación",
        "contratación",
        "presupuesto",
        "estudio de mercado",
        "especificaciones técnicas",
        "términos de referencia",
        "plazo",
        "forma de pago",
        "garantía",
        "oferente",
        "proveedor",
        "adjudicación",
        "mejor valor por dinero",
        "eficiencia",
        "efectividad",
        "competencia",
        "transparencia",
        "control",
        "administrador de contrato"
    ]

    encontradas = []

    for palabra in palabras_interes:

        if palabra in texto_minuscula:
            encontradas.append(palabra)

    return ", ".join(encontradas)