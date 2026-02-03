# ============================================
# PUNTO DE ENTRADA DE LA APLICACIÓN LUXERA  Prueba
# ============================================
# Comando: python run.py

import os
from app import create_app, db
from app.models.user import User
from app.models.laptop import (
    Laptop, LaptopImage, Brand, LaptopModel, Processor,
    OperatingSystem, Screen, GraphicsCard, Storage, Ram,
    Store, Location, Supplier
)

# Crear la aplicación
config_name = os.environ.get('FLASK_ENV', 'default')
app = create_app(config_name)


# Contexto de Shell
@app.shell_context_processor
def make_shell_context():
    """Variables disponibles en flask shell"""
    return {
        'db': db,
        'User': User,
        'Laptop': Laptop,
        'LaptopImage': LaptopImage,
        'Brand': Brand,
        'LaptopModel': LaptopModel,
        'Processor': Processor,
        'OperatingSystem': OperatingSystem,
        'Screen': Screen,
        'GraphicsCard': GraphicsCard,
        'Storage': Storage,
        'Ram': Ram,
        'Store': Store,
        'Location': Location,
        'Supplier': Supplier,
    }


# Ejecutar
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)