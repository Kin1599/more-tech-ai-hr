"""upd tables

Revision ID: 01c970b3edd6
Revises: 657da183b25c
Create Date: 2025-09-07 21:34:32.127927

"""
from typing import Sequence, Union

from sqlalchemy.dialects.postgresql import ARRAY
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01c970b3edd6'
down_revision: Union[str, None] = '657da183b25c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 0) Переименования таблиц под новые модели
    with op.batch_alter_table("vacancies", schema=None) as batch:
        # promt -> prompt (если уже переименовано — пропустится на уровне БД)
        try:
            batch.alter_column("promt", new_column_name="prompt")
        except Exception:
            pass

    # applications -> job_applications
    try:
        op.rename_table("applications", "job_applications")
    except Exception:
        pass

    # application_events -> job_application_events
    try:
        op.rename_table("application_events", "job_application_events")
    except Exception:
        pass

    # 1) Новый ENUM для заявок: job_application_status_enum
    job_app_status = sa.Enum(
        "cvReview", "interview", "waitResult", "rejected", "approved",
        name="job_application_status_enum"
    )
    job_app_status.create(bind, checkfirst=True)

    # 2) Перевод статусов в job_applications.status из старого status_enum
    #    review   -> cvReview
    #    screening-> interview
    #    result   -> waitResult
    #    reject   -> rejected
    #    approve  -> approved
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
              SELECT 1
              FROM information_schema.columns
              WHERE table_name='job_applications' AND column_name='status'
          ) THEN
            ALTER TABLE job_applications
            ALTER COLUMN status TYPE job_application_status_enum
            USING (
              CASE status::text
                WHEN 'review'    THEN 'cvReview'
                WHEN 'screening' THEN 'interview'
                WHEN 'result'    THEN 'waitResult'
                WHEN 'reject'    THEN 'rejected'
                WHEN 'approve'   THEN 'approved'
                ELSE NULL
              END
            )::job_application_status_enum;
          END IF;
        END$$;
        """
    )

    # 3) Перевод статусов в job_application_events.status
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
              SELECT 1
              FROM information_schema.columns
              WHERE table_name='job_application_events' AND column_name='status'
          ) THEN
            ALTER TABLE job_application_events
            ALTER COLUMN status TYPE job_application_status_enum
            USING (
              CASE status::text
                WHEN 'review'    THEN 'cvReview'
                WHEN 'screening' THEN 'interview'
                WHEN 'result'    THEN 'waitResult'
                WHEN 'reject'    THEN 'rejected'
                WHEN 'approve'   THEN 'approved'
                ELSE NULL
              END
            )::job_application_status_enum;
          END IF;
        END$$;
        """
    )

    # 4) meeting_status_enum: заменяем reject/approve на rejected/approved
    # создаём временный новый тип
    op.execute(
        "CREATE TYPE meeting_status_enum_new AS ENUM ('cvReview','waitPickTime','waitMeeting','waitResult','rejected','approved')"
    )
    # маппинг значений
    op.execute(
        """
        ALTER TABLE meetings
        ALTER COLUMN status TYPE meeting_status_enum_new
        USING (
          CASE status::text
            WHEN 'reject'  THEN 'rejected'
            WHEN 'approve' THEN 'approved'
            ELSE status::text
          END
        )::meeting_status_enum_new
        """
    )
    # дроп старого и переименование нового в актуальное имя
    op.execute("DROP TYPE meeting_status_enum")
    op.execute("ALTER TYPE meeting_status_enum_new RENAME TO meeting_status_enum")

    # 5) Добавляем applicant_resume_versions
    op.create_table(
        "applicant_resume_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicant_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("text_hash", sa.String(length=64)),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # 6) Добавляем ссылку на версию резюме в job_applications (пока nullable=True)
    with op.batch_alter_table("job_applications", schema=None) as batch:
        batch.add_column(
            sa.Column(
                "resume_version_id",
                sa.Integer(),
                sa.ForeignKey("applicant_resume_versions.id", ondelete="RESTRICT"),
                nullable=True,  # после заполнения можно отдельной миграцией сделать NOT NULL
            )
        )

    # 7) job_application_cv_evaluations
    op.create_table(
        "job_application_cv_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_application_id",
            sa.Integer(),
            sa.ForeignKey("job_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resume_version_id",
            sa.Integer(),
            sa.ForeignKey("applicant_resume_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("strengths", ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("weaknesses", ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # 8) Старый тип status_enum больше не нужен — удалим, если существует
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_enum') THEN
            DROP TYPE status_enum;
          END IF;
        END$$;
        """
    )

    # (опционально) полезные индексы
    op.execute("CREATE INDEX IF NOT EXISTS ix_job_applications_applicant_vacancy ON job_applications(applicant_id, vacancy_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_meetings_application_id ON meetings(application_id)")


def downgrade() -> None:
    # Откат индексов
    op.execute("DROP INDEX IF EXISTS ix_meetings_application_id")
    op.execute("DROP INDEX IF EXISTS ix_job_applications_applicant_vacancy")

    # 1) Удаляем job_application_cv_evaluations
    op.drop_table("job_application_cv_evaluations")

    # 2) Удаляем resume_version_id из job_applications
    with op.batch_alter_table("job_applications", schema=None) as batch:
        try:
            batch.drop_constraint("job_applications_resume_version_id_fkey", type_="foreignkey")
        except Exception:
            pass
        try:
            batch.drop_column("resume_version_id")
        except Exception:
            pass

    # 3) Дропаем applicant_resume_versions
    op.drop_table("applicant_resume_versions")

    # 4) Возвращаем meeting_status_enum к старому набору значений
    op.execute(
        "CREATE TYPE meeting_status_enum_old AS ENUM ('cvReview','waitPickTime','waitMeeting','waitResult','reject','approve')"
    )
    op.execute(
        """
        ALTER TABLE meetings
        ALTER COLUMN status TYPE meeting_status_enum_old
        USING (
          CASE status::text
            WHEN 'rejected' THEN 'reject'
            WHEN 'approved' THEN 'approve'
            ELSE status::text
          END
        )::meeting_status_enum_old
        """
    )
    op.execute("DROP TYPE meeting_status_enum")
    op.execute("ALTER TYPE meeting_status_enum_old RENAME TO meeting_status_enum")

    # 5) Возврат статусов заявок в старый status_enum
    op.execute("CREATE TYPE status_enum AS ENUM ('review','screening','result','reject','approve')")

    op.execute(
        """
        ALTER TABLE job_application_events
        ALTER COLUMN status TYPE status_enum
        USING (
          CASE status::text
            WHEN 'cvReview'  THEN 'review'
            WHEN 'interview' THEN 'screening'
            WHEN 'waitResult' THEN 'result'
            WHEN 'rejected' THEN 'reject'
            WHEN 'approved' THEN 'approve'
            ELSE NULL
          END
        )::status_enum
        """
    )

    op.execute(
        """
        ALTER TABLE job_applications
        ALTER COLUMN status TYPE status_enum
        USING (
          CASE status::text
            WHEN 'cvReview'  THEN 'review'
            WHEN 'interview' THEN 'screening'
            WHEN 'waitResult' THEN 'result'
            WHEN 'rejected' THEN 'reject'
            WHEN 'approved' THEN 'approve'
            ELSE NULL
          END
        )::status_enum
        """
    )

    # 6) Удаляем новый тип job_application_status_enum
    op.execute("DROP TYPE IF EXISTS job_application_status_enum")

    # 7) Переименовываем таблицы обратно (если нужно)
    try:
        op.rename_table("job_application_events", "application_events")
    except Exception:
        pass
    try:
        op.rename_table("job_applications", "applications")
    except Exception:
        pass

    # 8) Переименовываем колонку prompt -> promt
    with op.batch_alter_table("vacancies", schema=None) as batch:
        try:
            batch.alter_column("prompt", new_column_name="promt")
        except Exception:
            pass