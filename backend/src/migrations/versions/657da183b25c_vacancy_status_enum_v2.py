"""vacancy status enum v2

Revision ID: 657da183b25c
Revises: 09cca1d91ed7
Create Date: 2025-09-07 16:48:47.943846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '657da183b25c'
down_revision: Union[str, None] = '09cca1d91ed7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) создаём новый тип с новыми метками
    op.execute("CREATE TYPE vacancy_status_enum_new AS ENUM ('active','closed','stopped')")

    # 2) переводим данные и меняем тип колонки
    #    hold   -> active
    #    found  -> closed
    #    approve-> active   (если нужно "stopped" для отдельных статусов — скажи, добавим правило)
    op.execute(
        """
        ALTER TABLE vacancies
        ALTER COLUMN status TYPE vacancy_status_enum_new
        USING (
            CASE status::text
                WHEN 'hold'    THEN 'active'
                WHEN 'found'   THEN 'closed'
                WHEN 'approve' THEN 'active'
                ELSE 'active'
            END
        )::vacancy_status_enum_new
        """
    )

    # 3) дропаем старый тип и переименовываем новый в старое имя,
    #    чтобы совпадало с models.py (name='vacancy_status_enum')
    op.execute("DROP TYPE vacancy_status_enum")
    op.execute("ALTER TYPE vacancy_status_enum_new RENAME TO vacancy_status_enum")


def downgrade():
    # обратная операция

    # 1) создаём временный старый тип
    op.execute("CREATE TYPE vacancy_status_enum_old AS ENUM ('hold','found','approve')")

    # 2) откатываем значения:
    #    active  -> hold
    #    closed  -> found
    #    stopped -> hold (фолбэк)
    op.execute(
        """
        ALTER TABLE vacancies
        ALTER COLUMN status TYPE vacancy_status_enum_old
        USING (
            CASE status::text
                WHEN 'active'  THEN 'hold'
                WHEN 'closed'  THEN 'found'
                WHEN 'stopped' THEN 'hold'
                ELSE 'hold'
            END
        )::vacancy_status_enum_old
        """
    )

    # 3) удаляем текущий тип и возвращаем имя
    op.execute("DROP TYPE vacancy_status_enum")
    op.execute("ALTER TYPE vacancy_status_enum_old RENAME TO vacancy_status_enum")