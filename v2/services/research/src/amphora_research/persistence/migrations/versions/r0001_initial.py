"""Immutable Research identities and revision heads."""
from pathlib import Path

from alembic import op

revision = "research_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Evidence-bearing Research identities require an explicit forward migration")
