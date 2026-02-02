# -*- coding: utf-8 -*-
# ============================================
# SERVICIO DE SESIONES
# ============================================
# Lógica de negocio para gestión de sesiones de usuario

from app import db
from app.models.user_session import UserSession
from flask import request
from datetime import datetime, timedelta
import secrets


class SessionService:
    """
    Servicio para gestión de sesiones de usuarios
    
    Proporciona métodos para:
    - Crear y gestionar sesiones
    - Rastrear actividad de usuarios
    - Terminar sesiones remotamente
    - Limpiar sesiones expiradas
    """
    
    @staticmethod
    def create_session(user_id, duration_hours=24):
        """
        Crea una nueva sesión para un usuario
        
        Args:
            user_id (int): ID del usuario
            duration_hours (int): Duración de la sesión en horas (default: 24)
        
        Returns:
            UserSession: Sesión creada
        
        Ejemplo:
            session = SessionService.create_session(user_id=5, duration_hours=48)
        """
        # Generar token único
        session_token = secrets.token_urlsafe(32)
        
        # Obtener información de la request
        ip_address = None
        user_agent = None
        device_info = None
        
        if request:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            
            # Información adicional del dispositivo
            device_info = {
                'platform': request.user_agent.platform,
                'browser': request.user_agent.browser,
                'version': request.user_agent.version,
                'language': request.user_agent.language
            }
        
        # Crear sesión
        session = UserSession.create_session(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            duration_hours=duration_hours
        )
        
        return session
    
    @staticmethod
    def get_active_sessions(user_id):
        """
        Obtiene sesiones activas de un usuario
        
        Args:
            user_id (int): ID del usuario
        
        Returns:
            list: Lista de sesiones activas
        
        Ejemplo:
            sessions = SessionService.get_active_sessions(5)
            print(f"Sesiones activas: {len(sessions)}")
        """
        return UserSession.get_active_sessions(user_id)
    
    @staticmethod
    def get_session_by_token(session_token):
        """
        Obtiene una sesión por su token
        
        Args:
            session_token (str): Token de sesión
        
        Returns:
            UserSession: Sesión o None
        
        Ejemplo:
            session = SessionService.get_session_by_token(token)
        """
        return UserSession.query.filter_by(session_token=session_token).first()
    
    @staticmethod
    def update_session_activity(session_id):
        """
        Actualiza el timestamp de última actividad de una sesión
        
        Args:
            session_id (int): ID de la sesión
        
        Ejemplo:
            SessionService.update_session_activity(session_id=10)
        """
        session = UserSession.query.get(session_id)
        if session:
            session.update_activity()
    
    @staticmethod
    def terminate_session(session_id):
        """
        Termina una sesión específica
        
        Args:
            session_id (int): ID de la sesión
        
        Ejemplo:
            SessionService.terminate_session(10)
        """
        session = UserSession.query.get(session_id)
        if session:
            session.terminate()
    
    @staticmethod
    def terminate_all_user_sessions(user_id, except_session_id=None):
        """
        Termina todas las sesiones de un usuario
        
        Args:
            user_id (int): ID del usuario
            except_session_id (int, optional): ID de sesión a mantener activa
        
        Ejemplo:
            # Cerrar todas las sesiones excepto la actual
            SessionService.terminate_all_user_sessions(
                user_id=5,
                except_session_id=current_session_id
            )
        """
        UserSession.terminate_all_user_sessions(user_id, except_session_id)
    
    @staticmethod
    def cleanup_expired_sessions():
        """
        Limpia sesiones expiradas del sistema
        
        Returns:
            int: Número de sesiones eliminadas
        
        Ejemplo:
            deleted = SessionService.cleanup_expired_sessions()
            print(f"Eliminadas {deleted} sesiones expiradas")
        """
        return UserSession.cleanup_expired_sessions()
    
    @staticmethod
    def get_session_count_by_user(user_id):
        """
        Obtiene el número de sesiones activas de un usuario
        
        Args:
            user_id (int): ID del usuario
        
        Returns:
            int: Número de sesiones activas
        
        Ejemplo:
            count = SessionService.get_session_count_by_user(5)
        """
        return len(UserSession.get_active_sessions(user_id))
    
    @staticmethod
    def get_all_active_sessions():
        """
        Obtiene todas las sesiones activas del sistema
        
        Returns:
            list: Lista de sesiones activas
        
        Ejemplo:
            all_sessions = SessionService.get_all_active_sessions()
            print(f"Total sesiones activas: {len(all_sessions)}")
        """
        return UserSession.query.filter_by(is_active=True).filter(
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.last_activity.desc()).all()
    
    @staticmethod
    def get_sessions_by_ip(ip_address):
        """
        Obtiene sesiones desde una IP específica
        
        Args:
            ip_address (str): Dirección IP
        
        Returns:
            list: Lista de sesiones
        
        Ejemplo:
            sessions = SessionService.get_sessions_by_ip('192.168.1.100')
        """
        return UserSession.query.filter_by(
            ip_address=ip_address,
            is_active=True
        ).all()
    
    @staticmethod
    def detect_suspicious_sessions(user_id):
        """
        Detecta sesiones potencialmente sospechosas
        
        Args:
            user_id (int): ID del usuario
        
        Returns:
            list: Lista de sesiones sospechosas con razones
        
        Ejemplo:
            suspicious = SessionService.detect_suspicious_sessions(5)
            for session_info in suspicious:
                print(f"Sesión sospechosa: {session_info['reason']}")
        """
        sessions = UserSession.get_active_sessions(user_id)
        suspicious = []
        
        # Obtener IPs únicas
        ips = set(s.ip_address for s in sessions if s.ip_address)
        
        # Si hay más de 3 IPs diferentes, puede ser sospechoso
        if len(ips) > 3:
            for session in sessions:
                suspicious.append({
                    'session': session,
                    'reason': 'Múltiples IPs activas simultáneamente',
                    'severity': 'medium'
                })
        
        # Detectar sesiones de ubicaciones muy distantes
        # (esto requeriría integración con servicio de geolocalización)
        
        # Detectar sesiones muy antiguas pero aún activas
        for session in sessions:
            age_hours = (datetime.utcnow() - session.created_at).total_seconds() / 3600
            if age_hours > 72:  # Más de 3 días
                suspicious.append({
                    'session': session,
                    'reason': f'Sesión muy antigua ({int(age_hours)} horas)',
                    'severity': 'low'
                })
        
        return suspicious
    
    @staticmethod
    def get_session_statistics():
        """
        Obtiene estadísticas de sesiones del sistema
        
        Returns:
            dict: Estadísticas de sesiones
        
        Ejemplo:
            stats = SessionService.get_session_statistics()
            print(f"Usuarios activos: {stats['active_users']}")
        """
        all_active = SessionService.get_all_active_sessions()
        
        # Usuarios únicos
        unique_users = set(s.user_id for s in all_active)
        
        # Agrupar por browser
        by_browser = {}
        for session in all_active:
            if session.device_info and 'browser' in session.device_info:
                browser = session.device_info['browser']
                if browser not in by_browser:
                    by_browser[browser] = 0
                by_browser[browser] += 1
        
        # Agrupar por plataforma
        by_platform = {}
        for session in all_active:
            if session.device_info and 'platform' in session.device_info:
                platform = session.device_info['platform']
                if platform not in by_platform:
                    by_platform[platform] = 0
                by_platform[platform] += 1
        
        return {
            'total_active_sessions': len(all_active),
            'active_users': len(unique_users),
            'by_browser': by_browser,
            'by_platform': by_platform,
            'average_sessions_per_user': len(all_active) / len(unique_users) if unique_users else 0
        }
    
    @staticmethod
    def extend_session(session_id, additional_hours=24):
        """
        Extiende la duración de una sesión
        
        Args:
            session_id (int): ID de la sesión
            additional_hours (int): Horas adicionales
        
        Returns:
            UserSession: Sesión actualizada
        
        Ejemplo:
            # Extender sesión por 24 horas más
            session = SessionService.extend_session(session_id=10, additional_hours=24)
        """
        session = UserSession.query.get(session_id)
        if session and session.is_valid():
            session.expires_at = session.expires_at + timedelta(hours=additional_hours)
            db.session.commit()
            return session
        return None
