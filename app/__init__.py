from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "sicop_secret_key_2026")

    from .routes import main
    app.register_blueprint(main)
    from app.inteligencia_routes import inteligencia
    app.register_blueprint(inteligencia)
    
    return app

