# -*- coding: utf-8 -*-
# ============================================
# SCRIPT DE POBLADO DE DATOS RBAC (SEED)
# ============================================
# Este script inicializa la base de datos con:
# 1. Permisos del sistema (170+)
# 2. Roles predefinidos (8 roles)
# 3. Asignación de permisos a roles

import sys
import os

# Agregar directorio actual al path para imports
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.permission import Permission
from app.models.role import Role
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService

app = create_app()

# ============================================
# DEFINICIÓN DE PERMISOS
# ============================================

ALL_PERMISSIONS = [
    # --- DASHBOARD (5) ---
    {'name': 'dashboard.view', 'module': 'dashboard', 'display_name': 'Ver Dashboard General', 'description': 'Acceso al dashboard principal'},
    {'name': 'dashboard.view_sales', 'module': 'dashboard', 'display_name': 'Ver Gráficos de Ventas', 'description': 'Ver gráficos de ingresos y ventas'},
    {'name': 'dashboard.view_inventory', 'module': 'dashboard', 'display_name': 'Ver Estado Inventario', 'description': 'Ver resumen de inventario'},
    {'name': 'dashboard.view_financial', 'module': 'dashboard', 'display_name': 'Ver Datos Financieros', 'description': 'Ver métricas financieras (márgenes, costos)'},
    {'name': 'dashboard.export', 'module': 'dashboard', 'display_name': 'Exportar Datos Dashboard', 'description': 'Exportar datos del dashboard'},

    # --- INVENTORY (Laptops) (30) ---
    {'name': 'inventory.view_list', 'module': 'inventory', 'display_name': 'Ver Lista Inventario', 'description': 'Ver listado de laptops'},
    {'name': 'inventory.view_detail', 'module': 'inventory', 'display_name': 'Ver Detalle Laptop', 'description': 'Ver detalles completos de una laptop'},
    {'name': 'inventory.view_costs', 'module': 'inventory', 'display_name': 'Ver Costos', 'description': 'Ver costos de compra y márgenes', 'is_dangerous': True},
    {'name': 'inventory.create', 'module': 'inventory', 'display_name': 'Crear Laptop', 'description': 'Agregar nuevas laptops al inventario'},
    {'name': 'inventory.edit', 'module': 'inventory', 'display_name': 'Editar Laptop', 'description': 'Modificar datos de laptops'},
    {'name': 'inventory.delete', 'module': 'inventory', 'display_name': 'Eliminar Laptop', 'description': 'Eliminar laptops del sistema', 'is_dangerous': True},
    {'name': 'inventory.adjust_stock', 'module': 'inventory', 'display_name': 'Ajustar Stock', 'description': 'Modificar cantidades manualmente'},
    {'name': 'inventory.import', 'module': 'inventory', 'display_name': 'Importar Laptops', 'description': 'Carga masiva de laptops'},
    {'name': 'inventory.export', 'module': 'inventory', 'display_name': 'Exportar Inventario', 'description': 'Descargar reporte de inventario'},
    {'name': 'inventory.print_labels', 'module': 'inventory', 'display_name': 'Imprimir Etiquetas', 'description': 'Generar etiquetas de código de barras'},
    # Seriales
    {'name': 'inventory.serials.view', 'module': 'inventory', 'display_name': 'Ver Seriales', 'description': 'Ver seriales de laptops'},
    {'name': 'inventory.serials.add', 'module': 'inventory', 'display_name': 'Agregar Seriales', 'description': 'Registrar nuevos seriales'},
    {'name': 'inventory.serials.edit', 'module': 'inventory', 'display_name': 'Editar Seriales', 'description': 'Modificar información de seriales'},
    {'name': 'inventory.serials.delete', 'module': 'inventory', 'display_name': 'Eliminar Seriales', 'description': 'Eliminar seriales', 'is_dangerous': True},
    # Categorías/Config
    {'name': 'inventory.brands.manage', 'module': 'inventory', 'display_name': 'Gestionar Marcas', 'description': 'Crear/Editar/Eliminar marcas'},
    {'name': 'inventory.models.manage', 'module': 'inventory', 'display_name': 'Gestionar Modelos', 'description': 'Crear/Editar/Eliminar modelos'},
    {'name': 'inventory.specs.manage', 'module': 'inventory', 'display_name': 'Gestionar Especificaciones', 'description': 'Gestionar procesadores, RAM, discos, etc.'},
    {'name': 'inventory.locations.manage', 'module': 'inventory', 'display_name': 'Gestionar Ubicaciones', 'description': 'Gestionar almacenes y ubicaciones'},

    # --- INVOICES (Facturación) (25) ---
    {'name': 'invoices.view_list', 'module': 'invoices', 'display_name': 'Ver Facturas', 'description': 'Ver listado de facturas'},
    {'name': 'invoices.view_detail', 'module': 'invoices', 'display_name': 'Ver Detalle Factura', 'description': 'Ver factura completa'},
    {'name': 'invoices.create', 'module': 'invoices', 'display_name': 'Crear Factura', 'description': 'Emitir nueva factura'},
    {'name': 'invoices.edit_draft', 'module': 'invoices', 'display_name': 'Editar Borrador', 'description': 'Editar facturas en borrador'},
    {'name': 'invoices.cancel', 'module': 'invoices', 'display_name': 'Anular Factura', 'description': 'Anular una factura emitida', 'is_dangerous': True},
    {'name': 'invoices.delete', 'module': 'invoices', 'display_name': 'Eliminar Factura', 'description': 'Eliminar registro de factura (solo borradores)', 'is_dangerous': True},
    {'name': 'invoices.print', 'module': 'invoices', 'display_name': 'Imprimir Factura', 'description': 'Generar PDF de factura'},
    {'name': 'invoices.email', 'module': 'invoices', 'display_name': 'Enviar por Email', 'description': 'Enviar factura al cliente'},
    {'name': 'invoices.payments.add', 'module': 'invoices', 'display_name': 'Registrar Pago', 'description': 'Agregar pago a factura'},
    {'name': 'invoices.ncf.manage', 'module': 'invoices', 'display_name': 'Gestionar NCF', 'description': 'Administrar secuencias NCF', 'is_dangerous': True},
    {'name': 'invoices.view_own', 'module': 'invoices', 'display_name': 'Ver Mis Facturas', 'description': 'Ver solo facturas generadas por el usuario'},

    # --- CUSTOMERS (Clientes) (15) ---
    {'name': 'customers.view_list', 'module': 'customers', 'display_name': 'Ver Clientes', 'description': 'Ver listado de clientes'},
    {'name': 'customers.view_detail', 'module': 'customers', 'display_name': 'Ver Detalle Cliente', 'description': 'Ver perfil completo del cliente'},
    {'name': 'customers.create', 'module': 'customers', 'display_name': 'Crear Cliente', 'description': 'Registrar nuevo cliente'},
    {'name': 'customers.edit', 'module': 'customers', 'display_name': 'Editar Cliente', 'description': 'Modificar datos de cliente'},
    {'name': 'customers.delete', 'module': 'customers', 'display_name': 'Eliminar Cliente', 'description': 'Eliminar cliente del sistema', 'is_dangerous': True},
    {'name': 'customers.export', 'module': 'customers', 'display_name': 'Exportar Clientes', 'description': 'Descargar lista de clientes'},
    {'name': 'customers.view_history', 'module': 'customers', 'display_name': 'Ver Historial', 'description': 'Ver historial de compras del cliente'},

    # --- EXPENSES (Gastos) (15) ---
    {'name': 'expenses.view_list', 'module': 'expenses', 'display_name': 'Ver Gastos', 'description': 'Ver listado de gastos'},
    {'name': 'expenses.view_detail', 'module': 'expenses', 'display_name': 'Ver Detalle Gasto', 'description': 'Ver detalles del gasto'},
    {'name': 'expenses.create', 'module': 'expenses', 'display_name': 'Registrar Gasto', 'description': 'Crear nuevo registro de gasto'},
    {'name': 'expenses.edit', 'module': 'expenses', 'display_name': 'Editar Gasto', 'description': 'Modificar gasto existente'},
    {'name': 'expenses.delete', 'module': 'expenses', 'display_name': 'Eliminar Gasto', 'description': 'Eliminar gasto', 'is_dangerous': True},
    {'name': 'expenses.approve', 'module': 'expenses', 'display_name': 'Aprobar Gastos', 'description': 'Aprobar gastos pendientes'},
    {'name': 'expenses.categories.manage', 'module': 'expenses', 'display_name': 'Gestionar Categorías', 'description': 'Administrar categorías de gastos'},
    {'name': 'expenses.export', 'module': 'expenses', 'display_name': 'Exportar Gastos', 'description': 'Descargar reporte de gastos'},

    # --- REPORTS (Reportes) (30) ---
    {'name': 'reports.sales.view', 'module': 'reports', 'display_name': 'Reporte de Ventas', 'description': 'Ver reportes de ventas'},
    {'name': 'reports.inventory.view', 'module': 'reports', 'display_name': 'Reporte de Inventario', 'description': 'Ver reportes de inventario'},
    {'name': 'reports.financial.view', 'module': 'reports', 'display_name': 'Reporte Financiero', 'description': 'Ver reportes de ganancias y pérdidas', 'is_dangerous': True},
    {'name': 'reports.tax.view', 'module': 'reports', 'display_name': 'Reporte Fiscal (DGII)', 'description': 'Ver reportes para impuestos (606, 607, etc.)'},
    {'name': 'reports.commissions.view', 'module': 'reports', 'display_name': 'Reporte Comisiones', 'description': 'Ver reporte de comisiones de vendedores'},
    {'name': 'reports.customers.view', 'module': 'reports', 'display_name': 'Reporte Clientes', 'description': 'Ver análisis de clientes'},
    {'name': 'reports.audit.view', 'module': 'reports', 'display_name': 'Reporte Auditoría', 'description': 'Ver logs de auditoría del sistema'},
    
    # --- ADMIN (Administración) (20) ---
    {'name': 'admin.users.view', 'module': 'admin', 'display_name': 'Ver Usuarios', 'description': 'Ver lista de usuarios'},
    {'name': 'admin.users.create', 'module': 'admin', 'display_name': 'Crear Usuario', 'description': 'Crear nuevos usuarios'},
    {'name': 'admin.users.edit', 'module': 'admin', 'display_name': 'Editar Usuario', 'description': 'Modificar usuarios'},
    {'name': 'admin.users.delete', 'module': 'admin', 'display_name': 'Eliminar Usuario', 'description': 'Eliminar/Desactivar usuarios', 'is_dangerous': True},
    {'name': 'admin.roles.view', 'module': 'admin', 'display_name': 'Ver Roles', 'description': 'Ver roles del sistema'},
    {'name': 'admin.roles.manage', 'module': 'admin', 'display_name': 'Gestionar Roles', 'description': 'Crear/Editar roles y permisos', 'is_dangerous': True},
    {'name': 'admin.settings.view', 'module': 'admin', 'display_name': 'Ver Configuración', 'description': 'Ver configuración del sistema'},
    {'name': 'admin.settings.edit', 'module': 'admin', 'display_name': 'Editar Configuración', 'description': 'Modificar configuración global', 'is_dangerous': True},
    {'name': 'admin.security.view', 'module': 'admin', 'display_name': 'Ver Seguridad', 'description': 'Ver panel de seguridad'},
]

# ============================================
# DEFINICIÓN DE ROLES
# ============================================

ROLES_DEFINITION = {
    'super_admin': {
        'display_name': 'Super Administrador',
        'description': 'Acceso total y control absoluto del sistema',
        'permissions': ['*']  # Wildcard para todo
    },
    'admin': {
        'display_name': 'Administrador',
        'description': 'Gestión general del negocio, acceso a todo excepto config crítica',
        'permissions': [
            'dashboard.*', 
            'inventory.*', 
            'invoices.*', 
            'customers.*', 
            'expenses.*', 
            'reports.*',
            'admin.users.view', 'admin.users.create', 'admin.users.edit'
        ]
    },
    'gerente_ventas': {
        'display_name': 'Gerente de Ventas',
        'description': 'Supervisión de vendedores, aprobación de descuentos, reportes de ventas',
        'permissions': [
            'dashboard.view', 'dashboard.view_sales', 'dashboard.view_inventory',
            'inventory.view_list', 'inventory.view_detail', 'inventory.view_costs',
            'invoices.*',
            'customers.*',
            'reports.sales.view', 'reports.commissions.view', 'reports.customers.view'
        ]
    },
    'vendedor': {
        'display_name': 'Vendedor',
        'description': 'Facturación, gestión de clientes y vista básica de inventario',
        'permissions': [
            'dashboard.view', 'dashboard.view_sales',
            'inventory.view_list', 'inventory.view_detail',
            'invoices.view_list', 'invoices.view_detail', 'invoices.create', 'invoices.print', 'invoices.email', 'invoices.view_own',
            'customers.view_list', 'customers.view_detail', 'customers.create', 'customers.edit',
            'reports.commissions.view'
        ]
    },
    'contador': {
        'display_name': 'Contador',
        'description': 'Acceso a finanzas, gastos, reportes fiscales y auditoría',
        'permissions': [
            'dashboard.view', 'dashboard.view_financial',
            'invoices.view_list', 'invoices.view_detail', 'invoices.ncf.manage',
            'expenses.*',
            'reports.*'
        ]
    },
    'almacenista': {
        'display_name': 'Almacenista',
        'description': 'Gestión física de inventario, entradas y salidas',
        'permissions': [
            'dashboard.view', 'dashboard.view_inventory',
            'inventory.view_list', 'inventory.view_detail', 'inventory.create', 'inventory.edit', 
            'inventory.adjust_stock', 'inventory.import', 'inventory.print_labels',
            'inventory.serials.*',
            'inventory.locations.manage'
        ]
    },
    'visor': {
        'display_name': 'Visor (Sólo Lectura)',
        'description': 'Acceso de solo lectura para auditoría o consulta',
        'permissions': [
            'dashboard.view',
            'inventory.view_list', 'inventory.view_detail',
            'invoices.view_list', 'invoices.view_detail',
            'customers.view_list', 'customers.view_detail',
            'expenses.view_list', 'expenses.view_detail'
        ]
    },
    'soporte_tecnico': {
        'display_name': 'Soporte Técnico',
        'description': 'Acceso para mantenimiento y soporte de primer nivel',
        'permissions': [
            'dashboard.view',
            'inventory.view_list', 'inventory.view_detail',
            'admin.users.view', 'admin.settings.view', 'admin.security.view',
            'reports.audit.view'
        ]
    }
}


def seed_permissions():
    """Crear todos los permisos definidos"""
    print("🌱 Sembrando permisos...")
    created_count = 0
    skipped_count = 0

    for perm_data in ALL_PERMISSIONS:
        existing = Permission.get_by_name(perm_data['name'])
        if not existing:
            PermissionService.create_permission(
                name=perm_data['name'],
                display_name=perm_data['display_name'],
                description=perm_data['description'],
                module=perm_data['module'],
                is_dangerous=perm_data.get('is_dangerous', False)
            )
            created_count += 1
            # print(f"   [+] Creado: {perm_data['name']}")
        else:
            skipped_count += 1
    
    print(f"✅ Permisos: {created_count} creados, {skipped_count} existentes.")


def resolve_permissions(role_perms):
    """
    Convierte lista de strings (con wildcards) a objetos Permission
    Ej: ['inventory.*'] -> [Permission(inventory.create), Permission(inventory.edit)...]
    """
    if role_perms == ['*']:
        return Permission.query.all()
    
    resolved = set()
    all_perms = Permission.query.all()
    
    for pattern in role_perms:
        if pattern.endswith('.*'):
            # Wildcard de módulo (ej: inventory.*)
            module = pattern.split('.')[0]
            for p in all_perms:
                if p.module == module:
                    resolved.add(p)
        elif '.*' in pattern:
            # Wildcard parcial (ej: inventory.serials.*)
            prefix = pattern.replace('*', '')
            for p in all_perms:
                if p.name.startswith(prefix):
                    resolved.add(p)
        else:
            # Nombre exacto
            p = Permission.get_by_name(pattern)
            if p:
                resolved.add(p)
            else:
                print(f"   ⚠️ Advertencia: Permiso '{pattern}' no encontrado")
                
    return list(resolved)


def seed_roles():
    """Crear roles y asignar permisos"""
    print("\n🌱 Sembrando roles...")
    
    for role_name, role_def in ROLES_DEFINITION.items():
        role = Role.get_by_name(role_name)
        
        if not role:
            role = RoleService.create_role(
                name=role_name,
                display_name=role_def['display_name'],
                description=role_def['description'],
                is_system_role=True
            )
            print(f"   [+] Rol creado: {role_def['display_name']}")
        else:
            print(f"   [=] Rol existente: {role_def['display_name']}")
            
        # Asignar permisos
        permissions = resolve_permissions(role_def['permissions'])
        
        # Sincronizar permisos (RoleService.sync_permissions reemplaza todos)
        # Solo lo hacemos si acabamos de crear el rol o para asegurar integridad
        perm_ids = [p.id for p in permissions]
        RoleService.sync_permissions(role.id, perm_ids)
        print(f"       -> {len(permissions)} permisos asignados")


if __name__ == '__main__':
    with app.app_context():
        try:
            print("="*50)
            print(" INICIANDO POBLADO DE DATOS RBAC")
            print("="*50)
            
            seed_permissions()
            seed_roles()
            
            print("\n" + "="*50)
            print(" ✅ PROCESO COMPLETADO EXITOSAMENTE")
            print("="*50)
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {str(e)}")
            db.session.rollback()
