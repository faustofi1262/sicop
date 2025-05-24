from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.orm import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    correo = Column(String(120), unique=True)
    contraseña = Column(String(120))
    rol = Column(String(50))  # Admin, Técnico, etc.

class PartidaPAC(Base):
    __tablename__ = 'partidas_pac'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20))
    descripcion = Column(Text)
    unidad = Column(String(50))
    presupuesto = Column(Integer)
    fecha_creacion = Column(Date)
