# ============================================
# EXTENSIONES GLOBALES DE LA APLICACIÓN
# ============================================

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Inicializar extensiones como variables globales
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()