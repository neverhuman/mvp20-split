"""Isolated result selections, preparation witnesses and fenced history."""
from pathlib import Path

from alembic import op

revision = "planning_0010"
down_revision = "planning_0009"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Result publication history requires a forward migration")
