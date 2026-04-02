"""add workspace tables

Revision ID: a2b3c4d5e6f7
Revises: 96dbedbddf0d
Create Date: 2026-04-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = '96dbedbddf0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to users (if not exists from initial)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'")

    # --- Invoices ---
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('number', sa.String(50), nullable=False),
        sa.Column('client', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('due_date', sa.Date, nullable=False),
        sa.Column('lines', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(20), server_default='concept'),
        sa.Column('paid_date', sa.Date, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Expenses ---
    op.create_table(
        'expenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('category', sa.String(100), server_default='Overig'),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('btw_rate', sa.Numeric(5, 2), server_default=sa.text('21')),
        sa.Column('status', sa.String(20), server_default='concept'),
        sa.Column('supplier_id', sa.String(100), nullable=True),
        sa.Column('receipt_url', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Debtors ---
    op.create_table(
        'debtors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('kvk', sa.String(20), nullable=True),
        sa.Column('btw', sa.String(30), nullable=True),
        sa.Column('iban', sa.String(34), nullable=True),
        sa.Column('payment_term', sa.Integer, server_default=sa.text('30')),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Creditors ---
    op.create_table(
        'creditors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), server_default='Overig'),
        sa.Column('iban', sa.String(34), nullable=True),
        sa.Column('payment_term', sa.Integer, server_default=sa.text('30')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Bank Transactions ---
    op.create_table(
        'bank_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('category', sa.String(100), server_default=''),
        sa.Column('matched', sa.Boolean, server_default=sa.text('false')),
        sa.Column('matched_invoice_id', sa.String(100), nullable=True),
        sa.Column('matched_expense_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('bank_transactions')
    op.drop_table('creditors')
    op.drop_table('debtors')
    op.drop_table('expenses')
    op.drop_table('invoices')
