"""add always_ignore and name-based default category to vendor

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vendor', sa.Column('always_ignore', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('vendor', sa.Column('default_category_name', sa.String(), nullable=True))
    op.add_column('vendor', sa.Column('default_category_is_fund', sa.Boolean(), nullable=True))

    op.drop_column('vendor', 'default_budget_item_id')
    op.drop_column('vendor', 'default_fund_item_id')


def downgrade() -> None:
    op.add_column('vendor', sa.Column('default_fund_item_id', sa.Integer(), sa.ForeignKey('fund_item.id'), nullable=True))
    op.add_column('vendor', sa.Column('default_budget_item_id', sa.Integer(), sa.ForeignKey('budget_item.id'), nullable=True))

    op.drop_column('vendor', 'default_category_is_fund')
    op.drop_column('vendor', 'default_category_name')
    op.drop_column('vendor', 'always_ignore')
