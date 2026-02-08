# -*- coding: utf-8 -*-
"""
================================================================================
MODELOS DE INVENTARIO DE LAPTOPS - V2.0 MEJORADO
================================================================================
Versión: 2.0
Fecha: 2025-02-07
Descripción: Modelo de datos unificado y mejorado para inventario de laptops.
             Compatible con el sistema de estandarización de Icecat.

Características:
    - Campos JSON para especificaciones normalizadas
    - Soporte para especificaciones unificadas de todas las marcas
    - Campos calculados para propiedades derivadas
    - Índices optimizados para búsquedas frecuentes
    - Relaciones con catálogos normalizados
================================================================================
"""

from app import db
from app.models.mixins import TimestampMixin, CatalogMixin
from datetime import datetime, date
import json


# =============================================================================
# MODELOS DE CATÁLOGO (usan CatalogMixin)
# =============================================================================

class Brand(CatalogMixin, db.Model):
    """
    Marcas de laptops (Dell, HP, Lenovo, etc.)
    Usa CatalogMixin: id, name, is_active, timestamps, métodos get_active() y get_or_create()
    """
    __tablename__ = 'brands'

    # Campos adicionales específicos
    logo_url = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='brand', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo_url': self.logo_url,
            'website': self.website,
            'country': self.country,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LaptopModel(CatalogMixin, db.Model):
    """
    Modelos de laptops (Inspiron 15, ThinkPad X1, etc.)
    """
    __tablename__ = 'laptop_models'

    # Campo adicional: referencia a marca (opcional)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)
    
    # Campos adicionales
    series = db.Column(db.String(100), nullable=True)  # Ej: ThinkPad, XPS, Omen
    release_year = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # gaming, business, ultrabook
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='model', lazy='dynamic')
    brand_ref = db.relationship('Brand', foreign_keys=[brand_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand_id': self.brand_id,
            'series': self.series,
            'release_year': self.release_year,
            'category': self.category,
            'is_active': self.is_active
        }


class Processor(CatalogMixin, db.Model):
    """
    Generaciones de Procesadores (ej: Intel Core 13th Gen, AMD Ryzen 8000 Series, Apple M3)
    El campo 'name' de CatalogMixin almacena el nombre de la generación.
    """
    __tablename__ = 'processors'

    # Campos técnicos adicionales
    manufacturer = db.Column(db.String(50), nullable=True)  # Intel, AMD, Apple
    family = db.Column(db.String(100), nullable=True)  # Core i7, Ryzen 7
    cores = db.Column(db.Integer, nullable=True)
    threads = db.Column(db.Integer, nullable=True)
    base_frequency = db.Column(db.String(20), nullable=True)
    turbo_frequency = db.Column(db.String(20), nullable=True)
    cache = db.Column(db.String(50), nullable=True)
    tdp = db.Column(db.String(20), nullable=True)
    lithography = db.Column(db.String(20), nullable=True)  # 7nm, 10nm, etc.
    generation = db.Column(db.String(100), nullable=True)  # AMD Ryzen 8000 Series
    model_number = db.Column(db.String(100), nullable=True)  # 8940HX
    has_npu = db.Column(db.Boolean, default=False)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='processor', lazy='dynamic')
    
    @property
    def all_info(self):
        """Retorna una cadena combinada con toda la información del procesador"""
        parts = [self.manufacturer, self.family, self.generation, self.model_number]
        return " ".join([p for p in parts if p]).strip()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'family': self.family,
            'generation': self.generation,
            'model_number': self.model_number,
            'cores': self.cores,
            'threads': self.threads,
            'base_frequency': self.base_frequency,
            'turbo_frequency': self.turbo_frequency,
            'cache': self.cache,
            'tdp': self.tdp,
            'lithography': self.lithography,
            'all_info': f"{self.manufacturer} {self.family} {self.generation} {self.model_number}".strip(),
            'has_npu': self.has_npu,
            'is_active': self.is_active
        }


class OperatingSystem(CatalogMixin, db.Model):
    """
    Sistemas Operativos (Windows 11 Pro, macOS, Ubuntu, etc.)
    """
    __tablename__ = 'operating_systems'

    # Campos adicionales
    version = db.Column(db.String(50), nullable=True)  # 11, 10, Sonoma, etc.
    architecture = db.Column(db.String(20), nullable=True)  # 64-bit, 32-bit
    family = db.Column(db.String(50), nullable=True)  # Windows, macOS, Linux
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='operating_system', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'architecture': self.architecture,
            'family': self.family,
            'is_active': self.is_active
        }


class Screen(CatalogMixin, db.Model):
    """
    Pantallas (15.6" FHD IPS, 14" 2K OLED, etc.)
    """
    __tablename__ = 'screens'

    # Campos técnicos
    diagonal_inches = db.Column(db.Numeric(3, 1), nullable=True)
    resolution = db.Column(db.String(50), nullable=True)  # 1920x1080
    panel_type = db.Column(db.String(50), nullable=True)  # IPS, OLED, TN
    hd_type = db.Column(db.String(50), nullable=True)  # Full HD, 4K UHD
    refresh_rate = db.Column(db.Integer, nullable=True)  # Hz
    brightness = db.Column(db.Integer, nullable=True)  # nits
    touchscreen = db.Column(db.Boolean, default=False)
    aspect_ratio = db.Column(db.String(20), nullable=True)  # 16:9, 16:10
    color_gamut = db.Column(db.String(50), nullable=True)  # 100% sRGB
    hdr = db.Column(db.Boolean, default=False)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='screen', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'diagonal_inches': float(self.diagonal_inches) if self.diagonal_inches else None,
            'resolution': self.resolution,
            'panel_type': self.panel_type,
            'hd_type': self.hd_type,
            'refresh_rate': self.refresh_rate,
            'brightness': self.brightness,
            'touchscreen': self.touchscreen,
            'aspect_ratio': self.aspect_ratio,
            'color_gamut': self.color_gamut,
            'hdr': self.hdr,
            'is_active': self.is_active
        }


class GraphicsCard(CatalogMixin, db.Model):
    """
    Tarjetas Gráficas (NVIDIA RTX 4060, Intel Iris Xe, etc.)
    """
    __tablename__ = 'graphics_cards'

    # Campos técnicos
    brand = db.Column(db.String(50), nullable=True)  # NVIDIA, AMD, Intel
    gpu_type = db.Column(db.String(50), nullable=True)  # dedicated, integrated
    memory_gb = db.Column(db.Integer, nullable=True)
    memory_type = db.Column(db.String(50), nullable=True)  # GDDR6, GDDR5
    ray_tracing = db.Column(db.Boolean, default=False)
    dlss = db.Column(db.Boolean, default=False)
    tdp = db.Column(db.String(20), nullable=True)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='graphics_card', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'gpu_type': self.gpu_type,
            'memory_gb': self.memory_gb,
            'memory_type': self.memory_type,
            'ray_tracing': self.ray_tracing,
            'dlss': self.dlss,
            'tdp': self.tdp,
            'is_active': self.is_active
        }


class Storage(CatalogMixin, db.Model):
    """
    Tipos de Almacenamiento (512GB SSD NVMe, 1TB HDD, etc.)
    """
    __tablename__ = 'storage'

    # Campos técnicos
    capacity_gb = db.Column(db.Integer, nullable=True)
    media_type = db.Column(db.String(50), nullable=True)  # SSD, HDD, eMMC
    interface = db.Column(db.String(50), nullable=True)  # NVMe, SATA, PCIe
    form_factor = db.Column(db.String(50), nullable=True)  # M.2, 2.5"
    nvme = db.Column(db.Boolean, default=False)
    read_speed = db.Column(db.Integer, nullable=True)  # MB/s
    write_speed = db.Column(db.Integer, nullable=True)  # MB/s
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='storage', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'capacity_gb': self.capacity_gb,
            'media_type': self.media_type,
            'interface': self.interface,
            'form_factor': self.form_factor,
            'nvme': self.nvme,
            'read_speed': self.read_speed,
            'write_speed': self.write_speed,
            'is_active': self.is_active
        }


class Ram(CatalogMixin, db.Model):
    """
    Tipos de RAM (16GB DDR5, 32GB DDR4, etc.)
    """
    __tablename__ = 'ram'

    # Campos técnicos
    capacity_gb = db.Column(db.Integer, nullable=True)
    ram_type = db.Column(db.String(50), nullable=True)  # DDR4, DDR5, LPDDR5
    speed_mhz = db.Column(db.Integer, nullable=True)
    form_factor = db.Column(db.String(50), nullable=True)  # SO-DIMM, DIMM
    channels = db.Column(db.String(20), nullable=True)  # Dual, Single
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='ram', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'capacity_gb': self.capacity_gb,
            'ram_type': self.ram_type,
            'speed_mhz': self.speed_mhz,
            'form_factor': self.form_factor,
            'channels': self.channels,
            'is_active': self.is_active
        }


class Store(CatalogMixin, db.Model):
    """
    Tiendas (Tienda Principal, Sucursal Centro, etc.)
    """
    __tablename__ = 'stores'

    # Campos adicionales específicos de tiendas
    address = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    manager_name = db.Column(db.String(100))
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='store', lazy='dynamic')
    locations = db.relationship('Location', backref='store_ref', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'manager_name': self.manager_name,
            'is_active': self.is_active
        }


class Location(CatalogMixin, db.Model):
    """
    Ubicaciones dentro de tiendas (Estante A-1, Vitrina 3, Bodega, etc.)
    """
    __tablename__ = 'locations'

    # Relación con tienda (opcional)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    
    # Campos adicionales
    location_type = db.Column(db.String(50), nullable=True)  # shelf, showcase, warehouse
    notes = db.Column(db.Text, nullable=True)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='location', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'store_id': self.store_id,
            'location_type': self.location_type,
            'notes': self.notes,
            'is_active': self.is_active
        }


class Supplier(CatalogMixin, db.Model):
    """
    Proveedores de laptops
    """
    __tablename__ = 'suppliers'

    # Campos adicionales específicos de proveedores
    contact_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    website = db.Column(db.String(200))
    tax_id = db.Column(db.String(50), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='supplier', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'website': self.website,
            'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'is_active': self.is_active
        }


# =============================================================================
# MODELO PRINCIPAL: LAPTOP
# =============================================================================

class Laptop(TimestampMixin, db.Model):
    """
    Modelo principal de inventario de laptops - V2.0 Mejorado
    
    Responsabilidad: SOLO almacenar datos
    Lógica de negocio: en Services (SKUService, FinancialService, etc.)
    """
    __tablename__ = 'laptops'

    # ===== 1. IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    gtin = db.Column(db.String(50), unique=True, nullable=True, index=True)  # UPC/EAN
    icecat_id = db.Column(db.Integer, nullable=True, index=True)
    serial_number = db.Column(db.String(100), nullable=True, index=True)

    # ===== 2. MARKETING Y WEB (SEO) =====
    display_name = db.Column(db.String(200), nullable=False)
    short_description = db.Column(db.String(500), nullable=True)
    long_description_html = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    seo_title = db.Column(db.String(70), nullable=True)
    seo_description = db.Column(db.String(160), nullable=True)
    keywords = db.Column(db.String(500), nullable=True)  # Palabras clave para búsqueda

    # ===== 3. RELACIONES CON CATÁLOGOS =====
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False, index=True)
    model_id = db.Column(db.Integer, db.ForeignKey('laptop_models.id'), nullable=False, index=True)
    processor_id = db.Column(db.Integer, db.ForeignKey('processors.id'), nullable=False)
    os_id = db.Column(db.Integer, db.ForeignKey('operating_systems.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    graphics_card_id = db.Column(db.Integer, db.ForeignKey('graphics_cards.id'), nullable=False)
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'), nullable=False)
    ram_id = db.Column(db.Integer, db.ForeignKey('ram.id'), nullable=False)

    # Logística
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # ===== 4. ESPECIFICACIONES TÉCNICAS NORMALIZADAS (JSON) =====
    # Almacena las especificaciones unificadas del servicio Icecat
    unified_specs = db.Column(db.JSON, default=dict, nullable=True)
    
    # Campos específicos extraídos de unified_specs para búsqueda/indexación
    processor_full_name = db.Column(db.String(200), nullable=True, index=True)
    processor_family = db.Column(db.String(100), nullable=True, index=True)
    processor_generation = db.Column(db.String(100), nullable=True, index=True)
    processor_model_number = db.Column(db.String(100), nullable=True, index=True)
    ram_capacity = db.Column(db.Integer, nullable=True, index=True)
    storage_capacity = db.Column(db.Integer, nullable=True, index=True)
    screen_size = db.Column(db.Numeric(3, 1), nullable=True, index=True)
    has_discrete_gpu = db.Column(db.Boolean, default=False, nullable=True, index=True)

    # ===== 5. DETALLES TÉCNICOS ESPECÍFICOS =====
    npu = db.Column(db.Boolean, default=False, nullable=False)  # Tiene NPU (AI)
    storage_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    ram_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    keyboard_layout = db.Column(db.String(20), default='US', nullable=False)
    keyboard_backlight = db.Column(db.Boolean, default=False, nullable=True)
    keyboard_numeric_pad = db.Column(db.Boolean, default=False, nullable=True)
    fingerprint_reader = db.Column(db.Boolean, default=False, nullable=True)
    face_recognition = db.Column(db.Boolean, default=False, nullable=True)
    touchscreen = db.Column(db.Boolean, default=False, nullable=True)
    stylus_support = db.Column(db.Boolean, default=False, nullable=True)
    
    # Conectividad
    connectivity_ports = db.Column(db.JSON, default=dict, nullable=True)  # Lista de puertos
    wifi_standard = db.Column(db.String(50), nullable=True)  # Wi-Fi 6, Wi-Fi 6E
    bluetooth_version = db.Column(db.String(20), nullable=True)  # 5.0, 5.2
    ethernet_port = db.Column(db.Boolean, default=False, nullable=True)
    cellular = db.Column(db.String(20), nullable=True)  # 4G, 5G
    
    # Datos de Icecat
    full_specs_json = db.Column(db.JSON, default=dict, nullable=True)
    normalized_specs = db.Column(db.JSON, default=dict, nullable=True)
    last_icecat_sync = db.Column(db.DateTime, nullable=True)
    
    # Campos adicionales detectados en DB para compatibilidad
    icecat_import_status = db.Column(db.String(20), default='pending', nullable=False)
    icecat_product_id = db.Column(db.String(100), nullable=True)
    icecat_raw_data = db.Column(db.JSON, nullable=True)
    icecat_imported_at = db.Column(db.DateTime, nullable=True)
    icecat_last_synced_at = db.Column(db.DateTime, nullable=True)
    user_modified_fields = db.Column(db.JSON, nullable=True)
    mpn = db.Column(db.String(100), nullable=True)
    ean = db.Column(db.String(100), nullable=True)
    upc = db.Column(db.String(100), nullable=True)
    msrp = db.Column(db.Numeric(12, 2), nullable=True)
    market_segment = db.Column(db.String(50), nullable=True)

    # ===== 6. ESTADO Y CATEGORÍA =====
    # Valores de category: 'laptop', 'workstation', 'gaming', 'ultrabook', '2in1'
    category = db.Column(db.String(20), nullable=False, default='laptop', index=True)
    # Valores de condition: 'new', 'used', 'refurbished'
    condition = db.Column(db.String(20), nullable=False, default='used', index=True)
    
    # Subcategoría específica
    subcategory = db.Column(db.String(50), nullable=True)  # gaming, business, creative

    # ===== 7. FINANCIEROS =====
    purchase_cost = db.Column(db.Numeric(12, 2), nullable=False)
    sale_price = db.Column(db.Numeric(12, 2), nullable=False)
    discount_price = db.Column(db.Numeric(12, 2), nullable=True)
    tax_percent = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Precios en otras monedas (para referencia)
    sale_price_dop = db.Column(db.Numeric(12, 2), nullable=True)

    # ===== 8. INVENTARIO =====
    quantity = db.Column(db.Integer, default=1, nullable=False)
    reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
    min_alert = db.Column(db.Integer, default=1, nullable=False)
    max_stock = db.Column(db.Integer, nullable=True)  # Stock máximo deseado

    # ===== 9. TIMESTAMPS =====
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    sale_date = db.Column(db.Date, nullable=True)
    warranty_months = db.Column(db.Integer, default=12, nullable=True)
    warranty_expiry = db.Column(db.Date, nullable=True)
    
    # Notas
    internal_notes = db.Column(db.Text, nullable=True)
    public_notes = db.Column(db.Text, nullable=True)
    
    # created_at y updated_at vienen de TimestampMixin

    # ===== RELACIÓN CON USUARIO CREADOR =====
    created_by = db.relationship('User', backref='laptops_created', foreign_keys=[created_by_id])

    # ===== PROPIEDADES CALCULADAS =====

    @property
    def available_quantity(self):
        """Cantidad disponible (total - reservada)"""
        return self.quantity - self.reserved_quantity

    @property
    def effective_price(self):
        """Precio efectivo (con descuento si existe)"""
        if self.discount_price and self.discount_price > 0:
            return self.discount_price
        return self.sale_price

    @property
    def gross_profit(self):
        """Ganancia bruta por unidad"""
        return float(self.effective_price) - float(self.purchase_cost)

    @property
    def margin_percentage(self):
        """Porcentaje de margen"""
        if float(self.purchase_cost) > 0:
            return (self.gross_profit / float(self.purchase_cost)) * 100
        return 0

    @property
    def price_with_tax(self):
        """Precio con impuesto incluido"""
        return float(self.effective_price) * (1 + float(self.tax_percent) / 100)

    @property
    def is_low_stock(self):
        """Indica si el stock está bajo el mínimo de alerta"""
        return self.available_quantity <= self.min_alert
    
    @property
    def is_overstock(self):
        """Indica si hay exceso de stock"""
        if self.max_stock:
            return self.quantity > self.max_stock
        return False
    
    @property
    def gpu_type(self):
        """Retorna el tipo de GPU (dedicada o integrada)"""
        if self.has_discrete_gpu:
            return "dedicated"
        return "integrated"
    
    @property
    def age_days(self):
        """Días desde la entrada al inventario"""
        if self.entry_date:
            return (date.today() - self.entry_date).days
        return 0

    # ===== MÉTODOS DE ACTUALIZACIÓN DESDE ICECAT =====
    
    def update_from_unified_specs(self, unified_specs: dict):
        """
        Actualiza los campos del laptop desde las especificaciones unificadas.
        
        Args:
            unified_specs: Diccionario con especificaciones unificadas de IcecatService
        """
        if not unified_specs:
            return
        
        # Guardar especificaciones completas
        self.unified_specs = unified_specs
        
        # Extraer campos para indexación
        processor = unified_specs.get('procesador', {})
        self.processor_full_name = processor.get('nombre_completo', '')
        
        memory = unified_specs.get('memoria_ram', {})
        self.ram_capacity = memory.get('capacidad_gb', 0)
        
        storage = unified_specs.get('almacenamiento', {})
        self.storage_capacity = storage.get('capacidad_total_gb', 0)
        
        display = unified_specs.get('pantalla', {})
        self.screen_size = display.get('diagonal_pulgadas', 0)
        
        graphics = unified_specs.get('tarjeta_grafica', {})
        self.has_discrete_gpu = graphics.get('tiene_dedicada', False)
        
        # Actualizar campos booleanos
        self.npu = unified_specs.get('caracteristicas_adicionales', {}).get('tiene_npu', False)
        self.ram_upgradeable = unified_specs.get('memoria_ram', {}).get('ampliable', False)
        self.storage_upgradeable = unified_specs.get('almacenamiento', {}).get('ampliable', False)
        
        # Actualizar conectividad
        connectivity = unified_specs.get('conectividad', {})
        self.wifi_standard = connectivity.get('wifi', '')
        self.bluetooth_version = connectivity.get('bluetooth', '')
        self.ethernet_port = connectivity.get('ethernet', False)
        self.cellular = connectivity.get('celular', '')
        
        # Actualizar entrada
        input_data = unified_specs.get('entrada', {})
        self.keyboard_backlight = input_data.get('retroiluminacion', False)
        self.keyboard_numeric_pad = input_data.get('teclado_numerico', False)
        self.fingerprint_reader = input_data.get('lector_huellas', False)
        self.face_recognition = input_data.get('reconocimiento_facial', False)
        self.stylus_support = input_data.get('lapiz_optico', False)
        
        # Actualizar pantalla
        self.touchscreen = display.get('tactil', False)
        
        # Actualizar timestamp de sincronización
        self.last_icecat_sync = datetime.now()

    # ===== MÉTODOS DE SERIALIZACIÓN =====

    def to_dict(self, include_relationships=True, include_specs=False):
        """
        Serializa el objeto a diccionario (para JSON)

        Args:
            include_relationships: Si incluir datos de relaciones (más pesado)
            include_specs: Si incluir especificaciones técnicas completas

        Returns:
            dict con todos los datos del laptop
        """
        data = {
            # Identificadores
            'id': self.id,
            'sku': self.sku,
            'slug': self.slug,
            'gtin': self.gtin,
            'icecat_id': self.icecat_id,
            'serial_number': self.serial_number,

            # Marketing y SEO
            'display_name': self.display_name,
            'short_description': self.short_description,
            'long_description_html': self.long_description_html,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,
            'keywords': self.keywords,

            # Campos indexados de especificaciones
            'processor_full_name': self.processor_full_name,
            'ram_capacity': self.ram_capacity,
            'storage_capacity': self.storage_capacity,
            'screen_size': float(self.screen_size) if self.screen_size else None,
            'has_discrete_gpu': self.has_discrete_gpu,

            # Detalles técnicos
            'npu': self.npu,
            'storage_upgradeable': self.storage_upgradeable,
            'ram_upgradeable': self.ram_upgradeable,
            'keyboard_layout': self.keyboard_layout,
            'keyboard_backlight': self.keyboard_backlight,
            'keyboard_numeric_pad': self.keyboard_numeric_pad,
            'fingerprint_reader': self.fingerprint_reader,
            'face_recognition': self.face_recognition,
            'touchscreen': self.touchscreen,
            'stylus_support': self.stylus_support,
            
            # Conectividad
            'connectivity_ports': self.connectivity_ports,
            'wifi_standard': self.wifi_standard,
            'bluetooth_version': self.bluetooth_version,
            'ethernet_port': self.ethernet_port,
            'cellular': self.cellular,
            
            'last_icecat_sync': self.last_icecat_sync.isoformat() if self.last_icecat_sync else None,

            # Estado y categoría
            'category': self.category,
            'subcategory': self.subcategory,
            'condition': self.condition,
            'gpu_type': self.gpu_type,

            # Financieros
            'purchase_cost': float(self.purchase_cost) if self.purchase_cost else 0,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'discount_price': float(self.discount_price) if self.discount_price else None,
            'tax_percent': float(self.tax_percent) if self.tax_percent else 0,
            'effective_price': float(self.effective_price) if self.effective_price else 0,
            'gross_profit': self.gross_profit,
            'margin_percentage': self.margin_percentage,
            'price_with_tax': self.price_with_tax,

            # Inventario
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'min_alert': self.min_alert,
            'max_stock': self.max_stock,
            'is_low_stock': self.is_low_stock,
            'is_overstock': self.is_overstock,
            
            # Garantía
            'warranty_months': self.warranty_months,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,

            # Timestamps
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'age_days': self.age_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,

            # Notas
            'internal_notes': self.internal_notes,
            'public_notes': self.public_notes
        }
        
        # Incluir especificaciones unificadas si se solicita
        if include_specs and self.unified_specs:
            data['unified_specs'] = self.unified_specs

        # Incluir relaciones si se solicita
        if include_relationships:
            data.update({
                'brand': self.brand.name if self.brand else None,
                'brand_id': self.brand_id,
                'model': self.model.name if self.model else None,
                'model_id': self.model_id,
                'processor': self.processor.name if self.processor else None,
                'processor_id': self.processor_id,
                'operating_system': self.operating_system.name if self.operating_system else None,
                'os_id': self.os_id,
                'screen': self.screen.name if self.screen else None,
                'screen_id': self.screen_id,
                'graphics_card': self.graphics_card.name if self.graphics_card else None,
                'graphics_card_id': self.graphics_card_id,
                'storage': self.storage.name if self.storage else None,
                'storage_id': self.storage_id,
                'ram': self.ram.name if self.ram else None,
                'ram_id': self.ram_id,
                'store': self.store.name if self.store else None,
                'store_id': self.store_id,
                'location': self.location.name if self.location else None,
                'location_id': self.location_id,
                'supplier': self.supplier.name if self.supplier else None,
                'supplier_id': self.supplier_id,
                'created_by_username': self.created_by.username if self.created_by else None,
                'images': [img.to_dict() for img in self.images] if hasattr(self, 'images') else []
            })

        return data
    
    def to_public_dict(self) -> dict:
        """
        Retorna un diccionario con los datos públicos del laptop.
        Para uso en catálogos públicos y APIs.
        """
        return {
            'sku': self.sku,
            'slug': self.slug,
            'display_name': self.display_name,
            'short_description': self.short_description,
            'brand': self.brand.name if self.brand else None,
            'model': self.model.name if self.model else None,
            'processor': self.processor_full_name,
            'ram': f"{self.ram_capacity}GB" if self.ram_capacity else None,
            'storage': f"{self.storage_capacity}GB" if self.storage_capacity else None,
            'screen_size': float(self.screen_size) if self.screen_size else None,
            'graphics': 'Dedicada' if self.has_discrete_gpu else 'Integrada',
            'os': self.operating_system.name if self.operating_system else None,
            'category': self.category,
            'condition': self.condition,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'discount_price': float(self.discount_price) if self.discount_price else None,
            'price_with_tax': self.price_with_tax,
            'is_available': self.available_quantity > 0,
            'images': [img.to_dict() for img in self.images] if hasattr(self, 'images') else [],
            'warranty_months': self.warranty_months
        }

    def __repr__(self):
        """Representación en string del objeto"""
        return f'<Laptop {self.sku} - {self.display_name}>'

    # ===== ÍNDICES COMPUESTOS (para optimización de queries) =====
    __table_args__ = (
        db.Index('idx_laptop_brand_category', 'brand_id', 'category'),
        db.Index('idx_laptop_published_featured', 'is_published', 'is_featured'),
        db.Index('idx_laptop_entry_date', 'entry_date'),
        db.Index('idx_laptop_store_location', 'store_id', 'location_id'),
        db.Index('idx_laptop_specs', 'processor_full_name', 'ram_capacity', 'storage_capacity'),
        db.Index('idx_laptop_gpu', 'has_discrete_gpu'),
        db.Index('idx_laptop_screen', 'screen_size'),
        db.Index('idx_laptop_price', 'sale_price'),
    )


# =============================================================================
# MODELO DE IMÁGENES
# =============================================================================

class LaptopImage(TimestampMixin, db.Model):
    """
    Galería de imágenes vinculada a una Laptop específica.
    """
    __tablename__ = 'laptop_images'

    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)  # Ruta de la imagen
    position = db.Column(db.Integer, default=0, nullable=False)  # Posición en galería
    alt_text = db.Column(db.String(255), nullable=True)  # SEO alt text
    is_cover = db.Column(db.Boolean, default=False, nullable=False)  # Es portada
    ordering = db.Column(db.Integer, default=0, nullable=False)
    
    # Metadatos de la imagen
    file_size = db.Column(db.Integer, nullable=True)  # Tamaño en bytes
    width = db.Column(db.Integer, nullable=True)  # Ancho en píxeles
    height = db.Column(db.Integer, nullable=True)  # Alto en píxeles
    mime_type = db.Column(db.String(50), nullable=True)  # image/jpeg, image/png
    source = db.Column(db.String(50), default='upload')  # upload, icecat, url

    # Relación - lazy='select' para permitir eager loading
    laptop = db.relationship('Laptop', backref=db.backref('images', lazy='select', cascade='all, delete-orphan'))

    def to_dict(self):
        """Serializa la imagen a diccionario"""
        return {
            'id': self.id,
            'laptop_id': self.laptop_id,
            'image_path': self.image_path,
            'position': self.position,
            'alt_text': self.alt_text,
            'is_cover': self.is_cover,
            'ordering': self.ordering,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'mime_type': self.mime_type,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<LaptopImage {self.id} - Laptop {self.laptop_id}>'

    __table_args__ = (
        db.Index('idx_laptop_image_laptop_cover', 'laptop_id', 'is_cover'),
    )


# =============================================================================
# MODELO DE HISTORIAL DE PRECIOS
# =============================================================================

class LaptopPriceHistory(TimestampMixin, db.Model):
    """
    Historial de cambios de precios de una laptop.
    """
    __tablename__ = 'laptop_price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=False, index=True)
    
    # Precios anteriores
    old_purchase_cost = db.Column(db.Numeric(12, 2), nullable=True)
    old_sale_price = db.Column(db.Numeric(12, 2), nullable=True)
    old_discount_price = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Precios nuevos
    new_purchase_cost = db.Column(db.Numeric(12, 2), nullable=True)
    new_sale_price = db.Column(db.Numeric(12, 2), nullable=True)
    new_discount_price = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Metadatos del cambio
    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    change_reason = db.Column(db.String(255), nullable=True)
    
    # Relaciones
    laptop = db.relationship('Laptop', backref='price_history', lazy='select')
    changed_by = db.relationship('User', backref='price_changes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'laptop_id': self.laptop_id,
            'old_purchase_cost': float(self.old_purchase_cost) if self.old_purchase_cost else None,
            'old_sale_price': float(self.old_sale_price) if self.old_sale_price else None,
            'old_discount_price': float(self.old_discount_price) if self.old_discount_price else None,
            'new_purchase_cost': float(self.new_purchase_cost) if self.new_purchase_cost else None,
            'new_sale_price': float(self.new_sale_price) if self.new_sale_price else None,
            'new_discount_price': float(self.new_discount_price) if self.new_discount_price else None,
            'changed_by': self.changed_by.username if self.changed_by else None,
            'change_reason': self.change_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODELO DE ESTADÍSTICAS DE VISTAS
# =============================================================================

class LaptopViewStats(db.Model):
    """
    Estadísticas de vistas de una laptop.
    """
    __tablename__ = 'laptop_view_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=False, index=True)
    
    # Contadores
    total_views = db.Column(db.Integer, default=0)
    unique_views = db.Column(db.Integer, default=0)
    
    # Vistas por período
    views_today = db.Column(db.Integer, default=0)
    views_this_week = db.Column(db.Integer, default=0)
    views_this_month = db.Column(db.Integer, default=0)
    
    # Fechas de reset
    last_reset_date = db.Column(db.Date, default=date.today)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    laptop = db.relationship('Laptop', backref='view_stats', uselist=False)
    
    def increment_view(self, unique=False):
        """Incrementa los contadores de vistas"""
        self.total_views += 1
        self.views_today += 1
        self.views_this_week += 1
        self.views_this_month += 1
        
        if unique:
            self.unique_views += 1
        
        self.updated_at = datetime.utcnow()
    
    def reset_periodic_counters(self):
        """Reinicia los contadores periódicos si es necesario"""
        today = date.today()
        
        if self.last_reset_date != today:
            # Verificar si es un nuevo día
            self.views_today = 0
            
            # Verificar si es una nueva semana
            if today.weekday() == 0:  # Lunes
                self.views_this_week = 0
            
            # Verificar si es un nuevo mes
            if today.day == 1:
                self.views_this_month = 0
            
            self.last_reset_date = today
    
    def to_dict(self):
        return {
            'laptop_id': self.laptop_id,
            'total_views': self.total_views,
            'unique_views': self.unique_views,
            'views_today': self.views_today,
            'views_this_week': self.views_this_week,
            'views_this_month': self.views_this_month,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Exportar modelos
__all__ = [
    'Brand',
    'LaptopModel',
    'Processor',
    'OperatingSystem',
    'Screen',
    'GraphicsCard',
    'Storage',
    'Ram',
    'Store',
    'Location',
    'Supplier',
    'Laptop',
    'LaptopImage',
    'LaptopPriceHistory',
    'LaptopViewStats'
]
