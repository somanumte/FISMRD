"""Manual update for Icecat V2.0

Revision ID: manual_update_v2
Revises: 1db9fbda9ba6
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'manual_update_v2'
down_revision = '1db9fbda9ba6'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add missing columns to 'laptops' table
    with op.batch_alter_table('laptops', schema=None) as batch_op:
        # Identificadores
        batch_op.add_column(sa.Column('serial_number', sa.String(length=100), nullable=True))
        
        # Especificaciones
        batch_op.add_column(sa.Column('unified_specs', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('processor_full_name', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('ram_capacity', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('storage_capacity', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('screen_size', sa.Numeric(precision=3, scale=1), nullable=True))
        batch_op.add_column(sa.Column('has_discrete_gpu', sa.Boolean(), nullable=True, server_default='false'))
        
        # Detalles técnicos
        batch_op.add_column(sa.Column('keyboard_backlight', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('keyboard_numeric_pad', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('fingerprint_reader', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('face_recognition', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('touchscreen', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('stylus_support', sa.Boolean(), nullable=True, server_default='false'))
        
        # Conectividad
        batch_op.add_column(sa.Column('wifi_standard', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('bluetooth_version', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('ethernet_port', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('cellular', sa.String(length=20), nullable=True))
        
        # Estado y financieros
        batch_op.add_column(sa.Column('subcategory', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('sale_price_dop', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column('max_stock', sa.Integer(), nullable=True))

        # Crear índices
        batch_op.create_index('ix_laptops_serial_number', ['serial_number'], unique=False)
        batch_op.create_index('ix_laptops_processor_full_name', ['processor_full_name'], unique=False)
        batch_op.create_index('ix_laptops_ram_capacity', ['ram_capacity'], unique=False)
        batch_op.create_index('ix_laptops_storage_capacity', ['storage_capacity'], unique=False)
        batch_op.create_index('ix_laptops_screen_size', ['screen_size'], unique=False)
        batch_op.create_index('ix_laptops_has_discrete_gpu', ['has_discrete_gpu'], unique=False)

    # 2. Create laptop_price_history table
    op.create_table('laptop_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('laptop_id', sa.Integer(), nullable=False),
        sa.Column('old_purchase_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('old_sale_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('old_discount_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('new_purchase_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('new_sale_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('new_discount_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('changed_by_id', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['laptop_id'], ['laptops.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('laptop_price_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_laptop_price_history_laptop_id'), ['laptop_id'], unique=False)

    # 3. Create laptop_view_stats table
    op.create_table('laptop_view_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('laptop_id', sa.Integer(), nullable=False),
        sa.Column('total_views', sa.Integer(), nullable=True),
        sa.Column('unique_views', sa.Integer(), nullable=True),
        sa.Column('views_today', sa.Integer(), nullable=True),
        sa.Column('views_this_week', sa.Integer(), nullable=True),
        sa.Column('views_this_month', sa.Integer(), nullable=True),
        sa.Column('last_reset_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['laptop_id'], ['laptops.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('laptop_view_stats', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_laptop_view_stats_laptop_id'), ['laptop_id'], unique=False)

def downgrade():
    with op.batch_alter_table('laptop_view_stats', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_laptop_view_stats_laptop_id'))
    op.drop_table('laptop_view_stats')
    
    with op.batch_alter_table('laptop_price_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_laptop_price_history_laptop_id'))
    op.drop_table('laptop_price_history')
    
    with op.batch_alter_table('laptops', schema=None) as batch_op:
        batch_op.drop_index('ix_laptops_has_discrete_gpu')
        batch_op.drop_index('ix_laptops_screen_size')
        batch_op.drop_index('ix_laptops_storage_capacity')
        batch_op.drop_index('ix_laptops_ram_capacity')
        batch_op.drop_index('ix_laptops_processor_full_name')
        batch_op.drop_index('ix_laptops_serial_number')
        
        batch_op.drop_column('max_stock')
        batch_op.drop_column('sale_price_dop')
        batch_op.drop_column('subcategory')
        batch_op.drop_column('cellular')
        batch_op.drop_column('ethernet_port')
        batch_op.drop_column('bluetooth_version')
        batch_op.drop_column('wifi_standard')
        batch_op.drop_column('stylus_support')
        batch_op.drop_column('touchscreen')
        batch_op.drop_column('face_recognition')
        batch_op.drop_column('fingerprint_reader')
        batch_op.drop_column('keyboard_numeric_pad')
        batch_op.drop_column('keyboard_backlight')
        batch_op.drop_column('npu')
        batch_op.drop_column('has_discrete_gpu')
        batch_op.drop_column('screen_size')
        batch_op.drop_column('storage_capacity')
        batch_op.drop_column('ram_capacity')
        batch_op.drop_column('processor_full_name')
        batch_op.drop_column('unified_specs')
        batch_op.drop_column('serial_number')
