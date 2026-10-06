"""Append-only origin of public synthetic candidate declarations."""
from pathlib import Path

from alembic import op

revision = "research_0014"
down_revision = "research_0013"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Candidate registration history requires a forward migration")
