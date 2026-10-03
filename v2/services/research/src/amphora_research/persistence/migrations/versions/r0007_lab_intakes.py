"""Atomic lab intake outcomes and exact observation membership."""
from pathlib import Path

from alembic import op

revision = "research_0007"
down_revision = "research_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Lab intake history requires an explicit forward migration")
