# -*- coding: utf-8 -*-
import os
import sys

# Agregar directorio actual al path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.role import Role
from app.models.permission import Permission
from app.services.role_service import RoleService

app = create_app()

def resolve_perms(patterns):
    resolved = []
    all_perms = Permission.query.all()
    for pattern in patterns:
        if pattern.endswith('.*'):
            module = pattern.split('.')[0]
            resolved.extend([p for p in all_perms if p.module == module])
        else:
            p = Permission.query.filter_by(name=pattern).first()
            if p:
                resolved.append(p)
    return list(set(resolved))

def create_roles():
    print("🚀 Creando perfiles solicitados...")
    
    with app.app_context():
        # 1. Vendedor
        vendedor_perms = resolve_perms([
            'dashboard.view', 'dashboard.view_sales',
            'inventory.view_list', 'inventory.view_detail',
            'invoices.create', 'invoices.view_list', 'invoices.view_detail', 'invoices.print',
            'customers.*',
            'reports.commissions.view'
        ])
        
        # 2. Administrador Restringido (Sin Finanzas)
        # Obtenemos todos los permisos
        all_perms = Permission.query.all()
        # Excluimos los sensibles
        excluded = [
            'dashboard.view_financial',
            'inventory.view_costs',
            'expenses.view_list', 'expenses.view_detail', 'expenses.create', 'expenses.edit', 'expenses.delete', 'expenses.approve', 'expenses.categories.manage', 'expenses.export',
            'reports.financial.view', 'reports.tax.view'
        ]
        admin_rest_perms = [p for p in all_perms if p.name not in excluded]

        # 3. Auditor Operativo
        auditor_perms = resolve_perms([
            'dashboard.view', 'dashboard.view_inventory',
            'inventory.view_list', 'inventory.view_detail',
            'invoices.view_list', 'invoices.view_detail',
            'customers.view_list', 'customers.view_detail',
            'reports.audit.view'
        ])

        roles_to_create = [
            {
                'name': 'vendedor_corporativo',
                'display_name': 'Vendedor Corporativo',
                'description': 'Acceso a ventas, clientes e inventario (sin costos).',
                'perms': vendedor_perms
            },
            {
                'name': 'admin_restringido',
                'display_name': 'Administrador (Sin Finanzas)',
                'description': 'Gestión total del sistema exceptuando costos, gastos y reportes contables.',
                'perms': admin_rest_perms
            },
            {
                'name': 'auditor_operativo',
                'display_name': 'Auditor Operativo',
                'description': 'Solo lectura de registros y reportes de auditoría.',
                'perms': auditor_perms
            }
        ]

        for r_data in roles_to_create:
            role = Role.query.filter_by(name=r_data['name']).first()
            if not role:
                role = RoleService.create_role(
                    name=r_data['name'],
                    display_name=r_data['display_name'],
                    description=r_data['description']
                )
                print(f"✅ Creado: {r_data['display_name']}")
            else:
                print(f"ℹ️ Ya existe: {r_data['display_name']}, actualizando permisos...")
            
            role.permissions = r_data['perms']
            db.session.commit()
            print(f"   -> {len(r_data['perms'])} permisos sincronizados.")

if __name__ == '__main__':
    create_roles()
