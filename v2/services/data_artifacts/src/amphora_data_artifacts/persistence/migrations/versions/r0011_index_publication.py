"""Verified index snapshots and authoritative corpus-head publication."""
from pathlib import Path

from alembic import op

revision = "artifact_0011"
down_revision = "artifact_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Index publication history requires an explicit forward migration")
