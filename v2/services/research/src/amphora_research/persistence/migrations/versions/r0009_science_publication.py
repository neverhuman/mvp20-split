"""Isolated scientific Artifact publication history and fenced leases."""
from pathlib import Path

from alembic import op

revision = "research_0009"
down_revision = "research_0008"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Scientific publication history requires an explicit forward migration")
