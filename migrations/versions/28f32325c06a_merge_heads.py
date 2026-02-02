"""Merge heads

Revision ID: 28f32325c06a
Revises: add_rbac_tables, e006d822bd38
Create Date: 2026-01-31 05:29:15.988576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28f32325c06a'
down_revision = ('add_rbac_tables', 'e006d822bd38')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
