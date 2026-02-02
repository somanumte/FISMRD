# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.models.laptop import Laptop, Brand
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.user import User
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta

# Crear Blueprint
main_bp = Blueprint('main', __name__)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def calculate_percentage_change(current, previous):
    """Calcula el cambio porcentual entre dos valores"""
    if previous == 0 or previous is None:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100


def get_date_range(period='month'):
    """Obtiene rango de fechas según el período"""
    today = datetime.now()

    if period == 'today':
        return today.replace(hour=0, minute=0, second=0), today
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday.replace(hour=0, minute=0, second=0), yesterday.replace(hour=23, minute=59, second=59)
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start.replace(hour=0, minute=0, second=0), today
    elif period == 'month':
        start = today.replace(day=1, hour=0, minute=0, second=0)
        return start, today
    elif period == 'quarter':
        quarter = (today.month - 1) // 3
        start = today.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0)
        return start, today
    elif period == 'year':
        start = today.replace(month=1, day=1, hour=0, minute=0, second=0)
        return start, today

    return today.replace(day=1, hour=0, minute=0, second=0), today

def get_growth_indicator(change):
    """Retorna indicador de crecimiento con color"""
    if change > 0:
        return {
            'icon': 'arrow-up',
            'color': 'green',
            'text': f'+{change:.1f}%'
        }
    elif change < 0:
        return {
            'icon': 'arrow-down',
            'color': 'red',
            'text': f'{change:.1f}%'
        }
    else:
        return {
            'icon': 'minus',
            'color': 'gray',
            'text': '0%'
        }


def get_time_ago(dt):
    """Calcula tiempo transcurrido en formato legible"""
    now = datetime.now()
    diff = now - dt

    if diff.days > 0:
        if diff.days == 1:
            return 'hace 1 día'
        return f'hace {diff.days} días'

    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return 'hace 1 hora'
        return f'hace {hours} horas'

    minutes = diff.seconds // 60
    if minutes > 0:
        if minutes == 1:
            return 'hace 1 minuto'
        return f'hace {minutes} minutos'

    return 'hace un momento'


# ============================================
# RUTA PRINCIPAL DEL DASHBOARD
# ============================================

@main_bp.route('/dashboard')
@login_required
def dashboard():  # <-- Cambiado de redirect_to_dashboard a dashboard
    """Redirige al dashboard premium"""
    return redirect(url_for('dashboard.index'))

# ============================================
# API ENDPOINTS
# ============================================

@main_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """API para stats en tiempo real"""
    period = request.args.get('period', 'month')
    start_date, end_date = get_date_range(period)

    total_laptops = Laptop.query.count()
    total_customers = Customer.query.count()

    invoices = Invoice.query.filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
        Invoice.status.in_(['paid', 'completed'])
    ).all()

    revenue = sum(float(inv.subtotal) for inv in invoices)

    return jsonify({
        'success': True,
        'data': {
            'inventory': {
                'total_laptops': total_laptops,
                'available': Laptop.query.filter(Laptop.quantity > 0).count(),
                'low_stock': Laptop.query.filter(Laptop.quantity <= Laptop.min_alert).count()
            },
            'sales': {
                'revenue': revenue,
                'orders': len(invoices),
                'customers': total_customers
            },
            'timestamp': datetime.now().isoformat()
        }
    })


# ============================================
# RUTAS DE ADMIN (COMPATIBILIDAD)
# ============================================

# Admin panel route moved to app/routes/admin.py


@main_bp.route('/admin/users')
@login_required
def admin_users():
    """
    Lista de usuarios (placeholder para compatibilidad)
    """
    if not current_user.is_admin:
        abort(403)

    users = User.query.order_by(User.created_at.desc()).all()

    return render_template(
        'admin/users.html',
        users=users
    )


@main_bp.route('/admin/catalogs')
@login_required
def admin_catalogs():
    """
    Gestión unificada de catálogos
    """
    if not (current_user.is_admin or current_user.has_permission('inventory.view')):
        abort(403)

    return render_template('admin/catalogs.html')


@main_bp.route('/admin/catalogs/<catalog_type>/<int:item_id>')
@login_required
def catalog_detail(catalog_type, item_id):
    """
    Vista detallada para Brands (con Models) o Stores (con Locations)
    """
    if not (current_user.is_admin or current_user.has_permission('inventory.view')):
        abort(403)

    # Map catalog types to models
    from app.models.laptop import Brand, LaptopModel, Store, Location

    catalog_map = {
        'brands': {'model': Brand, 'child_model': LaptopModel, 'child_name': 'Modelos', 'child_type': 'models'},
        'stores': {'model': Store, 'child_model': Location, 'child_name': 'Ubicaciones', 'child_type': 'locations'}
    }

    if catalog_type not in catalog_map:
        abort(404)

    config = catalog_map[catalog_type]
    parent_item = config['model'].query.get_or_404(item_id)

    return render_template(
        'admin/catalog_detail.html',
        catalog_type=catalog_type,
        parent_item=parent_item,
        child_model_name=config['child_name'],
        child_type=config['child_type']
    )


# ============================================
# MANEJADORES DE ERRORES
# ============================================

def register_error_handlers(app):
    """
    Registra los manejadores de errores personalizados
    Se llama desde app/__init__.py
    """

    @app.errorhandler(403)
    def forbidden(error):
        """Error 403: Acceso prohibido"""
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        """Error 404: Página no encontrada"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """Error 500: Error interno del servidor"""
        db.session.rollback()  # Revertir cualquier transacción pendiente
        return render_template('errors/500.html'), 500
