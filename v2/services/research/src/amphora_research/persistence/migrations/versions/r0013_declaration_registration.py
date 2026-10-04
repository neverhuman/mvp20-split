"""Append-only provenance for authenticated declaration registration."""
from pathlib import Path

from alembic import op

revision = "research_0013"
down_revision = "research_0012"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Declaration registration history requires a forward migration")
