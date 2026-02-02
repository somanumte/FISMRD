# -*- coding: utf-8 -*-
# ============================================
# API DE CATÁLOGOS - Endpoints para Select2 y Gestión
# ============================================
# Actualizado al nuevo modelo de datos
# Incluye ExpenseCategory y lógica de gestión completa

from flask import Blueprint, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)
from app.models.expense import ExpenseCategory
from app.services.catalog_service import CatalogService
from app.utils.decorators import admin_required, json_response, handle_exceptions

# Crear Blueprint
catalog_api_bp = Blueprint('catalog_api', __name__, url_prefix='/api/catalog')


# ===== MAPPING DE MODELOS =====
CATALOG_MODELS = {
    'brands': Brand,
    'models': LaptopModel,
    'processors': Processor,
    'operating-systems': OperatingSystem,
    'screens': Screen,
    'graphics-cards': GraphicsCard,
    'storage': Storage,
    'ram': Ram,
    'stores': Store,
    'locations': Location,
    'suppliers': Supplier,
    'expense-categories': ExpenseCategory
}

CATALOG_NAMES = {
    'brands': 'Marca',
    'models': 'Modelo',
    'processors': 'Procesador',
    'operating-systems': 'Sistema Operativo',
    'screens': 'Pantalla',
    'graphics-cards': 'Tarjeta Gráfica',
    'storage': 'Almacenamiento',
    'ram': 'Memoria RAM',
    'stores': 'Tienda',
    'locations': 'Ubicación',
    'suppliers': 'Proveedor',
    'expense-categories': 'Categoría de Gasto'
}


# ===== FUNCIÓN HELPER GENÉRICA =====

def get_catalog_items(model, search_term='', page=1, page_size=20, filters=None):
    """
    Función genérica para obtener items de catálogo con búsqueda y paginación
    """
    # Query base (incluir inactivos si se solicita explícitamente, pero por defecto solo activos para select2)
    # Para gestión, querremos ver todos probablemente, o filtrarlos.
    # Vamos a permitir pasar 'active_only' en request
    active_only = request.args.get('active_only', 'true') == 'true'
    
    query = model.query
    if active_only and hasattr(model, 'is_active'):
        query = query.filter_by(is_active=True)

    # Búsqueda
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(model.name.ilike(search_pattern))

    # Filtros adicionales (e.g. brand_id para models)
    if filters:
        for key, value in filters.items():
            if hasattr(model, key) and value:
                query = query.filter(getattr(model, key) == value)

    # Ordenar por nombre
    query = query.order_by(model.name)

    # Calcular total
    total = query.count()

    # Paginación
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Formatear
    results = []
    for item in items:
        item_dict = {'id': item.id, 'text': item.name}
        
        # Campos extra comunes
        if hasattr(item, 'is_active'):
            item_dict['is_active'] = item.is_active
            
        # Campos específicos por tipo
        if isinstance(item, LaptopModel):
            item_dict['brand_id'] = item.brand_id
            item_dict['brand_name'] = item.brand.name if item.brand else None
        elif isinstance(item, Location):
            item_dict['store_id'] = item.store_id
            item_dict['store_name'] = item.store_ref.name if item.store_ref else None
        elif isinstance(item, ExpenseCategory):
            item_dict['color'] = item.color
            item_dict['description'] = item.description
        elif isinstance(item, Supplier):
            item_dict['contact_name'] = item.contact_name
            item_dict['phone'] = item.phone
            item_dict['email'] = item.email
            
        results.append(item_dict)

    # Determinar si hay más páginas
    has_more = (offset + page_size) < total

    return {
        'results': results,
        'pagination': {
            'more': has_more
        },
        'total': total
    }


def create_catalog_item_generic(model, data, model_name_str):
    """
    Crea un nuevo item genérico
    """
    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    # Verificar existencia
    existing = model.query.filter(
        db.func.lower(model.name) == name.lower()
    ).first()

    if existing:
        if hasattr(existing, 'is_active') and not existing.is_active:
             return {'error': f'El {model_name_str} "{name}" ya existe pero está inactivo. Usa la opción de reactivar.'}, 409
        return {'error': f'El {model_name_str} "{name}" ya existe'}, 409

    # Campos extra permitidos según modelo
    extra_fields = {}
    
    # Modelos con dependencias
    if model == LaptopModel:
        if 'brand_id' not in data:
            return {'error': 'La marca es requerida para crear un modelo'}, 400
        extra_fields['brand_id'] = data.get('brand_id')
        
    elif model == Location:
        if 'store_id' not in data:
            return {'error': 'La tienda es requerida para crear una ubicación'}, 400
        extra_fields['store_id'] = data.get('store_id')
        
    elif model == Supplier:
        for field in ['contact_name', 'email', 'phone', 'address', 'website', 'notes']:
            if field in data:
                extra_fields[field] = data[field]
                
    elif model == ExpenseCategory:
        for field in ['color', 'description']:
            if field in data:
                extra_fields[field] = data[field]
    
    elif model == Store:
        for field in ['address', 'phone']:
            if field in data:
                extra_fields[field] = data[field]

    # Crear
    new_item = model(name=name, **extra_fields)
    # Asignar is_active si el modelo lo tiene (ExpenseCategory no hereda de CatalogMixin pero lo revisaré)
    if hasattr(new_item, 'is_active'):
        new_item.is_active = True
        
    db.session.add(new_item)
    db.session.commit()

    return {
        'id': new_item.id,
        'text': new_item.name,
        'created': True,
        'message': f'{model_name_str} "{new_item.name}" creado exitosamente'
    }, 201


# ===== ENDPOINTS GENÉRICOS (ROUTING POR TIPO) =====

@catalog_api_bp.route('/<catalog_type>', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def list_catalog_items(catalog_type):
    """Listar items de cualquier catálogo"""
    if catalog_type not in CATALOG_MODELS:
        return {'error': 'Tipo de catálogo no válido'}, 404

    model = CATALOG_MODELS[catalog_type]
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    # Filtros específicos - convertir a int
    filters = {}
    if catalog_type == 'models':
        brand_id = request.args.get('brand_id', type=int)
        if brand_id:
            filters['brand_id'] = brand_id
    elif catalog_type == 'locations':
        store_id = request.args.get('store_id', type=int)
        if store_id:
            filters['store_id'] = store_id

    return get_catalog_items(model, search, page, filters=filters)


@catalog_api_bp.route('/<catalog_type>', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_catalog_item_endpoint(catalog_type):
    """Crear item en cualquier catálogo"""
    if catalog_type not in CATALOG_MODELS:
        return {'error': 'Tipo de catálogo no válido'}, 404

    model = CATALOG_MODELS[catalog_type]
    model_name_str = CATALOG_NAMES.get(catalog_type, 'Item')
    data = request.get_json()

    return create_catalog_item_generic(model, data, model_name_str)


@catalog_api_bp.route('/<catalog_type>/<int:id>', methods=['PUT'])
@login_required
@admin_required
@json_response
@handle_exceptions
def update_catalog_item(catalog_type, id):
    """Actualizar item de cualquier catálogo"""
    if catalog_type not in CATALOG_MODELS:
        return {'error': 'Tipo de catálogo no válido'}, 404

    model = CATALOG_MODELS[catalog_type]
    item = model.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        new_name = data['name'].strip()
        if new_name and new_name != item.name:
            # Check duplicates
            existing = model.query.filter(
                db.func.lower(model.name) == new_name.lower(),
                model.id != id
            ).first()
            if existing:
                return {'error': f'Ya existe otro registro con el nombre "{new_name}"'}, 409
            item.name = new_name

    # Campos extra
    if catalog_type == 'suppliers':
        if 'contact_name' in data: item.contact_name = data['contact_name']
        if 'email' in data: item.email = data['email']
        if 'phone' in data: item.phone = data['phone']
        if 'address' in data: item.address = data['address']
        if 'website' in data: item.website = data['website']
        if 'notes' in data: item.notes = data['notes']
        
    elif catalog_type == 'expense-categories':
        if 'color' in data: item.color = data['color']
        if 'description' in data: item.description = data['description']
        
    elif catalog_type == 'stores':
        if 'address' in data: item.address = data['address']
        if 'phone' in data: item.phone = data['phone']

    db.session.commit()
    
    return {
        'id': item.id,
        'text': item.name,
        'message': 'Actualizado exitosamente'
    }


@catalog_api_bp.route('/<catalog_type>/<int:id>', methods=['DELETE'])
@login_required
@admin_required
@json_response
@handle_exceptions
def deactivate_catalog_item(catalog_type, id):
    """Desactivar (Soft Delete) item"""
    if catalog_type not in CATALOG_MODELS:
        return {'error': 'Tipo de catálogo no válido'}, 404

    model = CATALOG_MODELS[catalog_type]
    
    # ExpenseCategory no tiene is_active por defecto en el modelo original?
    # Vamos a asumir que sí o lo manejaremos.
    # Si no tiene is_active, no podemos desactivarlo.
    if not hasattr(model, 'is_active'):
        # Para ExpenseCategory, si no tiene is_active, tal vez borrado físico si no hay relaciones?
        # Por seguridad, solo permitiremos is_active.
        return {'error': 'Este catálogo no soporta desactivación'}, 400

    if CatalogService.deactivate_item(model, id):
        return {'message': 'Elemento desactivado exitosamente'}
    
    return {'error': 'No se pudo desactivar el elemento'}, 400


@catalog_api_bp.route('/<catalog_type>/<int:id>/reactivate', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def reactivate_catalog_item(catalog_type, id):
    """Reactivar item"""
    if catalog_type not in CATALOG_MODELS:
        return {'error': 'Tipo de catálogo no válido'}, 404

    model = CATALOG_MODELS[catalog_type]
    
    if CatalogService.reactivate_item(model, id):
        return {'message': 'Elemento reactivado exitosamente'}
    
    return {'error': 'No se pudo reactivar el elemento'}, 400


@catalog_api_bp.route('/<catalog_type>/merge', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def merge_catalog_items(catalog_type):
    """
    Fusionar dos items
    Payload: { "source_id": 1, "target_id": 2 }
    """
    if catalog_type not in CATALOG_MODELS:
        return {'error': 'Tipo de catálogo no válido'}, 404

    data = request.get_json()
    source_id = data.get('source_id')
    target_id = data.get('target_id')

    if not source_id or not target_id:
        return {'error': 'Se requieren source_id y target_id'}, 400

    if source_id == target_id:
        return {'error': 'No se puede fusionar un elemento consigo mismo'}, 400

    model = CATALOG_MODELS[catalog_type]
    
    count = CatalogService.merge_items(model, source_id, target_id)
    
    return {
        'message': f'Fusión completada. {count} registros actualizados.',
        'updated_count': count
    }


# ===== ESTADÍSTICAS GLOBAL =====

@catalog_api_bp.route('/stats', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def catalog_stats():
    """Obtiene estadísticas de todos los catálogos"""
    return CatalogService.get_catalog_stats()
