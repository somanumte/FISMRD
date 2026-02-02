# -*- coding: utf-8 -*-
# ============================================
# DASHBOARD LUXERA - Versión Premium con IA
# ============================================

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.utils.decorators import permission_required
from app import db
from app.models.laptop import Laptop, Brand, LaptopModel
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

# Colores para gráficos
CHART_COLORS = {
    'primary': '#6366f1',  # Indigo
    'success': '#10b981',  # Emerald
    'danger': '#ef4444',  # Red
    'warning': '#f59e0b',  # Amber
    'info': '#3b82f6',  # Blue
    'purple': '#8b5cf6',  # Purple
    'pink': '#ec4899',  # Pink
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
    current_cogs_query = db.session.query(
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Laptop, InvoiceItem.laptop_id == Laptop.id
    ).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    )
    current_cogs = float(current_cogs_query.scalar() or 0)

    previous_cogs_query = db.session.query(
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Laptop, InvoiceItem.laptop_id == Laptop.id
    ).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    )
    previous_cogs = float(previous_cogs_query.scalar() or 0)

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
    inventory_value = db.session.query(
        func.sum(Laptop.purchase_cost * Laptop.quantity)
    ).scalar() or 0

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
    # Total de laptops
    total_laptops = Laptop.query.count()

    # Stock disponible (quantity - reserved)
    available_stock = db.session.query(
        func.sum(Laptop.quantity - Laptop.reserved_quantity)
    ).scalar() or 0

    # Stock bajo (<= min_alert)
    low_stock_query = Laptop.query.filter(
        (Laptop.quantity - Laptop.reserved_quantity) <= Laptop.min_alert,
        (Laptop.quantity - Laptop.reserved_quantity) > 0
    )
    low_stock_count = low_stock_query.count()
    low_stock_items = low_stock_query.limit(10).all()

    # Sin stock
    out_of_stock_count = Laptop.query.filter(
        (Laptop.quantity - Laptop.reserved_quantity) <= 0
    ).count()

    # Stock muerto (sin ventas en 90 días)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    dead_stock_query = Laptop.query.outerjoin(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).outerjoin(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        or_(
            Invoice.invoice_date < ninety_days_ago,
            Invoice.id.is_(None)
        )
    ).group_by(Laptop.id).having(
        func.count(InvoiceItem.id) == 0
    )
    dead_stock_count = dead_stock_query.count()
    dead_stock_items = dead_stock_query.limit(10).all()

    # Valor del inventario
    inventory_value = db.session.query(
        func.sum(Laptop.purchase_cost * Laptop.quantity)
    ).scalar() or 0

    inventory_sale_value = db.session.query(
        func.sum(Laptop.sale_price * Laptop.quantity)
    ).scalar() or 0

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
    inventory_turnover = (sales_last_30 / avg_inventory_value) if avg_inventory_value > 0 else 0
    avg_inventory_days = 365 / inventory_turnover if inventory_turnover > 0 else 0

    return {
        'summary': {
            'total_items': total_laptops,
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
            'dead_stock': dead_stock_items
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
            # Solo para facturas pagadas/completadas para ser cautos
            cogs = db.session.query(
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
            cogs = db.session.query(
                func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
            ).join(
                Invoice, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Laptop, InvoiceItem.laptop_id == Laptop.id
            ).filter(
                Invoice.invoice_date == day,
                Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
            ).scalar() or 0

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
                # Nota: Calcular beneficio diario exacto es complejo sin asignar gastos diarios.
                # Usaremos (Ventas - COGS) para beneficio bruto aproximado en gráficos diarios.
                cogs = db.session.query(
                    func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
                ).join(
                    Invoice, InvoiceItem.invoice_id == Invoice.id
                ).join(
                    Laptop, InvoiceItem.laptop_id == Laptop.id
                ).filter(
                    Invoice.invoice_date == current_day,
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0
                
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
                cogs = db.session.query(
                    func.sum(InvoiceItem.quantity * Laptop.purchase_cost)
                ).join(
                    Invoice, InvoiceItem.invoice_id == Invoice.id
                ).join(
                    Laptop, InvoiceItem.laptop_id == Laptop.id
                ).filter(
                    Invoice.invoice_date.between(current_month, month_end),
                    Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
                ).scalar() or 0

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


def get_brand_performance():
    """Obtiene rendimiento por marca basado en ventas reales"""
    # Filtrar solo marcas que tengan ventas reales en facturas
    brand_data = db.session.query(
        Brand.name,
        func.count(Laptop.id).label('product_count'),
        func.sum(
            case(
                (Laptop.quantity > 0, Laptop.quantity),
                else_=0
            )
        ).label('total_stock'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('sale_value'),
        func.sum(InvoiceItem.quantity * Laptop.purchase_cost).label('total_cost')
    ).join(
        Laptop, Brand.id == Laptop.brand_id
    ).outerjoin(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).outerjoin(
        Invoice, and_(
            InvoiceItem.invoice_id == Invoice.id,
            Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
        )
    ).group_by(
        Brand.name
    ).having(
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price) > 0
    ).order_by(
        desc('sale_value')
    ).limit(10).all()

    brands = []
    sales = []
    margins = []

    for brand in brand_data:
        brands.append(brand.name)
        revenue = float(brand.sale_value or 0)
        cost = float(brand.total_cost or 0)
        
        # Cálculo de margen ponderado: (Ventas Totales - Costo Total) / Ventas Totales
        if revenue > 0:
            margin = ((revenue - cost) / revenue) * 100
        else:
            margin = 0
            
        sales.append(revenue)
        margins.append(round(margin, 1))

    return {
        'brands': brands,
        'sales': sales,
        'margins': margins,
        'top_brand': brands[0] if brands else None,
        'top_margin': max(margins) if margins else 0
    }


def get_condition_performance():
    """Obtiene rendimiento por condición basado en ventas reales"""
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
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
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


def get_top_products(limit=10):
    """Obtiene productos más vendidos y rentables"""
    # Productos más vendidos (por unidades)
    top_selling = db.session.query(
        Brand.name.label('brand_name'),
        LaptopModel.name.label('model_name'),
        Laptop.sku,
        Laptop.category,
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.avg(
            (InvoiceItem.unit_price - Laptop.purchase_cost) / InvoiceItem.unit_price * 100
        ).label('margin')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Brand, Laptop.brand_id == Brand.id
    ).join(
        LaptopModel, Laptop.model_id == LaptopModel.id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(
        Laptop.id, Brand.name, LaptopModel.name, Laptop.sku, Laptop.category
    ).order_by(
        desc('units_sold')
    ).limit(limit).all()

    # Productos más rentables (por margen porcentual)
    top_profitable = db.session.query(
        Brand.name.label('brand_name'),
        LaptopModel.name.label('model_name'),
        Laptop.sku,
        Laptop.category,
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.avg(
            (InvoiceItem.unit_price - Laptop.purchase_cost) / InvoiceItem.unit_price * 100
        ).label('margin'),
        func.sum(
            InvoiceItem.quantity * (InvoiceItem.unit_price - Laptop.purchase_cost)
        ).label('total_profit')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Brand, Laptop.brand_id == Brand.id
    ).join(
        LaptopModel, Laptop.model_id == LaptopModel.id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(
        Laptop.id, Brand.name, LaptopModel.name, Laptop.sku, Laptop.category
    ).order_by(
        desc('margin')
    ).limit(limit).all()

    # Productos con mayores ganancias (por valor absoluto)
    top_revenue = db.session.query(
        Brand.name.label('brand_name'),
        LaptopModel.name.label('model_name'),
        Laptop.sku,
        Laptop.category,
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.avg(
            (InvoiceItem.unit_price - Laptop.purchase_cost) / InvoiceItem.unit_price * 100
        ).label('margin'),
        func.sum(
            InvoiceItem.quantity * (InvoiceItem.unit_price - Laptop.purchase_cost)
        ).label('total_profit')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Brand, Laptop.brand_id == Brand.id
    ).join(
        LaptopModel, Laptop.model_id == LaptopModel.id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(
        Laptop.id, Brand.name, LaptopModel.name, Laptop.sku, Laptop.category
    ).order_by(
        desc('total_profit')
    ).limit(limit).all()

    return {
        'top_selling': [
            {
                'brand': item.brand_name,
                'model': item.model_name,
                'sku': item.sku,
                'category': item.category,
                'units_sold': item.units_sold or 0,
                'revenue': float(item.revenue or 0),
                'margin': float(item.margin or 0),
                'profit': float((item.revenue or 0) * (item.margin or 0) / 100)
            }
            for item in top_selling
        ],
        'top_profitable': [
            {
                'brand': item.brand_name,
                'model': item.model_name,
                'sku': item.sku,
                'category': item.category,
                'units_sold': item.units_sold or 0,
                'revenue': float(item.revenue or 0),
                'margin': float(item.margin or 0),
                'profit': float(item.total_profit or 0)
            }
            for item in top_profitable
        ],
        'top_revenue': [
            {
                'brand': item.brand_name,
                'model': item.model_name,
                'sku': item.sku,
                'category': item.category,
                'units_sold': item.units_sold or 0,
                'revenue': float(item.revenue or 0),
                'margin': float(item.margin or 0),
                'profit': float(item.total_profit or 0)
            }
            for item in top_revenue
        ]
    }


def get_bcg_matrix_data(period='month'):
    """Genera datos para matriz BCG con crecimiento real"""
    start_date, end_date = get_date_range(period)
    prev_start, prev_end = get_previous_period(start_date, end_date)

    # Ventas periodo actual por producto (con margen promedio)
    current_sales_query = db.session.query(
        InvoiceItem.laptop_id.label('id'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.line_total).label('revenue'),
        func.avg(
            (InvoiceItem.unit_price - Laptop.purchase_cost) / InvoiceItem.unit_price * 100
        ).label('avg_margin')
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).join(
        Laptop, InvoiceItem.laptop_id == Laptop.id
    ).filter(
        Invoice.invoice_date.between(start_date, end_date),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(InvoiceItem.laptop_id).subquery()

    # Ventas periodo anterior por producto
    prev_sales_query = db.session.query(
        InvoiceItem.laptop_id.label('id'),
        func.sum(InvoiceItem.line_total).label('revenue')
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.invoice_date.between(prev_start, prev_end),
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(InvoiceItem.laptop_id).subquery()

    # Query principal combinando todo
    products_data = db.session.query(
        Laptop.display_name,
        Laptop.category,
        Brand.name.label('brand'),
        Laptop.quantity,
        func.coalesce(current_sales_query.c.units_sold, 0).label('units_sold'),
        func.coalesce(current_sales_query.c.revenue, 0).label('revenue'),
        func.coalesce(prev_sales_query.c.revenue, 0).label('prev_revenue'),
        func.coalesce(current_sales_query.c.avg_margin, 0).label('margin')
    ).join(
        Brand, Laptop.brand_id == Brand.id
    ).outerjoin(
        current_sales_query, Laptop.id == current_sales_query.c.id
    ).outerjoin(
        prev_sales_query, Laptop.id == prev_sales_query.c.id
    ).group_by(
        Laptop.id, Laptop.display_name, Laptop.category, Brand.name, Laptop.quantity,
        current_sales_query.c.units_sold, current_sales_query.c.revenue, prev_sales_query.c.revenue,
        current_sales_query.c.avg_margin
    ).all()

    # Total de unidades vendidas (para market share)
    total_market_units = sum(float(p.units_sold or 0) for p in products_data)

    # Preparar datos para análisis BCG
    bcg_data = []
    for product in products_data:
        units_sold = float(product.units_sold or 0)
        revenue = float(product.revenue or 0)
        prev_revenue = float(product.prev_revenue or 0)
        
        # Market Share relativo (porcentaje de ventas totales del catálogo)
        market_share = (units_sold / total_market_units * 100) if total_market_units > 0 else 0
        
        # Tasa de crecimiento REAL
        if prev_revenue > 0:
            growth_rate = ((revenue - prev_revenue) / prev_revenue) * 100
        else:
            growth_rate = 100 if revenue > 0 else 0

        # Determinar cuadrante BCG (ajustado a umbrales reales)
        # Market Share > 5% es alto (asumiendo muchos productos)
        # Growth > 10% es alto
        if market_share > 5 and growth_rate > 10:
            quadrant = 'star'
            color = CHART_COLORS['primary']
            label = 'Estrella'
        elif market_share > 5 and growth_rate <= 10:
            quadrant = 'cash_cow'
            color = CHART_COLORS['success']
            label = 'Vaca Lechera'
        elif market_share <= 5 and growth_rate > 10:
            quadrant = 'question_mark'
            color = CHART_COLORS['warning']
            label = 'Oportunidad'
        else:
            quadrant = 'dog'
            color = CHART_COLORS['gray']
            label = 'Riesgo'

        bcg_data.append({
            'name': product.display_name,
            'category': product.category or 'Sin categoría',
            'brand': product.brand,
            'x': round(market_share, 1),
            'y': round(growth_rate, 1),
            'z': revenue,
            'color': color,
            'label': label,
            'quadrant': quadrant,
            'units_sold': int(units_sold),
            'margin': round(float(product.margin or 0), 1),
            'profit': round(revenue * (float(product.margin or 0) / 100), 2)
        })

    # Análisis por cuadrante
    quadrant_analysis = {}
    for item in bcg_data:
        quadrant = item['label']
        if quadrant not in quadrant_analysis:
            quadrant_analysis[quadrant] = {
                'count': 0,
                'total_sales': 0,
                'total_profit': 0,
                'avg_margin': 0,
                'items': []
            }

        quadrant_analysis[quadrant]['count'] += 1
        quadrant_analysis[quadrant]['total_sales'] += item['z']
        quadrant_analysis[quadrant]['total_profit'] += item['profit']
        quadrant_analysis[quadrant]['items'].append(item['name'])

    # Calcular márgenes promedio por cuadrante
    for quadrant in quadrant_analysis:
        if quadrant_analysis[quadrant]['count'] > 0:
            items_in_quadrant = [item for item in bcg_data if item['label'] == quadrant]
            if items_in_quadrant:
                avg_margin = sum(item['margin'] for item in items_in_quadrant) / len(items_in_quadrant)
                quadrant_analysis[quadrant]['avg_margin'] = round(avg_margin, 2)

    return {
        'matrix_data': bcg_data,
        'quadrant_analysis': quadrant_analysis
    }


def get_recent_activity():
    """Obtiene actividad reciente"""
    # Facturas recientes
    recent_invoices = Invoice.query.order_by(
        Invoice.created_at.desc()
    ).limit(5).all()

    # Laptops recientemente agregadas
    recent_laptops = Laptop.query.order_by(
        Laptop.created_at.desc()
    ).limit(5).all()

    # Clientes recientes
    recent_customers = Customer.query.order_by(
        Customer.created_at.desc()
    ).limit(5).all()

    return {
        'invoices': recent_invoices,
        'laptops': recent_laptops,
        'customers': recent_customers
    }


def get_ai_insights(financial_data, inventory_data, sales_data, bcg_data):
    """Genera insights usando IA"""
    try:
        ai_context = {
            'financial': financial_data.get('metrics', {}),
            'inventory': inventory_data.get('summary', {}),
            'sales': sales_data,
            'period': financial_data.get('period_label', 'Mes')
        }

        # Generar reporte ejecutivo
        executive_report = AIService.generate_executive_report(
            financial_data.get('metrics', {}),
            inventory_data.get('summary', {}),
            sales_data
        )

        # Generar análisis BCG
        bcg_analysis = AIService.generate_bcg_matrix_analysis(
            bcg_data['matrix_data']
        )

        # Generar alertas prioritarias
        alerts = []

        # Alertas financieras
        if financial_data.get('metrics', {}).get('net_margin', 0) < 10:
            alerts.append({
                'type': 'danger',
                'icon': 'exclamation-circle',
                'title': 'Margen Neto Bajo',
                'message': f"El margen neto ({financial_data['metrics']['net_margin']:.1f}%) está por debajo del objetivo (10%).",
                'action': 'Revisar precios y costos',
                'link': 'dashboard.index'
            })

        # Alertas de inventario
        if inventory_data.get('summary', {}).get('dead_stock_count', 0) > 5:
            alerts.append({
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'title': 'Stock Muerto Detectado',
                'message': f"{inventory_data['summary']['dead_stock_count']} productos sin movimiento en 90 días.",
                'action': 'Crear promoción de liquidación',
                'link': 'inventory.laptops_list'
            })

        if inventory_data.get('summary', {}).get('low_stock_count', 0) > 3:
            alerts.append({
                'type': 'info',
                'icon': 'info-circle',
                'title': 'Stock Bajo',
                'message': f"{inventory_data['summary']['low_stock_count']} productos necesitan reabastecimiento.",
                'action': 'Ver inventario',
                'link': 'inventory.laptops_list'
            })

        # Alertas de ventas
        if financial_data.get('sales', {}).get('growth', 0) < 0:
            alerts.append({
                'type': 'danger',
                'icon': 'chart-line',
                'title': 'Crecimiento Negativo',
                'message': f"Ventas decrecieron {abs(financial_data['sales']['growth']):.1f}% vs período anterior.",
                'action': 'Analizar tendencias',
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

    # Obtener todos los datos
    financial_data = get_financial_metrics(period)
    inventory_data = get_inventory_analysis()
    sales_trends = get_sales_trends(period)
    brand_performance = get_brand_performance()
    top_products = get_top_products(10)
    bcg_data = get_bcg_matrix_data(period)
    # recent_activity = get_recent_activity() (Removed from UI)
    condition_performance = get_condition_performance()

    # Generar insights con IA
    ai_insights = get_ai_insights(financial_data, inventory_data, sales_trends, bcg_data)

    # Preparar datos para el template
    # Distribución por categoría REAL
    category_distribution_data = db.session.query(
        Laptop.category,
        func.count(Laptop.id).label('products'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.line_total).label('revenue')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid', 'completed', 'overdue', 'pending'])
    ).group_by(
        Laptop.category
    ).all()

    category_distribution = []
    for cd in category_distribution_data:
        category_distribution.append({
            'category': cd.category,
            'products': cd.products,
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

    return jsonify({
        'success': True,
        'data': {
            'financial': financial_data,
            'inventory': inventory_data['summary'],
            'sales_trends': sales_trends,
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