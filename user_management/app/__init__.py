from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

from .config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']

    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'

    db.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)

    with app.app_context():
        from .routes import init_routes
        init_routes(app)
        db.create_all()

    return app