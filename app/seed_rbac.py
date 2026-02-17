# -*- coding: utf-8 -*-
"""
============================================
SEED RBAC - Permisos Granulares + 3 Roles
============================================
Ejecutar con:  flask shell < seed_rbac.py
           o:  python -c "from app import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); exec(open('seed_rbac.py').read())"

Crea:
  - 52 permisos granulares organizados por módulo
  - 3 roles del sistema: Administrador, Vendedor, Inventarista
  - Asignación automática de permisos por rol

SEGURO PARA RE-EJECUTAR: No duplica permisos ni roles existentes.
"""

from app import db
from app.models.permission import Permission
from app.models.role import Role

# ============================================
# 1. DEFINICIÓN DE PERMISOS GRANULARES
# ============================================

PERMISSIONS = [
    # ──────────────── DASHBOARD ────────────────
    {
        'name': 'dashboard.view',
        'display_name': 'Ver Dashboard',
        'description': 'Acceso al dashboard principal con métricas y KPIs',
        'module': 'dashboard',
        'category': 'view',
        'is_dangerous': False
    },

    # ──────────────── INVENTARIO: LAPTOPS ────────────────
    {
        'name': 'inventory.laptops.view',
        'display_name': 'Ver Inventario',
        'description': 'Ver listado y detalle de laptops en inventario',
        'module': 'inventory',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'inventory.laptops.create',
        'display_name': 'Crear Laptop',
        'description': 'Agregar nuevas laptops al inventario',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'inventory.laptops.edit',
        'display_name': 'Editar Laptop',
        'description': 'Modificar datos de laptops existentes',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'inventory.laptops.delete',
        'display_name': 'Eliminar Laptop',
        'description': 'Eliminar laptops del inventario',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'inventory.laptops.duplicate',
        'display_name': 'Duplicar Laptop',
        'description': 'Crear copia de una laptop existente',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },

    # ---------------- PRODUCTOS GENERICOS ----------------
    {
        'name': 'products.view',
        'display_name': 'Ver Productos',
        'description': 'Ver listado y detalle de productos genericos',
        'module': 'inventory',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'products.create',
        'display_name': 'Crear Producto',
        'description': 'Agregar nuevos productos genericos al inventario',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'products.edit',
        'display_name': 'Editar Producto',
        'description': 'Modificar datos de productos existentes',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'products.delete',
        'display_name': 'Eliminar Producto',
        'description': 'Eliminar productos del inventario (Soft Delete)',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'products.categories.manage',
        'display_name': 'Gestionar Categorias',
        'description': 'Crear y editar categorias de productos',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'products.stock',
        'display_name': 'Ajustar Stock',
        'description': 'Realizar ajustes manuales de inventario',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },

    # ---------------- INVENTARIO: SERIALES ----------------
    {
        'name': 'inventory.serials.view',
        'display_name': 'Ver Seriales',
        'description': 'Ver listado y detalle de números de serie',
        'module': 'inventory',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'inventory.serials.create',
        'display_name': 'Crear Serial',
        'description': 'Registrar nuevos números de serie',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'inventory.serials.edit',
        'display_name': 'Editar Serial',
        'description': 'Modificar datos de seriales existentes',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'inventory.serials.delete',
        'display_name': 'Eliminar Serial',
        'description': 'Eliminar números de serie del sistema',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'inventory.serials.change_status',
        'display_name': 'Cambiar Estado de Serial',
        'description': 'Cambiar el estado de un serial (disponible, vendido, dañado, etc.)',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },

    # ──────────────── INVENTARIO: CATÁLOGOS ────────────────
    {
        'name': 'inventory.catalogs.view',
        'display_name': 'Ver Catálogos',
        'description': 'Ver catálogos de marcas, modelos, procesadores, tiendas, etc.',
        'module': 'inventory',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'inventory.catalogs.manage',
        'display_name': 'Gestionar Catálogos',
        'description': 'Crear, editar y eliminar ítems de catálogos',
        'module': 'inventory',
        'category': 'manage',
        'is_dangerous': False
    },

    # ──────────────── FACTURAS ────────────────
    {
        'name': 'invoices.list',
        'display_name': 'Listar Facturas',
        'description': 'Ver listado de todas las facturas',
        'module': 'invoices',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'invoices.view',
        'display_name': 'Ver Detalle de Factura',
        'description': 'Ver detalle completo de una factura',
        'module': 'invoices',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'invoices.create',
        'display_name': 'Crear Factura',
        'description': 'Crear nuevas facturas de venta',
        'module': 'invoices',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'invoices.edit',
        'display_name': 'Editar Factura',
        'description': 'Modificar facturas existentes y cambiar estado',
        'module': 'invoices',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'invoices.delete',
        'display_name': 'Eliminar Factura',
        'description': 'Anular o eliminar facturas',
        'module': 'invoices',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'invoices.export',
        'display_name': 'Exportar Facturas',
        'description': 'Exportar facturas a CSV u otros formatos',
        'module': 'invoices',
        'category': 'export',
        'is_dangerous': False
    },
    {
        'name': 'invoices.settings.view',
        'display_name': 'Ver Config. Facturación',
        'description': 'Ver configuración de empresa, NCF y facturación',
        'module': 'invoices',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'invoices.settings.manage',
        'display_name': 'Gestionar Config. Facturación',
        'description': 'Modificar configuración de empresa, NCF, logo, datos fiscales',
        'module': 'invoices',
        'category': 'manage',
        'is_dangerous': True
    },

    # ──────────────── CLIENTES ────────────────
    {
        'name': 'customers.view',
        'display_name': 'Ver Clientes',
        'description': 'Ver listado y detalle de clientes',
        'module': 'customers',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'customers.create',
        'display_name': 'Crear Cliente',
        'description': 'Registrar nuevos clientes',
        'module': 'customers',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'customers.edit',
        'display_name': 'Editar Cliente',
        'description': 'Modificar datos de clientes existentes',
        'module': 'customers',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'customers.delete',
        'display_name': 'Eliminar Cliente',
        'description': 'Desactivar o eliminar clientes',
        'module': 'customers',
        'category': 'manage',
        'is_dangerous': True
    },

    # ──────────────── GASTOS ────────────────
    {
        'name': 'expenses.view',
        'display_name': 'Ver Gastos',
        'description': 'Ver dashboard y detalle de gastos',
        'module': 'expenses',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'expenses.list',
        'display_name': 'Listar Gastos',
        'description': 'Ver listado completo de gastos',
        'module': 'expenses',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'expenses.create',
        'display_name': 'Crear Gasto',
        'description': 'Registrar nuevos gastos y categorías',
        'module': 'expenses',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'expenses.edit',
        'display_name': 'Editar Gasto',
        'description': 'Modificar gastos existentes y cambiar estado de pago',
        'module': 'expenses',
        'category': 'manage',
        'is_dangerous': False
    },
    {
        'name': 'expenses.delete',
        'display_name': 'Eliminar Gasto',
        'description': 'Eliminar gastos del sistema',
        'module': 'expenses',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'expenses.export',
        'display_name': 'Exportar Gastos',
        'description': 'Exportar gastos a CSV u otros formatos',
        'module': 'expenses',
        'category': 'export',
        'is_dangerous': False
    },

    # ──────────────── REPORTES ────────────────
    {
        'name': 'reports.view',
        'display_name': 'Ver Centro de Reportes',
        'description': 'Acceder al índice principal de reportes',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'reports.sales.view',
        'display_name': 'Ver Reportes de Ventas',
        'description': 'Acceder a reportes de ventas, tendencias y métodos de pago',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'reports.inventory.view',
        'display_name': 'Ver Reportes de Inventario',
        'description': 'Acceder a reportes de stock, valoración y movimientos',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'reports.customers.view',
        'display_name': 'Ver Reportes de Clientes',
        'description': 'Acceder a reportes de clientes, retención y análisis',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'reports.ncf.view',
        'display_name': 'Ver Reportes NCF',
        'description': 'Acceder a reportes de comprobantes fiscales (606, 607)',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'reports.financial.view',
        'display_name': 'Ver Reportes Financieros',
        'description': 'Acceder a reportes financieros, P&L y flujo de caja',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'reports.audit.view',
        'display_name': 'Ver Log de Auditoría',
        'description': 'Acceder al registro de auditoría del sistema',
        'module': 'reports',
        'category': 'view',
        'is_dangerous': False
    },

    # ──────────────── ADMINISTRACIÓN: USUARIOS ────────────────
    {
        'name': 'admin.users.view',
        'display_name': 'Ver Usuarios',
        'description': 'Ver listado y detalle de usuarios del sistema',
        'module': 'admin',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'admin.users.create',
        'display_name': 'Crear Usuario',
        'description': 'Registrar nuevos usuarios en el sistema',
        'module': 'admin',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'admin.users.edit',
        'display_name': 'Editar Usuario',
        'description': 'Modificar datos, roles y estado de usuarios',
        'module': 'admin',
        'category': 'manage',
        'is_dangerous': True
    },
    {
        'name': 'admin.users.delete',
        'display_name': 'Eliminar Usuario',
        'description': 'Desactivar usuarios del sistema',
        'module': 'admin',
        'category': 'manage',
        'is_dangerous': True
    },

    # ──────────────── ADMINISTRACIÓN: ROLES ────────────────
    {
        'name': 'admin.roles.view',
        'display_name': 'Ver Roles',
        'description': 'Ver listado de roles y sus permisos',
        'module': 'admin',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'admin.roles.manage',
        'display_name': 'Gestionar Roles',
        'description': 'Crear, editar, eliminar roles y asignar permisos',
        'module': 'admin',
        'category': 'manage',
        'is_dangerous': True
    },

    # ──────────────── ADMINISTRACIÓN: CONFIGURACIÓN ────────────────
    {
        'name': 'admin.settings.view',
        'display_name': 'Ver Configuración del Sistema',
        'description': 'Ver configuración general, Icecat, integraciones',
        'module': 'admin',
        'category': 'view',
        'is_dangerous': False
    },
    {
        'name': 'admin.settings.manage',
        'display_name': 'Gestionar Configuración del Sistema',
        'description': 'Modificar configuración general, API keys, integraciones',
        'module': 'admin',
        'category': 'manage',
        'is_dangerous': True
    },
]


# ============================================
# 2. DEFINICIÓN DE ROLES Y SUS PERMISOS
# ============================================

ROLES = {
    'administrador': {
        'display_name': 'Administrador',
        'description': 'Acceso completo a todas las funciones del sistema. '
                       'Gestiona usuarios, roles, configuración y todos los módulos.',
        'is_system_role': True,
        # ALL permissions
        'permissions': [p['name'] for p in PERMISSIONS],
    },

    'vendedor': {
        'display_name': 'Vendedor',
        'description': 'Gestiona ventas: crea facturas, administra clientes, '
                       'consulta inventario disponible y ve reportes de ventas.',
        'is_system_role': True,
        'permissions': [
            # Dashboard
            'dashboard.view',

            # Inventario (solo lectura + ver seriales)
            'inventory.laptops.view',
            'inventory.serials.view',
            'inventory.catalogs.view',

            # Facturas (CRUD completo excepto settings y delete)
            'invoices.list',
            'invoices.view',
            'invoices.create',
            'invoices.edit',
            'invoices.export',

            # Clientes (CRUD completo)
            'customers.view',
            'customers.create',
            'customers.edit',

            # Reportes (ventas y clientes)
            'reports.view',
            'reports.sales.view',
            'reports.customers.view',

            # Productos (solo lectura)
            'products.view',
        ],
    },

    'inventarista': {
        'display_name': 'Gestor de Inventario',
        'description': 'Gestiona el inventario completo: laptops, seriales, catálogos. '
                       'Registra gastos operativos y consulta reportes de inventario.',
        'is_system_role': True,
        'permissions': [
            # Dashboard
            'dashboard.view',

            # Inventario (CRUD completo)
            'inventory.laptops.view',
            'inventory.laptops.create',
            'inventory.laptops.edit',
            'inventory.laptops.delete',
            'inventory.laptops.duplicate',
            'inventory.serials.view',
            'inventory.serials.create',
            'inventory.serials.edit',
            'inventory.serials.delete',
            'inventory.serials.change_status',
            'inventory.catalogs.view',
            'inventory.catalogs.manage',

            # Gastos (CRUD completo)
            'expenses.view',
            'expenses.list',
            'expenses.create',
            'expenses.edit',
            'expenses.delete',
            'expenses.export',

            # Reportes (inventario)
            'reports.view',
            'reports.inventory.view',

            # Clientes (solo lectura, para referencia)
            'customers.view',

            # Productos (CRUD completo)
            'products.view',
            'products.create',
            'products.edit',
            'products.delete',
            'products.categories.manage',
            'products.stock',
        ],
    },
}


# ============================================
# 3. EJECUCIÓN DEL SEED
# ============================================

def seed():
    """Ejecuta el seed completo de permisos y roles."""

    print('=' * 60)
    print('  SEED RBAC - LuxeraRD')
    print('=' * 60)

    # -- Paso 1: Crear permisos --
    print('\n[PERMISOS] Creando permisos...')
    created_perms = 0
    skipped_perms = 0

    for perm_data in PERMISSIONS:
        existing = Permission.query.filter_by(name=perm_data['name']).first()
        if existing:
            # Actualizar display_name y description si cambió
            changed = False
            if existing.display_name != perm_data['display_name']:
                existing.display_name = perm_data['display_name']
                changed = True
            if existing.description != perm_data['description']:
                existing.description = perm_data['description']
                changed = True
            if existing.module != perm_data['module']:
                existing.module = perm_data['module']
                changed = True
            if existing.category != perm_data.get('category'):
                existing.category = perm_data.get('category')
                changed = True
            if existing.is_dangerous != perm_data.get('is_dangerous', False):
                existing.is_dangerous = perm_data.get('is_dangerous', False)
                changed = True
            if changed:
                print(f'  [UPD] Actualizado: {perm_data["name"]}')
            else:
                skipped_perms += 1
            continue

        perm = Permission(
            name=perm_data['name'],
            display_name=perm_data['display_name'],
            description=perm_data['description'],
            module=perm_data['module'],
            category=perm_data.get('category'),
            is_dangerous=perm_data.get('is_dangerous', False)
        )
        db.session.add(perm)
        created_perms += 1
        print(f'  [OK] Creado: {perm_data["name"]}')

    db.session.commit()
    print(f'\n  Resumen: {created_perms} creados, {skipped_perms} ya existían')

    # -- Paso 2: Crear roles --
    print('\n[ROLES] Creando roles...')

    for role_name, role_data in ROLES.items():
        existing_role = Role.query.filter_by(name=role_name).first()

        if existing_role:
            print(f'  [EXISTE] Rol "{role_name}" ya existe - actualizando permisos...')
            role = existing_role
            role.display_name = role_data['display_name']
            role.description = role_data['description']
            role.is_system_role = role_data['is_system_role']
        else:
            role = Role(
                name=role_name,
                display_name=role_data['display_name'],
                description=role_data['description'],
                is_system_role=role_data['is_system_role']
            )
            db.session.add(role)
            db.session.flush()  # Get role.id
            print(f'  [OK] Creado: {role_data["display_name"]}')

        # Sincronizar permisos del rol
        perm_names = role_data['permissions']
        permissions = Permission.query.filter(Permission.name.in_(perm_names)).all()
        role.permissions = permissions
        print(f'     -> {len(permissions)} permisos asignados')

    db.session.commit()

    # -- Paso 3: Resumen final --
    print('\n' + '=' * 60)
    print('  [FIN] SEED COMPLETADO')
    print('=' * 60)

    total_perms = Permission.query.count()
    total_roles = Role.query.count()
    print(f'\n  Permisos en DB: {total_perms}')
    print(f'  Roles en DB:    {total_roles}')

    print('\n  Roles y sus permisos:')
    for role in Role.query.order_by(Role.name).all():
        perm_count = len(role.permissions)
        print(f'    * {role.display_name} ({role.name}): {perm_count} permisos')

    print('\n  Permisos por módulo:')
    for module, perms in Permission.get_all_grouped_by_module().items():
        print(f'    * {module}: {len(perms)} permisos')

    print('\n  [INFO] Para asignar un rol a un usuario:')
    print('     from app.services.role_service import RoleService')
    print('     RoleService.assign_role_to_user(user_id=1, role_id=<role_id>)')
    print()


# Auto-ejecutar
seed()
