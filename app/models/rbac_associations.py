# -*- coding: utf-8 -*-
# ============================================
# TABLAS DE ASOCIACIÓN RBAC
# ============================================
# Tablas many-to-many para roles y permisos

from app import db
from datetime import datetime


# ============================================
# TABLA: role_permissions
# ============================================
# Relación many-to-many entre Role y Permission
# Un rol puede tener múltiples permisos
# Un permiso puede pertenecer a múltiples roles

role_permissions = db.Table('role_permissions',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
    db.Column('granted_at', db.DateTime, default=datetime.utcnow),
    db.Column('granted_by_id', db.Integer, db.ForeignKey('user.id')),
    db.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
)


# ============================================
# TABLA: user_roles
# ============================================
# Relación many-to-many entre User y Role
# Un usuario puede tener múltiples roles
# Un rol puede ser asignado a múltiples usuarios

user_roles = db.Table('user_roles',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow),
    db.Column('assigned_by_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('expires_at', db.DateTime, nullable=True),  # Opcional: roles temporales
    db.Column('is_active', db.Boolean, default=True),
    db.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
)
