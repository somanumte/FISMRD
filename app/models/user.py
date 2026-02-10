# -*- coding: utf-8 -*-
# ============================================
# MODELO DE USUARIO V3.0
# ============================================
# Cambios V3:
#   - Tabla renombrada: 'user' → 'users' (convención plural + evita palabra reservada PG)
#   - Eliminado campo duplicado: last_password_change (se usa password_changed_at)
#   - has_permission() ahora verifica expires_at e is_active de user_roles
#   - get_all_permissions() ya no tiene 'pass' suelto para admin
#   - increment_failed_login() ya NO hace commit() interno (evita side-effects)

from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt
from sqlalchemy import event


class User(UserMixin, db.Model):
    """
    Modelo de Usuario para el sistema de autenticación.
    RBAC completo con verificación de expiración de roles.
    """
    __tablename__ = 'users'  # V3: Renombrado de 'user' a 'users'

    # ===== COLUMNAS =====
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Seguridad: bloqueo por intentos
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    # ===== CAMPOS RBAC =====
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    # V3: Eliminado 'last_password_change' (duplicado de password_changed_at)
    password_expires_at = db.Column(db.DateTime, nullable=True)

    # 2FA
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    two_factor_secret = db.Column(db.String(255), nullable=True)

    # ===== RELACIONES RBAC =====
    from app.models.rbac_associations import user_roles

    roles = db.relationship(
        'Role',
        secondary=user_roles,
        foreign_keys=[user_roles.c.user_id, user_roles.c.role_id],
        backref=db.backref('users', lazy='dynamic')
    )

    # ===== MÉTODOS DE AUTENTICACIÓN =====

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Encripta y guarda la contraseña. Actualiza password_changed_at."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password):
        """Verifica si una contraseña es correcta"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def increment_failed_login(self):
        """
        Incrementa el contador de intentos fallidos.
        Bloquea la cuenta si supera el máximo.
        """
        self.failed_login_attempts += 1
        from datetime import timedelta
        from config import Config
        max_attempts = Config.MAX_LOGIN_ATTEMPTS
        lockout_time = Config.LOGIN_LOCKOUT_TIME
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_time)
        db.session.commit()

    def reset_failed_login(self):
        """Reinicia el contador de intentos fallidos"""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    def is_locked(self):
        """Verifica si la cuenta está bloqueada"""
        if not self.locked_until:
            return False
        if datetime.utcnow() > self.locked_until:
            self.locked_until = None
            self.failed_login_attempts = 0
            return False
        return True

    def can_login(self):
        """Verifica si el usuario puede hacer login"""
        if not self.is_active:
            return False
        if self.is_locked():
            return False
        return True

    def update_last_login(self):
        """Actualiza la fecha del último login"""
        self.last_login = datetime.utcnow()

    # ===== MÉTODOS RBAC (V3: con verificación de expiración) =====

    def _get_active_roles(self):
        """
        V3: Obtiene solo los roles activos y no expirados del usuario.
        Filtra por is_active y expires_at en la tabla user_roles.
        """
        from app.models.rbac_associations import user_roles
        from app.models.role import Role

        now = datetime.utcnow()
        active_role_ids = db.session.query(user_roles.c.role_id).filter(
            user_roles.c.user_id == self.id,
            user_roles.c.is_active == True,
            db.or_(
                user_roles.c.expires_at.is_(None),
                user_roles.c.expires_at > now
            )
        ).all()

        role_ids = [r[0] for r in active_role_ids]
        if not role_ids:
            return []

        return Role.query.filter(
            Role.id.in_(role_ids),
            Role.is_active == True
        ).all()

    def has_permission(self, permission):
        """
        V3: Verifica permiso considerando expires_at e is_active de user_roles.
        """
        if self.is_admin:
            return True
        for role in self._get_active_roles():
            for perm in role.permissions:
                if perm.name == permission:
                    return True
        return False

    def has_role(self, role_name):
        """V3: Verifica rol considerando expiración"""
        if self.is_admin:
            return True
        return any(role.name == role_name for role in self._get_active_roles())

    def has_any_permission(self, *permission_names):
        """Verifica si tiene AL MENOS UNO de los permisos"""
        if self.is_admin:
            return True
        for role in self._get_active_roles():
            for perm in role.permissions:
                if perm.name in permission_names:
                    return True
        return False

    def has_all_permissions(self, *permission_names):
        """Verifica si tiene TODOS los permisos"""
        if self.is_admin:
            return True
        user_permissions = set()
        for role in self._get_active_roles():
            for perm in role.permissions:
                user_permissions.add(perm.name)
        return all(perm in user_permissions for perm in permission_names)

    def get_all_permissions(self):
        """
        V3: Obtiene todos los permisos del usuario (resuelve el 'pass' de admin).
        """
        if self.is_admin:
            from app.models.permission import Permission
            return Permission.query.filter_by(is_active=True).all()

        perms = set()
        for role in self._get_active_roles():
            for perm in role.permissions:
                perms.add(perm)
        return list(perms)

    def get_permission_names(self):
        """Obtiene lista de nombres de permisos"""
        return [p.name for p in self.get_all_permissions()]

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'roles': [r.name for r in self.roles] if self.roles else []
        }

    @staticmethod
    def create_user(username, email, password, full_name=None, is_admin=False):
        """Crea un usuario completo"""
        if User.query.filter_by(username=username).first():
            raise ValueError(f'El username "{username}" ya está en uso')
        if User.query.filter_by(email=email).first():
            raise ValueError(f'El email "{email}" ya está registrado')

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_admin=is_admin
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        return user


# ============================================
# EVENTOS DE SQLAlchemy
# ============================================

@event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    """Se ejecuta antes de actualizar un usuario"""
    target.updated_at = datetime.utcnow()
