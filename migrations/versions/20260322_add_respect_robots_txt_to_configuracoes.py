"""add respect_robots_txt to configuracoes

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-22 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "configuracoes",
        sa.Column(
            "respect_robots_txt",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Se True, verifica robots.txt antes de extrair cada URL",
        ),
    )


def downgrade() -> None:
    op.drop_column("configuracoes", "respect_robots_txt")
