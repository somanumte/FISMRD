"""Strict master manual sync for all catalogs V2.0

Revision ID: manual_sync_all_catalogs_v3
Revises: manual_update_v2_final
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'manual_sync_all_catalogs_v3'
down_revision = 'manual_update_v2_final'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Brands
    with op.batch_alter_table('brands', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logo_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('website', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('country', sa.String(length=100), nullable=True))

    # 2. Laptop Models
    with op.batch_alter_table('laptop_models', schema=None) as batch_op:
        batch_op.add_column(sa.Column('series', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('release_year', sa.Integer(), nullable=True))

    # 3. Processors
    with op.batch_alter_table('processors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lithography', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('tdp', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('cache', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('has_npu', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('manufacturer', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('turbo_frequency', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('base_frequency', sa.String(length=20), nullable=True))

    # 4. Operating Systems
    with op.batch_alter_table('operating_systems', schema=None) as batch_op:
        batch_op.add_column(sa.Column('family', sa.String(length=50), nullable=True))

    # 5. Screens
    with op.batch_alter_table('screens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('diagonal_inches', sa.Numeric(precision=3, scale=1), nullable=True))
        batch_op.add_column(sa.Column('hdr', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('brightness', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('resolution', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('hd_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('color_gamut', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('touchscreen', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('refresh_rate', sa.Integer(), nullable=True))

    # 6. Graphics Cards
    with op.batch_alter_table('graphics_cards', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dlss', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('memory_gb', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('tdp', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('memory_type', sa.String(length=50), nullable=True))

    # 7. Storage
    with op.batch_alter_table('storage', schema=None) as batch_op:
        batch_op.add_column(sa.Column('media_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('write_speed', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('nvme', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('read_speed', sa.Integer(), nullable=True))

    # 8. RAM
    with op.batch_alter_table('ram', schema=None) as batch_op:
        batch_op.add_column(sa.Column('channels', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('form_factor', sa.String(length=50), nullable=True))

    # 9. Stores
    with op.batch_alter_table('stores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manager_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=True))

    # 10. Locations
    with op.batch_alter_table('locations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('location_type', sa.String(length=50), nullable=True))

    # 11. Suppliers
    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tax_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('payment_terms', sa.String(length=100), nullable=True))

    # 12. Laptop Images
    with op.batch_alter_table('laptop_images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('height', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('width', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('mime_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(length=50), nullable=True, server_default='upload'))
        batch_op.add_column(sa.Column('file_size', sa.Integer(), nullable=True))

def downgrade():
    pass
