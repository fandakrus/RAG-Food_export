from flask import Blueprint

def init_routes(app):
    from .singup import auth_bp
    from .render_page import page_bp
    from .admin import admin_bp
    from .reset_password import reset_password_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reset_password_bp)
