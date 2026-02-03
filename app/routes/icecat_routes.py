# -*- coding: utf-8 -*-
# ============================================
# RUTAS API PARA INTEGRACIÓN CON ICECAT
# ============================================
# Endpoints para buscar productos en Icecat e importar datos

import logging
import os
import requests
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.utils.decorators import permission_required
from app.services.icecat_service import get_icecat_service, IcecatService, IcecatConfig
from app import db
from app.models.laptop import (
    Laptop, LaptopImage, Brand, LaptopModel, Processor, 
    OperatingSystem, Screen, GraphicsCard, Storage, Ram
)
from app.services.catalog_service import CatalogService
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import json

logger = logging.getLogger(__name__)

# Crear Blueprint
icecat_bp = Blueprint('icecat', __name__, url_prefix='/icecat')

# Configuración para descarga de imágenes
UPLOAD_FOLDER = 'static/uploads/laptops'
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}


# ===== FORMULARIO DE BÚSQUEDA =====

@icecat_bp.route('/', methods=['GET'])
@login_required
@permission_required('inventory.laptops.create')
def icecat_search_form():
    """
    Muestra el formulario de búsqueda de productos en Icecat
    """
    return render_template('inventory/icecat_search.html')


# ===== API: BUSCAR POR GTIN =====

@icecat_bp.route('/api/search/gtin', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def search_by_gtin():
    """
    Busca un producto en Icecat por código GTIN/EAN/UPC
    
    JSON Body:
    {
        "gtin": "0123456789012",
        "language": "ES"  // opcional
    }
    """
    data = request.get_json()
    
    if not data or not data.get('gtin'):
        return jsonify({
            'success': False,
            'error': 'El código GTIN/EAN es requerido'
        }), 400
    
    gtin = data['gtin'].strip()
    language = data.get('language', 'ES')
    
    # Validar formato de GTIN
    if not gtin.isdigit() or len(gtin) not in [8, 12, 13, 14]:
        return jsonify({
            'success': False,
            'error': 'El código GTIN debe ser numérico y tener 8, 12, 13 o 14 dígitos'
        }), 400
    
    try:
        service = get_icecat_service()
        success, result = service.search_by_gtin(gtin, language)
        
        if success:
            # Mapear a formato de laptop
            mapped_data = service.map_to_laptop_data(result)
            return jsonify({
                'success': True,
                'product': _serialize_product(result),
                'mapped_data': mapped_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 404
            
    except Exception as e:
        logger.error(f"Error en búsqueda por GTIN: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500


# ===== API: BUSCAR POR MARCA Y CÓDIGO =====

@icecat_bp.route('/api/search/brand-code', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def search_by_brand_code():
    """
    Busca un producto en Icecat por marca y código de producto
    
    JSON Body:
    {
        "brand": "Dell",
        "product_code": "XPS-15-9520",
        "language": "ES"  // opcional
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Datos no proporcionados'
        }), 400
    
    brand = data.get('brand', '').strip()
    product_code = data.get('product_code', '').strip()
    language = data.get('language', 'ES')
    
    if not brand:
        return jsonify({
            'success': False,
            'error': 'La marca es requerida'
        }), 400
    
    if not product_code:
        return jsonify({
            'success': False,
            'error': 'El código de producto es requerido'
        }), 400
    
    try:
        service = get_icecat_service()
        success, result = service.search_by_brand_code(brand, product_code, language)
        
        if success:
            mapped_data = service.map_to_laptop_data(result)
            return jsonify({
                'success': True,
                'product': _serialize_product(result),
                'mapped_data': mapped_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 404
            
    except Exception as e:
        logger.error(f"Error en búsqueda por marca/código: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500


# ===== API: BUSCAR POR ID DE ICECAT =====

@icecat_bp.route('/api/search/id', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def search_by_icecat_id():
    """
    Busca un producto en Icecat por su ID interno
    
    JSON Body:
    {
        "icecat_id": 12345678,
        "language": "ES"  // opcional
    }
    """
    data = request.get_json()
    
    if not data or not data.get('icecat_id'):
        return jsonify({
            'success': False,
            'error': 'El ID de Icecat es requerido'
        }), 400
    
    try:
        icecat_id = int(data['icecat_id'])
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'El ID debe ser un número válido'
        }), 400
    
    language = data.get('language', 'ES')
    
    try:
        service = get_icecat_service()
        success, result = service.search_by_icecat_id(icecat_id, language)
        
        if success:
            mapped_data = service.map_to_laptop_data(result)
            return jsonify({
                'success': True,
                'product': _serialize_product(result),
                'mapped_data': mapped_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 404
            
    except Exception as e:
        logger.error(f"Error en búsqueda por ID: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500


# ===== API: IMPORTAR IMÁGENES =====

@icecat_bp.route('/api/import-images', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def import_images():
    """
    Descarga e importa imágenes seleccionadas de Icecat
    
    JSON Body:
    {
        "laptop_id": 123,  // opcional, si se quiere asociar a laptop existente
        "images": [
            {"url": "https://...", "position": 0, "is_cover": true},
            {"url": "https://...", "position": 1, "is_cover": false}
        ]
    }
    """
    data = request.get_json()
    
    if not data or not data.get('images'):
        return jsonify({
            'success': False,
            'error': 'No se proporcionaron imágenes para importar'
        }), 400
    
    images_data = data['images']
    laptop_id = data.get('laptop_id')
    
    imported_images = []
    errors = []
    
    for idx, img_info in enumerate(images_data):
        url = img_info.get('url')
        if not url:
            continue
        
        try:
            # Descargar la imagen
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determinar extensión
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            ext = 'jpg'
            if 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            elif 'gif' in content_type:
                ext = 'gif'
            
            # Generar nombre único
            filename = f"icecat_{uuid.uuid4().hex[:8]}_{idx}.{ext}"
            
            # Crear directorio si no existe
            if laptop_id:
                save_dir = os.path.join('app', UPLOAD_FOLDER, str(laptop_id))
            else:
                save_dir = os.path.join('app', UPLOAD_FOLDER, 'temp_imports')
            
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)
            
            # Guardar imagen
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Ruta relativa para la DB
            relative_path = filepath.replace('app/', '').replace('app\\', '')
            
            imported_images.append({
                'filename': filename,
                'path': relative_path,
                'position': img_info.get('position', idx),
                'is_cover': img_info.get('is_cover', False),
                'original_url': url
            })
            
            logger.info(f"Imagen importada: {filename} desde {url}")
            
        except Exception as e:
            logger.error(f"Error importando imagen {url}: {e}")
            errors.append({
                'url': url,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'imported': imported_images,
        'errors': errors,
        'message': f'Se importaron {len(imported_images)} imágenes' + 
                   (f', {len(errors)} fallaron' if errors else '')
    })


# ===== API: CREAR LAPTOP DESDE ICECAT =====

@icecat_bp.route('/api/create-laptop', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def create_laptop_from_icecat():
    """
    Crea una nueva laptop a partir de datos de Icecat
    Los datos vienen pre-procesados del frontend con los ajustes del usuario
    
    JSON Body:
    {
        "icecat_id": 12345,
        "display_name": "Dell XPS 15",
        "short_description": "...",
        "long_description_html": "...",
        "brand_id": 1,
        "model_id": 2,
        "processor_id": 3,
        // ... otros campos del modelo Laptop
        "images": [
            {"path": "uploads/...", "position": 0, "is_cover": true}
        ]
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No se proporcionaron datos'
        }), 400
    
    try:
        # Importar aquí para evitar circular imports
        from app.services.sku_service import SKUService
        from app.routes.inventory import generate_slug, ensure_unique_slug
        
        # Generar SKU
        sku = SKUService.generate_laptop_sku()
        
        # Generar slug
        display_name = data.get('display_name', 'Producto Icecat')
        base_slug = generate_slug(display_name)
        slug = ensure_unique_slug(base_slug)
        
        # Crear el objeto Laptop
        laptop = Laptop(
            sku=sku,
            slug=slug,
            display_name=display_name,
            short_description=data.get('short_description', '')[:300],
            long_description_html=data.get('long_description_html', ''),
            
            # IDs de catálogos (deben venir ya seleccionados por el usuario)
            brand_id=data.get('brand_id'),
            model_id=data.get('model_id'),
            processor_id=data.get('processor_id'),
            os_id=data.get('os_id'),
            screen_id=data.get('screen_id'),
            graphics_card_id=data.get('graphics_card_id'),
            storage_id=data.get('storage_id'),
            ram_id=data.get('ram_id'),
            store_id=data.get('store_id'),
            location_id=data.get('location_id'),
            supplier_id=data.get('supplier_id'),
            
            # Detalles técnicos
            npu=data.get('npu', False),
            storage_upgradeable=data.get('storage_upgradeable', False),
            ram_upgradeable=data.get('ram_upgradeable', False),
            keyboard_layout=data.get('keyboard_layout', 'US'),
            connectivity_ports=data.get('connectivity_ports', {}),
            
            # Estado
            category=data.get('category', 'laptop'),
            condition=data.get('condition', 'new'),
            
            # Financieros
            purchase_cost=data.get('purchase_cost', 0),
            sale_price=data.get('sale_price', 0),
            discount_price=data.get('discount_price'),
            tax_percent=data.get('tax_percent', 0),
            
            # Inventario
            quantity=data.get('quantity', 1),
            reserved_quantity=0,
            min_alert=data.get('min_alert', 1),
            
            # Notas
            internal_notes=f"Importado desde Icecat ID: {data.get('icecat_id', 'N/A')}\n" + 
                          (data.get('internal_notes', '') or ''),
            
            # Usuario creador
            created_by_id=current_user.id
        )
        
        db.session.add(laptop)
        db.session.flush()  # Para obtener el ID
        
        # Procesar imágenes importadas
        images_data = data.get('images', [])
        for img_info in images_data:
            if img_info.get('path'):
                image = LaptopImage(
                    laptop_id=laptop.id,
                    image_path=img_info['path'],
                    position=img_info.get('position', 0),
                    alt_text=f"{display_name} - Imagen {img_info.get('position', 0) + 1}",
                    is_cover=img_info.get('is_cover', False),
                    ordering=img_info.get('position', 0)
                )
                db.session.add(image)
        
        db.session.commit()
        
        logger.info(f"Laptop creada desde Icecat: {laptop.sku} (ID: {laptop.id})")
        
        return jsonify({
            'success': True,
            'laptop_id': laptop.id,
            'sku': laptop.sku,
            'message': f'Laptop {laptop.sku} creada exitosamente',
            'redirect_url': url_for('inventory.laptop_detail', id=laptop.id)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando laptop desde Icecat: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error al crear laptop: {str(e)}'
        }), 500


# ===== API: OBTENER O CREAR CATÁLOGO =====

@icecat_bp.route('/api/catalog/get-or-create', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def get_or_create_catalog():
    """
    Obtiene o crea un item de catálogo (marca, procesador, etc.)
    
    JSON Body:
    {
        "catalog_type": "brand",  // brand, model, processor, os, screen, graphics, storage, ram
        "name": "Dell",
        "brand_id": 1  // opcional, solo para modelos
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400
    
    catalog_type = data.get('catalog_type')
    name = data.get('name', '').strip()
    
    if not catalog_type or not name:
        return jsonify({
            'success': False,
            'error': 'Tipo de catálogo y nombre son requeridos'
        }), 400
    
    # Mapeo de tipos a modelos
    catalog_models = {
        'brand': Brand,
        'model': LaptopModel,
        'processor': Processor,
        'os': OperatingSystem,
        'screen': Screen,
        'graphics': GraphicsCard,
        'storage': Storage,
        'ram': Ram
    }
    
    Model = catalog_models.get(catalog_type)
    if not Model:
        return jsonify({
            'success': False,
            'error': f'Tipo de catálogo no válido: {catalog_type}'
        }), 400
    
    try:
        # Buscar existente
        item = Model.query.filter(Model.name.ilike(name)).first()
        
        if item:
            return jsonify({
                'success': True,
                'created': False,
                'id': item.id,
                'name': item.name
            })
        
        # Crear nuevo
        if catalog_type == 'model':
            brand_id = data.get('brand_id')
            item = Model(name=name, brand_id=brand_id, is_active=True)
        else:
            item = Model(name=name, is_active=True)
        
        db.session.add(item)
        db.session.commit()
        
        logger.info(f"Catálogo creado: {catalog_type} -> {name} (ID: {item.id})")
        
        return jsonify({
            'success': True,
            'created': True,
            'id': item.id,
            'name': item.name
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando catálogo {catalog_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== API: CONFIGURAR CREDENCIALES =====

@icecat_bp.route('/api/config', methods=['GET', 'POST'])
@login_required
@permission_required('admin.settings')
def icecat_config():
    """
    GET: Obtiene la configuración actual de Icecat (sin tokens sensibles)
    POST: Actualiza la configuración de Icecat
    """
    if request.method == 'GET':
        service = get_icecat_service()
        return jsonify({
            'success': True,
            'config': {
                'username': service.config.username,
                'has_api_token': bool(service.config.api_token),
                'has_content_token': bool(service.config.content_token),
                'default_language': service.config.default_language,
                'base_url': service.config.base_url
            }
        })
    
    # POST - Actualizar configuración
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400
    
    # Aquí se podría guardar en la base de datos o archivo de configuración
    # Por ahora solo actualizamos las variables de entorno en memoria
    
    if data.get('username'):
        os.environ['ICECAT_USERNAME'] = data['username']
    if data.get('api_token'):
        os.environ['ICECAT_API_TOKEN'] = data['api_token']
    if data.get('content_token'):
        os.environ['ICECAT_CONTENT_TOKEN'] = data['content_token']
    if data.get('language'):
        os.environ['ICECAT_LANGUAGE'] = data['language']
    
    # Reiniciar el servicio con la nueva configuración
    global _icecat_service_instance
    from app.services.icecat_service import _icecat_service_instance
    _icecat_service_instance = None
    
    return jsonify({
        'success': True,
        'message': 'Configuración actualizada'
    })


# ===== HELPER: SERIALIZAR PRODUCTO =====

def _serialize_product(product) -> dict:
    """Serializa un IcecatProduct a diccionario para JSON"""
    return {
        'icecat_id': product.icecat_id,
        'brand': product.brand,
        'brand_id': product.brand_id,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'title': product.title,
        'category': product.category,
        'category_id': product.category_id,
        'gtin': product.gtin,
        'gtins': product.gtins,
        'short_description': product.short_description,
        'long_description': product.long_description,
        'summary_short': product.summary_short,
        'summary_long': product.summary_long,
        'main_image': _serialize_image(product.main_image) if product.main_image else None,
        'gallery': [_serialize_image(img) for img in product.gallery],
        'feature_groups': {
            group: [
                {'name': f.name, 'value': f.value, 'measure': f.measure}
                for f in features
            ]
            for group, features in product.feature_groups.items()
        },
        'release_date': product.release_date,
        'warranty_info': product.warranty_info
    }


def _serialize_image(image) -> dict:
    """Serializa una IcecatImage a diccionario"""
    return {
        'url': image.url,
        'thumb_url': image.thumb_url,
        'low_url': image.low_url,
        'medium_url': image.medium_url,
        'width': image.width,
        'height': image.height,
        'size': image.size,
        'is_main': image.is_main,
        'position': image.position,
        'image_type': image.image_type
    }
