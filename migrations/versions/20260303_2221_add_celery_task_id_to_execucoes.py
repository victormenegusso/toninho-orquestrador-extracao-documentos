"""add celery_task_id to execucoes

Revision ID: a1b2c3d4e5f6
Revises: 5f04d9df9438
Create Date: 2026-03-03 22:21:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "5f04d9df9438"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "execucoes",
        sa.Column(
            "celery_task_id",
            sa.String(length=255),
            nullable=True,
            comment="ID da task Celery associada (para revogação)",
        ),
    )


def downgrade() -> None:
    op.drop_column("execucoes", "celery_task_id")
