# -*- coding: utf-8 -*-
# ============================================
# RUTAS ADICIONALES PARA ADMIN - CONFIGURACIÓN DE ICECAT
# ============================================
# Agregar estas rutas al archivo app/routes/admin.py

"""
INSTRUCCIONES DE INTEGRACIÓN:
=============================

1. Agregar estos imports al inicio de admin.py:
   
   from app.models.system_setting import SystemSetting, init_icecat_settings

2. Agregar estas rutas al final de admin.py (antes de cualquier código final):
   
   [Copiar todo el código de abajo]

3. Crear el archivo app/models/system_setting.py con el modelo SystemSetting

4. Crear el template app/templates/admin/icecat_config.html

5. Agregar el enlace en app/templates/admin/panel.html después de "Reportes y Análisis":

    {% if current_user.is_admin or current_user.has_permission('admin.settings') %}
    <!-- Configuración de Icecat -->
    <a href="{{ url_for('admin.icecat_config') }}"
        class="flex items-center justify-between p-4 bg-cyan-50 dark:bg-cyan-900/30 border-2 border-cyan-200 dark:border-cyan-800 rounded-xl hover:bg-cyan-100 dark:hover:bg-cyan-900/50 transition-all duration-300 group">
        <div class="flex items-center space-x-4">
            <div
                class="w-12 h-12 bg-cyan-100 dark:bg-cyan-900 rounded-xl flex items-center justify-center">
                <i class="fas fa-cloud text-xl text-cyan-600 dark:text-cyan-400"></i>
            </div>
            <div>
                <h3 class="font-bold text-gray-900 dark:text-white">Integración Icecat</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Catálogo de productos global</p>
            </div>
        </div>
        <svg class="w-5 h-5 text-gray-400 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors"
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7">
            </path>
        </svg>
    </a>
    {% endif %}

6. Ejecutar migración para crear la tabla system_settings:
   flask db migrate -m "Add system_settings table"
   flask db upgrade
"""

# ============================================
# RUTAS - COPIAR EN admin.py
# ============================================

@admin_bp.route('/icecat-config')
@login_required
@permission_required('admin.settings')
def icecat_config():
    """
    Página de configuración de la integración con Icecat
    """
    from app.models.system_setting import SystemSetting
    
    # Obtener configuración actual
    config = {
        'username': SystemSetting.get('icecat_username', 'openIcecat-live'),
        'language': SystemSetting.get('icecat_language', 'ES'),
        'enabled': SystemSetting.get('icecat_enabled', 'true').lower() == 'true',
        'has_api_token': bool(SystemSetting.get('icecat_api_token', '')),
        'has_content_token': bool(SystemSetting.get('icecat_content_token', ''))
    }
    
    return render_template('admin/icecat_config.html', config=config)


@admin_bp.route('/api/icecat-config', methods=['POST'])
@login_required
@permission_required('admin.settings')
def save_icecat_config():
    """
    Guarda la configuración de Icecat
    """
    from app.models.system_setting import SystemSetting
    from app.services.icecat_service import reload_icecat_config
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400
    
    try:
        # Guardar configuración
        if 'icecat_enabled' in data:
            SystemSetting.set(
                key='icecat_enabled',
                value='true' if data['icecat_enabled'] else 'false',
                category='icecat',
                description='Habilitar integración con Icecat'
            )
        
        if 'icecat_username' in data:
            SystemSetting.set(
                key='icecat_username',
                value=data['icecat_username'],
                category='icecat',
                description='Usuario de Icecat'
            )
        
        if 'icecat_language' in data:
            SystemSetting.set(
                key='icecat_language',
                value=data['icecat_language'],
                category='icecat',
                description='Idioma por defecto'
            )
        
        # Tokens - solo guardar si se proporcionan nuevos valores
        if data.get('icecat_api_token'):
            SystemSetting.set(
                key='icecat_api_token',
                value=data['icecat_api_token'],
                category='icecat',
                description='API Token de Icecat',
                encrypted=True
            )
        
        if data.get('icecat_content_token'):
            SystemSetting.set(
                key='icecat_content_token',
                value=data['icecat_content_token'],
                category='icecat',
                description='Content Token de Icecat',
                encrypted=True
            )
        
        # Recargar configuración en el servicio
        reload_icecat_config()
        
        # Log de auditoría
        AuditService.log_action(
            action='update_icecat_config',
            module='admin',
            target_type='SystemSetting',
            target_id=0,
            details={'updated_fields': list(data.keys())}
        )
        
        return jsonify({'success': True, 'message': 'Configuración guardada'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/icecat-test', methods=['POST'])
@login_required
@permission_required('admin.settings')
def test_icecat_connection():
    """
    Prueba la conexión con Icecat
    """
    from app.services.icecat_service import get_icecat_service, reload_icecat_config
    
    try:
        # Recargar configuración antes de probar
        service = reload_icecat_config()
        
        if not service.is_enabled():
            return jsonify({
                'success': False, 
                'error': 'La integración con Icecat está deshabilitada'
            })
        
        # Probar con un producto conocido (PlayStation 5)
        success, result = service.search_by_gtin('0711719709695')
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Conexión exitosa',
                'product': {
                    'title': result.title,
                    'brand': result.brand,
                    'category': result.category
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# CÓDIGO PARA panel.html - AGREGAR DESPUÉS DE "Reportes y Análisis"
# ============================================

"""
Agregar este bloque en app/templates/admin/panel.html después del enlace de "Reportes y Análisis"
(aproximadamente después de la línea 259):

                    {% if current_user.is_admin or current_user.has_permission('admin.settings') %}
                    <!-- Integración Icecat -->
                    <a href="{{ url_for('admin.icecat_config') }}"
                        class="flex items-center justify-between p-4 bg-cyan-50 dark:bg-cyan-900/30 border-2 border-cyan-200 dark:border-cyan-800 rounded-xl hover:bg-cyan-100 dark:hover:bg-cyan-900/50 transition-all duration-300 group">
                        <div class="flex items-center space-x-4">
                            <div
                                class="w-12 h-12 bg-cyan-100 dark:bg-cyan-900 rounded-xl flex items-center justify-center">
                                <i class="fas fa-cloud text-xl text-cyan-600 dark:text-cyan-400"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-gray-900 dark:text-white">Integración Icecat</h3>
                                <p class="text-sm text-gray-600 dark:text-gray-400">Catálogo de productos global</p>
                            </div>
                        </div>
                        <svg class="w-5 h-5 text-gray-400 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors"
                            fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7">
                            </path>
                        </svg>
                    </a>
                    {% endif %}
"""
