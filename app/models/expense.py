# -*- coding: utf-8 -*-
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    is_recurring = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20))  # monthly, weekly, daily, yearly
    advance_days = db.Column(db.Integer, default=7)
    auto_renew = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    category_ref = db.relationship('ExpenseCategory', backref='expenses', lazy='joined')
    creator = db.relationship('User', backref='expenses', lazy='joined')

    @hybrid_property
    def is_overdue(self):
        if self.is_paid:
            return False
        return self.due_date < date.today()

    @hybrid_property
    def days_until(self):
        if self.is_paid:
            return 0
        delta = self.due_date - date.today()
        return delta.days

    def _get_next_period_date(self, base_date):
        """Calcula la fecha exacta del siguiente periodo a partir de una fecha base"""
        if not base_date:
            return None
            
        next_date = base_date
        if self.frequency == 'daily':
            next_date = next_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            next_date = next_date + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            # Avanzar un mes manejando dÃ­as (ej: 31 Ene -> 28 Feb)
            year = next_date.year
            month = next_date.month + 1
            if month > 12:
                month = 1
                year += 1
            
            # Obtener Ãºltimo dÃ­a del prÃ³ximo mes
            import calendar
            _, last_day = calendar.monthrange(year, month)
            
            # Ajustar dÃ­a si excede el Ãºltimo dÃ­a del mes
            # Intentamos mantener el dÃ­a original del vencimiento base
            target_day = min(self.due_date.day, last_day)
            next_date = next_date.replace(year=year, month=month, day=target_day)

        elif self.frequency == 'yearly':
            try:
                next_date = next_date.replace(year=next_date.year + 1)
            except ValueError:
                # Caso bisiesto: 29 Feb -> 28 Feb
                next_date = next_date.replace(year=next_date.year + 1, day=28)
        
        return next_date

    @hybrid_property
    def next_due_date(self):
        if not self.is_recurring or not self.due_date:
            return None

        today = date.today()
        next_date = self.due_date

        # Si el vencimiento base es futuro, ese es el prÃ³ximo
        if next_date > today:
            return next_date

        # Avanzar hasta encontrar el primero >= hoy
        safety_break = 0
        while next_date <= today and safety_break < 100:
            safety_break += 1
            next_date = self._get_next_period_date(next_date)
            if not next_date: break

        return next_date

    def generate_next_occurrence(self):
        """Genera una nueva instancia para el prÃ³ximo periodo"""
        if not self.is_recurring:
            return None
        
        next_date = self.next_due_date
        if not next_date:
            return None
            
        return Expense(
            description=self.description,
            amount=self.amount,
            category_id=self.category_id,
            due_date=next_date,
            is_paid=False,
            is_recurring=True,
            frequency=self.frequency,
            advance_days=self.advance_days,
            auto_renew=self.auto_renew,
            notes=self.notes,
            created_by=self.created_by
        )

    def __repr__(self):
        return f'<Expense {self.id}: {self.description}>'

    def to_dict(self):
        """Serializar a diccionario para APIs"""
        return {
            'id': self.id,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0,
            'category_id': self.category_id,
            'category': {
                'id': self.category_ref.id if self.category_ref else None,
                'name': self.category_ref.name if self.category_ref else None,
                'color': self.category_ref.color if self.category_ref else None
            },
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'is_recurring': self.is_recurring,
            'frequency': self.frequency,
            'advance_days': self.advance_days,
            'auto_renew': self.auto_renew,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_by_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_overdue': self.is_overdue,
            'days_until': self.days_until,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'status': 'paid' if self.is_paid else ('overdue' if self.is_overdue else 'pending')
        }


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color = db.Column(db.String(50))  # Para UI styling
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ExpenseCategory {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }