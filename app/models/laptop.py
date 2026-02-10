# -*- coding: utf-8 -*-
"""
================================================================================
MODELOS DE INVENTARIO DE LAPTOPS - V2.0 MEJORADO
================================================================================
VersiÃ³n: 2.0
Fecha: 2025-02-07
DescripciÃ³n: Modelo de datos unificado y mejorado para inventario de laptops.
             Compatible con el sistema de estandarizaciÃ³n de Icecat.

CaracterÃ­sticas:
    - Campos JSON para especificaciones normalizadas
    - Soporte para especificaciones unificadas de todas las marcas
    - Campos calculados para propiedades derivadas
    - Ãndices optimizados para bÃºsquedas frecuentes
    - Relaciones con catÃ¡logos normalizados
================================================================================
"""

from app import db
from app.models.mixins import TimestampMixin, CatalogMixin
from datetime import datetime, date
import json


# =============================================================================
# MODELOS DE CATÃLOGO (usan CatalogMixin)
# =============================================================================

class Brand(CatalogMixin, db.Model):
    """
    Marcas de laptops (Dell, HP, Lenovo, etc.)
    Usa CatalogMixin: id, name, is_active, timestamps, mÃ©todos get_active() y get_or_create()
    """
    __tablename__ = 'brands'

    # Campos adicionales especÃ­ficos
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
    El campo 'name' de CatalogMixin almacena el nombre de la generaciÃ³n.
    """
    __tablename__ = 'processors'

    # Campos tÃ©cnicos adicionales
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
    full_name = db.Column(db.String(255), nullable=True)  # NEW: Persisted full name
    has_npu = db.Column(db.Boolean, default=False)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='processor', lazy='dynamic')
    
    @property
    def all_info(self):
        """Retorna una cadena combinada con toda la informaciÃ³n del procesador"""
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
    full_name = db.Column(db.String(255), nullable=True)  # NEW: Persisted full name
    
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

    # Campos tÃ©cnicos
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
    full_name = db.Column(db.String(255), nullable=True)  # NEW: Persisted full name
    
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
    Tarjetas GrÃ¡ficas (NVIDIA RTX 4060, Intel Iris Xe, etc.)
    """
    __tablename__ = 'graphics_cards'

    # Campos tÃ©cnicos (HÃ­brido / Granular)
    # GPU Dedicada
    discrete_brand = db.Column(db.String(50), nullable=True)
    discrete_model = db.Column(db.String(100), nullable=True)
    discrete_memory_gb = db.Column(db.Integer, nullable=True)
    discrete_memory_type = db.Column(db.String(50), nullable=True)
    
    # GPU Integrada
    onboard_brand = db.Column(db.String(50), nullable=True)
    onboard_model = db.Column(db.String(100), nullable=True)
    onboard_family = db.Column(db.String(50), nullable=True)
    onboard_memory_gb = db.Column(db.Integer, nullable=True) # NEW

    # Legacy / Resumen (se mantienen para compatibilidad o como calculados)
    brand = db.Column(db.String(50), nullable=True)  # Marca principal
    gpu_type = db.Column(db.String(50), nullable=True)  # dedicated, integrated (calculado)
    memory_gb = db.Column(db.Integer, nullable=True) # Memoria total o dedicada principal
    memory_type = db.Column(db.String(50), nullable=True)
    
    # Flags especiales
    has_discrete_gpu = db.Column(db.Boolean, default=False)
    ray_tracing = db.Column(db.Boolean, default=False)
    dlss = db.Column(db.Boolean, default=False)
    discrete_full_name = db.Column(db.String(255), nullable=True)  # NEW
    onboard_full_name = db.Column(db.String(255), nullable=True)   # NEW
    tdp = db.Column(db.String(20), nullable=True)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='graphics_card', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'discrete_brand': self.discrete_brand,
            'discrete_model': self.discrete_model,
            'discrete_memory_gb': self.discrete_memory_gb,
            'discrete_memory_type': self.discrete_memory_type,
            'onboard_brand': self.onboard_brand,
            'onboard_model': self.onboard_model,
            'onboard_family': self.onboard_family,
            'onboard_memory_gb': self.onboard_memory_gb,
            'has_discrete_gpu': self.has_discrete_gpu,
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

    # Campos tÃ©cnicos
    capacity_gb = db.Column(db.Integer, nullable=True)
    media_type = db.Column(db.String(50), nullable=True)  # SSD, HDD, eMMC
    interface = db.Column(db.String(50), nullable=True)  # NVMe, SATA, PCIe
    form_factor = db.Column(db.String(50), nullable=True)  # M.2, 2.5"
    nvme = db.Column(db.Boolean, default=False)
    read_speed = db.Column(db.Integer, nullable=True)  # MB/s
    write_speed = db.Column(db.Integer, nullable=True)  # MB/s
    full_name = db.Column(db.String(255), nullable=True)  # NEW: Persisted full name
    
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

    # Campos tÃ©cnicos
    capacity_gb = db.Column(db.Integer, nullable=True)
    ram_type = db.Column(db.String(50), nullable=True)  # DDR4, DDR5, LPDDR5
    speed_mhz = db.Column(db.Integer, nullable=True)
    transfer_rate = db.Column(db.String(50), nullable=True) # MT/s
    full_name = db.Column(db.String(255), nullable=True)  # NEW: Persisted full name
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
            'transfer_rate': self.transfer_rate,
            'form_factor': self.form_factor,
            'channels': self.channels,
            'is_active': self.is_active
        }


class Store(CatalogMixin, db.Model):
    """
    Tiendas (Tienda Principal, Sucursal Centro, etc.)
    """
    __tablename__ = 'stores'

    # Campos adicionales especÃ­ficos de tiendas
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

    # RelaciÃ³n con tienda (opcional)
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

    # Campos adicionales especÃ­ficos de proveedores
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
    LÃ³gica de negocio: en Services (SKUService, FinancialService, etc.)
    """
    __tablename__ = 'laptops'

    # ===== 1. IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    gtin = db.Column(db.String(50), unique=True, nullable=True, index=True)  # UPC/EAN
    icecat_id = db.Column(db.Integer, nullable=True, index=True)

    # ===== 2. MARKETING Y WEB (SEO) =====
    display_name = db.Column(db.String(400), nullable=False)
    short_description = db.Column(db.String(500), nullable=True)
    long_description_html = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    seo_title = db.Column(db.String(70), nullable=True)
    seo_description = db.Column(db.String(160), nullable=True)
    keywords = db.Column(db.String(500), nullable=True)  # Palabras clave para bÃºsqueda

    # ===== 3. RELACIONES CON CATÃLOGOS =====
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False, index=True)
    model_id = db.Column(db.Integer, db.ForeignKey('laptop_models.id'), nullable=False, index=True)
    processor_id = db.Column(db.Integer, db.ForeignKey('processors.id'), nullable=False)
    os_id = db.Column(db.Integer, db.ForeignKey('operating_systems.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    graphics_card_id = db.Column(db.Integer, db.ForeignKey('graphics_cards.id'), nullable=False)
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'), nullable=False)
    ram_id = db.Column(db.Integer, db.ForeignKey('ram.id'), nullable=False)

    # LogÃ­stica
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # ===== 4. ESPECIFICACIONES TÃ‰CNICAS (VINCULADAS) =====
    # Almacena las especificaciones unificadas completas para referencia
    unified_specs = db.Column(db.JSON, default=dict, nullable=True)
    weight_lbs = db.Column(db.Numeric(5, 2), nullable=True)  # Peso en libras

    # ===== 5. DETALLES TÃ‰CNICOS ESPECÃFICOS =====
    storage_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    ram_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    
    # Detalle de almacenamiento y RAM se mantienen aquÃ­ como booleanos de capacidad
    storage_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    ram_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    
    # Teclado y Entrada
    keyboard_layout = db.Column(db.String(20), default='US', nullable=False)
    keyboard_backlight = db.Column(db.Boolean, default=False, nullable=True)
    numeric_keypad = db.Column(db.Boolean, default=False, nullable=True)
    keyboard_language = db.Column(db.String(50), nullable=True)
    pointing_device = db.Column(db.String(100), nullable=True)
    keyboard_backlight_color = db.Column(db.String(50), nullable=True)
    keyboard_backlight_zone = db.Column(db.String(50), nullable=True)
    
    fingerprint_reader = db.Column(db.Boolean, default=False, nullable=True)
    face_recognition = db.Column(db.Boolean, default=False, nullable=True)
    # touchscreen se mueve a Screen, aquÃ­ queda para sobreescritura manual si aplica
    touchscreen_override = db.Column(db.Boolean, nullable=True)
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

    # ===== 6. ESTADO Y CATEGORÃA =====
    # Valores de category: 'laptop', 'workstation', 'gaming', 'ultrabook', '2in1'
    category = db.Column(db.String(20), nullable=False, default='laptop', index=True)
    # Valores de condition: 'new', 'used', 'refurbished'
    condition = db.Column(db.String(20), nullable=False, default='used', index=True)
    
    # SubcategorÃ­a especÃ­fica
    subcategory = db.Column(db.String(50), nullable=True)  # gaming, business, creative

    # ===== 7. FINANCIEROS =====
    purchase_cost = db.Column(db.Numeric(12, 2), nullable=False)
    sale_price = db.Column(db.Numeric(12, 2), nullable=False)
    discount_price = db.Column(db.Numeric(12, 2), nullable=True)
    tax_percent = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)
    currency = db.Column(db.String(3), default='DOP', nullable=False)
    
    # Precios en otras monedas (para referencia)
    sale_price_dop = db.Column(db.Numeric(12, 2), nullable=True)

    # ===== 8. INVENTARIO =====
    quantity = db.Column(db.Integer, default=1, nullable=False)
    reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
    min_alert = db.Column(db.Integer, default=1, nullable=False)
    max_stock = db.Column(db.Integer, nullable=True)  # Stock mÃ¡ximo deseado

    # ===== 9. TIMESTAMPS =====
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    sale_date = db.Column(db.Date, nullable=True)
    warranty_months = db.Column(db.Integer, default=12, nullable=True)
    warranty_expiry = db.Column(db.Date, nullable=True)
    
    # Notas
    internal_notes = db.Column(db.Text, nullable=True)
    public_notes = db.Column(db.Text, nullable=True)
    
    # created_at y updated_at vienen de TimestampMixin

    # ===== RELACIÃ“N CON USUARIO CREADOR =====
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
        """Indica si el stock estÃ¡ bajo el mÃ­nimo de alerta"""
        return self.available_quantity <= self.min_alert
    
    @property
    def is_overstock(self):
        """Indica si hay exceso de stock"""
        if self.max_stock:
            return self.quantity > self.max_stock
        return False
    
    @property
    def has_discrete_gpu(self):
        """Indica si tiene GPU dedicada basÃ¡ndose en la relaciÃ³n con graphics_card"""
        if self.graphics_card and self.graphics_card.gpu_type == 'dedicated':
            return True
        return False

    @property
    def gpu_type(self):
        """Retorna el tipo de GPU (dedicada o integrada)"""
        if self.has_discrete_gpu:
            return "dedicated"
        return "integrated"
    
    # ===== PROPIEDADES DELEGADAS (SINGLE SOURCE OF TRUTH) =====
    
    @property
    def processor_family(self):
        return self.processor.family if self.processor else None

    @processor_family.setter
    def processor_family(self, value):
        if self.processor:
            self.processor.family = value

    @property
    def processor_generation(self):
        return self.processor.generation if self.processor else None

    @processor_generation.setter
    def processor_generation(self, value):
        if self.processor:
            self.processor.generation = value

    @property
    def processor_model(self):
        return self.processor.model_number if self.processor else None

    @processor_model.setter
    def processor_model(self, value):
        if self.processor:
            self.processor.model_number = value

    @property
    def npu(self):
        return self.processor.has_npu if self.processor else False

    @npu.setter
    def npu(self, value):
        if self.processor:
            self.processor.has_npu = bool(value)

    @property
    def processor_full_name(self):
        return self.processor.full_name if self.processor else None

    @processor_full_name.setter
    def processor_full_name(self, value):
        # Generalmente informativo, no intentamos parsearlo de vuelta
        pass


    @property
    def ram_capacity(self):
        return self.ram.capacity_gb if self.ram else 0

    @ram_capacity.setter
    def ram_capacity(self, value):
        if self.ram:
            try:
                self.ram.capacity_gb = int(value)
            except (ValueError, TypeError):
                pass

    @property
    def ram_type(self):
        return self.ram.ram_type if self.ram else None

    @ram_type.setter
    def ram_type(self, value):
        if self.ram:
            self.ram.ram_type = value

    @property
    def storage_capacity(self):
        return self.storage.capacity_gb if self.storage else 0

    @storage_capacity.setter
    def storage_capacity(self, value):
        if self.storage:
            try:
                self.storage.capacity_gb = int(value)
            except (ValueError, TypeError):
                pass

    @property
    def screen_size(self):
        return float(self.screen.diagonal_inches) if self.screen and self.screen.diagonal_inches else 0.0

    @screen_size.setter
    def screen_size(self, value):
        if self.screen:
            try:
                from decimal import Decimal
                self.screen.diagonal_inches = Decimal(str(value))
            except (ValueError, TypeError, Decimal.InvalidOperation):
                pass

    @property
    def touchscreen(self):
        if self.touchscreen_override is not None:
            return self.touchscreen_override
        return self.screen.touchscreen if self.screen else False

    @touchscreen.setter
    def touchscreen(self, value):
        self.touchscreen_override = bool(value)

    @property
    def screen_full_name(self):
        return self.screen.full_name if self.screen else None

    @property
    def discrete_gpu_full_name(self):
        return self.graphics_card.discrete_full_name if self.graphics_card else None

    @property
    def onboard_gpu_full_name(self):
        return self.graphics_card.onboard_full_name if self.graphics_card else None

    @property
    def storage_full_name(self):
        return self.storage.full_name if self.storage else None

    @property
    def ram_full_name(self):
        return self.ram.full_name if self.ram else None

    # ===== RESÃšMENES DINÃMICOS =====

    @staticmethod
    def _map_resolution_name(resolution_str):
        """Mapea una resoluciÃ³n de texto a su etiqueta comercial (2K, 4K, etc.)"""
        if not resolution_str:
            return None
        
        # Extraer el primer nÃºmero (horizontal)
        import re
        match = re.search(r'(\d{3,4})', resolution_str)
        if not match:
            return None
            
        h_res = int(match.group(1))
        
        if 1800 <= h_res <= 2000:
            return "FHD"
        elif 2000 < h_res <= 2600:
            return "2K"
        elif 2600 < h_res <= 2900:
            return "2.5K"
        elif 2900 < h_res <= 3400:
            return "3K"
        elif 3400 < h_res <= 4500:
            return "4K"
        elif 7000 < h_res <= 8500:
            return "8K"
        
        return None

    @property
    def processor_summary(self):
        """Genera el resumen de procesador: 'AMD Ryzen 8000 Series Ryzen 7 8940HX'"""
        if not self.processor: return None
        
        parts = []
        gen = self.processor.generation or ""
        fam = self.processor.family or ""
        model = self.processor.model_number or ""
        
        if gen: parts.append(gen)
        if fam and fam.lower() not in gen.lower():
            parts.append(fam)
        if model: parts.append(model)
        
        # Eliminar duplicados consecutivos
        clean_parts = []
        for p in parts:
            if not clean_parts or p.lower() != clean_parts[-1].lower():
                clean_parts.append(p)
                
        return ' '.join(clean_parts) or self.processor.name

    @property
    def display_summary(self):
        """Genera el resumen de pantalla: '15.6" 4K AMOLED 144Hz Touch'"""
        if not self.screen: return None
        parts = []
        if self.screen.diagonal_inches: parts.append(f"{self.screen.diagonal_inches}\"")
        
        # Obtener etiqueta de resoluciÃ³n (2K, 4K, etc.)
        res_label = self._map_resolution_name(self.screen.resolution)
        if res_label:
            parts.append(res_label)
            
        if self.screen.hd_type:
            # Agregar Tipo HD si no es idÃ©ntico al label (evitar FHD FHD)
            if not res_label or self.screen.hd_type.lower() != res_label.lower():
                parts.append(self.screen.hd_type)
            
        if self.screen.panel_type:
            # Eliminar '-Level' del panel
            panel = self.screen.panel_type.replace('-Level', '')
            parts.append(panel)
            
        if self.screen.refresh_rate and self.screen.refresh_rate > 60: parts.append(f"{self.screen.refresh_rate}Hz")
        if self.touchscreen: parts.append('Touch')
        return ' '.join(parts) if parts else self.screen.name

    @property
    def memory_summary(self):
        """Genera el resumen de memoria: '16GB DDR5 6400MHz'"""
        if not self.ram: return None
        parts = []
        if self.ram.capacity_gb: parts.append(f"{self.ram.capacity_gb}GB")
        if self.ram.ram_type: parts.append(self.ram.ram_type)
        if self.ram.speed_mhz: parts.append(f"{self.ram.speed_mhz}MHz")
        return ' '.join(parts) if parts else self.ram.name

    @property
    def storage_summary(self):
        """Genera el resumen de almacenamiento: '512GB SSD NVMe M.2'"""
        if not self.storage: return None
        parts = []
        if self.storage.capacity_gb:
            if self.storage.capacity_gb >= 1024:
                parts.append(f"{round(self.storage.capacity_gb / 1024, 1)}TB")
            else:
                parts.append(f"{self.storage.capacity_gb}GB")
        if self.storage.media_type: parts.append(self.storage.media_type)
        if self.storage.nvme: parts.append('NVMe')
        if self.storage.form_factor: parts.append(self.storage.form_factor)
        return ' '.join(parts) if parts else self.storage.name

    @property
    def discrete_gpu_summary(self):
        """Genera el resumen de GPU dedicada: 'NVIDIA RTX 4060 8GB GDDR6'"""
        if not self.graphics_card or not self.graphics_card.discrete_model:
            return None
        parts = []
        # Deduplicar marca y nombre
        brand = self.graphics_card.brand or ""
        name = self.graphics_card.name or ""
        
        if brand and brand.lower() not in name.lower():
            parts.append(brand)
        parts.append(name)
        
        if self.graphics_card.memory_gb: parts.append(f"{self.graphics_card.memory_gb}GB")
        if self.graphics_card.memory_type: parts.append(self.graphics_card.memory_type)
        
        # Eliminar palabras duplicadas consecutivas
        clean_parts = []
        for p in parts:
            if not clean_parts or p.lower() != clean_parts[-1].lower():
                clean_parts.append(p)
        return ' '.join(clean_parts)

    @property
    def integrated_gpu_summary(self):
        """Genera el resumen de GPU integrada: 'Intel Iris Xe'"""
        if not self.graphics_card or not self.graphics_card.onboard_model:
            return None
        parts = []
        brand = self.graphics_card.brand or ""
        name = self.graphics_card.name or ""
        
        if brand and brand.lower() not in name.lower():
            parts.append(brand)
        parts.append(name)
        
        # Eliminar palabras duplicadas consecutivas
        clean_parts = []
        for p in parts:
            if not clean_parts or p.lower() != clean_parts[-1].lower():
                clean_parts.append(p)
        return ' '.join(clean_parts)
    
    @property
    def age_days(self):
        """DÃ­as desde la entrada al inventario"""
        if self.entry_date:
            return (date.today() - self.entry_date).days
        return 0

    # ===== MÃ‰TODOS DE ACTUALIZACIÃ“N DESDE ICECAT =====
    
    def update_from_unified_specs(self, unified_specs: dict):
        """
        Actualiza los vÃ­nculos y metadata del laptop desde las especificaciones unificadas.
        La informaciÃ³n tÃ©cnica vive en las tablas de catÃ¡logo relacionadas.
        """
        if not unified_specs:
            return
        
        # Guardar especificaciones completas para referencia legacy
        self.unified_specs = unified_specs
        
        # 1. Obtener secciones de especificaciones
        processor = unified_specs.get('procesador', {})
        memory = unified_specs.get('memoria_ram', {})
        storage = unified_specs.get('almacenamiento', {})
        display = unified_specs.get('pantalla', {})
        graphics = unified_specs.get('tarjeta_grafica', {})
        connectivity = unified_specs.get('conectividad', {})
        input_data = unified_specs.get('entrada', {})
        physical = unified_specs.get('fisico', {})
        additional = unified_specs.get('caracteristicas_adicionales', {})

        # 2. Actualizar metadata de Laptop (lo que no es catÃ¡logo)
        self.ram_upgradeable = memory.get('ampliable', False)
        self.storage_upgradeable = storage.get('ampliable', False)
        
        # Conectividad
        self.wifi_standard = connectivity.get('wifi', '')
        self.bluetooth_version = connectivity.get('bluetooth', '')
        self.ethernet_port = connectivity.get('ethernet', False)
        self.cellular = connectivity.get('celular', '')
        
        # Entrada
        self.keyboard_backlight = input_data.get('retroiluminacion', False)
        self.keyboard_numeric_pad = input_data.get('teclado_numerico', False)
        self.fingerprint_reader = input_data.get('lector_huellas', False)
        self.face_recognition = input_data.get('reconocimiento_facial', False)
        self.stylus_support = input_data.get('lapiz_optico', False)
        self.keyboard_layout = input_data.get('disposicion_teclado', '')
        
        # Peso
        if physical.get('peso_lbs'):
            self.weight_lbs = physical.get('peso_lbs')

        # 3. VÃNCULO CON CATÃLOGOS (FOREIGN KEYS)
        from app.services.catalog_service import CatalogService
        
        # Procesador (incluyendo NPU)
        self.processor_id = CatalogService.get_or_create_processor(
            family=processor.get('familia'),
            generation=processor.get('generacion'),
            model=processor.get('modelo'),
            manufacturer=processor.get('fabricante'),
            has_npu=additional.get('tiene_npu', False)
        )
        
        # Pantalla
        self.screen_id = CatalogService.get_or_create_screen(
            diagonal_inches=display.get('diagonal_pulgadas'),
            resolution=display.get('resolucion'),
            panel_type=display.get('tipo_panel') or display.get('tipo'),
            hd_type=display.get('tipo_hd'),
            touchscreen=display.get('tactil'),
            refresh_rate=display.get('tasa_refresco_hz'),
            brightness=display.get('brillo_nits'),
            aspect_ratio=display.get('relacion_aspecto'),
            color_gamut=display.get('gama_colores'),
            hdr=display.get('hdr')
        )
        
        # Memoria RAM
        self.ram_id = CatalogService.get_or_create_ram(
            capacity_gb=memory.get('capacidad_gb'),
            ram_type=memory.get('tipo'),
            speed_mhz=memory.get('velocidad_mhz'),
            form_factor=memory.get('factor_forma'),
            channels=memory.get('canales'),
            layout=memory.get('distribucion')
        )
        
        # Almacenamiento
        self.storage_id = CatalogService.get_or_create_storage(
            capacity_gb=storage.get('capacidad_total_gb'),
            media_type=storage.get('tipo_medio'),
            interface=storage.get('interfaz_ssd'),
            form_factor=storage.get('factor_forma_ssd'),
            nvme=storage.get('nvme')
        )
        
        # Tarjeta GrÃ¡fica
        if graphics.get('tiene_dedicada'):
            self.has_discrete_gpu = True
            self.graphics_card_id = CatalogService.get_or_create_graphics_card(
                brand=graphics.get('marca_dedicada'),
                name=graphics.get('modelo_dedicada'),
                memory_gb=graphics.get('memoria_dedicada_gb'),
                memory_type=graphics.get('tipo_memoria_dedicada'),
                gpu_type='dedicated',
                ray_tracing=graphics.get('ray_tracing'),
                dlss=graphics.get('dlss')
            )
        else:
            self.has_discrete_gpu = False
            self.graphics_card_id = CatalogService.get_or_create_graphics_card(
                brand=graphics.get('marca_integrada'),
                name=graphics.get('modelo_integrada'),
                onboard_family=graphics.get('familia_integrada'),
                gpu_type='integrated'
            )
        
        self.last_icecat_sync = datetime.now()
        
        # Actualizar timestamp de sincronizaciÃ³n
        self.last_icecat_sync = datetime.now()

    # ===== MÃ‰TODOS DE SERIALIZACIÃ“N =====

    def to_dict(self, include_relationships=True, include_specs=False):
        """
        Serializa el objeto a diccionario (para JSON)

        Args:
            include_relationships: Si incluir datos de relaciones (mÃ¡s pesado)
            include_specs: Si incluir especificaciones tÃ©cnicas completas

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

            # Marketing y SEO
            'display_name': self.display_name,
            'short_description': self.short_description,
            'long_description_html': self.long_description_html,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,
            'keywords': self.keywords,

            # Especificaciones Resumidas (DinÃ¡micas)
            'display_summary': self.display_summary,
            'memory_summary': self.memory_summary,
            'storage_summary': self.storage_summary,
            'discrete_gpu_summary': self.discrete_gpu_summary,
            'integrated_gpu_summary': self.integrated_gpu_summary,
            'weight_lbs': float(self.weight_lbs) if self.weight_lbs else None,

            # Detalles tÃ©cnicos
            'npu': self.npu,
            'storage_upgradeable': self.storage_upgradeable,
            'ram_upgradeable': self.ram_upgradeable,
            'keyboard_layout': self.keyboard_layout,
            'keyboard_backlight': self.keyboard_backlight,
            'keyboard_numeric_pad': self.numeric_keypad,
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

            # Estado y categorÃ­a
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
            
            # GarantÃ­a
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
                'images': [img.to_dict() for img in self.images] if hasattr(self, 'images') else [],
                'serials': [
                    {
                        'id': s.id,
                        'serial_number': s.serial_number,
                        'status': s.status
                    } for s in self.serials.all()
                ] if hasattr(self, 'serials') else []
            })

        return data
    
    def to_public_dict(self) -> dict:
        """
        Retorna un diccionario con los datos pÃºblicos del laptop.
        Para uso en catÃ¡logos pÃºblicos y APIs.
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
        """RepresentaciÃ³n en string del objeto"""
        return f'<Laptop {self.sku} - {self.display_name}>'

    # ===== ÃNDICES COMPUESTOS =====
    __table_args__ = (
        db.Index('idx_laptop_brand_category', 'brand_id', 'category'),
        db.Index('idx_laptop_published_featured', 'is_published', 'is_featured'),
        db.Index('idx_laptop_entry_date', 'entry_date'),
        db.Index('idx_laptop_store_location', 'store_id', 'location_id'),
        db.Index('idx_laptop_price', 'sale_price'),
    )


# =============================================================================
# MODELO DE IMÃGENES
# =============================================================================

class LaptopImage(TimestampMixin, db.Model):
    """
    GalerÃ­a de imÃ¡genes vinculada a una Laptop especÃ­fica.
    """
    __tablename__ = 'laptop_images'

    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)  # Ruta de la imagen
    position = db.Column(db.Integer, default=0, nullable=False)  # PosiciÃ³n en galerÃ­a
    alt_text = db.Column(db.String(255), nullable=True)  # SEO alt text
    is_cover = db.Column(db.Boolean, default=False, nullable=False)  # Es portada
    ordering = db.Column(db.Integer, default=0, nullable=False)
    
    # Metadatos de la imagen
    file_size = db.Column(db.Integer, nullable=True)  # TamaÃ±o en bytes
    width = db.Column(db.Integer, nullable=True)  # Ancho en pÃ­xeles
    height = db.Column(db.Integer, nullable=True)  # Alto en pÃ­xeles
    mime_type = db.Column(db.String(50), nullable=True)  # image/jpeg, image/png
    source = db.Column(db.String(50), default='upload')  # upload, icecat, url

    # RelaciÃ³n - lazy='select' para permitir eager loading
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
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
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
# MODELO DE ESTADÃSTICAS DE VISTAS
# =============================================================================

class LaptopViewStats(db.Model):
    """
    EstadÃ­sticas de vistas de una laptop.
    """
    __tablename__ = 'laptop_view_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=False, index=True)
    
    # Contadores
    total_views = db.Column(db.Integer, default=0)
    unique_views = db.Column(db.Integer, default=0)
    
    # Vistas por perÃ­odo
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
        """Reinicia los contadores periÃ³dicos si es necesario"""
        today = date.today()
        
        if self.last_reset_date != today:
            # Verificar si es un nuevo dÃ­a
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