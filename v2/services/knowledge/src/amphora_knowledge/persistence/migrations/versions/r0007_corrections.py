"""Append-only Knowledge receipt corrections; old publications remain immutable."""
from pathlib import Path

from alembic import op

revision = "knowledge_0007"
down_revision = "knowledge_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Correction history requires an explicit forward migration")
