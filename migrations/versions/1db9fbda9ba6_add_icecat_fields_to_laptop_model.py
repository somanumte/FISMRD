"""Add Icecat fields to Laptop model

Revision ID: 1db9fbda9ba6
Revises: b44c0b0bf280
Create Date: 2026-02-06 19:50:09.388295

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1db9fbda9ba6'
down_revision = 'b44c0b0bf280'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create system_settings table
    op.create_table('system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('system_settings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_system_settings_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_system_settings_key'), ['key'], unique=True)

    # 2. Add Icecat fields to laptops table
    with op.batch_alter_table('laptops', schema=None) as batch_op:
        batch_op.add_column(sa.Column('icecat_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('full_specs_json', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('normalized_specs', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('last_icecat_sync', sa.DateTime(), nullable=True))
        
        # Ensure gtin index exists or update it if needed
        # We use a try/except pattern in the migration or just add it if it might be missing
        batch_op.create_index(batch_op.f('ix_laptops_icecat_id'), ['icecat_id'], unique=False)


def downgrade():
    with op.batch_alter_table('laptops', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_laptops_icecat_id'))
        batch_op.drop_column('last_icecat_sync')
        batch_op.drop_column('normalized_specs')
        batch_op.drop_column('full_specs_json')
        batch_op.drop_column('icecat_id')

    with op.batch_alter_table('system_settings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_system_settings_key'))
        batch_op.drop_index(batch_op.f('ix_system_settings_category'))

    op.drop_table('system_settings')
