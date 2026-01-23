# ============================================
# CONTEXT PROCESSORS PARA TEMPLATES
# ============================================

from datetime import datetime, timedelta


def register_context_processors(app):
    """
    Registra todos los context processors en la aplicación Flask
    """

    # Context processor para las funciones now() y timedelta() en templates
    @app.context_processor
    def utility_processor():
        def now():
            return datetime.utcnow()

        def make_timedelta(days=0):
            return timedelta(days=days)

        return {
            'now': now,
            'timedelta': make_timedelta
        }

    # Context processor global para variables de aplicación
    @app.context_processor
    def inject_global_vars():
        return {
            'app_name': 'Luxera',
            'app_version': '1.0.0',
            'allow_registration': app.config.get('ALLOW_REGISTRATION', False)
        }