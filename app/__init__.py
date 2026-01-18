from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    from .routes import main
    #from .auth_old import auth

    app.register_blueprint(main)
    #app.register_blueprint(auth_old)

    return app