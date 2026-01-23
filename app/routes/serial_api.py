# ============================================
# API DE SERIALES
# ============================================
# Endpoints REST para gestión de números de serie
# 
# Endpoints:
# - GET  /api/serials/search       - Buscar serial
# - POST /api/serials/validate     - Validar serial
# - GET  /api/serials/<id>         - Obtener serial
# - POST /api/serials              - Crear serial
# - PUT  /api/serials/<id>         - Actualizar serial
# - DELETE /api/serials/<id>       - Eliminar serial
# - POST /api/serials/batch        - Crear múltiples seriales
# - GET  /api/serials/laptop/<id>  - Seriales de una laptop
# - POST /api/serials/<id>/status  - Cambiar estado

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.serial import LaptopSerial, InvoiceItemSerial, SerialMovement, SERIAL_STATUS_CHOICES
from app.models.laptop import Laptop
from app.services.serial_service import SerialService
from functools import wraps
import logging

logger = logging.getLogger(__name__)

serial_api = Blueprint('serial_api', __name__, url_prefix='/api/serials')


# ============================================
# DECORADORES
# ============================================

def json_response(f):
    """Decorador para asegurar respuestas JSON"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error en API: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    return decorated_function


def require_json(f):
    """Decorador para requerir JSON en el body"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Se requiere Content-Type: application/json'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ENDPOINTS DE BÚSQUEDA
# ============================================

@serial_api.route('/search')
@login_required
@json_response
def search_serial():
    """
    Busca un serial por número o código de barras.
    
    Query params:
        q: Texto de búsqueda (requerido)
        laptop_id: Filtrar por laptop (opcional)
        status: Filtrar por estado (opcional)
        limit: Límite de resultados (default: 50)
    
    Returns:
        {
            found: bool,
            serial: {...} | null,
            results: [...] (si hay múltiples)
        }
    """
    query = request.args.get('q', '').strip()
    laptop_id = request.args.get('laptop_id', type=int)
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    
    if not query:
        return jsonify({
            'found': False,
            'serial': None,
            'results': [],
            'error': 'Se requiere parámetro de búsqueda (q)'
        })
    
    # Buscar coincidencia exacta primero
    serial = SerialService.find_by_serial(query)
    
    if serial:
        return jsonify({
            'found': True,
            'serial': serial.to_dict(),
            'results': [serial.to_dict()]
        })
    
    # Si no hay coincidencia exacta, buscar parcialmente
    results = SerialService.search_serials(
        query=query,
        laptop_id=laptop_id,
        status=status,
        limit=limit
    )
    
    return jsonify({
        'found': len(results) > 0,
        'serial': results[0].to_dict() if results else None,
        'results': [r.to_dict() for r in results]
    })


@serial_api.route('/validate', methods=['POST'])
@login_required
@json_response
@require_json
def validate_serial():
    """
    Valida un número de serial.
    
    Body JSON:
        serial_number: Número de serie a validar (requerido)
        serial_type: Tipo de serial (opcional, default: 'manufacturer')
        exclude_id: ID a excluir de validación de unicidad (opcional)
    
    Returns:
        {
            valid: bool,
            unique: bool,
            errors: [...],
            existing_serial: {...} | null
        }
    """
    data = request.get_json()
    
    serial_number = data.get('serial_number', '').strip()
    serial_type = data.get('serial_type', 'manufacturer')
    exclude_id = data.get('exclude_id')
    
    if not serial_number:
        return jsonify({
            'valid': False,
            'unique': False,
            'errors': ['El número de serie es requerido']
        })
    
    errors = []
    
    # Validar formato
    is_valid, error = SerialService.validate_serial_format(serial_number, serial_type)
    if not is_valid:
        errors.append(error)
    
    # Validar unicidad
    is_unique, existing = SerialService.is_serial_unique(serial_number, exclude_id)
    
    return jsonify({
        'valid': is_valid and is_unique,
        'format_valid': is_valid,
        'unique': is_unique,
        'errors': errors,
        'existing_serial': existing.to_dict(include_laptop=True) if existing else None
    })


# ============================================
# ENDPOINTS CRUD
# ============================================

@serial_api.route('/<int:serial_id>')
@login_required
@json_response
def get_serial(serial_id):
    """Obtiene un serial por ID"""
    serial = LaptopSerial.query.get(serial_id)
    
    if not serial:
        return jsonify({
            'success': False,
            'error': f'Serial con ID {serial_id} no encontrado'
        }), 404
    
    # Obtener información de venta si existe
    sale_info = SerialService.get_serial_sale_info(serial_id)
    
    data = serial.to_dict()
    data['sale_info'] = sale_info
    
    return jsonify({
        'success': True,
        'serial': data
    })


@serial_api.route('', methods=['POST'])
@login_required
@json_response
@require_json
def create_serial():
    """
    Crea un nuevo serial.
    
    Body JSON:
        laptop_id: ID de la laptop (requerido)
        serial_number: Número de serie (requerido)
        serial_type: Tipo de serial (opcional)
        barcode: Código de barras (opcional)
        notes: Notas (opcional)
        unit_cost: Costo unitario (opcional)
        warranty_start: Inicio garantía (opcional, formato YYYY-MM-DD)
        warranty_end: Fin garantía (opcional, formato YYYY-MM-DD)
        warranty_provider: Proveedor de garantía (opcional)
    """
    data = request.get_json()
    
    laptop_id = data.get('laptop_id')
    serial_number = data.get('serial_number')
    
    if not laptop_id:
        return jsonify({
            'success': False,
            'error': 'laptop_id es requerido'
        }), 400
    
    if not serial_number:
        return jsonify({
            'success': False,
            'error': 'serial_number es requerido'
        }), 400
    
    # Parsear fechas si vienen como string
    from datetime import datetime
    
    warranty_start = data.get('warranty_start')
    warranty_end = data.get('warranty_end')
    received_date = data.get('received_date')
    
    if warranty_start and isinstance(warranty_start, str):
        warranty_start = datetime.strptime(warranty_start, '%Y-%m-%d').date()
    
    if warranty_end and isinstance(warranty_end, str):
        warranty_end = datetime.strptime(warranty_end, '%Y-%m-%d').date()
    
    if received_date and isinstance(received_date, str):
        received_date = datetime.strptime(received_date, '%Y-%m-%d').date()
    
    success, result = SerialService.create_serial(
        laptop_id=laptop_id,
        serial_number=serial_number,
        serial_type=data.get('serial_type', 'manufacturer'),
        barcode=data.get('barcode'),
        notes=data.get('notes'),
        unit_cost=data.get('unit_cost'),
        received_date=received_date,
        warranty_start=warranty_start,
        warranty_end=warranty_end,
        warranty_provider=data.get('warranty_provider'),
        created_by_id=current_user.id
    )
    
    if success:
        return jsonify({
            'success': True,
            'serial': result.to_dict(),
            'message': f'Serial {serial_number} creado exitosamente'
        }), 201
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400


@serial_api.route('/batch', methods=['POST'])
@login_required
@json_response
@require_json
def create_serials_batch():
    """
    Crea múltiples seriales a la vez.
    
    Body JSON:
        laptop_id: ID de la laptop (requerido)
        serial_numbers: Lista de números de serie (requerido)
        ... (mismos campos opcionales que create_serial)
    """
    data = request.get_json()
    
    laptop_id = data.get('laptop_id')
    serial_numbers = data.get('serial_numbers', [])
    
    if not laptop_id:
        return jsonify({
            'success': False,
            'error': 'laptop_id es requerido'
        }), 400
    
    if not serial_numbers:
        return jsonify({
            'success': False,
            'error': 'serial_numbers es requerido'
        }), 400
    
    # Campos opcionales
    kwargs = {
        'serial_type': data.get('serial_type', 'manufacturer'),
        'created_by_id': current_user.id
    }
    
    # Procesar fechas
    from datetime import datetime
    
    for date_field in ['warranty_start', 'warranty_end', 'received_date']:
        if data.get(date_field):
            try:
                kwargs[date_field] = datetime.strptime(data[date_field], '%Y-%m-%d').date()
            except:
                pass
    
    for field in ['warranty_provider', 'notes']:
        if data.get(field):
            kwargs[field] = data[field]
    
    result = SerialService.create_serials_batch(
        laptop_id=laptop_id,
        serial_numbers=serial_numbers,
        **kwargs
    )
    
    return jsonify({
        'success': result['success'],
        'created_count': result['created_count'],
        'error_count': result['error_count'],
        'total': result['total'],
        'created': [s.to_dict() for s in result['created']],
        'errors': result['errors']
    })


@serial_api.route('/<int:serial_id>', methods=['PUT'])
@login_required
@json_response
@require_json
def update_serial(serial_id):
    """
    Actualiza un serial existente.
    
    Body JSON: campos a actualizar
    """
    data = request.get_json()
    
    # Campos actualizables
    allowed_fields = [
        'serial_number', 'serial_type', 'barcode', 'notes', 
        'unit_cost', 'warranty_start', 'warranty_end', 'warranty_provider'
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    # Parsear fechas
    from datetime import datetime
    
    for date_field in ['warranty_start', 'warranty_end']:
        if update_data.get(date_field) and isinstance(update_data[date_field], str):
            update_data[date_field] = datetime.strptime(update_data[date_field], '%Y-%m-%d').date()
    
    success, result = SerialService.update_serial(serial_id, **update_data)
    
    if success:
        return jsonify({
            'success': True,
            'serial': result.to_dict(),
            'message': 'Serial actualizado exitosamente'
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400


@serial_api.route('/<int:serial_id>', methods=['DELETE'])
@login_required
@json_response
def delete_serial(serial_id):
    """Elimina un serial"""
    success, error = SerialService.delete_serial(serial_id, user_id=current_user.id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Serial eliminado exitosamente'
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 400


# ============================================
# ENDPOINTS POR LAPTOP
# ============================================

@serial_api.route('/laptop/<int:laptop_id>')
@login_required
@json_response
def get_serials_for_laptop(laptop_id):
    """
    Obtiene todos los seriales de una laptop.
    
    Query params:
        status: Filtrar por estado (opcional)
    """
    laptop = Laptop.query.get(laptop_id)
    if not laptop:
        return jsonify({
            'success': False,
            'error': f'Laptop con ID {laptop_id} no encontrada'
        }), 404
    
    status = request.args.get('status')
    
    query = LaptopSerial.query.filter_by(laptop_id=laptop_id)
    
    if status:
        query = query.filter_by(status=status)
    
    serials = query.order_by(LaptopSerial.created_at.desc()).all()
    
    # Estadísticas
    stats = SerialService.count_serials_by_status(laptop_id)
    validation = SerialService.validate_laptop_serial_count(laptop_id)
    
    return jsonify({
        'success': True,
        'laptop': {
            'id': laptop.id,
            'sku': laptop.sku,
            'display_name': laptop.display_name,
            'quantity': laptop.quantity
        },
        'serials': [s.to_dict(include_laptop=False) for s in serials],
        'count': len(serials),
        'stats': stats,
        'validation': validation
    })


@serial_api.route('/laptop/<int:laptop_id>/available')
@login_required
@json_response
def get_available_serials_for_laptop(laptop_id):
    """Obtiene solo los seriales disponibles de una laptop"""
    serials = SerialService.get_available_serials_for_laptop(laptop_id)
    
    return jsonify({
        'success': True,
        'serials': [s.to_dict(include_laptop=False) for s in serials],
        'count': len(serials)
    })


# ============================================
# ENDPOINTS DE ESTADO
# ============================================

@serial_api.route('/<int:serial_id>/status', methods=['POST'])
@login_required
@json_response
@require_json
def change_serial_status(serial_id):
    """
    Cambia el estado de un serial.
    
    Body JSON:
        status: Nuevo estado (requerido)
        reason: Razón del cambio (opcional)
    """
    data = request.get_json()
    
    new_status = data.get('status')
    reason = data.get('reason')
    
    if not new_status:
        return jsonify({
            'success': False,
            'error': 'status es requerido'
        }), 400
    
    success, result = SerialService.change_serial_status(
        serial_id=serial_id,
        new_status=new_status,
        reason=reason,
        user_id=current_user.id
    )
    
    if success:
        return jsonify({
            'success': True,
            'serial': result.to_dict(),
            'message': f'Estado cambiado a {new_status}'
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400


# ============================================
# ENDPOINTS DE HISTORIAL Y TRAZABILIDAD
# ============================================

@serial_api.route('/<int:serial_id>/history')
@login_required
@json_response
def get_serial_history(serial_id):
    """Obtiene el historial de movimientos de un serial"""
    serial = LaptopSerial.query.get(serial_id)
    
    if not serial:
        return jsonify({
            'success': False,
            'error': f'Serial con ID {serial_id} no encontrado'
        }), 404
    
    movements = SerialService.get_serial_history(serial_id)
    sale_info = SerialService.get_serial_sale_info(serial_id)
    
    return jsonify({
        'success': True,
        'serial': serial.to_dict(),
        'sale_info': sale_info,
        'history': [m.to_dict() for m in movements]
    })


# ============================================
# ENDPOINTS DE ESTADÍSTICAS
# ============================================

@serial_api.route('/stats')
@login_required
@json_response
def get_serial_stats():
    """Obtiene estadísticas generales de seriales"""
    stats = SerialService.get_serial_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })


# ============================================
# ENDPOINTS DE SINCRONIZACIÓN
# ============================================

@serial_api.route('/laptop/<int:laptop_id>/sync', methods=['POST'])
@login_required
@json_response
def sync_laptop_quantity(laptop_id):
    """
    Sincroniza la cantidad de una laptop con sus seriales disponibles.
    """
    success, result = SerialService.sync_laptop_quantity(laptop_id)
    
    if success:
        return jsonify({
            'success': True,
            'result': result,
            'message': 'Cantidad sincronizada' if result['synced'] else 'No se requirió sincronización'
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 400


# ============================================
# OPCIONES (para selects)
# ============================================

@serial_api.route('/status-options')
@login_required
@json_response
def get_status_options():
    """Obtiene las opciones de estado para selects"""
    return jsonify({
        'success': True,
        'options': SERIAL_STATUS_CHOICES
    })
