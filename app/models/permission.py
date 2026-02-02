# -*- coding: utf-8 -*-
# ============================================
# MODELO DE PERMISO
# ============================================
# Define permisos granulares del sistema

from datetime import datetime
from app import db


class Permission(db.Model):
    """
    Modelo de Permiso para sistema RBAC
    
    Un permiso representa una acción específica que se puede realizar.
    Ejemplo: 'inventory.create', 'invoices.delete', 'reports.view_financial'
    """
    __tablename__ = 'permissions'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    
    # Categorización
    module = db.Column(db.String(50), nullable=False, index=True)  # 'inventory', 'invoices', etc.
    category = db.Column(db.String(50))  # 'view', 'manage', 'export', etc.
    
    # Flags
    is_dangerous = db.Column(db.Boolean, default=False)  # Permisos que requieren precaución
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones (se definen en Role)
    # roles = relationship via role_permissions table
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        """
        Serializa el permiso a diccionario
        
        Returns:
            dict: Representación del permiso
        """
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'module': self.module,
            'category': self.category,
            'is_dangerous': self.is_dangerous,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_by_name(name):
        """
        Obtiene un permiso por su nombre
        
        Args:
            name: Nombre del permiso
        
        Returns:
            Permission: Objeto Permission o None
        """
        return Permission.query.filter_by(name=name).first()
    
    @staticmethod
    def get_by_module(module):
        """
        Obtiene todos los permisos de un módulo
        
        Args:
            module: Nombre del módulo
        
        Returns:
            list: Lista de permisos
        """
        return Permission.query.filter_by(module=module).order_by(Permission.name).all()
    
    @staticmethod
    def get_all_grouped_by_module():
        """
        Obtiene todos los permisos agrupados por módulo
        
        Returns:
            dict: Diccionario {module: [permissions]}
        """
        permissions = Permission.query.order_by(Permission.module, Permission.name).all()
        grouped = {}
        
        for perm in permissions:
            if perm.module not in grouped:
                grouped[perm.module] = []
            grouped[perm.module].append(perm)
        
        return grouped
