"""add phone/zip/state/country/website/extra to debtors

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-22

Perfex (and Moneybird/WeFact) expose more than just address+city — we were
dropping phone, zip, state, country, website, plus all the billing_* /
shipping_* variants and geo fields. Promote the most-used ones to columns
and keep the rest in a JSONB `extra` for later.
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE debtors ADD COLUMN IF NOT EXISTS phone VARCHAR(50)")
    op.execute("ALTER TABLE debtors ADD COLUMN IF NOT EXISTS zip VARCHAR(20)")
    op.execute("ALTER TABLE debtors ADD COLUMN IF NOT EXISTS state VARCHAR(100)")
    op.execute("ALTER TABLE debtors ADD COLUMN IF NOT EXISTS country VARCHAR(100)")
    op.execute("ALTER TABLE debtors ADD COLUMN IF NOT EXISTS website VARCHAR(255)")
    op.execute("ALTER TABLE debtors ADD COLUMN IF NOT EXISTS extra JSONB")


def downgrade() -> None:
    for col in ("phone", "zip", "state", "country", "website", "extra"):
        op.execute(f"ALTER TABLE debtors DROP COLUMN IF EXISTS {col}")
