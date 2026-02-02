# -*- coding: utf-8 -*-
# ============================================
# MODELO DE ROL
# ============================================
# Define roles del sistema para RBAC

from datetime import datetime
from app import db


class Role(db.Model):
    """
    Modelo de Rol para sistema RBAC
    
    Un rol agrupa permisos y se asigna a usuarios.
    Ejemplo: 'Vendedor', 'Administrador', 'Contador'
    """
    __tablename__ = 'roles'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Flags
    is_system_role = db.Column(db.Boolean, default=False)  # Roles predefinidos no se pueden eliminar
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Auditoría
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relaciones (se definen en Permission y User)
    # permissions = relationship via role_permissions table
    # users = relationship via user_roles table
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission_name):
        """
        Verifica si el rol tiene un permiso específico
        
        Args:
            permission_name: Nombre del permiso (ej: 'inventory.create')
        
        Returns:
            bool: True si el rol tiene el permiso
        """
        return any(p.name == permission_name for p in self.permissions)
    
    def add_permission(self, permission):
        """
        Agregar permiso al rol
        
        Args:
            permission: Objeto Permission
        """
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission):
        """
        Remover permiso del rol
        
        Args:
            permission: Objeto Permission
        """
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def get_permission_names(self):
        """
        Obtiene lista de nombres de permisos
        
        Returns:
            list: Lista de nombres de permisos
        """
        return [p.name for p in self.permissions]
    
    def to_dict(self, include_permissions=False):
        """
        Serializa el rol a diccionario
        
        Args:
            include_permissions: Si incluir lista de permisos
        
        Returns:
            dict: Representación del rol
        """
        data = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'permission_count': len(self.permissions),
            'user_count': self.users.count() if hasattr(self, 'users') else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_permissions:
            data['permissions'] = [p.to_dict() for p in self.permissions]
        
        return data
    
    @staticmethod
    def get_by_name(name):
        """
        Obtiene un rol por su nombre
        
        Args:
            name: Nombre del rol
        
        Returns:
            Role: Objeto Role o None
        """
        return Role.query.filter_by(name=name).first()
    
    @staticmethod
    def get_active_roles():
        """
        Obtiene todos los roles activos
        
        Returns:
            list: Lista de roles activos
        """
        return Role.query.filter_by(is_active=True).order_by(Role.display_name).all()
