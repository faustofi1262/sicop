# ============================================================
# SERVICIO DE LECTURA DE PDF
# CONTROL Y EVIDENCIA - SICOP
#
# El archivo se procesa EN MEMORIA.
# NO se guarda físicamente en el servidor.
# ============================================================

from io import BytesIO

from pypdf import PdfReader


def extraer_texto_pdf_control(archivo_pdf):

    if not archivo_pdf:
        raise ValueError(
            "No se recibió ningún archivo PDF."
        )

    # Leer archivo completo en memoria
    contenido = archivo_pdf.read()

    if not contenido:
        raise ValueError(
            "El archivo PDF está vacío."
        )

    # Crear PDF virtual en memoria
    memoria_pdf = BytesIO(contenido)

    try:

        lector = PdfReader(memoria_pdf)

    except Exception as e:

        raise ValueError(
            f"No fue posible abrir el PDF: {e}"
        )


    if not lector.pages:

        raise ValueError(
            "El PDF no contiene páginas."
        )


    textos = []

    for numero_pagina, pagina in enumerate(
        lector.pages,
        start=1
    ):

        try:

            texto = pagina.extract_text() or ""

            texto = texto.strip()

            if texto:

                textos.append(
                    f"\n--- PÁGINA {numero_pagina} ---\n"
                    f"{texto}"
                )

        except Exception as e:

            print(
                f"Error leyendo página {numero_pagina}:",
                e
            )


    texto_completo = "\n".join(textos).strip()


    # Si prácticamente no se pudo extraer texto,
    # probablemente sea un PDF escaneado.
    if len(texto_completo) < 100:

        raise ValueError(
            "No se pudo extraer suficiente texto del PDF. "
            "El documento podría estar escaneado como imagen."
        )


    # Evitar mandar accidentalmente documentos gigantes
    # completos al modelo.
    LIMITE_CARACTERES = 120000

    if len(texto_completo) > LIMITE_CARACTERES:

        texto_completo = texto_completo[
            :LIMITE_CARACTERES
        ]


    return texto_completo