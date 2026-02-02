# -*- coding: utf-8 -*-
# ============================================
# RUTAS DE REPORTES Y ANÁLISIS
# ============================================

from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice, InvoiceItem, NCF_TYPES, NCF_SALES_TYPES, NCFSequence
from app.models.customer import Customer
from app.models.laptop import Laptop, Brand
from app.models.expense import Expense, ExpenseCategory
from app.models.serial import LaptopSerial, SerialMovement
from app.models.user import User
from app.utils.decorators import admin_required, permission_required
from sqlalchemy import func, desc, and_, or_, extract, text
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Crear Blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# ============================================
# RUTA PRINCIPAL: PANEL DE REPORTES
# ============================================

@reports_bp.route('/')
@login_required
@permission_required('reports.view')
def index():
    """
    Panel principal de reportes con todas las categorías
    """
    # Estadísticas rápidas para el dashboard
    total_reports = 29
    
    categories = [
        {
            'id': 'sales',
            'name': 'Ventas',
            'icon': '💰',
            'count': 9,
            'color': 'blue',
            'description': 'Análisis de ventas y facturación'
        },
        {
            'id': 'inventory',
            'name': 'Inventario',
            'icon': '📦',
            'count': 6,
            'color': 'green',
            'description': 'Control de stock y productos'
        },
        {
            'id': 'customers',
            'name': 'Clientes',
            'icon': '👥',
            'count': 4,
            'color': 'purple',
            'description': 'Análisis de base de clientes'
        },
        {
            'id': 'financial',
            'name': 'Financiero',
            'icon': '💵',
            'count': 3,
            'color': 'yellow',
            'description': 'Estados financieros y P&L'
        },
        {
            'id': 'ncf',
            'name': 'NCF/DGII',
            'icon': '📋',
            'count': 4,
            'color': 'red',
            'description': 'Comprobantes fiscales'
        },
        {
            'id': 'operational',
            'name': 'Operacional',
            'icon': '⚙️',
            'count': 3,
            'color': 'gray',
            'description': 'Sistema y auditoría'
        }
    ]
    
    return render_template(
        'reports/index.html',
        categories=categories,
        total_reports=total_reports
    )


# ============================================
# REPORTES DE VENTAS
# ============================================

@reports_bp.route('/sales/summary')
@login_required
@permission_required('reports.sales.view')
def sales_summary():
    """
    Reporte: Resumen de Ventas por Período
    """
    # Obtener parámetros de filtro
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    status = request.args.get('status', 'paid')
    payment_method = request.args.get('payment_method', '')
    
    return render_template(
        'reports/sales/summary.html',
        start_date=start_date,
        end_date=end_date,
        status=status,
        payment_method=payment_method
    )


@reports_bp.route('/api/sales/summary')
@login_required
@permission_required('reports.sales.view')
def api_sales_summary():
    """
    API: Datos para resumen de ventas
    """
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        status = request.args.get('status', 'paid')
        payment_method = request.args.get('payment_method', '')
        
        # Query base
        query = Invoice.query.filter(
            Invoice.invoice_date >= start_date,
            Invoice.invoice_date <= end_date
        )
        
        if status:
            query = query.filter(Invoice.status == status)
        
        if payment_method:
            query = query.filter(Invoice.payment_method == payment_method)
        
        invoices = query.all()
        
        # Calcular métricas
        total_sales = sum(float(inv.subtotal) for inv in invoices)
        total_invoices = len(invoices)
        avg_ticket = total_sales / total_invoices if total_invoices > 0 else 0
        
        # Ventas por día para gráfico
        daily_sales_query = db.session.query(
            Invoice.invoice_date,
            func.sum(Invoice.subtotal).label('total'),
            func.count(Invoice.id).label('count')
        ).filter(
            Invoice.invoice_date >= start_date,
            Invoice.invoice_date <= end_date
        )
        
        if status:
            daily_sales_query = daily_sales_query.filter(Invoice.status == status)
        if payment_method:
            daily_sales_query = daily_sales_query.filter(Invoice.payment_method == payment_method)
            
        daily_sales = daily_sales_query.group_by(Invoice.invoice_date).order_by(Invoice.invoice_date).all()
        
        chart_data = {
            'labels': [d[0].strftime('%d/%m') for d in daily_sales],
            'sales': [float(d[1]) for d in daily_sales],
            'count': [d[2] for d in daily_sales]
        }
        
        # Comparación con período anterior
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days + 1)
        prev_end = start_date - timedelta(days=1)
        
        prev_query = Invoice.query.filter(
            Invoice.invoice_date >= prev_start,
            Invoice.invoice_date <= prev_end
        )
        
        if status:
            prev_query = prev_query.filter(Invoice.status == status)
        if payment_method:
            prev_query = prev_query.filter(Invoice.payment_method == payment_method)
            
        prev_invoices = prev_query.all()
        
        prev_total = sum(float(inv.subtotal) for inv in prev_invoices)
        growth = ((total_sales - prev_total) / prev_total * 100) if prev_total > 0 else (100 if total_sales > 0 else 0)
        
        return jsonify({
            'success': True,
            'data': {
                'total_sales': round(total_sales, 2),
                'total_invoices': total_invoices,
                'avg_ticket': round(avg_ticket, 2),
                'growth': round(growth, 2),
                'prev_total': round(prev_total, 2),
                'chart_data': chart_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error en sales_summary: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reports_bp.route('/sales/by-product')
@login_required
@permission_required('reports.sales.view')
def sales_by_product():
    """
    Reporte: Ventas por Producto
    """
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    
    return render_template(
        'reports/sales/by_product.html',
        start_date=start_date,
        end_date=end_date
    )


@reports_bp.route('/api/sales/by-product')
@login_required
@permission_required('reports.sales.view')
def api_sales_by_product():
    """
    API: Ventas por producto
    """
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        # Ventas por producto
        product_sales = db.session.query(
            Laptop.display_name,
            Laptop.sku,
            func.sum(InvoiceItem.quantity).label('units_sold'),
            func.sum(InvoiceItem.line_total).label('revenue')
        ).join(InvoiceItem).join(Invoice).filter(
            Invoice.invoice_date >= start_date,
            Invoice.invoice_date <= end_date,
            Invoice.status == 'paid'
        ).group_by(Laptop.id, Laptop.display_name, Laptop.sku).order_by(
            desc('revenue')
        ).limit(20).all()
        
        products = []
        labels = []
        revenues = []
        units = []
        
        for product in product_sales:
            products.append({
                'name': product[0],
                'sku': product[1],
                'units_sold': product[2],
                'revenue': float(product[3])
            })
            labels.append(product[0][:30])  # Truncar nombre
            revenues.append(float(product[3]))
            units.append(product[2])
        
        return jsonify({
            'success': True,
            'data': {
                'products': products,
                'chart_data': {
                    'labels': labels,
                    'revenues': revenues,
                    'units': units
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error en sales_by_product: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# ============================================
# REPORTES DE VENTAS ADICIONALES
# ============================================

@reports_bp.route('/sales/by-customer')
@login_required
@permission_required('reports.sales.view')
def sales_by_customer():
    """Reporte: Ventas por Cliente"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/sales/by_customer.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/sales/by-customer')
@login_required
@permission_required('reports.sales.view')
def api_sales_by_customer():
    """API: Ventas por Cliente"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        query = db.session.query(
            Customer.id,
            Customer.first_name,
            Customer.last_name,
            Customer.company_name,
            func.count(Invoice.id).label('invoice_count'),
            func.sum(Invoice.total).label('total_sales')
        ).join(Invoice).filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.status == 'paid'
        ).group_by(Customer.id).order_by(desc('total_sales')).limit(50)
        
        results = query.all()
        data = [{
            'id': r.id,
            'name': f"{r.first_name} {r.last_name}" if r.first_name else r.company_name,
            'count': r.invoice_count,
            'total': float(r.total_sales)
        } for r in results]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error in sales_by_customer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/sales/by-payment-method')
@login_required
@permission_required('reports.sales.view')
def sales_by_payment_method():
    """Reporte: Ventas por Método de Pago"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/sales/by_payment_method.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/sales/by-payment-method')
@login_required
@permission_required('reports.sales.view')
def api_sales_by_payment_method():
    """API: Ventas por Método de Pago"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        results = db.session.query(
            Invoice.payment_method,
            func.count(Invoice.id),
            func.sum(Invoice.total)
        ).filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.status == 'paid'
        ).group_by(Invoice.payment_method).all()
        
        labels = [r[0].replace('_', ' ').title() if r[0] else 'N/A' for r in results]
        values = [float(r[2]) for r in results]
        counts = [r[1] for r in results]
        
        return jsonify({
            'success': True, 
            'data': {
                'labels': labels,
                'values': values,
                'counts': counts
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/sales/by-user')
@login_required
@permission_required('reports.sales.view')
def sales_by_user():
    """Reporte: Ventas por Usuario"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/sales/by_user.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/sales/by-user')
@login_required
@permission_required('reports.sales.view')
def api_sales_by_user():
    """API: Ventas por Usuario"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        results = db.session.query(
            User.username,
            func.count(Invoice.id),
            func.sum(Invoice.total)
        ).join(Invoice, Invoice.created_by_id == User.id).filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.status == 'paid'
        ).group_by(User.id, User.username).all()
        
        data = [{'user': r[0], 'count': r[1], 'total': float(r[2])} for r in results]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/sales/trends')
@login_required
@permission_required('reports.sales.view')
def sales_trends():
    """Reporte: Análisis de Tendencias"""
    return render_template('reports/sales/trends.html')

@reports_bp.route('/api/sales/trends')
@login_required
@permission_required('reports.sales.view')
def api_sales_trends():
    try:
        # Últimos 12 meses
        today = date.today()
        start_date = today - timedelta(days=365)
        
        results = db.session.query(
            func.to_char(Invoice.invoice_date, 'YYYY-MM').label('month'),
            func.sum(Invoice.subtotal)
        ).filter(
            Invoice.invoice_date >= start_date,
            Invoice.status.in_(['issued', 'paid', 'completed'])
        ).group_by(func.to_char(Invoice.invoice_date, 'YYYY-MM')).order_by(func.to_char(Invoice.invoice_date, 'YYYY-MM')).all()
        
        labels = [r[0] for r in results]
        values = [float(r[1]) for r in results]
        
        return jsonify({
            'success': True,
            'data': {'labels': labels, 'values': values}
        })
    except Exception as e:
        logger.error(f"Error in sales_trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/sales/pending')
@login_required
@permission_required('reports.sales.view')
def pending_invoices():
    """Reporte: Facturas Pendientes"""
    return render_template('reports/sales/pending.html')

@reports_bp.route('/api/sales/pending')
@login_required
@permission_required('reports.sales.view')
def api_pending_invoices():
    try:
        invoices = Invoice.query.filter(
            Invoice.status == 'pending'
        ).order_by(Invoice.due_date).all()
        
        data = [{
            'number': inv.invoice_number,
            'customer': inv.customer.full_name if inv.customer else 'N/A',
            'date': inv.invoice_date.isoformat(),
            'due_date': inv.due_date.isoformat() if inv.due_date else None,
            'total': float(inv.total),
            'days_overdue': (date.today() - inv.due_date).days if inv.due_date and date.today() > inv.due_date else 0
        } for inv in invoices]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# REPORTES DE INVENTARIO
# ============================================

@reports_bp.route('/inventory/current-status')
@login_required
def inventory_current_status():
    """
    Reporte: Estado Actual del Inventario
    """
    return render_template('reports/inventory/current_status.html')


@reports_bp.route('/api/inventory/current-status')
@login_required
def api_inventory_current_status():
    """
    API: Estado actual del inventario
    """
    try:
        laptops = Laptop.query.all()
        
        total_products = len(laptops)
        total_units = sum(l.quantity for l in laptops)
        total_value = sum(float(l.sale_price * l.quantity) for l in laptops)
        low_stock_count = sum(1 for l in laptops if l.is_low_stock)
        
        # Por categoría
        category_data = db.session.query(
            Laptop.category,
            func.count(Laptop.id).label('count'),
            func.sum(Laptop.quantity).label('units')
        ).group_by(Laptop.category).all()
        
        categories = {
            'labels': [c[0] for c in category_data],
            'counts': [c[1] for c in category_data],
            'units': [c[2] for c in category_data]
        }
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': total_products,
                'total_units': total_units,
                'total_value': round(total_value, 2),
                'low_stock_count': low_stock_count,
                'categories': categories
            }
        })
        
    except Exception as e:
        logger.error(f"Error en inventory_current_status: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reports_bp.route('/inventory/low-stock')
@login_required
@permission_required('reports.inventory.view')
def inventory_low_stock():
    """
    Reporte: Productos con Stock Bajo
    """
    return render_template('reports/inventory/low_stock.html')


@reports_bp.route('/api/inventory/low-stock')
@login_required
@permission_required('reports.inventory.view')
def api_inventory_low_stock():
    """
    API: Productos con stock bajo
    """
    try:
        low_stock_products = Laptop.query.filter(
            Laptop.quantity <= Laptop.min_alert
        ).order_by(Laptop.quantity).all()
        
        products = []
        for laptop in low_stock_products:
            products.append({
                'sku': laptop.sku,
                'name': laptop.display_name,
                'current_stock': laptop.quantity,
                'min_alert': laptop.min_alert,
                'missing': max(0, laptop.min_alert - laptop.quantity),
                'value': float(laptop.sale_price),
                'status': 'critical' if laptop.quantity == 0 else 'low'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'products': products,
                'total_count': len(products)
            }
        })
        
    except Exception as e:
        logger.error(f"Error en inventory_low_stock: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# ============================================
# REPORTES DE INVENTARIO ADICIONALES
# ============================================

@reports_bp.route('/inventory/movements')
@login_required
@permission_required('reports.inventory.view')
def inventory_movements():
    """Reporte: Movimientos de Inventario"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/inventory/movements.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/inventory/movements')
@login_required
@permission_required('reports.inventory.view')
def api_inventory_movements():
    """API: Movimientos de Inventario"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        query = db.session.query(
            SerialMovement,
            LaptopSerial.serial_number,
            Laptop.display_name,
            User.username
        ).join(LaptopSerial, SerialMovement.serial_id == LaptopSerial.id)\
         .join(Laptop, LaptopSerial.laptop_id == Laptop.id)\
         .outerjoin(User, SerialMovement.user_id == User.id)\
         .filter(func.date(SerialMovement.created_at).between(start_date, end_date))\
         .order_by(desc(SerialMovement.created_at))
         
        results = query.all()
        data = [{
            'date': r.SerialMovement.created_at.strftime('%Y-%m-%d %H:%M'),
            'type': r.SerialMovement.movement_type,
            'serial': r.serial_number,
            'product': r.display_name,
            'from': r.SerialMovement.previous_status,
            'to': r.SerialMovement.new_status,
            'user': r.username or 'Sistema',
            'description': r.SerialMovement.description
        } for r in results]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/inventory/turnover')
@login_required
@permission_required('reports.inventory.view')
def inventory_turnover():
    """Reporte: Análisis de Rotación"""
    return render_template('reports/inventory/turnover.html')

@reports_bp.route('/api/inventory/turnover')
@login_required
@permission_required('reports.inventory.view')
def api_inventory_turnover():
    """API: Rotación de Inventario"""
    try:
        # Simplificado: Ventas por marca en los últimos 90 días
        ninety_days_ago = date.today() - timedelta(days=90)
        
        results = db.session.query(
            Brand.name,
            func.count(InvoiceItem.id).label('sold_count')
        ).join(Laptop, InvoiceItem.product_id == Laptop.id)\
         .join(Brand, Laptop.brand_id == Brand.id)\
         .join(Invoice, InvoiceItem.invoice_id == Invoice.id)\
         .filter(Invoice.invoice_date >= ninety_days_ago, Invoice.status == 'paid')\
         .group_by(Brand.name).all()
         
        labels = [r[0] for r in results]
        values = [r[1] for r in results]
        
        return jsonify({
            'success': True,
            'data': {'labels': labels, 'values': values}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/inventory/valuation')
@login_required
@permission_required('reports.inventory.view')
def inventory_valuation():
    """Reporte: Valoración de Inventario"""
    return render_template('reports/inventory/valuation.html')

@reports_bp.route('/api/inventory/valuation')
@login_required
@permission_required('reports.inventory.view')
def api_inventory_valuation():
    """API: Valoración de Inventario"""
    try:
        query = db.session.query(
            Brand.name,
            func.sum(Laptop.quantity * Laptop.purchase_cost).label('total_cost'),
            func.sum(Laptop.quantity * Laptop.sale_price).label('total_value')
        ).join(Brand).group_by(Brand.name)
        
        results = query.all()
        
        data = [{
            'brand': r[0],
            'cost': float(r[1] or 0),
            'value': float(r[2] or 0),
            'profit': float((r[2] or 0) - (r[1] or 0))
        } for r in results]
        
        total_cost = sum(d['cost'] for d in data)
        total_value = sum(d['value'] for d in data)
        
        return jsonify({
            'success': True,
            'data': {
                'items': data,
                'total_cost': total_cost,
                'total_value': total_value
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/inventory/serials')
@login_required
@permission_required('reports.inventory.view')
def inventory_serials():
    """Reporte: Seriales"""
    return render_template('reports/inventory/serials.html')

@reports_bp.route('/api/inventory/serials')
@login_required
@permission_required('reports.inventory.view')
def api_inventory_serials():
    """API: Búsqueda de Seriales"""
    try:
        search = request.args.get('search', '').strip()
        query = db.session.query(
            LaptopSerial, Laptop.display_name
        ).join(Laptop)
        
        if search:
            query = query.filter(
                or_(
                    LaptopSerial.serial_number.ilike(f'%{search}%'),
                    Laptop.display_name.ilike(f'%{search}%')
                )
            )
        
        results = query.limit(100).all()
        
        data = [{
            'serial': r.LaptopSerial.serial_number,
            'product': r.display_name,
            'status': r.LaptopSerial.status,
            'cost': float(r.LaptopSerial.effective_cost),
            'days_in_inventory': (date.today() - (r.LaptopSerial.received_date or date.today())).days
        } for r in results]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# ============================================
# REPORTES DE CLIENTES ADICIONALES
# ============================================

@reports_bp.route('/customers/most-valuable')
@login_required
@permission_required('reports.customers.view')
def customers_most_valuable():
    """Reporte: Clientes Más Valiosos"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=365)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/customers/most_valuable.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/customers/most-valuable')
@login_required
@permission_required('reports.customers.view')
def api_customers_most_valuable():
    """API: Clientes más valiosos"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        limit = int(request.args.get('limit', 20))
        
        query = db.session.query(
            Customer.id,
            Customer.first_name,
            Customer.last_name,
            Customer.company_name,
            func.count(Invoice.id).label('invoice_count'),
            func.sum(Invoice.total).label('total_spent'),
            func.max(Invoice.invoice_date).label('last_purchase')
        ).join(Invoice).filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.status == 'paid'
        ).group_by(Customer.id).order_by(desc('total_spent')).limit(limit)
        
        results = query.all()
        data = [{
            'id': r.id,
            'name': f"{r.first_name} {r.last_name}" if r.first_name else r.company_name,
            'count': r.invoice_count,
            'total': float(r.total_spent),
            'last_purchase': r.last_purchase.isoformat() if r.last_purchase else None
        } for r in results]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/customers/retention')
@login_required
@permission_required('reports.customers.view')
def customers_retention():
    """Reporte: Análisis de Retención"""
    return render_template('reports/customers/retention.html')

@reports_bp.route('/api/customers/retention')
@login_required
@permission_required('reports.customers.view')
def api_customers_retention():
    """API: Análisis de Retención"""
    try:
        # Clientes que compraron en los últimos 90 días
        recent_cutoff = date.today() - timedelta(days=90)
        
        # Clientes activos (compra reciente)
        active_customers = db.session.query(Customer.id).join(Invoice).filter(
            Invoice.invoice_date >= recent_cutoff,
            Invoice.status == 'paid'
        ).distinct().count()
        
        # Total clientes
        total_customers = Customer.query.count()
        
        # Clientes recurrentes (más de 1 compra histórica)
        repeat_customers = db.session.query(Customer.id).join(Invoice).filter(
            Invoice.status == 'paid'
        ).group_by(Customer.id).having(func.count(Invoice.id) > 1).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total_customers,
                'active': active_customers,
                'repeat': repeat_customers,
                'churn_risk': total_customers - active_customers
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/customers/history/<int:customer_id>')
@login_required
@permission_required('reports.customers.view')
def customers_history(customer_id):
    """Reporte: Historial de Cliente"""
    customer = Customer.query.get_or_404(customer_id)
    return render_template('reports/customers/history.html', customer=customer)

@reports_bp.route('/api/customers/history/<int:customer_id>')
@login_required
@permission_required('reports.customers.view')
def api_customers_history(customer_id):
    """API: Historial de Cliente"""
    try:
        # Facturas
        invoices = Invoice.query.filter_by(customer_id=customer_id).order_by(desc(Invoice.invoice_date)).all()
        
        data = [{
            'date': inv.invoice_date.isoformat(),
            'type': 'invoice',
            'reference': inv.invoice_number,
            'amount': float(inv.total),
            'status': inv.status,
            'description': f"Factura {inv.invoice_number}"
        } for inv in invoices]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# REPORTES DE NCF (DGII)
# ============================================

@reports_bp.route('/ncf/summary')
@login_required
@permission_required('reports.ncf.view')
def ncf_summary():
    """Reporte: Resumen de Secuencias NCF"""
    return render_template('reports/ncf/summary.html')

@reports_bp.route('/api/ncf/summary')
@login_required
@permission_required('reports.ncf.view')
def api_ncf_summary():
    """API: Estado de Secuencias NCF"""
    try:
        sequences = NCFSequence.query.filter_by(is_active=True).all()
        
        data = [{
            'type': s.ncf_type,
            'name': s.name,
            'current': s.current_sequence,
            'remaining': s.remaining_count if s.range_end else 'Illimitado',
            'status': 'expired' if s.is_expired else ('exhausted' if s.is_exhausted else 'active'),
            'valid_until': s.valid_until.isoformat() if s.valid_until else None
        } for s in sequences]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/ncf/606')
@login_required
@permission_required('reports.ncf.view')
def ncf_606():
    """Reporte: 606 (Compras)"""
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/ncf/report_606.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/ncf/606')
@login_required
@permission_required('reports.ncf.view')
def api_ncf_606():
    """API: Datos para Reporte 606"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        # Nota: El modelo Expense actual no tiene campo NCF ni RNC del proveedor
        # Se muestra la información disponible
        expenses = Expense.query.filter(
            Expense.due_date.between(start_date, end_date)
        ).all()
        
        data = [{
            'rnc': '000000000', # No disponible en modelo
            'ncf': 'B0000000000', # No disponible en modelo
            'date': e.due_date.isoformat(),
            'amount': float(e.amount),
            'itbis': 0.00, # No desglosado en modelo
            'concept': e.description,
            'category': e.category_ref.name if e.category_ref else 'General'
        } for e in expenses]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/ncf/607')
@login_required
@permission_required('reports.ncf.view')
def ncf_607():
    """Reporte: 607 (Ventas)"""
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    return render_template('reports/ncf/report_607.html', start_date=start_date, end_date=end_date)

@reports_bp.route('/api/ncf/607')
@login_required
@permission_required('reports.ncf.view')
def api_ncf_607():
    """API: Datos para Reporte 607"""
    try:
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        invoices = Invoice.query.filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.status != 'draft' # Incluir pagadas y pendientes, excluir borradores
        ).all()
        
        data = [{
            'rnc': inv.customer.id_number if inv.customer else '',
            'type_id': 1 if inv.customer and inv.customer.id_type == 'rnc' else 2,
            'ncf': inv.ncf,
            'ncf_modified': '', # Para notas de crédito/débito
            'date': inv.invoice_date.isoformat(),
            'amount_invoiced': float(inv.subtotal),
            'itbis_invoiced': float(inv.tax_amount),
            'total': float(inv.total)
        } for inv in invoices]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# ============================================
# REPORTES DE CLIENTES
# ============================================

@reports_bp.route('/customers/overview')
@login_required
@permission_required('reports.customers.view')
def customers_overview():
    """
    Reporte: Base de Clientes
    """
    return render_template('reports/customers/overview.html')


@reports_bp.route('/api/customers/overview')
@login_required
@permission_required('reports.customers.view')
def api_customers_overview():
    """
    API: Resumen de clientes
    """
    try:
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(is_active=True).count()
        
        # Por tipo
        by_type = db.session.query(
            Customer.customer_type,
            func.count(Customer.id)
        ).group_by(Customer.customer_type).all()
        
        # Por provincia (top 10)
        by_province = db.session.query(
            Customer.province,
            func.count(Customer.id)
        ).filter(Customer.province.isnot(None)).group_by(
            Customer.province
        ).order_by(desc(func.count(Customer.id))).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'by_type': {
                    'labels': [t[0] for t in by_type],
                    'values': [t[1] for t in by_type]
                },
                'by_province': {
                    'labels': [p[0] for p in by_province],
                    'values': [p[1] for p in by_province]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error en customers_overview: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500





# ============================================
# REPORTES FINANCIEROS
# ============================================

@reports_bp.route('/financial/pnl')
@login_required
@permission_required('reports.financial.view')
def financial_pnl():
    """Reporte: Estado de Resultados (P&L)"""
    return render_template('reports/financial/pnl.html')

@reports_bp.route('/api/financial/pnl')
@login_required
@permission_required('reports.financial.view')
def api_financial_pnl():
    """API: Datos para P&L"""
    try:
        current_year = date.today().year
        
        # Ingresos por mes (Facturas pagadas)
        income_query = db.session.query(
            func.extract('month', Invoice.invoice_date).label('month'),
            func.sum(Invoice.total).label('total')
        ).filter(
            extract('year', Invoice.invoice_date) == current_year,
            Invoice.status == 'paid'
        ).group_by('month').all()
        
        # Gastos por mes (Expenses)
        expense_query = db.session.query(
            func.extract('month', Expense.due_date).label('month'),
            func.sum(Expense.amount).label('total')
        ).filter(
            extract('year', Expense.due_date) == current_year
        ).group_by('month').all()
        
        # Estructurar datos mes a mes (1-12)
        months = []
        income_data = []
        expense_data = []
        profit_data = []
        
        import calendar
        
        income_map = {int(r[0]): float(r[1] or 0) for r in income_query}
        expense_map = {int(r[0]): float(r[1] or 0) for r in expense_query}
        
        for m in range(1, 13):
            months.append(calendar.month_abbr[m])
            inc = income_map.get(m, 0.0)
            exp = expense_map.get(m, 0.0)
            income_data.append(inc)
            expense_data.append(exp)
            profit_data.append(inc - exp)
            
        return jsonify({
            'success': True,
            'data': {
                'months': months,
                'income': income_data,
                'expenses': expense_data,
                'profit': profit_data,
                'totals': {
                    'income': sum(income_data),
                    'expenses': sum(expense_data),
                    'profit': sum(profit_data)
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/financial/cashflow')
@login_required
@permission_required('reports.financial.view')
def financial_cashflow():
    """Reporte: Flujo de Caja"""
    return render_template('reports/financial/cashflow.html')

@reports_bp.route('/api/financial/cashflow')
@login_required
@permission_required('reports.financial.view')
def api_financial_cashflow():
    """API: Flujo de Caja (Visualización de liquidez en el tiempo)"""
    try:
        # Últimos 12 meses
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        # Unificar Facturas (Entradas) y Gastos (Salidas) en una línea de tiempo
        
        # Entradas
        infolist = db.session.query(
            Invoice.invoice_date.label('date'),
            Invoice.total.label('amount'),
            db.literal('IN').label('type')
        ).filter(
            Invoice.invoice_date.between(start_date, end_date),
            Invoice.status == 'paid'
        ).all()
        
        # Salidas
        outlist = db.session.query(
            Expense.due_date.label('date'),
            Expense.amount.label('amount'),
            db.literal('OUT').label('type')
        ).filter(
            Expense.due_date.between(start_date, end_date)
        ).all()
        
        # Combinar y ordenar
        combined = sorted(infolist + outlist, key=lambda x: x.date)
        
        balance = 0
        timeline = []
        
        # Agrupar por mes para el gráfico (más limpio)
        monthly_data = {}
        
        for item in combined:
            m_key = item.date.strftime('%Y-%m')
            val = float(item.amount) if item.type == 'IN' else -float(item.amount)
            
            if m_key not in monthly_data:
                monthly_data[m_key] = 0
            monthly_data[m_key] += val

        # Calcular acumulado
        accumulated_balance = 0
        labels = []
        data_points = []
        
        sorted_keys = sorted(monthly_data.keys())
        for k in sorted_keys:
            accumulated_balance += monthly_data[k]
            labels.append(k)
            data_points.append(accumulated_balance)
            
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'values': data_points,
                'current_balance': accumulated_balance
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/financial/expenses')
@login_required
@permission_required('reports.financial.view')
def financial_expenses():
    """Reporte: Análisis de Gastos"""
    return render_template('reports/financial/expenses.html')

@reports_bp.route('/api/financial/expenses')
@login_required
@permission_required('reports.financial.view')
def api_financial_expenses():
    """API: Desglose de gastos"""
    try:
        current_year = date.today().year
        
        query = db.session.query(
            ExpenseCategory.name,
            func.sum(Expense.amount)
        ).join(Expense).filter(
            extract('year', Expense.due_date) == current_year
        ).group_by(ExpenseCategory.name).all()
        
        labels = [r[0] for r in query]
        values = [float(r[1]) for r in query]
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'values': values,
                'total': sum(values)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# REPORTES OPERACIONALES
# ============================================

@reports_bp.route('/operational/activity')
@login_required
@permission_required('reports.audit.view')
def operational_activity():
    """Reporte: Actividad de Usuarios"""
    return render_template('reports/operational/activity.html')

@reports_bp.route('/api/operational/activity')
@login_required
@permission_required('reports.audit.view')
def api_operational_activity():
    """
    API: Muro de actividad.
    Combina:
    - Facturas creadas
    - Gastos registrados
    - Movimientos de seriales
    """
    try:
        limit = 50
        
        # 1. Movimientos de inventario (Ya tiene usuario)
        movements = db.session.query(
            SerialMovement.created_at.label('date'),
            User.username,
            db.literal('Inventario').label('module'),
            SerialMovement.description.label('action')
        ).outerjoin(User, SerialMovement.user_id == User.id).limit(limit).all()
        
        # 2. Facturas (Creador)
        invoices = db.session.query(
            Invoice.created_at.label('date'),
            User.username,
            db.literal('Ventas').label('module'),
            func.concat('Creó factura ', Invoice.invoice_number).label('action')
        ).outerjoin(User, Invoice.created_by_id == User.id).order_by(desc(Invoice.created_at)).limit(limit).all()
        
        # 3. Gastos
        expenses = db.session.query(
            Expense.created_at.label('date'),
            User.username,
            db.literal('Finanzas').label('module'),
            func.concat('Registró gasto: ', Expense.description).label('action')
        ).outerjoin(User, Expense.created_by == User.id).order_by(desc(Expense.created_at)).limit(limit).all()
        
        # Combinar y ordenar
        combined = sorted(movements + invoices + expenses, key=lambda x: x.date, reverse=True)[:limit]
        
        data = [{
            'date': item.date.strftime('%Y-%m-%d %H:%M:%S'),
            'user': item.username or 'Sistema',
            'module': item.module,
            'action': item.action
        } for item in combined]
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/operational/status')
@login_required
@permission_required('reports.audit.view')
def operational_status():
    """Reporte: Estado del Sistema"""
    return render_template('reports/operational/status.html')

@reports_bp.route('/api/operational/status')
@login_required
@permission_required('reports.audit.view')
def api_operational_status():
    """API: Métricas de salud del sistema"""
    try:
        # Conteos rápidos
        stats = {
            'products': Laptop.query.count(),
            'serials': LaptopSerial.query.count(),
            'customers': Customer.query.count(),
            'invoices': Invoice.query.count(),
            'expenses': Expense.query.count(),
            'db_size': 'N/A' # SQLite file size could be checked but avoiding FS ops
        }
        
        # Verificar conexión DB simple
        try:
            db.session.execute(text('SELECT 1'))
            db_status = 'Online'
        except:
            db_status = 'Offline'
            
        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'system_time': datetime.now().isoformat(),
                'db_status': db_status,
                'version': '1.0.0'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
