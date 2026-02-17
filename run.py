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
    # Obtener IP local dinámicamente
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    print("\n" + "=" * 60)
    print("INICIANDO SERVIDOR LUXERA")
    print("=" * 60)
    print(f"URL Local:   http://127.0.0.1:5000")
    print(f"URL Network: http://{local_ip}:5000")
    print("=" * 60)
    print("DEBUG: ON")
    print("Comandos CLI disponibles:")
    print("   flask setup-fresh     - ⚠️ Reinicia TODO + 50 laptops")
    print("   flask reset-db        - Reinicia BD vacía")
    print("   flask create-admin    - Crear admin")
    print("   flask seed-catalog    - Poblar catálogos")
    print("   flask seed-laptops    - Crear 50 laptops")
    print("   flask list-laptops    - Ver inventario")
    print("   flask list-users      - Ver usuarios")
    print("   flask inventory-stats - Estadísticas")
    print("=" * 60)
    print("👤 Admin: felixjosemartinezbrito@gmail.com / 1234")
    print("=" * 60)
    print("💡 Presiona CTRL+C para detener")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)