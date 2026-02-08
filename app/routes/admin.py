# -*- coding: utf-8 -*-
# ============================================
# RUTAS DE ADMINISTRACIÓN
# ============================================
# Gestión de usuarios, roles y configuración

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.role import Role
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.services.audit_service import AuditService
from app.utils.decorators import permission_required, admin_required, any_permission_required
from app.utils.security import validate_password_strength

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================
# VISTAS (Templates)
# ============================================

@admin_bp.route('/')
@login_required
def admin_panel():
    """
    Panel de administración principal
    Accessible para administradores y usuarios con permisos específicos
    """
    # Verificar si el usuario tiene AL MENOS UN permiso de administración o reporte
    has_access = (
        current_user.is_admin or 
        current_user.has_permission('admin.users.view') or 
        current_user.has_permission('admin.roles.view') or 
        current_user.has_permission('reports.view') or
        current_user.has_permission('reports.audit.view') or
        current_user.has_permission('inventory.view')  # Ejemplo, ajustar según necesidad real de catálogos
    )
    
    if not has_access:
        flash('No tienes acceso al panel de administración.', 'error')
        return redirect(url_for('main.dashboard'))

    # Obtener estadísticas (solo si es admin o tiene permisos de ver usuarios, sino mostrar 0 o N/A)
    # Para simplificar, mostramos estadísticas generales pero protegemos enlaces en el template
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()

    # Usuarios recientes
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    # Fecha actual
    from datetime import datetime
    now = datetime.now()

    return render_template(
        'admin/panel.html',
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        recent_users=recent_users,
        now=now
    )

@admin_bp.route('/access-control')
@login_required
@any_permission_required('admin.users.view', 'admin.roles.view')
def access_control():
    """
    Centro de Control de Acceso Unificado
    Gestiona Usuarios y Roles en una sola interfaz
    """
    return render_template('admin/access_control.html')

@admin_bp.route('/users')
@login_required
@any_permission_required('admin.users.view')
def users_list():
    """Vista de lista de usuarios"""
    return render_template('admin/users_list.html')

@admin_bp.route('/roles')
@login_required
@any_permission_required('admin.roles.view')
def roles_list():
    """Vista de lista de roles"""
    return render_template('admin/roles_list.html')

@admin_bp.route('/audit')
@login_required
@permission_required('reports.audit.view')
def audit_log():
    """Vista de logs de auditoría"""
    return render_template('admin/audit_log.html')

@admin_bp.route('/icecat-settings')
@login_required
@admin_required
def icecat_settings():
    """Vista de configuración de API de Icecat"""
    from app.models.system_setting import SystemSetting
    
    # Obtener configuraciones actuales
    api_username = SystemSetting.get_value('icecat_api_username', '')
    content_username = SystemSetting.get_value('icecat_content_username', '')
    language = SystemSetting.get_value('icecat_language', 'es')
    
    return render_template(
        'admin/icecat_settings.html',
        api_username=api_username,
        content_username=content_username,
        language=language
    )

# ============================================
# API ENDPOINTS - USUARIOS
# ============================================

@admin_bp.route('/api/users', methods=['GET'])
@login_required
@permission_required('admin.users.view')
def get_users():
    """Obtener lista de usuarios (JSON)"""
    users = User.query.filter_by(is_active=True).all()
    user_list = []
    
    for user in users:
        user_data = user.to_dict()
        user_data['roles'] = [role.name for role in user.roles]
        user_list.append(user_data)
        
    return jsonify(user_list)

@admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
@permission_required('admin.users.view')
def get_user_details(user_id):
    """Obtener detalles de un usuario"""
    user = User.query.get_or_404(user_id)
    data = user.to_dict()
    data['roles'] = [role.to_dict() for role in user.roles]
    data['all_permissions'] = user.get_permission_names()
    return jsonify(data)

@admin_bp.route('/api/users', methods=['POST'])
@login_required
@permission_required('admin.users.create', audit_action='create_user', audit_module='admin')
def create_user():
    """Crear nuevo usuario"""
    data = request.get_json()
    
    # Validaciones básicas
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
        
    # Validar fortaleza de contraseña
    is_valid, msg = validate_password_strength(data['password'])
    if not is_valid:
        return jsonify({'error': msg}), 400
        
    try:
        user = User.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data.get('full_name'),
            is_admin=data.get('is_admin', False)
        )
        
        # Asignar roles si se envían
        if 'roles' in data and isinstance(data['roles'], list):
            for role_name in data['roles']:
                role = RoleService.get_role_by_name(role_name)
                if role:
                    RoleService.assign_role_to_user(user.id, role.id, current_user.id)
        
        return jsonify(user.to_dict()), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@permission_required('admin.users.edit', audit_action='update_user', audit_module='admin')
def update_user(user_id):
    """Actualizar usuario existente"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'email' in data and data['email'] != user.email:
            # Validar email único
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'El email ya está en uso'}), 400
            user.email = data['email']
        if 'password' in data and data['password']:
            # Validar fortaleza
            is_valid, msg = validate_password_strength(data['password'])
            if not is_valid:
                return jsonify({'error': msg}), 400
                
            user.set_password(data['password'])
            user.must_change_password = True # Forzar cambio en próximo login
            
        # Actualizar campos RBAC
        if 'is_active' in data:
            user.is_active = data['is_active']
            
        # Sincronizar roles si se envían
        if 'roles' in data:
            RoleService.sync_roles_to_user(user.id, data['roles'])
        
        db.session.commit()
        return jsonify(user.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@permission_required('admin.users.delete', audit_action='delete_user', audit_module='admin')
def delete_user(user_id):
    """Eliminar (desactivar) usuario"""
    if user_id == current_user.id:
        return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
        
    user = User.query.get_or_404(user_id)
    
    # Soft delete (desactivar)
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Usuario desactivado exitosamente'})

# ============================================
# API ENDPOINTS - GESTIÓN DE ROLES DE USUARIO
# ============================================

@admin_bp.route('/api/users/<int:user_id>/roles', methods=['POST'])
@login_required
@permission_required('admin.users.edit', audit_action='assign_role_to_user', audit_module='admin')
def assign_role(user_id):
    """Asignar rol a usuario"""
    data = request.get_json()
    role_id = data.get('role_id')
    
    if not role_id:
        return jsonify({'error': 'role_id requerido'}), 400
        
    try:
        RoleService.assign_role_to_user(user_id, role_id, current_user.id)
        # Log explícito de cambio de rol
        AuditService.log_role_change(
            user_id=user_id,
            action='assign_role',
            role_name=Role.query.get(role_id).name,
            changed_by_id=current_user.id
        )
        return jsonify({'message': 'Rol asignado exitosamente'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/api/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@login_required
@permission_required('admin.users.edit', audit_action='remove_role_from_user', audit_module='admin')
def remove_role(user_id, role_id):
    """Remover rol de usuario"""
    try:
        role = Role.query.get(role_id)
        if not role:
             return jsonify({'error': 'Rol no encontrado'}), 404

        RoleService.remove_role_from_user(user_id, role_id)
        # Log explícito
        AuditService.log_role_change(
            user_id=user_id,
            action='remove_role',
            role_name=role.name,
            changed_by_id=current_user.id
        )
        return jsonify({'message': 'Rol removido exitosamente'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# ============================================
# API ENDPOINTS - ROLES (CRUD)
# ============================================

@admin_bp.route('/api/roles', methods=['GET'])
@login_required
@any_permission_required('admin.roles.view', 'admin.roles.manage')
def get_roles():
    """Listar todos los roles"""
    roles = RoleService.get_all_roles(include_inactive=True)
    return jsonify([role.to_dict(include_permissions=True) for role in roles])

@admin_bp.route('/api/roles', methods=['POST'])
@login_required
@permission_required('admin.roles.manage', audit_action='create_role', audit_module='admin')
def create_role():
    """Crear nuevo rol"""
    data = request.get_json()
    try:
        role = RoleService.create_role(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description')
        )
        
        # Asignar permisos iniciales
        if 'permissions' in data:
            RoleService.sync_permissions(role.id, data['permissions'])
            
        # Log detallado de auditoría
        AuditService.log_action(
            action='create_role',
            module='admin',
            target_type='Role',
            target_id=role.id,
            details={'display_name': role.display_name, 'permission_count': len(data.get('permissions', []))}
        )
            
        return jsonify(role.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/api/roles/<int:role_id>', methods=['PUT'])
@login_required
@permission_required('admin.roles.manage', audit_action='update_role', audit_module='admin')
def update_role(role_id):
    """Actualizar rol"""
    data = request.get_json()
    try:
        role = RoleService.update_role(
            role_id=role_id,
            display_name=data.get('display_name'),
            description=data.get('description'),
            is_active=data.get('is_active')
        )
        
        # Actualizar permisos si se envían
        if 'permissions' in data:
            RoleService.sync_permissions(role.id, data['permissions'])
            
        # Log detallado de auditoría
        AuditService.log_action(
            action='update_role',
            module='admin',
            target_type='Role',
            target_id=role.id,
            details={'display_name': role.display_name, 'permissions_updated': 'permissions' in data}
        )
            
        return jsonify(role.to_dict(include_permissions=True))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/api/roles/<int:role_id>', methods=['DELETE'])
@login_required
@permission_required('admin.roles.manage', audit_action='delete_role', audit_module='admin')
def delete_role(role_id):
    """Eliminar un rol"""
    try:
        # Obtener info antes de borrar para el log
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'error': 'Rol no encontrado'}), 404
        
        display_name = role.display_name
        
        RoleService.delete_role(role_id)
        
        # Log detallado
        AuditService.log_action(
            action='delete_role',
            module='admin',
            target_type='Role',
            target_id=role_id,
            details={'display_name': display_name}
        )
        
        return jsonify({'message': 'Rol eliminado correctamente'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# ============================================
# API ENDPOINTS - PERMISOS
# ============================================

@admin_bp.route('/api/permissions', methods=['GET'])
@login_required
@any_permission_required('admin.roles.manage', 'admin.roles.view')
def get_permissions():
    """Listar todos los permisos agrupados por módulo"""
    grouped_perms = PermissionService.get_permissions_grouped_by_module()
    # Serializar objetos Permission a dicts
    serialized_perms = {}
    for module, perms in grouped_perms.items():
        serialized_perms[module] = [p.to_dict() for p in perms]
    
    return jsonify(serialized_perms)

# ============================================
# API ENDPOINTS - AUDITORÍA
# ============================================

@admin_bp.route('/api/audit', methods=['GET'])
@login_required
@permission_required('reports.audit.view')
def get_audit_logs():
    """Obtener logs de auditoría con paginación"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = AuditService.get_logs(page=page, per_page=per_page)
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    })

# ============================================
# API ENDPOINTS - ICECAT CONFIGURATION
# ============================================

@admin_bp.route('/api/icecat-settings', methods=['GET'])
@login_required
@admin_required
def get_icecat_settings():
    """Obtener configuración actual de Icecat"""
    from app.models.system_setting import SystemSetting
    
    return jsonify({
        'api_token': SystemSetting.get_value('icecat_api_token', ''),
        'content_token': SystemSetting.get_value('icecat_content_token', ''),
        'api_username': SystemSetting.get_value('icecat_api_username', ''),
        'app_key': SystemSetting.get_value('icecat_app_key', ''),
        'content_username': SystemSetting.get_value('icecat_content_username', ''),
        'language': SystemSetting.get_value('icecat_language', 'es')
    })

@admin_bp.route('/api/icecat-settings', methods=['POST'])
@login_required
@admin_required
def save_icecat_settings():
    """Guardar configuración de Icecat"""
    from app.models.system_setting import SystemSetting
    
    data = request.get_json()
    
    try:
        # Guardar configuraciones
        SystemSetting.set_value(
            'icecat_api_token',
            data.get('api_token', ''),
            description='Icecat API Access Token',
            category='icecat'
        )
        
        SystemSetting.set_value(
            'icecat_content_token',
            data.get('content_token', ''),
            description='Icecat Content Access Token',
            category='icecat'
        )

        SystemSetting.set_value(
            'icecat_api_username',
            data.get('api_username', ''),
            description='Icecat API Access Token (Username)',
            category='icecat'
        )
        
        SystemSetting.set_value(
            'icecat_app_key',
            data.get('app_key', ''),
            description='Icecat AppKey (Full Icecat)',
            category='icecat'
        )
        
        SystemSetting.set_value(
            'icecat_content_username',
            data.get('content_username', ''),
            description='Icecat Content Access Token (Username)',
            category='icecat'
        )
        
        SystemSetting.set_value(
            'icecat_language',
            data.get('language', 'es'),
            description='Idioma por defecto para Icecat',
            category='icecat'
        )
        
        return jsonify({
            'success': True,
            'message': 'Configuración guardada exitosamente'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al guardar configuración: {str(e)}'
        }), 500

@admin_bp.route('/api/icecat-settings/test', methods=['POST'])
@login_required
@admin_required
def test_icecat_connection():
    """Probar conexión con Icecat usando las credenciales proporcionadas"""
    from app.services.icecat_service import IcecatService
    import requests
    
    data = request.get_json()
    username = data.get('username', '')
    app_key = data.get('app_key', '')
    api_token = data.get('api_token', '')
    content_token = data.get('content_token', '')
    
    # Validar requerimientos
    if not api_token and not username:
        return jsonify({
            'success': False,
            'message': 'Se requiere un API Token o un Username'
        }), 400
    
    try:
        # Probar con una lista de GTINs conocidos (Open Icecat friendly y Full Icecat)
        # ASUS Zenbook, Dell Vostro, HP 250 G10
        test_gtins = ['5397184771327', '197105780767', '198122307951']
        
        last_response = None
        success = False
        
        for test_gtin in test_gtins:
            try:
                # Determinar modo de autenticación
                params = {
                    'GTIN': test_gtin,
                    'Language': 'es',
                    'Content': 'All'
                }
                headers = {}
                
                if api_token:
                    # Modo Token (Headers)
                    headers['Api-Token'] = api_token
                    if content_token:
                        headers['Content-Token'] = content_token
                else:
                    # Modo Legacy (Params)
                    params['UserName'] = username
                    if app_key:
                        params['AppKey'] = app_key

                # Realizar petición (con reintentos SSL)
                # Intento 1: Conexión segura
                try:
                    response = requests.get(
                        IcecatService.BASE_URL,
                        params=params,
                        headers=headers,
                        timeout=5
                    )
                except requests.exceptions.SSLError:
                    # Intento 2: Fallback SSL
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    response = requests.get(
                        IcecatService.BASE_URL,
                        params=params,
                        headers=headers,
                        timeout=5,
                        verify=False
                    )
                
                last_response = response
                
                if response.status_code == 200:
                    json_data = response.json()
                    # Verificar que hay data real (no error disfrazado)
                    if 'data' in json_data and json_data['data']:
                        success = True
                        break # Éxito, salir del loop
                    elif 'StatusCode' in json_data and json_data['StatusCode'] != 1:
                         # Es un error de Icecat (ej. 401 User/AppKey mismatch)
                         continue 
            except Exception as e:
                continue # Intentar siguiente GTIN
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Conexión exitosa con Icecat'
            })
        
        # Si fallaron todos, analizar el último error
        if last_response:
            if last_response.status_code == 401:
                return jsonify({
                    'success': False,
                    'message': 'Credenciales inválidas. Verifica tu username/token.'
                }), 401
            else:
                 # Intentar dar un mensaje más descriptivo
                error_msg = f'Error de API: {last_response.status_code}'
                try:
                    error_json = last_response.json()
                    if error_json.get('Message'):
                        error_msg = error_json.get('Message')
                except:
                    pass
                
                return jsonify({
                    'success': False,
                    'message': f'No se pudo verificar. {error_msg}'
                }), last_response.status_code
        else:
             return jsonify({
                'success': False,
                'message': 'Error de conexión (Timeout o Red)'
            }), 500
    
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'message': 'Timeout al conectar con Icecat'
        }), 504
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
