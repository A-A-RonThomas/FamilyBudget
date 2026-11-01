"""add is_split and parent_id to transaction for splitting purchases

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transaction', sa.Column('is_split', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('transaction', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_transaction_parent_id', 'transaction', 'transaction',
        ['parent_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_transaction_parent_id', 'transaction', ['parent_id'])


def downgrade() -> None:
    op.drop_index('ix_transaction_parent_id', table_name='transaction')
    op.drop_constraint('fk_transaction_parent_id', 'transaction', type_='foreignkey')
    op.drop_column('transaction', 'parent_id')
    op.drop_column('transaction', 'is_split')
