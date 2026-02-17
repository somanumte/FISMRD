# -*- coding: utf-8 -*-
# ============================================
# MODELO DE PERMISO V3.0
# ============================================
# Cambios V3:
#   - Agregado is_active para soft-delete de permisos
#   - Índice compuesto module + category

from datetime import datetime
from app import db


class Permission(db.Model):
    """
    Permiso granular para sistema RBAC.
    Ejemplo: 'inventory.create', 'invoices.delete', 'reports.view_financial'
    """
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    module = db.Column(db.String(50), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # V3: Agregado
    is_dangerous = db.Column(db.Boolean, default=False, nullable=False) # Agregado para seeding

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @staticmethod
    def get_by_name(name):
        """Busca un permiso por su nombre unico"""
        return Permission.query.filter_by(name=name).first()

    @classmethod
    def get_all_grouped_by_module(cls):
        """
        Obtiene todos los permisos agrupados por su modulo.
        Retorna: dict { 'modulo': [objetos_permiso] }
        """
        permissions = cls.query.filter_by(is_active=True).order_by(cls.module, cls.name).all()
        grouped = {}
        for p in permissions:
            if p.module not in grouped:
                grouped[p.module] = []
            grouped[p.module].append(p)
        return grouped

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'module': self.module,
            'category': self.category,
            'is_active': self.is_active,
            'is_dangerous': self.is_dangerous
        }

    def __repr__(self):
        return f'<Permission {self.name}>'

    __table_args__ = (
        db.Index('idx_permission_module_category', 'module', 'category'),
    )
