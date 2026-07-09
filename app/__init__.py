"""Factory Flask — crée l'application avec tous les blueprints."""
import os
from flask import Flask
from config import get_config
from app.extensions import init_directories
from app.utils.logger import setup_logging
from app.security.encryption import EncryptionService
from app.repositories.user_repository import init_tables


def create_app() -> Flask:
    setup_logging()
    init_directories()

    # Initialiser le chiffrement
    EncryptionService.get()

    # Initialiser la BDD
    init_tables()

    app = Flask(__name__,
                template_folder="templates",
                static_folder="static")

    cfg = get_config()
    app.config.from_object(cfg)
    app.secret_key = cfg.SECRET_KEY

    # Blueprints
    from app.routes.auth_routes   import bp as auth_bp
    from app.routes.admin_routes  import bp as admin_bp
    from app.routes.api_routes    import bp as api_bp
    from app.routes.webcam_routes import bp as webcam_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(webcam_bp)

    return app
