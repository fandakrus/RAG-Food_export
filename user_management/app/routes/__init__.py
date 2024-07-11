from flask import Blueprint

def init_routes(app):
    from .singup import auth_bp
    from .singup_page import signup_page_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(signup_page_bp)
