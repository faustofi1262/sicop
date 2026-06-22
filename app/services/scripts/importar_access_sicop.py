import os
import pandas as pd
from app.routes import get_connection

BASE = os.path.dirname(os.path.abspath(__file__))

def limpio(valor):
    if pd.isna(valor):
        return None
    return str(valor).strip()

def numero(valor):
    if pd.isna(valor):
        return 0
    try:
        return float(valor)
    except:
        return 0

def fecha(valor):
    if pd.isna(valor):
        return None
    try:
        return pd.to_datetime(valor).date()
    except:
        return None

df = pd.read_excel(os.path.join(BASE, "tareas.xlsx"))

conn = get_connection()
cur = conn.cursor()

insertados = 0
omitidos = 0

for _, row in df.iterrows():

    req_id = int(row["Id"])

    cur.execute("SELECT id FROM requerimientos WHERE id = %s", (req_id,))
    if cur.fetchone():
        omitidos += 1
        continue

    cur.execute("""
        INSERT INTO requerimientos (
            id,
            mem_requi,
            fecha_memo_requi,
            unid_requirente,
            memo_vice_ad,
            fecha_memo_vice_ad,
            memo_dir_ad,
            fecha_memo_dir_ad,
            fecha_recep_req,
            breve_descr,
            monto_req,
            funcionario_encargado,
            programa,
            descripcion,
            fuente_financiamiento,
            numero_partida
        )
        VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s
        )
    """, (
        req_id,
        limpio(row.get("Num_of_area_req")),
        fecha(row.get("Fecha_of_area_req")),
        int(row.get("Nombre_unidad_solicita")) if not pd.isna(row.get("Nombre_unidad_solicita")) else None,
        limpio(row.get("Num_of_vadm")),
        fecha(row.get("Fecha_of_vadm")),
        limpio(row.get("num_of_dir_ad")),
        fecha(row.get("Fecha_of_dir_ad")),
        fecha(row.get("fecha_recep_ucp")),
        limpio(row.get("breve_descripcion")),
        numero(row.get("Monto_solicitado_req")),
        limpio(row.get("Persona_asignada")),
        limpio(row.get("Cuatrimestre")),
        limpio(row.get("Objeto_contratacion")),
        limpio(row.get("Fondo")),
        limpio(row.get("Posición Presupuestaria"))
    ))

    insertados += 1

#cur.execute("""
#    SELECT setval(
#        'requerimientos_id_seq',
#        COALESCE((SELECT MAX(id) FROM requerimientos), 1)
#    )
#""")

conn.commit()
cur.close()
conn.close()

print("✅ IMPORTACIÓN DE REQUERIMIENTOS COMPLETADA")
print("Insertados:", insertados)
print("Omitidos:", omitidos)