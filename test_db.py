from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL[:30], "...")  # solo para verificar
print("Conectando a la base...")

conn = psycopg2.connect(DATABASE_URL)
print("✅ Conectado a Neon")

cur = conn.cursor()
cur.execute("SELECT id, usuario, rol FROM usuarios")
rows = cur.fetchall()

print("Usuarios encontrados:")
for r in rows:
    print(r)

cur.close()
conn.close()
