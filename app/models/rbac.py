# -*- coding: utf-8 -*-
# ============================================
# IMPORTACIONES DE MODELOS RBAC V3.0
# ============================================

from app import db
from app.models.role import Role
from app.models.permission import Permission
from app.models.audit_log import AuditLog
from app.models.user_session import UserSession
from app.models.rbac_associations import role_permissions, user_roles

# Actualizar relaciones en Role
Role.permissions = db.relationship(
    'Permission',
    secondary=role_permissions,
    backref=db.backref('roles', lazy='dynamic')
)

__all__ = [
    'Role',
    'Permission',
    'AuditLog',
    'UserSession',
    'role_permissions',
    'user_roles'
]
