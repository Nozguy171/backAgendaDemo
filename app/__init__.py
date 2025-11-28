from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    db.init_app(app)

    with app.app_context():
        from .routes.tenants import tenants_bp
        from .routes.services import services_bp
        from .routes.customers import customers_bp
        from .routes.appointments import appointments_bp
        from .routes.admin import admin_bp
        from app.routes.availability import availability_bp
        app.register_blueprint(tenants_bp, url_prefix="/tenants")
        app.register_blueprint(services_bp, url_prefix="/services")
        app.register_blueprint(customers_bp, url_prefix="/customers")
        app.register_blueprint(appointments_bp, url_prefix="/appointments")
        app.register_blueprint(admin_bp, url_prefix="/admin")
        app.register_blueprint(availability_bp)

        db.create_all()

    return app
