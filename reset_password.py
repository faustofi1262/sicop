import os
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()  # carga DATABASE_URL desde .env

DATABASE_URL = os.getenv("DATABASE_URL")

usuario = "ffigueroa"
nueva_password = "Admin2026!"  # 👈 la que tú quieras

hash_nuevo = generate_password_hash(nueva_password)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute(
    "UPDATE usuarios SET password_hash = %s WHERE usuario = %s",
    (hash_nuevo, usuario)
)
conn.commit()
cur.close()
conn.close()

print("✅ Contraseña actualizada para:", usuario)
