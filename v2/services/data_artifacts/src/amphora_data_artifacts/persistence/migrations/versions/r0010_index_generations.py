"""Owned immutable generation intent/history and lease-fenced build cursors."""
from pathlib import Path

from alembic import op

revision = "artifact_0010"
down_revision = "artifact_0009"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Generation history requires an explicit forward migration")
