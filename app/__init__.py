from flask import Flask, app
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "sicop_secret_key_2026")

    from .routes import main
    app.register_blueprint(main)
    from .inteligencia_routes import inteligencia
    app.register_blueprint(inteligencia) 
    from .planificacion_routes import planificacion
    app.register_blueprint(planificacion)
    
    from .inteligencia_financiera_routes import inteligencia_financiera
    app.register_blueprint(inteligencia_financiera)
    
    from app.consultas_routes import consultas_bp
    app.register_blueprint(consultas_bp)
    
    return app

