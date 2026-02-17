# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.decorators import permission_required, any_permission_required
from app import db
from app.models.expense import Expense, ExpenseCategory
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_, extract, case, and_

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def handle_recurrence(expense):
    """
    Verifica y genera la siguiente ocurrencia si el gasto es recurrente, 
    auto-renew y está pagado.
    """
    if expense.is_paid and expense.is_recurring and expense.auto_renew:
        next_due = expense.next_due_date
        if next_due:
            # Verificar si ya existe para evitar duplicados
            existing = Expense.query.filter_by(
                description=expense.description,
                due_date=next_due,
                created_by=expense.created_by
            ).first()
            
            if not existing:
                next_occurrence = expense.generate_next_occurrence()
                if next_occurrence:
                    db.session.add(next_occurrence)
                    return True
    return False

# ============================================
# VISTAS PRINCIPALES
# ============================================

@bp.route('/')
@login_required
@permission_required('expenses.view')
def expenses_list():
    """Renderiza la vista principal de gastos"""
    # Solo pasamos datos estáticos necesarios para la carga inicial
    # Todo lo demás se carga vía API
    return render_template('Expenses/expenses_list.html')

@bp.route('/api/dashboard')
@login_required
@permission_required('expenses.view')
def api_dashboard_data():
    """API para obtener datos consolidados del dashboard"""
    try:
        today = date.today()
        # Obtener mes y año de filtros
        month = request.args.get('month', today.month, type=int)
        year = request.args.get('year', today.year, type=int)
        
        start_of_month = date(year, month, 1)
        # Fin de mes
        if month == 12:
            end_of_month = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(year, month + 1, 1) - timedelta(days=1)
            
        # 1. KPIs Principales (Mes Actual)
        # Total Gastos (Pagados + Pendientes del mes)
        total_month = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.created_by == current_user.id,
            Expense.due_date >= start_of_month,
            Expense.due_date <= end_of_month
        ).scalar()
        
        # Gastos Pendientes (Mes actual)
        pending_month = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.created_by == current_user.id,
            Expense.is_paid == False,
            Expense.due_date >= start_of_month,
            Expense.due_date <= end_of_month
        ).scalar()
        
        # Gastos Vencidos (Total histórico)
        overdue_total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.created_by == current_user.id,
            Expense.is_paid == False,
            Expense.due_date < today
        ).scalar()
        
        # Próximos Vencimientos (7 días, conteo)
        next_week = today + timedelta(days=7)
        upcoming_count = Expense.query.filter(
            Expense.created_by == current_user.id,
            Expense.is_paid == False,
            Expense.due_date >= today,
            Expense.due_date <= next_week
        ).count()
        
        # 2. Datos para Gráfico Diario (Mes Actual)
        # Agrupado por día
        daily_data_query = db.session.query(
            extract('day', Expense.due_date).label('day'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.created_by == current_user.id,
            Expense.due_date >= start_of_month,
            Expense.due_date <= end_of_month
        ).group_by(extract('day', Expense.due_date)).all()
        
        # Rellenar días vacíos
        days_in_month = list(range(1, end_of_month.day + 1))
        daily_map = {d.day: float(d.total) for d in daily_data_query}
        chart_daily = {
            'labels': days_in_month,
            'data': [daily_map.get(day, 0) for day in days_in_month]
        }

        # 3. Datos para Gráfico Categorías (Mes Actual)
        category_data_query = db.session.query(
            ExpenseCategory.name,
            ExpenseCategory.color,
            func.sum(Expense.amount).label('total')
        ).join(Expense).filter(
            Expense.created_by == current_user.id,
            Expense.due_date >= start_of_month,
            Expense.due_date <= end_of_month
        ).group_by(ExpenseCategory.name, ExpenseCategory.color).all()
        
        chart_categories = [{
            'name': c.name,
            'color': c.color or '#808080',
            'value': float(c.total)
        } for c in category_data_query]

        return jsonify({
            'kpi': {
                'total_month': float(total_month),
                'pending_month': float(pending_month),
                'overdue_total': float(overdue_total),
                'upcoming_count': upcoming_count
            },
            'charts': {
                'daily': chart_daily,
                'categories': chart_categories
            }
        })
        
    except Exception as e:
        print(f"Error in dashboard backend: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/list')
@login_required
@permission_required('expenses.list')
def api_list_expenses():
    """API para listar gastos con filtros y paginación"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'all')
        category_id = request.args.get('category_id', 'all')
        month = request.args.get('month', None, type=int)
        year = request.args.get('year', None, type=int)
        is_recurring = request.args.get('is_recurring', 'all')
        
        query = Expense.query.filter_by(created_by=current_user.id)
        
        # Filtros de periodo
        if year:
            query = query.filter(extract('year', Expense.due_date) == year)
        if month:
            query = query.filter(extract('month', Expense.due_date) == month)

        if is_recurring == 'true':
            query = query.filter(Expense.is_recurring == True)
        elif is_recurring == 'false':
            query = query.filter(Expense.is_recurring == False)
        
        # Filtros
        if search:
            query = query.filter(
                or_(
                    Expense.description.ilike(f'%{search}%'),
                    Expense.notes.ilike(f'%{search}%')
                )
            )
            
        if status == 'pending':
            query = query.filter(Expense.is_paid == False, Expense.due_date >= date.today())
        elif status == 'overdue':
            query = query.filter(Expense.is_paid == False, Expense.due_date < date.today())
        elif status == 'paid':
            query = query.filter(Expense.is_paid == True)
            
        if category_id != 'all' and category_id.isdigit():
            query = query.filter_by(category_id=int(category_id))
            
        # Ordenar por fecha de vencimiento desc
        expenses_paginated = query.order_by(Expense.due_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'expenses': [e.to_dict() for e in expenses_paginated.items],
            'total': expenses_paginated.total,
            'pages': expenses_paginated.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('expenses.create', audit_action='create_expense', audit_module='expenses')
def api_create_expense():
    """Crear un nuevo gasto"""
    try:
        data = request.json
        
        # Validaciones básicas
        if not data.get('description') or not data.get('amount') or not data.get('category_id'):
            return jsonify({'error': 'Campos requeridos faltantes'}), 400
            
        expense = Expense(
            description=data['description'],
            amount=float(data['amount']),
            category_id=int(data['category_id']),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            is_paid=data.get('is_paid', False),
            is_recurring=data.get('is_recurring', False),
            frequency=data.get('frequency'),
            advance_days=int(data.get('advance_days', 7)),
            auto_renew=data.get('auto_renew', False),
            notes=data.get('notes'),
            created_by=current_user.id
        )
        
        if expense.is_paid and not expense.paid_date:
            expense.paid_date = date.today()
            
        db.session.add(expense)
        
        # Generar próxima recurrencia si aplica
        handle_recurrence(expense)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Gasto creado', 'expense': expense.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/<int:expense_id>', methods=['DELETE'])
@login_required
@permission_required('expenses.delete', audit_action='delete_expense', audit_module='expenses')
def api_delete_expense(expense_id):
    """Eliminar un gasto"""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.created_by != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
        
    try:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Gasto eliminado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/<int:expense_id>', methods=['PUT'])
@login_required
@permission_required('expenses.edit', audit_action='edit_expense', audit_module='expenses')
def api_update_expense(expense_id):
    """Actualizar un gasto"""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.created_by != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
        
    try:
        data = request.json
        expense.description = data.get('description', expense.description)
        expense.amount = float(data.get('amount', expense.amount))
        expense.category_id = int(data.get('category_id', expense.category_id))
        if 'due_date' in data:
            expense.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        
        expense.is_recurring = data.get('is_recurring', expense.is_recurring)
        expense.frequency = data.get('frequency', expense.frequency)
        expense.auto_renew = data.get('auto_renew', expense.auto_renew)
        expense.notes = data.get('notes', expense.notes)
        
        # Actualización de estado pagado
        if 'is_paid' in data:
            new_paid_status = data['is_paid']
            if new_paid_status and not expense.is_paid:
                expense.is_paid = True
                expense.paid_date = date.today()
            elif not new_paid_status:
                expense.is_paid = False
                expense.paid_date = None
        
        # Generar próxima recurrencia si aplica (por si se marcó como pagado ahora)
        handle_recurrence(expense)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Gasto actualizado', 'expense': expense.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/<int:expense_id>/toggle-status', methods=['POST'])
@login_required
@permission_required('expenses.edit', audit_action='toggle_expense_status', audit_module='expenses')
def api_toggle_status(expense_id):
    """Cambiar estado de pago rápidamente"""
    expense = Expense.query.get_or_404(expense_id)
    if expense.created_by != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
        
    try:
        expense.is_paid = not expense.is_paid
        expense.paid_date = date.today() if expense.is_paid else None
        
        # Lógica de recurrencia centralizada
        handle_recurrence(expense)
        
        db.session.commit()
        return jsonify({'success': True, 'new_status': expense.is_paid})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/categories')
@login_required
@permission_required('expenses.view')
def api_get_categories():
    """Obtener todas las categorías"""
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return jsonify([c.to_dict() for c in categories])


@bp.route('/api/sync-recurring', methods=['POST'])
@login_required
@permission_required('expenses.create')
def api_sync_recurring():
    """Sincroniza gastos recurrentes para asegurar que existan los del periodo seleccionado"""
    try:
        today = date.today()
        # Obtener mes y año objetivo del request
        target_month = request.args.get('month', today.month, type=int)
        target_year = request.args.get('year', today.year, type=int)
        
        # El límite superior de la sincronización es el último día del mes seleccionado
        import calendar
        _, last_day = calendar.monthrange(target_year, target_month)
        sync_boundary = date(target_year, target_month, last_day)

        # Si el periodo seleccionado es pasado, sincronizar al menos hasta hoy
        if sync_boundary < today:
            sync_boundary = today
        # Buscar gastos marcados como recurrentes y con auto-renew
        recurring_base_expenses = Expense.query.filter_by(
            created_by=current_user.id,
            is_recurring=True,
            auto_renew=True
        ).all()
        
        created_count = 0
        for expense in recurring_base_expenses:
            # Obtener el más reciente (por fecha de vencimiento)
            latest = Expense.query.filter_by(
                description=expense.description,
                created_by=current_user.id
            ).order_by(Expense.due_date.desc()).first()
            
            if latest:
                # Calcular la fecha del siguiente periodo
                next_date = latest._get_next_period_date(latest.due_date)
                
                # Generar gastos mientras no excedamos el límite
                inner_count = 0
                while next_date and next_date <= sync_boundary and inner_count < 24:
                    # Evitar duplicados
                    exists = Expense.query.filter_by(
                        description=expense.description,
                        due_date=next_date,
                        created_by=current_user.id
                    ).first()
                    
                    if not exists:
                        new_occurrence = latest.generate_next_occurrence()
                        if new_occurrence:
                            new_occurrence.due_date = next_date
                            db.session.add(new_occurrence)
                            db.session.flush()
                            latest = new_occurrence
                            created_count += 1
                        else:
                            break
                    else:
                        latest = exists
                    
                    # Avanzar a la siguiente fecha para el siguiente ciclo del while
                    next_date = latest._get_next_period_date(latest.due_date)
                    inner_count += 1
                        
                    if created_count > 100: break

        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Se generaron {created_count} gastos recurrentes pendientes.',
            'created_count': created_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/categories/stats')
@login_required
@permission_required('expenses.view')
def categories_stats():
    """Estadísticas detalladas por categoría"""
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date_obj = date.today().replace(day=1)
        end_date_obj = date.today()

    # Obtener estadísticas por categoría
    category_stats = db.session.query(
        ExpenseCategory.id,
        ExpenseCategory.name,
        ExpenseCategory.color,
        func.count(Expense.id).label('expense_count'),
        func.coalesce(func.sum(Expense.amount), 0).label('total_amount'),
        func.avg(Expense.amount).label('average_amount'),
        func.max(Expense.amount).label('max_amount'),
        func.min(Expense.amount).label('min_amount')
    ).outerjoin(
        Expense, and_(
            Expense.category_id == ExpenseCategory.id,
            Expense.created_by == current_user.id,
            Expense.due_date >= start_date_obj,
            Expense.due_date <= end_date_obj
        )
    ).group_by(
        ExpenseCategory.id,
        ExpenseCategory.name,
        ExpenseCategory.color
    ).order_by(
        func.coalesce(func.sum(Expense.amount), 0).desc()
    ).all()

    # Calcular porcentajes
    grand_total = sum(stat.total_amount or 0 for stat in category_stats)

    result = []
    for stat in category_stats:
        percentage = (stat.total_amount / grand_total * 100) if grand_total > 0 else 0

        result.append({
            'id': stat.id,
            'name': stat.name,
            'color': stat.color or '#2D64B3',
            'expense_count': stat.expense_count or 0,
            'total_amount': float(stat.total_amount) if stat.total_amount else 0,
            'average_amount': float(stat.average_amount) if stat.average_amount else 0,
            'max_amount': float(stat.max_amount) if stat.max_amount else 0,
            'min_amount': float(stat.min_amount) if stat.min_amount else 0,
            'percentage': round(percentage, 2)
        })

    return jsonify({
        'categories': result,
        'period': {
            'start_date': start_date_obj.isoformat(),
            'end_date': end_date_obj.isoformat()
        },
        'totals': {
            'grand_total': float(grand_total),
            'total_expenses': sum(item['expense_count'] for item in result)
        }
    })


# ============================================
# RUTAS EXISTENTES (IMPLEMENTAR)
# ============================================

@bp.route('/export')
@login_required
@permission_required('expenses.export')
def expense_export():
    """Exportar gastos a CSV"""
    try:
        # Obtener todos los gastos del usuario
        expenses = Expense.query.filter_by(created_by=current_user.id).all()

        # Crear output en memoria
        output = io.StringIO()
        writer = csv.writer(output)

        # Escribir encabezados
        writer.writerow([
            'ID', 'Descripción', 'Monto', 'Categoría', 'Fecha Vencimiento',
            'Pagado', 'Fecha Pago', 'Recurrente', 'Frecuencia', 'Notas'
        ])

        # Escribir datos
        for expense in expenses:
            writer.writerow([
                expense.id,
                expense.description,
                float(expense.amount),
                expense.category_ref.name if expense.category_ref else '',
                expense.due_date.strftime('%Y-%m-%d') if expense.due_date else '',
                'Sí' if expense.is_paid else 'No',
                expense.paid_date.strftime('%Y-%m-%d') if expense.paid_date else '',
                'Sí' if expense.is_recurring else 'No',
                expense.frequency or '',
                expense.notes or ''
            ])

        # Preparar respuesta
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'gastos_export_{timestamp}.csv'

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'error')
        return redirect(url_for('expenses.expenses_list'))


@bp.route('/categories')
@login_required
@permission_required('expenses.view')
def categories_list():
    """Listar categorías de gastos"""
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()

    # Obtener estadísticas por categoría
    category_stats = []
    for category in categories:
        expense_count = Expense.query.filter_by(
            category_id=category.id,
            created_by=current_user.id
        ).count()

        total_amount = db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.category_id == category.id,
            Expense.created_by == current_user.id
        ).scalar() or 0

        category_stats.append({
            'category': category,
            'expense_count': expense_count,
            'total_amount': float(total_amount)
        })

    return render_template(
        'expenses/categories.html',  # Necesitarás crear este template
        categories=category_stats
    )


@bp.route('/categories/create', methods=['POST'])
@login_required
@permission_required('expenses.create')
def category_create():
    """Crear nueva categoría de gastos"""
    try:
        name = request.form.get('name')
        color = request.form.get('color')
        description = request.form.get('description')

        if not name:
            flash('El nombre de la categoría es requerido', 'error')
            return redirect(url_for('expenses.categories_list'))

        # Verificar si ya existe
        existing = ExpenseCategory.query.filter_by(name=name).first()
        if existing:
            flash('Ya existe una categoría con ese nombre', 'error')
            return redirect(url_for('expenses.categories_list'))

        # Crear categoría
        category = ExpenseCategory(
            name=name,
            color=color,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        flash('Categoría creada exitosamente', 'success')
        return redirect(url_for('expenses.categories_list'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear categoría: {str(e)}', 'error')
        return redirect(url_for('expenses.categories_list'))


# Función para crear categorías por defecto
def create_default_categories():
    """Crear categorías por defecto si no existen"""
    default_categories = [
        {'name': 'Alquiler', 'color': 'bg-red-100 text-red-800'},
        {'name': 'Servicios', 'color': 'bg-blue-100 text-blue-800'},
        {'name': 'Salarios', 'color': 'bg-green-100 text-green-800'},
        {'name': 'Marketing', 'color': 'bg-purple-100 text-purple-800'},
        {'name': 'Suministros', 'color': 'bg-yellow-100 text-yellow-800'},
        {'name': 'Mantenimiento', 'color': 'bg-indigo-100 text-indigo-800'},
        {'name': 'Impuestos', 'color': 'bg-pink-100 text-pink-800'},
        {'name': 'Transporte', 'color': 'bg-gray-100 text-gray-800'},
    ]

    for cat_data in default_categories:
        if not ExpenseCategory.query.filter_by(name=cat_data['name']).first():
            category = ExpenseCategory(
                name=cat_data['name'],
                color=cat_data['color']
            )
            db.session.add(category)

    db.session.commit()