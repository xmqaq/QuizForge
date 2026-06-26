"""add question_ids to quiz_session

Revision ID: a1b2c3d4e5f6
Revises: 20ab870eeff0
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "20ab870eeff0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "quiz_session",
        sa.Column("question_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("quiz_session", "question_ids")
