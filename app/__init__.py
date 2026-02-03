# ============================================
# INICIALIZACIÓN DE LA APLICACIÓN FLASK
# ============================================
from flask import Flask, send_from_directory
import os

# Importar extensiones desde módulo separado
from app.extensions import db, login_manager, bcrypt, migrate


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
    migrate.init_app(app, db)

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # User loader para Flask-Login
    from app.models.user import User
    
    # Importar modelos RBAC para registro en SQLAlchemy/Migraciones
    from app.models import rbac

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar context processors desde módulo separado
    from app.utils.context_processors import register_context_processors
    register_context_processors(app)
    
    # --- SEGURIDAD: Validar sesión en cada request ---
    from flask import request, redirect, url_for, session
    from flask_login import current_user, logout_user
    from app.utils.session_manager import validate_session
    
    @app.before_request
    def check_valid_session():
        # Si el usuario está logueado pero no tiene una sesión válida en DB
        if current_user.is_authenticated:
            # RUTAS EXCLUIDAS: No validar sesión en estas rutas para evitar bucles infinitos
            # o porque son necesarias antes de validar (como logout)
            excluded_endpoints = ['auth.login', 'auth.logout', 'static', 'favicon']
            
            # Verificar si el endpoint actual está excluido
            is_excluded = False
            if not request.endpoint:
                is_excluded = True # Si no hay endpoint, es probablemente un error o ruta especial
            else:
                for endpoint in excluded_endpoints:
                    if endpoint in request.endpoint:
                        is_excluded = True
                        break
            
            if not is_excluded:
                if not validate_session():
                    logout_user()
                    session.clear()
                    # Opcional: flash('Tu sesión ha expirado.', 'warning')
                    return redirect(url_for('auth.login'))

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
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    from app.routes.icecat_routes import icecat_bp
    from app.models.system_setting import SystemSetting

    app.register_blueprint(icecat_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(catalog_api_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(serial_api)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

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