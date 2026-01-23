# ============================================
# CONFIGURACIÓN DE LOGGING PARA LA APLICACIÓN
# ============================================

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """
    Configura el sistema de logging para la aplicación Flask

    Args:
        app: Instancia de la aplicación Flask
    """
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Configurar file handler con rotación
    file_handler = RotatingFileHandler(
        'logs/luxera.log',
        maxBytes=10240000,  # 10 MB
        backupCount=10
    )

    # Configurar formato del log
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))

    # Establecer nivel de logging
    file_handler.setLevel(logging.INFO)

    # Añadir handler al logger de la aplicación
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Mensaje inicial
    app.logger.info('Luxera startup - Logging configurado')