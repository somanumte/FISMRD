# -*- coding: utf-8 -*-
# ============================================
# MODELO DE LOG DE AUDITORÍA
# ============================================
# Registra todas las acciones del sistema para compliance

from datetime import datetime
from app import db


class AuditLog(db.Model):
    """
    Modelo de Log de Auditoría
    
    Registra todas las acciones realizadas en el sistema para:
    - Compliance (SOC 2, ISO 27001)
    - Seguridad
    - Trazabilidad
    - Investigación de incidentes
    """
    __tablename__ = 'audit_logs'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    
    # Usuario que realizó la acción
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    
    # Acción realizada
    action = db.Column(db.String(100), nullable=False, index=True)  # 'create_laptop', 'delete_invoice', etc.
    module = db.Column(db.String(50), nullable=False, index=True)  # 'inventory', 'invoices', etc.
    
    # Objetivo de la acción
    target_type = db.Column(db.String(50))  # 'Laptop', 'Invoice', 'User', etc.
    target_id = db.Column(db.Integer)  # ID del objeto afectado
    
    # Detalles adicionales (JSON)
    details = db.Column(db.JSON)  # Información adicional sobre la acción
    
    # Información de la sesión
    ip_address = db.Column(db.String(45))  # IPv4 o IPv6
    user_agent = db.Column(db.Text)  # Browser/client info
    
    # Estado de la acción
    status = db.Column(db.String(20), default='success')  # 'success', 'failed', 'denied'
    error_message = db.Column(db.Text)  # Si hubo error
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relación
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User#{self.user_id}>'
    
    @staticmethod
    def log(user_id, action, module, target_type=None, target_id=None, 
            details=None, ip_address=None, user_agent=None, status='success', error_message=None):
        """
        Método estático para crear log de auditoría
        
        Args:
            user_id: ID del usuario que realiza la acción
            action: Nombre de la acción
            module: Módulo del sistema
            target_type: Tipo de objeto afectado (opcional)
            target_id: ID del objeto afectado (opcional)
            details: Detalles adicionales en JSON (opcional)
            ip_address: IP del cliente (opcional)
            user_agent: User agent del cliente (opcional)
            status: Estado de la acción (default: 'success')
            error_message: Mensaje de error si aplica (opcional)
        
        Returns:
            AuditLog: Objeto creado
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            module=module,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
    
    def to_dict(self):
        """
        Serializa el log a diccionario
        
        Returns:
            dict: Representación del log
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'user_full_name': self.user.full_name if self.user else None,
            'action': self.action,
            'module': self.module,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_recent_logs(limit=100):
        """
        Obtiene los logs más recientes
        
        Args:
            limit: Número máximo de logs a retornar
        
        Returns:
            list: Lista de logs
        """
        return AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_logs_by_user(user_id, limit=100):
        """
        Obtiene logs de un usuario específico
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de logs
        
        Returns:
            list: Lista de logs
        """
        return AuditLog.query.filter_by(user_id=user_id).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_logs_by_module(module, limit=100):
        """
        Obtiene logs de un módulo específico
        
        Args:
            module: Nombre del módulo
            limit: Número máximo de logs
        
        Returns:
            list: Lista de logs
        """
        return AuditLog.query.filter_by(module=module).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_failed_actions(limit=100):
        """
        Obtiene acciones fallidas o denegadas
        
        Args:
            limit: Número máximo de logs
        
        Returns:
            list: Lista de logs
        """
        return AuditLog.query.filter(
            AuditLog.status.in_(['failed', 'denied'])
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
