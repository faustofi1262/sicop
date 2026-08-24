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
    from app.normativa_control_routes import normativa_control_bp
    app.register_blueprint(consultas_bp)
    app.register_blueprint(normativa_control_bp)
    # ==========================================================
# REGISTRO DEL MÓDULO CONTROL Y EVIDENCIA
# ==========================================================
# Permite habilitar las rutas correspondientes al módulo
# independiente de seguimiento y evidencia institucional.
# ==========================================================

    from app.control_evidencia_routes import control_evidencia_bp

    app.register_blueprint(control_evidencia_bp)
    
   
   
  
  
    return app

