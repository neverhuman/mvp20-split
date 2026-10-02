"""Rebuild audit and atomic replacement of a semantic snapshot's materialization."""

from pathlib import Path

from alembic import op

revision = "knowledge_0002"
down_revision = "knowledge_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Knowledge history requires an explicit forward migration")
