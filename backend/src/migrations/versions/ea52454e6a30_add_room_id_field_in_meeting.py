"""add room_id field in Meeting

Revision ID: ea52454e6a30
Revises: 15a80f279fa9
Create Date: 2025-09-09 19:46:08.882750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea52454e6a30'
down_revision: Union[str, None] = '15a80f279fa9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'meetings',
        sa.Column('roomId', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('meetings', 'roomId')
