from flask import Blueprint

def init_routes(app):
    from .singup import auth_bp

    app.register_blueprint(auth_bp)
