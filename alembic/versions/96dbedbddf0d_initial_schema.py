"""initial_schema

Revision ID: 96dbedbddf0d
Revises:
Create Date: 2026-04-01 19:44:20.761733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '96dbedbddf0d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""

    # --- Companies ---
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('kvk_number', sa.String(20), nullable=True),
        sa.Column('btw_number', sa.String(20), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(10), nullable=True),
        sa.Column('iban', sa.String(34), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('company_type', sa.String(20), nullable=True),
        sa.Column('fiscal_year_start', sa.String(5), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=True),
        sa.Column('settings', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Users ---
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('role', sa.String(20), server_default='user'),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_provider_id', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean, server_default=sa.text('false')),
        sa.Column('onboarding_step', sa.Integer, server_default=sa.text('0')),
        sa.Column('onboarding_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Transactions ---
    transaction_type = postgresql.ENUM('income', 'expense', name='transactiontype', create_type=True)
    transaction_source = postgresql.ENUM('manual', 'bank', 'pdf', 'csv', name='transactionsource', create_type=True)
    transaction_status = postgresql.ENUM('pending', 'processed', 'reviewed', 'error', name='transactionstatus', create_type=True)

    transaction_type.create(op.get_bind(), checkfirst=True)
    transaction_source.create(op.get_bind(), checkfirst=True)
    transaction_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('type', transaction_type, nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('btw_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('btw_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('source', transaction_source, server_default='manual'),
        sa.Column('status', transaction_status, server_default='pending'),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('ai_category', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Documents ---
    processing_status = postgresql.ENUM('uploaded', 'ocr_processing', 'ai_processing', 'completed', 'error', name='processingstatus', create_type=True)
    processing_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('extracted_data', postgresql.JSONB, nullable=True),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('processing_status', processing_status, server_default='uploaded'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Ledger Entries ---
    op.create_table(
        'ledger_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id'), nullable=False),
        sa.Column('account_code', sa.String(10), nullable=False),
        sa.Column('account_name', sa.String(100), nullable=False),
        sa.Column('debit', sa.Numeric(12, 2), server_default=sa.text('0')),
        sa.Column('credit', sa.Numeric(12, 2), server_default=sa.text('0')),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- VAT Reports ---
    vat_status = postgresql.ENUM('draft', 'submitted', 'accepted', name='vatstatus', create_type=True)
    vat_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'vat_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('period', sa.String(10), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('btw_collected', sa.Numeric(12, 2), server_default=sa.text('0')),
        sa.Column('btw_paid', sa.Numeric(12, 2), server_default=sa.text('0')),
        sa.Column('btw_balance', sa.Numeric(12, 2), server_default=sa.text('0')),
        sa.Column('status', vat_status, server_default='draft'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Bank Connections ---
    op.create_table(
        'bank_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('institution_id', sa.String(100), nullable=False),
        sa.Column('institution_name', sa.String(255), nullable=False),
        sa.Column('institution_logo', sa.String(500), nullable=True),
        sa.Column('requisition_id', sa.String(255), nullable=False, unique=True),
        sa.Column('account_id', sa.String(255), nullable=True),
        sa.Column('iban', sa.String(34), nullable=True),
        sa.Column('account_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('last_synced', sa.DateTime, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # --- Cloud Connections ---
    op.create_table(
        'cloud_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_account_id', sa.String(255), nullable=True),
        sa.Column('provider_email', sa.String(255), nullable=True),
        sa.Column('provider_name', sa.String(255), nullable=True),
        sa.Column('access_token', sa.String(2000), nullable=True),
        sa.Column('refresh_token', sa.String(2000), nullable=True),
        sa.Column('token_expires_at', sa.DateTime, nullable=True),
        sa.Column('sync_folder_id', sa.String(500), nullable=True),
        sa.Column('sync_folder_name', sa.String(500), nullable=True),
        sa.Column('auto_import', sa.Boolean, server_default=sa.text('false')),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('is_active', sa.Boolean, server_default=sa.text('true')),
        sa.Column('last_synced', sa.DateTime, nullable=True),
        sa.Column('files_imported', sa.Integer, server_default=sa.text('0')),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('cloud_connections')
    op.drop_table('bank_connections')
    op.drop_table('vat_reports')
    op.drop_table('ledger_entries')
    op.drop_table('documents')
    op.drop_table('transactions')
    op.drop_table('users')
    op.drop_table('companies')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS vatstatus')
    op.execute('DROP TYPE IF EXISTS processingstatus')
    op.execute('DROP TYPE IF EXISTS transactionstatus')
    op.execute('DROP TYPE IF EXISTS transactionsource')
    op.execute('DROP TYPE IF EXISTS transactiontype')
