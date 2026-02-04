# -*- coding: utf-8 -*-
"""
Migración: Actualización de modelos de Laptop para soporte PIM/Icecat

Esta migración:
1. Crea la tabla icecat_product_data para almacenar datos originales de Icecat
2. Agrega nuevos campos al modelo Laptop para tracking de origen de datos
3. Mejora la tabla laptop_images para soportar imágenes remotas
4. Crea la tabla laptop_technical_specs para especificaciones adicionales
5. Agrega campos de especificaciones a los modelos de catálogo

Revision ID: 001_pim_icecat_support
Create Date: 2024-XX-XX
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_pim_icecat_support'
down_revision = None  # Ajustar al último migration ID
branch_labels = None
depends_on = None


def upgrade():
    """Aplicar cambios de migración"""
    
    # ========================================
    # 1. CREAR TABLA icecat_product_data
    # ========================================
    op.create_table(
        'icecat_product_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        
        # Identificadores de Icecat
        sa.Column('icecat_id', sa.Integer(), nullable=False),
        sa.Column('icecat_gtin', sa.String(20), nullable=True),
        sa.Column('product_code', sa.String(100), nullable=True),
        
        # Información básica
        sa.Column('brand_name', sa.String(100), nullable=False),
        sa.Column('brand_id_icecat', sa.String(50), nullable=True),
        sa.Column('product_name', sa.String(300), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('category_name', sa.String(100), nullable=True),
        sa.Column('category_id_icecat', sa.String(50), nullable=True),
        
        # Descripciones
        sa.Column('short_description', sa.Text(), nullable=True),
        sa.Column('long_description_html', sa.Text(), nullable=True),
        sa.Column('summary_short', sa.Text(), nullable=True),
        sa.Column('summary_long', sa.Text(), nullable=True),
        
        # Especificaciones (JSON)
        sa.Column('specifications_json', sa.JSON(), nullable=True),
        sa.Column('feature_groups_json', sa.JSON(), nullable=True),
        
        # Campos extraídos
        sa.Column('extracted_processor', sa.String(200), nullable=True),
        sa.Column('extracted_ram', sa.String(100), nullable=True),
        sa.Column('extracted_storage', sa.String(100), nullable=True),
        sa.Column('extracted_screen', sa.String(100), nullable=True),
        sa.Column('extracted_graphics', sa.String(200), nullable=True),
        sa.Column('extracted_os', sa.String(100), nullable=True),
        sa.Column('extracted_weight_kg', sa.Numeric(5, 2), nullable=True),
        sa.Column('extracted_battery_wh', sa.Numeric(6, 2), nullable=True),
        sa.Column('extracted_dimensions', sa.String(100), nullable=True),
        
        # Imágenes
        sa.Column('images_json', sa.JSON(), nullable=True),
        sa.Column('main_image_url', sa.String(500), nullable=True),
        
        # Información adicional
        sa.Column('warranty_info', sa.Text(), nullable=True),
        sa.Column('release_date', sa.String(50), nullable=True),
        sa.Column('ean_codes', sa.JSON(), nullable=True),
        
        # Metadatos
        sa.Column('language', sa.String(5), server_default='ES', nullable=True),
        sa.Column('last_icecat_update', sa.DateTime(), nullable=True),
        sa.Column('raw_response_json', sa.JSON(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Índices para icecat_product_data
    op.create_index('idx_icecat_data_icecat_id', 'icecat_product_data', ['icecat_id'], unique=True)
    op.create_index('idx_icecat_data_gtin', 'icecat_product_data', ['icecat_gtin'])
    op.create_index('idx_icecat_data_product_code', 'icecat_product_data', ['product_code'])
    
    # ========================================
    # 2. AGREGAR COLUMNAS A TABLA laptops
    # ========================================
    
    # Referencia a Icecat
    op.add_column('laptops', sa.Column('icecat_data_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_laptops_icecat_data',
        'laptops', 'icecat_product_data',
        ['icecat_data_id'], ['id']
    )
    op.create_index('idx_laptop_icecat_data', 'laptops', ['icecat_data_id'])
    
    # Identificadores externos
    op.add_column('laptops', sa.Column('gtin', sa.String(20), nullable=True))
    op.add_column('laptops', sa.Column('mpn', sa.String(100), nullable=True))
    op.add_column('laptops', sa.Column('upc', sa.String(20), nullable=True))
    op.create_index('idx_laptop_gtin', 'laptops', ['gtin'])
    op.create_index('idx_laptop_mpn', 'laptops', ['mpn'])
    
    # Tracking de origen de datos
    op.add_column('laptops', sa.Column('data_source', sa.String(30), 
                                       server_default='manual', nullable=False))
    op.add_column('laptops', sa.Column('modified_fields_json', sa.JSON(), nullable=True))
    op.create_index('idx_laptop_data_source', 'laptops', ['data_source'])
    
    # SEO adicional
    op.add_column('laptops', sa.Column('seo_keywords', sa.String(255), nullable=True))
    
    # Características adicionales
    op.add_column('laptops', sa.Column('keyboard_backlit', sa.Boolean(), 
                                       server_default='true', nullable=True))
    op.add_column('laptops', sa.Column('fingerprint_reader', sa.Boolean(), 
                                       server_default='false', nullable=True))
    op.add_column('laptops', sa.Column('ir_camera', sa.Boolean(), 
                                       server_default='false', nullable=True))
    op.add_column('laptops', sa.Column('wireless_connectivity', sa.JSON(), nullable=True))
    
    # Dimensiones físicas
    op.add_column('laptops', sa.Column('weight_kg', sa.Numeric(5, 2), nullable=True))
    op.add_column('laptops', sa.Column('width_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('laptops', sa.Column('depth_mm', sa.Numeric(6, 2), nullable=True))
    op.add_column('laptops', sa.Column('height_mm', sa.Numeric(5, 2), nullable=True))
    
    # Batería
    op.add_column('laptops', sa.Column('battery_wh', sa.Numeric(6, 2), nullable=True))
    op.add_column('laptops', sa.Column('battery_cells', sa.Integer(), nullable=True))
    
    # Estética
    op.add_column('laptops', sa.Column('color', sa.String(50), nullable=True))
    op.add_column('laptops', sa.Column('chassis_material', sa.String(50), nullable=True))
    
    # Garantía
    op.add_column('laptops', sa.Column('warranty_months', sa.Integer(), nullable=True))
    op.add_column('laptops', sa.Column('warranty_type', sa.String(50), nullable=True))
    
    # MSRP y moneda
    op.add_column('laptops', sa.Column('msrp', sa.Numeric(12, 2), nullable=True))
    op.add_column('laptops', sa.Column('currency', sa.String(3), 
                                       server_default='DOP', nullable=False))
    
    # Timestamp de sync con Icecat
    op.add_column('laptops', sa.Column('last_icecat_sync', sa.DateTime(), nullable=True))
    
    # ========================================
    # 3. MEJORAR TABLA laptop_images
    # ========================================
    
    # URLs para imágenes remotas
    op.add_column('laptop_images', sa.Column('image_url', sa.String(500), nullable=True))
    op.add_column('laptop_images', sa.Column('thumb_url', sa.String(500), nullable=True))
    op.add_column('laptop_images', sa.Column('medium_url', sa.String(500), nullable=True))
    
    # Flag de imagen remota
    op.add_column('laptop_images', sa.Column('is_remote', sa.Boolean(), 
                                             server_default='false', nullable=False))
    
    # Dimensiones
    op.add_column('laptop_images', sa.Column('width', sa.Integer(), nullable=True))
    op.add_column('laptop_images', sa.Column('height', sa.Integer(), nullable=True))
    op.add_column('laptop_images', sa.Column('file_size_bytes', sa.Integer(), nullable=True))
    
    # Origen y estado de descarga
    op.add_column('laptop_images', sa.Column('source', sa.String(50), 
                                             server_default='manual', nullable=False))
    op.add_column('laptop_images', sa.Column('source_url', sa.String(500), nullable=True))
    op.add_column('laptop_images', sa.Column('is_downloaded', sa.Boolean(), 
                                             server_default='false', nullable=False))
    op.add_column('laptop_images', sa.Column('download_error', sa.String(255), nullable=True))
    
    # Índice adicional
    op.create_index('idx_laptop_image_position', 'laptop_images', ['laptop_id', 'position'])
    
    # ========================================
    # 4. CREAR TABLA laptop_technical_specs
    # ========================================
    op.create_table(
        'laptop_technical_specs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('laptop_id', sa.Integer(), nullable=False),
        sa.Column('spec_group', sa.String(100), nullable=False),
        sa.Column('spec_name', sa.String(200), nullable=False),
        sa.Column('spec_value', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(30), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('source', sa.String(50), server_default='manual', nullable=True),
        sa.ForeignKeyConstraint(['laptop_id'], ['laptops.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_tech_spec_laptop_group', 'laptop_technical_specs', ['laptop_id', 'spec_group'])
    
    # ========================================
    # 5. AGREGAR CAMPOS A MODELOS DE CATÁLOGO
    # ========================================
    
    # Brands
    op.add_column('brands', sa.Column('icecat_brand_id', sa.String(50), nullable=True))
    op.add_column('brands', sa.Column('logo_url', sa.String(500), nullable=True))
    op.add_column('brands', sa.Column('website', sa.String(200), nullable=True))
    op.create_index('idx_brand_icecat_id', 'brands', ['icecat_brand_id'])
    
    # Laptop Models
    op.add_column('laptop_models', sa.Column('icecat_product_family', sa.String(100), nullable=True))
    
    # Processors - especificaciones técnicas
    op.add_column('processors', sa.Column('manufacturer', sa.String(50), nullable=True))
    op.add_column('processors', sa.Column('family', sa.String(50), nullable=True))
    op.add_column('processors', sa.Column('model_number', sa.String(50), nullable=True))
    op.add_column('processors', sa.Column('cores', sa.Integer(), nullable=True))
    op.add_column('processors', sa.Column('threads', sa.Integer(), nullable=True))
    op.add_column('processors', sa.Column('base_clock_ghz', sa.Numeric(4, 2), nullable=True))
    op.add_column('processors', sa.Column('boost_clock_ghz', sa.Numeric(4, 2), nullable=True))
    op.add_column('processors', sa.Column('cache_mb', sa.Integer(), nullable=True))
    op.add_column('processors', sa.Column('tdp_watts', sa.Integer(), nullable=True))
    op.add_column('processors', sa.Column('generation', sa.String(20), nullable=True))
    op.add_column('processors', sa.Column('architecture', sa.String(50), nullable=True))
    
    # Operating Systems
    op.add_column('operating_systems', sa.Column('version', sa.String(50), nullable=True))
    op.add_column('operating_systems', sa.Column('edition', sa.String(50), nullable=True))
    op.add_column('operating_systems', sa.Column('architecture', sa.String(10), nullable=True))
    
    # Screens - especificaciones técnicas
    op.add_column('screens', sa.Column('size_inches', sa.Numeric(4, 1), nullable=True))
    op.add_column('screens', sa.Column('resolution_width', sa.Integer(), nullable=True))
    op.add_column('screens', sa.Column('resolution_height', sa.Integer(), nullable=True))
    op.add_column('screens', sa.Column('resolution_name', sa.String(20), nullable=True))
    op.add_column('screens', sa.Column('panel_type', sa.String(30), nullable=True))
    op.add_column('screens', sa.Column('refresh_rate_hz', sa.Integer(), nullable=True))
    op.add_column('screens', sa.Column('brightness_nits', sa.Integer(), nullable=True))
    op.add_column('screens', sa.Column('color_gamut', sa.String(50), nullable=True))
    op.add_column('screens', sa.Column('touch_enabled', sa.Boolean(), nullable=True))
    op.add_column('screens', sa.Column('hdr_support', sa.Boolean(), nullable=True))
    op.add_column('screens', sa.Column('aspect_ratio', sa.String(10), nullable=True))
    
    # Graphics Cards - especificaciones técnicas
    op.add_column('graphics_cards', sa.Column('manufacturer', sa.String(50), nullable=True))
    op.add_column('graphics_cards', sa.Column('is_integrated', sa.Boolean(), nullable=True))
    op.add_column('graphics_cards', sa.Column('vram_gb', sa.Integer(), nullable=True))
    op.add_column('graphics_cards', sa.Column('vram_type', sa.String(20), nullable=True))
    op.add_column('graphics_cards', sa.Column('max_tdp_watts', sa.Integer(), nullable=True))
    op.add_column('graphics_cards', sa.Column('cuda_cores', sa.Integer(), nullable=True))
    op.add_column('graphics_cards', sa.Column('ray_tracing', sa.Boolean(), nullable=True))
    
    # Storage - especificaciones técnicas
    op.add_column('storage', sa.Column('capacity_gb', sa.Integer(), nullable=True))
    op.add_column('storage', sa.Column('storage_type', sa.String(20), nullable=True))
    op.add_column('storage', sa.Column('interface', sa.String(30), nullable=True))
    op.add_column('storage', sa.Column('form_factor', sa.String(20), nullable=True))
    op.add_column('storage', sa.Column('read_speed_mbps', sa.Integer(), nullable=True))
    op.add_column('storage', sa.Column('write_speed_mbps', sa.Integer(), nullable=True))
    
    # RAM - especificaciones técnicas
    op.add_column('ram', sa.Column('capacity_gb', sa.Integer(), nullable=True))
    op.add_column('ram', sa.Column('ram_type', sa.String(20), nullable=True))
    op.add_column('ram', sa.Column('speed_mhz', sa.Integer(), nullable=True))
    op.add_column('ram', sa.Column('channels', sa.Integer(), nullable=True))
    op.add_column('ram', sa.Column('is_soldered', sa.Boolean(), nullable=True))


def downgrade():
    """Revertir cambios de migración"""
    
    # ========================================
    # REVERTIR CAMBIOS EN ORDEN INVERSO
    # ========================================
    
    # RAM
    op.drop_column('ram', 'is_soldered')
    op.drop_column('ram', 'channels')
    op.drop_column('ram', 'speed_mhz')
    op.drop_column('ram', 'ram_type')
    op.drop_column('ram', 'capacity_gb')
    
    # Storage
    op.drop_column('storage', 'write_speed_mbps')
    op.drop_column('storage', 'read_speed_mbps')
    op.drop_column('storage', 'form_factor')
    op.drop_column('storage', 'interface')
    op.drop_column('storage', 'storage_type')
    op.drop_column('storage', 'capacity_gb')
    
    # Graphics Cards
    op.drop_column('graphics_cards', 'ray_tracing')
    op.drop_column('graphics_cards', 'cuda_cores')
    op.drop_column('graphics_cards', 'max_tdp_watts')
    op.drop_column('graphics_cards', 'vram_type')
    op.drop_column('graphics_cards', 'vram_gb')
    op.drop_column('graphics_cards', 'is_integrated')
    op.drop_column('graphics_cards', 'manufacturer')
    
    # Screens
    op.drop_column('screens', 'aspect_ratio')
    op.drop_column('screens', 'hdr_support')
    op.drop_column('screens', 'touch_enabled')
    op.drop_column('screens', 'color_gamut')
    op.drop_column('screens', 'brightness_nits')
    op.drop_column('screens', 'refresh_rate_hz')
    op.drop_column('screens', 'panel_type')
    op.drop_column('screens', 'resolution_name')
    op.drop_column('screens', 'resolution_height')
    op.drop_column('screens', 'resolution_width')
    op.drop_column('screens', 'size_inches')
    
    # Operating Systems
    op.drop_column('operating_systems', 'architecture')
    op.drop_column('operating_systems', 'edition')
    op.drop_column('operating_systems', 'version')
    
    # Processors
    op.drop_column('processors', 'architecture')
    op.drop_column('processors', 'generation')
    op.drop_column('processors', 'tdp_watts')
    op.drop_column('processors', 'cache_mb')
    op.drop_column('processors', 'boost_clock_ghz')
    op.drop_column('processors', 'base_clock_ghz')
    op.drop_column('processors', 'threads')
    op.drop_column('processors', 'cores')
    op.drop_column('processors', 'model_number')
    op.drop_column('processors', 'family')
    op.drop_column('processors', 'manufacturer')
    
    # Laptop Models
    op.drop_column('laptop_models', 'icecat_product_family')
    
    # Brands
    op.drop_index('idx_brand_icecat_id', table_name='brands')
    op.drop_column('brands', 'website')
    op.drop_column('brands', 'logo_url')
    op.drop_column('brands', 'icecat_brand_id')
    
    # laptop_technical_specs
    op.drop_index('idx_tech_spec_laptop_group', table_name='laptop_technical_specs')
    op.drop_table('laptop_technical_specs')
    
    # laptop_images
    op.drop_index('idx_laptop_image_position', table_name='laptop_images')
    op.drop_column('laptop_images', 'download_error')
    op.drop_column('laptop_images', 'is_downloaded')
    op.drop_column('laptop_images', 'source_url')
    op.drop_column('laptop_images', 'source')
    op.drop_column('laptop_images', 'file_size_bytes')
    op.drop_column('laptop_images', 'height')
    op.drop_column('laptop_images', 'width')
    op.drop_column('laptop_images', 'is_remote')
    op.drop_column('laptop_images', 'medium_url')
    op.drop_column('laptop_images', 'thumb_url')
    op.drop_column('laptop_images', 'image_url')
    
    # laptops
    op.drop_column('laptops', 'last_icecat_sync')
    op.drop_column('laptops', 'currency')
    op.drop_column('laptops', 'msrp')
    op.drop_column('laptops', 'warranty_type')
    op.drop_column('laptops', 'warranty_months')
    op.drop_column('laptops', 'chassis_material')
    op.drop_column('laptops', 'color')
    op.drop_column('laptops', 'battery_cells')
    op.drop_column('laptops', 'battery_wh')
    op.drop_column('laptops', 'height_mm')
    op.drop_column('laptops', 'depth_mm')
    op.drop_column('laptops', 'width_mm')
    op.drop_column('laptops', 'weight_kg')
    op.drop_column('laptops', 'wireless_connectivity')
    op.drop_column('laptops', 'ir_camera')
    op.drop_column('laptops', 'fingerprint_reader')
    op.drop_column('laptops', 'keyboard_backlit')
    op.drop_column('laptops', 'seo_keywords')
    op.drop_index('idx_laptop_data_source', table_name='laptops')
    op.drop_column('laptops', 'modified_fields_json')
    op.drop_column('laptops', 'data_source')
    op.drop_index('idx_laptop_mpn', table_name='laptops')
    op.drop_index('idx_laptop_gtin', table_name='laptops')
    op.drop_column('laptops', 'upc')
    op.drop_column('laptops', 'mpn')
    op.drop_column('laptops', 'gtin')
    op.drop_index('idx_laptop_icecat_data', table_name='laptops')
    op.drop_constraint('fk_laptops_icecat_data', 'laptops', type_='foreignkey')
    op.drop_column('laptops', 'icecat_data_id')
    
    # icecat_product_data
    op.drop_index('idx_icecat_data_product_code', table_name='icecat_product_data')
    op.drop_index('idx_icecat_data_gtin', table_name='icecat_product_data')
    op.drop_index('idx_icecat_data_icecat_id', table_name='icecat_product_data')
    op.drop_table('icecat_product_data')
