# ============================================
# INICIALIZACIÓN DE LA APLICACIÓN FLASK
# ============================================
from flask import Flask, send_from_directory
import os

# Importar extensiones desde módulo separado
from app.extensions import db, login_manager, bcrypt


def create_app(config_name='development'):
    """
    Factory pattern para crear la aplicación Flask
    """
    from config import config

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # User loader para Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar context processors desde módulo separado
    from app.utils.context_processors import register_context_processors
    register_context_processors(app)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )

    # Registrar Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.inventory import inventory_bp
    from app.routes.api.catalog_api import catalog_api_bp
    from app.routes.api.customers import customers_bp
    from app.routes.invoices import invoices_bp
    from app.routes.expenses import bp as expenses_bp
    from app.routes.public import public_bp
    from app.routes.serial_api import serial_api
    from app.routes.dashboard import dashboard_bp  # <--- Agregado

    app.register_blueprint(public_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(catalog_api_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(serial_api)
    app.register_blueprint(dashboard_bp)  # <--- Agregado

    # Configuración de CORS para APIs
    from flask_cors import CORS
    CORS(app, resources={
        r"/expenses/api/*": {
            "origins": ["http://localhost:5000", "http://tudominio.com"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Registrar manejadores de errores
    from app.routes.main import register_error_handlers
    register_error_handlers(app)

    # Configurar logging desde módulo separado (solo en producción)
    if not app.debug and not app.testing:
        from app.utils.logging_config import setup_logging
        setup_logging(app)

    # Registrar comandos CLI desde módulo separado
    from app.cli import register_cli_commands
    register_cli_commands(app)

    return app