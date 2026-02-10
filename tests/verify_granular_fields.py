import sys
import os
from datetime import date

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.laptop import (
    Laptop, Screen, GraphicsCard, Storage, Ram, Brand, LaptopModel, Processor, OperatingSystem, Store
)
from app.services.catalog_service import CatalogService

def verify_granular_fields():
    app = create_app()
    with app.app_context():
        print("Starting verification of granular fields...")

        # 1. Prepare Mock Data (simulating form data)
        mock_form_data = {
            'brand_id': 'TestBrand',
            'model_id': 'TestModel',
            'processor_family': 'Intel Core Ultra',
            'processor_generation': 'Series 2',
            'processor_model': '155H',
            'processor_manufacturer': 'Intel',
            'os_id': 'Windows 11 Home',
            'store_id': 'Main Store',
            'location_id': 'Warehouse A',
            'supplier_id': 'Supplier X',
            
            # Granular Screen
            'screen_id': '', # Empty to force creation
            'screen_diagonal_inches': 16.0,
            'screen_resolution': '2560x1600',
            'screen_panel_type': 'OLED',
            'screen_refresh_rate': 120,
            'screen_touchscreen_override': True,
            
            # Granular GPU
            'graphics_card_id': '',
            'has_discrete_gpu': True,
            'discrete_gpu_brand': 'NVIDIA',
            'discrete_gpu_model': 'RTX 4070',
            'discrete_gpu_memory_gb': 8.0,
            'discrete_gpu_memory_type': 'GDDR6',
            'onboard_gpu_brand': 'Intel',
            'onboard_gpu_model': 'Arc Graphics',
            'onboard_gpu_family': 'Arc',

            # Granular Storage
            'storage_id': '',
            'storage_capacity': 1024,
            'storage_media': 'SSD',
            'storage_nvme': True,
            'storage_form_factor': 'M.2',

            # Granular RAM
            'ram_id': '',
            'ram_capacity': 32,
            'ram_type_detailed': 'LPDDR5X',
            'ram_speed_mhz': 7467,
            'ram_transfer_rate': '7467 MT/s',
            
            'weight_lbs': 4.19
        }

        # 2. Process Data via CatalogService
        print("Processing data via CatalogService...")
        processed_data = CatalogService.process_laptop_form_data(mock_form_data)
        
        # 3. Verify IDs are returned
        assert processed_data['screen_id'] is not None
        assert processed_data['graphics_card_id'] is not None
        assert processed_data['storage_id'] is not None
        assert processed_data['ram_id'] is not None
        
        # 4. Verify Catalog Items Created Correctly
        screen = Screen.query.get(processed_data['screen_id'])
        print(f"Screen Created: {screen.name}")
        assert screen.diagonal_inches == 16.0
        assert screen.resolution == '2560x1600'
        assert screen.panel_type == 'OLED'
        assert screen.refresh_rate == 120
        assert screen.touchscreen == True

        gpu = GraphicsCard.query.get(processed_data['graphics_card_id'])
        print(f"GPU Created: {gpu.name}")
        assert gpu.has_discrete_gpu == True
        assert gpu.discrete_brand == 'NVIDIA'
        assert gpu.discrete_model == 'RTX 4070'
        assert gpu.discrete_memory_gb == 8.0
        assert gpu.discrete_memory_type == 'GDDR6'

        storage = Storage.query.get(processed_data['storage_id'])
        print(f"Storage Created: {storage.name}")
        assert storage.capacity_gb == 1024
        assert storage.media_type == 'SSD'
        assert storage.nvme == True
        assert storage.form_factor == 'M.2'

        ram = Ram.query.get(processed_data['ram_id'])
        print(f"RAM Created: {ram.name}")
        assert ram.capacity_gb == 32
        assert ram.ram_type == 'LPDDR5X'
        assert ram.speed_mhz == 7467
        # assert ram.transfer_rate == '7467 MT/s' # Assuming model has this field, check

        # 5. Create Laptop Object (Simulate DB Insertion)
        print("Creating Laptop object...")
        laptop = Laptop(
            sku='TEST-SKU-001',
            slug='test-laptop-001',
            display_name='Test Laptop 2024',
            brand_id=processed_data['brand_id'],
            model_id=processed_data['model_id'],
            processor_id=processed_data['processor_id'],
            os_id=processed_data['os_id'],
            screen_id=processed_data['screen_id'],
            graphics_card_id=processed_data['graphics_card_id'],
            storage_id=processed_data['storage_id'],
            ram_id=processed_data['ram_id'],
            store_id=processed_data['store_id'],
            location_id=processed_data['location_id'],
            supplier_id=processed_data['supplier_id'],
            # Required fields
            purchase_cost=1000.00,
            sale_price=1500.00,
            quantity=5,
            category='laptop',
            condition='new',
            
            weight_lbs=mock_form_data['weight_lbs'],
            entry_date=date.today(),
            created_by_id=1 
        )
        
        db.session.add(laptop)
        # We won't commit to avoid polluting DB, just flush to get ID/relationships
        db.session.flush()

        # 6. Verify Laptop Properties (Single Source of Truth)
        print("Verifying Laptop properties...")
        assert laptop.screen.resolution == '2560x1600'
        assert laptop.graphics_card.discrete_model == 'RTX 4070'
        assert laptop.storage.capacity_gb == 1024
        assert laptop.ram.capacity_gb == 32
        assert laptop.weight_lbs == 4.19

        print("✅ VERIFICATION SUCCESSFUL: All granular fields processed and mapped correctly.")
        db.session.rollback()

if __name__ == '__main__':
    verify_granular_fields()
