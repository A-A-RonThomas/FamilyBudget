"""add imported_at to transaction so newly synced transactions can be flagged

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-11-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: rows imported before this column existed have no import time
    op.add_column('transaction', sa.Column('imported_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_transaction_imported_at', 'transaction', ['imported_at'])


def downgrade() -> None:
    op.drop_index('ix_transaction_imported_at', table_name='transaction')
    op.drop_column('transaction', 'imported_at')
