from werkzeug.security import generate_password_hash
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

nueva_password = "admin123"  # 👈 puedes cambiarla luego

hash_password = generate_password_hash(nueva_password)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    UPDATE usuarios
    SET password_hash = %s
    WHERE usuario = %s
""", (hash_password, "admin"))

conn.commit()
cur.close()
conn.close()

print("✅ Contraseña del admin actualizada correctamente")
print("Usuario: admin")
print("Contraseña:", nueva_password)
