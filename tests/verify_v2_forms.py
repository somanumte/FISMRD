
import os
import sys
from datetime import datetime

# Añadir el directorio raíz al path para importar la app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app import create_app, db
from app.services.icecat_service import IcecatService
from app.forms.laptop_forms import LaptopForm
from app.models.laptop import Brand, LaptopModel, Processor, Store
from flask import Flask, request

def test_icecat_normalization():
    print("Testing Icecat Normalization...")
    app = create_app()
    with app.app_context():
        # GTIN de una laptop ASUS conocida (debería tener specs completas)
        gtin = '195553106368'
        print(f"Fetching data for GTIN: {gtin}")
        
        result = IcecatService.fetch_by_gtin(gtin)
        
        if not result['success']:
            print(f"FAIL: Could not fetch data from Icecat: {result.get('message')}")
            return False
            
        product = result['product']
        
        # Verificar campos V2.0 clave
        expected_fields = [
            'marca', 'modelo', 'nombre_visualizacion', 
            'procesador', 'memoria_ram', 'almacenamiento',
            'pantalla', 'tarjeta_grafica', 'conectividad', 'entrada'
        ]
        
        missing = [f for f in expected_fields if f not in product]
        if missing:
            print(f"FAIL: Missing expected fields: {missing}")
            return False
            
        print("SUCCESS: Icecat data contains all expected V2.0 structures")
        
        # Verificar sub-campos específicos
        proc = product.get('procesador', {})
        if not proc.get('nombre_completo'):
            print("FAIL: Processor full name is missing")
            return False
            
        print(f"Processor: {proc.get('nombre_completo')}")
        print(f"RAM: {product.get('memoria_ram', {}).get('capacidad_gb')} GB")
        print(f"Storage: {product.get('almacenamiento', {}).get('capacidad_total_gb')} GB")
        print(f"Screen: {product.get('pantalla', {}).get('diagonal_pulgadas')}\"")
        
        return True

def test_laptop_form_validation():
    print("\nTesting LaptopForm Validation...")
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Mocking data that would come from Icecat + manual entries
        form_data = {
            'display_name': 'Test Laptop V2.0',
            'sku': 'LX-20260207-0001',
            'gtin': '1234567890123',
            'brand_id': 'ASUS',
            'model_id': 'Vivobook',
            'processor_id': 'AMD Ryzen 7 5700U',
            'processor_full_name': 'AMD Ryzen 7 5700U (8 cores, 1.8GHz)',
            'os_id': 'Windows 11 Home',
            'screen_id': '1920x1080',
            'screen_size': '15.6',
            'graphics_card_id': 'AMD Radeon Graphics',
            'has_discrete_gpu': 'n', # No
            'storage_id': 'SSD',
            'storage_capacity': '512',
            'ram_id': 'DDR4',
            'ram_capacity': '16',
            'store_id': '1', # Assuming 1 exists or will be handled by CatalogService
            'quantity': '1',
            'purchase_cost': '500.00',
            'sale_price': '750.00',
            'category': 'laptop',
            'condition': 'new',
            'is_published': 'y',
            'keyboard_backlight': 'y',
            'wifi_standard': 'Wi-Fi 6 (802.11ax)',
            'currency': 'USD',
            'warranty_months': '12',
            'public_notes': 'This is a public note for testing'
        }
        
        # Create a request context for the form to work
        with app.test_request_context(method='POST', data=form_data):
            form = LaptopForm()
            
            # Since some SelectFields might not have choices loaded yet in a raw testing app context,
            # we manually set them if needed (though __init__ should handle it if DB is ready)
            try:
                if not form.validate():
                    print("FAIL: Form validation failed")
                    from pprint import pprint
                    pprint(form.errors)
                    return False
                else:
                    print("SUCCESS: LaptopForm validated successfully with all V2.0 fields")
                    return True
            except Exception as e:
                print(f"ERROR: Exception during form validation: {str(e)}")
                return False

if __name__ == '__main__':
    icecat_ok = test_icecat_normalization()
    form_ok = test_laptop_form_validation()
    
    if icecat_ok and form_ok:
        print("\nALL V2.0 VERIFICATIONS PASSED")
        sys.exit(0)
    else:
        print("\nVERIFICATION FAILED")
        sys.exit(1)
