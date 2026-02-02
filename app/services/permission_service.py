# -*- coding: utf-8 -*-
# ============================================
# SERVICIO DE PERMISOS
# ============================================
# Lógica de negocio para gestión de permisos

from app import db
from app.models.permission import Permission
from flask_login import current_user


class PermissionService:
    """
    Servicio para gestión de permisos del sistema RBAC
    
    Proporciona métodos para:
    - Verificar permisos de usuarios
    - Crear y gestionar permisos
    - Consultar permisos por módulo
    """
    
    @staticmethod
    def check_permission(permission_name, user=None):
        """
        Verifica si un usuario tiene un permiso específico
        
        Args:
            permission_name (str): Nombre del permiso (ej: 'inventory.create')
            user: Usuario a verificar (default: current_user)
        
        Returns:
            bool: True si el usuario tiene el permiso
        
        Ejemplo:
            if PermissionService.check_permission('inventory.delete'):
                # Permitir eliminar
        """
        if user is None:
            if not current_user.is_authenticated:
                return False
            user = current_user
        
        return user.has_permission(permission_name)
    
    @staticmethod
    def require_permission(permission_name, user=None):
        """
        Lanza excepción si el usuario no tiene el permiso
        
        Args:
            permission_name (str): Nombre del permiso requerido
            user: Usuario a verificar (default: current_user)
        
        Raises:
            403: Si el usuario no tiene el permiso
        
        Ejemplo:
            PermissionService.require_permission('invoices.delete')
            # Continúa solo si tiene permiso, sino lanza 403
        """
        from flask import abort
        
        if not PermissionService.check_permission(permission_name, user):
            abort(403, description=f"Permiso requerido: {permission_name}")
    
    @staticmethod
    def get_all_permissions():
        """
        Obtiene todos los permisos del sistema
        
        Returns:
            list: Lista de objetos Permission ordenados por módulo y nombre
        
        Ejemplo:
            perms = PermissionService.get_all_permissions()
            for perm in perms:
                print(f"{perm.module}.{perm.name}")
        """
        return Permission.query.order_by(
            Permission.module, 
            Permission.name
        ).all()
    
    @staticmethod
    def get_permissions_by_module(module):
        """
        Obtiene permisos de un módulo específico
        
        Args:
            module (str): Nombre del módulo (ej: 'inventory', 'invoices')
        
        Returns:
            list: Lista de permisos del módulo
        
        Ejemplo:
            inv_perms = PermissionService.get_permissions_by_module('inventory')
        """
        return Permission.query.filter_by(
            module=module
        ).order_by(Permission.name).all()
    
    @staticmethod
    def get_permissions_grouped_by_module():
        """
        Obtiene permisos agrupados por módulo
        
        Returns:
            dict: Diccionario {module: [permissions]}
        
        Ejemplo:
            grouped = PermissionService.get_permissions_grouped_by_module()
            for module, perms in grouped.items():
                print(f"{module}: {len(perms)} permisos")
        """
        return Permission.get_all_grouped_by_module()
    
    @staticmethod
    def create_permission(name, display_name, description, module, 
                         category=None, is_dangerous=False):
        """
        Crea un nuevo permiso
        
        Args:
            name (str): Nombre único (ej: 'inventory.create')
            display_name (str): Nombre para mostrar
            description (str): Descripción del permiso
            module (str): Módulo del sistema
            category (str, optional): Categoría (view, manage, export, etc.)
            is_dangerous (bool, optional): Si requiere precaución
        
        Returns:
            Permission: Permiso creado
        
        Raises:
            ValueError: Si el permiso ya existe
        
        Ejemplo:
            perm = PermissionService.create_permission(
                name='inventory.create',
                display_name='Crear Laptop',
                description='Permite crear nuevas laptops en el inventario',
                module='inventory',
                category='manage'
            )
        """
        # Verificar si ya existe
        existing = Permission.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f"Permiso '{name}' ya existe")
        
        # Crear permiso
        permission = Permission(
            name=name,
            display_name=display_name,
            description=description,
            module=module,
            category=category,
            is_dangerous=is_dangerous
        )
        
        db.session.add(permission)
        db.session.commit()
        
        return permission
    
    @staticmethod
    def get_permission_by_name(name):
        """
        Obtiene un permiso por su nombre
        
        Args:
            name (str): Nombre del permiso
        
        Returns:
            Permission: Objeto Permission o None
        
        Ejemplo:
            perm = PermissionService.get_permission_by_name('inventory.create')
        """
        return Permission.get_by_name(name)
    
    @staticmethod
    def get_dangerous_permissions():
        """
        Obtiene permisos marcados como peligrosos
        
        Returns:
            list: Lista de permisos peligrosos
        
        Ejemplo:
            dangerous = PermissionService.get_dangerous_permissions()
            # ['inventory.delete', 'invoices.delete', ...]
        """
        return Permission.query.filter_by(is_dangerous=True).all()
    
    @staticmethod
    def search_permissions(query):
        """
        Busca permisos por nombre o descripción
        
        Args:
            query (str): Texto a buscar
        
        Returns:
            list: Lista de permisos que coinciden
        
        Ejemplo:
            results = PermissionService.search_permissions('delete')
            # Retorna todos los permisos con 'delete' en nombre o descripción
        """
        search = f"%{query}%"
        return Permission.query.filter(
            db.or_(
                Permission.name.ilike(search),
                Permission.display_name.ilike(search),
                Permission.description.ilike(search)
            )
        ).all()
    
    @staticmethod
    def get_user_permissions(user=None):
        """
        Obtiene todos los permisos de un usuario
        
        Args:
            user: Usuario (default: current_user)
        
        Returns:
            list: Lista de objetos Permission
        
        Ejemplo:
            my_perms = PermissionService.get_user_permissions()
            perm_names = [p.name for p in my_perms]
        """
        if user is None:
            if not current_user.is_authenticated:
                return []
            user = current_user
        
        return user.get_all_permissions()
    
    @staticmethod
    def get_user_permission_names(user=None):
        """
        Obtiene nombres de permisos de un usuario
        
        Args:
            user: Usuario (default: current_user)
        
        Returns:
            list: Lista de nombres de permisos
        
        Ejemplo:
            perm_names = PermissionService.get_user_permission_names()
            # ['inventory.create', 'inventory.edit', ...]
        """
        if user is None:
            if not current_user.is_authenticated:
                return []
            user = current_user
        
        return user.get_permission_names()
    
    @staticmethod
    def bulk_create_permissions(permissions_data):
        """
        Crea múltiples permisos en una sola operación
        
        Args:
            permissions_data (list): Lista de diccionarios con datos de permisos
        
        Returns:
            tuple: (created_count, skipped_count)
        
        Ejemplo:
            data = [
                {
                    'name': 'inventory.create',
                    'display_name': 'Crear Laptop',
                    'module': 'inventory',
                    'description': '...'
                },
                # ... más permisos
            ]
            created, skipped = PermissionService.bulk_create_permissions(data)
        """
        created = 0
        skipped = 0
        
        for perm_data in permissions_data:
            # Verificar si ya existe
            existing = Permission.query.filter_by(name=perm_data['name']).first()
            if existing:
                skipped += 1
                continue
            
            # Crear permiso
            permission = Permission(**perm_data)
            db.session.add(permission)
            created += 1
        
        db.session.commit()
        
        return created, skipped
