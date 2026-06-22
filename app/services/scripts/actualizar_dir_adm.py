import os
import pandas as pd
from app.routes import get_connection

BASE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_excel(os.path.join(BASE, "tareas.xlsx"))

def limpio(v):
    if pd.isna(v):
        return None
    return str(v).strip()

def fecha(v):
    if pd.isna(v):
        return None
    try:
        return pd.to_datetime(v).date()
    except:
        return None

print("Columnas:", list(df.columns[:10]))

fila_116 = df[df["Id"] == 116]
print("Fila 116:")
print(fila_116[["Id", "num_of_dir_adm", "Fecha_of_dir_adm"]])

conn = get_connection()
cur = conn.cursor()

actualizados = 0

for _, row in df.iterrows():
    req_id = int(row["Id"])
    memo = limpio(row.get("num_of_dir_adm"))
    fec = fecha(row.get("Fecha_of_dir_adm"))

    cur.execute("""
        UPDATE requerimientos
        SET memo_dir_ad = %s,
            fecha_memo_dir_ad = %s
        WHERE id = %s
    """, (memo, fec, req_id))

    actualizados += cur.rowcount

conn.commit()
cur.close()
conn.close()

print("Actualizados reales:", actualizados)
