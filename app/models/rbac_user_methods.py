# -*- coding: utf-8 -*-
# ============================================
# EXTENSIONES RBAC PARA MODELO USER
# ============================================
# Métodos adicionales para agregar al modelo User
# INSTRUCCIONES: Copiar estos métodos dentro de la clase User en user.py

"""
MÉTODOS RBAC PARA AGREGAR A LA CLASE USER:

Agregar estos métodos después del método to_dict() y antes de create_user()
"""

def has_permission(self, permission_name):
    """
    Verifica si el usuario tiene un permiso específico
    
    Args:
        permission_name (str): Nombre del permiso (ej: 'inventory.create')
    
    Returns:
        bool: True si el usuario tiene el permiso
    
    Ejemplo:
        if current_user.has_permission('inventory.delete'):
            # Permitir eliminar laptop
        else:
            abort(403)
    """
    # Super admin tiene todos los permisos
    if self.is_admin:
        return True
    
    # Verificar en todos los roles asignados
    for role in self.roles:
        if role.is_active and role.has_permission(permission_name):
            return True
    
    return False

def has_any_permission(self, *permission_names):
    """
    Verifica si el usuario tiene AL MENOS UNO de los permisos
    
    Args:
        *permission_names: Lista de nombres de permisos
    
    Returns:
        bool: True si tiene al menos uno
    
    Ejemplo:
        if current_user.has_any_permission('inventory.view_list', 'inventory.view_detail'):
            # Mostrar inventario
    """
    return any(self.has_permission(p) for p in permission_names)

def has_all_permissions(self, *permission_names):
    """
    Verifica si el usuario tiene TODOS los permisos
    
    Args:
        *permission_names: Lista de nombres de permisos
    
    Returns:
        bool: True si tiene todos
    
    Ejemplo:
        if current_user.has_all_permissions('invoices.create', 'invoices.assign_ncf'):
            # Permitir crear factura con NCF
    """
    return all(self.has_permission(p) for p in permission_names)

def get_all_permissions(self):
    """
    Obtiene lista de todos los permisos del usuario
    
    Returns:
        list: Lista de objetos Permission
    
    Ejemplo:
        permissions = current_user.get_all_permissions()
        for perm in permissions:
            print(perm.name)
    """
    # Importar aquí para evitar circular import
    from app.models.permission import Permission
    
    # Super admin tiene todos los permisos
    if self.is_admin:
        return Permission.query.all()
    
    # Recolectar permisos de todos los roles
    permissions = set()
    for role in self.roles:
        if role.is_active:
            permissions.update(role.permissions)
    
    return list(permissions)

def get_permission_names(self):
    """
    Obtiene lista de nombres de permisos del usuario
    
    Returns:
        list: Lista de nombres de permisos (strings)
    
    Ejemplo:
        perm_names = current_user.get_permission_names()
        # ['inventory.create', 'inventory.edit', ...]
    """
    return [p.name for p in self.get_all_permissions()]

def assign_role(self, role):
    """
    Asigna un rol al usuario
    
    Args:
        role: Objeto Role
    
    Ejemplo:
        vendedor_role = Role.get_by_name('vendedor')
        user.assign_role(vendedor_role)
        db.session.commit()
    """
    if role not in self.roles:
        self.roles.append(role)

def remove_role(self, role):
    """
    Remueve un rol del usuario
    
    Args:
        role: Objeto Role
    
    Ejemplo:
        vendedor_role = Role.get_by_name('vendedor')
        user.remove_role(vendedor_role)
        db.session.commit()
    """
    if role in self.roles:
        self.roles.remove(role)

def has_role(self, role_name):
    """
    Verifica si el usuario tiene un rol específico
    
    Args:
        role_name (str): Nombre del rol
    
    Returns:
        bool: True si tiene el rol
    
    Ejemplo:
        if current_user.has_role('vendedor'):
            # Es vendedor
    """
    return any(role.name == role_name and role.is_active for role in self.roles)

def get_role_names(self):
    """
    Obtiene lista de nombres de roles del usuario
    
    Returns:
        list: Lista de nombres de roles
    
    Ejemplo:
        role_names = current_user.get_role_names()
        # ['vendedor', 'almacenista']
    """
    return [role.name for role in self.roles if role.is_active]
