# ============================================
# FUNCIONES DE SEED PARA POBLAR LA BASE DE DATOS
# ============================================

import random
import re
from datetime import date, timedelta

from app.extensions import db
from app.services.sku_service import SKUService


def create_catalogs():
    """
    Crea todos los catálogos necesarios en la base de datos
    """
    # Importar modelos dentro de la función para evitar importaciones circulares
    from app.models.laptop import (
        Brand, Processor, OperatingSystem, Screen, GraphicsCard,
        Storage, Ram, Store, Location, Supplier
    )
    from app.models.expense import ExpenseCategory

    # Inicializar listas para almacenar objetos
    catalog_objects = []

    # === MARCAS ===
    brands = ['Dell', 'Lenovo', 'HP', 'ASUS', 'Acer', 'MSI', 'Apple', 'Microsoft', 'Samsung', 'Gigabyte', 'Razer']
    for name in brands:
        if not Brand.query.filter_by(name=name).first():
            catalog_objects.append(Brand(name=name, is_active=True))

    # === GENERACIONES DE PROCESADORES (Catálogo) ===
    processor_samples = [
        ('Intel Core i3-1215U', 'Intel 12th Gen'), 
        ('Intel Core i5-1235U', 'Intel 12th Gen'), 
        ('Intel Core i7-1255U', 'Intel 12th Gen'),
        ('Intel Core i5-12450H', 'Intel 12th Gen'), 
        ('Intel Core i7-12700H', 'Intel 12th Gen'),
        ('Intel Core i5-1335U', 'Intel 13th Gen'), 
        ('Intel Core i7-1355U', 'Intel 13th Gen'),
        ('Intel Core i7-13650HX', 'Intel 13th Gen'), 
        ('Intel Core i9-13980HX', 'Intel 13th Gen'),
        ('AMD Ryzen 5 6600H', 'AMD Ryzen 6000 Series'), 
        ('AMD Ryzen 7 6800H', 'AMD Ryzen 6000 Series'),
        ('AMD Ryzen 5 7530U', 'AMD Ryzen 7000 Series'), 
        ('AMD Ryzen 7 7840HS', 'AMD Ryzen 7000 Series'),
        ('Apple M1', 'Apple M1 Chip'),
        ('Apple M2 Pro', 'Apple M2 Chip'),
        ('Apple M3 Max', 'Apple M3 Chip'),
    ]
    
    # Crear solo registros únicos de generación en el catálogo
    unique_generations = {}
    for full_name, gen_name in processor_samples:
        if gen_name not in unique_generations:
            # Inferir fabricante
            man = 'Intel' if 'Intel' in full_name else 'AMD' if 'AMD' in full_name else 'Apple' if 'Apple' in full_name else 'Other'
            unique_generations[gen_name] = man

    for gen_name, man in unique_generations.items():
        if not Processor.query.filter_by(name=gen_name).first():
            catalog_objects.append(Processor(
                name=gen_name,
                generation=gen_name,
                manufacturer=man,
                is_active=True
            ))

    # === SISTEMAS OPERATIVOS ===
    operating_systems = [
        'Windows 11 Home', 'Windows 11 Pro', 'Windows 10 Pro',
        'FreeDOS', 'Sin Sistema Operativo'
    ]
    for name in operating_systems:
        if not OperatingSystem.query.filter_by(name=name).first():
            catalog_objects.append(OperatingSystem(name=name, is_active=True))

    # === PANTALLAS ===
    screens = [
        '14" FHD IPS (1920x1080)', '14" FHD IPS 144Hz',
        '14" QHD IPS 165Hz (2560x1440)',
        '15.6" FHD IPS (1920x1080)', '15.6" FHD IPS 120Hz', '15.6" FHD IPS 144Hz',
        '15.6" FHD VA 144Hz', '15.6" QHD IPS 165Hz (2560x1440)',
        '16" FHD+ IPS (1920x1200)', '16" WQXGA IPS (2560x1600)',
        '16" QHD+ 165Hz (2560x1600)', '16" QHD IPS 165Hz (2560x1440)',
        '17.3" FHD IPS (1920x1080)', '17.3" FHD IPS 144Hz',
        '17.3" QHD IPS 165Hz (2560x1440)',
        '14" 2.8K OLED 90Hz', '15.6" 4K OLED (3840x2160)',
        '16" 4K OLED HDR', '18" QHD+ 240Hz (2560x1600)',
    ]
    for name in screens:
        if not Screen.query.filter_by(name=name).first():
            catalog_objects.append(Screen(name=name, is_active=True))

    # === TARJETAS GRÁFICAS ===
    graphics_cards = [
        'Intel UHD Graphics', 'Intel Iris Xe Graphics',
        'AMD Radeon Graphics', 'AMD Radeon 680M',
        'NVIDIA GeForce GTX 1650', 'NVIDIA GeForce GTX 1660 Ti',
        'NVIDIA GeForce RTX 3050', 'NVIDIA GeForce RTX 3050 Ti',
        'NVIDIA GeForce RTX 3060', 'NVIDIA GeForce RTX 3070', 'NVIDIA GeForce RTX 3080',
        'NVIDIA GeForce RTX 4050', 'NVIDIA GeForce RTX 4060',
        'NVIDIA GeForce RTX 4070', 'NVIDIA GeForce RTX 4080', 'NVIDIA GeForce RTX 4090',
    ]
    for name in graphics_cards:
        if not GraphicsCard.query.filter_by(name=name).first():
            catalog_objects.append(GraphicsCard(name=name, is_active=True))

    # === ALMACENAMIENTO ===
    storage_types = [
        '256GB SSD NVMe', '512GB SSD NVMe', '512GB SSD NVMe PCIe 4.0',
        '1TB SSD NVMe', '1TB SSD NVMe PCIe 4.0', '2TB SSD NVMe PCIe 4.0',
        '256GB SSD + 1TB HDD', '512GB SSD + 1TB HDD',
    ]
    for name in storage_types:
        if not Storage.query.filter_by(name=name).first():
            catalog_objects.append(Storage(name=name, is_active=True))

    # === RAM ===
    ram_types = [
        '8GB DDR4 3200MHz', '16GB DDR4 3200MHz', '32GB DDR4 3200MHz',
        '8GB DDR5 4800MHz', '16GB DDR5 4800MHz', '16GB DDR5 5200MHz',
        '32GB DDR5 4800MHz', '32GB DDR5 5200MHz', '64GB DDR5 5200MHz',
    ]
    for name in ram_types:
        if not Ram.query.filter_by(name=name).first():
            catalog_objects.append(Ram(name=name, is_active=True))

    # === TIENDAS ===
    stores = [
        ('Tienda Principal', 'Av. Principal #123', '809-555-0001'),
        ('Sucursal Centro', 'Calle El Conde #456', '809-555-0002'),
        ('Sucursal Plaza', 'Plaza Central Local 23', '809-555-0003'),
    ]
    for name, address, phone in stores:
        if not Store.query.filter_by(name=name).first():
            catalog_objects.append(Store(name=name, address=address, phone=phone, is_active=True))

    # === UBICACIONES ===
    locations = [
        'Vitrina Principal', 'Vitrina Gaming', 'Estante A-1', 'Estante A-2',
        'Estante B-1', 'Estante B-2', 'Bodega', 'Almacén'
    ]
    for name in locations:
        if not Location.query.filter_by(name=name).first():
            catalog_objects.append(Location(name=name, is_active=True))

    # === PROVEEDORES ===
    suppliers = [
        ('TechDistributor RD', 'Juan Pérez', 'ventas@techdist.com', '809-555-1001'),
        ('CompuMaster', 'María García', 'info@compumaster.com', '809-555-1002'),
        ('Digital Import', 'Carlos López', 'sales@digitalimport.com', '809-555-1003'),
        ('MegaTech Supplies', 'Ana Rodríguez', 'orders@megatech.com', '809-555-1004'),
    ]
    for name, contact, email, phone in suppliers:
        if not Supplier.query.filter_by(name=name).first():
            catalog_objects.append(Supplier(
                name=name, contact_name=contact, email=email, phone=phone, is_active=True
            ))

    # === CATEGORÍAS DE GASTOS ===
    expense_categories = [
        {'name': 'Alquiler', 'color': 'bg-red-100 text-red-800'},
        {'name': 'Servicios', 'color': 'bg-blue-100 text-blue-800'},
        {'name': 'Salarios', 'color': 'bg-green-100 text-green-800'},
        {'name': 'Marketing', 'color': 'bg-purple-100 text-purple-800'},
        {'name': 'Suministros', 'color': 'bg-yellow-100 text-yellow-800'},
        {'name': 'Mantenimiento', 'color': 'bg-indigo-100 text-indigo-800'},
        {'name': 'Impuestos', 'color': 'bg-pink-100 text-pink-800'},
        {'name': 'Transporte', 'color': 'bg-gray-100 text-gray-800'},
    ]
    for cat_data in expense_categories:
        if not ExpenseCategory.query.filter_by(name=cat_data['name']).first():
            catalog_objects.append(ExpenseCategory(name=cat_data['name'], color=cat_data['color']))

    # Añadir todos los objetos a la sesión
    for obj in catalog_objects:
        db.session.add(obj)

    # Hacer flush para asignar IDs
    db.session.flush()


def create_sample_laptops(admin_id):
    """
    Crea 50 laptops reales de prueba en la base de datos

    Args:
        admin_id: ID del usuario administrador que crea las laptops
    """
    # Importar modelos dentro de la función para evitar importaciones circulares
    from app.models.laptop import (
        Laptop, LaptopModel, Brand, Processor, Screen, GraphicsCard,
        Storage, Ram, OperatingSystem, Store, Location, Supplier
    )
    from app.models.serial import LaptopSerial

    # Los catálogos se crearán bajo demanda usando CatalogService
    from app.services.catalog_service import CatalogService
    stores = list(Store.query.all())
    locations = list(Location.query.all())
    suppliers = list(Supplier.query.all())

    # 50 laptops reales
    laptops_data = [
        # DELL (10)
        {'brand': 'Dell', 'model': 'Inspiron 15 3520', 'processor': 'Intel Core i5-1235U',
         'ram': '8GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 450,
         'price': 599},
        {'brand': 'Dell', 'model': 'Inspiron 15 3530', 'processor': 'Intel Core i7-1355U',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 550,
         'price': 749},
        {'brand': 'Dell', 'model': 'Latitude 5540', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)',
         'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 750, 'price': 999},
        {'brand': 'Dell', 'model': 'Latitude 7440', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR5 5200MHz',
         'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" FHD IPS (1920x1080)',
         'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 950, 'price': 1299},
        {'brand': 'Dell', 'model': 'XPS 15 9530', 'processor': 'Intel Core i7-13700H', 'ram': '16GB DDR5 4800MHz',
         'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4050',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 1200,
         'price': 1599},
        {'brand': 'Dell', 'model': 'XPS 15 9530 OLED', 'processor': 'Intel Core i7-13700H',
         'ram': '32GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '15.6" 4K OLED (3840x2160)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 1600,
         'price': 2199},
        {'brand': 'Dell', 'model': 'G15 5530', 'processor': 'Intel Core i5-13450H', 'ram': '16GB DDR5 4800MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050', 'screen': '15.6" FHD IPS 120Hz',
         'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 700, 'price': 949},
        {'brand': 'Dell', 'model': 'G15 5535', 'processor': 'AMD Ryzen 7 7840HS', 'ram': '16GB DDR5 4800MHz',
         'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS 144Hz',
         'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 850, 'price': 1149},
        {'brand': 'Dell', 'model': 'G16 7630', 'processor': 'Intel Core i7-13650HX', 'ram': '16GB DDR5 4800MHz',
         'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '16" QHD+ 165Hz (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1100,
         'price': 1449},
        {'brand': 'Dell', 'model': 'Alienware m16 R1', 'processor': 'Intel Core i9-13900HX',
         'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080',
         'screen': '16" QHD+ 165Hz (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2200,
         'price': 2899},
        # LENOVO (10)
        {'brand': 'Lenovo', 'model': 'IdeaPad 3 15IAU7', 'processor': 'Intel Core i3-1215U',
         'ram': '8GB DDR4 3200MHz', 'storage': '256GB SSD NVMe', 'gpu': 'Intel UHD Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 320,
         'price': 449},
        {'brand': 'Lenovo', 'model': 'IdeaPad 5 15IAL7', 'processor': 'Intel Core i5-1235U',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 480,
         'price': 649},
        {'brand': 'Lenovo', 'model': 'ThinkPad E15 Gen 4', 'processor': 'Intel Core i5-1235U',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 620,
         'price': 849},
        {'brand': 'Lenovo', 'model': 'ThinkPad T14 Gen 4', 'processor': 'Intel Core i7-1355U',
         'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 900,
         'price': 1249},
        {'brand': 'Lenovo', 'model': 'ThinkPad X1 Carbon Gen 11', 'processor': 'Intel Core i7-1365U',
         'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 1300,
         'price': 1799},
        {'brand': 'Lenovo', 'model': 'IdeaPad Gaming 3 15IAH7', 'processor': 'Intel Core i5-12500H',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050',
         'screen': '15.6" FHD IPS 120Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 600, 'price': 799},
        {'brand': 'Lenovo', 'model': 'LOQ 15IRH8', 'processor': 'Intel Core i5-13420H', 'ram': '16GB DDR5 4800MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS 144Hz',
         'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 750, 'price': 999},
        {'brand': 'Lenovo', 'model': 'Legion 5 15IAH7H', 'processor': 'Intel Core i7-12700H',
         'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 950,
         'price': 1299},
        {'brand': 'Lenovo', 'model': 'Legion Pro 5 16IRX8', 'processor': 'Intel Core i7-13700HX',
         'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4070',
         'screen': '16" WQXGA IPS (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1400,
         'price': 1899},
        {'brand': 'Lenovo', 'model': 'Legion Pro 7 16IRX8H', 'processor': 'Intel Core i9-13900HX',
         'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080',
         'screen': '16" WQXGA IPS (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2000,
         'price': 2699},
        # HP (10)
        {'brand': 'HP', 'model': '15-fd0xxx', 'processor': 'Intel Core i3-1215U', 'ram': '8GB DDR4 3200MHz',
         'storage': '256GB SSD NVMe', 'gpu': 'Intel UHD Graphics', 'screen': '15.6" FHD IPS (1920x1080)',
         'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 300, 'price': 399},
        {'brand': 'HP', 'model': '15-fc0xxx', 'processor': 'AMD Ryzen 5 7530U', 'ram': '16GB DDR4 3200MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'AMD Radeon Graphics', 'screen': '15.6" FHD IPS (1920x1080)',
         'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 420, 'price': 549},
        {'brand': 'HP', 'model': 'Pavilion 15-eg3xxx', 'processor': 'Intel Core i5-1335U',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 500,
         'price': 699},
        {'brand': 'HP', 'model': 'ProBook 450 G10', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)',
         'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 650, 'price': 899},
        {'brand': 'HP', 'model': 'EliteBook 840 G10', 'processor': 'Intel Core i7-1355U',
         'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 950,
         'price': 1349},
        {'brand': 'HP', 'model': 'Spectre x360 14', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR5 5200MHz',
         'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" 2.8K OLED 90Hz',
         'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 1150, 'price': 1599},
        {'brand': 'HP', 'model': 'Victus 15-fa0xxx', 'processor': 'Intel Core i5-12450H',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 580, 'price': 779},
        {'brand': 'HP', 'model': 'Victus 16-r0xxx', 'processor': 'Intel Core i5-13500H', 'ram': '16GB DDR5 4800MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '16" FHD+ IPS (1920x1200)',
         'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 750, 'price': 999},
        # ASUS (10)
        {'brand': 'ASUS', 'model': 'Vivobook 15 X1502ZA', 'processor': 'Intel Core i3-1215U',
         'ram': '8GB DDR4 3200MHz', 'storage': '256GB SSD NVMe', 'gpu': 'Intel UHD Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 340,
         'price': 449},
        {'brand': 'ASUS', 'model': 'Vivobook 15 X1504VA', 'processor': 'Intel Core i5-1335U',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 480,
         'price': 649},
        {'brand': 'ASUS', 'model': 'Zenbook 14 UX3402VA', 'processor': 'Intel Core i5-1340P',
         'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 800,
         'price': 1099},
        {'brand': 'ASUS', 'model': 'Zenbook Pro 14 OLED', 'processor': 'Intel Core i7-13700H',
         'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4050',
         'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 1200,
         'price': 1649},
        {'brand': 'ASUS', 'model': 'TUF Gaming F15 FX507ZC', 'processor': 'Intel Core i5-12500H',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 620, 'price': 849},
        {'brand': 'ASUS', 'model': 'TUF Gaming A15 FA507NV', 'processor': 'AMD Ryzen 7 7735HS',
         'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 850,
         'price': 1149},
        {'brand': 'ASUS', 'model': 'ROG Strix G15 G513RW', 'processor': 'AMD Ryzen 9 6900HX',
         'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 3070',
         'screen': '15.6" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1100,
         'price': 1499},
        {'brand': 'ASUS', 'model': 'ROG Strix G16 G614JV', 'processor': 'Intel Core i7-13650HX',
         'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '16" FHD+ IPS (1920x1200)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1000,
         'price': 1349},
        {'brand': 'ASUS', 'model': 'ROG Zephyrus G14 GA402XV', 'processor': 'AMD Ryzen 9 7940HS',
         'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '14" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1250,
         'price': 1699},
        {'brand': 'ASUS', 'model': 'ROG Strix SCAR 18 G834JY', 'processor': 'Intel Core i9-13980HX',
         'ram': '32GB DDR5 5200MHz', 'storage': '2TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4090',
         'screen': '18" QHD+ 240Hz (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2800,
         'price': 3699},
        # ACER (5)
        {'brand': 'Acer', 'model': 'Aspire 3 A315-59', 'processor': 'Intel Core i5-1235U',
         'ram': '8GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 380,
         'price': 499},
        {'brand': 'Acer', 'model': 'Aspire 5 A515-57', 'processor': 'Intel Core i7-1255U',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 520,
         'price': 699},
        {'brand': 'Acer', 'model': 'Swift 3 SF314-512', 'processor': 'Intel Core i7-1260P',
         'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics',
         'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 680,
         'price': 899},
        {'brand': 'Acer', 'model': 'Nitro 5 AN515-58', 'processor': 'Intel Core i5-12500H',
         'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 600, 'price': 799},
        {'brand': 'Acer', 'model': 'Predator Helios 16 PH16-71', 'processor': 'Intel Core i7-13700HX',
         'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4070',
         'screen': '16" WQXGA IPS (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1350,
         'price': 1799},
        # MSI (5)
        {'brand': 'MSI', 'model': 'Modern 15 B13M', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)',
         'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 500, 'price': 679},
        {'brand': 'MSI', 'model': 'Thin GF63 12VE', 'processor': 'Intel Core i5-12450H', 'ram': '16GB DDR4 3200MHz',
         'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS 144Hz',
         'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 680, 'price': 899},
        {'brand': 'MSI', 'model': 'Cyborg 15 A12VF', 'processor': 'Intel Core i7-12650H',
         'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 900,
         'price': 1199},
        {'brand': 'MSI', 'model': 'Katana 15 B13VFK', 'processor': 'Intel Core i7-13620H',
         'ram': '16GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060',
         'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 950,
         'price': 1299},
        {'brand': 'MSI', 'model': 'Raider GE78 HX 13VH', 'processor': 'Intel Core i9-13950HX',
         'ram': '32GB DDR5 5200MHz', 'storage': '2TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080',
         'screen': '17.3" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2300,
         'price': 2999},
    ]

    # Catálogos dinámicos
    # conditions...

    # Variables aleatorias
    conditions = ['new', 'used', 'refurbished']
    keyboard_layouts = ['US', 'ES', 'LATAM']
    connectivity_options = [
        {'usb_a_3': 2, 'usb_c': 1, 'hdmi': 1, 'audio_jack': 1},
        {'usb_a_3': 3, 'usb_c': 2, 'hdmi': 1, 'ethernet': 1, 'audio_jack': 1},
        {'usb_a_31': 2, 'usb_c_thunderbolt': 2, 'hdmi_21': 1, 'sd_card': 1, 'audio_jack': 1},
    ]

    # Crear laptops
    laptop_objects = []
    for i, laptop_data in enumerate(laptops_data):
        sku = SKUService.generate_laptop_sku()

        slug_base = f"{laptop_data['brand']}-{laptop_data['model']}".lower()
        slug_base = slug_base.replace(' ', '-').replace('/', '-').replace('.', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug_base)
        slug = re.sub(r'-+', '-', slug).strip('-')

        existing = Laptop.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{i + 1}"

        # Convertir costo de USD a DOP (pesos dominicanos)
        purchase_cost_dop = laptop_data['cost'] * 64
        sale_price_dop = purchase_cost_dop * 1.20  # Margen del 20%

        brand_id = CatalogService.get_or_create_brand(laptop_data['brand'])
        model_id = CatalogService.get_or_create_model(laptop_data['model'], brand_id)
        
        # Procesador
        p_name = laptop_data['processor']
        # Extraer familia y generacion burdamente para el seed
        p_fam = p_name.split('-')[0] if '-' in p_name else p_name
        p_id = CatalogService.get_or_create_processor(family=p_fam, generation=p_name, manufacturer=laptop_data['brand'])
        
        # RAM
        ram_str = laptop_data['ram']
        ram_cap = int(ram_str.split('GB')[0]) if 'GB' in ram_str else 8
        ram_id = CatalogService.get_or_create_ram(ram_str, capacity_gb=ram_cap)
        
        # Storage
        st_str = laptop_data['storage']
        st_cap = 512
        if 'TB' in st_str: st_cap = 1024
        elif 'GB' in st_str: st_cap = int(st_str.split('GB')[0])
        storage_id = CatalogService.get_or_create_storage(st_str, capacity_gb=st_cap)
        
        # GPU
        gpu_id = CatalogService.get_or_create_graphics_card(laptop_data['gpu'])
        
        # Screen
        sc_str = laptop_data['screen']
        sc_size = 15.6
        if '"' in sc_str:
            try: sc_size = float(sc_str.split('"')[0])
            except: pass
        screen_id = CatalogService.get_or_create_screen(sc_str, diagonal_inches=sc_size)
        
        # OS
        os_id = CatalogService.get_or_create_os(laptop_data['os'])

        laptop = Laptop(
            sku=sku,
            slug=slug,
            display_name=f"{laptop_data['brand']} {laptop_data['model']}",
            short_description=f"Laptop {laptop_data['category']} con {laptop_data['processor']} y {laptop_data['ram']}",
            is_published=random.choice([True, True, True, False]),
            is_featured=random.choice([True, False, False, False, False]),
            brand_id=brand_id,
            model_id=model_id,
            processor_id=p_id,
            ram_id=ram_id,
            storage_id=storage_id,
            graphics_card_id=gpu_id,
            screen_id=screen_id,
            os_id=os_id,
            store_id=random.choice(stores).id,
            location_id=random.choice(locations).id,
            supplier_id=random.choice(suppliers).id,
            category=laptop_data['category'],
            condition=random.choice(conditions),
            keyboard_layout=random.choice(keyboard_layouts),
            connectivity_ports=random.choice(connectivity_options),
            npu=random.choice([True, False, False, False]),
            storage_upgradeable=random.choice([True, True, False]),
            ram_upgradeable=random.choice([True, True, False]),
            purchase_cost=purchase_cost_dop,
            sale_price=sale_price_dop,
            discount_price=sale_price_dop * 0.9 if random.random() < 0.2 else None,
            tax_percent=18.00,
            quantity=random.randint(1, 8),
            reserved_quantity=0,
            min_alert=2,
            entry_date=date.today() - timedelta(days=random.randint(1, 90)),
            created_by_id=admin_id,
            currency='USD',
            icecat_import_status='pending'
        )

        laptop_objects.append(laptop)
        db.session.add(laptop)

    # Hacer flush para asignar IDs a las laptops
    db.session.flush()

    # Crear seriales para cada laptop según la cantidad
    for laptop in laptop_objects:
        for i in range(1, laptop.quantity + 1):
            serial_number = f"{laptop.sku}-{i:02d}"
            serial = LaptopSerial(
                laptop_id=laptop.id,
                serial_number=serial_number,
                serial_normalized=LaptopSerial.normalize_serial(serial_number),
                serial_type='manufacturer',
                unit_cost=laptop.purchase_cost,
                received_date=laptop.entry_date,
                status='available',
                created_by_id=admin_id
            )
            db.session.add(serial)
    
    db.session.commit()


def create_extensive_laptops(admin_id):
    """
    Genera 100 modelos de laptops reales con UPC y precios en DOP.
    """
    from app.models.laptop import (
        Laptop, LaptopModel, Brand, Processor, Screen, GraphicsCard,
        Storage, Ram, OperatingSystem, Store, Location, Supplier
    )
    from app.models.serial import LaptopSerial
    import random
    import re
    from datetime import date, timedelta
    
    db.session.flush()

    # Catálogos básicos
    # CatalogService se encargará de esto
    from app.services.catalog_service import CatalogService
    stores = list(Store.query.all())
    locations = list(Location.query.all())
    suppliers = list(Supplier.query.all())

    # 100 Modelos Reales (Investigación + Comunes)
    extensive_data = [
        # Lenovo
        {"brand": "Lenovo", "model": "IdeaPad 15.6 FHD IPS Ryzen 7 5700U", "upc": "973597302492", "cost": 480},
        {"brand": "Lenovo", "model": "IdeaPad 15.6 FHD Ryzen 3 7320U", "upc": "973597348131", "cost": 320},
        {"brand": "Lenovo", "model": "Legion 5 16IRX9 i7-14650HX RTX 4060", "upc": "602072538780", "cost": 1100},
        {"brand": "Lenovo", "model": "ThinkPad P16 Gen 2 i9-13980HX RTX 3500", "upc": "602072512773", "cost": 2100},
        {"brand": "Lenovo", "model": "Yoga 7i 16\" 2.5K Touch i7-1355U", "upc": "197529605412", "cost": 850},
        {"brand": "Lenovo", "model": "ThinkPad X1 Carbon Gen 11 i7-1365U", "upc": "197528123456", "cost": 1400},
        {"brand": "Lenovo", "model": "LOQ 15IRH8 i5-13420H RTX 4050", "upc": "197528654321", "cost": 750},
        {"brand": "Lenovo", "model": "IdeaPad Slim 3 14\" Ryzen 5 7530U", "upc": "197528987654", "cost": 420},
        {"brand": "Lenovo", "model": "Legion Pro 7i i9-14900HX RTX 4080", "upc": "197528111222", "cost": 2200},
        {"brand": "Lenovo", "model": "ThinkStation P3 Tiny i7-13700", "upc": "197528333444", "cost": 900},
        
        # Dell
        {"brand": "Dell", "model": "XPS 16 9640 Core Ultra 7 155H 1TB", "upc": "602072481918", "cost": 1500},
        {"brand": "Dell", "model": "XPS 16 9640 Core Ultra 7 155H 512GB", "upc": "602072494956", "cost": 1350},
        {"brand": "Dell", "model": "Inspiron 14 7440 Core 5 120U", "upc": "602072517747", "cost": 650},
        {"brand": "Dell", "model": "Alienware m18 R2 i9-14900HX RTX 4070", "upc": "632823326731", "cost": 2300},
        {"brand": "Dell", "model": "Latitude 7455 Snapdragon X Elite", "upc": "609198531268", "cost": 1200},
        {"brand": "Dell", "model": "Precision 3490 Core Ultra 5 135H", "upc": "632823916048", "cost": 950},
        {"brand": "Dell", "model": "Vostro 3520 i5-1235U 8GB 512GB", "upc": "632823123456", "cost": 450},
        {"brand": "Dell", "model": "G15 5530 i7-13650HX RTX 4060", "upc": "632823654321", "cost": 950},
        {"brand": "Dell", "model": "OptiPlex 7010 Micro i5-13500T", "upc": "632823987654", "cost": 600},
        {"brand": "Dell", "model": "Latitude 5440 i5-1335U 16GB", "upc": "632823111222", "cost": 800},

        # HP
        {"brand": "HP", "model": "Pavilion 15.6 FHD Ryzen 7 7730U 16GB", "upc": "196105870171", "cost": 550},
        {"brand": "HP", "model": "Envy x360 14\" Ryzen 5 8640HS", "upc": "197497123456", "cost": 720},
        {"brand": "HP", "model": "Spectre x360 14\" i7-1355U OLED", "upc": "197497654321", "cost": 1200},
        {"brand": "HP", "model": "Victus 15-fa0031dx i5-12450H RTX 3050", "upc": "197497987654", "cost": 680},
        {"brand": "HP", "model": "EliteBook 840 G10 i7-1365U", "upc": "197497111222", "cost": 1100},
        {"brand": "HP", "model": "ProBook 450 G10 i5-1335U", "upc": "197497333444", "cost": 750},
        {"brand": "HP", "model": "Omen 16-wd0013dx i7-13620H RTX 4060", "upc": "197497555666", "cost": 1050},
        {"brand": "HP", "model": "Laptop 17-cn3053cl i5-1335U", "upc": "197497777888", "cost": 500},
        {"brand": "HP", "model": "Chromebook 14\" Celeron N4500", "upc": "197497999000", "cost": 180},
        {"brand": "HP", "model": "ZBook Power G10 i7-13700H RTX A1000", "upc": "197497222333", "cost": 1600},

        # Apple
        {"brand": "Apple", "model": "MacBook Air 13\" (M3, 2024) 8GB 256GB", "upc": "195949123456", "cost": 950},
        {"brand": "Apple", "model": "MacBook Pro 14\" (M3 Pro, 2023) 18GB 512GB", "upc": "195949012345", "cost": 1750},
        {"brand": "Apple", "model": "MacBook Air 15\" (M3, 2024) 16GB 512GB", "upc": "195949222333", "cost": 1350},
        {"brand": "Apple", "model": "MacBook Pro 16\" (M3 Max, 2023) 36GB 1TB", "upc": "195949333444", "cost": 3100},
        {"brand": "Apple", "model": "MacBook Air 13\" (M2, 2022) 8GB 256GB", "upc": "194253012345", "cost": 850},
        {"brand": "Apple", "model": "MacBook Pro 14\" (M2 Pro, 2023) 16GB 512GB", "upc": "194253111222", "cost": 1600},
        {"brand": "Apple", "model": "iMac 24\" (M3, 2023) 8-core CPU 256GB", "upc": "195949444555", "cost": 1150},
        {"brand": "Apple", "model": "Mac mini (M2, 2023) 8GB 256GB", "upc": "194253222333", "cost": 520},
        {"brand": "Apple", "model": "Mac Studio (M2 Max, 2023) 32GB 512GB", "upc": "194253333444", "cost": 1750},

        # ASUS
        {"brand": "ASUS", "model": "ROG Zephyrus G14 (2024) Ryzen 9 RTX 4060", "upc": "197105432109", "cost": 1350},
        {"brand": "ASUS", "model": "Zenbook 14 OLED i7-1355H 16GB 1TB", "upc": "197105123456", "cost": 850},
        {"brand": "ASUS", "model": "Vivobook 16\" Ryzen 7 7730U 16GB 512GB", "upc": "197105654321", "cost": 520},
        {"brand": "ASUS", "model": "TUF Gaming F15 i7-13620H RTX 4060", "upc": "197105987654", "cost": 950},
        {"brand": "ASUS", "model": "ROG Strix SCAR 16 i9-14900HX RTX 4080", "upc": "197105111222", "cost": 2400},
        {"brand": "ASUS", "model": "ExpertBook B9 i7-1355U 32GB 2TB", "upc": "197105333444", "cost": 1800},
        {"brand": "ASUS", "model": "Zenbook Pro 14 Duo i9-13900H RTX 4060", "upc": "197105555666", "cost": 1900},
        {"brand": "ASUS", "model": "ROG Flow X16 Ryzen 9 RTX 4070", "upc": "197105777888", "cost": 2100},
        {"brand": "ASUS", "model": "ProArt Studiobook 16 i9-13980HX RTX 3000", "upc": "197105999000", "cost": 2300},

        # Acer
        {"brand": "Acer", "model": "Swift Go 14 Core Ultra 7 155H OLED", "upc": "195133246810", "cost": 750},
        {"brand": "Acer", "model": "Nitro V 15 i5-13420H RTX 4050", "upc": "195133123456", "cost": 680},
        {"brand": "Acer", "model": "Aspire 5 15.6\" i7-1355U 16GB 512GB", "upc": "195133654321", "cost": 550},
        {"brand": "Acer", "model": "Predator Helios Neo 16 i7-13700HX RTX 4060", "upc": "195133987654", "cost": 980},
        {"brand": "Acer", "model": "Swift Edge 16 Ryzen 7 7840U OLED", "upc": "195133111222", "cost": 1100},
        {"brand": "Acer", "model": "Spin 5 14\" i7-1260P Touch", "upc": "195133333444", "cost": 850},
        {"brand": "Acer", "model": "TravelMate P6 i7-1355U 16GB", "upc": "195133555666", "cost": 1200},
        {"brand": "Acer", "model": "Chromebook Spin 714 i5-1335U", "upc": "195133777888", "cost": 620},
        {"brand": "Acer", "model": "Predator Triton 17X i9-13900HX RTX 4090", "upc": "195133999000", "cost": 3200},

        # MSI
        {"brand": "MSI", "model": "Cyborg 15 A13VF i7-13620H RTX 4060", "upc": "824142345674", "cost": 900},
        {"brand": "MSI", "model": "Prestige 14 Evo i7-13700H 16GB", "upc": "824142123456", "cost": 850},
        {"brand": "MSI", "model": "Katana 15 i7-13620H RTX 4070", "upc": "824142654321", "cost": 1100},
        {"brand": "MSI", "model": "Raider GE78 HX i9-14900HX RTX 4080", "upc": "824142987654", "cost": 2600},
        {"brand": "MSI", "model": "Thin GF63 i5-12450H RTX 3050", "upc": "824142111222", "cost": 620},
        {"brand": "MSI", "model": "Summit E16 Flip i7-1360P RTX 4050", "upc": "824142333444", "cost": 1400},
        {"brand": "MSI", "model": "Creator Z17 HX i9-13980HX RTX 4070", "upc": "824142555666", "cost": 2800},
        {"brand": "MSI", "model": "Titan GT77 HX i9-13980HX RTX 4090", "upc": "824142777888", "cost": 4200},
        {"brand": "MSI", "model": "Modern 15 B13M i5-1335U 8GB", "upc": "824142999000", "cost": 480},

        # Microsoft
        {"brand": "Microsoft", "model": "Surface Laptop 6 15\" Core Ultra 5 135H", "upc": "671381542306", "cost": 1100},
        {"brand": "Microsoft", "model": "Surface Laptop 6 15\" Core Ultra 7 165H 16GB", "upc": "682174375247", "cost": 1400},
        {"brand": "Microsoft", "model": "Surface Laptop 6 15\" Core Ultra 7 165H 32GB", "upc": "682174411709", "cost": 1800},
        {"brand": "Microsoft", "model": "Surface Pro 9 i5-1235U 8GB 256GB", "upc": "889842123456", "cost": 850},
        {"brand": "Microsoft", "model": "Surface Laptop Go 3 i5-1235U 8GB", "upc": "889842654321", "cost": 650},
        {"brand": "Microsoft", "model": "Surface Studio 2 i7-11370H RTX 3050 Ti", "upc": "889842987654", "cost": 1900},

        # Samsung / Gigabyte / Razer
        {"brand": "Samsung", "model": "Galaxy Book4 Pro 14\" Core Ultra 7 OLED", "upc": "887276123456", "cost": 1200},
        {"brand": "Samsung", "model": "Galaxy Book4 Ultra i9 RTX 4070", "upc": "887276654321", "cost": 2400},
        {"brand": "Gigabyte", "model": "AORUS 15 i7-13620H RTX 4060", "upc": "471933123456", "cost": 1050},
        {"brand": "Gigabyte", "model": "AERO 14 OLED i7-13700H RTX 4050", "upc": "471933654321", "cost": 1350},
        {"brand": "Razer", "model": "Blade 14 Ryzen 9 7940HS RTX 4070", "upc": "811254123456", "cost": 2100},
        {"brand": "Razer", "model": "Blade 16 i9-14900HX RTX 4080", "upc": "811254654321", "cost": 3200},
    ]

    # Rellenar hasta 100 si es necesario con variaciones
    while len(extensive_data) < 100:
        base = random.choice(extensive_data[:50])
        new_item = base.copy()
        new_item["model"] = f"{base['model']} Plus v{len(extensive_data)}"
        new_item["upc"] = str(int(base["upc"]) + len(extensive_data))
        new_item["cost"] = base["cost"] + random.randint(50, 200)
        extensive_data.append(new_item)

    # Los modelos se crearán bajo demanda en el loop principal

    # Crear Laptops
    laptop_objects = []
    for i, data in enumerate(extensive_data):
        sku = f"LXP-{data['upc'][-6:]}-{i:02d}"
        
        slug = re.sub(r'[^a-z0-9-]', '', data['model'].lower().replace(' ', '-'))
        if Laptop.query.filter_by(slug=slug).first():
            slug = f"{slug}-{i}"

        # Costos y Precios en DOP
        purchase_cost_dop = data['cost'] * 64.5 # Tasa RD
        sale_price_dop = purchase_cost_dop * 1.25 # 25% Margen

        # Categoría basada en nombre
        category = 'laptop'
        if 'gaming' in data['model'].lower() or 'rtx' in data['model'].lower() or 'rog' in data['model'].lower() or 'alienware' in data['model'].lower():
            category = 'gaming'
        elif 'workstation' in data['model'].lower() or 'precision' in data['model'].lower() or 'thinkpad p' in data['model'].lower():
            category = 'workstation'

        brand_id = CatalogService.get_or_create_brand(data['brand'])
        model_id = CatalogService.get_or_create_model(data['model'], brand_id)
        
        # Processor
        proc_id = CatalogService.get_or_create_processor(family=data['model'], generation="Multiple")
        
        # RAM
        ram_id = CatalogService.get_or_create_ram(capacity_gb=random.choice([8, 16, 32]))
        
        # Storage
        storage_id = CatalogService.get_or_create_storage(capacity_gb=random.choice([256, 512, 1024]))
        
        # GPU
        gpu_id = CatalogService.get_or_create_graphics_card(name="Integrated Graphics")
        
        # Screen
        screen_id = CatalogService.get_or_create_screen(diagonal_inches=random.choice([14.0, 15.6, 16.0]))
        
        # OS
        os_id = CatalogService.get_or_create_os("Windows 11 Home")

        laptop = Laptop(
            sku=sku,
            slug=slug,
            upc=data['upc'],
            gtin=data['upc'],
            display_name=f"{data['brand']} {data['model']}",
            short_description=f"Laptop {category} de alto rendimiento con garantía local.",
            is_published=True,
            brand_id=brand_id,
            model_id=model_id,
            processor_id=proc_id,
            ram_id=ram_id,
            storage_id=storage_id,
            graphics_card_id=gpu_id,
            screen_id=screen_id,
            os_id=os_id,
            store_id=random.choice(stores).id,
            location_id=random.choice(locations).id,
            supplier_id=random.choice(suppliers).id,
            category=category,
            condition='new',
            purchase_cost=purchase_cost_dop,
            sale_price=sale_price_dop,
            tax_percent=18,
            quantity=random.randint(2, 12),
            currency='DOP',
            created_by_id=admin_id,
            entry_date=date.today() - timedelta(days=random.randint(1, 120))
        )
        db.session.add(laptop)
        laptop_objects.append(laptop)

    db.session.flush()

    # Seriales
    for laptop in laptop_objects:
        for j in range(laptop.quantity):
            serial = LaptopSerial(
                laptop_id=laptop.id,
                serial_number=f"SN-{laptop.sku}-{j:02d}",
                serial_normalized=LaptopSerial.normalize_serial(f"SN-{laptop.sku}-{j:02d}"),
                serial_type='manufacturer',
                unit_cost=laptop.purchase_cost,
                received_date=laptop.entry_date,
                status='available',
                created_by_id=admin_id
            )
            db.session.add(serial)
    
    db.session.commit()


def generate_financial_history(admin_id, months=24, avg_sales=3000000, avg_expenses=500000):
    """
    Simula 2 años de historial financiero.
    """
    from app.models.invoice import Invoice, InvoiceItem, NCFSequence
    from app.models.expense import Expense, ExpenseCategory
    from app.models.customer import Customer
    from app.models.laptop import Laptop
    from decimal import Decimal
    
    # Asegurar clientes
    customers = Customer.query.all()
    if not customers:
        # Crear clientes de prueba si no existen
        for i in range(20):
            c = Customer(
                first_name=f"Cliente {i}",
                last_name=f"Prueba",
                id_number=f"001{random.randint(1000000, 9999999)}1",
                id_type='cedula',
                customer_type='person',
                is_active=True
            )
            db.session.add(c)
        db.session.flush()
        customers = Customer.query.all()

    # Categorías de gasto
    expense_cats = ExpenseCategory.query.all()
    laptops = Laptop.query.all()
    if not laptops:
        return "No hay laptops en inventario para generar ventas."

    start_date = date.today() - timedelta(days=months * 30)
    
    for m in range(months):
        current_month_date = start_date + timedelta(days=m * 30)
        
        # --- Simular Ventas (Facturas) ---
        monthly_sales_target = avg_sales * random.uniform(0.8, 1.2)
        total_sales = 0
        
        while total_sales < monthly_sales_target:
            # Crear Factura
            inv_date = current_month_date + timedelta(days=random.randint(0, 28))
            customer = random.choice(customers)
            
            # NCF
            ncf_type = 'B02' if random.random() > 0.3 else 'B01'
            seq = NCFSequence.get_or_create(ncf_type)
            ncf = seq.get_next_ncf()
            
            invoice = Invoice(
                invoice_number=f"INV-{inv_date.strftime('%y%m')}-{random.randint(1000, 9999)}",
                ncf=ncf,
                ncf_type=ncf_type,
                customer_id=customer.id,
                invoice_date=inv_date,
                payment_method=random.choice(['cash', 'transfer', 'card']),
                status='paid',
                created_by_id=admin_id
            )
            db.session.add(invoice)
            db.session.flush()
            
            # Items (1-3 laptops)
            num_items = random.randint(1, 3)
            inv_subtotal = 0
            for _ in range(num_items):
                laptop = random.choice(laptops)
                qty = 1
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    laptop_id=laptop.id,
                    description=laptop.display_name,
                    quantity=qty,
                    unit_price=laptop.sale_price,
                    line_total=laptop.sale_price * qty
                )
                db.session.add(item)
                inv_subtotal += (laptop.sale_price * qty)
            
            invoice.subtotal = inv_subtotal
            invoice.tax_amount = inv_subtotal * Decimal('0.18')
            invoice.total = inv_subtotal + invoice.tax_amount
            
            total_sales += float(invoice.total)

        # --- Simular Gastos ---
        monthly_expenses_target = avg_expenses * random.uniform(0.9, 1.1)
        total_expenses = 0
        
        while total_expenses < monthly_expenses_target:
            cat = random.choice(expense_cats)
            amount = random.uniform(5000, 50000)
            exp_date = current_month_date + timedelta(days=random.randint(0, 28))
            
            expense = Expense(
                description=f"Pago de {cat.name} - {exp_date.strftime('%B')}",
                amount=Decimal(str(round(amount, 2))),
                category_id=cat.id,
                due_date=exp_date,
                is_paid=True,
                paid_date=exp_date,
                created_by=admin_id
            )
            db.session.add(expense)
            total_expenses += amount
            
        db.session.commit()
    
    return f"Simulados {months} meses de historia: Ventas promedio ~{avg_sales}, Gastos promedio ~{avg_expenses}"