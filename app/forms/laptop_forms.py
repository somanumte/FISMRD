# -*- coding: utf-8 -*-
# =========================================
# FORMULARIOS DE INVENTARIO DE LAPTOPS
# ============================================
# Actualizado al nuevo modelo de datos

from app import db
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField, SelectField, DecimalField, IntegerField,
    TextAreaField, BooleanField, SubmitField, HiddenField,
    DateField, SelectMultipleField, FieldList, FormField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError, URL, Regexp
from app.utils.validators import (
    PositiveNumber, PositiveOrZero, SalePriceValidator,
    MinimumMarginValidator, QuantityValidator, SKUValidator
)
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)

# ===== OPCIONES DE PUERTOS DE CONECTIVIDAD =====
CONNECTIVITY_PORTS_CHOICES = [
    ('usb_a_2', 'USB-A 2.0'),
    ('usb_a_3', 'USB-A 3.0'),
    ('usb_a_31', 'USB-A 3.1'),
    ('usb_c', 'USB-C'),
    ('usb_c_thunderbolt', 'USB-C Thunderbolt'),
    ('hdmi', 'HDMI'),
    ('hdmi_21', 'HDMI 2.1'),
    ('displayport', 'DisplayPort'),
    ('mini_displayport', 'Mini DisplayPort'),
    ('ethernet', 'Ethernet RJ-45'),
    ('sd_card', 'Lector SD'),
    ('microsd', 'Lector MicroSD'),
    ('audio_jack', 'Jack Audio 3.5mm'),
    ('vga', 'VGA'),
    ('dvi', 'DVI'),
]

# ===== OPCIONES DE KEYBOARD LAYOUT =====
KEYBOARD_LAYOUT_CHOICES = [
    ('US', 'US - Ingles'),
    ('UK', 'UK - Ingles britanico'),
    ('ES', 'ES - Espanol Espana'),
    ('LATAM', 'LATAM - Espanol Latinoamerica'),
    ('DE', 'DE - Aleman'),
    ('FR', 'FR - Frances'),
    ('IT', 'IT - Italiano'),
    ('PT', 'PT - Portugues'),
    ('BR', 'BR - Portugues Brasil'),
    ('JP', 'JP - Japones'),
    ('KR', 'KR - Coreano'),
    ('CN', 'CN - Chino'),
]


# ===== FORMULARIO DE BÚSQUEDA RÁPIDA =====
class QuickSearchForm(FlaskForm):
    """
    Formulario simple para búsqueda rápida en el inventario
    """
    q = StringField(
        'Buscar',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Buscar por SKU, nombre, modelo...',
            'class': 'form-input'
        }
    )
    submit = SubmitField('Buscar')


# ===== FORMULARIO DE FILTROS =====
class FilterForm(FlaskForm):
    """
    Formulario para filtrar el listado de laptops
    Usado en laptops_list.html
    """
    # Filtro por tienda
    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por marca
    brand_id = SelectField(
        'Marca',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por procesador (Familia)
    processor_id = SelectField(
        'Procesador',
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por generación de procesador
    processor_generation = SelectField(
        'Generación',
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por tarjeta gráfica
    graphics_card_id = SelectField(
        'Tarjeta Gráfica',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por pantalla
    screen_id = SelectField(
        'Pantalla',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por categoría
    category = SelectField(
        'Categoría',
        choices=[
            ('', 'Todas'),
            ('laptop', 'Laptop'),
            ('workstation', 'Workstation'),
            ('gaming', 'Gaming')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    # Filtro por condición
    condition = SelectField(
        'Condición',
        choices=[
            ('', 'Todas'),
            ('new', 'Nuevo'),
            ('used', 'Usado'),
            ('refurbished', 'Refurbished')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y carga las opciones de los selectores"""
        super(FilterForm, self).__init__(*args, **kwargs)

        # Stores
        self.store_id.choices = [(0, 'Todas las tiendas')] + [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]

        # Brands
        self.brand_id.choices = [(0, 'Todas las marcas')] + [
            (b.id, b.name) for b in Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
        ]

        # Processors (Grouped by Family)
        self.processor_id.choices = [('', 'Todos los procesadores')] + [
            (f[0], f[0]) for f in db.session.query(Processor.family).filter(
                Processor.is_active == True,
                Processor.family != None
            ).distinct().order_by(Processor.family).all()
        ]

        # Processor Generations
        self.processor_generation.choices = [('', 'Todas las generaciones')] + [
            (g[0], g[0]) for g in db.session.query(Processor.name).filter(
                Processor.is_active == True,
                Processor.name != None
            ).distinct().order_by(Processor.name).all()
        ]

        # Graphics Cards
        self.graphics_card_id.choices = [(0, 'Todas las GPUs')] + [
            (g.id, g.name) for g in GraphicsCard.query.filter_by(is_active=True).order_by(GraphicsCard.name).all()
        ]

        # Screens
        self.screen_id.choices = [(0, 'Todas las pantallas')] + [
            (s.id, s.name) for s in Screen.query.filter_by(is_active=True).order_by(Screen.name).all()
        ]


# ===== FORMULARIO PRINCIPAL DE LAPTOP =====
class LaptopForm(FlaskForm):
    """
    Formulario principal para agregar/editar laptops
    """

    # ===== 1. IDENTIFICADORES =====
    sku = StringField(
        'SKU',
        validators=[Optional(), SKUValidator()],
        render_kw={
            'placeholder': 'Se generara automaticamente',
            'class': 'form-input',
            'readonly': True
        }
    )

    icecat_id = HiddenField('Icecat ID')
    full_specs_json = HiddenField('Icecat Full Specs')
    normalized_specs = HiddenField('Icecat Normalized Specs')

    gtin = StringField(
        'EAN / UPC (GTIN)',
        validators=[Optional(), Length(max=50)],
        render_kw={
            'placeholder': 'Escanea o ingresa el codigo de barras',
            'class': 'form-input',
            'id': 'gtin-input'
        }
    )


    slug = StringField(
        'URL amigable',
        validators=[
            Optional(),
            Length(max=255),
            Regexp(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', message='Solo letras minusculas, numeros y guiones')
        ],
        render_kw={
            'placeholder': 'Se generara automaticamente del nombre',
            'class': 'form-input'
        }
    )

    # ===== 2. MARKETING Y WEB (SEO) =====
    display_name = StringField(
        'Nombre Comercial',
        validators=[
            DataRequired(message='El nombre comercial es requerido'),
            Length(max=200)
        ],
        render_kw={
            'placeholder': 'Ej: Dell XPS 15 - Intel i7 - 16GB RAM - 512GB SSD',
            'class': 'form-input'
        }
    )

    short_description = TextAreaField(
        'Descripcion Corta',
        validators=[Optional(), Length(max=300)],
        render_kw={
            'placeholder': 'Descripcion breve para tarjetas de producto (max. 300 caracteres)',
            'class': 'form-input',
            'rows': '2'
        }
    )

    long_description_html = TextAreaField(
        'Descripcion Completa (HTML/Markdown)',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Descripcion detallada del producto. Soporta HTML y Markdown.',
            'class': 'form-input',
            'rows': '6'
        }
    )

    is_published = BooleanField(
        'Publicado',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    is_featured = BooleanField(
        'Destacado',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    seo_title = StringField(
        'Titulo SEO',
        validators=[Optional(), Length(max=70)],
        render_kw={
            'placeholder': 'Titulo para motores de busqueda (max. 70 caracteres)',
            'class': 'form-input'
        }
    )

    seo_description = StringField(
        'Descripcion SEO',
        validators=[Optional(), Length(max=160)],
        render_kw={
            'placeholder': 'Meta descripcion para SEO (max. 160 caracteres)',
            'class': 'form-input'
        }
    )

    # ===== 3. ESPECIFICACIONES TÉCNICAS =====
    brand_id = StringField(
        'Marca',
        validators=[DataRequired(message='La marca es requerida')],
        render_kw={
            'placeholder': 'Ej: Dell, HP, ASUS',
            'class': 'form-input spec-field',
            'id': 'brand_id'
        }
    )

    model_id = StringField(
        'Modelo',
        validators=[DataRequired(message='El modelo es requerido')],
        render_kw={
            'placeholder': 'Ej: Inspiron 15, ROG Strix G18',
            'class': 'form-input spec-field',
            'id': 'model_id'
        }
    )

    # Procesador (Nueva estructura de 3 campos)
    processor_family = StringField(
        'Familia del Procesador',
        validators=[DataRequired(message='La familia del procesador es requerida')],
        render_kw={
            'placeholder': 'Ej: Intel Core i7 / AMD Ryzen 9',
            'class': 'form-input spec-field',
            'id': 'processor_family'
        }
    )
    processor_generation = StringField(
        'Generación',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Ej: 12th Gen / AMD Ryzen 8000 Series',
            'class': 'form-input spec-field',
            'id': 'processor_generation'
        }
    )
    processor_model = StringField(
        'Modelo / Número',
        validators=[DataRequired(message='El modelo del procesador es requerido')],
        render_kw={
            'placeholder': 'Ej: 12700H / 8940HX',
            'class': 'form-input spec-field',
            'id': 'processor_model'
        }
    )

    processor_full_name = StringField(
        'Nombre Completo (Ejecución)',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Ej: 12th Gen Intel Core i7-12700H',
            'class': 'form-input',
            'id': 'processor_full_name'
        }
    )

    os_id = StringField(
        'Sistema Operativo',
        validators=[DataRequired(message='El sistema operativo es requerido')],
        render_kw={
            'placeholder': 'Ej: Windows 11 Pro',
            'class': 'form-input spec-field',
            'id': 'os_id'
        }
    )

    screen_id = StringField(
        'Resolución de Pantalla',
        validators=[DataRequired(message='La pantalla es requerida')],
        render_kw={
            'placeholder': 'Ej: 15.6" FHD IPS',
            'class': 'form-input spec-field',
            'id': 'screen_id'
        }
    )

    screen_size = DecimalField(
        'Tamaño de Pantalla (Pulgadas)',
        places=1,
        validators=[Optional(), NumberRange(min=0)],
        render_kw={
            'placeholder': 'Ej: 15.6',
            'class': 'form-input',
            'step': '0.1',
            'id': 'screen_size'
        }
    )

    graphics_card_id = StringField(
        'Tarjeta Gráfica',
        validators=[DataRequired(message='La tarjeta grafica es requerida')],
        render_kw={
            'placeholder': 'Ej: NVIDIA RTX 4060',
            'class': 'form-input spec-field',
            'id': 'graphics_card_id'
        }
    )

    has_discrete_gpu = BooleanField(
        'Tiene GPU Dedicada',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded',
            'id': 'has_discrete_gpu'
        }
    )

    storage_id = StringField(
        'Almacenamiento',
        validators=[DataRequired(message='El almacenamiento es requerido')],
        render_kw={
            'placeholder': 'Ej: 512GB SSD NVMe',
            'class': 'form-input spec-field',
            'id': 'storage_id'
        }
    )

    storage_upgradeable = BooleanField(
        'Almacenamiento ampliable',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    storage_capacity = IntegerField(
        'Capacidad Almacenamiento (GB)',
        validators=[Optional(), NumberRange(min=0)],
        render_kw={
            'placeholder': 'Ej: 512',
            'class': 'form-input',
            'id': 'storage_capacity'
        }
    )

    ram_id = StringField(
        'RAM',
        validators=[DataRequired(message='La RAM es requerida')],
        render_kw={
            'placeholder': 'Ej: 16GB DDR5',
            'class': 'form-input spec-field',
            'id': 'ram_id'
        }
    )

    ram_upgradeable = BooleanField(
        'RAM ampliable',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    ram_capacity = IntegerField(
        'Capacidad RAM (GB)',
        validators=[Optional(), NumberRange(min=0)],
        render_kw={
            'placeholder': 'Ej: 16',
            'class': 'form-input',
            'id': 'ram_capacity'
        }
    )

    # ===== 4. DETALLES TÉCNICOS ESPECÍFICOS =====
    npu = BooleanField(
        'Tiene NPU (Procesador de IA)',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    keyboard_backlight = BooleanField(
        'Teclado retroiluminado',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded',
            'id': 'keyboard_backlight'
        }
    )

    keyboard_layout = SelectField(
        'Distribucion del Teclado',
        choices=KEYBOARD_LAYOUT_CHOICES,
        default='US',
        validators=[DataRequired(message='La distribucion del teclado es requerida')],
        render_kw={
            'class': 'form-input'
        }
    )

    connectivity_ports = TextAreaField(
        'Puertos de Conectividad',
        validators=[Optional(), Length(max=2000)],
        render_kw={
            'class': 'form-input',
            'placeholder': 'Ej: 2x USB 3.2, 1x HDMI, 1x RJ-45...',
            'rows': '3',
            'id': 'connectivity_ports'
        }
    )

    wifi_standard = StringField(
        'Estandar Wi-Fi',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Ej: Wi-Fi 6 (802.11ax)',
            'class': 'form-input',
            'id': 'wifi_standard'
        }
    )

    cellular = StringField(
        'Conectividad Celular',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Ej: 4G LTE, 5G (Opcional)',
            'class': 'form-input',
            'id': 'cellular'
        }
    )

    # ===== 10. COMERCIAL Y GARANTÍA =====
    keywords = StringField(
        'Palabras clave (SEO)',
        validators=[Optional(), Length(max=500)],
        render_kw={
            'placeholder': 'Ej: gaming, ultrabook, workstation, dell, xps',
            'class': 'form-input',
            'id': 'keywords'
        }
    )

    currency = StringField(
        'Moneda',
        default='USD',
        validators=[Optional(), Length(max=10)],
        render_kw={
            'class': 'form-input',
            'id': 'currency'
        }
    )

    warranty_months = IntegerField(
        'Meses de Garantía',
        validators=[Optional(), NumberRange(min=0)],
        render_kw={
            'placeholder': 'Ej: 12',
            'class': 'form-input',
            'id': 'warranty_months'
        }
    )

    warranty_expiry = DateField(
        'Vencimiento de Garantía',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'type': 'date',
            'id': 'warranty_expiry'
        }
    )

    public_notes = TextAreaField(
        'Notas Públicas',
        validators=[Optional(), Length(max=2000)],
        render_kw={
            'placeholder': 'Notas visibles para el cliente...',
            'class': 'form-input',
            'rows': '3',
            'id': 'public_notes'
        }
    )

    # ===== 5. ESTADO Y CATEGORÍA =====
    category = SelectField(
        'Categoría',
        choices=[
            ('', 'Selecciona una categoria'),
            ('laptop', ' Laptop'),
            ('workstation', ' Workstation'),
            ('gaming', ' Gaming')
        ],
        validators=[DataRequired(message='La categoria es requerida')],
        render_kw={
            'class': 'form-input'
        }
    )

    condition = SelectField(
        'Condicion',
        choices=[
            ('', 'Selecciona condicion'),
            ('new', ' Nuevo'),
            ('used', ' Usado'),
            ('refurbished', ' Reacondicionado')
        ],
        validators=[DataRequired(message='La condicion es requerida')],
        default='used',
        render_kw={
            'class': 'form-input',
            'id': 'condition'
        }
    )

    # ===== 6. IMÁGENES =====
    # Campos para hasta 8 imágenes
    image_1 = FileField(
        'Imagen 1 (Principal)',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_1_alt = StringField(
        'Texto alternativo Imagen 1',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_2 = FileField(
        'Imagen 2',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_2_alt = StringField(
        'Texto alternativo Imagen 2',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_3 = FileField(
        'Imagen 3',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_3_alt = StringField(
        'Texto alternativo Imagen 3',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_4 = FileField(
        'Imagen 4',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_4_alt = StringField(
        'Texto alternativo Imagen 4',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_5 = FileField(
        'Imagen 5',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_5_alt = StringField(
        'Texto alternativo Imagen 5',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_6 = FileField(
        'Imagen 6',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_6_alt = StringField(
        'Texto alternativo Imagen 6',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_7 = FileField(
        'Imagen 7',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_7_alt = StringField(
        'Texto alternativo Imagen 7',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    image_8 = FileField(
        'Imagen 8',
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'accept': 'image/*'
        }
    )

    image_8_alt = StringField(
        'Texto alternativo Imagen 8',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripción de la imagen para SEO',
            'class': 'form-input'
        }
    )

    # ===== 7. FINANCIEROS =====
    purchase_cost = DecimalField(
        'Costo de Compra ($)',
        places=2,
        validators=[
            DataRequired(message='El costo de compra es requerido'),
            PositiveNumber(message='El costo debe ser mayor a 0')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0.01',
            'id': 'purchase_cost'
        }
    )

    sale_price = DecimalField(
        'Precio de Venta ($)',
        places=2,
        validators=[
            DataRequired(message='El precio de venta es requerido'),
            PositiveNumber(message='El precio debe ser mayor a 0'),
            SalePriceValidator('purchase_cost')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0.01',
            'id': 'sale_price'
        }
    )

    discount_price = DecimalField(
        'Precio con Descuento ($)',
        places=2,
        validators=[
            Optional(),
            PositiveOrZero(message='El precio de descuento debe ser 0 o mayor')
        ],
        render_kw={
            'placeholder': '0.00 (dejar vacio si no hay descuento)',
            'class': 'form-input',
            'step': '0.01',
            'min': '0'
        }
    )

    tax_percent = DecimalField(
        'Impuesto (%)',
        places=2,
        default=0.00,
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message='El impuesto debe estar entre 0 y 100%')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'max': '100'
        }
    )

    # Campo oculto para mostrar el margen (calculado por JavaScript)
    margin_percentage = HiddenField('Margen %')

    # ===== 8. INVENTARIO =====
    quantity = IntegerField(
        'Cantidad Total',
        validators=[
            DataRequired(message='La cantidad es requerida'),
            QuantityValidator(min_quantity=0, max_quantity=9999)
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
        validators=[
            Optional(),
            PositiveOrZero(message='La cantidad reservada debe ser 0 o mayor')
        ],
        default=0,
        render_kw={
            'placeholder': '0',
            'class': 'form-input',
            'min': '0'
        }
    )

    min_alert = IntegerField(
        'Alerta Minima',
        validators=[
            DataRequired(message='La alerta minima es requerida'),
            PositiveOrZero(message='La alerta debe ser 0 o mayor')
        ],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-input',
            'min': '0'
        }
    )

    # ===== UBICACIÓN Y LOGÍSTICA =====
    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[DataRequired(message='La tienda es requerida')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea una tienda',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/stores'
        }
    )

    location_id = SelectField(
        'Ubicacion',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: Estante A-1, Vitrina 3',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/locations'
        }
    )

    supplier_id = SelectField(
        'Proveedor',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea un proveedor',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/suppliers'
        }
    )

    # ===== 9. TIMESTAMPS =====
    # entry_date se establece automaticamente en el backend (date.today())
    # sale_date se establece cuando se realiza una venta

    # ===== NOTAS =====
    internal_notes = TextAreaField(
        'Notas Internas',
        validators=[Optional(), Length(max=2000)],
        render_kw={
            'placeholder': 'Notas internas, observaciones, etc. (no visibles al publico)',
            'class': 'form-input',
            'rows': '4'
        }
    )

    # ===== SUBMIT =====
    submit = SubmitField(
        'Guardar Laptop',
        render_kw={
            'class': 'w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300'
        }
    )

    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y carga las opciones de los selectores"""
        super(LaptopForm, self).__init__(*args, **kwargs)

        # Cargar opciones para los SelectFields desde la base de datos
        # Nota: brand_id, model_id, etc. ahora son StringFields, no se cargan opciones aquí.

        # Catalog Fields (Ubicación y Logística)
        self.store_id.choices = [(0, 'Selecciona una tienda')] + [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]

        # La inicialización de choices para brand_id, model_id, etc. fue removida 
        # porque esos campos ahora son de tipo Texto (StringField) para mejorar
        # la integración con el auto-llenado de Icecat.

        # Storage
        self.storage_id.choices = [(0, 'Selecciona o crea almacenamiento')] + [
            (st.id, st.name) for st in Storage.query.filter_by(is_active=True).order_by(Storage.name).all()
        ]

        # RAM
        self.ram_id.choices = [(0, 'Selecciona o crea RAM')] + [
            (r.id, r.name) for r in Ram.query.filter_by(is_active=True).order_by(Ram.name).all()
        ]

        # Locations
        self.location_id.choices = [(0, 'Selecciona o crea una ubicacion')] + [
            (l.id, l.name) for l in Location.query.filter_by(is_active=True).order_by(Location.name).all()
        ]

        # Suppliers
        self.supplier_id.choices = [(0, 'Selecciona o crea un proveedor')] + [
            (s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
        ]

    def validate_reserved_quantity(self, field):
        """Valida que la cantidad reservada no exceda la cantidad total"""
        if field.data and self.quantity.data:
            if field.data > self.quantity.data:
                raise ValidationError('La cantidad reservada no puede ser mayor que la cantidad total')

    def validate_discount_price(self, field):
        """Valida que el precio de descuento sea menor al precio de venta"""
        if field.data and self.sale_price.data:
            if field.data >= self.sale_price.data:
                raise ValidationError('El precio de descuento debe ser menor al precio de venta')

    # Validar que las imágenes sean del tipo correcto
    def validate_image_1(self, field):
        self._validate_image_field(field, 'image_1')

    def validate_image_2(self, field):
        self._validate_image_field(field, 'image_2')

    def validate_image_3(self, field):
        self._validate_image_field(field, 'image_3')

    def validate_image_4(self, field):
        self._validate_image_field(field, 'image_4')

    def validate_image_5(self, field):
        self._validate_image_field(field, 'image_5')

    def validate_image_6(self, field):
        self._validate_image_field(field, 'image_6')

    def validate_image_7(self, field):
        self._validate_image_field(field, 'image_7')

    def validate_image_8(self, field):
        self._validate_image_field(field, 'image_8')

    def _validate_image_field(self, field, field_name):
        """Valida un campo de imagen individual"""
        if field.data:
            # Verificar extensión del archivo
            filename = field.data.filename
            if filename:
                allowed_extensions = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'avif'}
                if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                    raise ValidationError('Solo se permiten imágenes (jpg, png, webp, gif, avif)')