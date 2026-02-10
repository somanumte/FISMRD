import sys
import os
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.services.catalog_service import CatalogService
from app.models.laptop import Laptop, Brand, LaptopModel, Processor, GraphicsCard, Screen, Storage, Ram, OperatingSystem, Store

def verify_granular_fields():
    app = create_app()
    with app.app_context():
        print("Starting Granular Fields Verification V2...")

        # Data simulating form submission (with new fields)
        form_data = {
            'sku': 'TEST-GRANULAR-V2',
            'display_name': 'Test Laptop Granular V2',
            'brand_id': 'Dell',
            'model_id': 'XPS 15',
            'category': 'laptop',
            'condition': 'new',
            'processor_family': 'Intel Core i7',
            'processor_generation': '12th Gen',
            'processor_model': '12700H',
            'os_id': 'Windows 11 Pro',
            'screen_id': '1920x1080',
            'screen_diagonal_inches': 15.6,
            'screen_refresh_rate': 120,
            'screen_panel_type': 'IPS',
            'screen_full_name': '15.6" FHD IPS 120Hz',
            'ram_id': '16GB DDR5',
            'ram_capacity': 16,
            'ram_type_detailed': 'DDR5',
            'ram_speed_mhz': 4800,
            'ram_transfer_rate': '4800 MT/s', # New field
            'ram_full_name': '16GB DDR5 4800MHz 4800 MT/s',
            'storage_id': '512GB SSD',
            'storage_capacity': 512,
            'storage_media': 'SSD',
            'storage_nvme': True,
            'storage_full_name': '512GB SSD NVMe',
            'graphics_card_id': 'NVIDIA RTX 3050',
            'has_discrete_gpu': True,
            'discrete_gpu_brand': 'NVIDIA',
            'discrete_gpu_model': 'RTX 3050',
            'discrete_gpu_memory_gb': 4.0,
            'discrete_gpu_full_name': 'NVIDIA RTX 3050 4GB',
            'onboard_gpu_brand': 'Intel',
            'onboard_gpu_model': 'Iris Xe',
            'onboard_gpu_family': 'Intel Graphics',
            'onboard_gpu_memory_gb': 0, # New field (integrated usually 0 or share, but field exists)
            'onboard_gpu_full_name': 'Intel Iris Xe',
            'weight_lbs': 4.5,
            'purchase_cost': 1000,
            'sale_price': 1500,
            'currency': 'USD',
            'store_id': Store.query.first().id if Store.query.first() else 1,
            'quantity': 1
        }

        # Mocking CatalogService behavior or calling it directly
        # CatalogService.process_laptop_form_data usually takes form object, 
        # but internal methods might take dicts if refactored, 
        # strictly speaking it takes form data. 
        # But we can try to call create_laptop if we construct a Mock form or similar.
        # Or simpler: create via Laptop model and direct catalog creation to verify model/db support.
        
        # Lets try to use CatalogService.process_laptop_form_data if possible, 
        # but it requires a FlaskForm object usually.
        # So we will verify the underlying CatalogService helper methods or just Model creation.
        
        # 1. Verify GraphicsCard with onboard_memory_gb
        print("Verifying GraphicsCard creation...")
        gpu_data = {
            'discrete_brand': form_data.get('discrete_gpu_brand'),
            'discrete_model': form_data.get('discrete_gpu_model'),
            'discrete_memory_gb': form_data.get('discrete_gpu_memory_gb'),
            'onboard_brand': form_data.get('onboard_gpu_brand'),
            'onboard_model': form_data.get('onboard_gpu_model'),
            'onboard_memory_gb': form_data.get('onboard_gpu_memory_gb'), # Key verification
            'has_discrete_gpu': form_data.get('has_discrete_gpu')
        }
        gpu_id = CatalogService._get_or_create_generic(GraphicsCard, form_data.get('graphics_card_id'), **gpu_data)
        
        db.session.commit()
        
        # Re-fetch to verify
        gpu_refetched = GraphicsCard.query.get(gpu_id)
        print(f"GraphicsCard ID: {gpu_refetched.id}")
        print(f"Onboard Memory: {gpu_refetched.onboard_memory_gb}")
        
        if gpu_refetched.onboard_memory_gb is not None:
             print("SUCCESS: onboard_memory_gb persisted.")
        else:
             print("FAILURE: onboard_memory_gb is None.")

        # 2. Verify Ram with transfer_rate
        print("Verifying Ram creation...")
        ram_data = {
            'capacity_gb': form_data.get('ram_capacity'),
            'ram_type': form_data.get('ram_type_detailed'),
            'speed_mhz': form_data.get('ram_speed_mhz'),
            'transfer_rate': form_data.get('ram_transfer_rate') # Key verification
        }
        ram_id = CatalogService._get_or_create_generic(Ram, form_data.get('ram_id'), **ram_data)
        db.session.commit()
        
        ram_refetched = Ram.query.get(ram_id)
        print(f"Ram ID: {ram_refetched.id}")
        print(f"Transfer Rate: {ram_refetched.transfer_rate}")
        
        if ram_refetched.transfer_rate == '4800 MT/s':
            print("SUCCESS: transfer_rate persisted.")
        else:
            print(f"FAILURE: transfer_rate mismatch. Got {ram_refetched.transfer_rate}")

if __name__ == "__main__":
    verify_granular_fields()
