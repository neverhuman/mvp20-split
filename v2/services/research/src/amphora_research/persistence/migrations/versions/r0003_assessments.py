"""Append-only assessment intents and resolved decisions."""

from pathlib import Path

from alembic import op

revision = "research_0003"
down_revision = "research_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Assessment history requires an explicit forward migration")
