from werkzeug.security import generate_password_hash
import psycopg2
import os

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

password_hash = generate_password_hash("123456")

cur.execute("""
UPDATE usuarios
SET password_hash = %s
WHERE usuario = 'ffigueroa'
""", (password_hash,))

conn.commit()
conn.close()

print("✅ Contraseña actualizada")
