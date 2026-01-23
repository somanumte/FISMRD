# ============================================
# MIGRACIÓN: Sistema de Seriales de Fabricante
# ============================================
# 
# Este script crea las tablas necesarias para el sistema de seriales.
# Ejecutar con: flask db upgrade o directamente con Python
#
# Tablas creadas:
# - laptop_serials: Almacena seriales individuales
# - invoice_item_serials: Relación entre items de factura y seriales
# - serial_movements: Historial de movimientos de cada serial

"""
Migración para sistema de seriales de fabricante

Revision ID: add_serial_tracking
Revises: (previous_revision)
Create Date: 2025-01-22
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = 'add_serial_tracking'
down_revision = None  # Ajustar según tu historial de migraciones
branch_labels = None
depends_on = None


def upgrade():
    """Crear tablas del sistema de seriales"""

    # ============================================
    # TABLA: laptop_serials
    # ============================================
    op.create_table(
        'laptop_serials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('serial_number', sa.String(100), nullable=False),
        sa.Column('serial_normalized', sa.String(100), nullable=False),
        sa.Column('laptop_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='available'),
        sa.Column('serial_type', sa.String(50), nullable=True, server_default='manufacturer'),
        sa.Column('barcode', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('unit_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('warranty_start', sa.Date(), nullable=True),
        sa.Column('warranty_end', sa.Date(), nullable=True),
        sa.Column('warranty_provider', sa.String(100), nullable=True),
        sa.Column('sold_date', sa.DateTime(), nullable=True),
        sa.Column('sold_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Keys
        sa.ForeignKeyConstraint(['laptop_id'], ['laptops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id']),

        # Unique Constraints
        sa.UniqueConstraint('serial_number', name='uq_serial_number'),
        sa.UniqueConstraint('serial_normalized', name='uq_serial_normalized'),
    )

    # Índices para laptop_serials
    op.create_index('idx_serial_number', 'laptop_serials', ['serial_number'])
    op.create_index('idx_serial_normalized', 'laptop_serials', ['serial_normalized'])
    op.create_index('idx_serial_laptop_id', 'laptop_serials', ['laptop_id'])
    op.create_index('idx_serial_status', 'laptop_serials', ['status'])
    op.create_index('idx_serial_laptop_status', 'laptop_serials', ['laptop_id', 'status'])
    op.create_index('idx_serial_barcode', 'laptop_serials', ['barcode'])

    # ============================================
    # TABLA: invoice_item_serials
    # ============================================
    op.create_table(
        'invoice_item_serials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_item_id', sa.Integer(), nullable=False),
        sa.Column('serial_id', sa.Integer(), nullable=False),
        sa.Column('unit_sale_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Keys
        sa.ForeignKeyConstraint(['invoice_item_id'], ['invoice_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['serial_id'], ['laptop_serials.id'], ondelete='RESTRICT'),

        # Unique Constraint - Un serial solo puede estar en un item
        sa.UniqueConstraint('serial_id', 'invoice_item_id', name='uq_serial_invoice_item'),
    )

    # Índices para invoice_item_serials
    op.create_index('idx_invoice_item_serial', 'invoice_item_serials', ['invoice_item_id', 'serial_id'])

    # ============================================
    # TABLA: serial_movements
    # ============================================
    op.create_table(
        'serial_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('serial_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.String(30), nullable=False),
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),  # Renombrado de 'metadata' que es reservado
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Keys
        sa.ForeignKeyConstraint(['serial_id'], ['laptop_serials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
    )

    # Índices para serial_movements
    op.create_index('idx_movement_serial_id', 'serial_movements', ['serial_id'])
    op.create_index('idx_movement_serial_type', 'serial_movements', ['serial_id', 'movement_type'])
    op.create_index('idx_movement_date', 'serial_movements', ['created_at'])

    print("✅ Tablas de seriales creadas exitosamente")


def downgrade():
    """Eliminar tablas del sistema de seriales"""

    # Eliminar índices primero
    op.drop_index('idx_movement_date', table_name='serial_movements')
    op.drop_index('idx_movement_serial_type', table_name='serial_movements')
    op.drop_index('idx_movement_serial_id', table_name='serial_movements')

    op.drop_index('idx_invoice_item_serial', table_name='invoice_item_serials')

    op.drop_index('idx_serial_barcode', table_name='laptop_serials')
    op.drop_index('idx_serial_laptop_status', table_name='laptop_serials')
    op.drop_index('idx_serial_status', table_name='laptop_serials')
    op.drop_index('idx_serial_laptop_id', table_name='laptop_serials')
    op.drop_index('idx_serial_normalized', table_name='laptop_serials')
    op.drop_index('idx_serial_number', table_name='laptop_serials')

    # Eliminar tablas en orden inverso (por dependencias)
    op.drop_table('serial_movements')
    op.drop_table('invoice_item_serials')
    op.drop_table('laptop_serials')

    print("✅ Tablas de seriales eliminadas")


# ============================================
# SCRIPT ALTERNATIVO PARA SQLAlchemy DIRECTO
# ============================================

def create_tables_direct():
    """
    Crear tablas directamente con SQLAlchemy si no usas Alembic.

    Uso:
        from app import db, create_app
        app = create_app()
        with app.app_context():
            from migrations.add_serial_tracking import create_tables_direct
            create_tables_direct()
    """
    from app import db
    from app.models.serial import LaptopSerial, InvoiceItemSerial, SerialMovement

    # Crear todas las tablas
    db.create_all()

    print("✅ Tablas creadas con SQLAlchemy")


def verify_tables():
    """Verifica que las tablas existan"""
    from app import db
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    required_tables = ['laptop_serials', 'invoice_item_serials', 'serial_movements']

    missing = [t for t in required_tables if t not in tables]

    if missing:
        print(f"❌ Tablas faltantes: {missing}")
        return False

    print("✅ Todas las tablas de seriales existen")
    return True


# ============================================
# DATOS DE PRUEBA (Opcional)
# ============================================

def seed_test_data():
    """
    Crea datos de prueba para el sistema de seriales.
    Solo usar en desarrollo.
    """
    from app import db
    from app.models.laptop import Laptop
    from app.models.serial import LaptopSerial
    from datetime import date, timedelta

    # Obtener algunas laptops existentes
    laptops = Laptop.query.limit(3).all()

    if not laptops:
        print("⚠️ No hay laptops para crear seriales de prueba")
        return

    test_serials = [
        # Seriales para laptop 1
        {'serial': 'ABC123XYZ', 'type': 'service_tag'},
        {'serial': 'DEF456UVW', 'type': 'service_tag'},
        {'serial': 'GHI789RST', 'type': 'service_tag'},
        # Seriales para laptop 2
        {'serial': '5CG9102ABC', 'type': 'manufacturer'},
        {'serial': '5CG9103DEF', 'type': 'manufacturer'},
    ]

    created = 0
    for i, laptop in enumerate(laptops):
        # Asignar 2-3 seriales por laptop
        for serial_data in test_serials[i * 2:(i + 1) * 2]:
            try:
                serial = LaptopSerial(
                    laptop_id=laptop.id,
                    serial_number=serial_data['serial'],
                    serial_normalized=LaptopSerial.normalize_serial(serial_data['serial']),
                    serial_type=serial_data['type'],
                    status='available',
                    received_date=date.today() - timedelta(days=i * 7),
                    warranty_start=date.today() - timedelta(days=i * 7),
                    warranty_end=date.today() + timedelta(days=365),
                    warranty_provider='Fabricante'
                )
                db.session.add(serial)
                created += 1
            except Exception as e:
                print(f"⚠️ Error creando serial {serial_data['serial']}: {e}")

    try:
        db.session.commit()
        print(f"✅ {created} seriales de prueba creados")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    # Si se ejecuta directamente, mostrar ayuda
    print("""
    ============================================
    MIGRACIÓN: Sistema de Seriales
    ============================================

    Este script debe ejecutarse a través de Flask-Migrate (Alembic):

        flask db upgrade

    O puede crear las tablas directamente:

        from app import create_app, db
        app = create_app()
        with app.app_context():
            from migrations.add_serial_tracking import create_tables_direct
            create_tables_direct()

    Para verificar las tablas:

        with app.app_context():
            from migrations.add_serial_tracking import verify_tables
            verify_tables()

    Para crear datos de prueba (solo desarrollo):

        with app.app_context():
            from migrations.add_serial_tracking import seed_test_data
            seed_test_data()
    """)