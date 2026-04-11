"""float to numeric for monetary fields

Revision ID: a1b2c3d4e5f6
Revises: bd08dd4f0618
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '1e1eed82c3df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('transaction', 'amount',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='amount::numeric(10,2)'
    )

    op.alter_column('budget_item', 'expected',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='expected::numeric(10,2)'
    )
    op.alter_column('budget_item', 'actual',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='actual::numeric(10,2)'
    )

    op.alter_column('fund_item', 'starting_value',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='starting_value::numeric(10,2)'
    )
    op.alter_column('fund_item', 'plus',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='plus::numeric(10,2)'
    )
    op.alter_column('fund_item', 'minus',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='minus::numeric(10,2)'
    )
    op.alter_column('fund_item', 'ending_value',
        type_=sa.Numeric(10, 2),
        existing_type=sa.DOUBLE_PRECISION(),
        postgresql_using='ending_value::numeric(10,2)'
    )


def downgrade() -> None:
    op.alter_column('transaction', 'amount',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='amount::double precision'
    )

    op.alter_column('budget_item', 'expected',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='expected::double precision'
    )
    op.alter_column('budget_item', 'actual',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='actual::double precision'
    )

    op.alter_column('fund_item', 'starting_value',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='starting_value::double precision'
    )
    op.alter_column('fund_item', 'plus',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='plus::double precision'
    )
    op.alter_column('fund_item', 'minus',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='minus::double precision'
    )
    op.alter_column('fund_item', 'ending_value',
        type_=sa.DOUBLE_PRECISION(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='ending_value::double precision'
    )