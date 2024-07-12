from flask import Blueprint

def init_routes(app):
    from .singup import auth_bp
    from .render_page import page_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(admin_bp)
