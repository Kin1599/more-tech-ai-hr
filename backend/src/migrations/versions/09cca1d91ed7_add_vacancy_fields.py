"""add vacancy fields

Revision ID: 09cca1d91ed7
Revises: 486f09133e04
Create Date: 2025-09-07 16:31:35.308933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09cca1d91ed7'
down_revision: Union[str, None] = '486f09133e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    offer_type = sa.Enum("TK", "GPH", "IP", name="offer_type_enum")
    busy_type = sa.Enum("allTime", "projectTime", name="busy_type_enum")
    offer_type.create(bind, checkfirst=True)
    busy_type.create(bind, checkfirst=True)

    with op.batch_alter_table("vacancies") as batch:
        batch.add_column(sa.Column("region", sa.String(), nullable=True))
        batch.add_column(sa.Column("city", sa.String(), nullable=True))
        batch.add_column(sa.Column("address", sa.String(), nullable=True))
        batch.add_column(sa.Column("offerType", offer_type, nullable=True))
        batch.add_column(sa.Column("busyType", busy_type, nullable=True))
        batch.add_column(sa.Column("graph", sa.String(), nullable=True))
        batch.add_column(sa.Column("salaryMin", sa.Numeric(), nullable=True))
        batch.add_column(sa.Column("salaryMax", sa.Numeric(), nullable=True))
        batch.add_column(sa.Column("annualBonus", sa.Numeric(), nullable=True))
        batch.add_column(sa.Column("bonusType", sa.String(), nullable=True))
        batch.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch.add_column(sa.Column("promt", sa.Text(), nullable=True))
        batch.add_column(sa.Column("exp", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("degree", sa.Boolean(), nullable=True))
        batch.add_column(sa.Column("specialSoftware", sa.String(), nullable=True))
        batch.add_column(sa.Column("computerSkills", sa.String(), nullable=True))
        batch.add_column(sa.Column("foreignLanguages", sa.String(), nullable=True))
        batch.add_column(sa.Column("languageLevel", sa.String(), nullable=True))
        batch.add_column(sa.Column("businessTrips", sa.Boolean(), nullable=True))

def downgrade():
    with op.batch_alter_table("vacancies") as batch:
        batch.drop_column("businessTrips")
        batch.drop_column("languageLevel")
        batch.drop_column("foreignLanguages")
        batch.drop_column("computerSkills")
        batch.drop_column("specialSoftware")
        batch.drop_column("degree")
        batch.drop_column("exp")
        batch.drop_column("promt")
        batch.drop_column("description")
        batch.drop_column("bonusType")
        batch.drop_column("annualBonus")
        batch.drop_column("salaryMax")
        batch.drop_column("salaryMin")
        batch.drop_column("graph")
        batch.drop_column("busyType")
        batch.drop_column("offerType")
        batch.drop_column("address")
        batch.drop_column("city")
        batch.drop_column("region")

    bind = op.get_bind()
    offer_type = sa.Enum("TK", "GPH", "IP", name="offer_type_enum")
    busy_type = sa.Enum("allTime", "projectTime", name="busy_type_enum")
    offer_type.drop(bind, checkfirst=True)
    busy_type.drop(bind, checkfirst=True)
