"""Final manual update for Icecat V2.0

Revision ID: manual_update_v2_final
Revises: manual_update_v2
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'manual_update_v2_final'
down_revision = 'manual_update_v2'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('laptops', schema=None) as batch_op:
        batch_op.add_column(sa.Column('keywords', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'))
        batch_op.add_column(sa.Column('warranty_months', sa.Integer(), nullable=True, server_default='12'))
        batch_op.add_column(sa.Column('warranty_expiry', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('public_notes', sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table('laptops', schema=None) as batch_op:
        batch_op.drop_column('public_notes')
        batch_op.drop_column('warranty_expiry')
        batch_op.drop_column('warranty_months')
        batch_op.drop_column('currency')
        batch_op.drop_column('keywords')
