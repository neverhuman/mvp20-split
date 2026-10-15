"""Immutable declared ancestry membership under one root reservation."""
from pathlib import Path

from alembic import op

revision = "artifact_0013"
down_revision = "artifact_0012"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Protected closure history requires an explicit forward migration")
