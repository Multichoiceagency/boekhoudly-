"""add parent_id and sort_order to companies

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-04-22

Adds hierarchy fields so the /bedrijven page can render a real tree
(Holding → Werk-BV → sub-entity) and reorder via drag-and-drop.

On Postgres the ALTER TABLE ... ADD COLUMN IF NOT EXISTS pattern is
used so re-running the migration on a partially-applied database is
idempotent. The FK uses ON DELETE SET NULL so deleting a parent company
promotes children to root instead of cascading data loss.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS parent_id UUID")
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0")
    # Add the FK separately so re-runs don't fail on existing constraint.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'companies_parent_id_fkey'
            ) THEN
                ALTER TABLE companies
                ADD CONSTRAINT companies_parent_id_fkey
                FOREIGN KEY (parent_id) REFERENCES companies(id) ON DELETE SET NULL;
            END IF;
        END$$;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_companies_parent_id ON companies(parent_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_companies_parent_id")
    op.execute("ALTER TABLE companies DROP CONSTRAINT IF EXISTS companies_parent_id_fkey")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS sort_order")
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS parent_id")
