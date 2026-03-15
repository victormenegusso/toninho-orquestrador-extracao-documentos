"""add metodo_extracao to configuracoes

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "configuracoes",
        sa.Column(
            "metodo_extracao",
            sa.String(length=20),
            nullable=False,
            server_default="html2text",
            comment="Motor de extração: html2text (padrão) ou docling",
        ),
    )


def downgrade() -> None:
    op.drop_column("configuracoes", "metodo_extracao")
