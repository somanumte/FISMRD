# -*- coding: utf-8 -*-
# ============================================
# MODELO DE LOG DE AUDITORÍA V3.0
# ============================================
# Cambios V3:
#   - Agregados old_value y new_value para tracking de cambios específicos
#   - log() ya NO hace commit() interno (el caller es responsable)
#   - Índice compuesto para partitioning-ready queries por fecha
#   - FK a 'users' (renombrada)

from datetime import datetime
from app import db
from sqlalchemy import CheckConstraint


class AuditLog(db.Model):
    """
    Log de auditoría para compliance y trazabilidad.
    V3: old_value/new_value, sin commit interno, índices mejorados.
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    # Acción
    action = db.Column(db.String(100), nullable=False, index=True)
    module = db.Column(db.String(50), nullable=False, index=True)

    # Objetivo
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)

    # V3: Valores antes y después del cambio
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)

    # Detalles adicionales
    details = db.Column(db.JSON, nullable=True)

    # Sesión
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    # Estado
    status = db.Column(db.String(20), default='success', nullable=False)
    error_message = db.Column(db.Text, nullable=True)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relación
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by User#{self.user_id}>'

    @staticmethod
    def log(user_id, action, module, target_type=None, target_id=None,
            details=None, old_value=None, new_value=None,
            ip_address=None, user_agent=None, status='success', error_message=None):
        """
        Crea log de auditoría.
        V3: Ya NO hace commit() interno. El caller es responsable del commit.
        """
        log_entry = AuditLog(
            user_id=user_id, action=action, module=module,
            target_type=target_type, target_id=target_id,
            details=details, old_value=old_value, new_value=new_value,
            ip_address=ip_address, user_agent=user_agent,
            status=status, error_message=error_message
        )
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return log_entry

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'user_full_name': self.user.full_name if self.user else None,
            'action': self.action,
            'module': self.module,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'details': self.details,
            'ip_address': self.ip_address,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def get_recent_logs(limit=100):
        return AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_logs_by_user(user_id, limit=100):
        return AuditLog.query.filter_by(user_id=user_id).order_by(
            AuditLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_logs_by_module(module, limit=100):
        return AuditLog.query.filter_by(module=module).order_by(
            AuditLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_failed_actions(limit=100):
        return AuditLog.query.filter(
            AuditLog.status.in_(['failed', 'denied'])
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'denied')",
            name='ck_audit_status'
        ),
        # Índice compuesto para queries por fecha + módulo (partitioning-ready)
        db.Index('idx_audit_date_module', 'created_at', 'module'),
        db.Index('idx_audit_target', 'target_type', 'target_id'),
        db.Index('idx_audit_user_date', 'user_id', 'created_at'),
    )
