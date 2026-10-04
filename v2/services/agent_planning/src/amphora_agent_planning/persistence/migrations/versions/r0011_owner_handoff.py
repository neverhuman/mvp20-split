"""Immutable owner handoff preparations/events and separate fenced control."""
from pathlib import Path

from alembic import op

revision = "planning_0011"
down_revision = "planning_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Owner handoff history requires a forward migration")
