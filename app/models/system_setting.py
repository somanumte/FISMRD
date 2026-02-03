# -*- coding: utf-8 -*-
# ============================================
# MODELO DE CONFIGURACIÓN DEL SISTEMA
# ============================================
# Almacena configuraciones key-value para el sistema
# Ubicación: app/models/system_setting.py

from app import db
from app.models.mixins import TimestampMixin
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64
import hashlib


class SystemSetting(TimestampMixin, db.Model):
    """
    Modelo para almacenar configuraciones del sistema en formato key-value.
    Soporta valores encriptados para datos sensibles como tokens y contraseñas.
    """
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    is_encrypted = db.Column(db.Boolean, default=False, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='general', index=True)
    description = db.Column(db.String(255), nullable=True)
    
    # Clave de encriptación derivada de SECRET_KEY
    _cipher = None
    
    @classmethod
    def _get_cipher(cls):
        """Obtiene el cipher para encriptar/desencriptar valores sensibles"""
        if cls._cipher is None:
            from flask import current_app
            # Derivar una clave de 32 bytes desde SECRET_KEY
            secret = current_app.config.get('SECRET_KEY', 'default-secret-key-change-me')
            key = hashlib.sha256(secret.encode()).digest()
            key_b64 = base64.urlsafe_b64encode(key)
            cls._cipher = Fernet(key_b64)
        return cls._cipher
    
    @classmethod
    def get(cls, key: str, default=None):
        """
        Obtiene un valor de configuración por su clave.
        Si está encriptado, lo desencripta automáticamente.
        """
        setting = cls.query.filter_by(key=key).first()
        if setting is None:
            return default
        
        if setting.is_encrypted and setting.value:
            try:
                cipher = cls._get_cipher()
                decrypted = cipher.decrypt(setting.value.encode())
                return decrypted.decode()
            except Exception:
                return default
        
        return setting.value if setting.value else default
    
    @classmethod
    def set(cls, key: str, value: str, category: str = 'general', 
            description: str = None, encrypted: bool = False):
        """
        Establece un valor de configuración.
        Si encrypted=True, encripta el valor antes de guardarlo.
        """
        setting = cls.query.filter_by(key=key).first()
        
        # Encriptar si es necesario
        final_value = value
        if encrypted and value:
            cipher = cls._get_cipher()
            final_value = cipher.encrypt(value.encode()).decode()
        
        if setting is None:
            setting = cls(
                key=key,
                value=final_value,
                is_encrypted=encrypted,
                category=category,
                description=description
            )
            db.session.add(setting)
        else:
            setting.value = final_value
            setting.is_encrypted = encrypted
            if category:
                setting.category = category
            if description:
                setting.description = description
        
        db.session.commit()
        return setting
    
    @classmethod
    def delete(cls, key: str):
        """Elimina una configuración"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            db.session.delete(setting)
            db.session.commit()
            return True
        return False
    
    @classmethod
    def get_by_category(cls, category: str) -> dict:
        """Obtiene todas las configuraciones de una categoría"""
        settings = cls.query.filter_by(category=category).all()
        result = {}
        for setting in settings:
            result[setting.key] = cls.get(setting.key)
        return result
    
    @classmethod
    def get_all_categories(cls) -> list:
        """Obtiene lista de categorías únicas"""
        categories = db.session.query(cls.category).distinct().all()
        return [c[0] for c in categories]
    
    def to_dict(self, include_value: bool = False):
        """Serializa la configuración a diccionario"""
        data = {
            'id': self.id,
            'key': self.key,
            'category': self.category,
            'description': self.description,
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_value:
            if self.is_encrypted:
                data['value'] = '••••••••' if self.value else None
                data['has_value'] = bool(self.value)
            else:
                data['value'] = self.value
        
        return data
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>'


# ============================================
# CONSTANTES DE CONFIGURACIÓN DE ICECAT
# ============================================

ICECAT_SETTINGS = {
    'icecat_username': {
        'description': 'Usuario de Icecat (para Open Icecat usar: openIcecat-live)',
        'encrypted': False,
        'default': 'openIcecat-live'
    },
    'icecat_api_token': {
        'description': 'Token de API de Icecat (opcional para Open Icecat)',
        'encrypted': True,
        'default': ''
    },
    'icecat_content_token': {
        'description': 'Token de contenido de Icecat para acceder a imágenes (opcional)',
        'encrypted': True,
        'default': ''
    },
    'icecat_language': {
        'description': 'Idioma por defecto para las consultas (ES, EN, PT, etc.)',
        'encrypted': False,
        'default': 'ES'
    },
    'icecat_enabled': {
        'description': 'Habilitar integración con Icecat',
        'encrypted': False,
        'default': 'true'
    }
}


def init_icecat_settings():
    """
    Inicializa las configuraciones de Icecat con valores por defecto
    si no existen en la base de datos.
    """
    for key, config in ICECAT_SETTINGS.items():
        existing = SystemSetting.query.filter_by(key=key).first()
        if existing is None:
            SystemSetting.set(
                key=key,
                value=config['default'],
                category='icecat',
                description=config['description'],
                encrypted=config['encrypted']
            )
