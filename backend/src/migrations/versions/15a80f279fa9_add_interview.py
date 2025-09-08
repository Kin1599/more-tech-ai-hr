"""add Interview

Revision ID: 15a80f279fa9
Revises: 31ad1de02d80
Create Date: 2025-09-08 20:05:48.602687

"""
from typing import Sequence, Union

from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15a80f279fa9'
down_revision: Union[str, None] = '31ad1de02d80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'interviews',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_application_id', sa.Integer, sa.ForeignKey('job_applications.id', ondelete="CASCADE"), nullable=False),
        sa.Column('history_json', sa.Text, nullable=False),
        sa.Column('feedback_json', sa.Text, nullable=True),
        sa.Column('strengths', sa.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column('weaknesses', sa.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column('verdict', sa.Enum('strong_hire', 'hire', 'borderline', 'no_hire',
                                     name='interview_verdict_enum'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('interviews')
    sa.Enum(name='interview_verdict_enum').drop(op.get_bind(), checkfirst=True)