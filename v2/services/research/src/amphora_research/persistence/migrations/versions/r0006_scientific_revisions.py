"""Separate scientific revision journals and exact local specimen links."""
from pathlib import Path

from alembic import op

revision = "research_0006"
down_revision = "research_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Scientific history requires an explicit forward migration")
