# -*- coding: utf-8 -*-
# ============================================
# SERVICIO DE ROLES
# ============================================
# Lógica de negocio para gestión de roles

from app import db
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from flask_login import current_user


class RoleService:
    """
    Servicio para gestión de roles del sistema RBAC
    
    Proporciona métodos para:
    - Crear y gestionar roles
    - Asignar/remover permisos a roles
    - Asignar/remover roles a usuarios
    """
    
    @staticmethod
    def create_role(name, display_name, description=None, is_system_role=False, created_by_id=None):
        """
        Crea un nuevo rol
        
        Args:
            name (str): Nombre único del rol (ej: 'vendedor')
            display_name (str): Nombre para mostrar
            description (str, optional): Descripción del rol
            is_system_role (bool, optional): Si es rol del sistema (no eliminable)
            created_by_id (int, optional): ID del usuario que crea el rol
        
        Returns:
            Role: Rol creado
        
        Raises:
            ValueError: Si el rol ya existe
        
        Ejemplo:
            role = RoleService.create_role(
                name='vendedor',
                display_name='Vendedor',
                description='Puede crear facturas y gestionar clientes'
            )
        """
        # Verificar si ya existe
        existing = Role.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f"Rol '{name}' ya existe")
        
        # Determinar creador de forma segura para scripts
        final_created_by = created_by_id
        if final_created_by is None:
            try:
                if current_user and current_user.is_authenticated:
                    final_created_by = current_user.id
            except:
                pass

        # Crear rol
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            is_system_role=is_system_role,
            created_by_id=final_created_by
        )
        
        db.session.add(role)
        db.session.commit()
        
        return role
    
    @staticmethod
    def get_all_roles(include_inactive=False):
        """
        Obtiene todos los roles
        
        Args:
            include_inactive (bool): Si incluir roles inactivos
        
        Returns:
            list: Lista de roles
        
        Ejemplo:
            roles = RoleService.get_all_roles()
        """
        query = Role.query
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(Role.display_name).all()
    
    @staticmethod
    def get_role_by_name(name):
        """
        Obtiene un rol por su nombre
        
        Args:
            name (str): Nombre del rol
        
        Returns:
            Role: Objeto Role o None
        
        Ejemplo:
            vendedor = RoleService.get_role_by_name('vendedor')
        """
        return Role.get_by_name(name)
    
    @staticmethod
    def get_role_by_id(role_id):
        """
        Obtiene un rol por su ID
        
        Args:
            role_id (int): ID del rol
        
        Returns:
            Role: Objeto Role o None
        
        Ejemplo:
            role = RoleService.get_role_by_id(1)
        """
        return Role.query.get(role_id)
    
    @staticmethod
    def update_role(role_id, **kwargs):
        """
        Actualiza un rol
        
        Args:
            role_id (int): ID del rol
            **kwargs: Campos a actualizar (display_name, description, is_active)
        
        Returns:
            Role: Rol actualizado
        
        Raises:
            ValueError: Si el rol no existe o es del sistema y se intenta modificar campos protegidos
        
        Ejemplo:
            role = RoleService.update_role(
                role_id=1,
                display_name='Vendedor Senior',
                description='Nueva descripción'
            )
        """
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        # Campos permitidos para actualizar
        allowed_fields = ['display_name', 'description', 'is_active']
        
        # Si es rol del sistema, no permitir cambiar el nombre
        if role.is_system_role and 'name' in kwargs:
            raise ValueError("No se puede cambiar el nombre de un rol del sistema")
        
        # Actualizar campos
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(role, field, value)
        
        db.session.commit()
        
        return role
    
    @staticmethod
    def delete_role(role_id):
        """
        Elimina un rol
        
        Args:
            role_id (int): ID del rol
        
        Raises:
            ValueError: Si el rol no existe o es del sistema
        
        Ejemplo:
            RoleService.delete_role(5)
        """
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        if role.is_system_role:
            raise ValueError("No se puede eliminar un rol del sistema")
        
        db.session.delete(role)
        db.session.commit()
    
    @staticmethod
    def assign_permission_to_role(role_id, permission_id, granted_by_id=None):
        """
        Asigna un permiso a un rol
        
        Args:
            role_id (int): ID del rol
            permission_id (int): ID del permiso
            granted_by_id (int, optional): ID del usuario que otorga el permiso
        
        Returns:
            Role: Rol actualizado
        
        Raises:
            ValueError: Si el rol o permiso no existen
        
        Ejemplo:
            role = RoleService.assign_permission_to_role(
                role_id=1,
                permission_id=10
            )
        """
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        permission = Permission.query.get(permission_id)
        if not permission:
            raise ValueError(f"Permiso con ID {permission_id} no existe")
        
        # Agregar permiso si no lo tiene
        if permission not in role.permissions:
            role.permissions.append(permission)
            db.session.commit()
        
        return role
    
    @staticmethod
    def remove_permission_from_role(role_id, permission_id):
        """
        Remueve un permiso de un rol
        
        Args:
            role_id (int): ID del rol
            permission_id (int): ID del permiso
        
        Returns:
            Role: Rol actualizado
        
        Raises:
            ValueError: Si el rol o permiso no existen
        
        Ejemplo:
            role = RoleService.remove_permission_from_role(
                role_id=1,
                permission_id=10
            )
        """
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        permission = Permission.query.get(permission_id)
        if not permission:
            raise ValueError(f"Permiso con ID {permission_id} no existe")
        
        # Remover permiso si lo tiene
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.session.commit()
        
        return role
    
    @staticmethod
    def assign_permissions_bulk(role_id, permission_ids):
        """
        Asigna múltiples permisos a un rol
        
        Args:
            role_id (int): ID del rol
            permission_ids (list): Lista de IDs de permisos
        
        Returns:
            Role: Rol actualizado
        
        Ejemplo:
            role = RoleService.assign_permissions_bulk(
                role_id=1,
                permission_ids=[1, 2, 3, 4, 5]
            )
        """
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        # Convertir a enteros para evitar errores de tipo en DB
        ids = [int(pid) for pid in permission_ids if str(pid).isdigit()]
        
        # Obtener permisos
        permissions = Permission.query.filter(Permission.id.in_(ids)).all()
        
        # Agregar permisos que no tenga
        for permission in permissions:
            if permission not in role.permissions:
                role.permissions.append(permission)
        
        db.session.commit()
        
        return role
    
    @staticmethod
    def sync_permissions(role_id, permission_ids):
        """
        Sincroniza permisos de un rol (reemplaza todos los permisos)
        
        Args:
            role_id (int): ID del rol
            permission_ids (list): Lista de IDs de permisos
        
        Returns:
            Role: Rol actualizado
        
        Ejemplo:
            # El rol tendrá SOLO estos permisos
            role = RoleService.sync_permissions(
                role_id=1,
                permission_ids=[1, 2, 3]
            )
        """
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        # Convertir a enteros para evitar errores de tipo en DB
        ids = [int(pid) for pid in permission_ids if str(pid).isdigit()]
        
        # Obtener permisos
        permissions = Permission.query.filter(Permission.id.in_(ids)).all()
        
        # Reemplazar todos los permisos
        role.permissions = permissions
        
        db.session.commit()
        
        return role
    
    @staticmethod
    def assign_role_to_user(user_id, role_id, assigned_by_id=None):
        """
        Asigna un rol a un usuario
        
        Args:
            user_id (int): ID del usuario
            role_id (int): ID del rol
            assigned_by_id (int, optional): ID del usuario que asigna el rol
        
        Returns:
            User: Usuario actualizado
        
        Raises:
            ValueError: Si el usuario o rol no existen
        
        Ejemplo:
            user = RoleService.assign_role_to_user(
                user_id=5,
                role_id=1
            )
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no existe")
        
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        # Asignar rol si no lo tiene
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
        
        return user
    
    @staticmethod
    def remove_role_from_user(user_id, role_id):
        """
        Remueve un rol de un usuario
        
        Args:
            user_id (int): ID del usuario
            role_id (int): ID del rol
        
        Returns:
            User: Usuario actualizado
        
        Raises:
            ValueError: Si el usuario o rol no existen
        
        Ejemplo:
            user = RoleService.remove_role_from_user(
                user_id=5,
                role_id=1
            )
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no existe")
        
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Rol con ID {role_id} no existe")
        
        # Remover rol si lo tiene
        if role in user.roles:
            user.roles.remove(role)
            db.session.commit()
        
        return user
    
    @staticmethod
    def sync_roles_to_user(user_id, role_names):
        """
        Sincroniza los roles de un usuario (reemplaza todos los roles actuales)
        
        Args:
            user_id (int): ID del usuario
            role_names (list): Lista de nombres de roles a asignar
            
        Returns:
            User: Usuario actualizado
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Usuario con ID {user_id} no existe")
            
        # Obtener objetos Role por sus nombres
        roles = Role.query.filter(Role.name.in_(role_names)).all()
        
        # Reemplazar roles
        user.roles = roles
        db.session.commit()
        
        return user
    
    @staticmethod
    def get_users_with_role(role_id):
        """
        Obtiene usuarios que tienen un rol específico
        
        Args:
            role_id (int): ID del rol
        
        Returns:
            list: Lista de usuarios
        
        Ejemplo:
            vendedores = RoleService.get_users_with_role(1)
        """
        role = Role.query.get(role_id)
        if not role:
            return []
        
        return role.users
    
    @staticmethod
    def get_role_permissions(role_id):
        """
        Obtiene permisos de un rol
        
        Args:
            role_id (int): ID del rol
        
        Returns:
            list: Lista de permisos
        
        Ejemplo:
            perms = RoleService.get_role_permissions(1)
        """
        role = Role.query.get(role_id)
        if not role:
            return []
        
        return role.permissions
    
    @staticmethod
    def clone_role(source_role_id, new_name, new_display_name, description=None):
        """
        Clona un rol existente con sus permisos
        
        Args:
            source_role_id (int): ID del rol a clonar
            new_name (str): Nombre del nuevo rol
            new_display_name (str): Nombre para mostrar
            description (str, optional): Descripción
        
        Returns:
            Role: Nuevo rol creado
        
        Ejemplo:
            # Crear "Vendedor Senior" basado en "Vendedor"
            new_role = RoleService.clone_role(
                source_role_id=1,
                new_name='vendedor_senior',
                new_display_name='Vendedor Senior'
            )
        """
        source_role = Role.query.get(source_role_id)
        if not source_role:
            raise ValueError(f"Rol con ID {source_role_id} no existe")
        
        # Crear nuevo rol
        new_role = RoleService.create_role(
            name=new_name,
            display_name=new_display_name,
            description=description or source_role.description
        )
        
        # Copiar permisos
        new_role.permissions = list(source_role.permissions)
        db.session.commit()
        
        return new_role
