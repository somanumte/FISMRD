# -*- coding: utf-8 -*-
from app import db
from app.models.mixins import TimestampMixin

class SystemSetting(TimestampMixin, db.Model):
    """
    Configuraciones globales del sistema (credenciales de API, etc.)
    """
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), default='general', index=True)

    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_value(cls, key, value, description=None, category='general'):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description: setting.description = description
            if category: setting.category = category
        else:
            setting = cls(key=key, value=value, description=description, category=category)
            db.session.add(setting)
        db.session.commit()
        return setting

    def __repr__(self):
        return f'<SystemSetting {self.key}>'
