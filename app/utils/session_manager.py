# -*- coding: utf-8 -*-
from flask import session, request, current_app
from app.models.user_session import UserSession
from app.models.user import User
import secrets

def create_session(user):
    """
    Crea una nueva sesión para el usuario y la guarda en la base de datos.
    Generate a secure random token.
    """
    # Generar token seguro
    token = secrets.token_urlsafe(64)
    
    # Obtener información del cliente
    ip_address = request.remote_addr
    ua_string = str(request.user_agent)
    
    # Información del User Agent
    user_agent_info = ua_string[:255] # Truncar si es muy largo

    # Crear sesión en DB
    user_session = UserSession.create_session(
        user_id=user.id,
        session_token=token,
        ip_address=ip_address,
        user_agent=user_agent_info,
        duration_hours=12 # 12 horas por defecto
    )
    
    # Guardar token en la sesión de Flask (cookie firmada)
    session['session_token'] = token
    
    return user_session

def validate_session():
    """
    Valida si la sesión actual es válida.
    Retorna True si es válida, False si no.
    """
    token = session.get('session_token')
    
    if not token:
        return False
        
    # Buscar sesión en DB
    user_session = UserSession.query.filter_by(session_token=token).first()
    
    if user_session and user_session.is_valid():
        # Actualizar última actividad
        user_session.update_activity()
        return True
        
    return False

def terminate_current_session():
    """
    Termina la sesión actual (Logout).
    """
    token = session.get('session_token')
    
    if token:
        user_session = UserSession.query.filter_by(session_token=token).first()
        if user_session:
            user_session.terminate()
            
    session.pop('session_token', None)
