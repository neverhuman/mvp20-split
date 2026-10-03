"""Immutable interpretation intents, results and exact dependency indexes."""
from pathlib import Path

from alembic import op

revision = "research_0011"
down_revision = "research_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Interpretation history requires an explicit forward migration")
