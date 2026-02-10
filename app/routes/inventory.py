# -*- coding: utf-8 -*-
# ============================================
# RUTAS DE INVENTARIO - LAPTOPS
# ============================================
# Actualizado con sistema hÃ­brido de imÃ¡genes

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.laptop import (
    Laptop, LaptopImage, Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)
from app.models.serial import LaptopSerial, SERIAL_STATUS_CHOICES
from app.forms.laptop_forms import LaptopForm, FilterForm
from app.services.sku_service import SKUService
from app.services.catalog_service import CatalogService
from app.services.serial_service import SerialService
from app.services.laptop_image_service import LaptopImageService
from app.utils.task_manager import TaskManager
from app.utils.decorators import admin_required, permission_required, any_permission_required
from datetime import datetime, date
from sqlalchemy import or_
import re
import os
import json
from werkzeug.utils import secure_filename
from PIL import Image  # Importar PIL para procesamiento de imÃ¡genes

# Configurar logging
logger = logging.getLogger(__name__)

# Crear Blueprint
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# ConfiguraciÃ³n de imÃ¡genes
UPLOAD_FOLDER = 'static/uploads/laptops'
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'avif'}


# ===== UTILIDADES =====

def generate_slug(text):
    """
    Genera un slug URL-friendly a partir de texto

    Args:
        text: Texto a convertir en slug

    Returns:
        str: Slug generado
    """
    # Convertir a minusculas y reemplazar espacios
    slug = text.lower().strip()
    # Eliminar caracteres especiales, mantener solo alfanumericos y espacios
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Reemplazar espacios y guiones multiples con un solo guion
    slug = re.sub(r'[-\s]+', '-', slug)
    # Eliminar guiones al inicio y final
    slug = slug.strip('-')
    return slug


def ensure_unique_slug(base_slug, laptop_id=None):
    """
    Asegura que el slug sea unico

    Args:
        base_slug: Slug base
        laptop_id: ID de la laptop actual (para edicion)

    Returns:
        str: Slug unico
    """
    slug = base_slug
    counter = 1

    while True:
        query = Laptop.query.filter_by(slug=slug)
        if laptop_id:
            query = query.filter(Laptop.id != laptop_id)

        if not query.first():
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def process_connectivity_ports(form_data):
    """
    Procesa los puertos de conectividad del formulario

    Args:
        form_data: Lista de puertos seleccionados

    Returns:
        dict: Diccionario con los puertos y sus cantidades
    """
    if not form_data:
        return {}

    # Si es una cadena (TextAreaField), separar por comas
    if isinstance(form_data, str):
        ports_list = [p.strip() for p in form_data.split(',') if p.strip()]
        # Usar el texto completo como llave y 1 como valor dummy
        return {port: 1 for port in ports_list}

    # Si es una lista (SelectMultipleField - Legacy o futuro), contar ocurrencias
    ports = {}
    for port in form_data:
        ports[port] = ports.get(port, 0) + 1

    return ports


def allowed_image_file(filename):
    """
    Verifica si el archivo tiene una extensiÃ³n de imagen permitida

    Args:
        filename: Nombre del archivo

    Returns:
        bool: True si es permitido, False si no
    """
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def validate_serial_quantity(quantity, serials_data, mode='add', laptop_id=None):
    """
    Valida que la cantidad de seriales coincida con la cantidad en inventario.

    Args:
        quantity: Cantidad en inventario
        serials_data: Lista de seriales del formulario
        mode: 'add' o 'edit'
        laptop_id: ID de la laptop (para modo ediciÃ³n)

    Returns:
        tuple: (es_valido, mensaje_error)
    """
    try:
        total_serials = len(serials_data)

        # En modo ediciÃ³n, contar seriales existentes + nuevos
        if mode == 'edit' and laptop_id:
            # Obtener seriales existentes para esta laptop
            existing_serials = SerialService.get_available_serials_for_laptop(laptop_id)
            existing_count = len(existing_serials)

            # Contar solo los nuevos seriales
            new_serial_numbers = {s['serial_number'] for s in serials_data if 'serial_number' in s}
            existing_serial_numbers = {s.serial_number for s in existing_serials}
            new_serials_count = len(new_serial_numbers - existing_serial_numbers)

            total_serials = existing_count + new_serials_count

        if total_serials > quantity:
            return False, f"La cantidad de seriales ({total_serials}) no puede ser mayor que la cantidad en inventario ({quantity})"

        if total_serials < quantity:
            return False, f"La cantidad de seriales ({total_serials}) no puede ser menor que la cantidad en inventario ({quantity}). Agrega mÃ¡s seriales o reduce la cantidad."

        return True, ""

    except Exception as e:
        return False, f"Error en validaciÃ³n: {str(e)}"


def process_laptop_images(laptop, form):
    """
    Procesa las imÃ¡genes del formulario (hÃ­brido: nuevas subidas + URLs de Icecat + existentes).
    Mantiene el orden exacto de los slots para asignar la portada correctamente.
    """
    success_count = 0
    error_messages = []
    
    # 1. Eliminar imÃ¡genes marcadas
    images_to_delete_json = request.form.get('images_to_delete', '[]')
    try:
        to_delete_ids = json.loads(images_to_delete_json)
        for img_id in to_delete_ids:
            img = LaptopImage.query.get(img_id)
            if img and img.laptop_id == laptop.id:
                try: 
                    from flask import current_app
                    full_path = os.path.join(current_app.root_path, 'static', img.image_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as e:
                    logger.error(f"Error al eliminar archivo fÃ­sico: {e}")
                db.session.delete(img)
    except: pass
    db.session.flush()

    # 2. Identificar todos los slots activos
    all_keys = set(request.files.keys()) | set(request.form.keys())
    image_slots = set()
    for k in all_keys:
        if k.startswith('image_'):
            try:
                parts = k.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    image_slots.add(int(parts[1]))
            except: pass
    
    sorted_slots = sorted(list(image_slots))
    
    # 3. Clasificar tareas por slot
    slot_tasks = {} # slot_id -> task_info
    icecat_download_tasks = [] # Lista para ThreadPoolExecutor
    
    for i in sorted_slots:
        file = request.files.get(f'image_{i}')
        url = request.form.get(f'image_{i}_url')
        image_id = request.form.get(f'image_{i}_id')
        alt_text = request.form.get(f'image_{i}_alt') or f"Imagen {i}"

        # Prioridad de procesamiento:
        # A. Archivo nuevo subido (Local upload)
        if file and file.filename:
            slot_tasks[i] = {
                'type': 'upload',
                'file': file,
                'alt': alt_text
            }
        # B. URL de Icecat (Requiere descarga)
        elif url and url.startswith('http'):
            slot_tasks[i] = {
                'type': 'icecat',
                'url': url,
                'alt': alt_text
            }
            icecat_download_tasks.append({'slot': i, 'url': url})
        # C. Imagen existente (Reordenamiento o cambio de alt)
        elif image_id:
            slot_tasks[i] = {
                'type': 'existing',
                'id': int(image_id),
                'alt': alt_text
            }

    # 4. Procesar imÃ¡genes en paralelo (Nuevas + Icecat)
    processed_images_dict = {} # slot -> img_obj
    
    # Identificar tareas para ejecuciÃ³n paralela
    new_tasks = {i: t for i, t in slot_tasks.items() if t['type'] in ['upload', 'icecat']}
    existing_tasks = {i: t for i, t in slot_tasks.items() if t['type'] == 'existing'}
    
    if new_tasks:
        from flask import current_app
        from concurrent.futures import ThreadPoolExecutor, as_completed
        app = current_app._get_current_object()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            # IMPORTANTE: db_session=False para obtener solo metadata y evitar conflictos de hilos
            future_to_slot = {
                executor.submit(
                    LaptopImageService.process_and_save_image,
                    laptop_id=laptop.id, sku=laptop.sku, 
                    source=task.get('file') or task.get('url'),
                    position=slot_id, is_cover=(slot_id == 1), 
                    alt_text=task['alt'],
                    db_session=False, # SOLO DISCO
                    app=app
                ): slot_id
                for slot_id, task in new_tasks.items()
            }
            
            for future in as_completed(future_to_slot):
                slot_id = future_to_slot[future]
                try:
                    result = future.result()
                    if result and isinstance(result, dict):
                        # Crear el objeto en el HILO PRINCIPAL para evitar errores de sesión
                        img_obj = LaptopImage(**result)
                        if new_tasks[slot_id]['type'] == 'icecat':
                            img_obj.source = 'icecat'
                        
                        db.session.add(img_obj)
                        processed_images_dict[slot_id] = img_obj
                        success_count += 1
                    else:
                        error_messages.append(f"Fallo al procesar imagen slot {slot_id}")
                except Exception as e:
                    error_messages.append(f"ExcepciÃ³n en slot {slot_id}: {str(e)}")

    # 5. Procesar imÃ¡genes existentes (Secuencial, es rÃ¡pido)
    for i, task in existing_tasks.items():
        img_obj = LaptopImage.query.get(task['id'])
        if img_obj and img_obj.laptop_id == laptop.id:
            img_obj.position = i
            img_obj.ordering = i
            img_obj.is_cover = (i == 1)
            if task['alt']: img_obj.alt_text = task['alt']
            processed_images_dict[i] = img_obj

    # Construir lista final en ORDEN
    processed_images = [processed_images_dict[i] for i in sorted_slots if i in processed_images_dict]

    # 6. Limpieza final: Eliminar imÃ¡genes que ya no estÃ¡n en la lista procesada
    db.session.flush()
    keep_ids = [img.id for img in processed_images if img and img.id]
    LaptopImageService.cleanup_laptop_images(laptop.id, keep_ids=keep_ids)

    # 7. Sincronizar positions y orderings por si hubo fallos intermedios
    for idx, img in enumerate(processed_images):
        img.position = idx + 1
        img.ordering = idx + 1
        img.is_cover = (idx == 0)

    try:
        db.session.flush()
        logger.info(f"âœ… GalerÃ­a procesada: {len(processed_images)} imÃ¡genes listas.")
    except Exception as e:
        logger.error(f"âŒ Error en flush final: {str(e)}")
        error_messages.append(f"Error guardando galerÃ­a: {str(e)}")

    return success_count, error_messages




# ===== RUTA PRINCIPAL: LISTADO DE LAPTOPS =====

@inventory_bp.route('/')
@login_required
@permission_required('inventory.laptops.view')
def laptops_list():
    """
    Muestra el listado principal de laptops con filtros y busqueda
    """
    # Obtener parametros de filtros
    store_filter = request.args.get('store', type=int, default=0)
    brand_filter = request.args.get('brand', type=int, default=0)
    category_filter = request.args.get('category', '')
    processor_filter = request.args.get('processor', '')
    generation_filter = request.args.get('generation', '')
    gpu_filter = request.args.get('gpu', type=int, default=0)
    screen_filter = request.args.get('screen', type=int, default=0)
    condition_filter = request.args.get('condition', '')
    supplier_filter = request.args.get('supplier', type=int, default=0)
    is_published_filter = request.args.get('is_published', '')
    is_featured_filter = request.args.get('is_featured', '')
    has_npu_filter = request.args.get('has_npu', '')
    min_price = request.args.get('min_price', type=float, default=0)
    max_price = request.args.get('max_price', type=float, default=0)
    search_query = request.args.get('q', '').strip()
    stock_status = request.args.get('stock_status', 'in_stock')
    sort_by = request.args.get('sort_by', 'entry_date_desc')

    # Paginacion
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Query base
    query = Laptop.query

    # Busqueda por texto
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                Laptop.sku.ilike(search_pattern),
                Laptop.display_name.ilike(search_pattern),
                Laptop.slug.ilike(search_pattern),
                Laptop.short_description.ilike(search_pattern)
            )
        )

    # Aplicar filtros
    if store_filter and store_filter > 0:
        query = query.filter(Laptop.store_id == store_filter)

    if brand_filter and brand_filter > 0:
        query = query.filter(Laptop.brand_id == brand_filter)

    if category_filter:
        query = query.filter(Laptop.category == category_filter)

    if processor_filter or generation_filter:
        query = query.join(Laptop.processor)
        if processor_filter:
            query = query.filter(Processor.family == processor_filter)
        if generation_filter:
            query = query.filter(Processor.name == generation_filter)

    if gpu_filter and gpu_filter > 0:
        query = query.filter(Laptop.graphics_card_id == gpu_filter)

    if screen_filter and screen_filter > 0:
        query = query.filter(Laptop.screen_id == screen_filter)

    if condition_filter:
        query = query.filter(Laptop.condition == condition_filter)

    if supplier_filter and supplier_filter > 0:
        query = query.filter(Laptop.supplier_id == supplier_filter)

    if is_published_filter:
        query = query.filter(Laptop.is_published == (is_published_filter == '1'))

    if is_featured_filter:
        query = query.filter(Laptop.is_featured == (is_featured_filter == '1'))

    if stock_status == 'in_stock':
        query = query.filter(Laptop.quantity > 0)
    elif stock_status == 'out_of_stock':
        query = query.filter(Laptop.quantity <= 0)

    if has_npu_filter:
        query = query.join(Laptop.processor).filter(Processor.has_npu == (has_npu_filter == '1'))

    if min_price > 0:
        query = query.filter(Laptop.sale_price >= min_price)

    if max_price > 0:
        query = query.filter(Laptop.sale_price <= max_price)

    # Ordenar segÃºn el filtro seleccionado
    if sort_by == 'entry_date_desc':
        query = query.order_by(Laptop.entry_date.desc())
    elif sort_by == 'entry_date_asc':
        query = query.order_by(Laptop.entry_date.asc())
    elif sort_by == 'sale_price_asc':
        query = query.order_by(Laptop.sale_price.asc())
    elif sort_by == 'sale_price_desc':
        query = query.order_by(Laptop.sale_price.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Laptop.display_name.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(Laptop.display_name.desc())
    elif sort_by == 'quantity_desc':
        query = query.order_by(Laptop.quantity.desc())
    elif sort_by == 'quantity_asc':
        query = query.order_by(Laptop.quantity.asc())
    elif sort_by == 'brand_asc':
        query = query.join(Laptop.brand).order_by(Brand.name.asc())
    elif sort_by == 'brand_desc':
        query = query.join(Laptop.brand).order_by(Brand.name.desc())
    elif sort_by == 'category_asc':
        query = query.order_by(Laptop.category.asc())
    elif sort_by == 'category_desc':
        query = query.order_by(Laptop.category.desc())
    elif sort_by == 'status_asc':
        query = query.order_by(Laptop.is_published.asc(), Laptop.is_featured.asc())
    elif sort_by == 'status_desc':
        query = query.order_by(Laptop.is_published.desc(), Laptop.is_featured.desc())
    else:
        # Orden por defecto
        query = query.order_by(Laptop.entry_date.desc())

    # Paginar
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    laptops = pagination.items

    # Calcular estadisticas GLOBALES (todas las laptops, no solo filtradas)
    all_laptops = Laptop.query.all()

    # VALOR TOTAL = suma del precio de venta * cantidad de TODAS las laptops
    total_inventory_value = sum(
        float(laptop.sale_price * laptop.quantity)
        for laptop in all_laptops
        if laptop.sale_price and laptop.quantity
    )

    # Contar laptops con stock bajo
    low_stock_count = len([l for l in all_laptops if l.is_low_stock])

    # Contar publicadas y destacadas
    published_count = len([l for l in all_laptops if l.is_published])
    featured_count = len([l for l in all_laptops if l.is_featured])

    stats = {
        'total': len(all_laptops),
        'total_value': total_inventory_value,
        'low_stock': low_stock_count,
        'published': published_count,
        'featured': featured_count
    }

    # Formularios
    filter_form = FilterForm()

    # Obtener rango de precios de la base de datos
    price_range = db.session.query(
        db.func.min(Laptop.sale_price),
        db.func.max(Laptop.sale_price)
    ).first()

    min_db_price = float(price_range[0]) if price_range[0] else 0
    max_db_price = float(price_range[1]) if price_range[1] else 10000

    return render_template(
        'inventory/laptops_list.html',
        laptops=laptops,
        pagination=pagination,
        stats=stats,
        filter_form=filter_form,
        min_db_price=min_db_price,
        max_db_price=max_db_price,
        search_query=search_query,
        sort_by=sort_by,
        stock_status=stock_status
    )


# ===== AGREGAR NUEVA LAPTOP =====

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('inventory.laptops.create')
def laptop_add():
    """
    Muestra el formulario y procesa la creacion de una nueva laptop
    """
    form = LaptopForm()

    if form.validate_on_submit():
        try:
            # Procesar catalogos dinamicos (crear si son strings)
            catalog_data = CatalogService.process_laptop_form_data({
                'brand_id': form.brand_id.data,
                'model_id': form.model_id.data,
                'processor_family': form.processor_family.data,
                'processor_generation': form.processor_generation.data,
                'processor_model': form.processor_model.data,
                'os_id': form.os_id.data,
                'screen_id': form.screen_id.data,
                'graphics_card_id': form.graphics_card_id.data,
                'storage_id': form.storage_id.data,
                'ram_id': form.ram_id.data,
                'store_id': form.store_id.data,
                'location_id': form.location_id.data,
                'supplier_id': form.supplier_id.data,
                
                # Campos granulares - Pantalla
                'screen_diagonal_inches': form.screen_diagonal_inches.data,
                'screen_resolution': form.screen_resolution.data,
                'screen_hd_type': form.screen_hd_type.data,
                'screen_panel_type': form.screen_panel_type.data,
                'screen_refresh_rate': form.screen_refresh_rate.data,
                'screen_touchscreen_override': form.screen_touchscreen_override.data,
                
                # Campos granulares - GPU
                'has_discrete_gpu': form.has_discrete_gpu.data,
                'discrete_gpu_brand': form.discrete_gpu_brand.data,
                'discrete_gpu_model': form.discrete_gpu_model.data,
                'discrete_gpu_memory_gb': form.discrete_gpu_memory_gb.data,
                'discrete_gpu_memory_type': form.discrete_gpu_memory_type.data,
                'onboard_gpu_brand': form.onboard_gpu_brand.data,
                'onboard_gpu_model': form.onboard_gpu_model.data,
                'onboard_gpu_family': form.onboard_gpu_family.data,
                
                # Campos granulares - Almacenamiento
                'storage_capacity': form.storage_capacity.data,
                'storage_media': form.storage_media.data,
                'storage_nvme': form.storage_nvme.data,
                'storage_form_factor': form.storage_form_factor.data,
                
                # Campos granulares - RAM
                'ram_capacity': form.ram_capacity.data,
                'ram_type_detailed': form.ram_type_detailed.data,
                'ram_speed_mhz': form.ram_speed_mhz.data,
                'ram_transfer_rate': form.ram_transfer_rate.data,
                'processor_full_name': form.processor_full_name.data,
                'screen_full_name': form.screen_full_name.data,
                'discrete_gpu_full_name': form.discrete_gpu_full_name.data,
                'onboard_gpu_full_name': form.onboard_gpu_full_name.data,
                'storage_full_name': form.storage_full_name.data,
                'ram_full_name': form.ram_full_name.data
            })

            # Generar SKU automaticamente
            sku = SKUService.generate_laptop_sku()

            # Generar slug
            if form.slug.data:
                slug = ensure_unique_slug(generate_slug(form.slug.data))
            else:
                slug = ensure_unique_slug(generate_slug(form.display_name.data))

            # Procesar puertos de conectividad
            connectivity_ports = process_connectivity_ports(form.connectivity_ports.data)

            # Crear nueva laptop
            laptop = Laptop(
                # Identificadores
                sku=sku,
                slug=slug,

                # Marketing y SEO
                display_name=form.display_name.data,
                short_description=form.short_description.data,
                long_description_html=form.long_description_html.data,
                is_published=form.is_published.data,
                is_featured=form.is_featured.data,
                seo_title=form.seo_title.data,
                seo_description=form.seo_description.data,

                # Relaciones
                brand_id=catalog_data['brand_id'],
                model_id=catalog_data['model_id'],
                processor_id=catalog_data['processor_id'],
                # processor fields removed (delegated to Processor model)
                os_id=catalog_data['os_id'],
                screen_id=catalog_data['screen_id'],
                graphics_card_id=catalog_data['graphics_card_id'],
                storage_id=catalog_data['storage_id'],
                ram_id=catalog_data['ram_id'],
                store_id=catalog_data['store_id'],
                location_id=catalog_data.get('location_id'),
                supplier_id=catalog_data.get('supplier_id'),

                # Campos adicionales
                gtin=form.gtin.data,
                keywords=form.keywords.data,
                warranty_months=form.warranty_months.data,
                warranty_expiry=form.warranty_expiry.data,
                public_notes=form.public_notes.data,
                pointing_device=form.pointing_device.data,
                keyboard_backlight_color=form.keyboard_backlight_color.data,
                keyboard_backlight_zone=form.keyboard_backlight_zone.data,

                # Detalles tecnicos
                npu=form.npu.data,
                storage_upgradeable=form.storage_upgradeable.data,
                ram_upgradeable=form.ram_upgradeable.data,
                touchscreen_override=form.screen_touchscreen_override.data,
                keyboard_layout=form.keyboard_layout.data,
                keyboard_backlight=form.keyboard_backlight.data,
                numeric_keypad=form.numeric_keypad.data,
                keyboard_language=form.keyboard_language.data,
                fingerprint_reader=form.fingerprint_reader.data,
                face_recognition=form.face_recognition.data,
                stylus_support=form.stylus_support.data,
                connectivity_ports=connectivity_ports,
                wifi_standard=form.wifi_standard.data,
                bluetooth_version=form.bluetooth_version.data,
                ethernet_port=form.ethernet_port.data,
                cellular=form.cellular.data,
                weight_lbs=form.weight_lbs.data,

                # Estado y categoria
                category=form.category.data,
                condition=form.condition.data,

                # Financieros
                purchase_cost=form.purchase_cost.data,
                sale_price=form.sale_price.data,
                discount_price=form.discount_price.data if form.discount_price.data else None,
                tax_percent=form.tax_percent.data if form.tax_percent.data else 0,

                # Inventario
                quantity=form.quantity.data,
                reserved_quantity=form.reserved_quantity.data if form.reserved_quantity.data else 0,
                min_alert=form.min_alert.data,

                # Timestamps
                entry_date=date.today(),
                sale_date=None,
                internal_notes=form.internal_notes.data,

                # Auditoria
                created_by_id=current_user.id
            )

            # Guardar en base de datos
            db.session.add(laptop)
            db.session.flush()  # Para obtener el ID

            # PROCESAR SERIALES - CON MEJOR MANEJO DE ERRORES
            serials_json = request.form.get('serials_json', '[]')
            serial_errors = []

            try:
                serials_data = json.loads(serials_json)

                # Validar cantidad de seriales vs inventario
                is_valid, error_msg = validate_serial_quantity(
                    quantity=form.quantity.data,
                    serials_data=serials_data,
                    mode='add'
                )

                if not is_valid:
                    db.session.rollback()
                    flash(f'âŒ {error_msg}', 'error')
                    return render_template('inventory/laptop_form.html', form=form, mode='add')

                for serial_info in serials_data:
                    serial_number = serial_info.get('serial_number', '').strip().upper()
                    if serial_number:
                        success, result = SerialService.create_serial(  # CAMBIADO: Capturar retorno
                            laptop_id=laptop.id,
                            serial_number=serial_number,
                            created_by_id=current_user.id
                        )

                        if not success:  # NUEVO: Verificar si hubo error
                            serial_errors.append(f"Serial {serial_number}: {result}")
                            logger.error(f"Error al crear serial {serial_number}: {result}")

            except Exception as e:
                logger.error(f"Error procesando seriales: {str(e)}")
                serial_errors.append(f"Error general: {str(e)}")

            # Si hubo errores en seriales, hacer rollback y mostrar
            if serial_errors:
                db.session.rollback()
                error_msg = "Errores al guardar seriales:<br>" + "<br>".join(serial_errors)
                flash(f'âŒ {error_msg}', 'error')
                return render_template('inventory/laptop_form.html', form=form, mode='add')

            # Procesar imÃ¡genes
            # Si hay URLs de Icecat pero no imÃ¡genes locales nuevas, podemos hacerlo en background
            icecat_urls = catalog_data.get('images', []) if 'catalog_data' in locals() else []
            
            # Solo si NO hay archivos subidos manualmente, lo hacemos en background
            manual_files = [f for f in request.files if f.startswith('image_') and request.files[f].filename]
            
            if icecat_urls and not manual_files:
                from flask import current_app
                app = current_app._get_current_object()
                TaskManager.run_async(
                    LaptopImageService.background_save_icecat_images,
                    laptop_id=laptop.id, 
                    sku=laptop.sku, 
                    image_urls=icecat_urls,
                    app=app
                )
                img_success = len(icecat_urls) # Estimado para el mensaje
                img_errors = []
            else:
                img_success, img_errors = process_laptop_images(laptop, form)
            
            db.session.commit()

            # Mensaje de Ã©xito
            if img_success > 0:
                flash(f'âœ… Laptop {sku} agregada con {img_success} imagen(es)', 'success')
            else:
                flash(f'âœ… Laptop {sku} agregada exitosamente', 'success')

            # Mostrar errores de imÃ¡genes si los hay
            for error in img_errors:
                flash(f'âš ï¸ {error}', 'warning')

            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al agregar laptop: {str(e)}', exc_info=True)
            flash(f'âŒ Error al agregar laptop: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    return render_template('inventory/laptop_form.html', form=form, mode='add')


# ===== VER DETALLE DE LAPTOP =====

@inventory_bp.route('/<int:id>')
@login_required
@permission_required('inventory.laptops.view')
def laptop_detail(id):
    """
    Muestra el detalle completo de una laptop
    """
    laptop = Laptop.query.get_or_404(id)

    # Obtener laptops similares (misma categoria y marca)
    similar_laptops = Laptop.query.filter(
        Laptop.category == laptop.category,
        Laptop.brand_id == laptop.brand_id,
        Laptop.id != laptop.id,
        Laptop.is_published == True
    ).limit(5).all()

    # CORRECCIÃ“N: Obtener imÃ¡genes ordenadas usando sorted() en lugar de order_by()
    # Â¡laptop.images es una lista, no un objeto Query!
    images = sorted(laptop.images, key=lambda img: img.ordering)

    # Imagen de portada
    cover_image = next((img for img in laptop.images if img.is_cover), None)

    return render_template(
        'inventory/laptop_detail.html',
        laptop=laptop,
        similar_laptops=similar_laptops,
        images=images,
        cover_image=cover_image
    )


# ===== VER LAPTOP POR SLUG (para URLs publicas) =====

@inventory_bp.route('/p/<slug>')
def laptop_by_slug(slug):
    """
    Muestra el detalle de una laptop por su slug (URL publica)
    """
    laptop = Laptop.query.filter_by(slug=slug, is_published=True).first_or_404()

    # Obtener laptops similares
    similar_laptops = Laptop.query.filter(
        Laptop.category == laptop.category,
        Laptop.brand_id == laptop.brand_id,
        Laptop.id != laptop.id,
        Laptop.is_published == True
    ).limit(5).all()

    # CORRECCIÃ“N: Obtener imÃ¡genes ordenadas usando sorted() en lugar de order_by()
    images = sorted(laptop.images, key=lambda img: img.ordering)
    cover_image = next((img for img in laptop.images if img.is_cover), None)

    return render_template(
        'inventory/laptop_public.html',
        laptop=laptop,
        similar_laptops=similar_laptops,
        images=images,
        cover_image=cover_image
    )


# ===== EDITAR LAPTOP =====

@inventory_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('inventory.laptops.edit')
def laptop_edit(id):
    """
    Edita una laptop existente
    """
    laptop = Laptop.query.get_or_404(id)
    form = LaptopForm(obj=laptop)
    
    # ===== CORRECCIÃ“N: Convertir IDs a nombres para mostrar en el formulario =====
    if request.method == 'GET':
        # Cargar nombres en lugar de IDs para los selects
        if laptop.brand_id:
            brand = Brand.query.get(laptop.brand_id)
            form.brand_id.data = brand.name if brand else str(laptop.brand_id)
        
        if laptop.model_id:
            model = LaptopModel.query.get(laptop.model_id)
            form.model_id.data = model.name if model else str(laptop.model_id)
        
        if laptop.processor_id:
            processor = Processor.query.get(laptop.processor_id)
            if processor:
                form.processor_family.data = processor.family
                form.processor_generation.data = processor.generation
                form.processor_model.data = processor.model_number
                form.processor_full_name.data = processor.full_name
        
        if laptop.os_id:
            os_obj = OperatingSystem.query.get(laptop.os_id)
            form.os_id.data = os_obj.name if os_obj else str(laptop.os_id)
        
        if laptop.screen_id:
            screen = Screen.query.get(laptop.screen_id)
            if screen:
                form.screen_id.data = screen.name
                form.screen_resolution.data = screen.resolution
                form.screen_diagonal_inches.data = screen.diagonal_inches
                form.screen_hd_type.data = screen.hd_type
                form.screen_panel_type.data = screen.panel_type
                form.screen_refresh_rate.data = screen.refresh_rate
                form.screen_touchscreen_override.data = laptop.touchscreen # Usar el override del laptop
                form.screen_full_name.data = laptop.screen_full_name
            else:
                form.screen_id.data = str(laptop.screen_id)
        
        if laptop.graphics_card_id:
            gpu = GraphicsCard.query.get(laptop.graphics_card_id)
            if gpu:
                form.graphics_card_id.data = gpu.name
                form.has_discrete_gpu.data = gpu.has_discrete_gpu
                form.discrete_gpu_brand.data = gpu.discrete_brand
                form.discrete_gpu_model.data = gpu.discrete_model
                form.discrete_gpu_memory_gb.data = gpu.discrete_memory_gb
                form.discrete_gpu_memory_type.data = gpu.discrete_memory_type
                form.onboard_gpu_brand.data = gpu.onboard_brand
                form.onboard_gpu_model.data = gpu.onboard_model
                form.onboard_gpu_family.data = gpu.onboard_family
                form.discrete_gpu_full_name.data = laptop.discrete_gpu_full_name
                form.onboard_gpu_full_name.data = laptop.onboard_gpu_full_name
            else:
                form.graphics_card_id.data = str(laptop.graphics_card_id)
        
        if laptop.storage_id:
            storage = Storage.query.get(laptop.storage_id)
            if storage:
                form.storage_id.data = storage.name
                form.storage_capacity.data = storage.capacity_gb
                form.storage_media.data = storage.media_type
                form.storage_nvme.data = storage.nvme
                form.storage_form_factor.data = storage.form_factor
                form.storage_full_name.data = laptop.storage_full_name
            else:
                form.storage_id.data = str(laptop.storage_id)
        
        if laptop.ram_id:
            ram = Ram.query.get(laptop.ram_id)
            if ram:
                form.ram_id.data = ram.name
                form.ram_capacity.data = ram.capacity_gb
                form.ram_type_detailed.data = ram.ram_type
                form.ram_speed_mhz.data = ram.speed_mhz
                form.ram_transfer_rate.data = ram.transfer_rate
                form.ram_full_name.data = laptop.ram_full_name
            else:
                form.ram_id.data = str(laptop.ram_id)

    # Pre-poblar connectivity_ports si existe
    if request.method == 'GET' and laptop.connectivity_ports:
        # CORRECCIÃ“N: Convertir las llaves del diccionario a un string separado por comas
        # Esto es lo que espera un TextAreaField, no una lista
        keys_list = list(laptop.connectivity_ports.keys())
        form.connectivity_ports.data = ", ".join(keys_list)

    if form.validate_on_submit():
        try:
            # Procesar catalogos dinamicos
            catalog_data = CatalogService.process_laptop_form_data({
                'brand_id': form.brand_id.data,
                'model_id': form.model_id.data,
                'processor_family': form.processor_family.data,
                'processor_generation': form.processor_generation.data,
                'processor_model': form.processor_model.data,
                'os_id': form.os_id.data,
                'screen_id': form.screen_id.data,
                'graphics_card_id': form.graphics_card_id.data,
                'storage_id': form.storage_id.data,
                'ram_id': form.ram_id.data,
                'store_id': form.store_id.data,
                'location_id': form.location_id.data,
                'supplier_id': form.supplier_id.data,
                
                # Campos granulares - Pantalla
                'screen_diagonal_inches': form.screen_diagonal_inches.data,
                'screen_resolution': form.screen_resolution.data,
                'screen_hd_type': form.screen_hd_type.data,
                'screen_panel_type': form.screen_panel_type.data,
                'screen_refresh_rate': form.screen_refresh_rate.data,
                'screen_touchscreen_override': form.screen_touchscreen_override.data,
                
                # Campos granulares - GPU
                'has_discrete_gpu': form.has_discrete_gpu.data,
                'discrete_gpu_brand': form.discrete_gpu_brand.data,
                'discrete_gpu_model': form.discrete_gpu_model.data,
                'discrete_gpu_memory_gb': form.discrete_gpu_memory_gb.data,
                'discrete_gpu_memory_type': form.discrete_gpu_memory_type.data,
                'onboard_gpu_brand': form.onboard_gpu_brand.data,
                'onboard_gpu_model': form.onboard_gpu_model.data,
                'onboard_gpu_family': form.onboard_gpu_family.data,
                
                # Campos granulares - Almacenamiento
                'storage_capacity': form.storage_capacity.data,
                'storage_media': form.storage_media.data,
                'storage_nvme': form.storage_nvme.data,
                'storage_form_factor': form.storage_form_factor.data,
                
                # Campos granulares - RAM
                'ram_capacity': form.ram_capacity.data,
                'ram_type_detailed': form.ram_type_detailed.data,
                'ram_speed_mhz': form.ram_speed_mhz.data,
                'ram_transfer_rate': form.ram_transfer_rate.data,
                'processor_full_name': form.processor_full_name.data,
                'screen_full_name': form.screen_full_name.data,
                'discrete_gpu_full_name': form.discrete_gpu_full_name.data,
                'onboard_gpu_full_name': form.onboard_gpu_full_name.data,
                'storage_full_name': form.storage_full_name.data,
                'ram_full_name': form.ram_full_name.data
            })

            # Actualizar slug
            if form.slug.data:
                sanitized_slug = generate_slug(form.slug.data)
                laptop.slug = ensure_unique_slug(sanitized_slug, laptop.id)
            elif form.display_name.data != laptop.display_name:
                base_slug = generate_slug(form.display_name.data)
                laptop.slug = ensure_unique_slug(base_slug, laptop.id)

            # Procesar puertos de conectividad
            connectivity_ports = process_connectivity_ports(form.connectivity_ports.data)

            # Actualizar campos
            # Marketing y SEO
            laptop.display_name = form.display_name.data
            laptop.short_description = form.short_description.data
            laptop.long_description_html = form.long_description_html.data
            laptop.is_published = form.is_published.data
            laptop.is_featured = form.is_featured.data
            laptop.seo_title = form.seo_title.data
            laptop.seo_description = form.seo_description.data

            # Relaciones
            laptop.brand_id = catalog_data['brand_id']
            laptop.model_id = catalog_data['model_id']
            laptop.processor_id = catalog_data['processor_id']
            # processor fields removed (delegated to Processor model)
            # laptop.processor_family = form.processor_family.data
            # laptop.processor_generation = form.processor_generation.data
            # laptop.processor_model = form.processor_model.data
            # laptop.processor_full_name = form.processor_full_name.data
              
            # Add missing fields
            laptop.gtin = form.gtin.data
            laptop.keywords = form.keywords.data
            laptop.warranty_months = form.warranty_months.data
            laptop.warranty_expiry = form.warranty_expiry.data
            laptop.public_notes = form.public_notes.data
            laptop.pointing_device = form.pointing_device.data
            laptop.keyboard_backlight_color = form.keyboard_backlight_color.data
            laptop.keyboard_backlight_zone = form.keyboard_backlight_zone.data
            laptop.os_id = catalog_data['os_id']
            laptop.screen_id = catalog_data['screen_id']
            laptop.graphics_card_id = catalog_data['graphics_card_id']
            laptop.storage_id = catalog_data['storage_id']
            laptop.ram_id = catalog_data['ram_id']
            laptop.store_id = catalog_data['store_id']
            laptop.location_id = catalog_data.get('location_id')
            laptop.supplier_id = catalog_data.get('supplier_id')

            # Detalles tecnicos
            laptop.npu = form.npu.data
            laptop.storage_upgradeable = form.storage_upgradeable.data
            laptop.ram_upgradeable = form.ram_upgradeable.data
            laptop.touchscreen_override = form.screen_touchscreen_override.data
            laptop.keyboard_layout = form.keyboard_layout.data
            laptop.keyboard_backlight = form.keyboard_backlight.data
            laptop.numeric_keypad = form.numeric_keypad.data
            laptop.keyboard_language = form.keyboard_language.data
            laptop.fingerprint_reader = form.fingerprint_reader.data
            laptop.face_recognition = form.face_recognition.data
            laptop.stylus_support = form.stylus_support.data
            laptop.connectivity_ports = connectivity_ports
            laptop.wifi_standard = form.wifi_standard.data
            laptop.bluetooth_version = form.bluetooth_version.data
            laptop.ethernet_port = form.ethernet_port.data
            laptop.cellular = form.cellular.data
            laptop.weight_lbs = form.weight_lbs.data

            # Estado y categoria
            laptop.category = form.category.data
            laptop.condition = form.condition.data

            # Financieros
            laptop.purchase_cost = form.purchase_cost.data
            laptop.sale_price = form.sale_price.data
            laptop.discount_price = form.discount_price.data if form.discount_price.data else None
            laptop.tax_percent = form.tax_percent.data if form.tax_percent.data else 0

            # Inventario
            laptop.quantity = form.quantity.data
            laptop.reserved_quantity = form.reserved_quantity.data if form.reserved_quantity.data else 0
            laptop.min_alert = form.min_alert.data

            # Notas
            laptop.internal_notes = form.internal_notes.data

            laptop.updated_at = datetime.utcnow()

            # ===== PROCESAR SERIALES EN MODO EDICIÃ“N =====
            serials_json = request.form.get('serials_json', '[]')
            serial_errors = []

            # Validar cantidad de seriales vs inventario (en modo ediciÃ³n)
            try:
                serials_data = json.loads(serials_json)
                is_valid, error_msg = validate_serial_quantity(
                    quantity=form.quantity.data,
                    serials_data=serials_data,
                    mode='edit',
                    laptop_id=laptop.id
                )

                if not is_valid:
                    db.session.rollback()
                    flash(f'âŒ {error_msg}', 'error')
                    return render_template('inventory/laptop_form.html', form=form, mode='edit', laptop=laptop)

                # Obtener seriales existentes para esta laptop
                existing_serials = SerialService.get_available_serials_for_laptop(laptop.id)
                existing_serial_numbers = {s.serial_number for s in existing_serials}
                submitted_serial_numbers = {s['serial_number'] for s in serials_data if 'serial_number' in s}

                # Identificar seriales a eliminar (estÃ¡n en BD pero no en formulario)
                serials_to_delete = existing_serial_numbers - submitted_serial_numbers

                # Identificar seriales a agregar (estÃ¡n en formulario pero no en BD)
                serials_to_add = submitted_serial_numbers - existing_serial_numbers

                # Validar que no se eliminen seriales vendidos
                for serial_number in list(serials_to_delete):
                    serial = SerialService.find_by_serial(serial_number)
                    if serial and serial.status == 'sold':
                        serial_errors.append(f"No se puede eliminar el serial {serial_number} porque ya fue vendido")
                        serials_to_delete.remove(serial_number)

                # Eliminar seriales marcados para eliminar
                for serial_number in serials_to_delete:
                    serial = SerialService.find_by_serial(serial_number)
                    if serial and serial.laptop_id == laptop.id:
                        success, error = SerialService.delete_serial(serial.id, user_id=current_user.id)
                        if not success:
                            serial_errors.append(f"Error al eliminar serial {serial_number}: {error}")

                # Agregar nuevos seriales
                for serial_info in serials_data:
                    serial_number = serial_info.get('serial_number', '').strip().upper()
                    if serial_number in serials_to_add:
                        success, result = SerialService.create_serial(
                            laptop_id=laptop.id,
                            serial_number=serial_number,
                            created_by_id=current_user.id
                        )
                        if not success:
                            serial_errors.append(f"Serial {serial_number}: {result}")

            except Exception as e:
                logger.error(f"Error procesando seriales en ediciÃ³n: {str(e)}")
                serial_errors.append(f"Error general: {str(e)}")

            # Si hubo errores en seriales, mostrar pero no hacer rollback completo
            if serial_errors:
                for error in serial_errors:
                    flash(f'âš ï¸ {error}', 'warning')

            # Procesar imÃ¡genes
            img_success, img_errors = process_laptop_images(laptop, form)
            db.session.commit()

            # Mensaje de Ã©xito
            if img_success > 0:
                flash(f'âœ… Laptop {laptop.sku} actualizada con {img_success} nueva(s) imagen(es)', 'success')
            else:
                flash(f'âœ… Laptop {laptop.sku} actualizada exitosamente', 'success')

            # Mostrar errores de imÃ¡genes si los hay
            for error in img_errors:
                flash(f'âš ï¸ {error}', 'warning')

            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al actualizar laptop {laptop.sku}: {str(e)}', exc_info=True)
            flash(f'âŒ Error al actualizar laptop: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    # CORRECCIÃ“N: Obtener imÃ¡genes ordenadas usando sorted() en lugar de order_by()
    images_list = sorted(laptop.images, key=lambda img: img.ordering)
    images_by_position = {img.position: img for img in images_list}

    return render_template('inventory/laptop_form.html', form=form, mode='edit', laptop=laptop,
                           images_by_position=images_by_position)


# ===== ELIMINAR LAPTOP =====

@inventory_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('inventory.laptops.delete')
def laptop_delete(id):
    """
    Elimina una laptop del inventario
    """
    laptop = Laptop.query.get_or_404(id)

    try:
        # Obtener y eliminar imÃ¡genes asociadas
        images = laptop.images

        # Eliminar archivos de imÃ¡genes del sistema de archivos
        for image in images:
            try:
                filepath = os.path.join('app', 'static', image.image_path)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f'Laptop {laptop.sku}: Imagen eliminada {image.image_path}')
            except Exception as e:
                logger.error(f'Error al eliminar imagen {image.image_path}: {str(e)}')

        # Eliminar directorio de imÃ¡genes si existe
        image_folder = os.path.join('app', 'static', 'uploads', 'laptops', str(laptop.id))
        if os.path.exists(image_folder):
            try:
                os.rmdir(image_folder)
                logger.info(f'Laptop {laptop.sku}: Directorio de imÃ¡genes eliminado')
            except Exception as e:
                logger.error(f'Error al eliminar directorio de imÃ¡genes: {str(e)}')

        # Eliminar la laptop de la base de datos
        db.session.delete(laptop)
        db.session.commit()

        flash(f'âœ… Laptop {laptop.sku} eliminada exitosamente', 'success')
        return redirect(url_for('inventory.laptops_list'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al eliminar laptop {laptop.sku}: {str(e)}', exc_info=True)
        flash(f'âŒ Error al eliminar laptop: {str(e)}', 'error')
        return redirect(url_for('inventory.laptop_detail', id=id))


# ===== DUPLICAR LAPTOP =====

@inventory_bp.route('/<int:id>/duplicate', methods=['POST'])
@login_required
@permission_required('inventory.laptops.create')
def laptop_duplicate(id):
    original = Laptop.query.get_or_404(id)

    # Generar nuevo SKU
    new_sku = SKUService.generate_laptop_sku()

    # Generar nuevo slug
    new_display_name = f"{original.display_name} (Copia)"
    base_slug = generate_slug(new_display_name)
    new_slug = ensure_unique_slug(base_slug)

    duplicate = Laptop(
        sku=new_sku,
        slug=new_slug,
        display_name=new_display_name,
        short_description=original.short_description,
        long_description_html=original.long_description_html,
        is_published=False,  # La copia no se publica automÃ¡ticamente
        is_featured=False,  # Tampoco se destaca
        seo_title=original.seo_title,
        seo_description=original.seo_description,
        brand_id=original.brand_id,
        model_id=original.model_id,
        processor_id=original.processor_id,
        os_id=original.os_id,
        screen_id=original.screen_id,
        graphics_card_id=original.graphics_card_id,
        storage_id=original.storage_id,
        ram_id=original.ram_id,
        store_id=original.store_id,
        location_id=original.location_id,
        supplier_id=original.supplier_id,
        npu=original.npu,
        storage_upgradeable=original.storage_upgradeable,
        ram_upgradeable=original.ram_upgradeable,
        keyboard_layout=original.keyboard_layout,
        connectivity_ports=original.connectivity_ports.copy() if original.connectivity_ports else {},
        category=original.category,
        condition=original.condition,
        purchase_cost=original.purchase_cost,
        sale_price=original.sale_price,
        discount_price=original.discount_price,
        tax_percent=original.tax_percent,
        quantity=original.quantity,
        reserved_quantity=original.reserved_quantity,
        min_alert=original.min_alert,
        entry_date=date.today(),  # Nueva fecha de entrada
        sale_date=original.sale_date,
        internal_notes=original.internal_notes,
        created_by_id=current_user.id
    )

    db.session.add(duplicate)
    db.session.commit()

    flash('Laptop duplicada correctamente', 'success')
    return redirect(url_for('inventory.laptop_edit', id=duplicate.id))


@inventory_bp.route('/get_generations/<family>')
@login_required
@any_permission_required('inventory.laptops.view', 'inventory.laptops.create', 'inventory.laptops.edit')
def get_generations(family):
    """
    API para obtener generaciones basadas en la familia del procesador
    """
    query = db.session.query(Processor.name).filter(Processor.is_active == True)
    
    if family and family != 'all' and family != 'None':
        query = query.filter(Processor.family == family)
        
    generations = query.distinct().order_by(Processor.name).all()
    
    return jsonify([g[0] for g in generations if g[0]])

    # ===== GESTIÓN DE SERIALES =====

@inventory_bp.route('/serials')
@login_required
@permission_required('inventory.laptops.view')
def serials_list():
    """
    Página de gestión de seriales con filtros por estado.
    URL: /inventory/serials
    """
    # Parámetros de filtrado
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    brand_filter = request.args.get('brand', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    # Query base con join a Laptop y Brand
    query = db.session.query(LaptopSerial).join(
        Laptop, LaptopSerial.laptop_id == Laptop.id
    ).join(
        Brand, Laptop.brand_id == Brand.id
    )

    # Filtrar por estado
    if status_filter:
        query = query.filter(LaptopSerial.status == status_filter)

    # Búsqueda
    if search:
        query = query.filter(
            or_(
                LaptopSerial.serial_number.ilike(f'%{search}%'),
                LaptopSerial.barcode.ilike(f'%{search}%'),
                Laptop.display_name.ilike(f'%{search}%'),
                Laptop.sku.ilike(f'%{search}%')
            )
        )

    # Filtrar por marca
    if brand_filter:
        query = query.filter(Brand.name == brand_filter)

    # Estadísticas por estado (sin filtros de búsqueda para totales globales)
    stats_query = db.session.query(
        LaptopSerial.status,
        db.func.count(LaptopSerial.id)
    ).group_by(LaptopSerial.status).all()

    stats = {s[0]: s[1] for s in stats_query}
    total_serials = sum(stats.values())

    # Obtener marcas para filtro
    brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).all()

    # Ordenar y paginar
    query = query.order_by(LaptopSerial.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    serials = pagination.items

    return render_template(
        'inventory/serials_list.html',
        serials=serials,
        pagination=pagination,
        stats=stats,
        total_serials=total_serials,
        status_filter=status_filter,
        search=search,
        brand_filter=brand_filter,
        brands=brands,
        status_choices=SERIAL_STATUS_CHOICES
    )