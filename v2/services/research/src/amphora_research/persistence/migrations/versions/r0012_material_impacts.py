"""Backfill exact eligibility material dependencies and maintain them atomically for all writers."""
from pathlib import Path

from alembic import op

revision = "research_0012"
down_revision = "research_0011"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Material impact history requires an explicit forward migration")
