"""fix_serial_movements_cascade

Revision ID: 497434710d0a
Revises: manual_sync_all_catalogs_v3
Create Date: 2026-02-07 19:35:48.514424

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '497434710d0a'
down_revision = 'manual_sync_all_catalogs_v3'
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL for more control
    # First, find the actual constraint name
    op.execute("""
        DO $$
        DECLARE
            constraint_name TEXT;
        BEGIN
            -- Find the foreign key constraint name
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'serial_movements'::regclass
              AND confrelid = 'laptop_serials'::regclass
              AND contype = 'f'
              AND conkey = ARRAY[(SELECT attnum FROM pg_attribute 
                                  WHERE attrelid = 'serial_movements'::regclass 
                                  AND attname = 'serial_id')];
            
            -- Drop the existing constraint if it exists
            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE serial_movements DROP CONSTRAINT %I', constraint_name);
            END IF;
            
            -- Create the new constraint with CASCADE
            ALTER TABLE serial_movements
            ADD CONSTRAINT serial_movements_serial_id_fkey
            FOREIGN KEY (serial_id) REFERENCES laptop_serials(id) ON DELETE CASCADE;
        END $$;
    """)


def downgrade():
    # Revert to constraint without CASCADE
    op.execute("""
        ALTER TABLE serial_movements DROP CONSTRAINT IF EXISTS serial_movements_serial_id_fkey;
        ALTER TABLE serial_movements
        ADD CONSTRAINT serial_movements_serial_id_fkey
        FOREIGN KEY (serial_id) REFERENCES laptop_serials(id);
    """)
