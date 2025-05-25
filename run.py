from flask import Flask
from dotenv import load_dotenv
from app import create_app
import os
load_dotenv()
app = create_app()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
@app.route('/')
def index():
    return "SICOP funcionando en Render!"

if __name__ == '__main__':
    app.run()
