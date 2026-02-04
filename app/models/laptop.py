# -*- coding: utf-8 -*-
# ============================================
# MODELOS DE INVENTARIO DE LAPTOPS v2.0
# ============================================
# Implementación basada en mejores prácticas de PIM
# (Product Information Management)
# 
# Características principales:
# - Separación entre datos de Icecat y datos manuales
# - Tracking de origen de cada campo (data_source)
# - Capacidad de enriquecer/modificar datos importados
# - Soporte para múltiples fuentes de datos
# - Galería de imágenes mejorada con URLs externas
# - Especificaciones técnicas detalladas

from app import db
from app.models.mixins import TimestampMixin, CatalogMixin
from datetime import datetime, date
from enum import Enum
import json


# ===== ENUMS PARA DATA SOURCE =====

class DataSource(str, Enum):
    """Fuente de origen de los datos"""
    MANUAL = 'manual'           # Ingresado manualmente por el usuario
    ICECAT = 'icecat'           # Importado desde Icecat
    ICECAT_MODIFIED = 'icecat_modified'  # Importado de Icecat y modificado
    API_IMPORT = 'api_import'   # Importado desde otra API
    BULK_IMPORT = 'bulk_import' # Importación masiva (CSV, Excel)


class ProductCondition(str, Enum):
    """Condición del producto"""
    NEW = 'new'
    USED = 'used'
    REFURBISHED = 'refurbished'
    OPEN_BOX = 'open_box'


class ProductCategory(str, Enum):
    """Categoría del producto"""
    LAPTOP = 'laptop'
    WORKSTATION = 'workstation'
    GAMING = 'gaming'
    ULTRABOOK = 'ultrabook'
    CHROMEBOOK = 'chromebook'
    TWO_IN_ONE = '2in1'


# ===== MODELOS DE CATÁLOGO (usan CatalogMixin) =====

class Brand(CatalogMixin, db.Model):
    """
    Marcas de laptops (Dell, HP, Lenovo, etc.)
    Usa CatalogMixin: id, name, is_active, timestamps, métodos get_active() y get_or_create()
    """
    __tablename__ = 'brands'
    
    # Campos adicionales para Icecat
    icecat_brand_id = db.Column(db.String(50), nullable=True, index=True)
    logo_url = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(200), nullable=True)

    # Relaciones
    laptops = db.relationship('Laptop', backref='brand', lazy='dynamic')
    
    @classmethod
    def get_or_create_from_icecat(cls, brand_name, icecat_brand_id=None, logo_url=None):
        """Obtiene o crea una marca desde datos de Icecat"""
        brand = cls.query.filter(
            db.func.lower(cls.name) == db.func.lower(brand_name)
        ).first()
        
        if not brand:
            brand = cls(
                name=brand_name,
                icecat_brand_id=icecat_brand_id,
                logo_url=logo_url,
                is_active=True
            )
            db.session.add(brand)
        elif icecat_brand_id and not brand.icecat_brand_id:
            brand.icecat_brand_id = icecat_brand_id
            if logo_url:
                brand.logo_url = logo_url
        
        return brand


class LaptopModel(CatalogMixin, db.Model):
    """
    Modelos de laptops (Inspiron 15, ThinkPad X1, etc.)
    """
    __tablename__ = 'laptop_models'

    # Campo adicional: referencia a marca (opcional)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)
    
    # Campos de Icecat
    icecat_product_family = db.Column(db.String(100), nullable=True)
    
    # Relaciones
    laptops = db.relationship('Laptop', backref='model', lazy='dynamic')


class Processor(CatalogMixin, db.Model):
    """
    Procesadores (Intel Core i7-12700H, AMD Ryzen 7 5700U, etc.)
    Incluye especificaciones técnicas detalladas
    """
    __tablename__ = 'processors'
    
    # Especificaciones técnicas
    manufacturer = db.Column(db.String(50), nullable=True)  # Intel, AMD, Apple
    family = db.Column(db.String(50), nullable=True)        # Core i7, Ryzen 7
    model_number = db.Column(db.String(50), nullable=True)  # 12700H, 5700U
    cores = db.Column(db.Integer, nullable=True)
    threads = db.Column(db.Integer, nullable=True)
    base_clock_ghz = db.Column(db.Numeric(4, 2), nullable=True)
    boost_clock_ghz = db.Column(db.Numeric(4, 2), nullable=True)
    cache_mb = db.Column(db.Integer, nullable=True)
    tdp_watts = db.Column(db.Integer, nullable=True)
    generation = db.Column(db.String(20), nullable=True)    # 12th Gen, Zen 3
    architecture = db.Column(db.String(50), nullable=True)  # Alder Lake, Zen 3

    # Relaciones
    laptops = db.relationship('Laptop', backref='processor', lazy='dynamic')
    
    @classmethod
    def get_or_create_from_specs(cls, name, **specs):
        """Obtiene o crea un procesador desde especificaciones"""
        processor = cls.query.filter(
            db.func.lower(cls.name) == db.func.lower(name)
        ).first()
        
        if not processor:
            processor = cls(name=name, is_active=True, **specs)
            db.session.add(processor)
        else:
            # Actualizar specs si están vacíos
            for key, value in specs.items():
                if hasattr(processor, key) and getattr(processor, key) is None:
                    setattr(processor, key, value)
        
        return processor


class OperatingSystem(CatalogMixin, db.Model):
    """
    Sistemas Operativos (Windows 11 Pro, macOS, Ubuntu, etc.)
    """
    __tablename__ = 'operating_systems'
    
    # Campos adicionales
    version = db.Column(db.String(50), nullable=True)
    edition = db.Column(db.String(50), nullable=True)  # Home, Pro, Enterprise
    architecture = db.Column(db.String(10), nullable=True)  # 64-bit, ARM64

    # Relaciones
    laptops = db.relationship('Laptop', backref='operating_system', lazy='dynamic')


class Screen(CatalogMixin, db.Model):
    """
    Pantallas con especificaciones detalladas
    """
    __tablename__ = 'screens'
    
    # Especificaciones técnicas
    size_inches = db.Column(db.Numeric(4, 1), nullable=True)
    resolution_width = db.Column(db.Integer, nullable=True)
    resolution_height = db.Column(db.Integer, nullable=True)
    resolution_name = db.Column(db.String(20), nullable=True)  # FHD, QHD, 4K
    panel_type = db.Column(db.String(30), nullable=True)  # IPS, OLED, VA, TN
    refresh_rate_hz = db.Column(db.Integer, nullable=True)
    brightness_nits = db.Column(db.Integer, nullable=True)
    color_gamut = db.Column(db.String(50), nullable=True)  # 100% sRGB, 72% NTSC
    touch_enabled = db.Column(db.Boolean, default=False, nullable=True)
    hdr_support = db.Column(db.Boolean, default=False, nullable=True)
    aspect_ratio = db.Column(db.String(10), nullable=True)  # 16:9, 16:10, 3:2

    # Relaciones
    laptops = db.relationship('Laptop', backref='screen', lazy='dynamic')


class GraphicsCard(CatalogMixin, db.Model):
    """
    Tarjetas Gráficas con especificaciones detalladas
    """
    __tablename__ = 'graphics_cards'
    
    # Especificaciones técnicas
    manufacturer = db.Column(db.String(50), nullable=True)  # NVIDIA, AMD, Intel
    is_integrated = db.Column(db.Boolean, default=False, nullable=True)
    vram_gb = db.Column(db.Integer, nullable=True)
    vram_type = db.Column(db.String(20), nullable=True)  # GDDR6, GDDR5
    max_tdp_watts = db.Column(db.Integer, nullable=True)
    cuda_cores = db.Column(db.Integer, nullable=True)  # Para NVIDIA
    ray_tracing = db.Column(db.Boolean, default=False, nullable=True)

    # Relaciones
    laptops = db.relationship('Laptop', backref='graphics_card', lazy='dynamic')


class Storage(CatalogMixin, db.Model):
    """
    Tipos de Almacenamiento con especificaciones
    """
    __tablename__ = 'storage'
    
    # Especificaciones técnicas
    capacity_gb = db.Column(db.Integer, nullable=True)
    storage_type = db.Column(db.String(20), nullable=True)  # SSD, HDD, eMMC
    interface = db.Column(db.String(30), nullable=True)  # NVMe, SATA, PCIe 4.0
    form_factor = db.Column(db.String(20), nullable=True)  # M.2 2280, 2.5"
    read_speed_mbps = db.Column(db.Integer, nullable=True)
    write_speed_mbps = db.Column(db.Integer, nullable=True)

    # Relaciones
    laptops = db.relationship('Laptop', backref='storage', lazy='dynamic')


class Ram(CatalogMixin, db.Model):
    """
    Tipos de RAM con especificaciones
    """
    __tablename__ = 'ram'
    
    # Especificaciones técnicas
    capacity_gb = db.Column(db.Integer, nullable=True)
    ram_type = db.Column(db.String(20), nullable=True)  # DDR4, DDR5, LPDDR5
    speed_mhz = db.Column(db.Integer, nullable=True)
    channels = db.Column(db.Integer, nullable=True)  # 1, 2 (dual-channel)
    is_soldered = db.Column(db.Boolean, nullable=True)  # ¿Soldada o reemplazable?

    # Relaciones
    laptops = db.relationship('Laptop', backref='ram', lazy='dynamic')


class Store(CatalogMixin, db.Model):
    """
    Tiendas (Tienda Principal, Sucursal Centro, etc.)
    """
    __tablename__ = 'stores'

    # Campos adicionales específicos de tiendas
    address = db.Column(db.String(300))
    phone = db.Column(db.String(20))

    # Relaciones
    laptops = db.relationship('Laptop', backref='store', lazy='dynamic')
    locations = db.relationship('Location', backref='store_ref', lazy='dynamic')


class Location(CatalogMixin, db.Model):
    """
    Ubicaciones dentro de tiendas (Estante A-1, Vitrina 3, Bodega, etc.)
    """
    __tablename__ = 'locations'

    # Relación con tienda (opcional)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)

    # Relaciones
    laptops = db.relationship('Laptop', backref='location', lazy='dynamic')


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
    notes = db.Column(db.Text)

    # Relaciones
    laptops = db.relationship('Laptop', backref='supplier', lazy='dynamic')


# ===== MODELO DE DATOS DE ICECAT =====

class IcecatProductData(TimestampMixin, db.Model):
    """
    Almacena los datos originales importados de Icecat.
    Esta es la "fuente de verdad" para los datos de Icecat.
    
    Esto permite:
    - Mantener los datos originales de Icecat como referencia
    - Detectar cambios cuando el usuario modifica los datos
    - Actualizar datos de Icecat sin perder personalizaciones
    - Auditar qué datos fueron modificados
    """
    __tablename__ = 'icecat_product_data'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # ===== IDENTIFICADORES DE ICECAT =====
    icecat_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    icecat_gtin = db.Column(db.String(20), index=True)  # EAN/UPC
    product_code = db.Column(db.String(100), index=True)  # Part Number
    
    # ===== INFORMACIÓN BÁSICA =====
    brand_name = db.Column(db.String(100), nullable=False)
    brand_id_icecat = db.Column(db.String(50))
    product_name = db.Column(db.String(300))
    title = db.Column(db.String(500))
    category_name = db.Column(db.String(100))
    category_id_icecat = db.Column(db.String(50))
    
    # ===== DESCRIPCIONES =====
    short_description = db.Column(db.Text)
    long_description_html = db.Column(db.Text)
    summary_short = db.Column(db.Text)
    summary_long = db.Column(db.Text)
    
    # ===== ESPECIFICACIONES (JSON estructurado) =====
    # Almacena todas las especificaciones de Icecat
    specifications_json = db.Column(db.JSON, default=dict)
    feature_groups_json = db.Column(db.JSON, default=dict)
    
    # ===== CAMPOS EXTRAÍDOS (para facilitar búsqueda) =====
    extracted_processor = db.Column(db.String(200))
    extracted_ram = db.Column(db.String(100))
    extracted_storage = db.Column(db.String(100))
    extracted_screen = db.Column(db.String(100))
    extracted_graphics = db.Column(db.String(200))
    extracted_os = db.Column(db.String(100))
    extracted_weight_kg = db.Column(db.Numeric(5, 2))
    extracted_battery_wh = db.Column(db.Numeric(6, 2))
    extracted_dimensions = db.Column(db.String(100))  # "35.96 x 24.66 x 1.86 cm"
    
    # ===== IMÁGENES (JSON array) =====
    images_json = db.Column(db.JSON, default=list)  # Lista de URLs de imágenes
    main_image_url = db.Column(db.String(500))
    
    # ===== INFORMACIÓN ADICIONAL =====
    warranty_info = db.Column(db.Text)
    release_date = db.Column(db.String(50))
    ean_codes = db.Column(db.JSON, default=list)  # Lista de todos los EAN/UPC
    
    # ===== METADATOS =====
    language = db.Column(db.String(5), default='ES')
    last_icecat_update = db.Column(db.DateTime)
    raw_response_json = db.Column(db.JSON)  # Respuesta completa de Icecat
    
    # ===== RELACIÓN CON LAPTOPS =====
    laptops = db.relationship('Laptop', backref='icecat_data', lazy='dynamic')
    
    def to_dict(self):
        """Serializa los datos de Icecat a diccionario"""
        return {
            'id': self.id,
            'icecat_id': self.icecat_id,
            'icecat_gtin': self.icecat_gtin,
            'product_code': self.product_code,
            'brand_name': self.brand_name,
            'product_name': self.product_name,
            'title': self.title,
            'category_name': self.category_name,
            'short_description': self.short_description,
            'long_description_html': self.long_description_html,
            'specifications': self.specifications_json,
            'feature_groups': self.feature_groups_json,
            'extracted': {
                'processor': self.extracted_processor,
                'ram': self.extracted_ram,
                'storage': self.extracted_storage,
                'screen': self.extracted_screen,
                'graphics': self.extracted_graphics,
                'os': self.extracted_os,
                'weight_kg': float(self.extracted_weight_kg) if self.extracted_weight_kg else None,
                'battery_wh': float(self.extracted_battery_wh) if self.extracted_battery_wh else None,
                'dimensions': self.extracted_dimensions,
            },
            'images': self.images_json,
            'main_image_url': self.main_image_url,
            'warranty_info': self.warranty_info,
            'release_date': self.release_date,
            'language': self.language,
            'last_icecat_update': self.last_icecat_update.isoformat() if self.last_icecat_update else None,
        }
    
    @classmethod
    def create_from_icecat_product(cls, icecat_product):
        """
        Crea un registro desde un IcecatProduct parseado.
        
        Args:
            icecat_product: Objeto IcecatProduct del servicio de Icecat
            
        Returns:
            Instancia de IcecatProductData
        """
        # Preparar imágenes
        images = []
        if icecat_product.main_image:
            images.append({
                'url': icecat_product.main_image.url,
                'thumb_url': icecat_product.main_image.thumb_url,
                'is_main': True,
                'position': 0
            })
        
        for img in icecat_product.gallery:
            images.append({
                'url': img.url,
                'thumb_url': img.thumb_url,
                'is_main': img.is_main,
                'position': img.position
            })
        
        # Preparar especificaciones
        specs = {}
        for feature in icecat_product.features:
            specs[feature.name] = {
                'value': feature.value,
                'group': feature.group,
                'measure': feature.measure
            }
        
        instance = cls(
            icecat_id=icecat_product.icecat_id,
            icecat_gtin=icecat_product.gtin,
            product_code=icecat_product.product_code,
            brand_name=icecat_product.brand,
            brand_id_icecat=icecat_product.brand_id,
            product_name=icecat_product.product_name,
            title=icecat_product.title,
            category_name=icecat_product.category,
            category_id_icecat=icecat_product.category_id,
            short_description=icecat_product.short_description or icecat_product.summary_short,
            long_description_html=icecat_product.long_description,
            summary_short=icecat_product.summary_short,
            summary_long=icecat_product.summary_long,
            specifications_json=specs,
            feature_groups_json=icecat_product.feature_groups,
            images_json=images,
            main_image_url=icecat_product.main_image.url if icecat_product.main_image else None,
            warranty_info=icecat_product.warranty_info,
            release_date=icecat_product.release_date,
            ean_codes=icecat_product.gtins,
            last_icecat_update=datetime.utcnow(),
            raw_response_json=icecat_product.raw_data
        )
        
        # Extraer campos específicos
        instance._extract_specs_from_features(icecat_product.features)
        
        return instance
    
    def _extract_specs_from_features(self, features):
        """Extrae especificaciones relevantes de la lista de features"""
        # Mapeo de nombres de características a campos
        spec_mapping = {
            'processor': ['procesador', 'processor', 'cpu', 'tipo de procesador', 
                         'familia del procesador', 'modelo del procesador'],
            'ram': ['memoria interna', 'ram', 'memoria ram', 'internal memory',
                   'memoria de trabajo', 'capacidad de ram'],
            'storage': ['capacidad total de almacenaje', 'almacenamiento', 
                       'storage', 'ssd', 'hdd', 'disco duro', 'capacidad ssd'],
            'screen': ['diagonal de la pantalla', 'pantalla', 'screen size', 
                      'display', 'tamaño de pantalla'],
            'graphics': ['tarjeta gráfica', 'gpu', 'graphics', 
                        'modelo de adaptador gráfico discreto', 'adaptador gráfico'],
            'os': ['sistema operativo', 'operating system', 'os instalado'],
            'weight': ['peso', 'weight'],
            'battery': ['capacidad de batería', 'battery', 'batería'],
            'dimensions': ['dimensiones', 'dimensions', 'ancho x profundidad x altura']
        }
        
        for feature in features:
            name_lower = feature.name.lower()
            
            for field, keys in spec_mapping.items():
                for key in keys:
                    if key in name_lower:
                        if field == 'processor':
                            self.extracted_processor = feature.value
                        elif field == 'ram':
                            self.extracted_ram = feature.value
                        elif field == 'storage':
                            self.extracted_storage = feature.value
                        elif field == 'screen':
                            self.extracted_screen = feature.value
                        elif field == 'graphics':
                            self.extracted_graphics = feature.value
                        elif field == 'os':
                            self.extracted_os = feature.value
                        elif field == 'weight':
                            try:
                                # Intentar extraer el peso numérico
                                weight_str = feature.value.replace('kg', '').replace(',', '.').strip()
                                self.extracted_weight_kg = float(weight_str)
                            except (ValueError, AttributeError):
                                pass
                        elif field == 'battery':
                            try:
                                battery_str = feature.value.replace('Wh', '').replace(',', '.').strip()
                                self.extracted_battery_wh = float(battery_str)
                            except (ValueError, AttributeError):
                                pass
                        elif field == 'dimensions':
                            self.extracted_dimensions = feature.value
                        break
    
    def __repr__(self):
        return f'<IcecatProductData {self.icecat_id} - {self.title}>'


# ===== MODELO PRINCIPAL: LAPTOP =====

class Laptop(TimestampMixin, db.Model):
    """
    Modelo principal de inventario de laptops
    
    Sigue el patrón PIM (Product Information Management):
    - Puede tener datos de Icecat como base (icecat_data_id)
    - Permite modificar/enriquecer los datos importados
    - Rastrea el origen de cada campo (data_source)
    - Permite entrada completamente manual
    
    Flujo de datos:
    1. Usuario busca en Icecat → Se crea IcecatProductData
    2. Datos de Icecat se copian a Laptop como valores iniciales
    3. Usuario puede ajustar cualquier campo
    4. Se guarda con data_source indicando origen
    
    O alternativamente:
    1. Usuario crea Laptop manualmente sin Icecat
    2. Todos los campos son data_source='manual'
    """
    __tablename__ = 'laptops'

    # ===== 1. IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # ===== 2. REFERENCIA A ICECAT (opcional) =====
    icecat_data_id = db.Column(
        db.Integer, 
        db.ForeignKey('icecat_product_data.id'), 
        nullable=True,
        index=True
    )
    
    # Identificadores de producto externo
    gtin = db.Column(db.String(20), nullable=True, index=True)  # EAN/UPC
    mpn = db.Column(db.String(100), nullable=True, index=True)  # Manufacturer Part Number
    upc = db.Column(db.String(20), nullable=True)  # Universal Product Code
    
    # ===== 3. TRACKING DE ORIGEN DE DATOS =====
    data_source = db.Column(
        db.String(30), 
        default=DataSource.MANUAL.value,
        nullable=False
    )
    # JSON que registra qué campos fueron modificados del original de Icecat
    modified_fields_json = db.Column(db.JSON, default=dict)
    
    # ===== 4. MARKETING Y WEB (SEO) =====
    display_name = db.Column(db.String(300), nullable=False)
    short_description = db.Column(db.String(500), nullable=True)
    long_description_html = db.Column(db.Text, nullable=True)
    
    # Publicación
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    
    # SEO
    seo_title = db.Column(db.String(70), nullable=True)
    seo_description = db.Column(db.String(160), nullable=True)
    seo_keywords = db.Column(db.String(255), nullable=True)

    # ===== 5. RELACIONES CON CATÁLOGOS =====
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

    # ===== 6. DETALLES TÉCNICOS ESPECÍFICOS =====
    # Características adicionales no en catálogo
    npu = db.Column(db.Boolean, default=False, nullable=False)  # Tiene NPU (AI)
    storage_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    ram_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    keyboard_layout = db.Column(db.String(20), default='US', nullable=False)
    keyboard_backlit = db.Column(db.Boolean, default=True, nullable=True)
    fingerprint_reader = db.Column(db.Boolean, default=False, nullable=True)
    ir_camera = db.Column(db.Boolean, default=False, nullable=True)  # Windows Hello
    
    # Puertos y conectividad (JSON para flexibilidad)
    connectivity_ports = db.Column(db.JSON, default=dict, nullable=True)
    wireless_connectivity = db.Column(db.JSON, default=dict, nullable=True)  # WiFi 6, BT 5.2
    
    # Dimensiones físicas
    weight_kg = db.Column(db.Numeric(5, 2), nullable=True)
    width_mm = db.Column(db.Numeric(6, 2), nullable=True)
    depth_mm = db.Column(db.Numeric(6, 2), nullable=True)
    height_mm = db.Column(db.Numeric(5, 2), nullable=True)
    
    # Batería
    battery_wh = db.Column(db.Numeric(6, 2), nullable=True)
    battery_cells = db.Column(db.Integer, nullable=True)
    
    # Color y materiales
    color = db.Column(db.String(50), nullable=True)
    chassis_material = db.Column(db.String(50), nullable=True)  # Aluminum, Plastic

    # ===== 7. ESTADO Y CATEGORÍA =====
    category = db.Column(
        db.String(20), 
        nullable=False, 
        default=ProductCategory.LAPTOP.value, 
        index=True
    )
    condition = db.Column(
        db.String(20), 
        nullable=False, 
        default=ProductCondition.USED.value, 
        index=True
    )
    
    # Información de garantía
    warranty_months = db.Column(db.Integer, nullable=True)
    warranty_type = db.Column(db.String(50), nullable=True)  # Manufacturer, Store

    # ===== 8. FINANCIEROS =====
    purchase_cost = db.Column(db.Numeric(12, 2), nullable=False)
    sale_price = db.Column(db.Numeric(12, 2), nullable=False)
    discount_price = db.Column(db.Numeric(12, 2), nullable=True)
    tax_percent = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)
    
    # MSRP (Precio sugerido del fabricante)
    msrp = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Moneda
    currency = db.Column(db.String(3), default='DOP', nullable=False)

    # ===== 9. INVENTARIO =====
    quantity = db.Column(db.Integer, default=1, nullable=False)
    reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
    min_alert = db.Column(db.Integer, default=1, nullable=False)

    # ===== 10. TIMESTAMPS =====
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    sale_date = db.Column(db.Date, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    
    # Fecha de último sync con Icecat
    last_icecat_sync = db.Column(db.DateTime, nullable=True)

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
    def is_from_icecat(self):
        """Indica si el producto tiene datos de Icecat"""
        return self.icecat_data_id is not None
    
    @property
    def has_modifications(self):
        """Indica si el producto tiene modificaciones sobre los datos de Icecat"""
        return bool(self.modified_fields_json)
    
    @property
    def cover_image(self):
        """Obtiene la imagen de portada del producto"""
        cover = LaptopImage.query.filter_by(
            laptop_id=self.id, 
            is_cover=True
        ).first()
        
        if cover:
            return cover
        
        # Si no hay cover, retornar la primera imagen
        return LaptopImage.query.filter_by(
            laptop_id=self.id
        ).order_by(LaptopImage.position).first()

    # ===== MÉTODOS DE TRACKING =====
    
    def mark_field_modified(self, field_name, original_value=None):
        """
        Marca un campo como modificado del original de Icecat.
        
        Args:
            field_name: Nombre del campo modificado
            original_value: Valor original de Icecat (opcional)
        """
        if self.modified_fields_json is None:
            self.modified_fields_json = {}
        
        self.modified_fields_json[field_name] = {
            'modified_at': datetime.utcnow().isoformat(),
            'original_value': original_value
        }
        
        # Actualizar data_source si era de Icecat
        if self.data_source == DataSource.ICECAT.value:
            self.data_source = DataSource.ICECAT_MODIFIED.value
    
    def get_original_value(self, field_name):
        """Obtiene el valor original de Icecat para un campo"""
        if self.modified_fields_json and field_name in self.modified_fields_json:
            return self.modified_fields_json[field_name].get('original_value')
        return None
    
    def reset_field_to_original(self, field_name):
        """Resetea un campo al valor original de Icecat"""
        original = self.get_original_value(field_name)
        if original is not None:
            setattr(self, field_name, original)
            del self.modified_fields_json[field_name]

    # ===== MÉTODOS DE SERIALIZACIÓN =====

    def to_dict(self, include_relationships=True, include_icecat=False):
        """
        Serializa el objeto a diccionario (para JSON)

        Args:
            include_relationships: Si incluir datos de relaciones
            include_icecat: Si incluir datos originales de Icecat

        Returns:
            dict con todos los datos del laptop
        """
        data = {
            # Identificadores
            'id': self.id,
            'sku': self.sku,
            'slug': self.slug,
            'gtin': self.gtin,
            'mpn': self.mpn,
            
            # Origen de datos
            'data_source': self.data_source,
            'is_from_icecat': self.is_from_icecat,
            'has_modifications': self.has_modifications,
            'modified_fields': list(self.modified_fields_json.keys()) if self.modified_fields_json else [],

            # Marketing y SEO
            'display_name': self.display_name,
            'short_description': self.short_description,
            'long_description_html': self.long_description_html,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,

            # Detalles técnicos
            'npu': self.npu,
            'storage_upgradeable': self.storage_upgradeable,
            'ram_upgradeable': self.ram_upgradeable,
            'keyboard_layout': self.keyboard_layout,
            'keyboard_backlit': self.keyboard_backlit,
            'fingerprint_reader': self.fingerprint_reader,
            'ir_camera': self.ir_camera,
            'connectivity_ports': self.connectivity_ports,
            'wireless_connectivity': self.wireless_connectivity,
            
            # Dimensiones
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'dimensions': {
                'width_mm': float(self.width_mm) if self.width_mm else None,
                'depth_mm': float(self.depth_mm) if self.depth_mm else None,
                'height_mm': float(self.height_mm) if self.height_mm else None,
            },
            
            # Batería
            'battery_wh': float(self.battery_wh) if self.battery_wh else None,
            'battery_cells': self.battery_cells,
            
            # Estética
            'color': self.color,
            'chassis_material': self.chassis_material,

            # Estado y categoría
            'category': self.category,
            'condition': self.condition,
            'warranty_months': self.warranty_months,

            # Financieros
            'purchase_cost': float(self.purchase_cost) if self.purchase_cost else 0,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'discount_price': float(self.discount_price) if self.discount_price else None,
            'tax_percent': float(self.tax_percent) if self.tax_percent else 0,
            'msrp': float(self.msrp) if self.msrp else None,
            'currency': self.currency,
            'effective_price': float(self.effective_price) if self.effective_price else 0,
            'gross_profit': self.gross_profit,
            'margin_percentage': self.margin_percentage,
            'price_with_tax': self.price_with_tax,

            # Inventario
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'min_alert': self.min_alert,
            'is_low_stock': self.is_low_stock,

            # Timestamps
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_icecat_sync': self.last_icecat_sync.isoformat() if self.last_icecat_sync else None,

            # Notas
            'internal_notes': self.internal_notes
        }

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
                'cover_image': self.cover_image.to_dict() if self.cover_image else None
            })
        
        # Incluir datos originales de Icecat si se solicita
        if include_icecat and self.icecat_data:
            data['icecat_original'] = self.icecat_data.to_dict()

        return data

    def __repr__(self):
        """Representación en string del objeto"""
        source = f" [{self.data_source}]" if self.data_source != DataSource.MANUAL.value else ""
        return f'<Laptop {self.sku} - {self.display_name}{source}>'

    # ===== ÍNDICES COMPUESTOS =====
    __table_args__ = (
        db.Index('idx_laptop_brand_category', 'brand_id', 'category'),
        db.Index('idx_laptop_published_featured', 'is_published', 'is_featured'),
        db.Index('idx_laptop_entry_date', 'entry_date'),
        db.Index('idx_laptop_store_location', 'store_id', 'location_id'),
        db.Index('idx_laptop_gtin', 'gtin'),
        db.Index('idx_laptop_data_source', 'data_source'),
    )


# ===== MODELO DE IMÁGENES MEJORADO =====

class LaptopImage(TimestampMixin, db.Model):
    """
    Galería de imágenes vinculada a una Laptop específica.
    
    Soporta:
    - Imágenes locales (subidas por el usuario)
    - Imágenes remotas (URLs de Icecat u otras fuentes)
    - Múltiples tamaños (thumb, medium, high)
    - Tracking de origen
    """
    __tablename__ = 'laptop_images'

    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(
        db.Integer, 
        db.ForeignKey('laptops.id', ondelete='CASCADE'), 
        nullable=False
    )
    
    # ===== RUTAS/URLs DE IMAGEN =====
    # Para imágenes locales
    image_path = db.Column(db.String(500), nullable=True)
    
    # Para imágenes remotas (Icecat)
    image_url = db.Column(db.String(500), nullable=True)  # URL alta resolución
    thumb_url = db.Column(db.String(500), nullable=True)  # Thumbnail
    medium_url = db.Column(db.String(500), nullable=True)  # Tamaño medio
    
    # Indica si la imagen es local o remota
    is_remote = db.Column(db.Boolean, default=False, nullable=False)
    
    # ===== METADATOS =====
    position = db.Column(db.Integer, default=0, nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)  # SEO alt text
    is_cover = db.Column(db.Boolean, default=False, nullable=False)
    ordering = db.Column(db.Integer, default=0, nullable=False)
    
    # Dimensiones originales
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    
    # Origen de la imagen
    source = db.Column(db.String(50), default='manual', nullable=False)  # manual, icecat, import
    source_url = db.Column(db.String(500), nullable=True)  # URL original si fue descargada
    
    # Estado de descarga (para imágenes de Icecat)
    is_downloaded = db.Column(db.Boolean, default=False, nullable=False)
    download_error = db.Column(db.String(255), nullable=True)

    # Relación
    laptop = db.relationship(
        'Laptop', 
        backref=db.backref('images', lazy='select', cascade='all, delete-orphan')
    )
    
    @property
    def display_url(self):
        """
        Retorna la URL a mostrar.
        Prioriza imagen local si existe, sino usa URL remota.
        """
        if self.image_path:
            return self.image_path
        return self.image_url
    
    @property
    def thumbnail_url(self):
        """Retorna URL del thumbnail"""
        if self.image_path:
            # Para imágenes locales, generar ruta de thumbnail
            # Esto asume que los thumbnails se generan con sufijo _thumb
            base, ext = self.image_path.rsplit('.', 1) if '.' in self.image_path else (self.image_path, '')
            return f"{base}_thumb.{ext}" if ext else self.image_path
        return self.thumb_url or self.image_url

    def to_dict(self):
        """Serializa la imagen a diccionario"""
        return {
            'id': self.id,
            'laptop_id': self.laptop_id,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'thumb_url': self.thumb_url,
            'medium_url': self.medium_url,
            'display_url': self.display_url,
            'thumbnail_url': self.thumbnail_url,
            'is_remote': self.is_remote,
            'position': self.position,
            'alt_text': self.alt_text,
            'is_cover': self.is_cover,
            'ordering': self.ordering,
            'width': self.width,
            'height': self.height,
            'source': self.source,
            'is_downloaded': self.is_downloaded,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        source_info = f" (remote: {self.source})" if self.is_remote else " (local)"
        return f'<LaptopImage {self.id} - Laptop {self.laptop_id}{source_info}>'

    __table_args__ = (
        db.Index('idx_laptop_image_laptop_cover', 'laptop_id', 'is_cover'),
        db.Index('idx_laptop_image_position', 'laptop_id', 'position'),
    )


# ===== MODELO DE ESPECIFICACIONES TÉCNICAS =====

class LaptopTechnicalSpecs(TimestampMixin, db.Model):
    """
    Almacena especificaciones técnicas adicionales del laptop.
    
    Permite almacenar cualquier especificación de Icecat
    sin necesidad de modificar el esquema de la base de datos.
    
    Útil para:
    - Especificaciones que varían entre modelos
    - Datos de Icecat que no tienen campo específico
    - Información técnica detallada
    """
    __tablename__ = 'laptop_technical_specs'
    
    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(
        db.Integer, 
        db.ForeignKey('laptops.id', ondelete='CASCADE'), 
        nullable=False
    )
    
    # Categoría/grupo de la especificación
    spec_group = db.Column(db.String(100), nullable=False)  # "Pantalla", "Procesador", etc.
    
    # Nombre y valor de la especificación
    spec_name = db.Column(db.String(200), nullable=False)
    spec_value = db.Column(db.Text, nullable=False)
    
    # Unidad de medida (opcional)
    unit = db.Column(db.String(30), nullable=True)
    
    # Orden de visualización dentro del grupo
    display_order = db.Column(db.Integer, default=0)
    
    # Origen del dato
    source = db.Column(db.String(50), default='manual')  # manual, icecat
    
    # Relación
    laptop = db.relationship(
        'Laptop', 
        backref=db.backref('technical_specs', lazy='dynamic', cascade='all, delete-orphan')
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'spec_group': self.spec_group,
            'spec_name': self.spec_name,
            'spec_value': self.spec_value,
            'unit': self.unit,
            'source': self.source
        }
    
    def __repr__(self):
        return f'<TechnicalSpec {self.spec_name}: {self.spec_value}>'
    
    __table_args__ = (
        db.Index('idx_tech_spec_laptop_group', 'laptop_id', 'spec_group'),
    )
