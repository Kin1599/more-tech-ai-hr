"""add wait to reqTypeEnum

Revision ID: 31ad1de02d80
Revises: ced149c937b0
Create Date: 2025-09-08 14:26:56.548873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31ad1de02d80'
down_revision: Union[str, None] = 'ced149c937b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем новое значение 'wait' в перечисление req_type_enum
    op.execute("ALTER TYPE req_type_enum ADD VALUE 'wait'")

def downgrade():
    pass
