"""add volumes table and replace output_dir with volume_id

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-22 18:00:00.000000

"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create volumes table
    op.create_table(
        "volumes",
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column(
            "tipo",
            sa.String(50),
            nullable=False,
            server_default="LOCAL",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="ATIVO",
        ),
        sa.Column("descricao", sa.String(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome", name="uq_volume_nome"),
        sa.UniqueConstraint("path", name="uq_volume_path"),
    )
    op.create_index("idx_volume_nome", "volumes", ["nome"], unique=False)
    op.create_index("idx_volume_status", "volumes", ["status"], unique=False)
    op.create_index("idx_volume_tipo", "volumes", ["tipo"], unique=False)

    # 2. Create default volume
    conn = op.get_bind()
    default_volume_id = uuid4().hex
    conn.execute(
        sa.text(
            "INSERT INTO volumes (id, nome, path, tipo, status, descricao, created_at, updated_at) "
            "VALUES (:id, :nome, :path, :tipo, :status, :descricao, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ),
        {
            "id": default_volume_id,
            "nome": "Saída Padrão",
            "path": "output",
            "tipo": "LOCAL",
            "status": "ATIVO",
            "descricao": "Volume padrão criado automaticamente",
        },
    )

    # 3. Create volumes for unique output_dir values that differ from the default
    existing_dirs = conn.execute(
        sa.text(
            "SELECT DISTINCT output_dir FROM configuracoes WHERE output_dir != 'output'"
        )
    ).fetchall()

    dir_to_volume_id = {"output": default_volume_id}
    for row in existing_dirs:
        output_dir = row[0]
        vol_id = uuid4().hex
        # Check for duplicate paths (normpath might create conflicts)
        existing = conn.execute(
            sa.text("SELECT id FROM volumes WHERE path = :path"),
            {"path": output_dir},
        ).fetchone()
        if existing:
            dir_to_volume_id[output_dir] = str(existing[0])
            continue

        vol_nome = f"Volume - {output_dir}"
        conn.execute(
            sa.text(
                "INSERT INTO volumes (id, nome, path, tipo, status, descricao, created_at, updated_at) "
                "VALUES (:id, :nome, :path, :tipo, :status, :descricao, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {
                "id": vol_id,
                "nome": vol_nome,
                "path": output_dir,
                "tipo": "LOCAL",
                "status": "ATIVO",
                "descricao": "Volume migrado automaticamente de output_dir",
            },
        )
        dir_to_volume_id[output_dir] = vol_id

    # 4. Add volume_id column to configuracoes (nullable initially)
    op.add_column(
        "configuracoes",
        sa.Column("volume_id", sa.Uuid(), nullable=True),
    )

    # 5. Populate volume_id based on output_dir
    for output_dir, vol_id in dir_to_volume_id.items():
        conn.execute(
            sa.text(
                "UPDATE configuracoes SET volume_id = :vol_id WHERE output_dir = :output_dir"
            ),
            {"vol_id": vol_id, "output_dir": output_dir},
        )

    # Set remaining (any that didn't match) to default volume
    conn.execute(
        sa.text("UPDATE configuracoes SET volume_id = :vol_id WHERE volume_id IS NULL"),
        {"vol_id": default_volume_id},
    )

    # 6. SQLite doesn't support ALTER COLUMN to set NOT NULL, so we need to
    # recreate via batch mode. For simplicity with SQLite, we use batch_alter_table.
    with op.batch_alter_table("configuracoes") as batch_op:
        batch_op.alter_column("volume_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_configuracoes_volume_id",
            "volumes",
            ["volume_id"],
            ["id"],
        )
        batch_op.drop_column("output_dir")

    op.create_index(
        "idx_configuracao_volume_id", "configuracoes", ["volume_id"], unique=False
    )


def downgrade() -> None:
    conn = op.get_bind()

    # 1. Add output_dir back
    with op.batch_alter_table("configuracoes") as batch_op:
        batch_op.add_column(
            sa.Column("output_dir", sa.String(500), nullable=True),
        )

    # 2. Populate output_dir from volume.path
    conn.execute(
        sa.text(
            "UPDATE configuracoes SET output_dir = "
            "(SELECT path FROM volumes WHERE volumes.id = configuracoes.volume_id)"
        )
    )

    # 3. Set default for any nulls
    conn.execute(
        sa.text(
            "UPDATE configuracoes SET output_dir = 'output' WHERE output_dir IS NULL"
        )
    )

    # 4. Make output_dir NOT NULL, drop volume_id
    with op.batch_alter_table("configuracoes") as batch_op:
        batch_op.alter_column("output_dir", nullable=False)
        batch_op.drop_column("volume_id")

    op.drop_index("idx_configuracao_volume_id", table_name="configuracoes")

    # 5. Drop volumes table
    op.drop_index("idx_volume_tipo", table_name="volumes")
    op.drop_index("idx_volume_status", table_name="volumes")
    op.drop_index("idx_volume_nome", table_name="volumes")
    op.drop_table("volumes")
