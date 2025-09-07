"""add column created_at for meeting

Revision ID: ced149c937b0
Revises: c65d46f1c6ea
Create Date: 2025-09-07 23:58:07.431472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ced149c937b0'
down_revision: Union[str, None] = 'c65d46f1c6ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'meetings',
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )

def downgrade():
    op.drop_column('meetings', 'created_at')
