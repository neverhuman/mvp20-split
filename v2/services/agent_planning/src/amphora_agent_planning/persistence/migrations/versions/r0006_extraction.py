"""Immutable extraction task and interpretation trace journal."""

from pathlib import Path

from alembic import op

revision = "planning_0006"
down_revision = "planning_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Planning history requires an explicit forward migration")
