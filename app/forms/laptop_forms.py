# -*- coding: utf-8 -*-
# =========================================
# FORMULARIOS DE INVENTARIO DE LAPTOPS v2.0
# =========================================
# Formularios mejorados con soporte para:
# - Importación desde Icecat
# - Entrada manual completa
# - Edición de datos importados
# - Validación avanzada

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField, SelectField, DecimalField, IntegerField,
    TextAreaField, BooleanField, SubmitField, HiddenField,
    DateField, SelectMultipleField, FieldList, FormField,
    FloatField
)
from wtforms.validators import (
    DataRequired, Optional, Length, NumberRange, 
    ValidationError, URL, Regexp, Email
)
from decimal import Decimal


# ===== OPCIONES CONSTANTES =====

CONNECTIVITY_PORTS_CHOICES = [
    ('usb_a_2', 'USB-A 2.0'),
    ('usb_a_3', 'USB-A 3.0'),
    ('usb_a_31', 'USB-A 3.1'),
    ('usb_a_32', 'USB-A 3.2'),
    ('usb_c', 'USB-C'),
    ('usb_c_thunderbolt3', 'USB-C Thunderbolt 3'),
    ('usb_c_thunderbolt4', 'USB-C Thunderbolt 4'),
    ('usb4', 'USB4'),
    ('hdmi', 'HDMI'),
    ('hdmi_20', 'HDMI 2.0'),
    ('hdmi_21', 'HDMI 2.1'),
    ('displayport', 'DisplayPort'),
    ('mini_displayport', 'Mini DisplayPort'),
    ('ethernet', 'Ethernet RJ-45'),
    ('ethernet_25g', 'Ethernet 2.5G'),
    ('sd_card', 'Lector SD'),
    ('microsd', 'Lector MicroSD'),
    ('audio_jack', 'Jack Audio 3.5mm'),
    ('vga', 'VGA'),
    ('dvi', 'DVI'),
    ('smart_card', 'Smart Card Reader'),
    ('sim_card', 'SIM Card Slot'),
]

WIRELESS_CONNECTIVITY_CHOICES = [
    ('wifi_5', 'WiFi 5 (802.11ac)'),
    ('wifi_6', 'WiFi 6 (802.11ax)'),
    ('wifi_6e', 'WiFi 6E'),
    ('wifi_7', 'WiFi 7 (802.11be)'),
    ('bt_50', 'Bluetooth 5.0'),
    ('bt_51', 'Bluetooth 5.1'),
    ('bt_52', 'Bluetooth 5.2'),
    ('bt_53', 'Bluetooth 5.3'),
    ('nfc', 'NFC'),
    ('lte', 'LTE/4G'),
    ('5g', '5G'),
]

KEYBOARD_LAYOUT_CHOICES = [
    ('US', 'US - Inglés'),
    ('UK', 'UK - Inglés Británico'),
    ('ES', 'ES - Español España'),
    ('LATAM', 'LATAM - Español Latinoamérica'),
    ('DE', 'DE - Alemán'),
    ('FR', 'FR - Francés'),
    ('IT', 'IT - Italiano'),
    ('PT', 'PT - Portugués'),
    ('BR', 'BR - Portugués Brasil'),
    ('JP', 'JP - Japonés'),
    ('KR', 'KR - Coreano'),
    ('CN', 'CN - Chino'),
]

CATEGORY_CHOICES = [
    ('laptop', 'Laptop'),
    ('workstation', 'Workstation'),
    ('gaming', 'Gaming'),
    ('ultrabook', 'Ultrabook'),
    ('chromebook', 'Chromebook'),
    ('2in1', '2-in-1 / Convertible'),
]

CONDITION_CHOICES = [
    ('new', 'Nuevo'),
    ('used', 'Usado'),
    ('refurbished', 'Refurbished'),
    ('open_box', 'Open Box'),
]

CURRENCY_CHOICES = [
    ('DOP', 'Peso Dominicano (DOP)'),
    ('USD', 'Dólar Americano (USD)'),
    ('EUR', 'Euro (EUR)'),
]

WARRANTY_TYPE_CHOICES = [
    ('manufacturer', 'Fabricante'),
    ('store', 'Tienda'),
    ('extended', 'Extendida'),
    ('none', 'Sin Garantía'),
]


# ===== FORMULARIO DE BÚSQUEDA EN ICECAT =====

class QuickSearchForm(FlaskForm):
    """
    Formulario para buscar productos en Icecat.
    Permite buscar por GTIN o por Marca + Código de producto.
    """
    search_type = SelectField(
        'Tipo de Búsqueda',
        choices=[
            ('gtin', 'Código de Barras (EAN/UPC)'),
            ('brand_code', 'Marca + Código de Producto')
        ],
        default='gtin',
        render_kw={'class': 'form-input'}
    )
    
    gtin = StringField(
        'Código GTIN/EAN/UPC',
        validators=[Optional(), Length(min=8, max=20)],
        render_kw={
            'placeholder': 'Escanea o ingresa el código de barras',
            'class': 'form-input font-mono',
            'data-search-type': 'gtin'
        }
    )
    
    brand = StringField(
        'Marca',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Ej: Dell, HP, Lenovo',
            'class': 'form-input',
            'data-search-type': 'brand_code'
        }
    )
    
    product_code = StringField(
        'Código de Producto (Part Number)',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Ej: XPS15-9530, ThinkPad-X1-G11',
            'class': 'form-input',
            'data-search-type': 'brand_code'
        }
    )
    
    language = SelectField(
        'Idioma',
        choices=[
            ('ES', 'Español'),
            ('EN', 'Inglés'),
            ('PT', 'Portugués'),
            ('FR', 'Francés'),
            ('DE', 'Alemán'),
        ],
        default='ES',
        render_kw={'class': 'form-input'}
    )
    
    submit = SubmitField(
        'Buscar en Icecat',
        render_kw={
            'class': 'btn-primary'
        }
    )
    
    def validate(self, extra_validators=None):
        """Validación personalizada según el tipo de búsqueda"""
        if not super().validate(extra_validators):
            return False
        
        if self.search_type.data == 'gtin':
            if not self.gtin.data:
                self.gtin.errors.append('El código GTIN es requerido')
                return False
        elif self.search_type.data == 'brand_code':
            if not self.brand.data:
                self.brand.errors.append('La marca es requerida')
                return False
            if not self.product_code.data:
                self.product_code.errors.append('El código de producto es requerido')
                return False
        
        return True


# ===== FORMULARIO DE SELECCIÓN DE IMÁGENES =====

class ImageSelectionForm(FlaskForm):
    """
    Formulario para seleccionar imágenes de Icecat o subir propias.
    Se usa dentro del formulario principal.
    """
    # Imágenes seleccionadas de Icecat (JSON string con URLs)
    selected_icecat_images = HiddenField('Imágenes de Icecat')
    
    # Imagen principal seleccionada
    cover_image_index = HiddenField('Índice de Imagen Principal', default='0')
    
    # Subida de imágenes propias
    uploaded_images = MultipleFileField(
        'Subir Imágenes',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif', 'avif'], 
                                'Solo imágenes (jpg, png, webp, gif, avif)')],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*',
            'multiple': True
        }
    )


# ===== FORMULARIO PRINCIPAL DE LAPTOP v2.0 =====

class LaptopForm(FlaskForm):
    """
    Formulario principal mejorado para agregar/editar laptops.
    
    Características:
    - Soporta datos pre-poblados de Icecat
    - Permite ajustar cualquier campo antes de guardar
    - Entrada manual completa sin Icecat
    - Validación avanzada de datos financieros
    - Soporte para especificaciones técnicas detalladas
    """
    
    # ===== CAMPOS OCULTOS DE CONTROL =====
    icecat_data_id = HiddenField('ID de Datos Icecat')
    data_source = HiddenField('Fuente de Datos', default='manual')
    modified_fields = HiddenField('Campos Modificados')  # JSON string
    
    # ===== 1. IDENTIFICADORES =====
    sku = StringField(
        'SKU',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'placeholder': 'Se generará automáticamente',
            'class': 'form-input bg-gray-100',
            'readonly': True
        }
    )
    
    slug = StringField(
        'Slug (URL amigable)',
        validators=[
            Optional(),
            Length(max=255),
            Regexp(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', 
                   message='Solo letras minúsculas, números y guiones')
        ],
        render_kw={
            'placeholder': 'Se generará automáticamente',
            'class': 'form-input'
        }
    )
    
    gtin = StringField(
        'GTIN/EAN/UPC',
        validators=[Optional(), Length(max=20)],
        render_kw={
            'placeholder': 'Código de barras del producto',
            'class': 'form-input font-mono'
        }
    )
    
    mpn = StringField(
        'MPN (Part Number)',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Número de parte del fabricante',
            'class': 'form-input'
        }
    )
    
    # ===== 2. MARKETING Y SEO =====
    display_name = StringField(
        'Nombre Comercial',
        validators=[
            DataRequired(message='El nombre comercial es requerido'),
            Length(max=300)
        ],
        render_kw={
            'placeholder': 'Ej: Dell XPS 15 - Intel i7 - 16GB RAM - 512GB SSD',
            'class': 'form-input text-lg font-medium'
        }
    )
    
    short_description = TextAreaField(
        'Descripción Corta',
        validators=[Optional(), Length(max=500)],
        render_kw={
            'placeholder': 'Descripción breve para tarjetas de producto (máx. 500 caracteres)',
            'class': 'form-input',
            'rows': '3'
        }
    )
    
    long_description_html = TextAreaField(
        'Descripción Completa',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Descripción detallada del producto. Soporta HTML.',
            'class': 'form-input',
            'rows': '8'
        }
    )
    
    is_published = BooleanField(
        'Publicar en catálogo web',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    is_featured = BooleanField(
        'Producto destacado',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    seo_title = StringField(
        'Título SEO',
        validators=[Optional(), Length(max=70)],
        render_kw={
            'placeholder': 'Título para buscadores (máx. 70 caracteres)',
            'class': 'form-input'
        }
    )
    
    seo_description = TextAreaField(
        'Meta Descripción SEO',
        validators=[Optional(), Length(max=160)],
        render_kw={
            'placeholder': 'Descripción para buscadores (máx. 160 caracteres)',
            'class': 'form-input',
            'rows': '2'
        }
    )
    
    seo_keywords = StringField(
        'Palabras Clave SEO',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'laptop, dell, xps, gaming (separadas por coma)',
            'class': 'form-input'
        }
    )
    
    # ===== 3. ESPECIFICACIONES PRINCIPALES =====
    # Estos campos se cargan dinámicamente con Select2
    
    brand_id = SelectField(
        'Marca',
        coerce=int,
        validators=[DataRequired(message='La marca es requerida')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea una marca',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/brands'
        }
    )
    
    model_id = SelectField(
        'Modelo',
        coerce=int,
        validators=[DataRequired(message='El modelo es requerido')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea un modelo',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/laptop_models'
        }
    )
    
    processor_id = SelectField(
        'Procesador',
        coerce=int,
        validators=[DataRequired(message='El procesador es requerido')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea un procesador',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/processors'
        }
    )
    
    ram_id = SelectField(
        'Memoria RAM',
        coerce=int,
        validators=[DataRequired(message='La RAM es requerida')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea RAM',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/ram'
        }
    )
    
    storage_id = SelectField(
        'Almacenamiento',
        coerce=int,
        validators=[DataRequired(message='El almacenamiento es requerido')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea almacenamiento',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/storage'
        }
    )
    
    screen_id = SelectField(
        'Pantalla',
        coerce=int,
        validators=[DataRequired(message='La pantalla es requerida')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea pantalla',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/screens'
        }
    )
    
    graphics_card_id = SelectField(
        'Tarjeta Gráfica',
        coerce=int,
        validators=[DataRequired(message='La GPU es requerida')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea GPU',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/graphics_cards'
        }
    )
    
    os_id = SelectField(
        'Sistema Operativo',
        coerce=int,
        validators=[DataRequired(message='El SO es requerido')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona o crea SO',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/operating_systems'
        }
    )
    
    # ===== 4. CARACTERÍSTICAS ADICIONALES =====
    npu = BooleanField(
        'Tiene NPU (AI/ML)',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    storage_upgradeable = BooleanField(
        'Almacenamiento Ampliable',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    ram_upgradeable = BooleanField(
        'RAM Ampliable',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    keyboard_layout = SelectField(
        'Layout de Teclado',
        choices=KEYBOARD_LAYOUT_CHOICES,
        default='US',
        render_kw={'class': 'form-input'}
    )
    
    keyboard_backlit = BooleanField(
        'Teclado Retroiluminado',
        default=True,
        render_kw={'class': 'form-checkbox'}
    )
    
    fingerprint_reader = BooleanField(
        'Lector de Huellas',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    ir_camera = BooleanField(
        'Cámara IR (Windows Hello)',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    connectivity_ports = SelectMultipleField(
        'Puertos de Conectividad',
        choices=CONNECTIVITY_PORTS_CHOICES,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-multiple',
            'data-placeholder': 'Selecciona los puertos disponibles'
        }
    )
    
    wireless_connectivity = SelectMultipleField(
        'Conectividad Inalámbrica',
        choices=WIRELESS_CONNECTIVITY_CHOICES,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-multiple',
            'data-placeholder': 'Selecciona la conectividad'
        }
    )
    
    # ===== 5. DIMENSIONES FÍSICAS =====
    weight_kg = DecimalField(
        'Peso (kg)',
        places=2,
        validators=[Optional(), NumberRange(min=0, max=10)],
        render_kw={
            'placeholder': '1.80',
            'class': 'form-input',
            'step': '0.01',
            'min': '0'
        }
    )
    
    width_mm = DecimalField(
        'Ancho (mm)',
        places=2,
        validators=[Optional(), NumberRange(min=0, max=1000)],
        render_kw={
            'placeholder': '356.0',
            'class': 'form-input',
            'step': '0.1'
        }
    )
    
    depth_mm = DecimalField(
        'Profundidad (mm)',
        places=2,
        validators=[Optional(), NumberRange(min=0, max=1000)],
        render_kw={
            'placeholder': '246.0',
            'class': 'form-input',
            'step': '0.1'
        }
    )
    
    height_mm = DecimalField(
        'Alto (mm)',
        places=2,
        validators=[Optional(), NumberRange(min=0, max=100)],
        render_kw={
            'placeholder': '18.6',
            'class': 'form-input',
            'step': '0.1'
        }
    )
    
    # ===== 6. BATERÍA =====
    battery_wh = DecimalField(
        'Capacidad de Batería (Wh)',
        places=2,
        validators=[Optional(), NumberRange(min=0, max=200)],
        render_kw={
            'placeholder': '86.0',
            'class': 'form-input',
            'step': '0.1'
        }
    )
    
    battery_cells = IntegerField(
        'Número de Celdas',
        validators=[Optional(), NumberRange(min=1, max=12)],
        render_kw={
            'placeholder': '6',
            'class': 'form-input'
        }
    )
    
    # ===== 7. ESTÉTICA =====
    color = StringField(
        'Color',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'placeholder': 'Ej: Platinum Silver, Carbon Black',
            'class': 'form-input'
        }
    )
    
    chassis_material = SelectField(
        'Material del Chasis',
        choices=[
            ('', 'Seleccionar...'),
            ('aluminum', 'Aluminio'),
            ('magnesium', 'Magnesio'),
            ('carbon_fiber', 'Fibra de Carbono'),
            ('plastic', 'Plástico'),
            ('mixed', 'Combinado'),
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    # ===== 8. ESTADO Y CATEGORÍA =====
    category = SelectField(
        'Categoría',
        choices=CATEGORY_CHOICES,
        default='laptop',
        validators=[DataRequired()],
        render_kw={'class': 'form-input'}
    )
    
    condition = SelectField(
        'Condición',
        choices=CONDITION_CHOICES,
        default='used',
        validators=[DataRequired()],
        render_kw={'class': 'form-input'}
    )
    
    warranty_months = IntegerField(
        'Garantía (meses)',
        validators=[Optional(), NumberRange(min=0, max=60)],
        render_kw={
            'placeholder': '12',
            'class': 'form-input'
        }
    )
    
    warranty_type = SelectField(
        'Tipo de Garantía',
        choices=WARRANTY_TYPE_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    # ===== 9. INFORMACIÓN FINANCIERA =====
    purchase_cost = DecimalField(
        'Costo de Compra',
        places=2,
        validators=[
            DataRequired(message='El costo de compra es requerido'),
            NumberRange(min=0, message='El costo debe ser positivo')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input font-mono',
            'step': '0.01',
            'min': '0'
        }
    )
    
    sale_price = DecimalField(
        'Precio de Venta',
        places=2,
        validators=[
            DataRequired(message='El precio de venta es requerido'),
            NumberRange(min=0, message='El precio debe ser positivo')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input font-mono',
            'step': '0.01',
            'min': '0'
        }
    )
    
    discount_price = DecimalField(
        'Precio con Descuento',
        places=2,
        validators=[
            Optional(),
            NumberRange(min=0, message='El precio debe ser positivo')
        ],
        render_kw={
            'placeholder': 'Dejar vacío si no hay descuento',
            'class': 'form-input font-mono',
            'step': '0.01',
            'min': '0'
        }
    )
    
    tax_percent = DecimalField(
        'Impuesto (%)',
        places=2,
        default=Decimal('18.00'),
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message='El impuesto debe estar entre 0 y 100%')
        ],
        render_kw={
            'placeholder': '18.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'max': '100'
        }
    )
    
    msrp = DecimalField(
        'MSRP (Precio Sugerido)',
        places=2,
        validators=[Optional(), NumberRange(min=0)],
        render_kw={
            'placeholder': 'Precio de lista del fabricante',
            'class': 'form-input font-mono',
            'step': '0.01',
            'min': '0'
        }
    )
    
    currency = SelectField(
        'Moneda',
        choices=CURRENCY_CHOICES,
        default='DOP',
        render_kw={'class': 'form-input'}
    )
    
    # Campos calculados (solo lectura, manejados por JS)
    gross_profit = HiddenField('Ganancia Bruta')
    margin_percentage = HiddenField('Margen %')
    
    # ===== 10. INVENTARIO =====
    quantity = IntegerField(
        'Cantidad Total',
        validators=[
            DataRequired(message='La cantidad es requerida'),
            NumberRange(min=0, max=9999)
        ],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-input',
            'min': '0',
            'max': '9999'
        }
    )
    
    reserved_quantity = IntegerField(
        'Cantidad Reservada',
        validators=[Optional(), NumberRange(min=0)],
        default=0,
        render_kw={
            'placeholder': '0',
            'class': 'form-input',
            'min': '0'
        }
    )
    
    min_alert = IntegerField(
        'Alerta Mínima',
        validators=[
            DataRequired(message='La alerta mínima es requerida'),
            NumberRange(min=0)
        ],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-input',
            'min': '0'
        }
    )
    
    # ===== 11. UBICACIÓN Y LOGÍSTICA =====
    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[DataRequired(message='La tienda es requerida')],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona una tienda',
            'data-endpoint': '/api/catalog/stores'
        }
    )
    
    location_id = SelectField(
        'Ubicación',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Ej: Estante A-1, Vitrina 3',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/locations'
        }
    )
    
    supplier_id = SelectField(
        'Proveedor',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-catalog',
            'data-placeholder': 'Selecciona un proveedor',
            'data-allow-create': 'true',
            'data-endpoint': '/api/catalog/suppliers'
        }
    )
    
    # ===== 12. NOTAS INTERNAS =====
    internal_notes = TextAreaField(
        'Notas Internas',
        validators=[Optional(), Length(max=2000)],
        render_kw={
            'placeholder': 'Notas privadas sobre este producto (no visibles al público)',
            'class': 'form-input',
            'rows': '4'
        }
    )
    
    # ===== SUBMIT =====
    submit = SubmitField(
        'Guardar Laptop',
        render_kw={
            'class': 'w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 '
                     'text-white font-semibold rounded-lg shadow-lg hover:shadow-xl '
                     'transition-all duration-300 disabled:opacity-50'
        }
    )
    
    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y carga las opciones de los selectores"""
        super(LaptopForm, self).__init__(*args, **kwargs)
        self._load_catalog_options()
    
    def _load_catalog_options(self):
        """Carga las opciones iniciales para los selectores"""
        # Importar modelos aquí para evitar imports circulares
        from app.models.laptop import (
            Brand, LaptopModel, Processor, OperatingSystem,
            Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
        )
        
        # Función helper para cargar opciones
        def load_options(model, field, default_text):
            field.choices = [(0, default_text)] + [
                (item.id, item.name) 
                for item in model.query.filter_by(is_active=True).order_by(model.name).all()
            ]
        
        load_options(Brand, self.brand_id, 'Selecciona una marca')
        load_options(LaptopModel, self.model_id, 'Selecciona un modelo')
        load_options(Processor, self.processor_id, 'Selecciona un procesador')
        load_options(OperatingSystem, self.os_id, 'Selecciona un SO')
        load_options(Screen, self.screen_id, 'Selecciona una pantalla')
        load_options(GraphicsCard, self.graphics_card_id, 'Selecciona una GPU')
        load_options(Storage, self.storage_id, 'Selecciona almacenamiento')
        load_options(Ram, self.ram_id, 'Selecciona RAM')
        load_options(Store, self.store_id, 'Selecciona una tienda')
        load_options(Location, self.location_id, 'Selecciona ubicación')
        load_options(Supplier, self.supplier_id, 'Selecciona proveedor')
    
    def populate_from_icecat(self, icecat_data: dict):
        """
        Pre-puebla el formulario con datos de Icecat.
        
        Args:
            icecat_data: Diccionario con datos preparados de Icecat
        """
        # Marcar como datos de Icecat
        self.icecat_data_id.data = icecat_data.get('icecat_data_id')
        self.data_source.data = 'icecat'
        
        # Identificadores
        self.gtin.data = icecat_data.get('gtin')
        self.mpn.data = icecat_data.get('mpn')
        
        # Marketing
        self.display_name.data = icecat_data.get('display_name')
        self.short_description.data = icecat_data.get('short_description')
        self.long_description_html.data = icecat_data.get('long_description_html')
        
        # Relaciones (si existen)
        if icecat_data.get('brand_id'):
            self.brand_id.data = icecat_data['brand_id']
        if icecat_data.get('model_id'):
            self.model_id.data = icecat_data['model_id']
        if icecat_data.get('processor_id'):
            self.processor_id.data = icecat_data['processor_id']
        if icecat_data.get('ram_id'):
            self.ram_id.data = icecat_data['ram_id']
        if icecat_data.get('storage_id'):
            self.storage_id.data = icecat_data['storage_id']
        if icecat_data.get('screen_id'):
            self.screen_id.data = icecat_data['screen_id']
        if icecat_data.get('graphics_card_id'):
            self.graphics_card_id.data = icecat_data['graphics_card_id']
        if icecat_data.get('os_id'):
            self.os_id.data = icecat_data['os_id']
        
        # Dimensiones
        if icecat_data.get('weight_kg'):
            self.weight_kg.data = Decimal(str(icecat_data['weight_kg']))
        if icecat_data.get('battery_wh'):
            self.battery_wh.data = Decimal(str(icecat_data['battery_wh']))
        
        # Categoría
        if icecat_data.get('category'):
            self.category.data = icecat_data['category']
    
    # ===== VALIDACIONES PERSONALIZADAS =====
    
    def validate_reserved_quantity(self, field):
        """Valida que la cantidad reservada no exceda la total"""
        if field.data and self.quantity.data:
            if field.data > self.quantity.data:
                raise ValidationError('La cantidad reservada no puede ser mayor que la total')
    
    def validate_discount_price(self, field):
        """Valida que el precio de descuento sea menor al de venta"""
        if field.data and self.sale_price.data:
            if field.data >= self.sale_price.data:
                raise ValidationError('El precio de descuento debe ser menor al precio de venta')
    
    def validate_sale_price(self, field):
        """Valida que el precio de venta sea mayor al costo"""
        if field.data and self.purchase_cost.data:
            if field.data < self.purchase_cost.data:
                # Solo advertencia, no error
                pass  # Se puede mostrar una advertencia en el frontend
    
    def validate_brand_id(self, field):
        """Valida que se haya seleccionado una marca válida"""
        if not field.data or field.data == 0:
            raise ValidationError('Debes seleccionar una marca')
    
    def validate_store_id(self, field):
        """Valida que se haya seleccionado una tienda válida"""
        if not field.data or field.data == 0:
            raise ValidationError('Debes seleccionar una tienda')


# ===== FORMULARIO DE FILTROS =====

class FilterForm(FlaskForm):
    """
    Formulario para filtrar el listado de laptops
    """
    q = StringField(
        'Buscar',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'SKU, nombre, GTIN...',
            'class': 'form-input'
        }
    )
    
    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    brand_id = SelectField(
        'Marca',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    category = SelectField(
        'Categoría',
        choices=[('', 'Todas')] + CATEGORY_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    condition = SelectField(
        'Condición',
        choices=[('', 'Todas')] + CONDITION_CHOICES,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    data_source = SelectField(
        'Origen de Datos',
        choices=[
            ('', 'Todos'),
            ('manual', 'Manual'),
            ('icecat', 'Icecat'),
            ('icecat_modified', 'Icecat (Modificado)'),
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    is_published = SelectField(
        'Estado',
        choices=[
            ('', 'Todos'),
            ('1', 'Publicados'),
            ('0', 'No Publicados'),
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    
    low_stock = BooleanField(
        'Solo bajo stock',
        default=False,
        render_kw={'class': 'form-checkbox'}
    )
    
    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self._load_filter_options()
    
    def _load_filter_options(self):
        """Carga opciones para los filtros"""
        from app.models.laptop import Brand, Store
        
        self.store_id.choices = [(0, 'Todas las tiendas')] + [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]
        
        self.brand_id.choices = [(0, 'Todas las marcas')] + [
            (b.id, b.name) for b in Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
        ]


# ===== FORMULARIO DE IMPORTACIÓN MASIVA =====

class BulkImportForm(FlaskForm):
    """
    Formulario para importación masiva de productos
    """
    import_file = FileField(
        'Archivo de Importación',
        validators=[
            DataRequired(),
            FileAllowed(['csv', 'xlsx', 'xls'], 'Solo archivos CSV o Excel')
        ],
        render_kw={
            'class': 'form-input',
            'accept': '.csv,.xlsx,.xls'
        }
    )
    
    import_mode = SelectField(
        'Modo de Importación',
        choices=[
            ('create', 'Solo crear nuevos'),
            ('update', 'Solo actualizar existentes'),
            ('both', 'Crear y actualizar'),
        ],
        default='both',
        render_kw={'class': 'form-input'}
    )
    
    default_store_id = SelectField(
        'Tienda por Defecto',
        coerce=int,
        validators=[DataRequired()],
        render_kw={'class': 'form-input'}
    )
    
    submit = SubmitField('Importar')
    
    def __init__(self, *args, **kwargs):
        super(BulkImportForm, self).__init__(*args, **kwargs)
        from app.models.laptop import Store
        self.default_store_id.choices = [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]
