# -*- coding: utf-8 -*-
# ============================================
# MODELO DE SESIÓN DE USUARIO
# ============================================
# Gestión de sesiones activas para seguridad

from datetime import datetime, timedelta
from app import db


class UserSession(db.Model):
    """
    Modelo de Sesión de Usuario
    
    Rastrea sesiones activas para:
    - Seguridad (detectar sesiones sospechosas)
    - Control de acceso concurrente
    - Auditoría de accesos
    - Gestión de sesiones (cerrar sesiones remotas)
    """
    __tablename__ = 'user_sessions'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Token de sesión
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Información del cliente
    ip_address = db.Column(db.String(45))  # IPv4 o IPv6
    user_agent = db.Column(db.Text)  # Browser/client info
    device_info = db.Column(db.JSON)  # Información adicional del dispositivo
    location = db.Column(db.String(100))  # Ubicación geográfica (opcional)
    
    # Estado
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Relación
    user = db.relationship('User', backref='sessions')
    
    def __repr__(self):
        return f'<UserSession User#{self.user_id} {self.session_token[:10]}...>'
    
    def is_expired(self):
        """
        Verifica si la sesión ha expirado
        
        Returns:
            bool: True si la sesión expiró
        """
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """
        Verifica si la sesión es válida (activa y no expirada)
        
        Returns:
            bool: True si la sesión es válida
        """
        return self.is_active and not self.is_expired()
    
    def update_activity(self):
        """
        Actualiza el timestamp de última actividad
        """
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def terminate(self):
        """
        Termina la sesión
        """
        self.is_active = False
        db.session.commit()
    
    def to_dict(self):
        """
        Serializa la sesión a diccionario
        
        Returns:
            dict: Representación de la sesión
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_info': self.device_info,
            'location': self.location,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @staticmethod
    def create_session(user_id, session_token, ip_address=None, user_agent=None, 
                      device_info=None, location=None, duration_hours=24):
        """
        Crea una nueva sesión
        
        Args:
            user_id: ID del usuario
            session_token: Token único de sesión
            ip_address: IP del cliente
            user_agent: User agent del cliente
            device_info: Información del dispositivo (JSON)
            location: Ubicación geográfica
            duration_hours: Duración de la sesión en horas (default: 24)
        
        Returns:
            UserSession: Sesión creada
        """
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            location=location,
            expires_at=expires_at
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    @staticmethod
    def get_active_sessions(user_id):
        """
        Obtiene sesiones activas de un usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            list: Lista de sesiones activas
        """
        return UserSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).filter(
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.last_activity.desc()).all()
    
    @staticmethod
    def terminate_all_user_sessions(user_id, except_session_id=None):
        """
        Termina todas las sesiones de un usuario
        
        Args:
            user_id: ID del usuario
            except_session_id: ID de sesión a mantener activa (opcional)
        """
        query = UserSession.query.filter_by(user_id=user_id, is_active=True)
        
        if except_session_id:
            query = query.filter(UserSession.id != except_session_id)
        
        sessions = query.all()
        
        for session in sessions:
            session.is_active = False
        
        db.session.commit()
    
    @staticmethod
    def cleanup_expired_sessions():
        """
        Limpia sesiones expiradas (para ejecutar periódicamente)
        
        Returns:
            int: Número de sesiones eliminadas
        """
        expired = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired)
        
        for session in expired:
            db.session.delete(session)
        
        db.session.commit()
        
        return count
