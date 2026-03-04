"""add use_browser to configuracoes

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-03 22:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "configuracoes",
        sa.Column(
            "use_browser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Se True, usa Playwright para renderizar páginas JavaScript (SPAs)",
        ),
    )


def downgrade() -> None:
    op.drop_column("configuracoes", "use_browser")
