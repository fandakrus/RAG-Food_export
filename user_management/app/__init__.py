from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from user_management.app.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)

    with app.app_context():
        from .routes import init_routes
        init_routes(app)
        db.create_all()

    return app