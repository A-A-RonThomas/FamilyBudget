"""update transaction table for simplefin

Revision ID: 001_simplefin_transaction
Revises:
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa

revision = '001_simplefin_transaction'
down_revision = '9be58c662800'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('transaction', sa.Column('is_income', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('transaction', 'is_income')