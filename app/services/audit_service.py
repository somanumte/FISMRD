# -*- coding: utf-8 -*-
# ============================================
# SERVICIO DE AUDITORÍA
# ============================================
# Lógica de negocio para sistema de auditoría

from app import db
from app.models.audit_log import AuditLog
from flask import request
from flask_login import current_user
from datetime import datetime, timedelta


class AuditService:
    """
    Servicio para gestión de auditoría del sistema
    
    Proporciona métodos para:
    - Registrar acciones de usuarios
    - Consultar logs de auditoría
    - Generar reportes de auditoría
    """
    
    @staticmethod
    def log_action(action, module, target_type=None, target_id=None, 
                   details=None, status='success', error_message=None, user_id=None):
        """
        Registra una acción en el sistema de auditoría
        
        Args:
            action (str): Nombre de la acción (ej: 'create_laptop', 'delete_invoice')
            module (str): Módulo del sistema (ej: 'inventory', 'invoices')
            target_type (str, optional): Tipo de objeto afectado (ej: 'Laptop', 'Invoice')
            target_id (int, optional): ID del objeto afectado
            details (dict, optional): Detalles adicionales (se guarda como JSON)
            status (str, optional): Estado de la acción ('success', 'failed', 'denied')
            error_message (str, optional): Mensaje de error si aplica
            user_id (int, optional): ID del usuario (default: current_user)
        
        Returns:
            AuditLog: Log creado
        
        Ejemplo:
            AuditService.log_action(
                action='create_laptop',
                module='inventory',
                target_type='Laptop',
                target_id=123,
                details={'brand': 'Dell', 'model': 'Latitude 5420'}
            )
        """
        # Obtener información del usuario
        if user_id is None:
            user_id = current_user.id if current_user.is_authenticated else None
        
        # Obtener información de la request
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
        
        # Crear log
        return AuditLog.log(
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
    
    @staticmethod
    def log_login(user_id, success=True, error_message=None):
        """
        Registra un intento de login
        
        Args:
            user_id (int): ID del usuario
            success (bool): Si el login fue exitoso
            error_message (str, optional): Mensaje de error si falló
        
        Ejemplo:
            AuditService.log_login(user_id=5, success=True)
        """
        status = 'success' if success else 'failed'
        AuditService.log_action(
            action='user_login',
            module='auth',
            target_type='User',
            target_id=user_id,
            status=status,
            error_message=error_message,
            user_id=user_id
        )
    
    @staticmethod
    def log_logout(user_id):
        """
        Registra un logout
        
        Args:
            user_id (int): ID del usuario
        
        Ejemplo:
            AuditService.log_logout(user_id=5)
        """
        AuditService.log_action(
            action='user_logout',
            module='auth',
            target_type='User',
            target_id=user_id,
            user_id=user_id
        )
    
    @staticmethod
    def log_permission_denied(permission_name, module, user_id=None):
        """
        Registra un intento de acceso denegado
        
        Args:
            permission_name (str): Nombre del permiso requerido
            module (str): Módulo del sistema
            user_id (int, optional): ID del usuario (default: current_user)
        
        Ejemplo:
            AuditService.log_permission_denied(
                permission_name='inventory.delete',
                module='inventory'
            )
        """
        if user_id is None:
            user_id = current_user.id if current_user.is_authenticated else None
        
        AuditService.log_action(
            action='permission_denied',
            module=module,
            details={'permission': permission_name},
            status='denied',
            user_id=user_id
        )
    
    @staticmethod
    def log_role_change(user_id, action, role_name, changed_by_id=None):
        """
        Registra cambios en roles de usuarios
        
        Args:
            user_id (int): ID del usuario afectado
            action (str): 'assign_role' o 'remove_role'
            role_name (str): Nombre del rol
            changed_by_id (int, optional): ID del usuario que hizo el cambio
        
        Ejemplo:
            AuditService.log_role_change(
                user_id=5,
                action='assign_role',
                role_name='vendedor',
                changed_by_id=1
            )
        """
        AuditService.log_action(
            action=action,
            module='admin',
            target_type='User',
            target_id=user_id,
            details={'role': role_name},
            user_id=changed_by_id or (current_user.id if current_user.is_authenticated else None)
        )
    
    @staticmethod
    def get_recent_logs(limit=100):
        """
        Obtiene los logs más recientes
        
        Args:
            limit (int): Número máximo de logs
        
        Returns:
            list: Lista de logs
        
        Ejemplo:
            recent = AuditService.get_recent_logs(50)
        """
        return AuditLog.get_recent_logs(limit)
    
    @staticmethod
    def get_logs_by_user(user_id, limit=100):
        """
        Obtiene logs de un usuario específico
        
        Args:
            user_id (int): ID del usuario
            limit (int): Número máximo de logs
        
        Returns:
            list: Lista de logs
        
        Ejemplo:
            user_logs = AuditService.get_logs_by_user(5, limit=50)
        """
        return AuditLog.get_logs_by_user(user_id, limit)
    
    @staticmethod
    def get_logs_by_module(module, limit=100):
        """
        Obtiene logs de un módulo específico
        
        Args:
            module (str): Nombre del módulo
            limit (int): Número máximo de logs
        
        Returns:
            list: Lista de logs
        
        Ejemplo:
            inv_logs = AuditService.get_logs_by_module('inventory', limit=100)
        """
        return AuditLog.get_logs_by_module(module, limit)
    
    @staticmethod
    def get_failed_actions(limit=100):
        """
        Obtiene acciones fallidas o denegadas
        
        Args:
            limit (int): Número máximo de logs
        
        Returns:
            list: Lista de logs
        
        Ejemplo:
            failed = AuditService.get_failed_actions(50)
        """
        return AuditLog.get_failed_actions(limit)
    
    @staticmethod
    def get_logs_by_date_range(start_date, end_date, module=None, user_id=None):
        """
        Obtiene logs en un rango de fechas
        
        Args:
            start_date (datetime): Fecha inicial
            end_date (datetime): Fecha final
            module (str, optional): Filtrar por módulo
            user_id (int, optional): Filtrar por usuario
        
        Returns:
            list: Lista de logs
        
        Ejemplo:
            from datetime import datetime, timedelta
            start = datetime.now() - timedelta(days=7)
            end = datetime.now()
            logs = AuditService.get_logs_by_date_range(start, end, module='inventory')
        """
        query = AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        )
        
        if module:
            query = query.filter_by(module=module)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def get_activity_summary(days=7):
        """
        Obtiene resumen de actividad de los últimos N días
        
        Args:
            days (int): Número de días a analizar
        
        Returns:
            dict: Resumen con estadísticas
        
        Ejemplo:
            summary = AuditService.get_activity_summary(7)
            # {
            #     'total_actions': 1234,
            #     'successful': 1200,
            #     'failed': 20,
            #     'denied': 14,
            #     'by_module': {...},
            #     'by_user': {...}
            # }
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = AuditLog.query.filter(
            AuditLog.created_at >= start_date
        ).all()
        
        # Calcular estadísticas
        total = len(logs)
        successful = sum(1 for log in logs if log.status == 'success')
        failed = sum(1 for log in logs if log.status == 'failed')
        denied = sum(1 for log in logs if log.status == 'denied')
        
        # Agrupar por módulo
        by_module = {}
        for log in logs:
            if log.module not in by_module:
                by_module[log.module] = 0
            by_module[log.module] += 1
        
        # Agrupar por usuario
        by_user = {}
        for log in logs:
            if log.user_id:
                if log.user_id not in by_user:
                    by_user[log.user_id] = {
                        'username': log.user.username if log.user else 'Unknown',
                        'count': 0
                    }
                by_user[log.user_id]['count'] += 1
        
        return {
            'total_actions': total,
            'successful': successful,
            'failed': failed,
            'denied': denied,
            'by_module': by_module,
            'by_user': by_user,
            'period_days': days
        }
    
    @staticmethod
    def search_logs(query=None, user_id=None, module=None, action=None, limit=100):
        """
        Busca en los logs con filtros avanzados
        
        Args:
            query (str, optional): Texto a buscar en acción, módulo o tipo
            user_id (int, optional): Filtrar por usuario
            module (str, optional): Filtrar por módulo
            action (str, optional): Filtrar por acción específica
            limit (int): Límite de resultados
            
        Returns:
            list: Lista de logs
        """
        q = AuditLog.query
        
        if user_id:
            q = q.filter_by(user_id=user_id)
        if module:
            q = q.filter_by(module=module)
        if action:
            q = q.filter_by(action=action)
            
        if query:
            search = f"%{query}%"
            q = q.filter(
                db.or_(
                    AuditLog.action.ilike(search),
                    AuditLog.module.ilike(search),
                    AuditLog.target_type.ilike(search)
                )
            )
            
        return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def export_logs_to_dict(logs):
        """
        Exporta logs a formato diccionario (para JSON/CSV)
        
        Args:
            logs (list): Lista de objetos AuditLog
        
        Returns:
            list: Lista de diccionarios
        
        Ejemplo:
            logs = AuditService.get_recent_logs(100)
            data = AuditService.export_logs_to_dict(logs)
            return jsonify(data)
        """
        return [log.to_dict() for log in logs]
