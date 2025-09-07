"""remove_fields_job_applications

Revision ID: c65d46f1c6ea
Revises: 01c970b3edd6
Create Date: 2025-09-07 22:43:15.934351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c65d46f1c6ea'
down_revision: Union[str, None] = '01c970b3edd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Удаляем столбцы soft, tech, salary, sumGrade из таблицы job_applications
    op.drop_column('job_applications', 'soft')
    op.drop_column('job_applications', 'tech')
    op.drop_column('job_applications', 'salary')
    op.drop_column('job_applications', 'sumGrade')

def downgrade():
    # Добавляем столбцы обратно для возможности отката миграции
    op.add_column('job_applications', sa.Column('soft', sa.Numeric, nullable=True))
    op.add_column('job_applications', sa.Column('tech', sa.Numeric, nullable=True))
    op.add_column('job_applications', sa.Column('salary', sa.Numeric, nullable=True))
    op.add_column('job_applications', sa.Column('sumGrade', sa.Numeric, nullable=True))