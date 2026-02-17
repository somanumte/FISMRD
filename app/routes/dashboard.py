# -*- coding: utf-8 -*-
# ============================================
# DASHBOARD LUXERA - Versión Premium con IA
# ============================================

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.utils.decorators import permission_required
from app import db
from app.models.laptop import Laptop, Brand, LaptopModel
from app.models.product import Product
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem, InvoiceSettings
from app.models.expense import Expense
from app.services.financial_service import FinancialService
from app.services.ai_service import AIService
from sqlalchemy import func, desc, and_, or_, extract, case
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

# Crear Blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# ============================================
# CONSTANTES Y CONFIGURACIÓN
# ============================================

PERIODS = {
    'today': 'Hoy',
    'week': 'Esta Semana',
    'month': 'Este Mes',
    'quarter': 'Este Trimestre',
    'year': 'Este Año'
}

# Colores para gráficos - Purple Gradient Theme
CHART_COLORS = {
    'primary': '#7c3aed',  # Purple (matching banner)
    'success': '#10b981',  # Emerald (kept for positive metrics)
    'danger': '#ef4444',  # Red (kept for negative metrics)
    'warning': '#f59e0b',  # Amber (kept for warnings)
    'info': '#a855f7',  # Light Purple (matching banner gradient)
    'purple': '#8b5cf6',  # Mid Purple
    'pink': '#c084fc',  # Light Purple Pink (matching banner end)
    'gray': '#6b7280'  # Gray
}


# ============================================
# FUNCIONES UTILITARIAS
# ============================================

def get_date_range(period='month'):
    """Obtiene rango de fechas para el período seleccionado"""
    today = date.today()

    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'quarter':
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_month, day=1)
        end_date = today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        # Por defecto, mes actual
        start_date = today.replace(day=1)
        end_date = today

    return start_date, end_date


def get_previous_period(start_date, end_date):
    """Obtiene el período anterior para comparación"""
    days_diff = (end_date - start_date).days
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=days_diff)
    return prev_start_date, prev_end_date


def format_currency(value):
    """Formatea valor como moneda"""
    try:
        return f"${float(value):,.2f}"
    except:
        return f"${0:,.2f}"


def calculate_growth(current, previous):
    """Calcula crecimiento porcentual"""
    if previous == 0:
        return 100 if current > 0 else 0

    return round(((current - previous) / previous) * 100, 1)


def get_trend_icon(value):
    """Devuelve icono y color basado en tendencia"""
    if value > 0:
        return {'icon': 'fa-arrow-up', 'color': 'green', 'class': 'positive'}
    elif value < 0:
        return {'icon': 'fa-arrow-down', 'color': 'red', 'class': 'negative'}
    else:
        return {'icon': 'fa-minus', 'color': 'gray', 'class': 'neutral'}


# ============================================
# FUNCIONES DE DATOS PRINCIPALES
# ============================================

def get_financial_metrics(period='month'):
    """Obtiene todas las métricas financieras para el período"""
    start_date, end_date = get_date_range(period)
    prev_start, prev_end = get_previous_period(start_date, end_date)

    # Ventas del período actual
    current_sales = db.session.query(
        func.sum(Invoice.subtotal).label('total_sales'),
        func.count(Invoice.id).label('invoice_count'),
        func.sum(
            case(
                (Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']), Invoice.subtotal),
                else_=0
            )
        ).label('paid_sales')
    ).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).first()

    # Ventas período anterior
    previous_sales = db.session.query(
        func.sum(Invoice.subtotal).label('total_sales'),
        func.count(Invoice.id).label('invoice_count')
    ).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).first()

    # Costos Reales (COGS)
    # Suma de (cantidad * costo_compra) de todos los items en facturas pagadas/completadas
    current_cogs_laptop = db.session.query(
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Laptop, InvoiceItem.laptop_id == Laptop.id
    ).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).scalar() or 0

    current_cogs_product = db.session.query(
        func.sum(InvoiceItem.quantity * Product.purchase_cost)
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Product, InvoiceItem.product_id == Product.id
    ).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).scalar() or 0
    
    current_cogs = float(current_cogs_laptop) + float(current_cogs_product)

    previous_cogs_laptop = db.session.query(
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Laptop, InvoiceItem.laptop_id == Laptop.id
    ).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).scalar() or 0

    previous_cogs_product = db.session.query(
        func.sum(InvoiceItem.quantity * Product.purchase_cost)
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Product, InvoiceItem.product_id == Product.id
    ).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).scalar() or 0
    
    previous_cogs = float(previous_cogs_laptop) + float(previous_cogs_product)

    # Gastos Operativos Reales
    # Suma de gastos pagados en el período
    current_expenses_query = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.paid_date.between(start_date, end_date),
        Expense.is_paid == True
    )
    current_expenses = float(current_expenses_query.scalar() or 0)

    previous_expenses_query = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.paid_date.between(prev_start, prev_end),
        Expense.is_paid == True
    )
    previous_expenses = float(previous_expenses_query.scalar() or 0)

    # Ventas
    current_sales_value = float(current_sales.total_sales or 0)
    previous_sales_value = float(previous_sales.total_sales or 0)

    # Calcular métricas financieras con datos reales
    current_data = [{
        'sales': current_sales_value,
        'cogs': current_cogs,
        'expenses': current_expenses,
        'invoice_count': current_sales.invoice_count or 0
    }]

    previous_data = [{
        'sales': previous_sales_value,
        'cogs': previous_cogs,
        'expenses': previous_expenses,
        'invoice_count': previous_sales.invoice_count or 0
    }]

    # Valor Inventario Real (actual) para cálculo de rotación
    inventory_value_laptop = db.session.query(
        func.sum(Laptop.purchase_cost * Laptop.quantity)
    ).scalar() or 0
    
    inventory_value_product = db.session.query(
        func.sum(Product.purchase_cost * Product.quantity)
    ).scalar() or 0
    
    inventory_value = float(inventory_value_laptop) + float(inventory_value_product)

    financial_metrics = FinancialService.calculate_financial_metrics(current_data, float(inventory_value))

    # Calcular tendencias
    growth_sales = calculate_growth(current_sales_value, previous_sales_value)
    
    previous_metrics = FinancialService.calculate_financial_metrics(previous_data, float(inventory_value))
    growth_profit = calculate_growth(
        financial_metrics.get('net_profit', 0),
        previous_metrics.get('net_profit', 0)
    )

    return {
        'period': period,
        'period_label': PERIODS.get(period, 'Mes'),
        'dates': {
            'current': {'start': start_date, 'end': end_date},
            'previous': {'start': prev_start, 'end': prev_end}
        },
        'sales': {
            'current': current_sales_value,
            'previous': previous_sales_value,
            'growth': growth_sales,
            'trend': get_trend_icon(growth_sales)
        },
        'metrics': financial_metrics,
        'trends': FinancialService.calculate_trend_analysis(current_data, previous_data)
    }


def get_inventory_analysis():
    """Analiza el estado del inventario"""
    # Total de items
    total_laptops = Laptop.query.count()
    total_products = Product.query.count()

    # Stock disponible (quantity - reserved)
    available_stock_laptop = db.session.query(
        func.sum(Laptop.quantity - Laptop.reserved_quantity)
    ).scalar() or 0
    
    available_stock_product = db.session.query(
        func.sum(Product.quantity)
    ).scalar() or 0
    
    available_stock = float(available_stock_laptop) + float(available_stock_product)

    # Stock bajo (<= min_alert)
    low_stock_laptop_query = Laptop.query.filter(
        (Laptop.quantity - Laptop.reserved_quantity) <= Laptop.min_alert,
        (Laptop.quantity - Laptop.reserved_quantity) > 0
    )
    low_stock_product_query = Product.query.filter(
        Product.quantity <= Product.min_alert,
        Product.quantity > 0
    )
    low_stock_count = low_stock_laptop_query.count() + low_stock_product_query.count()
    low_stock_items = low_stock_laptop_query.limit(5).all() + low_stock_product_query.limit(5).all()

    # Sin stock
    out_of_stock_laptop = Laptop.query.filter(
        (Laptop.quantity - Laptop.reserved_quantity) <= 0
    ).count()
    out_of_stock_product = Product.query.filter(
        Product.quantity <= 0
    ).count()
    out_of_stock_count = out_of_stock_laptop + out_of_stock_product

    # Stock muerto (Items con más de 90 días en inventario con stock)
    ninety_days_ago = date.today() - timedelta(days=90)
    dead_stock_laptop = Laptop.query.filter(
        Laptop.quantity > 0,
        Laptop.entry_date <= ninety_days_ago
    ).count()
    dead_stock_product = Product.query.filter(
        Product.quantity > 0,
        Product.entry_date <= ninety_days_ago
    ).count()
    dead_stock_count = dead_stock_laptop + dead_stock_product

    # Valor del inventario
    inventory_value_laptop = db.session.query(
        func.sum(Laptop.purchase_cost * Laptop.quantity)
    ).scalar() or 0
    inventory_value_product = db.session.query(
        func.sum(Product.purchase_cost * Product.quantity)
    ).scalar() or 0
    inventory_value = float(inventory_value_laptop) + float(inventory_value_product)

    inventory_sale_value_laptop = db.session.query(
        func.sum(Laptop.sale_price * Laptop.quantity)
    ).scalar() or 0
    inventory_sale_value_product = db.session.query(
        func.sum(Product.sale_price * Product.quantity)
    ).scalar() or 0
    inventory_sale_value = float(inventory_sale_value_laptop) + float(inventory_sale_value_product)

    # Potencial de ganancia
    potential_profit = inventory_sale_value - inventory_value

    # Rotación de inventario (simplificada)
    last_30_days = date.today() - timedelta(days=30)
    sales_last_30 = db.session.query(
        func.sum(Invoice.subtotal)
    ).filter(
        Invoice.invoice_date >= last_30_days,
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).scalar() or 0

    avg_inventory_value = inventory_value  # Simplificación
    inventory_turnover = (float(sales_last_30 or 0) / avg_inventory_value) if avg_inventory_value > 0 else 0
    avg_inventory_days = 365 / inventory_turnover if inventory_turnover > 0 else 0

    return {
        'summary': {
            'total_items': total_laptops + total_products,
            'available_stock': int(available_stock),
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'dead_stock_count': dead_stock_count,
            'inventory_value': float(inventory_value),
            'inventory_sale_value': float(inventory_sale_value),
            'potential_profit': float(potential_profit),
            'turnover': round(inventory_turnover, 2),
            'avg_days': round(avg_inventory_days, 2)
        },
        'alerts': {
            'low_stock': low_stock_items,
        }
    }


def get_sales_trends(period='month'):
    """Obtiene tendencias de ventas para gráficos"""
    start_date, end_date = get_date_range(period)

    # Determinar granularidad basada en período
    if period == 'today':
        # Por hora para hoy
        hours = []
        sales_data = []
        profit_data = []
        
        for i in range(24):
            hour_start = datetime.combine(start_date, datetime.min.time()) + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)

            sales = db.session.query(
                func.sum(Invoice.subtotal)
            ).filter(
                Invoice.created_at >= hour_start,
                Invoice.created_at < hour_end,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0
            
            # Ganancia horaria aproximada (Subtotal - Costo)
            cogs_laptop = db.session.query(
                func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
            ).join(
                Invoice, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Laptop, InvoiceItem.laptop_id == Laptop.id
            ).filter(
                Invoice.created_at >= hour_start,
                Invoice.created_at < hour_end,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0

            cogs_product = db.session.query(
                func.sum(InvoiceItem.quantity * Product.purchase_cost)
            ).join(
                Invoice, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Product, InvoiceItem.product_id == Product.id
            ).filter(
                Invoice.created_at >= hour_start,
                Invoice.created_at < hour_end,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0
            
            cogs = float(cogs_laptop) + float(cogs_product)

            hours.append(hour_start.strftime('%H:%M'))
            sales_data.append(float(sales))
            profit_data.append(float(sales) - float(cogs))

        return {
            'labels': hours,
            'datasets': [
                {
                    'label': 'Ventas',
                    'data': sales_data,
                    'color': CHART_COLORS['primary'],
                    'type': 'bar'
                },
                {
                    'label': 'Ganancia',
                    'data': profit_data,
                    'color': CHART_COLORS['success'],
                    'type': 'line'
                }
            ]
        }

    elif period == 'week':
        # Por día para la semana
        days = []
        sales_data = []
        profit_data = []

        for i in range(7):
            day = start_date + timedelta(days=i)
            if day > end_date:
                break

            # Ventas actuales
            sales = db.session.query(
                func.sum(Invoice.subtotal)
            ).filter(
                Invoice.invoice_date == day,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0

            # COGS del día
            cogs_laptop = db.session.query(
                func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
            ).join(
                Invoice, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Laptop, InvoiceItem.laptop_id == Laptop.id
            ).filter(
                Invoice.invoice_date == day,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0

            cogs_product = db.session.query(
                func.sum(InvoiceItem.quantity * Product.purchase_cost)
            ).join(
                Invoice, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Product, InvoiceItem.product_id == Product.id
            ).filter(
                Invoice.invoice_date == day,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0
            
            cogs = float(cogs_laptop) + float(cogs_product)

            days.append(day.strftime('%a'))
            sales_data.append(float(sales))
            profit_data.append(float(sales) - float(cogs))

        return {
            'labels': days,
            'datasets': [
                {
                    'label': 'Ventas',
                    'data': sales_data,
                    'color': CHART_COLORS['primary'],
                    'type': 'bar'
                },
                {
                    'label': 'Ganancia',
                    'data': profit_data,
                    'color': CHART_COLORS['success'],
                    'type': 'line'
                }
            ]
        }

    else:
        # Por mes para períodos más largos
        months = []
        sales_data = []
        profit_data = []

        if period == 'month':
            # Por día del mes
            current_day = start_date
            while current_day <= end_date:
                sales = db.session.query(
                    func.sum(Invoice.subtotal)
                ).filter(
                    Invoice.invoice_date == current_day,
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0

                # Calcular ganancia (Ventas - Costos)
                cogs_laptop = db.session.query(
                    func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
                ).join(
                    Invoice, InvoiceItem.invoice_id == Invoice.id
                ).join(
                    Laptop, InvoiceItem.laptop_id == Laptop.id
                ).filter(
                    Invoice.invoice_date == current_day,
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0

                cogs_product = db.session.query(
                    func.sum(InvoiceItem.quantity * Product.purchase_cost)
                ).join(
                    Invoice, InvoiceItem.invoice_id == Invoice.id
                ).join(
                    Product, InvoiceItem.product_id == Product.id
                ).filter(
                    Invoice.invoice_date == current_day,
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0
                
                cogs = float(cogs_laptop) + float(cogs_product)
                
                profit = float(sales) - float(cogs)

                months.append(current_day.strftime('%d/%m'))
                sales_data.append(float(sales))
                profit_data.append(profit)

                current_day += timedelta(days=1)

        elif period in ['quarter', 'year']:
            # Por mes
            current_month = start_date.replace(day=1)
            while current_month <= end_date:
                month_end = (current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                if month_end > end_date:
                    month_end = end_date

                sales = db.session.query(
                    func.sum(Invoice.subtotal)
                ).filter(
                    Invoice.invoice_date.between(current_month, month_end),
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0

                # COGS del mes
                cogs_laptop = db.session.query(
                    func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
                ).join(
                    Invoice, InvoiceItem.invoice_id == Invoice.id
                ).join(
                    Laptop, InvoiceItem.laptop_id == Laptop.id
                ).filter(
                    Invoice.invoice_date.between(current_month, month_end),
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0

                cogs_product = db.session.query(
                    func.sum(InvoiceItem.quantity * Product.purchase_cost)
                ).join(
                    Invoice, InvoiceItem.invoice_id == Invoice.id
                ).join(
                    Product, InvoiceItem.product_id == Product.id
                ).filter(
                    Invoice.invoice_date.between(current_month, month_end),
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0
                
                cogs = float(cogs_laptop) + float(cogs_product)

                # Gastos del mes
                expenses = db.session.query(
                    func.sum(Expense.amount)
                ).filter(
                    Expense.paid_date.between(current_month, month_end),
                    Expense.is_paid == True
                ).scalar() or 0

                profit = float(sales) - float(cogs) - float(expenses)

                months.append(current_month.strftime('%b'))
                sales_data.append(float(sales))
                profit_data.append(profit)

                # Siguiente mes
                current_month = month_end + timedelta(days=1)

        return {
            'labels': months,
            'datasets': [
                {
                    'label': 'Ventas',
                    'data': sales_data,
                    'color': CHART_COLORS['primary'],
                    'type': 'bar'
                },
                {
                    'label': 'Ganancia',
                    'data': profit_data,
                    'color': CHART_COLORS['success'],
                    'type': 'line'
                }
            ]
        }


def get_brand_performance(period='month'):
    """Obtiene rendimiento por marca basado en ventas reales CON FILTRO TEMPORAL"""
    start_date, end_date = get_date_range(period)

    # Marcas de Laptops
    laptop_brand_data = db.session.query(
        Brand.name,
        func.count(Laptop.id).label('product_count'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('sale_value'),
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost).label('total_cost')
    ).join(
        Laptop, Brand.id == Laptop.brand_id
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)
    ).group_by(Brand.name).all()

    # Marcas de Productos Genéricos (usando el campo string 'brand')
    product_brand_data = db.session.query(
        Product.brand.label('name'),
        func.count(Product.id).label('product_count'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('sale_value'),
        func.sum(InvoiceItem.quantity * Product.purchase_cost).label('total_cost')
    ).join(
        InvoiceItem, Product.id == InvoiceItem.product_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)
    ).group_by(Product.brand).all()

    # Combinar resultados
    brands = {}
    for b in laptop_brand_data:
        name = b.name or 'Genérico'
        brands[name] = {
            'count': b.product_count,
            'sales': float(b.sale_value or 0),
            'cost': float(b.total_cost or 0)
        }
    
    for b in product_brand_data:
        name = b.name or 'Genérico'
        if name in brands:
            brands[name]['count'] += b.product_count
            brands[name]['sales'] += float(b.sale_value or 0)
            brands[name]['cost'] += float(b.total_cost or 0)
        else:
            brands[name] = {
                'count': b.product_count,
                'sales': float(b.sale_value or 0),
                'cost': float(b.total_cost or 0)
            }

    # Formatear para el template
    formatted_brands = []
    top_brand = "N/A"
    max_sales = 0
    top_margin = 0

    for name, data in brands.items():
        margin = ((data['sales'] - data['cost']) / data['sales'] * 100) if data['sales'] > 0 else 0
        formatted_brands.append({
            'name': name,
            'product_count': data['count'],
            'sale_value': data['sales'],
            'margin': round(margin, 1)
        })
        if data['sales'] > max_sales:
            max_sales = data['sales']
            top_brand = name
            top_margin = margin

    # Ordenar por ventas
    sorted_brands = sorted(formatted_brands, key=lambda x: x['sale_value'], reverse=True)

    # Preparar listas para el gráfico
    brand_names = [b['name'] for b in sorted_brands]
    brand_sales = [b['sale_value'] for b in sorted_brands]
    brand_margins = [b['margin'] for b in sorted_brands]

    return {
        'brands': brand_names,
        'sales': brand_sales,
        'margins': brand_margins,
        'details': sorted_brands, # Mantener detalles por si se necesitan en tabla
        'top_brand': top_brand,
        'top_margin': round(top_margin, 1)
    }
def get_condition_performance(period='month'):
    """Obtiene rendimiento por condición basado en ventas reales CON FILTRO TEMPORAL"""
    start_date, end_date = get_date_range(period)
    
    data = db.session.query(
        Laptop.condition,
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost).label('total_cost')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)  # FILTRO TEMPORAL
    ).group_by(
        Laptop.condition
    ).all()

    conditions = []
    sales = []
    margins = []
    
    # Mapping for nice labels
    condition_labels = {
        'new': 'Nuevo',
        'used': 'Usado',
        'refurbished': 'Reacondicionado',
        'open_box': 'Open Box'
    }

    for item in data:
        label = condition_labels.get(item.condition, item.condition.capitalize())
        conditions.append(label)
        revenue = float(item.revenue or 0)
        cost = float(item.total_cost or 0)
        
        if revenue > 0:
            margin = ((revenue - cost) / revenue) * 100
        else:
            margin = 0
            
        sales.append(revenue)
        margins.append(round(margin, 1))

    return {
        'conditions': conditions,
        'sales': sales,
        'margins': margins
    }


def get_category_performance(period='month'):
    """Obtiene rendimiento por categoría CON FILTRO TEMPORAL, incluyendo productos genéricos"""
    start_date, end_date = get_date_range(period)
    
    # Categorías de Laptops
    laptop_categories = db.session.query(
        Laptop.category.label('category_name'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.line_total).label('revenue')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)
    ).group_by(Laptop.category).all()

    # Categorías de Productos Genéricos
    from app.models.product import ProductCategory
    product_categories = db.session.query(
        ProductCategory.name.label('category_name'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.line_total).label('revenue')
    ).join(
        Product, ProductCategory.id == Product.category_id
    ).join(
        InvoiceItem, Product.id == InvoiceItem.product_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)
    ).group_by(ProductCategory.name).all()

    # Combinar resultados
    all_categories = []
    for cat in laptop_categories:
        all_categories.append({'category': cat.category_name or 'Laptop', 'units_sold': cat.units_sold, 'revenue': cat.revenue})
    
    for cat in product_categories:
        # Si ya existe el nombre, sumar (poco probable por ser estructuras distintas pero posible)
        found = False
        for existing in all_categories:
            if existing['category'] == cat.category_name:
                existing['units_sold'] += cat.units_sold
                existing['revenue'] += cat.revenue
                found = True
                break
        if not found:
            all_categories.append({'category': cat.category_name, 'units_sold': cat.units_sold, 'revenue': cat.revenue})

    # Convertir de vuelta a objetos con atributos para compatibilidad
    from collections import namedtuple
    CatResult = namedtuple('CatResult', ['category', 'units_sold', 'revenue'])
    return [CatResult(**c) for c in all_categories]


def get_top_products(limit=10, period='month'):
    """Obtiene productos más vendidos y rentables CON FILTRO TEMPORAL"""
    start_date, end_date = get_date_range(period)

    # Laptops top
    top_laptops = db.session.query(
        Brand.name.label('brand_name'),
        LaptopModel.name.label('model_name'),
        Laptop.sku,
        Laptop.category,
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.sum(InvoiceItem.quantity * (InvoiceItem.unit_price - Laptop.purchase_cost)).label('total_profit'),
        func.avg((InvoiceItem.unit_price - Laptop.purchase_cost) / InvoiceItem.unit_price * 100).label('margin')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Brand, Laptop.brand_id == Brand.id
    ).join(
        LaptopModel, Laptop.model_id == LaptopModel.id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)
    ).group_by(Laptop.id, Brand.name, LaptopModel.name, Laptop.sku, Laptop.category).all()

    # Productos top
    from app.models.product import ProductCategory
    top_products_gen = db.session.query(
        Product.brand.label('brand_name'),
        Product.name.label('model_name'),
        Product.sku,
        ProductCategory.name.label('category'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.sum(InvoiceItem.quantity * (InvoiceItem.unit_price - Product.purchase_cost)).label('total_profit'),
        func.avg((InvoiceItem.unit_price - Product.purchase_cost) / InvoiceItem.unit_price * 100).label('margin')
    ).join(
        ProductCategory, Product.category_id == ProductCategory.id
    ).join(
        InvoiceItem, Product.id == InvoiceItem.product_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending']),
        Invoice.invoice_date.between(start_date, end_date)
    ).group_by(Product.id, Product.brand, Product.name, Product.sku, ProductCategory.name).all()

    # Combinar y procesar
    combined = []
    for item in top_laptops:
        combined.append({
            'brand': item.brand_name,
            'model': item.model_name,
            'sku': item.sku,
            'category': item.category,
            'units_sold': int(item.units_sold or 0),
            'revenue': float(item.revenue or 0),
            'profit': float(item.total_profit or 0),
            'margin': float(item.margin or 0)
        })
    
    for item in top_products_gen:
        combined.append({
            'brand': item.brand_name or 'Genérico',
            'model': item.model_name,
            'sku': item.sku,
            'category': item.category,
            'units_sold': int(item.units_sold or 0),
            'revenue': float(item.revenue or 0),
            'profit': float(item.total_profit or 0),
            'margin': float(item.margin or 0)
        })

    return {
        'top_selling': sorted(combined, key=lambda x: x['units_sold'], reverse=True)[:limit],
        'top_profitable': sorted(combined, key=lambda x: x['margin'], reverse=True)[:limit],
        'top_revenue': sorted(combined, key=lambda x: x['profit'], reverse=True)[:limit]
    }


def get_bcg_matrix_data(period='month'):
    """Genera datos para matriz BCG con crecimiento real (Laptops + Productos)"""
    start_date, end_date = get_date_range(period)
    prev_start, prev_end = get_previous_period(start_date, end_date)

    # 1. Obtener rendimiento de Laptops (Incluyendo ID)
    laptop_stats = db.session.query(
        Laptop.id,
        Laptop.display_name.label('name'),
        Laptop.category.label('category'),
        Brand.name.label('brand'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.line_total).label('revenue'),
        func.avg((InvoiceItem.unit_price - Laptop.purchase_cost) / InvoiceItem.unit_price * 100).label('margin')
    ).join(InvoiceItem, Laptop.id == InvoiceItem.laptop_id).join(Invoice, InvoiceItem.invoice_id == Invoice.id).join(Brand, Laptop.brand_id == Brand.id).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(Laptop.id, Laptop.display_name, Laptop.category, Brand.name).all()

    # 2. Obtener rendimiento de Productos Genéricos (Incluyendo ID)
    from app.models.product import ProductCategory
    product_stats = db.session.query(
        Product.id,
        Product.name.label('name'),
        ProductCategory.name.label('category'),
        Product.brand.label('brand'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.line_total).label('revenue'),
        func.avg((InvoiceItem.unit_price - Product.purchase_cost) / InvoiceItem.unit_price * 100).label('margin')
    ).join(InvoiceItem, Product.id == InvoiceItem.product_id).join(Invoice, InvoiceItem.invoice_id == Invoice.id).join(ProductCategory, Product.category_id == ProductCategory.id).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(Product.id, Product.name, ProductCategory.name, Product.brand).all()

    # 3. Obtener ventas anteriores para crecimiento
    laptop_prev = db.session.query(
        InvoiceItem.laptop_id.label('id'),
        func.sum(InvoiceItem.line_total).label('revenue')
    ).join(Invoice, InvoiceItem.invoice_id == Invoice.id).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(InvoiceItem.laptop_id).all()
    prev_laptop_map = {p.id: float(p.revenue or 0) for p in laptop_prev}

    product_prev = db.session.query(
        InvoiceItem.product_id.label('id'),
        func.sum(InvoiceItem.line_total).label('revenue')
    ).join(Invoice, InvoiceItem.invoice_id == Invoice.id).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(InvoiceItem.product_id).all()
    prev_product_map = {p.id: float(p.revenue or 0) for p in product_prev}

    # 4. Combinar y calcular metricas
    all_items = []
    
    # Calcular revenue total para market share relativo
    total_rev_laptops = sum(float(x.revenue or 0) for x in laptop_stats)
    total_rev_products = sum(float(x.revenue or 0) for x in product_stats)
    total_market_revenue = total_rev_laptops + total_rev_products
    
    # Procesar Laptops
    for l in laptop_stats:
        rev = float(l.revenue or 0)
        prev_rev = prev_laptop_map.get(l.id, 0)
        
        # Crecimiento vs periodo anterior
        growth = ((rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
        
        # Cuota de mercado relativa (vs total de ventas del negocio)
        share = (rev / total_market_revenue * 100) if total_market_revenue > 0 else 0
        
        all_items.append({
            'name': l.name,
            'category': l.category,
            'brand': l.brand,
            'units_sold': int(l.units_sold or 0),
            'sales': rev,
            'growth_rate': growth,
            'margin': float(l.margin or 0),
            'market_share': share
        })
        
    # Procesar Productos
    for p in product_stats:
        rev = float(p.revenue or 0)
        prev_rev = prev_product_map.get(p.id, 0)
        
        growth = ((rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
        share = (rev / total_market_revenue * 100) if total_market_revenue > 0 else 0
        
        all_items.append({
            'name': p.name,
            'category': p.category,
            'brand': p.brand or 'Genérico',
            'units_sold': int(p.units_sold or 0),
            'sales': rev,
            'growth_rate': growth,
            'margin': float(p.margin or 0),
            'market_share': share
        })

    return AIService.generate_bcg_matrix_analysis(all_items)


def get_ai_insights(financial_data, inventory_data, sales_trends, bcg_data):
    """Genera insights utilizando IA"""
    try:
        # Generar reporte ejecutivo
        executive_report = AIService.generate_executive_report(
            financial_data.get('metrics', {}),
            inventory_data.get('summary', {}),
            sales_trends
        )

        # El análisis BCG ya viene procesado en bcg_data
        bcg_analysis = bcg_data

        # Generar alertas basadas en datos
        alerts = []

        # Alertas de inventario
        if inventory_data.get('summary', {}).get('dead_stock_count', 0) > 5:
            alerts.append({
                'type': 'danger',
                'icon': 'skull-crossbones',
                'title': 'Stock Muerto Alto',
                'message': f"{inventory_data['summary']['dead_stock_count']} productos sin ventas en 90 días",
                'action': 'Ver productos',
                'link': 'inventory.laptops_list'
            })

        if inventory_data.get('summary', {}).get('low_stock_count', 0) > 3:
            alerts.append({
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'title': 'Stock Bajo',
                'message': f"{inventory_data['summary']['low_stock_count']} productos necesitan reabastecimiento",
                'action': 'Revisar inventario',
                'link': 'inventory.laptops_list'
            })

        # Alertas financieras
        if financial_data.get('metrics', {}).get('net_margin', 0) < 10:
            alerts.append({
                'type': 'warning',
                'icon': 'chart-line',
                'title': 'Margen Bajo',
                'message': f"Margen neto actual: {financial_data['metrics']['net_margin']:.1f}%",
                'action': 'Analizar precios',
                'link': 'inventory.laptops_list'
            })

        if financial_data.get('sales', {}).get('growth', 0) < 0:
            alerts.append({
                'type': 'danger',
                'icon': 'chart-bar',
                'title': 'Ventas en Descenso',
                'message': f"Las ventas han caído {abs(financial_data['sales']['growth']):.1f}% vs período anterior",
                'action': 'Ver tendencias',
                'link': 'dashboard.index'
            })

        # Insights positivos
        insights = []

        if financial_data.get('metrics', {}).get('net_margin', 0) > 20:
            insights.append({
                'type': 'success',
                'icon': 'chart-line',
                'title': 'Margen Excelente',
                'message': f"¡Margen neto del {financial_data['metrics']['net_margin']:.1f}%!",
                'suggestion': 'Mantén esta estrategia de precios.'
            })

        if inventory_data.get('summary', {}).get('turnover', 0) > 6:
            insights.append({
                'type': 'success',
                'icon': 'sync-alt',
                'title': 'Alta Rotación',
                'message': f"Rotación de inventario: {inventory_data['summary']['turnover']:.1f}x",
                'suggestion': 'El inventario se mueve rápidamente. ¡Excelente!'
            })

        if financial_data.get('sales', {}).get('growth', 0) > 15:
            insights.append({
                'type': 'success',
                'icon': 'rocket',
                'title': 'Crecimiento Acelerado',
                'message': f"Ventas crecieron {financial_data['sales']['growth']:.1f}%",
                'suggestion': 'Invierte en más inventario de productos populares.'
            })

        # Si no hay insights, agregar uno genérico
        if not insights:
            insights.append({
                'type': 'info',
                'icon': 'lightbulb',
                'title': 'Oportunidad de Mejora',
                'message': 'Analiza tus datos para identificar áreas de optimización.',
                'suggestion': 'Revisa el reporte ejecutivo para recomendaciones específicas.'
            })

        return {
            'executive_report': executive_report,
            'bcg_analysis': bcg_analysis,
            'alerts': alerts[:3],  # Máximo 3 alertas
            'insights': insights[:3]  # Máximo 3 insights
        }

    except Exception as e:
        print(f"Error en get_ai_insights: {e}")
        return {
            'executive_report': "Reporte no disponible en este momento.",
            'bcg_analysis': {},
            'alerts': [],
            'insights': []
        }


# ============================================
# RUTAS PRINCIPALES
# ============================================

@dashboard_bp.route('/')
@dashboard_bp.route('/<period>')
@login_required
@permission_required('dashboard.view')
def index(period='month'):
    """Dashboard principal"""
    # Validar período
    if period not in PERIODS:
        period = 'month'

    # Obtener todos los datos CON FILTRO TEMPORAL
    financial_data = get_financial_metrics(period)
    inventory_data = get_inventory_analysis()
    sales_trends = get_sales_trends(period)
    brand_performance = get_brand_performance(period)  # CON FILTRO TEMPORAL
    top_products = get_top_products(10, period)  # CON FILTRO TEMPORAL
    bcg_data = get_bcg_matrix_data(period)
    condition_performance = get_condition_performance(period)  # CON FILTRO TEMPORAL

    # Generar insights con IA
    ai_insights = get_ai_insights(financial_data, inventory_data, sales_trends, bcg_data)

    # Preparar datos para el template
    # Distribución por categoría REAL CON FILTRO TEMPORAL
    category_distribution_data = get_category_performance(period)

    category_distribution = []
    for cd in category_distribution_data:
        category_distribution.append({
            'category': cd.category,
            'units_sold': int(cd.units_sold or 0),
            'revenue': float(cd.revenue or 0)
        })

    # Preparar datos de categoría para gráficos
    category_chart_data = {
        'labels': [c['category'] for c in category_distribution],
        'sales': [c['revenue'] for c in category_distribution],
        'units': [c['units_sold'] for c in category_distribution]
    }

    # Tasa de conversión REAL
    total_customers_count = Customer.query.count()
    customers_with_invoices = db.session.query(func.count(func.distinct(Invoice.customer_id))).scalar() or 0
    conversion_rate = (customers_with_invoices / total_customers_count * 100) if total_customers_count > 0 else 0

    # Crecimiento de nuevos clientes
    new_customers_previous = Customer.query.filter(
        Customer.created_at.between(
            financial_data['dates']['previous']['start'],
            financial_data['dates']['previous']['end']
        )
    ).count()

    new_customers_current = Customer.query.filter(
        Customer.created_at >= financial_data['dates']['current']['start']
    ).count()

    customer_growth = calculate_growth(new_customers_current, new_customers_previous)

    # Indicadores de crecimiento REALES
    orders_previous = db.session.query(func.count(Invoice.id)).filter(
        Invoice.invoice_date.between(
            financial_data['dates']['previous']['start'],
            financial_data['dates']['previous']['end']
        ),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).scalar() or 0
    
    orders_growth = calculate_growth(financial_data['metrics'].get('invoice_count', 0), orders_previous)

    # Obtener configuración
    settings = InvoiceSettings.get_settings()
    
    # Calcular promedio diario REAL
    days_in_period = (financial_data['dates']['current']['end'] - financial_data['dates']['current']['start']).days + 1
    avg_daily_sales = financial_data['sales']['current'] / days_in_period if days_in_period > 0 else 0

    # Preparar datos para el template
    context = {
        # Configuración global
        'settings': settings,

        # Información del usuario y período
        'current_user': current_user,
        'current_period': period,
        'periods': PERIODS,

        # Datos financieros
        'financial_data': financial_data,
        'revenue_current': financial_data['sales']['current'],
        'revenue_previous': financial_data['sales']['previous'],
        'revenue_growth': financial_data['sales']['growth'],
        'revenue_trend': financial_data['sales']['trend'],

        'orders_current': financial_data['metrics'].get('invoice_count', 0),
        'gross_profit_current': financial_data['metrics'].get('gross_profit', 0),
        'net_profit_current': financial_data['metrics'].get('net_profit', 0),
        'gross_margin_current': financial_data['metrics'].get('gross_margin', 0),
        'net_margin_current': financial_data['metrics'].get('net_margin', 0),
        'break_even_point': financial_data['metrics'].get('break_even_point', 0),

        # Datos de inventario
        'inventory_data': inventory_data,
        'total_available': inventory_data['summary']['available_stock'],
        'low_stock_count': inventory_data['summary']['low_stock_count'],
        'out_of_stock_count': inventory_data['summary']['out_of_stock_count'],
        'dead_stock_count': inventory_data['summary']['dead_stock_count'],
        'inventory_value': inventory_data['summary']['inventory_value'],
        'inventory_sale_value': inventory_data['summary']['inventory_sale_value'],
        'potential_profit': inventory_data['summary']['potential_profit'],
        'inventory_turnover': inventory_data['summary']['turnover'],
        'avg_inventory_days': inventory_data['summary']['avg_days'],

        # Datos de ventas y tendencias
        'sales_trends': sales_trends,
        'daily_sales': json.dumps(sales_trends),  # Para JavaScript
        'avg_daily_sales': avg_daily_sales,

        # Datos de marcas y condición
        'brand_performance': brand_performance,
        'condition_performance': condition_performance,
        'category_chart_data': category_chart_data,
        'top_brand': brand_performance['top_brand'],
        'top_brand_margin': brand_performance['top_margin'],

        # Productos
        'top_products': top_products['top_selling'],
        'top_profitable': top_products['top_profitable'],
        'top_revenue': top_products['top_revenue'],

        # Matriz BCG
        'bcg_data': bcg_data,
        'bcg_matrix': json.dumps(bcg_data['matrix_data']),  # Para JavaScript

        # Clientes
        'active_customers': Customer.query.filter_by(is_active=True).count(),
        'total_customers': total_customers_count,
        'new_customers_current': new_customers_current,
        'conversion_rate': round(conversion_rate, 1),

        # Insights de IA
        'ai_insights': ai_insights,
        'executive_report': ai_insights['executive_report'],
        'alerts': ai_insights['alerts'],
        'insights': ai_insights['insights'],

        # Crecimiento e indicadores
        'growth_indicators': {
            'revenue': {
                'text': f"{financial_data['sales']['growth']}%",
                'icon': financial_data['sales']['trend']['icon'],
                'color': financial_data['sales']['trend']['color'],
                'class': financial_data['sales']['trend']['class']
            },
            'orders': {
                'text': f"{orders_growth}%",
                'icon': get_trend_icon(orders_growth)['icon'],
                'color': get_trend_icon(orders_growth)['color'],
                'class': get_trend_icon(orders_growth)['class']
            },
            'profit': {
                'text': f"{financial_data['trends'].get('net_profit', {}).get('change_percent', 0)}%",
                'icon': 'arrow-up' if financial_data['trends'].get('net_profit', {}).get('change_percent', 0) > 0 else 'arrow-down',
                'color': 'green' if financial_data['trends'].get('net_profit', {}).get('change_percent', 0) > 0 else 'red',
                'class': 'positive' if financial_data['trends'].get('net_profit', {}).get('change_percent', 0) > 0 else 'negative'
            },
            'customers': {
                'text': f"{customer_growth}%",
                'icon': get_trend_icon(customer_growth)['icon'],
                'color': get_trend_icon(customer_growth)['color'],
                'class': get_trend_icon(customer_growth)['class']
            }
        },

        # Distribución por categoría
        'category_distribution': category_distribution,

        # Colores para gráficos
        'chart_colors': CHART_COLORS
    }

    return render_template('/dashboard.html', **context)


@dashboard_bp.route('/api/chat', methods=['POST'])
@login_required
@permission_required('dashboard.view')
def chat_api():
    """API para chatbot IA"""
    try:
        data = request.get_json()
        prompt = data.get('message', '')

        # Obtener datos de contexto
        financial_data = get_financial_metrics('month')
        inventory_data = get_inventory_analysis()

        context = {
            'total_sales': financial_data['sales']['current'],
            'net_margin': financial_data['metrics']['net_margin'],
            'dead_stock_count': inventory_data['summary']['dead_stock_count'],
            'low_stock_count': inventory_data['summary']['low_stock_count'],
            'inventory_turnover': inventory_data['summary']['turnover']
        }

        # Generar respuesta (en producción, conectar con Gemini API)
        response = AIService.chat_with_gemini(prompt, context)

        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': "Lo siento, hubo un error procesando tu mensaje."
        })


@dashboard_bp.route('/api/refresh-data')
@login_required
@permission_required('dashboard.view')
def refresh_data():
    """API para refrescar datos del dashboard"""
    period = request.args.get('period', 'month')

    financial_data = get_financial_metrics(period)
    inventory_data = get_inventory_analysis()
    sales_trends = get_sales_trends(period)
    brand_performance = get_brand_performance(period)
    condition_performance = get_condition_performance(period)
    category_data = get_category_performance(period)

    return jsonify({
        'success': True,
        'data': {
            'financial': financial_data,
            'inventory': inventory_data['summary'],
            'sales_trends': sales_trends,
            'brand_performance': brand_performance,
            'condition_performance': condition_performance,
            'category_data': {
                'labels': [c.category for c in category_data],
                'sales': [float(c.revenue or 0) for c in category_data],
                'units': [int(c.units_sold or 0) for c in category_data]
            },
            'timestamp': datetime.now().isoformat()
        }
    })


@dashboard_bp.route('/api/sales-trends')
@login_required
@permission_required('dashboard.view')
def sales_trends_api():
    """API para obtener tendencias de ventas"""
    period = request.args.get('period', 'month')
    sales_trends = get_sales_trends(period)
    return jsonify(sales_trends)


@dashboard_bp.route('/api/generate-report')
@login_required
@permission_required('dashboard.view')
def generate_report():
    """Genera reporte ejecutivo completo"""
    try:
        period = request.args.get('period', 'month')

        financial_data = get_financial_metrics(period)
        inventory_data = get_inventory_analysis()
        sales_trends = get_sales_trends(period)

        report = AIService.generate_executive_report(
            financial_data.get('metrics', {}),
            inventory_data.get('summary', {}),
            sales_trends
        )

        return jsonify({
            'success': True,
            'report': report,
            'period': PERIODS.get(period, 'Mes'),
            'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M')
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })