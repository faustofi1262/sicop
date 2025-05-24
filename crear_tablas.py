from app.models import Base, engine

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    print("Tablas creadas en PostgreSQL (Neon)")
